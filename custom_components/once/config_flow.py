import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, OptionsFlow
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig, TextSelectorType

from .const import DOMAIN, CONF_ICCID, CONF_USERNAME, CONF_PASSWORD
from .once import OnceError, OnceAuthError
from .once_device import OnceDevice

_LOGGER = logging.getLogger(__name__)

_PASSWORD_SELECTOR = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))

CREDENTIALS_SCHEMA = vol.Schema({
    vol.Required(CONF_USERNAME): str,
    vol.Required(CONF_PASSWORD): _PASSWORD_SELECTOR,
})

USER_SCHEMA = vol.Schema({
    vol.Required(CONF_ICCID): str,
}).extend(CREDENTIALS_SCHEMA.schema)


def _clean_input(user_input: dict) -> dict:
    """Rimuove spazi iniziali/finali dai campi testuali."""
    return {key: value.strip() if isinstance(value, str) else value for key, value in user_input.items()}


async def _async_try_connect(hass: HomeAssistant, data: dict) -> tuple[str | None, dict]:
    """Verifica le credenziali contro l'API 1NCE. Ritorna (titolo, errori)."""
    device = OnceDevice(
        params={
            CONF_ICCID: data[CONF_ICCID],
            CONF_USERNAME: data[CONF_USERNAME],
            CONF_PASSWORD: data[CONF_PASSWORD],
        },
        session=async_get_clientsession(hass)
    )
    try:
        if await device.test_connection():
            return await device.get_title(), {}
        return None, {"base": "cannot_connect"}
    except OnceAuthError as err:
        _LOGGER.debug("Authentication failed: %s", err)
        return None, {"base": "invalid_auth"}
    except OnceError as err:
        _LOGGER.debug("Connection failed: %s", err)
        return None, {"base": "cannot_connect"}
    except Exception:  # pylint: disable=broad-except
        _LOGGER.exception("Unexpected error while connecting to 1NCE")
        return None, {"base": "unknown"}


class OnceConfigFlow(ConfigFlow, domain=DOMAIN):
    """Gestisce il flusso di configurazione per la SIM 1nce"""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Primo passo: richiedi iccid della SIM, username e password dell'account"""
        errors = {}

        if user_input is not None:
            user_input = _clean_input(user_input)

            # Una config entry per ICCID
            await self.async_set_unique_id(user_input[CONF_ICCID])
            self._abort_if_unique_id_configured()

            title, errors = await _async_try_connect(self.hass, user_input)
            if not errors:
                return self.async_create_entry(title=title, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(USER_SCHEMA, user_input),
            errors=errors
        )

    async def async_step_reauth(self, entry_data):
        """Avviato da ConfigEntryAuthFailed quando le credenziali non sono più valide."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        """Richiede nuove credenziali per la SIM."""
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        errors = {}

        if user_input is not None:
            data = {**entry.data, **_clean_input(user_input)}
            _, errors = await _async_try_connect(self.hass, data)
            if not errors:
                return self.async_update_reload_and_abort(entry, data=data, reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=self.add_suggested_values_to_schema(
                CREDENTIALS_SCHEMA, {CONF_USERNAME: entry.data.get(CONF_USERNAME)}
            ),
            description_placeholders={CONF_ICCID: entry.data.get(CONF_ICCID)},
            errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OnceOptionsFlow(config_entry)


class OnceOptionsFlow(OptionsFlow):
    """Permette di modificare username e password (l'ICCID identifica la config entry e non si modifica)."""

    def __init__(self, config_entry):
        # Non si assegna self.config_entry (deprecato nelle versioni recenti di Home Assistant)
        self._entry = config_entry

    async def async_step_init(self, user_input=None):
        """Mostra il form delle opzioni."""
        errors = {}

        if user_input is not None:
            data = {**self._entry.data, **_clean_input(user_input)}
            _, errors = await _async_try_connect(self.hass, data)
            if not errors:
                self.hass.config_entries.async_update_entry(self._entry, data=data)
                self.hass.config_entries.async_schedule_reload(self._entry.entry_id)
                return self.async_create_entry(title="", data=dict(self._entry.options))

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                CREDENTIALS_SCHEMA, user_input or {CONF_USERNAME: self._entry.data.get(CONF_USERNAME)}
            ),
            description_placeholders={CONF_ICCID: self._entry.data.get(CONF_ICCID)},
            errors=errors
        )
