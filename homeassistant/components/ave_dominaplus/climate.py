"""Climate platform for AVE DominaPlus."""

from __future__ import annotations

import logging
from typing import Any

from pyavedominaplus import (
    SEASON_SUMMER,
    SEASON_WINTER,
    THERMOSTAT_MODE_AUTO,
    THERMOSTAT_MODE_MANUAL,
    AVEDominaClient,
    DominaDevice,
    DominaThermostat,
)

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import CONF_HOST, UnitOfTemperature
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
    """Set up AVE DominaPlus climate entities."""
    client = entry.runtime_data.client
    host = entry.data[CONF_HOST]

    entities: list[AveDominaPlusClimate] = []
    for device in client.devices.values():
        if device.is_thermostat:
            thermostat = client.thermostats.get(device.id)
            if thermostat:
                entities.append(
                    AveDominaPlusClimate(
                        client, device, thermostat, host, entry.entry_id
                    )
                )

    async_add_entities(entities)


class AveDominaPlusClimate(AveDominaPlusEntity, ClimateEntity):
    """Representation of an AVE DominaPlus thermostat."""

    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.PRESET_MODE
    )
    _attr_preset_modes = ["auto", "manual"]
    _attr_min_temp = 5.0
    _attr_max_temp = 40.0
    _attr_target_temperature_step = 0.5
    _enable_turn_on_off_backwards_compatibility = False

    def __init__(
        self,
        client: AVEDominaClient,
        device: DominaDevice,
        thermostat: DominaThermostat,
        host: str,
        entry_id: str,
    ) -> None:
        """Initialize the climate entity."""
        super().__init__(client, device, host, entry_id)
        self._thermostat = thermostat

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self._thermostat.temperature or None

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        return self._thermostat.set_point or None

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current HVAC mode."""
        if self._thermostat.is_off:
            return HVACMode.OFF
        if self._thermostat.is_heating:
            return HVACMode.HEAT
        return HVACMode.COOL

    @property
    def preset_mode(self) -> str:
        """Return the current preset mode."""
        if self._thermostat.is_manual_mode:
            return "manual"
        return "auto"

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set the target temperature."""
        temperature: float | None = kwargs.get("temperature")
        if temperature is not None:
            await self._client.set_thermostat_set_point(self._device.id, temperature)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set the HVAC mode (season or off)."""
        if hvac_mode == HVACMode.OFF:
            await self._client.turn_off_thermostat(self._device.id)
        elif hvac_mode == HVACMode.HEAT:
            if self._thermostat.is_off:
                await self._client.turn_on_thermostat(self._device.id)
            await self._client.set_thermostat_season(self._device.id, SEASON_WINTER)
        elif hvac_mode == HVACMode.COOL:
            if self._thermostat.is_off:
                await self._client.turn_on_thermostat(self._device.id)
            await self._client.set_thermostat_season(self._device.id, SEASON_SUMMER)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode (auto/manual)."""
        if preset_mode == "manual":
            await self._client.set_thermostat_mode(
                self._device.id, THERMOSTAT_MODE_MANUAL
            )
        else:
            await self._client.set_thermostat_mode(
                self._device.id, THERMOSTAT_MODE_AUTO
            )

    @callback
    def _handle_update(self, event_type: str, data: dict[str, Any]) -> None:
        """Handle thermostat updates."""
        device_id = data.get("device_id")
        if device_id != self._device.id:
            return

        if event_type in (
            "thermostat_temperature",
            "thermostat_setpoint",
            "thermostat_season",
            "thermostat_mode",
            "thermostat_fan_level",
            "thermostat_local_off",
            "thermostat_full_status",
            "device_status",
        ):
            self.async_write_ha_state()
