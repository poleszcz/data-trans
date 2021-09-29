import os
import requests
import base64
import logging

logging.basicConfig(level=logging.DEBUG)

class AllegroAPI:
    def __init__(self, auth):
        self.auth = auth

    def get_headers(self):
        headers = {"Accept": "application/vnd.allegro.public.v1+json"}
        headers.update(self.auth)
        return headers

    def call_api(self, endpoint):
        headers = self.get_headers()
        logging.debug("Request headers: {}".format(headers))
        return requests.get(url=endpoint.url, headers=headers)


class AllegroClientCreds:
    def __init__(self):
        self.CLIENT_ID = os.getenv("CLIENT_ID")
        self.CLIENT_SECRET = os.getenv("CLIENT_SECRET")
        self.ALLEGRO_GET_TOKEN_URL = "https://allegro.pl/auth/oauth/token"
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

auth = AllegroClientCreds().get_auth()
endpoint = Endpoint("sale/categories")
r = AllegroAPI(auth).call_api(endpoint)
print(r.json())