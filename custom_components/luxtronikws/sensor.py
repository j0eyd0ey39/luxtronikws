"""Platform for sensor integration."""
from __future__ import annotations
import locale

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

from config.custom_components.luxtronikws.coordinator import LuxtronikCoordinator

from config.custom_components.luxtronikws.const import (
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
    entityDicts = localCoordinator.listEntities()

    entities = []
    for dict in entityDicts:
        entities.append(LuxtronikEntity(dict, localCoordinator, hass))

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
        _LOGGER.debug("Luxtronik entity "+entityDict["name"] +" created created")

    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def unique_id(self) -> str | None:
        return self._attr_device_id + str(self._attr_index)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        root = self.coordinator.data[self._attr_group]
        listed = list(root)
        item = listed[self._attr_index]
        valuestr = list(item)[1].text
        valuestr = valuestr[:len(valuestr)-2]
        point = locale.localeconv()["decimal_point"]
        valuestr.replace(".", point)
        valuestr.replace(",", point)

        self._attr_native_value = valuestr
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

