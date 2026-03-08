"""Light platform for AVE DominaPlus."""

from __future__ import annotations

import logging
from typing import Any

from pyavedominaplus import AVEDominaClient, DominaDevice

from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode, LightEntity
from homeassistant.const import CONF_HOST
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
    """Set up AVE DominaPlus lights."""
    client = entry.runtime_data.client
    host = entry.data[CONF_HOST]

    entities: list[AveDominaPlusLight] = []
    for device in client.devices.values():
        if device.is_light:
            entities.append(
                AveDominaPlusLight(
                    client, device, host, entry.entry_id, is_dimmer=False
                )
            )
        elif device.is_dimmer:
            entities.append(
                AveDominaPlusLight(client, device, host, entry.entry_id, is_dimmer=True)
            )

    async_add_entities(entities)


class AveDominaPlusLight(AveDominaPlusEntity, LightEntity):
    """Representation of an AVE DominaPlus light."""

    _attr_name = None

    def __init__(
        self,
        client: AVEDominaClient,
        device: DominaDevice,
        host: str,
        entry_id: str,
        is_dimmer: bool,
    ) -> None:
        """Initialize the light."""
        super().__init__(client, device, host, entry_id)
        self._is_dimmer = is_dimmer

        if is_dimmer:
            self._attr_color_mode = ColorMode.BRIGHTNESS
            self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
        else:
            self._attr_color_mode = ColorMode.ONOFF
            self._attr_supported_color_modes = {ColorMode.ONOFF}

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        return self._device.is_on

    @property
    def brightness(self) -> int | None:
        """Return the brightness of this light (0-255)."""
        if not self._is_dimmer:
            return None
        if self._device.current_value == 0:
            return 0
        return round(self._device.current_value * 255 / 31)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        if self._is_dimmer:
            if ATTR_BRIGHTNESS in kwargs:
                level = round(kwargs[ATTR_BRIGHTNESS] * 31 / 255)
                level = max(1, min(31, level))
                await self._client.set_dimmer_level(self._device.id, level)
            else:
                await self._client.turn_on_dimmer(self._device.id)
        else:
            await self._client.turn_on_light(self._device.id)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        if self._is_dimmer:
            await self._client.turn_off_dimmer(self._device.id)
        else:
            await self._client.turn_off_light(self._device.id)

    @callback
    def _process_update(self, event_type: str, data: dict[str, Any]) -> None:
        """Process a device status update."""
        if event_type == "device_status":
            self._device.update_status(data["status"])
