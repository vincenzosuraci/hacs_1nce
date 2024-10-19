import logging
from homeassistant.components.sensor import SensorEntityDescription, SensorStateClass, SensorEntity
from homeassistant.const import UnitOfInformation
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.sensor import SensorDeviceClass
from .const import *
from .coordinator import _1nceCoordinator

_LOGGER = logging.getLogger(__name__)


class _1nceSensor(CoordinatorEntity, SensorEntity):

    def __init__(self, coordinator: _1nceCoordinator, device_info: DeviceInfo, description: SensorEntityDescription):
        """Inizializza il sensore."""
        super().__init__(coordinator)

        self._description = description
        self._attr_device_class = description.device_class
        self._attr_state_class = description.state_class
        self._attr_suggested_display_precision = description.suggested_display_precision
        self._attr_name = description.name
        self._attr_unique_id = f"{device_info["name"]}_{description.key}"
        self._attr_icon = description.icon
        self._attr_unit_of_measurement = description.unit_of_measurement
        self._attr_device_info = device_info
        self._attr_icon = description.icon

    @property
    def state(self):
        """Ritorna lo stato attuale del sensore."""
        return self.coordinator.data.get(self._description.name)

    @property
    def available(self):
        """Controlla se il sensore è disponibile."""
        return self.coordinator.last_update_success

    async def async_update(self):
        """Aggiorna manualmente lo stato del sensore."""
        await self.coordinator.async_request_refresh()

    async def async_added_to_hass(self):
        """Iscrive il sensore al coordinatore per gli aggiornamenti."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )


async def get_sensors(coordinator: _1nceCoordinator, device_info: DeviceInfo):

    sensors = []

    data = await coordinator.get_1nce.fetch_data()

    if data is not None:

        if SENSOR_VOLUME in data:
            sensors.append(_1nceSensor(coordinator, device_info, SensorEntityDescription(
                key=str(SENSOR_VOLUME).lower().replace(" ", "_"),
                name=SENSOR_VOLUME,
                icon="mdi:web",
                unit_of_measurement=UnitOfInformation.MEGABYTES,
                suggested_display_precision=6,
                device_class=SensorDeviceClass.DATA_SIZE,
                state_class=SensorStateClass.MEASUREMENT
            )))
        if SENSOR_TOTAL_VOLUME in data:
            sensors.append(_1nceSensor(coordinator, device_info, SensorEntityDescription(
                key=str(SENSOR_TOTAL_VOLUME).lower().replace(" ", "_"),
                name=SENSOR_TOTAL_VOLUME,
                icon="mdi:web",
                unit_of_measurement=UnitOfInformation.MEGABYTES,
                suggested_display_precision=0,
                device_class=SensorDeviceClass.DATA_SIZE,
                state_class=SensorStateClass.MEASUREMENT
            )))
        if SENSOR_EXPIRY_DATE in data:
            sensors.append(_1nceSensor(coordinator, device_info, SensorEntityDescription(
                key=str(SENSOR_EXPIRY_DATE).lower().replace(" ", "_"),
                name=SENSOR_EXPIRY_DATE,
                icon="mdi:calendar-clock",
                device_class=SensorDeviceClass.DATE,
                state_class=SensorStateClass.MEASUREMENT
            )))

    return sensors


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Configura i sensori da una config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    _1nce = coordinator.get_1nce

    device_manufacturer = DEVICE_MANUFACTURER
    device_name = await _1nce.get_name()
    device_id = await _1nce.get_id()

    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, device_id)},  # Usa un identificativo unico per il router
        manufacturer=device_manufacturer,
        name=device_name,
    )

    device_info = DeviceInfo(
        identifiers={(DOMAIN, device_id)},
        name=device_name,
        manufacturer=device_name,
        model=device_model,  # Modello del modem (aggiorna con il modello corretto)
        sw_version=device_sw_version,  # Versione del software, può essere dinamico se riesci a recuperarlo dal modem
        via_device=(DOMAIN, config_entry.entry_id),
    )

    sensors = await get_sensors(coordinator, device_info)

    async_add_entities(sensors)
