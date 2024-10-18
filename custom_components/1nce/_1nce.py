import asyncio
import aiohttp
import async_timeout
import base64
import os
import time
import json as json_lib

from Cryptodome.PublicKey import RSA
from Cryptodome.Cipher import AES
from Cryptodome.Cipher import PKCS1_v1_5
from Cryptodome.Util.Padding import pad, unpad

from .const import CONF_ICCID, CONF_USERNAME, CONF_PASSWORD, SENSOR_VOLUME, SENSOR_TOTAL_VOLUME, SENSOR_EXPIRY_DATE

# ----------------------------------------------------------------------------------------------------------------------
#
# 1nce
#
# ----------------------------------------------------------------------------------------------------------------------

class _1nce:

    # Massimo numero di prove di login
    MAX_NUM_RETRIES = 1

    # Minimo tempo che deve trascorre tra due interrogazioni successive al router
    MIN_INTERVAL_S = 2

    def __init__(
        self,
        params = {}
    ):
        self._iccid = params.get(CONF_ICCID, None)
        self._username = params.get(CONF_USERNAME, None)
        self._password = params.get(CONF_PASSWORD, None)

        self._session = None
        self._sim_data = None
        self._access_token = None
        self._last_update_timestamp = None

    @property
    def iccid(self):
        return self._iccid

    def debug(self, msg):
        print(msg)

    def info(self, msg):
        print(msg)

    def warning(self, msg):
        print(msg)

    def error(self, msg):
        print(msg)

    async def fetch_data(self):
        return await self._get_sim_data()


    async def _get_sim_data(self, num_retries=MAX_NUM_RETRIES):

        if self._last_update_timestamp is None or time.time() > self._last_update_timestamp + self.MIN_INTERVAL_S:

            self._last_update_timestamp = time.time()

            if await self._get_access_token() is not None:

                sim_data = None

                url = "https://api.1nce.com/management-api/v1/sims/" + iccid + "/quota/data"

                headers = {
                    "accept": "application/json",
                    "authorization": "Bearer " + self._access_token
                }

                try:
                    async with async_timeout.timeout(10):  # Timeout di 10 secondi
                        await self._async_init_session()
                        async with self._session.get(url, headers=headers) as response:
                            if response.status == 200:
                                json_str = response.text
                                sim_data = json_lib.loads(json_str)
                                await self._async_close_session()
                            else:
                                if num_retries > 0:
                                    self._access_token = None
                                    await self._async_close_session()
                                    sim_data = await self._get_sim_data(num_retries - 1)
                                else:
                                    msg = f"Request error {url}: {response.status}"
                                    code = 202
                                    raise _1nceError(msg, code)
                except aiohttp.ClientError as err:
                        msg = f"Connection error {url}: {err}"
                        code = 201
                        raise _1nceError(msg, code)
                except asyncio.TimeoutError:
                    msg = f"Connection timeout {url}"
                    code = 200
                    raise _1nceError(msg, code)

                if sim_data is not None:

                    # Converti la stringa in un oggetto datetime
                    exp_date_obj = datetime.strptime(json["expiry_date"], "%Y-%m-%d %H:%M:%S")

                    # Converti l'oggetto datetime nel formato desiderato
                    exp_date = exp_date_obj.strftime("%d-%m-%Y")
                    self._sim_data = {
                        SENSOR_VOLUME: json["volume"],
                        SENSOR_TOTAL_VOLUME: json["total_volume"],
                        SENSOR_EXPIRY_DATE: exp_date
                    }
                    self.debug(self._sim_data)

        return self._sim_data

    async def _get_access_token(self):

        if self._access_token is None:

            url = 'https://api.1nce.com/management-api/oauth/token'

            json = {
                "grant_type": "client_credentials"
            }

            user_pass_str = self._username + ":" + self._password
            base64_user_pass_bytes = base64.b64encode(bytes(user_pass_str, 'utf-8'))
            base64_user_pass_str = base64_user_pass_bytes.decode('utf-8')

            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "authorization": "Basic " + base64_user_pass_str
            }

            try:
                async with async_timeout.timeout(10):  # Timeout di 10 secondi
                    await self._async_init_session()
                    async with self._session.post(url, headers=headers) as response:
                        if response.status == 200:
                            json_str = response.text
                            json = json_lib.loads(json_str)
                            self._access_token = json["access_token"]
                        else:
                            msg = f"Request error {url}: {response.status}"
                            code = 102
                            raise _1nceError(msg, code)
            except aiohttp.ClientError as err:
                msg = f"Connection error {url}: {err}"
                code = 101
                raise _1nceError(msg, code)
            except asyncio.TimeoutError:
                msg = f"Connection timeout {url}"
                code = 100
                raise _1nceError(msg, code)

        return self._access_token

    async def test_connection(self):
        data = await self.fetch_data()
        return data is not None

    # ------------------------------------------------------------------------------------------------------------------
    # Session related methods
    # ------------------------------------------------------------------------------------------------------------------

    async def _async_init_session(self):
        """ Init session """
        if self._session is None:
            self._session = aiohttp.ClientSession()
            self.debug("Session started")

    async def _async_close_session(self):
        """ Close session """
        if self._session:
            await self._session.close()
            self._session = None
            self.debug("Session closed")


class _1nceAuthError(Exception):
    """Eccezione personalizzata che accetta un messaggio e un codice di errore."""

    def __init__(self, message, code):
        # Chiama il costruttore della classe base (Exception) con il messaggio di errore
        super().__init__(message)
        self.code = code

    def __str__(self):
        # Ritorna una rappresentazione stringa dell'errore, includendo il codice
        return f"[1nce Authentication Error {self.code}]: {self.args[0]}"


class _1nceError(Exception):
    """Eccezione personalizzata che accetta un messaggio e un codice di errore."""

    def __init__(self, message, code):
        # Chiama il costruttore della classe base (Exception) con il messaggio di errore
        super().__init__(message)
        self.code = code

    def __str__(self):
        # Ritorna una rappresentazione stringa dell'errore, includendo il codice
        return f"[1nce Error {self.code}]: {self.args[0]}"