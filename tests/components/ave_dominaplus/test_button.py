"""Tests for the AVE DominaPlus button platform."""

from unittest.mock import MagicMock

import pytest

from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN, SERVICE_PRESS
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry


@pytest.mark.usefixtures("mock_client")
async def test_scenario_button(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_client: MagicMock,
) -> None:
    """Test pressing a scenario button calls activate_scenario."""
    entity_id = "button.night_mode_activate"

    state = hass.states.get(entity_id)
    assert state is not None

    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    mock_client.activate_scenario.assert_awaited_once_with("401")
