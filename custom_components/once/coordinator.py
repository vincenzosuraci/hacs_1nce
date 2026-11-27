"""DataUpdateCoordinator per una SIM 1NCE."""

import asyncio
from datetime import timedelta
import logging

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .once import OnceError, OnceAuthError

from .const import DOMAIN, UPDATE_INTERVAL_S, UPDATE_TIMEOUT_S

_LOGGER = logging.getLogger(__name__)


class OnceCoordinator(DataUpdateCoordinator):

    def __init__(self, hass, device):
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name=DOMAIN,
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=UPDATE_INTERVAL_S),
            always_update=True
        )
        self._device = device

    @property
    def device(self):
        return self._device

    async def _async_update_data(self):
        """Recupera i dati della SIM dall'API 1NCE."""
        try:
            async with asyncio.timeout(UPDATE_TIMEOUT_S):
                return await self.device.fetch_data()
        except OnceAuthError as err:
            # Raising ConfigEntryAuthFailed will cancel future updates
            # and start a config flow with SOURCE_REAUTH (async_step_reauth)
            raise ConfigEntryAuthFailed(str(err)) from err
        except OnceError as err:
            raise UpdateFailed(str(err)) from err
