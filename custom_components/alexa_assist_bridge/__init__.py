"""Home Assistant Alexa Assist Bridge integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
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
    hass.data[DOMAIN][entry.entry_id] = entry.data
    async_register_http_view(hass)
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
