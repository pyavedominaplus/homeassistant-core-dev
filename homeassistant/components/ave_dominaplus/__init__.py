"""The AVE DominaPlus integration."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from pyavedominaplus import AVEDominaClient

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import DOMAIN, SIGNAL_CONNECTION_STATE

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BUTTON,
    Platform.CLIMATE,
    Platform.COVER,
    Platform.LIGHT,
    Platform.SENSOR,
]


@dataclass
class AveDominaPlusRuntimeData:
    """Runtime data for AVE DominaPlus."""

    client: AVEDominaClient


type AveDominaPlusConfigEntry = ConfigEntry[AveDominaPlusRuntimeData]


async def async_setup_entry(
    hass: HomeAssistant, entry: AveDominaPlusConfigEntry
) -> bool:
    """Set up AVE DominaPlus from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]

    session = async_get_clientsession(hass)
    client = AVEDominaClient(host=host, port=port, session=session)

    try:
        await client.connect()
    except Exception as err:
        raise ConfigEntryNotReady(
            f"Cannot connect to AVE DominaPlus at {host}:{port}"
        ) from err

    await client.initialize()
    if not await client.wait_for_initialization(timeout=30.0):
        await client.disconnect()
        raise ConfigEntryNotReady("Timeout waiting for device initialization")

    # Register hub device
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, host)},
        name=f"AVE DominaPlus ({host})",
        manufacturer="AVE",
        model="DominaPlus Server",
    )

    # Remove stale devices
    known_device_ids = set(client.devices.keys())
    hub_identifier = (DOMAIN, host)
    for device_entry in dr.async_entries_for_config_entry(
        device_registry, entry.entry_id
    ):
        if hub_identifier in device_entry.identifiers:
            continue
        device_still_exists = False
        for identifier in device_entry.identifiers:
            if identifier[0] == DOMAIN:
                dev_id = identifier[1].removeprefix(f"{host}_")
                if dev_id in known_device_ids:
                    device_still_exists = True
                    break
        if not device_still_exists:
            _LOGGER.info(
                "Removing stale device %s (%s)",
                device_entry.name,
                device_entry.id,
            )
            device_registry.async_remove_device(device_entry.id)

    # Register connection callback
    @callback
    def connection_callback(status: str) -> None:
        """Handle connection status changes."""
        _LOGGER.debug("Connection status changed: %s", status)
        async_dispatcher_send(
            hass, f"{SIGNAL_CONNECTION_STATE}_{entry.entry_id}", status
        )

    entry.async_on_unload(client.register_connection_callback(connection_callback))

    entry.runtime_data = AveDominaPlusRuntimeData(client=client)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: AveDominaPlusConfigEntry
) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await entry.runtime_data.client.disconnect()
    return unload_ok
