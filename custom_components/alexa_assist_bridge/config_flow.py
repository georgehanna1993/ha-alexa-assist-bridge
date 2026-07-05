"""Config flow for Alexa Assist Bridge."""

from __future__ import annotations

import secrets
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_ALEXA_SKILL_ID,
    CONF_ALLOW_DEBUG_REQUESTS,
    CONF_AGENT_ID,
    CONF_ENDPOINT_ID,
    CONF_LANGUAGE,
    DEFAULT_AGENT_ID,
    DEFAULT_ALLOW_DEBUG_REQUESTS,
    DEFAULT_LANGUAGE,
    DOMAIN,
)


class AlexaAssistBridgeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle an Alexa Assist Bridge config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._suggested_endpoint_id = secrets.token_urlsafe(24)

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Create the integration entry."""
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()

            data = {
                CONF_ALEXA_SKILL_ID: user_input.get(CONF_ALEXA_SKILL_ID, "").strip(),
                CONF_ALLOW_DEBUG_REQUESTS: user_input[CONF_ALLOW_DEBUG_REQUESTS],
                CONF_AGENT_ID: user_input[CONF_AGENT_ID].strip(),
                CONF_ENDPOINT_ID: user_input[CONF_ENDPOINT_ID].strip(),
                CONF_LANGUAGE: user_input[CONF_LANGUAGE].strip(),
            }

            return self.async_create_entry(title="Alexa Assist Bridge", data=data)

        schema = vol.Schema(
            {
                vol.Optional(CONF_ALEXA_SKILL_ID): str,
                vol.Required(
                    CONF_AGENT_ID,
                    default=DEFAULT_AGENT_ID,
                ): str,
                vol.Required(
                    CONF_ENDPOINT_ID,
                    default=self._suggested_endpoint_id,
                ): str,
                vol.Required(
                    CONF_LANGUAGE,
                    default=DEFAULT_LANGUAGE,
                ): str,
                vol.Required(
                    CONF_ALLOW_DEBUG_REQUESTS,
                    default=DEFAULT_ALLOW_DEBUG_REQUESTS,
                ): bool,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
