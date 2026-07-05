"""HTTP endpoint for Alexa Assist Bridge."""

from __future__ import annotations

import logging
from typing import Any

from aiohttp import web

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .alexa import (
    AlexaRequestError,
    alexa_error_response,
    alexa_help_response,
    alexa_plain_text_response,
    extract_alexa_query,
    is_stop_or_cancel_request,
)
from .assist import async_process_assist
from .const import (
    CONF_AGENT_ID,
    CONF_ALLOW_DEBUG_REQUESTS,
    CONF_ENDPOINT_ID,
    CONF_LANGUAGE,
    DEFAULT_AGENT_ID,
    DEFAULT_LANGUAGE,
    DOMAIN,
)
from .security import AlexaSecurityError, async_validate_alexa_request

_LOGGER = logging.getLogger(__name__)

_VIEW_REGISTERED = f"{DOMAIN}_view_registered"


def async_register_http_view(hass: HomeAssistant) -> None:
    """Register the Alexa Assist Bridge HTTP view once."""
    if hass.data.get(_VIEW_REGISTERED):
        return

    hass.http.register_view(AlexaAssistBridgeView)
    hass.data[_VIEW_REGISTERED] = True


class AlexaAssistBridgeView(HomeAssistantView):
    """Receive Alexa Skill requests and forward user text to Assist."""

    url = "/api/alexa_assist_bridge/{endpoint_id}"
    name = "api:alexa_assist_bridge"
    requires_auth = False

    async def post(self, request: web.Request, endpoint_id: str) -> web.Response:
        """Handle an Alexa Skill request."""
        hass: HomeAssistant = request.app["hass"]
        entry = _entry_for_endpoint(hass, endpoint_id)
        if entry is None:
            return web.json_response(
                alexa_error_response("Unknown Alexa Assist Bridge endpoint."),
                status=404,
            )

        raw_body = await request.read()
        try:
            payload = await request.json()
        except ValueError:
            return web.json_response(
                alexa_error_response("The request body was not valid JSON."),
                status=400,
            )

        allow_debug_requests = bool(
            entry.get(CONF_ALLOW_DEBUG_REQUESTS, False)
        )

        try:
            await async_validate_alexa_request(
                hass=hass,
                request=request,
                payload=payload,
                raw_body=raw_body,
                configured_skill_id=entry.get("alexa_skill_id", ""),
                allow_debug_requests=allow_debug_requests,
            )
        except AlexaSecurityError as err:
            _LOGGER.warning("Rejected Alexa request: %s", err)
            return web.json_response(
                alexa_error_response("The Alexa request was rejected."),
                status=400,
            )

        try:
            if is_stop_or_cancel_request(payload):
                return web.json_response(alexa_plain_text_response("Goodbye."))

            query = extract_alexa_query(payload)
        except AlexaRequestError:
            return web.json_response(alexa_help_response())

        if not query:
            return web.json_response(alexa_help_response())

        try:
            result = await async_process_assist(
                hass=hass,
                text=query,
                conversation_id=_conversation_id(payload),
                agent_id=entry.get(CONF_AGENT_ID, DEFAULT_AGENT_ID),
                language=entry.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
            )
        except Exception:
            _LOGGER.exception("Assist processing failed")
            return web.json_response(
                alexa_error_response(
                    "Home Assistant had trouble processing that request."
                ),
                status=500,
            )

        return web.json_response(
            alexa_plain_text_response(
                result.speech,
                should_end_session=not result.continue_conversation,
            )
        )


def _entry_for_endpoint(
    hass: HomeAssistant,
    endpoint_id: str,
) -> dict[str, Any] | None:
    """Find the config entry data for an endpoint id."""
    for entry_data in hass.data.get(DOMAIN, {}).values():
        if entry_data.get(CONF_ENDPOINT_ID) == endpoint_id:
            return entry_data
    return None


def _conversation_id(payload: dict[str, Any]) -> str | None:
    """Return an Alexa session id suitable for HA conversation continuity."""
    session_id = payload.get("session", {}).get("sessionId")
    if isinstance(session_id, str) and session_id:
        return session_id
    return None
