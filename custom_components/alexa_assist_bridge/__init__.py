"""Home Assistant Alexa Assist Bridge integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_ASSISTANT_NAME,
    DEFAULT_ASSISTANT_NAME,
    DOMAIN,
)
from .diagnostics import initial_diagnostics
from .http import async_register_http_view

type AlexaAssistBridgeConfigEntry = ConfigEntry


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up Alexa Assist Bridge."""
    del config

    hass.data.setdefault(DOMAIN, {})
    async_register_http_view(hass)
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AlexaAssistBridgeConfigEntry,
) -> bool:
    """Set up Alexa Assist Bridge from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "config": _entry_config(entry),
        "diagnostics": initial_diagnostics(),
    }
    async_register_http_view(hass)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: AlexaAssistBridgeConfigEntry,
) -> bool:
    """Unload Alexa Assist Bridge config entry."""
    hass.data[DOMAIN].pop(entry.entry_id, None)
    if not hass.data[DOMAIN]:
        hass.data.pop(DOMAIN)
    return True


async def _async_update_listener(
    hass: HomeAssistant,
    entry: AlexaAssistBridgeConfigEntry,
) -> None:
    """Reload the config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


def _entry_config(entry: AlexaAssistBridgeConfigEntry) -> dict:
    """Merge setup data and options, with options taking precedence."""
    return {
        CONF_ASSISTANT_NAME: DEFAULT_ASSISTANT_NAME,
        **entry.data,
        **entry.options,
    }
