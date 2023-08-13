import logging
from core import PartInfo, PartSearch
from exceptions import *

class Digikey(PartSearch):
    ''' Digikey class to wrap the Digikey API
    
    To use this 
        1. Create a sandbox account on digikey and then add an application
        2. Get the client id and client secret from the application
        3. Use the setup_helper_cmd or setup_helper_browser to get one time code from redirect url
        4. Use the get_auth_token method to get the auth token and refresh token
        5. Save the auth token and refresh token for later use
        
    Please note that the auth token will expire after 30 minutes and the refresh token will expire after 90 days
    when calling the lookup_by_part_numbers method if an error occurs it will try to refresh the auth token and then try again
        
    Methods:
        setup_helper_cmd: helps the user get the code from the redirect url
        setup_helper_browser: same as setup_helper_cmd but opens the browser for the user
        get_auth_token: gets the auth token from digikey and updates the token attribute also returns the token
        get_refresh_token: refreshes the auth token and updates the token attribute also returns the token
        lookup_by_part_numbers: looks up the part numbers and returns a list of PartInfo objects
        
    Attributes:
        url: the url of the digikey api
        client_id: the client id from digikey
        client_secret: the client secret from digikey
        auth_token: the auth token from digikey
        refresh_token: the refresh token from digikey
    
    '''
    
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
        ''' Checks if the auth token is None and raises an exception if it is'''
        
        if self.auth_token is None:
            error = "Auth token is None, please get auth token first"
            self.logger.error(error)
            raise PartSearchAuthError(error)
        
        
    def _setup_helper_user_input(self):
        ''' Internal method to get the code from the user input'''
        
        user_input = input("Enter the code from the redirect url: ")
        cleaned_input = user_input.strip()
        
        if 'code=' in cleaned_input:
            code = cleaned_input.split('code=')[1]
            code = code.split('&')[0]
        else:
            error = "Error in getting code from input"
            print(error)
            raise PartSearchError(error)
            
        return code
    
    def _parse_error(self, response)->None:
        ''' Identifies the error and raises the appropriate exception
        
        args: response (requests.Response): the response from the request
        returns: None (no error)
        
        raises: PartSearchError: if an error occured
        
        '''
        if response.status_code == 200:
            self.logger.info(f"Was able to get all part info")
            return
        if response.status_code == 400:
            error = 'Recieved status code 400, Bad request'
            self.logger.error(error)
            raise PartSearchBadRequestError(error)
        elif response.status_code == 401:
            error = 'Recieved status code 401, Token is probably expired'
            self.logger.info(error)
            raise PartSearchAuthError(error)
        elif response.status_code == 403:
            error = 'Recieved status code 403, Forbidden'
            logging.error(error)
            raise PartSearchAuthError(error)
        elif response.status_code == 404:
            error = 'Recieved status code 404, Not found'
            logging.error(error)
            raise PartSearchConnectionError(error)
        elif response.status_code == 429:
            error = 'Recieved status code 429, DigiKey rate limit exceeded'
            self.logger.warning(error)
            raise PartSearchRateLimitError(error)
        elif response.status_code == 503:
            error = 'Recieved status code 503, Service unavailable'
            self.logger.error(error)
            raise PartSearchConnectionError(error)
        else:
            error = 'Unknown error occured'
            self.logger.error(error)
            raise PartSearchError(error)
        
    def setup_helper_cmd(self, redirect_uri:str):
        ''' Helps the user get auth code needed to use get_auth_token method'''
        
        raw_http = f"{self.url}v1/oauth2/authorize?response_type=code&client_id={self.client_id}&redirect_uri={redirect_uri}"
        print(f"Go to this url in your browser: {raw_http}")
        return self._setup_helper_user_input()
    
    def setup_helper_browser(self, redirect_uri:str):
        ''' Same as setup_helper_cmd but opens the browser for the user'''
        
        import webbrowser
        raw_http = f"{self.url}/v1/oauth2/authorize?response_type=code&client_id={self.client_id}&redirect_uri={redirect_uri}"
        webbrowser.open(raw_http)
        return self._setup_helper_user_input()
        
    def get_auth_token(self, code:str, redirect_uri:str='https://localhost') -> str:
        ''' Gets the auth token from digikey and updates the token attribute also returns the token
        
        This function will automaticaly update the auth_token and refresh_token attributes
        
        args: 
            code (str): the code from the redirect url (done in the browser)
            client_id (str): the client id from digikey
            client_secret (str): the client secret from digikey
            redirect_uri (str): the redirect uri from digikey
            
        returns:
            response tuple(auth_token, refresh_token)
            
        raises:
            PartSearchAuthError: if an error occured
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
            
            return (self.auth_token, self.refresh_token)
        else:
            error = f"Error in getting auth token, Response: {response.status_code}, {response.json()}"
            self.logger.error(error)
            raise PartSearchAuthError(error)
        
    def get_refresh_token(self):
        ''' Refreshes the auth token and updates the token attribute also returns the token
        
        returns: tuple(auth_token, refresh_token)
        
        raises: PartSearchAuthError: if an error occured
        '''
        
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
            
            return (self.auth_token, self.refresh_token)
        else:
            error = f"Error in getting auth token, Response: {response.status_code}, {response.json()}"
            self.logger.error(error)
            raise PartSearchAuthError(error)
        
        
    def lookup_by_part_numbers(self, part_numbers:[str]) -> list[PartInfo]:
        ''' Looks up the part numbers and returns a list of PartInfo objects
        
        args: part_numbers (list[str]): a list of part numbers to lookup
        
        returns: list[PartInfo]: a list of PartInfo objects
        
        raises: PartSearchError: if an error occured
        '''
        
        
        self._check_auth_token()
        
        infos = []
        fields_needed = ['ProductDescription', 'DigiKeyPartNumber', 'MediaLinks', 'Manufacturer', 'ManufacturerLeadWeeks', 'QuantityAvailable', 'StandardPricing', 'ProductStatus', 'ProductUrl']
        
        header = {
                'X-DIGIKEY-Client-Id': self.client_id, 
                'Authorization': f'Bearer {self.auth_token}'
                }
        
        for num in part_numbers:
            
            params = {
                'includes': ','.join(fields_needed),
                'X-DIGIKEY-Locale-Site': self.geo_loc,
                'X-DIGIKEY-Locale-Language': self.lang,
                'X-DIGIKEY-Locale-Currency': self.currency,
                }
            
            ext_url = f'Search/v3/Products/{num}'
            response = self.get(headers=header, params=params, ext_url=ext_url)
            
            self._parse_error(response)
            
            raw_info = response.json()
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
            
        return infos




if __name__ == "__main__":
    # set logging level to DEBUG
    logging.basicConfig(level=logging.DEBUG)
    
    import json
    
    
    ## test authentication
    # dk = Digikey('https://sandbox-api.digikey.com')
    # response = dk.get_auth_token(code='SaS6Y9OS', client_id='oBD0pWD6vDwuPJqu1GPvZs5Buf8zWn7V', client_secret='JJPWQbVWGXJaH1M8', redirect_uri='https://localhost')
    # print(response)
    # print(response.request.url)
    # print(response.request.body)
    # print(response.request.headers)
    # print(response.json())
    # code = dk.setup_helper_cmd(client_id='oBD0pWD6vDwuPJqu1GPvZs5Buf8zWn7V', redirect_uri='https://localhost')
    
    
    dk = Digikey('https://sandbox-api.digikey.com', client_id='oBD0pWD6vDwuPJqu1GPvZs5Buf8zWn7V', client_secret='JJPWQbVWGXJaH1M8', auth_token='iPW2lsfrfWtlGIrzKLcjOPnV5KtI', refresh_token='qdpWyUvJANhwOAv5oJmDNdz5v7nnWYiG')
    
    try:
        infos = dk.lookup_by_part_numbers(['GRM1555C1H2R2BA01D'])
    except PartSearchAuthError:
        auth, refresh = dk.get_refresh_token()
        print(f'auth: {auth}, refresh: {refresh}')
        infos = dk.lookup_by_part_numbers(['GRM1555C1H2R2BA01D'])
    print(repr(infos[0]))

    
