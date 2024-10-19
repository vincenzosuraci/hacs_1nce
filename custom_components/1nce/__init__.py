import logging
_LOGGER = logging.getLogger(__name__)

from .const import (
    SENSOR,
    DOMAIN,
    CONF_ICCID,
    CONF_USERNAME,
    CONF_PASSWORD,
)

try:
    from homeassistant.core import HomeAssistant
    from homeassistant.config_entries import ConfigEntry
    from .sensor import async_setup_entry as async_setup_sensors

    from ._1nce_device import _1nceDevice
    from .coordinator import _1nceCoordinator

    async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:

        iccid = config_entry.data[CONF_ICCID]
        username = config_entry.data[CONF_USERNAME]
        password = config_entry.data[CONF_PASSWORD]

        _1nce = _1nceDevice(params={
            "username": username,
            "password": password,
            "iccid": iccid
        })

        # Inizializza il coordinatore
        coordinator = _1nceCoordinator(hass, _1nce)

        # Memorizza il coordinatore nel registro dei dati di Home Assistant
        hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = coordinator

        # Esegui il primo aggiornamento
        await coordinator.async_config_entry_first_refresh()

        # Utilizza `async_add_platform` per configurare la piattaforma sensor
        # hass.config_entries.async_setup_platforms(config_entry, [SENSOR])
        await hass.config_entries.async_forward_entry_setups(config_entry, [SENSOR])

        return True


    async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
        await hass.config_entries.async_forward_entry_unload(config_entry, SENSOR)
        hass.data[DOMAIN].pop(config_entry.entry_id)

        return True

except ModuleNotFoundError:
    print("Execution outside the Home Assistant environment")