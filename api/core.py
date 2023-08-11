import logging
import requests


class GetPost:
    def __init__(self, url:str):
        self.base_url = url
        if not self.base_url.endswith('/'):
            self.base_url = self.base_url + '/'
        self.logger = logging.getLogger(__name__)

    def get(self, params:dict='', ext_url:str='', headers:dict=None):
        url = self.base_url + ext_url
        try:
            self.logger.debug(f"Sending GET request to: {url}, Headers: {headers}, Params: {params}")
            response = requests.get(url, params=params, headers=headers)
            self.logger.debug(f"Response from: {url}, Response: {response}")
            return response
        except Exception as e:
            self.logger.error(f"Error in sending GET request to: {url}, Error: {e}")
            raise e
        
    def post(self, data:dict, ext_url:str='', headers:dict=None):
        url = self.base_url + ext_url
        try:
            self.logger.debug(f"Sending POST request to: {url}, Headers: {headers}, Data: {data}")
            response = requests.post(url, data=data, headers=headers)
            self.logger.debug(f"Response from: {url}, Response: {response}")
            return response
        except Exception as e:
            self.logger.error(f"Error in sending POST request to: {url}, Error: {e}")
            raise e

class PartInfo:
    # life cycle status codes
    # NEW = 'New'
    # ACTIVE = 'Active'
    # OBSOLETE = 'Obsolete'
    # NFND = 'Not For New Designs'
    
    def __init__(self):
        self.name = None
        self.part_number = None
        self.distributer = None
        self.manufacturer = None
        self.lead_time = None
        self.quantity = None
        self.unit_price = None      # aproximate price
        self.life_cycle = None
        self.url = None
        self.datasheet_url = None
        
    def __dict__(self) -> dict:
        return {
            'name':self.name,
            'part_number':self.part_number,
            'distibuter':self.distributer,
            'manufacturer':self.manufacturer,
            'lead_time':self.lead_time,
            'quantity':self.quantity,
            'price':self.unit_price,
            'life_cycle':self.life_cycle,
            'url': self.url
        }
        
    def __str__(self) -> str:
        return  ''.join([
                f'name: {self.name}, ' \
                f'part_number: {self.part_number}, '
                f'distributer: {self.distributer}, '
                f'manufacturer: {self.manufacturer}, '
                f'lead_time: {self.lead_time}, '
                f'quantity: {self.quantity}, '
                f'unit_price: {self.unit_price}, '
                f'life_cycle: {self.life_cycle}, '
                f'url: {self.url}, '
                f'datasheet_url: {self.datasheet_url}'
            ])
                
    def __repr__(self):
        return self.__str__().replace(', ', ',\n\t')


# abstract class
class PartSearch:
    def lookup_by_part_numbers(self, part_numbers:[str]) -> list[PartInfo]:
        raise NotImplementedError
    def lookup_by_names(self, names:list[str]) -> list[PartInfo]:
        raise NotImplementedError