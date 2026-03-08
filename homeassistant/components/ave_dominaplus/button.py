"""Button platform for AVE DominaPlus."""

from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
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
    """Set up AVE DominaPlus scenario buttons."""
    client = entry.runtime_data.client
    host = entry.data[CONF_HOST]

    async_add_entities(
        AveDominaPlusScenarioButton(client, device, host, entry.entry_id)
        for device in client.devices.values()
        if device.is_scenario
    )


class AveDominaPlusScenarioButton(AveDominaPlusEntity, ButtonEntity):
    """Representation of an AVE DominaPlus scenario button."""

    _attr_translation_key = "scenario"

    async def async_press(self) -> None:
        """Activate the scenario."""
        await self._client.activate_scenario(self._device.id)
