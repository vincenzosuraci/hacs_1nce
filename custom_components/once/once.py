import asyncio
import base64
import time
from datetime import datetime

import aiohttp

from .const import CONF_ICCID, CONF_USERNAME, CONF_PASSWORD, SENSOR_VOLUME, SENSOR_TOTAL_VOLUME, SENSOR_EXPIRY_DATE

# ----------------------------------------------------------------------------------------------------------------------
# 1NCE Management API
# ----------------------------------------------------------------------------------------------------------------------
API_BASE_URL = "https://api.1nce.com/management-api"
TOKEN_URL = API_BASE_URL + "/oauth/token"
QUOTA_URL = API_BASE_URL + "/v1/sims/{iccid}/quota/data"

# Timeout di ogni singola richiesta HTTP (in secondi)
REQUEST_TIMEOUT_S = 10

# Formato legacy della data di scadenza (oggi l'API restituisce ISO 8601, es. "2034-12-02T00:00:00Z")
LEGACY_EXPIRY_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Codici HTTP restituiti dall'endpoint del token in caso di credenziali errate
AUTH_ERROR_STATUSES = (400, 401, 403)


# ----------------------------------------------------------------------------------------------------------------------
#
# 1nce
#
# ----------------------------------------------------------------------------------------------------------------------

