"""Config flow for Luxtronik WS integration."""
from __future__ import annotations

import logging

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL, MIN_SCAN_INTERVAL
from .lux_ip import getLuxIp
import websockets
import xml.etree.ElementTree as ET

_LOGGER = logging.getLogger(__name__)

async def getWebsocket(server, password: str):
    try:
        websocket = await websockets.connect("ws://"+server+":8214/", subprotocols=["Lux_WS"])
        await websocket.send("LOGIN;"+password)
        try:
            result = await websocket.recv()
            if not result.startswith("<Navigation id="):
                _LOGGER.critical("luxtronik login response is unknown")
                return None, None, True, False

            root = ET.fromstring(result)
            if len(root) < 5:
                _LOGGER.critical("wrong password")
                return None, None, True, False

        except websockets.exceptions.ConnectionClosedError:
            _LOGGER.critical("Connection closed unexpectedly.")
            return None, None, True, False

        _LOGGER.debug("Websocket returned:"+result)
        return websocket, root, True, True
    except OSError:
        _LOGGER.critical("Couldn't connect to websocket")
        return None, None, False, False

    return

class PlaceholderHub:
    def __init__(self, server: str) -> None:
        """Initialize."""
        self.server = server

    async def authenticate(self, password: str) -> (bool, bool):
        """Test if we can authenticate with the host."""
        ws, _, connected, loggedin = await getWebsocket(self.server, password)
        await ws.close()
        return connected, loggedin


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    hub = PlaceholderHub(data["server"])
    connected, loggedin = await hub.authenticate(data["password"])

    if not connected:
        raise CannotConnect

    if not loggedin:
        raise InvalidAuth

    _LOGGER.debug("Authentication ok, connected:"+str(connected)+ " loggedin:"+str(loggedin))
    # Return info that you want to store in the config entry.
    return {
        "title": "Luxtronik WS Integration",
        "server": data["server"],
        "password": data["password"],
    }


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Luxtronik WS."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        luxIp = await getLuxIp()

        dataSchema = vol.Schema(
            {
                vol.Required(
                    "update_interval",
                    default=DEFAULT_SCAN_INTERVAL,
                ): vol.All(vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL, max=900)),
                vol.Required("server", default=luxIp): str,
                vol.Required("password", default="998899"): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=dataSchema, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
