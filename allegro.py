import os
import requests
import logging
from pprint import pprint
import time

logging.basicConfig(level=logging.DEBUG)

TOKEN_FILE = ".usertoken"

class APIFilter:
    def __init__(self, filters):
        self.filters = filters
        self.url_filter = self.format_filter()

    def format_filter(self):
        idx = 0
        formatted = ""
        for element in self.filters.items():
            if idx == 0:
                formatted = "?{}={}".format(element[0], element[1])
            else:
                formatted = "{}&{}={}".format(formatted, element[0], element[1])
            idx += 1
        return formatted

class AllegroAPI:
    def __init__(self, auth):
        self.auth = auth

    def get_headers(self):
        headers = {"Accept": "application/vnd.allegro.public.v1+json"}
        headers.update(self.auth)
        return headers

    def call_api(self, endpoint, filters=""):
        headers = self.get_headers()
        logging.debug("Request headers: {}".format(headers))
        return requests.get(url="{}{}".format(endpoint.url, filters), headers=headers)


class AllegroClientCreds:
    def __init__(self):
        self.CLIENT_ID = os.getenv("CLIENT_ID")
        self.CLIENT_SECRET = os.getenv("CLIENT_SECRET")
        self.ALLEGRO_GET_TOKEN_URL = "https://allegro.pl/auth/oauth/token"
        self.ALLEGRO_GET_CODES_URL = "https://allegro.pl/auth/oauth/device"
        #FIXME: Code can't be hardcoded
        self.ALLEGRO_AFTER_USER_AUTH = "https://allegro.pl/auth/oauth/token?grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Adevice_code&device_code="
        self.TOKEN = None

    def get_token(self):
        resp = requests.post(
            url=self.ALLEGRO_GET_TOKEN_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            auth=(self.CLIENT_ID, self.CLIENT_SECRET),
            data={"grant_type": "client_credentials"}
        )
        self.TOKEN = resp.json()["access_token"]

    def get_auth(self):
        self.get_token()
        return { "Authorization": "Bearer {}".format(self.TOKEN)}

class AllegroDeviceCreds(AllegroClientCreds):
    def get_access_token(self):
        resp = requests.post(
            url=self.ALLEGRO_GET_CODES_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            auth=(self.CLIENT_ID, self.CLIENT_SECRET),
            data={"client_id": self.CLIENT_ID}
        )
        self.USER_CODE = resp.json()["user_code"]
        self.DEVICE_CODE = resp.json()["device_code"]
        self.VERIFICATION_URI_COMPLETE = resp.json()["verification_uri_complete"]
        logging.info("Verification url: {}".format(self.VERIFICATION_URI_COMPLETE))
        self.wait_for_access_token()



    def wait_for_access_token(self):
        while True:
            resp = requests.post(
                url="{}{}".format(self.ALLEGRO_AFTER_USER_AUTH, self.DEVICE_CODE),
                auth=(self.CLIENT_ID, self.CLIENT_SECRET)
            )
            if resp.status_code == 200:
                self.ACCESS_TOKEN = resp.json()['access_token']
                with open(TOKEN_FILE) as token_file:
                    token_file.write(self.ACCESS_TOKEN)
                return
            else:
                logging.info("Waiting for authentication: {}".format(resp.json()['error']))
            time.sleep(5)

    def get_auth(self):
        #FIXME: Powinna byc obsluzone rekreowanie tokenu
        if not os.path.isfile(TOKEN_FILE):
            self.get_access_token()

        with open(".usertoken") as token_file:
            token = token_file.readline().strip()
        return { "Authorization": "Bearer {}".format(token)}

class Endpoint:
    API_URL = "https://api.allegro.pl"
    def __init__(self, path):
        self.url = Endpoint.API_URL + "/" + path

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, full_url):
        self._url = full_url


auth = AllegroDeviceCreds().get_auth()

# auth = AllegroClientCreds().get_auth()
# #endpoint = Endpoint("sale/categories")
endpoint = Endpoint("sale/products")
query_filter = APIFilter({"phrase": "lego 75810"}).url_filter
# query_filter = ""
r = AllegroAPI(auth).call_api(endpoint, query_filter)
print(r.json())