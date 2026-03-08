"""Tests for the AVE DominaPlus climate platform."""

from unittest.mock import MagicMock

import pytest

from homeassistant.components.climate import (
    ATTR_HVAC_MODE,
    ATTR_PRESET_MODE,
    ATTR_TEMPERATURE,
    DOMAIN as CLIMATE_DOMAIN,
    SERVICE_SET_HVAC_MODE,
    SERVICE_SET_PRESET_MODE,
    SERVICE_SET_TEMPERATURE,
    HVACMode,
)
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry


@pytest.mark.usefixtures("mock_client")
async def test_climate_initial_state(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test climate entity reports correct initial state."""
    entity_id = "climate.living_room_thermostat"

    state = hass.states.get(entity_id)
    assert state is not None
    # season=1 (winter) and local_off=0 -> HEAT
    assert state.state == HVACMode.HEAT
    assert state.attributes["current_temperature"] == 21.5
    assert state.attributes["temperature"] == 22.0
    assert state.attributes["preset_mode"] == "auto"


@pytest.mark.usefixtures("mock_client")
async def test_climate_set_temperature(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_client: MagicMock,
) -> None:
    """Test setting target temperature."""
    entity_id = "climate.living_room_thermostat"

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {ATTR_ENTITY_ID: entity_id, ATTR_TEMPERATURE: 23.5},
        blocking=True,
    )

    mock_client.set_thermostat_set_point.assert_awaited_once_with("301", 23.5)


@pytest.mark.usefixtures("mock_client")
async def test_climate_set_hvac_mode_off(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_client: MagicMock,
) -> None:
    """Test setting HVAC mode to off."""
    entity_id = "climate.living_room_thermostat"

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: entity_id, ATTR_HVAC_MODE: HVACMode.OFF},
        blocking=True,
    )

    mock_client.turn_off_thermostat.assert_awaited_once_with("301")


@pytest.mark.usefixtures("mock_client")
async def test_climate_set_hvac_mode_heat(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_client: MagicMock,
) -> None:
    """Test setting HVAC mode to heat sets season to winter."""
    entity_id = "climate.living_room_thermostat"

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: entity_id, ATTR_HVAC_MODE: HVACMode.HEAT},
        blocking=True,
    )

    # Already on, so no turn_on call
    mock_client.turn_on_thermostat.assert_not_awaited()
    mock_client.set_thermostat_season.assert_awaited_once_with("301", 1)


@pytest.mark.usefixtures("mock_client")
async def test_climate_set_hvac_mode_cool(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_client: MagicMock,
) -> None:
    """Test setting HVAC mode to cool sets season to summer."""
    entity_id = "climate.living_room_thermostat"

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: entity_id, ATTR_HVAC_MODE: HVACMode.COOL},
        blocking=True,
    )

    mock_client.turn_on_thermostat.assert_not_awaited()
    mock_client.set_thermostat_season.assert_awaited_once_with("301", 0)


@pytest.mark.usefixtures("mock_client")
async def test_climate_set_heat_from_off(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_client: MagicMock,
    mock_thermostats,
) -> None:
    """Test switching to heat from off turns on first."""
    entity_id = "climate.living_room_thermostat"

    # Simulate thermostat being off
    mock_thermostats["301"].local_off = 1

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: entity_id, ATTR_HVAC_MODE: HVACMode.HEAT},
        blocking=True,
    )

    mock_client.turn_on_thermostat.assert_awaited_once_with("301")
    mock_client.set_thermostat_season.assert_awaited_once_with("301", 1)


@pytest.mark.usefixtures("mock_client")
async def test_climate_set_preset_mode(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_client: MagicMock,
) -> None:
    """Test setting preset mode to manual and auto."""
    entity_id = "climate.living_room_thermostat"

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: entity_id, ATTR_PRESET_MODE: "manual"},
        blocking=True,
    )
    mock_client.set_thermostat_mode.assert_awaited_once_with("301", 1)

    mock_client.set_thermostat_mode.reset_mock()

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: entity_id, ATTR_PRESET_MODE: "auto"},
        blocking=True,
    )
    mock_client.set_thermostat_mode.assert_awaited_once_with("301", 0)


@pytest.mark.usefixtures("mock_client")
async def test_climate_set_cool_from_off(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_client: MagicMock,
    mock_thermostats,
) -> None:
    """Test switching to cool from off turns on first."""
    entity_id = "climate.living_room_thermostat"

    # Simulate thermostat being off
    mock_thermostats["301"].local_off = 1

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: entity_id, ATTR_HVAC_MODE: HVACMode.COOL},
        blocking=True,
    )

    mock_client.turn_on_thermostat.assert_awaited_once_with("301")
    mock_client.set_thermostat_season.assert_awaited_once_with("301", 0)


@pytest.mark.usefixtures("mock_client")
async def test_climate_preset_mode_manual(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_client: MagicMock,
    mock_thermostats,
) -> None:
    """Test climate entity reports manual preset when thermostat is in manual mode."""
    entity_id = "climate.living_room_thermostat"

    callbacks = [
        call[0][0] for call in mock_client.register_update_callback.call_args_list
    ]

    # Simulate thermostat entering manual mode
    mock_thermostats["301"].mode = 1
    for cb in callbacks:
        cb("thermostat_mode", {"device_id": "301", "mode": "1"})
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.attributes["preset_mode"] == "manual"


@pytest.mark.usefixtures("mock_client")
async def test_climate_thermostat_update(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_client: MagicMock,
    mock_thermostats,
) -> None:
    """Test climate entity updates on thermostat callbacks."""
    entity_id = "climate.living_room_thermostat"

    # All entities register callbacks; broadcast to all of them
    callbacks = [
        call[0][0] for call in mock_client.register_update_callback.call_args_list
    ]

    def fire_update(event_type: str, data: dict) -> None:
        for cb in callbacks:
            cb(event_type, data)

    # Simulate season change to summer
    mock_thermostats["301"].season = 0
    fire_update("thermostat_season", {"device_id": "301", "season": "0"})
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == HVACMode.COOL

    # Simulate local off
    mock_thermostats["301"].local_off = 1
    fire_update("thermostat_local_off", {"device_id": "301", "local_off": "1"})
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == HVACMode.OFF
