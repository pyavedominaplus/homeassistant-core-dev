"""Tests for the AVE DominaPlus cover platform."""

from unittest.mock import MagicMock

import pytest

from homeassistant.components.cover import (
    ATTR_CURRENT_POSITION,
    ATTR_POSITION,
    DOMAIN as COVER_DOMAIN,
    SERVICE_CLOSE_COVER,
    SERVICE_OPEN_COVER,
    SERVICE_SET_COVER_POSITION,
    SERVICE_STOP_COVER,
    CoverState,
)
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry


@pytest.mark.usefixtures("mock_client")
async def test_cover_initial_state(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test cover reports correct initial state."""
    entity_id = "cover.kitchen_shutter"

    state = hass.states.get(entity_id)
    assert state is not None
    # current_value=0, is_closed=False (status 0 is not closed status 3)
    # position is None when not in a known state
    assert state.attributes.get(ATTR_CURRENT_POSITION) is None


@pytest.mark.usefixtures("mock_client")
async def test_cover_open_close_stop(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_client: MagicMock,
) -> None:
    """Test opening, closing, and stopping a cover."""
    entity_id = "cover.kitchen_shutter"

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    mock_client.open_shutter.assert_awaited_once_with("201")

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    mock_client.close_shutter.assert_awaited_once_with("201")

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_STOP_COVER,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    mock_client.stop_shutter.assert_awaited_once_with("201")


@pytest.mark.usefixtures("mock_client")
async def test_cover_set_position(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_client: MagicMock,
) -> None:
    """Test set_cover_position maps to open/close/stop."""
    entity_id = "cover.kitchen_shutter"

    # Position 0 -> close
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_SET_COVER_POSITION,
        {ATTR_ENTITY_ID: entity_id, ATTR_POSITION: 0},
        blocking=True,
    )
    mock_client.close_shutter.assert_awaited_once_with("201")

    # Position 100 -> open
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_SET_COVER_POSITION,
        {ATTR_ENTITY_ID: entity_id, ATTR_POSITION: 100},
        blocking=True,
    )
    mock_client.open_shutter.assert_awaited_once_with("201")

    # Position 50 -> stop
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_SET_COVER_POSITION,
        {ATTR_ENTITY_ID: entity_id, ATTR_POSITION: 50},
        blocking=True,
    )
    mock_client.stop_shutter.assert_awaited_once_with("201")


@pytest.mark.usefixtures("mock_client")
async def test_cover_status_updates(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_client: MagicMock,
) -> None:
    """Test cover reflects status updates for all states."""
    entity_id = "cover.kitchen_shutter"
    callbacks = [
        call[0][0] for call in mock_client.register_update_callback.call_args_list
    ]

    def fire_update(event_type: str, data: dict) -> None:
        for cb in callbacks:
            cb(event_type, data)

    # Status 3 = closed -> position 0
    fire_update("device_status", {"device_id": "201", "device_type": 3, "status": 3})
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == CoverState.CLOSED
    assert state.attributes[ATTR_CURRENT_POSITION] == 0

    # Status 1 = open -> position 100
    fire_update("device_status", {"device_id": "201", "device_type": 3, "status": 1})
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == CoverState.OPEN
    assert state.attributes[ATTR_CURRENT_POSITION] == 100

    # Status 5 = stopped/partially open -> position 50
    fire_update("device_status", {"device_id": "201", "device_type": 3, "status": 5})
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == CoverState.OPEN
    assert state.attributes[ATTR_CURRENT_POSITION] == 50

    # Status 2 = opening -> position None
    fire_update("device_status", {"device_id": "201", "device_type": 3, "status": 2})
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == CoverState.OPENING

    # Status 4 = closing -> position None
    fire_update("device_status", {"device_id": "201", "device_type": 3, "status": 4})
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == CoverState.CLOSING
