"""Tests for the AVE DominaPlus light platform."""

from unittest.mock import MagicMock

from pyavedominaplus.const import CONN_STATUS_OPEN
import pytest

from homeassistant.components.ave_dominaplus.const import SIGNAL_CONNECTION_STATE
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_MODE,
    ATTR_SUPPORTED_COLOR_MODES,
    DOMAIN as LIGHT_DOMAIN,
    ColorMode,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send

from tests.common import MockConfigEntry


@pytest.mark.usefixtures("mock_client")
async def test_light_on_off(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_client: MagicMock,
) -> None:
    """Test turning a light on and off."""
    entity_id = "light.living_room_light"

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_OFF
    # color_mode is None when off
    assert state.attributes[ATTR_SUPPORTED_COLOR_MODES] == [ColorMode.ONOFF]

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    mock_client.turn_on_light.assert_awaited_once_with("101")

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    mock_client.turn_off_light.assert_awaited_once_with("101")


@pytest.mark.usefixtures("mock_client")
async def test_dimmer_on_off(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_client: MagicMock,
) -> None:
    """Test turning a dimmer on and off uses dimmer-specific commands."""
    entity_id = "light.bedroom_dimmer"

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_ON
    assert state.attributes[ATTR_COLOR_MODE] == ColorMode.BRIGHTNESS
    assert state.attributes[ATTR_SUPPORTED_COLOR_MODES] == [ColorMode.BRIGHTNESS]
    assert state.attributes[ATTR_BRIGHTNESS] == round(15 * 255 / 31)

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    mock_client.turn_on_dimmer.assert_awaited_once_with("102")

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    mock_client.turn_off_dimmer.assert_awaited_once_with("102")


@pytest.mark.usefixtures("mock_client")
async def test_dimmer_set_brightness(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_client: MagicMock,
) -> None:
    """Test setting dimmer brightness."""
    entity_id = "light.bedroom_dimmer"

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id, ATTR_BRIGHTNESS: 128},
        blocking=True,
    )

    # 128/255 * 31 = ~15.6, rounded to 16
    mock_client.set_dimmer_level.assert_awaited_once_with("102", 16)


@pytest.mark.usefixtures("mock_client")
async def test_light_status_update(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_client: MagicMock,
) -> None:
    """Test light updates state from callback."""
    entity_id = "light.living_room_light"

    # Verify initially off
    assert hass.states.get(entity_id).state == STATE_OFF

    # Broadcast status update to all registered callbacks
    for call in mock_client.register_update_callback.call_args_list:
        call[0][0]("device_status", {"device_id": "101", "device_type": 1, "status": 1})
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == STATE_ON


@pytest.mark.usefixtures("mock_client")
async def test_entity_becomes_unavailable_on_disconnect(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test entity becomes unavailable when connection drops."""
    entity_id = "light.living_room_light"

    assert hass.states.get(entity_id).state != STATE_UNAVAILABLE

    # Simulate disconnect
    async_dispatcher_send(
        hass,
        f"{SIGNAL_CONNECTION_STATE}_{init_integration.entry_id}",
        "disconnected",
    )
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == STATE_UNAVAILABLE

    # Simulate reconnect
    async_dispatcher_send(
        hass,
        f"{SIGNAL_CONNECTION_STATE}_{init_integration.entry_id}",
        CONN_STATUS_OPEN,
    )
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state != STATE_UNAVAILABLE
