"""Base entity for AVE DominaPlus."""

from __future__ import annotations

from typing import Any

from pyavedominaplus import AVEDominaClient, DominaDevice
from pyavedominaplus.const import CONN_STATUS_OPEN

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, SIGNAL_CONNECTION_STATE

DEVICE_TYPE_NAMES: dict[int, str] = {
    1: "Light",
    2: "Dimmer",
    3: "Shutter",
    4: "Thermostat",
    5: "Economizer",
    6: "Scenario",
    9: "Energy Meter",
    16: "Shutter",
    19: "Shutter",
    22: "Light",
}


class AveDominaPlusEntity(Entity):
    """Base class for AVE DominaPlus entities."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        client: AVEDominaClient,
        device: DominaDevice,
        host: str,
        entry_id: str,
    ) -> None:
        """Initialize the entity."""
        self._client = client
        self._device = device
        self._entry_id = entry_id
        self._host = host
        self._attr_available = True
        self._attr_unique_id = f"{host}_{device.id}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{host}_{device.id}")},
            name=device.name,
            manufacturer="AVE",
            model=f"DominaPlus {DEVICE_TYPE_NAMES.get(device.device_type, 'Device')}",
            via_device=(DOMAIN, host),
        )

    async def async_added_to_hass(self) -> None:
        """Register callbacks when entity is added."""
        self.async_on_remove(self._client.register_update_callback(self._handle_update))
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{SIGNAL_CONNECTION_STATE}_{self._entry_id}",
                self._handle_connection_state,
            )
        )

    @callback
    def _handle_connection_state(self, status: str) -> None:
        """Handle connection state changes."""
        self._attr_available = status == CONN_STATUS_OPEN
        self.async_write_ha_state()

    @callback
    def _handle_update(self, event_type: str, data: dict[str, Any]) -> None:
        """Handle device updates from the library."""
        if data.get("device_id") == self._device.id:
            self._process_update(event_type, data)
            self.async_write_ha_state()

    @callback
    def _process_update(self, event_type: str, data: dict[str, Any]) -> None:
        """Process a device update. Override in subclasses."""
