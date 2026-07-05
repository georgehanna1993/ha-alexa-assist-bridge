"""Sensor entities for Alexa Assist Bridge."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_AGENT_ID,
    CONF_ALLOW_DEBUG_REQUESTS,
    CONF_ASSISTANT_NAME,
    CONF_ENDPOINT_ID,
    CONF_LANGUAGE,
    DEFAULT_AGENT_ID,
    DEFAULT_ASSISTANT_NAME,
    DEFAULT_LANGUAGE,
    DOMAIN,
    SIGNAL_DIAGNOSTICS_UPDATED,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Alexa Assist Bridge sensor entities."""
    async_add_entities([AlexaAssistBridgeStatusSensor(hass, entry)])


class AlexaAssistBridgeStatusSensor(SensorEntity):
    """Diagnostic status sensor for Alexa Assist Bridge."""

    _attr_has_entity_name = True
    _attr_name = "Status"
    _attr_icon = "mdi:account-voice"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the status sensor."""
        self.hass = hass
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_status"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Alexa Assist Bridge",
            manufacturer="Alexa Assist Bridge",
        )

    @property
    def native_value(self) -> str | None:
        """Return the latest bridge status."""
        return self._diagnostics.get("last_status")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return privacy-aware diagnostics as attributes."""
        config = self._runtime["config"]
        return {
            "assistant_name": config.get(
                CONF_ASSISTANT_NAME,
                DEFAULT_ASSISTANT_NAME,
            ),
            "agent_id": config.get(CONF_AGENT_ID, DEFAULT_AGENT_ID),
            "language": config.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
            "endpoint_id": config.get(CONF_ENDPOINT_ID),
            "allow_debug_requests": bool(
                config.get(CONF_ALLOW_DEBUG_REQUESTS, False)
            ),
            **self._diagnostics,
        }

    async def async_added_to_hass(self) -> None:
        """Subscribe to diagnostics updates."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{SIGNAL_DIAGNOSTICS_UPDATED}_{self.entry.entry_id}",
                self._handle_diagnostics_update,
            )
        )

    @callback
    def _handle_diagnostics_update(self) -> None:
        """Handle diagnostics update signal."""
        self.async_write_ha_state()

    @property
    def _runtime(self) -> dict[str, Any]:
        """Return runtime data for this config entry."""
        return self.hass.data[DOMAIN][self.entry.entry_id]

    @property
    def _diagnostics(self) -> dict[str, Any]:
        """Return diagnostics data for this config entry."""
        return self._runtime["diagnostics"]
