import mouser.api as mouser
import pandas
import logging


request = mouser.MouserPartSearchRequest('partnumber', 'mouser_api_keys.yaml')

search = request.part_search('SF2140A-1')

print(search)

request.print_clean_response()