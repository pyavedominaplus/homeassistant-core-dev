"""Tests for the AVE DominaPlus diagnostics."""

import pytest

from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.components.diagnostics import get_diagnostics_for_config_entry
from tests.typing import ClientSessionGenerator


@pytest.mark.usefixtures("mock_client")
async def test_diagnostics(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    init_integration: MockConfigEntry,
) -> None:
    """Test diagnostics returns expected data."""
    diagnostics = await get_diagnostics_for_config_entry(
        hass, hass_client, init_integration
    )

    assert "devices" in diagnostics
    assert "thermostats" in diagnostics
    assert "areas" in diagnostics

    # Verify devices
    assert "101" in diagnostics["devices"]
    assert diagnostics["devices"]["101"]["name"] == "Living Room Light"
    assert diagnostics["devices"]["101"]["device_type"] == 1

    assert "201" in diagnostics["devices"]
    assert diagnostics["devices"]["201"]["name"] == "Kitchen Shutter"

    # Verify thermostats
    assert "301" in diagnostics["thermostats"]
    thermo = diagnostics["thermostats"]["301"]
    assert thermo["name"] == "Living Room Thermostat"
    assert thermo["temperature"] == 21.5
    assert thermo["set_point"] == 22.0
    assert thermo["season"] == 1
    assert thermo["humidity_enabled"] is True
    assert thermo["humidity_value"] == 55
    assert "manual_set_point" in thermo

    # Verify areas
    assert "1" in diagnostics["areas"]
    assert diagnostics["areas"]["1"]["name"] == "Ground Floor"
