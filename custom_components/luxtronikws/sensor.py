"""Platform for sensor integration."""
from __future__ import annotations
from datetime import datetime, timedelta
import locale

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfTemperature,
    UnitOfPressure,
    UnitOfFrequency,
    PERCENTAGE,
    UnitOfPower,
    UnitOfEnergy,
    UnitOfTime)

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

from .coordinator import LuxtronikCoordinator

from .const import (
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    _LOGGER.info("sensor async setup entry called, title:" + config_entry.title)
    # Set up the sensor platform.

    localCoordinator = LuxtronikCoordinator(
        hass,
        config_entry.data["server"],
        config_entry.data["password"],
        config_entry.data["update_interval"],
    )
    await localCoordinator.async_config_entry_first_refresh()
    dicts = localCoordinator.listEntities()

    entities = []
    for dict in dicts["tempDicts"]:
        entities.append(LuxtronikTemperatureEntity(dict, localCoordinator, hass))
    for dict in dicts["pressureDicts"]:
        entities.append(LuxtronikPressureEntity(dict, localCoordinator, hass))
    for dict in dicts["frequencyDicts"]:
        entities.append(LuxtronikFrequencyEntity(dict, localCoordinator, hass))
    for dict in dicts["percentageDicts"]:
        entities.append(LuxtronikPercentageEntity(dict, localCoordinator, hass))
    for dict in dicts["powerDicts"]:
        entities.append(LuxtronikPowerEntity(dict, localCoordinator, hass))
    for dict in dicts["energyDicts"]:
        entities.append(LuxtronikEnergyEntity(dict, localCoordinator, hass))
    for dict in dicts["timeDicts"]:
        entities.append(LuxtronikTimeEntity(dict, localCoordinator, hass))
    for dict in dicts["stringDicts"]:
        entities.append(LuxtronikStringEntity(dict, localCoordinator, hass))
    for dict in dicts["counterDicts"]:
        entities.append(LuxtronikCounterEntity(dict, localCoordinator, hass))
    for dict in dicts["hourDicts"]:
        entities.append(LuxtronikHoursEntity(dict, localCoordinator, hass))

    async_add_entities(entities)

    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = localCoordinator
    _LOGGER.debug(
        "async setup entry finished, server:"
        + config_entry.data["server"]
        + " password:"
        + config_entry.data["password"]
        + " update interval:"
        + str(config_entry.data["update_interval"])
    )

class LuxtronikEntity(SensorEntity, CoordinatorEntity):
    """Representation of a Luxtronik Device entity"""
    def __init__(
        self, entityDict, coordinator, hass: HomeAssistant
    ) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator, context=entityDict["name"])
        self._attr_device_id = entityDict["name"]
        self._attr_hass = hass
        self._attr_device_model = entityDict["type"]
        self._attr_sw_version = entityDict["sw"]
        self._attr_index = entityDict["index"]
        self._attr_group = entityDict["group"]
        self._attr_has_entity_name = True
        self._attr_name = entityDict["name"]
        self._attr_friendly_name = entityDict["name"]
        self._attr_suffix_len = 0
        _LOGGER.debug("Luxtronik entity "+entityDict["name"] +" created")

    @property
    def unique_id(self) -> str | None:
        return self._attr_device_id + str(self._attr_index)

    def stripSuffix(self) -> str:
        """strip extra characters from data"""
        root = self.coordinator.data[self._attr_group]
        listed = list(root)
        item = listed[self._attr_index]
        valuestr = list(item)[1].text
        valuestr = valuestr[:len(valuestr)-self._attr_suffix_len]
        point = locale.localeconv()["decimal_point"]
        valuestr.replace(".", point)
        valuestr.replace(",", point)
        return valuestr


    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value = self.stripSuffix()
        _LOGGER.debug("Luxtronik sensor polled")
        self.async_write_ha_state()

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        manuf = "ACME"
        if self._attr_device_model.startswith("MSW"):
            manuf = "Alpha Innotec"

        return DeviceInfo(
            identifiers={(DOMAIN, self._attr_device_model)},
            name=self._attr_device_model,
            model=self._attr_device_model,
            suggested_area="Kitchen",
            manufacturer=manuf,
            sw_version=self._attr_sw_version,
        )

