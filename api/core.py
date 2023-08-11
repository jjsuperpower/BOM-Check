import logging
import requests


class GetPost:
    def __init__(self, url:str):
        self.base_url = url
        if not self.base_url.endswith('/'):
            self.base_url = self.base_url + '/'
        self.logger = logging.getLogger(__name__)

    def get(self, params:dict, ext_url:str=''):
        url = self.base_url + ext_url
        try:
            self.logger.debug(f"Sending GET request to: {url}, Params: {self.base_url}")
            response = requests.get(url, params=params)
            self.logger.debug(f"Response from: {url}, Response: {response}")
            return response
        except Exception as e:
            self.logger.error(f"Error in sending GET request to: {url}, Error: {e}")
            raise e
        
    def post(self, data:dict, ext_url:str=''):
        url = self.base_url + ext_url
        try:
            self.logger.debug(f"Sending POST request to: {url}, Data: {data}")
            response = requests.post(url, data=data)
            self.logger.debug(f"Response from: {url}, Response: {response}")
            return response
        except Exception as e:
            self.logger.error(f"Error in sending POST request to: {url}, Error: {e}")
            raise e
