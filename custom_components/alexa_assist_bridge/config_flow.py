"""Config flow for Alexa Assist Bridge."""

from __future__ import annotations

import secrets
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_ALEXA_SKILL_ID,
    CONF_ALLOW_DEBUG_REQUESTS,
    CONF_AGENT_ID,
    CONF_ASSISTANT_NAME,
    CONF_CONVERSATION_MODE,
    CONF_ENDPOINT_ID,
    CONF_LANGUAGE,
    CONF_SPOKEN_RESPONSE_PROMPT,
    CONVERSATION_MODES,
    DEFAULT_AGENT_ID,
    DEFAULT_ALLOW_DEBUG_REQUESTS,
    DEFAULT_ASSISTANT_NAME,
    DEFAULT_CONVERSATION_MODE,
    DEFAULT_LANGUAGE,
    DEFAULT_SPOKEN_RESPONSE_PROMPT,
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
                CONF_ASSISTANT_NAME: user_input[CONF_ASSISTANT_NAME].strip(),
                CONF_CONVERSATION_MODE: user_input[CONF_CONVERSATION_MODE],
                CONF_ENDPOINT_ID: user_input[CONF_ENDPOINT_ID].strip(),
                CONF_LANGUAGE: user_input[CONF_LANGUAGE].strip(),
                CONF_SPOKEN_RESPONSE_PROMPT: user_input[
                    CONF_SPOKEN_RESPONSE_PROMPT
                ],
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
                    CONF_ASSISTANT_NAME,
                    default=DEFAULT_ASSISTANT_NAME,
                ): str,
                vol.Required(
                    CONF_CONVERSATION_MODE,
                    default=DEFAULT_CONVERSATION_MODE,
                ): vol.In(CONVERSATION_MODES),
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
                vol.Required(
                    CONF_SPOKEN_RESPONSE_PROMPT,
                    default=DEFAULT_SPOKEN_RESPONSE_PROMPT,
                ): bool,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> AlexaAssistBridgeOptionsFlow:
        """Create the options flow."""
        return AlexaAssistBridgeOptionsFlow(config_entry)


class AlexaAssistBridgeOptionsFlow(config_entries.OptionsFlow):
    """Handle Alexa Assist Bridge options."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Manage integration options."""
        current = {**self._config_entry.data, **self._config_entry.options}

        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={
                    CONF_ALEXA_SKILL_ID: user_input.get(
                        CONF_ALEXA_SKILL_ID,
                        "",
                    ).strip(),
                    CONF_ALLOW_DEBUG_REQUESTS: user_input[CONF_ALLOW_DEBUG_REQUESTS],
                    CONF_AGENT_ID: user_input[CONF_AGENT_ID].strip(),
                    CONF_ASSISTANT_NAME: user_input[CONF_ASSISTANT_NAME].strip(),
                    CONF_CONVERSATION_MODE: user_input[CONF_CONVERSATION_MODE],
                    CONF_ENDPOINT_ID: user_input[CONF_ENDPOINT_ID].strip(),
                    CONF_LANGUAGE: user_input[CONF_LANGUAGE].strip(),
                    CONF_SPOKEN_RESPONSE_PROMPT: user_input[
                        CONF_SPOKEN_RESPONSE_PROMPT
                    ],
                },
            )

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_ALEXA_SKILL_ID,
                    default=current.get(CONF_ALEXA_SKILL_ID, ""),
                ): str,
                vol.Required(
                    CONF_AGENT_ID,
                    default=current.get(CONF_AGENT_ID, DEFAULT_AGENT_ID),
                ): str,
                vol.Required(
                    CONF_ASSISTANT_NAME,
                    default=current.get(
                        CONF_ASSISTANT_NAME,
                        DEFAULT_ASSISTANT_NAME,
                    ),
                ): str,
                vol.Required(
                    CONF_CONVERSATION_MODE,
                    default=current.get(
                        CONF_CONVERSATION_MODE,
                        DEFAULT_CONVERSATION_MODE,
                    ),
                ): vol.In(CONVERSATION_MODES),
                vol.Required(
                    CONF_ENDPOINT_ID,
                    default=current[CONF_ENDPOINT_ID],
                ): str,
                vol.Required(
                    CONF_LANGUAGE,
                    default=current.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
                ): str,
                vol.Required(
                    CONF_ALLOW_DEBUG_REQUESTS,
                    default=current.get(
                        CONF_ALLOW_DEBUG_REQUESTS,
                        DEFAULT_ALLOW_DEBUG_REQUESTS,
                    ),
                ): bool,
                vol.Required(
                    CONF_SPOKEN_RESPONSE_PROMPT,
                    default=current.get(
                        CONF_SPOKEN_RESPONSE_PROMPT,
                        DEFAULT_SPOKEN_RESPONSE_PROMPT,
                    ),
                ): bool,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
        )