class LuxtronikTemperatureEntity(LuxtronikEntity):
    """Representation of a Luxtronik Device entity"""
    def __init__(
        self, entityDict, coordinator, hass: HomeAssistant
    ) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(entityDict, coordinator, hass)
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_suffix_len = 2
        _LOGGER.debug("Luxtronik entity "+entityDict["name"] +" created")

class LuxtronikPressureEntity(LuxtronikEntity):
    """Representation of a Luxtronik Device entity"""
    def __init__(
        self, entityDict, coordinator, hass: HomeAssistant
    ) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(entityDict, coordinator, hass)
        self._attr_native_unit_of_measurement = UnitOfPressure.BAR
        self._attr_device_class = SensorDeviceClass.PRESSURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_suffix_len = 4

class LuxtronikFrequencyEntity(LuxtronikEntity):
    """Representation of a Luxtronik Device entity"""
    def __init__(
        self, entityDict, coordinator, hass: HomeAssistant
    ) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(entityDict, coordinator, hass)
        self._attr_native_unit_of_measurement = UnitOfFrequency.HERTZ
        self._attr_device_class = SensorDeviceClass.FREQUENCY
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_suffix_len = 3

class LuxtronikPercentageEntity(LuxtronikEntity):
    """Representation of a Luxtronik Device entity"""
    def __init__(
        self, entityDict, coordinator, hass: HomeAssistant
    ) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(entityDict, coordinator, hass)
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_device_class = None
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_suffix_len = 2
        self._attr_icon = "mdi:pump" # the only known instances of luxtronik percentage entities are pumps

class LuxtronikPowerEntity(LuxtronikEntity):
    """Representation of a Luxtronik Device entity"""
    def __init__(
        self, entityDict, coordinator, hass: HomeAssistant
    ) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(entityDict, coordinator, hass)
        self._attr_native_unit_of_measurement = UnitOfPower.KILO_WATT
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_suffix_len = 3

class LuxtronikEnergyEntity(LuxtronikEntity):
    """Representation of a Luxtronik Device entity"""
    def __init__(
        self, entityDict, coordinator, hass: HomeAssistant
    ) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(entityDict, coordinator, hass)
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_suffix_len = 4

class LuxtronikStringEntity(LuxtronikEntity):
    """Representation of a Luxtronik Device entity"""
    def __init__(
        self, entityDict, coordinator, hass: HomeAssistant
    ) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(entityDict, coordinator, hass)
        self._attr_native_unit_of_measurement = None
        self._attr_device_class = None
        self._attr_state_class = None
        self._attr_suffix_len = 0

class LuxtronikTimeEntity(LuxtronikEntity):
    """Representation of a Luxtronik Device entity"""
    def __init__(
        self, entityDict, coordinator, hass: HomeAssistant
    ) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(entityDict, coordinator, hass)
        self._attr_native_unit_of_measurement = UnitOfTime.SECONDS
        self._attr_device_class = SensorDeviceClass.DURATION
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_icon = "mdi:clock-digital"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        root = self.coordinator.data[self._attr_group]
        listed = list(root)
        item = listed[self._attr_index]
        time = list(item)[1].text
        if time.count(':') == 1:
            h, m = map(int, time.split(':'))
            s = 0
        else:
            h, m, s = map(int, time.split(':'))

        delta = timedelta(hours=h, minutes=m, seconds=s)
        self._attr_native_value = str(delta.total_seconds())
        _LOGGER.debug("Luxtronik sensor polled")
        self.async_write_ha_state()

class LuxtronikHoursEntity(LuxtronikEntity):
    """Representation of a Luxtronik Device entity"""
    def __init__(
        self, entityDict, coordinator, hass: HomeAssistant
    ) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(entityDict, coordinator, hass)
        self._attr_native_unit_of_measurement = UnitOfTime.HOURS
        self._attr_suggested_unit_of_measurement = UnitOfTime.HOURS
        self._attr_suggested_display_precision = 0
        self._attr_device_class = None
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_suffix_len = 1
        self._attr_icon = "mdi:counter"

class LuxtronikCounterEntity(LuxtronikEntity):
    """Representation of a Luxtronik Device entity"""
    def __init__(
        self, entityDict, coordinator, hass: HomeAssistant
    ) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(entityDict, coordinator, hass)
        self._attr_native_unit_of_measurement = None
        self._attr_device_class = None
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_suffix_len = 0
        self._attr_icon = "mdi:counter"