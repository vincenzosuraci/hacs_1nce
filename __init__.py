from threading import Thread

from datetime import timedelta
import logging

import voluptuous as vol

from homeassistant.const import (CONF_USERNAME, CONF_PASSWORD, CONF_SCAN_INTERVAL)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.event import async_track_time_interval

import base64

import requests

from datetime import datetime

import json as json_lib

# Setting log
_LOGGER = logging.getLogger('sim_credit_init')
_LOGGER.setLevel(logging.DEBUG)

# This is needed, it impacts on the name to be called in configurations.yaml
# Ref: https://developers.home-assistant.io/docs/en/creating_integration_manifest.html
DOMAIN = '1nce_account'

REQUIREMENTS = ['beautifulsoup4']

OBJECT_ID_CREDIT = 'credit'

CONF_PHONE_NUMBERS = 'phone_numbers'
CONF_SIM_ICCIDS = 'sim_iccids'

# Default scan interval = 15 minutes = 900 seconds
DEFAULT_SCAN_INTERVAL = timedelta(seconds=900)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_SIM_ICCIDS): [cv.string],
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.time_period,
    })
}, extra=vol.ALLOW_EXTRA)


# ----------------------------------------------------------------------------------------------------------------------
#
# ASYNC SETUP
#
# ----------------------------------------------------------------------------------------------------------------------


async def async_setup(hass, config):

    # create the 1nce Platform object
    hass.data[DOMAIN] = OncePlatform(hass, config)

    return True

# ----------------------------------------------------------------------------------------------------------------------
#
# 1NCE CRAWLER
#
# ----------------------------------------------------------------------------------------------------------------------

class OnceCrawler:

    def __init__(
        self,
        username,
        password
    ):
        self._username = username
        self._password = password
        self._credit = {}

    @property
    def username(self):
        return self._username

    @property
    def password(self):
        return self._password

    @property
    def credit(self):
        return self._credit

    def debug(self, msg):
        print(msg)

    def info(self, msg):
        print(msg)

    def error(self, msg):
        print(msg)

    @staticmethod
    def save_info(pnk, v, attributes):
        pass

    def get_sim_credit(self, iccid):

        # --------------------------------------------------------------------------------------------------------------
        #   FASE 1 - Obtain Access Token
        # --------------------------------------------------------------------------------------------------------------

        # login url
        url = 'https://api.1nce.com/management-api/oauth/token'

        # session keeping cookies
        session = requests.Session()

        json = {
            "grant_type": "client_credentials"
        }

        user_pass_str = self.username + ":" + self.password
        base64_user_pass_bytes = base64.b64encode(bytes(user_pass_str, 'utf-8'))
        base64_user_pass_str = base64_user_pass_bytes.decode('utf-8')

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": "Basic " + base64_user_pass_str
        }

        response = requests.post(
            url=url,
            json=json,
            headers=headers
        )

        # get http status code
        http_status_code = response.status_code

        # check response is okay
        if http_status_code != 200:

            self.error('login page (' + url + ') error: ' + str(http_status_code))

            # get html in bytes
            self.debug(str(response.content))

        else:

            # ----------------------------------------------------------------------------------------------------------
            #   FASE 2 - Recupero dell'accountId dal numero di telefono
            # ----------------------------------------------------------------------------------------------------------

            # get html in bytes
            json_str = response.text
            json = json_lib.loads(json_str)
            access_token = json["access_token"]

            url = "https://api.1nce.com/management-api/v1/sims/" + iccid + "/quota/data"

            headers = {
                "accept": "application/json",
                "authorization": "Bearer " + access_token
            }

            response = requests.get(
                url,
                headers=headers
            )

            # get http status code
            http_status_code = response.status_code

            # check response is okay
            if http_status_code != 200:

                self.error('login page (' + url + ') error: ' + str(http_status_code))

                # get html in bytes
                self.debug(str(response.text))

            else:
                # get html in bytes
                json_str = response.text
                json = json_lib.loads(json_str)

                if iccid not in self.credit:
                    self.credit[iccid] = {}

                self.credit[iccid]["volume"] = {
                    "value": json["volume"],
                    "icon": "mdi:web",
                    "uom": "MB"
                }

                self.credit[iccid]["total_volume"] = {
                    "value": json["total_volume"],
                    "icon": "mdi:web",
                    "uom": "MB"
                }

                # Converti la stringa in un oggetto datetime
                exp_date_obj = datetime.strptime(json["expiry_date"], "%Y-%m-%d %H:%M:%S")

                # Converti l'oggetto datetime nel formato desiderato
                exp_date_value = exp_date_obj.strftime("%d-%m-%Y")

                self.credit[iccid]["expiry_date"] = {
                    "value": exp_date_value,
                    "icon": "mdi:calendar-clock",
                    "uom": ""
                }

                for k, v in self.credit[iccid].items():
                    if v['value'] is not None:
                        pnk = iccid + '_' + k
                        self.info(pnk + ': ' + str(v['value']))
                        attributes = {
                            'icon': v['icon'],
                            'unit_of_measurement': v['uom']
                        }
                        self.save_info(pnk, v, attributes)


# ----------------------------------------------------------------------------------------------------------------------
#
# 1NCE PLATFORM
#
# ----------------------------------------------------------------------------------------------------------------------


class OncePlatform(OnceCrawler):

    def __init__(self, hass, config, domain):

        self._hass = hass
        self._config = config
        self._domain = domain
        self._name = '1nce'

        super().__init__(
            username = self.config[self.domain][CONF_USERNAME],
            password = self.config[self.domain][CONF_PASSWORD]
        )

        self._update_status_interval = self.config[self.domain][CONF_SCAN_INTERVAL]

        self.hass.async_create_task(self.async_update_credits())

        self.hass.async_create_task(self.async_start_timer())

    @property
    def hass(self):
        return self._hass

    @property
    def name(self):
        return self._name

    @property
    def domain(self):
        return self._domain

    @property
    def config(self):
        return self._config

    @property
    def update_status_interval(self):
        return self._update_status_interval

    async def async_start_timer(self):

        # This is used to update the status periodically
        self.info(self.name + ' credit will be updated each ' + str(self.update_status_interval))

        # Do not put "self.async_update_credits()", with the parenthesis,
        # otherwise you will pass a Coroutine, not a Coroutine function!
        # and get "Coroutine not allowed to be passed to HassJob"
        # Put "self.async_update_credits" without the parenthesis
        async_track_time_interval(
            self.hass,
            self.async_update_credits,
            self.update_status_interval
        )

    # Do not remove now=None, since when async_track_time_interval()
    # calls async_update_credits(), it passes to the function the time!
    async def async_update_credits(self, now=None):

        self.debug('Updating ' + self._name + ' account credit...')

        threads = []

        for sim_iccid in self.config[self.domain][CONF_SIM_ICCIDS]:
            thread = Thread(
                target=self.get_sim_credit,
                args=sim_iccid
            )
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

    def debug(self, msg):
        _LOGGER.error(msg)

    def info(self, msg):
        _LOGGER.info(msg)

    def error(self, msg):
        _LOGGER.error(msg)

    def save_info(self, pnk, v, attributes):
        self.hass.states.async_set(self.domain + "." + pnk, v['value'], attributes)