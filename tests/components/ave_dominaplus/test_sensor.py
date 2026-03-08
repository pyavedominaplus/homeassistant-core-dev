"""Tests for the AVE DominaPlus sensor platform."""

from unittest.mock import MagicMock

import pytest

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from tests.common import MockConfigEntry


@pytest.mark.usefixtures("mock_client")
async def test_humidity_sensor(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test humidity sensor entity is created and reports value."""
    # Sensor is disabled by default, so check entity registry
    entry = entity_registry.async_get("sensor.living_room_thermostat_humidity")

    assert entry is not None
    assert entry.disabled_by is not None  # Disabled by default
    assert entry.unique_id == "192.168.1.100_301_humidity"


@pytest.mark.usefixtures("entity_registry_enabled_by_default", "mock_client")
async def test_humidity_sensor_enabled(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test humidity sensor reports values when enabled."""
    entity_id = "sensor.living_room_thermostat_humidity"

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "55"
    assert state.attributes["device_class"] == SensorDeviceClass.HUMIDITY
    assert state.attributes["unit_of_measurement"] == PERCENTAGE


@pytest.mark.usefixtures("entity_registry_enabled_by_default", "mock_client")
async def test_humidity_sensor_update(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_client: MagicMock,
    mock_thermostats,
) -> None:
    """Test humidity sensor updates from callback."""
    entity_id = "sensor.living_room_thermostat_humidity"
    callbacks = [
        call[0][0] for call in mock_client.register_update_callback.call_args_list
    ]

    mock_thermostats["301"].humidity_value = 62
    for cb in callbacks:
        cb("humidity", {"device_id": "301", "humidity": 62})
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == "62"


@pytest.mark.usefixtures("entity_registry_enabled_by_default", "mock_client")
async def test_humidity_sensor_ignores_wrong_device(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_client: MagicMock,
    mock_thermostats,
) -> None:
    """Test humidity sensor ignores updates for other devices."""
    entity_id = "sensor.living_room_thermostat_humidity"
    callbacks = [
        call[0][0] for call in mock_client.register_update_callback.call_args_list
    ]

    initial_state = hass.states.get(entity_id).state

    # Fire update for a different device_id
    for cb in callbacks:
        cb("humidity", {"device_id": "999", "humidity": 99})
    await hass.async_block_till_done()

    # State should be unchanged
    assert hass.states.get(entity_id).state == initial_state


@pytest.mark.usefixtures("entity_registry_enabled_by_default", "mock_client")
async def test_humidity_sensor_zero_is_none(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_client: MagicMock,
    mock_thermostats,
) -> None:
    """Test humidity sensor returns None when value is zero."""
    entity_id = "sensor.living_room_thermostat_humidity"
    callbacks = [
        call[0][0] for call in mock_client.register_update_callback.call_args_list
    ]

    mock_thermostats["301"].humidity_value = 0
    for cb in callbacks:
        cb("humidity", {"device_id": "301", "humidity": 0})
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == "unknown"
