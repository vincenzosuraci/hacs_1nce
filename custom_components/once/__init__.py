import logging
_LOGGER = logging.getLogger(__name__)

from .const import (
    PLATFORMS,
    DOMAIN,
    CONF_ICCID,
    CONF_USERNAME,
    CONF_PASSWORD,
)

try:
    from homeassistant.core import HomeAssistant
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.helpers.aiohttp_client import async_get_clientsession

    from .once_device import OnceDevice
    from .coordinator import OnceCoordinator

    async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:

        iccid = config_entry.data[CONF_ICCID]

        # Le config entry create con versioni precedenti non hanno uno unique_id
        if config_entry.unique_id is None:
            hass.config_entries.async_update_entry(config_entry, unique_id=iccid)

        device = OnceDevice(
            params={
                CONF_ICCID: iccid,
                CONF_USERNAME: config_entry.data[CONF_USERNAME],
                CONF_PASSWORD: config_entry.data[CONF_PASSWORD],
            },
            session=async_get_clientsession(hass)
        )

        # Inizializza il coordinatore ed esegue la prima lettura
        coordinator = OnceCoordinator(hass, device)
        await coordinator.async_config_entry_first_refresh()

        # Memorizza il coordinatore nel registro dei dati di Home Assistant
        hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = coordinator

        await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

        return True


    async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
        unload_ok = await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
        if unload_ok:
            hass.data[DOMAIN].pop(config_entry.entry_id, None)

        return unload_ok

except ModuleNotFoundError:
    print("Execution outside the Home Assistant environment")
