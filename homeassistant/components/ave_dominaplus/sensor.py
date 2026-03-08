"""Sensor platform for AVE DominaPlus."""

from __future__ import annotations

import logging
from typing import Any

from pyavedominaplus import AVEDominaClient, DominaDevice, DominaThermostat

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import CONF_HOST, PERCENTAGE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import AveDominaPlusConfigEntry
from .entity import AveDominaPlusEntity

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AveDominaPlusConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up AVE DominaPlus sensors."""
    client = entry.runtime_data.client
    host = entry.data[CONF_HOST]

    entities: list[AveDominaPlusHumiditySensor] = []
    for device in client.devices.values():
        if device.is_thermostat:
            thermostat = client.thermostats.get(device.id)
            if thermostat and thermostat.humidity_enabled:
                entities.append(
                    AveDominaPlusHumiditySensor(
                        client, device, thermostat, host, entry.entry_id
                    )
                )

    async_add_entities(entities)


class AveDominaPlusHumiditySensor(AveDominaPlusEntity, SensorEntity):
    """Representation of an AVE DominaPlus humidity sensor."""

    _attr_translation_key = "humidity"
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        client: AVEDominaClient,
        device: DominaDevice,
        thermostat: DominaThermostat,
        host: str,
        entry_id: str,
    ) -> None:
        """Initialize the humidity sensor."""
        super().__init__(client, device, host, entry_id)
        self._thermostat = thermostat
        self._attr_unique_id = f"{host}_{device.id}_humidity"

    @property
    def native_value(self) -> int | None:
        """Return the humidity value."""
        if self._thermostat.humidity_value == 0:
            return None
        return self._thermostat.humidity_value

    @callback
    def _handle_update(self, event_type: str, data: dict[str, Any]) -> None:
        """Handle humidity updates."""
        if data.get("device_id") != self._device.id:
            return
        if event_type in ("humidity", "thermostat_full_status"):
            self.async_write_ha_state()