class Once:
    """Client asincrono della 1NCE Management API (indipendente da Home Assistant)."""

    # Numero di nuovi tentativi (con un nuovo token) se la richiesta della quota fallisce
    MAX_NUM_RETRIES = 1

    # Minimo tempo che deve trascorrere tra due interrogazioni successive all'API
    MIN_INTERVAL_S = 2

    def __init__(self, params=None, session=None):
        """
        :param params: dict con le chiavi CONF_ICCID, CONF_USERNAME, CONF_PASSWORD
        :param session: aiohttp.ClientSession opzionale. Se fornita (es. quella condivisa di Home Assistant)
                        viene riutilizzata e mai chiusa; altrimenti ne viene creata e chiusa una ad ogni lettura.
        """
        params = params or {}
        self._iccid = params.get(CONF_ICCID)
        self._username = params.get(CONF_USERNAME)
        self._password = params.get(CONF_PASSWORD)

        self._session = session
        self._own_session = session is None

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
        """Ritorna i dati della SIM: {SENSOR_VOLUME, SENSOR_TOTAL_VOLUME, SENSOR_EXPIRY_DATE}."""
        if (
            self._sim_data is not None
            and self._last_update_timestamp is not None
            and time.time() < self._last_update_timestamp + self.MIN_INTERVAL_S
        ):
            return self._sim_data

        sim_data = await self._get_sim_data(self.MAX_NUM_RETRIES)

        self._sim_data = self._parse_sim_data(sim_data)
        self._last_update_timestamp = time.time()
        self.debug(self._sim_data)

        return self._sim_data

    async def test_connection(self):
        data = await self.fetch_data()
        return data is not None

    # ------------------------------------------------------------------------------------------------------------------
    # API calls
    # ------------------------------------------------------------------------------------------------------------------

    async def _get_sim_data(self, num_retries):
        url = QUOTA_URL.format(iccid=self._iccid)
        status = None

        try:
            access_token = await self._get_access_token()

            headers = {
                "accept": "application/json",
                "authorization": "Bearer " + access_token
            }

            try:
                async with asyncio.timeout(REQUEST_TIMEOUT_S):
                    async with self._get_session().get(url, headers=headers) as response:
                        status = response.status
                        if status == 200:
                            return await response.json()
            except aiohttp.ClientError as err:
                raise OnceError(f"Connection error {url}: {err}", 201) from err
            except TimeoutError as err:
                raise OnceError(f"Connection timeout {url}", 200) from err
        finally:
            await self._async_close_session()

        if num_retries > 0:
            # Il token potrebbe essere scaduto: lo si scarta e si riprova
            self.debug(f"Request error {url}: {status}, retrying with a new access token")
            self._access_token = None
            return await self._get_sim_data(num_retries - 1)

        raise OnceError(f"Request error {url}: {status}", 202)

    async def _get_access_token(self):
        if self._access_token is not None:
            return self._access_token

        url = TOKEN_URL

        user_pass_str = self._username + ":" + self._password
        base64_user_pass_str = base64.b64encode(user_pass_str.encode("utf-8")).decode("utf-8")

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": "Basic " + base64_user_pass_str
        }

        json = {
            "grant_type": "client_credentials"
        }

        try:
            async with asyncio.timeout(REQUEST_TIMEOUT_S):
                async with self._get_session().post(url, headers=headers, json=json) as response:
                    status = response.status
                    if status == 200:
                        json_data = await response.json()
                        access_token = json_data.get("access_token")
                        if not access_token:
                            raise OnceError(f"Missing access token in response {url}", 102)
                        self._access_token = access_token
                        return self._access_token
        except aiohttp.ClientError as err:
            raise OnceError(f"Connection error {url}: {err}", 101) from err
        except TimeoutError as err:
            raise OnceError(f"Connection timeout {url}", 100) from err

        if status in AUTH_ERROR_STATUSES:
            raise OnceAuthError(f"Authentication failed {url}: {status}", 103)

        raise OnceError(f"Request error {url}: {status}", 102)

    @staticmethod
    def _parse_sim_data(sim_data):
        """Converte la risposta dell'API nel dict usato dai sensori (gestisce anche risposte vuote)."""
        sim_data = sim_data or {}

        return {
            SENSOR_VOLUME: sim_data.get("volume"),
            SENSOR_TOTAL_VOLUME: sim_data.get("total_volume"),
            SENSOR_EXPIRY_DATE: Once._parse_expiry_date(sim_data.get("expiry_date"))
        }

    @staticmethod
    def _parse_expiry_date(value):
        """Converte la data di scadenza in datetime.date.

        Accetta sia ISO 8601 ("2034-12-02T00:00:00Z", formato attuale dell'API)
        sia il formato legacy "2034-12-02 00:00:00". Ritorna None se il valore manca o non è valido.
        """
        if not value or not isinstance(value, str):
            return None
        value = value.strip()
        try:
            # Python >= 3.11 accetta anche il suffisso "Z"
            return datetime.fromisoformat(value).date()
        except ValueError:
            pass
        try:
            return datetime.strptime(value, LEGACY_EXPIRY_DATE_FORMAT).date()
        except ValueError:
            return None

    # ------------------------------------------------------------------------------------------------------------------
    # Session related methods
    # ------------------------------------------------------------------------------------------------------------------

    def _get_session(self):
        """Ritorna la sessione HTTP, creandone una propria se non è stata fornita."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _async_close_session(self):
        """Chiude la sessione solo se è stata creata da questa classe."""
        if self._own_session and self._session is not None:
            await self._session.close()
            self._session = None


class OnceError(Exception):
    """Eccezione personalizzata che accetta un messaggio e un codice di errore."""

    def __init__(self, message, code):
        # Chiama il costruttore della classe base (Exception) con il messaggio di errore
        super().__init__(message)
        self.code = code

    def __str__(self):
        # Ritorna una rappresentazione stringa dell'errore, includendo il codice
        return f"[1nce Error {self.code}]: {self.args[0]}"


class OnceAuthError(Exception):
    """Credenziali non valide: viene mappata su ConfigEntryAuthFailed (avvia la riautenticazione)."""

    def __init__(self, message, code):
        # Chiama il costruttore della classe base (Exception) con il messaggio di errore
        super().__init__(message)
        self.code = code

    def __str__(self):
        # Ritorna una rappresentazione stringa dell'errore, includendo il codice
        return f"[1nce Authentication Error {self.code}]: {self.args[0]}"
