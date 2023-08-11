import logging
from core import GetPost, PartInfo, PartSearch
import json
import time

class Digikey(GetPost, PartSearch):
    def __init__(self, url: str, client_id:str, client_secret:str, auth_token: str=None, refresh_token: str=None, geo_loc: str='US', lang: str='en', currency: str='USD'):
        if not url.endswith('/'):
            url = url + '/'
        
        super().__init__(url)
        
        self.url = url
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_token = auth_token
        self.refresh_token = refresh_token
        self.logger = logging.getLogger(__name__)
        
        self.geo_loc = geo_loc
        self.lang = lang
        self.currency = currency
        
    def _check_auth_token(self):
        if self.auth_token is None:
            error = "Auth token is None, please get auth token first"
            self.logger.error(error)
            raise RuntimeError(error)
        
        
    def _setup_helper_user_input(self):
        user_input = input("Enter the code from the redirect url: ")
        cleaned_input = user_input.strip()
        
        if 'code=' in cleaned_input:
            code = cleaned_input.split('code=')[1]
            code = code.split('&')[0]
        else:
            error = "Error in getting code from input"
            print(error)
            raise RuntimeError(error)
            
        return code
        
    def setup_helper_cmd(self, redirect_uri:str):
        ''' Helps the user get auth code needed to use get_auth_token method'''
        raw_http = f"{self.url}v1/oauth2/authorize?response_type=code&client_id={self.client_id}&redirect_uri={redirect_uri}"
        print(f"Go to this url in your browser: {raw_http}")
        return self._setup_helper_user_input()
    
    def setup_helper_browser(self, redirect_uri:str):
        import webbrowser
        raw_http = f"{self.url}/v1/oauth2/authorize?response_type=code&client_id={self.client_id}&redirect_uri={redirect_uri}"
        webbrowser.open(raw_http)
        return self._setup_helper_user_input()
        
    def get_auth_token(self, code:str, redirect_uri:str) -> str:
        ''' Gets the auth token from digikey and updates the token attribute also returns the token
        
        args: 
            code (str): the code from the redirect url (done in the browser)
            client_id (str): the client id from digikey
            client_secret (str): the client secret from digikey
            redirect_uri (str): the redirect uri from digikey
            
        returns:
            response (requests.Response): the response from the request
        '''
        
        
        ext_url = 'v1/oauth2/token'
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': redirect_uri
        }
        response = self.post(data=data, ext_url=ext_url)
        
        if response.status_code == 200:
            self.auth_token = response.json()['access_token']
            self.refresh_token = response.json()['refresh_token']
            self.logger.info(f"Got auth token: {self.auth_token}, refresh token: {self.refresh_token}")
            return response
        else:
            error = f"Error in getting auth token, Response: {response.status_code}, {response.json()}"
            self.logger.error(error)
            raise RuntimeError(error)
        
    def get_refresh_token(self):
        ''' Refreshes the auth token and updates the token attribute also returns the token'''
        ext_url = 'v1/oauth2/token'
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token
        }
        response = self.post(data=data, ext_url=ext_url)
        
        if response.status_code == 200:
            self.auth_token = response.json()['access_token']
            self.refresh_token = response.json()['refresh_token']
            self.logger.info(f"Got auth token: {self.auth_token}, refresh token: {self.refresh_token}")
            return response
        else:
            error = f"Error in getting auth token, Response: {response.status_code}, {response.json()}"
            self.logger.error(error)
            raise RuntimeError(error)
        
        
    def lookup_by_part_numbers(self, part_numbers:[str]) -> list[PartInfo]:
        self._check_auth_token()
        
        
        
        for retry in range(1):
            infos = []
            
            fields_needed = ['ProductDescription', 'DigiKeyPartNumber', 'MediaLinks', 'Manufacturer', 'ManufacturerLeadWeeks', 'QuantityAvailable', 'StandardPricing', 'ProductStatus', 'ProductUrl']
            
            header = {
                    'X-DIGIKEY-Client-Id': self.client_id, 
                    'Authorization': f'Bearer {self.auth_token}'
                    }
            
            params = { 
                    'includes': ','.join(fields_needed),
                    'X-DIGIKEY-Locale-Site': self.geo_loc,
                    'X-DIGIKEY-Locale-Language': self.lang,
                    'X-DIGIKEY-Locale-Currency': self.currency,
                    } 
            
            
            for num in part_numbers:
                ext_url = f'Search/v3/Products/{num}'
                response = self.get(headers=header, params=params, ext_url=ext_url)
                
                if response.status_code != 200:
                    infos = []      # scrap all info if one part number fails, simple and inefficient - I coded this on Friday
                    break
                
                raw_info = response.json()
                print(json.dumps(raw_info, indent=4))
                part_info = PartInfo()
                part_info.name = raw_info['ProductDescription']
                part_info.part_number = raw_info['DigiKeyPartNumber']
                part_info.distributer = 'DigiKey'
                part_info.manufacturer = raw_info['Manufacturer']['Value']
                part_info.lead_time = raw_info['ManufacturerLeadWeeks']
                part_info.quantity = raw_info['QuantityAvailable']
                part_info.unit_price = raw_info['StandardPricing'][2]['UnitPrice'] # 2 is the index for 100 quantity
                part_info.life_cycle = raw_info['ProductStatus']
                part_info.url = raw_info['ProductUrl']
                part_info.datasheet_url = raw_info['MediaLinks'][0]['Url']
                
                infos.append(part_info)
                
            if response.status_code == 200:
                self.logger.info(f"Was able to get all part info")
                return infos
            else:
                if retry == 1:
                    error = f"Error in getting part info after retry, Response: {response.status_code}, {response.json()}"
                    self.logger.error(error)
                    raise RuntimeError(error)
                
                if response.status_code == 401:
                    self.logger.info(f"Recieved status code 401, refreshing token and trying again")
                    self.get_refresh_token()
                    
                elif response.status_code == 429:
                    self.logger.warning(f"Recieved status code 429, waiting 1 minute and trying again")
                    time.sleep(60)
                    
                else:
                    error = f"Error in getting part info, Response: {response.status_code}, {response.json()}. Trying again"
                    self.logger.error(error)




if __name__ == "__main__":
    # set logging level to DEBUG
    logging.basicConfig(level=logging.DEBUG)
    
    
    ## test authentication
    # dk = Digikey('https://sandbox-api.digikey.com')
    # response = dk.get_auth_token(code='SaS6Y9OS', client_id='oBD0pWD6vDwuPJqu1GPvZs5Buf8zWn7V', client_secret='JJPWQbVWGXJaH1M8', redirect_uri='https://localhost')
    # print(response)
    # print(response.request.url)
    # print(response.request.body)
    # print(response.request.headers)
    # print(response.json())
    # code = dk.setup_helper_cmd(client_id='oBD0pWD6vDwuPJqu1GPvZs5Buf8zWn7V', redirect_uri='https://localhost')
    
    
    dk = Digikey('https://sandbox-api.digikey.com', client_id='oBD0pWD6vDwuPJqu1GPvZs5Buf8zWn7V', client_secret='JJPWQbVWGXJaH1M8', auth_token='nhGFjqBow1dqDSEfGtAITW4HWqeD', refresh_token='duNeODvxTasNwADKBcvODvG7dyaVanFK')
    infos = dk.lookup_by_part_numbers(['GRM1555C1H2R2BA01D'])
    print(repr(infos[0]))

    
