"""Example integration using DataUpdateCoordinator."""

from datetime import timedelta
import logging

import async_timeout

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

import importlib

# Importa il modulo 1nce.py da 1nce_account
module_1nce = importlib.import_module("_1nce")

# Ottieni la classe _1nceCrawler dal modulo importato
_1nceAuthError = getattr(module_1nce, '_1nceAuthError')
_1nceError = getattr(module_1nce, '_1nceError')

from .const import DOMAIN, UPDATE_INTERVAL_S

_LOGGER = logging.getLogger(__name__)


class _1nceCoordinator(DataUpdateCoordinator):

    def __init__(self, hass, _1nce):
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name=DOMAIN,
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=UPDATE_INTERVAL_S),
            # Set always_update to `False` if the data returned from the
            # api can be compared via `__eq__` to avoid duplicate updates
            # being dispatched to listeners
            always_update=True
        )
        self._1nce = _1nce

    @property
    def get_1nce(self):
        return self._1nce

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with async_timeout.timeout(10):
                # Grab active context variables to limit data required to be fetched from API
                # Note: using context is not required if there is no need or ability to limit
                # data retrieved from API.
                return await self._1nce.fetch_data()
        except _1nceAuthError as err:
            # Raising ConfigEntryAuthFailed will cancel future updates
            # and start a config flow with SOURCE_REAUTH (async_step_reauth)
            raise ConfigEntryAuthFailed from err
        except _1nceError as err:
            raise UpdateFailed(f"{err}")
