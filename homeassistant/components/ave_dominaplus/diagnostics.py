"""Diagnostics support for AVE DominaPlus."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from . import AveDominaPlusConfigEntry


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: AveDominaPlusConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    client = entry.runtime_data.client

    return {
        "devices": {
            device_id: {
                "name": device.name,
                "device_type": device.device_type,
                "app_type": device.app_type,
                "current_value": device.current_value,
                "maps": device.maps,
            }
            for device_id, device in client.devices.items()
        },
        "thermostats": {
            thermo_id: {
                "name": thermostat.name,
                "temperature": thermostat.temperature,
                "set_point": thermostat.set_point,
                "season": thermostat.season,
                "mode": thermostat.mode,
                "fan_level": thermostat.fan_level,
                "local_off": thermostat.local_off,
                "manual_set_point": thermostat.manual_set_point,
                "humidity_enabled": thermostat.humidity_enabled,
                "humidity_value": thermostat.humidity_value,
            }
            for thermo_id, thermostat in client.thermostats.items()
        },
        "areas": {
            area_id: {
                "name": area.name,
                "order": area.order,
                "is_visible": area.is_visible,
            }
            for area_id, area in client.areas.items()
        },
    }
