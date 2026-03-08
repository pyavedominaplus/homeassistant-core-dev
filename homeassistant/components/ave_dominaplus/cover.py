"""Cover platform for AVE DominaPlus."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
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
    """Set up AVE DominaPlus covers."""
    client = entry.runtime_data.client
    host = entry.data[CONF_HOST]

    entities: list[AveDominaPlusCover] = [
        AveDominaPlusCover(client, device, host, entry.entry_id)
        for device in client.devices.values()
        if device.is_shutter
    ]

    async_add_entities(entities)


class AveDominaPlusCover(AveDominaPlusEntity, CoverEntity):
    """Representation of an AVE DominaPlus shutter/cover."""

    _attr_name = None
    _attr_device_class = CoverDeviceClass.SHUTTER
    _attr_supported_features = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.STOP
        | CoverEntityFeature.SET_POSITION
    )

    @property
    def current_cover_position(self) -> int | None:
        """Return the current position of the cover.

        The DominaPlus protocol does not report exact positions, so we
        synthesize: 0 = closed, 100 = open, 50 = stopped/partially open.
        """
        if self._device.is_closed:
            return 0
        if self._device.is_open:
            return 100
        if self._device.is_stopped:
            return 50
        return None

    @property
    def is_closed(self) -> bool | None:
        """Return true if cover is closed."""
        return self._device.is_closed

    @property
    def is_opening(self) -> bool | None:
        """Return true if cover is opening."""
        return self._device.is_opening

    @property
    def is_closing(self) -> bool | None:
        """Return true if cover is closing."""
        return self._device.is_closing

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        await self._client.open_shutter(self._device.id)

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        await self._client.close_shutter(self._device.id)

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        await self._client.stop_shutter(self._device.id)

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move cover to a position. Mapped to open/close/stop."""
        position: int = kwargs[ATTR_POSITION]
        if position <= 10:
            await self._client.close_shutter(self._device.id)
        elif position >= 90:
            await self._client.open_shutter(self._device.id)
        else:
            await self._client.stop_shutter(self._device.id)

    @callback
    def _process_update(self, event_type: str, data: dict[str, Any]) -> None:
        """Process a device status update."""
        if event_type == "device_status":
            self._device.update_status(data["status"])
