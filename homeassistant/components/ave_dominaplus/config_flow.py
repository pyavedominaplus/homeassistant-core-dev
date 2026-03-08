"""Config flow for AVE DominaPlus."""

from __future__ import annotations

import logging
from typing import Any

from pyavedominaplus import DEFAULT_WS_PORT, AVEDominaClient
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_WS_PORT): int,
    }
)


async def _validate_connection(host: str, port: int) -> None:
    """Validate we can connect to the AVE DominaPlus server."""
    client = AVEDominaClient(host=host, port=port, auto_reconnect=False)
    try:
        await client.connect()
    finally:
        await client.disconnect()


class AveDominaPlusConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AVE DominaPlus."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]

            await self.async_set_unique_id(f"{host}:{port}")
            self._abort_if_unique_id_configured()

            try:
                await _validate_connection(host, port)
            except Exception:
                _LOGGER.exception(
                    "Cannot connect to AVE DominaPlus at %s:%s", host, port
                )
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=f"AVE DominaPlus ({host})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]

            try:
                await _validate_connection(host, port)
            except Exception:
                _LOGGER.exception(
                    "Cannot connect to AVE DominaPlus at %s:%s", host, port
                )
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(
                    self._get_reconfigure_entry(),
                    data_updates=user_input,
                )

        reconfigure_entry = self._get_reconfigure_entry()
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST, default=reconfigure_entry.data[CONF_HOST]
                    ): str,
                    vol.Required(
                        CONF_PORT, default=reconfigure_entry.data[CONF_PORT]
                    ): int,
                }
            ),
            errors=errors,
        )
