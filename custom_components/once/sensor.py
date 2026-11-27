import logging
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfInformation
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, DEVICE_MANUFACTURER, SENSOR_VOLUME, SENSOR_TOTAL_VOLUME, SENSOR_EXPIRY_DATE
from .coordinator import OnceCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class OnceSensorEntityDescription(SensorEntityDescription):
    """Descrizione di un sensore 1NCE.

    - key: suffisso dello unique_id (non modificarlo: cambierebbe lo unique_id delle entità esistenti)
    - data_key: chiave del dict restituito da Once.fetch_data()
    - translation_key: nome dell'entità in translations/*.json
    """

    data_key: str


SENSOR_DESCRIPTIONS = (
    OnceSensorEntityDescription(
        key="volume",
        data_key=SENSOR_VOLUME,
        translation_key="volume",
        icon="mdi:web",
        native_unit_of_measurement=UnitOfInformation.MEGABYTES,
        suggested_display_precision=6,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    OnceSensorEntityDescription(
        key="total_volume",
        data_key=SENSOR_TOTAL_VOLUME,
        translation_key="total_volume",
        icon="mdi:web",
        native_unit_of_measurement=UnitOfInformation.MEGABYTES,
        suggested_display_precision=0,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    OnceSensorEntityDescription(
        key="expiry_date",
        data_key=SENSOR_EXPIRY_DATE,
        translation_key="expiry_date",
        icon="mdi:calendar-clock",
        # I sensori di tipo DATE non possono avere state_class né unità di misura
        device_class=SensorDeviceClass.DATE,
    ),
)


class OnceSensor(CoordinatorEntity[OnceCoordinator], SensorEntity):

    _attr_has_entity_name = True

    entity_description: OnceSensorEntityDescription

    def __init__(
        self,
        coordinator: OnceCoordinator,
        device_id: str,
        device_info: DeviceInfo,
        description: OnceSensorEntityDescription
    ):
        """Inizializza il sensore."""
        super().__init__(coordinator)

        self.entity_description = description
        self._attr_unique_id = f"{device_id}_{description.key}"
        self._attr_device_info = device_info

    @property
    def native_value(self):
        """Ritorna il valore attuale del sensore."""
        data = self.coordinator.data or {}
        return data.get(self.entity_description.data_key)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Configura i sensori da una config entry."""
    coordinator: OnceCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    device_name = await coordinator.device.get_name()
    device_id = await coordinator.device.get_id()

    device_info = DeviceInfo(
        identifiers={(DOMAIN, device_id)},
        name=device_name,
        manufacturer=DEVICE_MANUFACTURER
    )

    async_add_entities(
        OnceSensor(coordinator, device_id, device_info, description)
        for description in SENSOR_DESCRIPTIONS
    )
