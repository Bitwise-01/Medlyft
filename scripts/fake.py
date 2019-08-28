# Date: 04/15/2019
# Author: Mohamed
# Description: A fake info generator


from time import sleep
from requests import get

url = 'https://randomuser.me/api/?inc=name,location&nat=us'


class Fake:

    def __init__(self):
        self.url = 'https://randomuser.me/api/?inc=name,location&nat=us'

    def get(self, amount):
        return [self.parse(get(self.url).json()['results'][0]) for _ in range(amount)]

    def parse(self, json_info):
        sleep(0.5)

        return {
            'firstname': json_info['name']['first'],
            'lastname': json_info['name']['last'],
            'address': json_info['location']['street']
        }
