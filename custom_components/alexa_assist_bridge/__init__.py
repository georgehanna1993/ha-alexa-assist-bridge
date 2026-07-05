"""Home Assistant Alexa Assist Bridge integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

type AlexaAssistBridgeConfigEntry = ConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AlexaAssistBridgeConfigEntry,
) -> bool:
    """Set up Alexa Assist Bridge from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data
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
