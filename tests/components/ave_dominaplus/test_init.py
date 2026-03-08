"""Tests for the AVE DominaPlus integration init."""

from collections.abc import Callable
from unittest.mock import AsyncMock, MagicMock

import pytest

from homeassistant.components.ave_dominaplus.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .conftest import HOST

from tests.common import MockConfigEntry


@pytest.mark.usefixtures("mock_client")
async def test_load_unload(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_client: MagicMock,
) -> None:
    """Test loading and unloading a config entry."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.LOADED
    mock_client.connect.assert_awaited_once()
    mock_client.initialize.assert_awaited_once()
    mock_client.wait_for_initialization.assert_awaited_once()

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED
    mock_client.disconnect.assert_awaited_once()


@pytest.mark.usefixtures("mock_client")
async def test_connect_failure(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_client: MagicMock,
) -> None:
    """Test setup retries when connection fails."""
    mock_client.connect = AsyncMock(side_effect=ConnectionError("refused"))

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


@pytest.mark.usefixtures("mock_client")
async def test_initialization_timeout(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_client: MagicMock,
) -> None:
    """Test setup retries when initialization times out."""
    mock_client.wait_for_initialization = AsyncMock(return_value=False)

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY
    mock_client.disconnect.assert_awaited_once()


@pytest.mark.usefixtures("mock_client")
async def test_hub_device_registered(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test the hub device is registered in the device registry."""
    device_entry = device_registry.async_get_device(identifiers={(DOMAIN, HOST)})

    assert device_entry is not None
    assert device_entry.manufacturer == "AVE"
    assert device_entry.model == "DominaPlus Server"
    assert device_entry.name == f"AVE DominaPlus ({HOST})"


@pytest.mark.usefixtures("mock_client")
async def test_child_devices_registered(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test child devices are registered via the entity platform."""
    # The light entity creates a device entry
    device_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, f"{HOST}_101")}
    )
    assert device_entry is not None
    assert device_entry.name == "Living Room Light"
    assert device_entry.manufacturer == "AVE"
    assert device_entry.model == "DominaPlus Light"


@pytest.mark.usefixtures("mock_client")
async def test_existing_device_not_removed(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_client: MagicMock,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test that devices still in the device list are not removed on setup."""
    mock_config_entry.add_to_hass(hass)

    # Pre-register a device that IS still in the current device list (device 101)
    device_registry.async_get_or_create(
        config_entry_id=mock_config_entry.entry_id,
        identifiers={(DOMAIN, f"{HOST}_101")},
        name="Living Room Light",
    )

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Device 101 should still exist (not removed as stale)
    existing_device = device_registry.async_get_device(
        identifiers={(DOMAIN, f"{HOST}_101")}
    )
    assert existing_device is not None


@pytest.mark.usefixtures("mock_client")
async def test_connection_callback_fires_dispatcher(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_client: MagicMock,
) -> None:
    """Test that connection state changes are dispatched to entities."""
    registered_callback: Callable[[str], None] | None = None

    def capture_callback(cb: Callable[[str], None]) -> Callable[[], None]:
        nonlocal registered_callback
        registered_callback = cb
        return lambda: None

    mock_client.register_connection_callback = MagicMock(side_effect=capture_callback)

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert registered_callback is not None

    # Fire a connection state change; verify no errors are raised
    registered_callback("disconnected")
    await hass.async_block_till_done()

    registered_callback("connected")
    await hass.async_block_till_done()


@pytest.mark.usefixtures("mock_client")
async def test_stale_device_removal(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_client: MagicMock,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test stale devices are removed on setup."""
    mock_config_entry.add_to_hass(hass)

    # Pre-register a device that won't be in the new device list
    device_registry.async_get_or_create(
        config_entry_id=mock_config_entry.entry_id,
        identifiers={(DOMAIN, f"{HOST}_999")},
        name="Stale Device",
    )

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Stale device should be removed
    stale_device = device_registry.async_get_device(
        identifiers={(DOMAIN, f"{HOST}_999")}
    )
    assert stale_device is None
