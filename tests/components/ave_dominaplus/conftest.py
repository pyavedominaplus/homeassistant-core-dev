"""Fixtures for AVE DominaPlus tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from pyavedominaplus import DominaArea, DominaDevice, DominaThermostat
import pytest

from homeassistant.components.ave_dominaplus.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry

HOST = "192.168.1.100"
PORT = 14001


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=f"AVE DominaPlus ({HOST})",
        data={
            CONF_HOST: HOST,
            CONF_PORT: PORT,
        },
        unique_id=f"{HOST}:{PORT}",
    )


def _make_light_device() -> DominaDevice:
    """Create a mock light device."""
    return DominaDevice(id="101", name="Living Room Light", device_type=1)


def _make_dimmer_device() -> DominaDevice:
    """Create a mock dimmer device."""
    device = DominaDevice(id="102", name="Bedroom Dimmer", device_type=2)
    device.current_value = 15
    return device


def _make_shutter_device() -> DominaDevice:
    """Create a mock shutter device."""
    return DominaDevice(id="201", name="Kitchen Shutter", device_type=3)


def _make_thermostat_device() -> DominaDevice:
    """Create a mock thermostat device."""
    return DominaDevice(id="301", name="Living Room Thermostat", device_type=4)


def _make_scenario_device() -> DominaDevice:
    """Create a mock scenario device."""
    return DominaDevice(id="401", name="Night Mode", device_type=6)


def _make_thermostat() -> DominaThermostat:
    """Create a mock thermostat object."""
    return DominaThermostat(
        id="301",
        name="Living Room Thermostat",
        temperature=21.5,
        set_point=22.0,
        season=1,
        mode=0,
        local_off=0,
        humidity_enabled=True,
        humidity_value=55,
    )


@pytest.fixture
def mock_devices() -> dict[str, DominaDevice]:
    """Return mock devices."""
    return {
        "101": _make_light_device(),
        "102": _make_dimmer_device(),
        "201": _make_shutter_device(),
        "301": _make_thermostat_device(),
        "401": _make_scenario_device(),
    }


@pytest.fixture
def mock_thermostats() -> dict[str, DominaThermostat]:
    """Return mock thermostats."""
    return {"301": _make_thermostat()}


@pytest.fixture
def mock_areas() -> dict[str, DominaArea]:
    """Return mock areas."""
    return {
        "1": DominaArea(id="1", name="Ground Floor", order="1"),
    }


@pytest.fixture
def mock_client(
    mock_devices: dict[str, DominaDevice],
    mock_thermostats: dict[str, DominaThermostat],
    mock_areas: dict[str, DominaArea],
) -> Generator[MagicMock]:
    """Return a mocked AVEDominaClient."""
    with (
        patch(
            "homeassistant.components.ave_dominaplus.AVEDominaClient",
            autospec=True,
        ) as client_mock,
        patch(
            "homeassistant.components.ave_dominaplus.config_flow.AVEDominaClient",
            new=client_mock,
        ),
    ):
        client = client_mock.return_value
        client.connect = AsyncMock()
        client.disconnect = AsyncMock()
        client.initialize = AsyncMock()
        client.wait_for_initialization = AsyncMock(return_value=True)
        client.request_device_statuses = AsyncMock()
        client.turn_on_light = AsyncMock()
        client.turn_off_light = AsyncMock()
        client.toggle_light = AsyncMock()
        client.turn_on_dimmer = AsyncMock()
        client.turn_off_dimmer = AsyncMock()
        client.set_dimmer_level = AsyncMock()
        client.step_dimmer = AsyncMock()
        client.open_shutter = AsyncMock()
        client.close_shutter = AsyncMock()
        client.stop_shutter = AsyncMock()
        client.activate_scenario = AsyncMock()
        client.turn_on_thermostat = AsyncMock()
        client.turn_off_thermostat = AsyncMock()
        client.set_thermostat_set_point = AsyncMock()
        client.set_thermostat_season = AsyncMock()
        client.set_thermostat_mode = AsyncMock()
        client.toggle_thermostat_local_off = AsyncMock()

        client.devices = mock_devices
        client.thermostats = mock_thermostats
        client.areas = mock_areas

        client.register_update_callback = MagicMock(return_value=lambda: None)
        client.register_connection_callback = MagicMock(return_value=lambda: None)

        yield client


@pytest.fixture
async def init_integration(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_client: MagicMock,
) -> MockConfigEntry:
    """Set up the AVE DominaPlus integration for testing."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    return mock_config_entry
