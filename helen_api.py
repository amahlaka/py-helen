# Python app to fetch electricity usage from the HELEN API
# Usage: 
# import helen_api
# api_session = helen_api.HelenAPI(site id, username, password)
# api_session.quick_usage("1 week ago") -> returns hourly usage for the last week

import requests
import json
import sys
import os
import lxml
from lxml.html import fromstring
import datetime
import logging
import helen_helpers


logging.basicConfig(filename='helen_api.log', encoding='utf-8', level=logging.DEBUG)

class HelenAPI:
    def __init__(self, site_id, username, password):
        self.base_url = 'https://api.omahelen.fi/v7/'
        self.session = requests.Session()
        self.logging = logging.getLogger(__name__)
        self.site_id = site_id
        self.failed_auth = False
        self.authenticated = False
        self.authenticate(username, password)
    def authenticate(self, username, password):
        try:
            self.pre_auth()
        except Exception as e:
            print("Error occurred during pre-auth: " + str(e) + " More info in the log file")
            logging.error(e, exc_info=True)
            sys.exit(1)
        try:
            self.login(username, password)
            self.authenticated = True
        except Exception as e:
            print("Error occurred during login: " + str(e) + " More info in the log file")
            logging.error(e, exc_info=True)
            sys.exit(1)

    def pre_auth(self):
        # Step 1: Get valid Login URL
        pre_url = "https://www.helen.fi/hcc/TupasLoginFrame?service=account&locale=en"
        pre_response = self.session.get(pre_url, allow_redirects=True)
        fromstring(pre_response.text).xpath('//form/@action')[0]
        login_init_url = fromstring(pre_response.text).xpath('//form/@action')[0]
        # Step 2: Get the login page and extract the login target url
        init_response = self.session.post(login_init_url, data={})
        self.login_url = "https://login.helen.fi" + fromstring(init_response.text).xpath('//form/@action')[0]

    def login(self, username, password):
        # Step 3: Send credentials to login page
        login_response = self.session.post(self.login_url, data={'username': username, 'password': password}, headers = {'Content-Type': 'application/x-www-form-urlencoded'})
        # Step 4: Follow the auth flow and fetching a auth code and state, and send it to the server
        auth_response = self.auth_code_parse(login_response)
        # Step 5: Send a GET request to the api to get extra cookies and a auth code
        api_response = self.session.get("https://api.omahelen.fi/v2/login?redirect=https://web.omahelen.fi/?lang=en&lang=en")
        self.login_phase_2(api_response)
    
    def login_phase_2(self, response):
        # This is used by both login and token refresh functions.
        auth_response = self.auth_code_parse(response)
        self.session.headers['Authorization'] = 'Bearer ' + self.session.cookies['access-token']
    
    def auth_code_parse(self, response):
        parsed_html = fromstring(response.text)
        auth_action = parsed_html.forms[0].action
        auth_code = parsed_html.forms[0].fields["code"]
        auth_state = parsed_html.forms[0].fields["state"]
        auth_response = self.session.get(auth_action, params={'code': auth_code, 'state': auth_state})
        return auth_response
    
    def refresh_token(self):
        # Refresh the session token
        response = self.session.get("https://www.helen.fi/kirjautuminen", allow_redirects=True)
        new_session = self.auth_code_parse(response)
        self.session.cookies['access-token'] = new_session.cookies['access-token']
        self.session.headers['Authorization'] = 'Bearer ' + self.session.cookies['access-token']
    
    def quick_usage(self, range):
        return self.get_usage(helen_helpers.get_date_formatted(range), helen_helpers.current_time())
    
    def get_usage(self, start_date, end_date, resolution="hour"):
        # Get the usage data from the API
        if not self.authenticated:
            print("Not authenticated, please run authenticate() first")
            return
        if isinstance(start_date, datetime.datetime):
            start_date = start_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        if isinstance(end_date, datetime.datetime):
            end_date = end_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        url = self.base_url + "measurements/electricity"
        response = self.session.get(url, params={
            "begin": start_date,
            "end": end_date,
            "resolution": resolution,
            "allow_transfer": "true",
            "delivery_site_id": self.site_id
        })
        if response.status_code == 401:
            if not self.failed_auth:
                self.failed_auth = True
                self.refresh_token()
                return self.get_usage(start_date, end_date, resolution)
            else:
                print("Failed to authenticate, please check your credentials")
                logging.error("Failed to authenticate, please check your credentials")
                return
        if response.status_code != 200:
            print("Error occurred during usage fetch: " + str(response.status_code) + " More info in the log file")
            logging.error("Error occurred during usage fetch: " + str(response.status_code))
            logging.debug(response.text)
            return
        return response.json()


