"""HTTP endpoint for Alexa Assist Bridge."""

from __future__ import annotations

import logging
from typing import Any

from aiohttp import web

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .alexa import (
    AlexaRequestError,
    alexa_error_response,
    alexa_help_response,
    alexa_launch_response,
    alexa_plain_text_response,
    extract_alexa_query,
    is_launch_request,
    is_stop_or_cancel_request,
)
from .assist import async_process_assist
from .const import (
    CONF_AGENT_ID,
    CONF_ALLOW_DEBUG_REQUESTS,
    CONF_ASSISTANT_NAME,
    CONF_CONVERSATION_MODE,
    CONF_ENDPOINT_ID,
    CONF_LANGUAGE,
    CONF_SPOKEN_RESPONSE_PROMPT,
    CONVERSATION_MODE_ALWAYS,
    CONVERSATION_MODE_ASSIST,
    CONVERSATION_MODE_NEVER,
    DEFAULT_AGENT_ID,
    DEFAULT_ASSISTANT_NAME,
    DEFAULT_CONVERSATION_MODE,
    DEFAULT_LANGUAGE,
    DEFAULT_SPOKEN_RESPONSE_PROMPT,
    DOMAIN,
    SIGNAL_DIAGNOSTICS_UPDATED,
)
from .diagnostics import (
    record_request,
    record_status,
    record_validation,
)
from .security import AlexaSecurityError, async_validate_alexa_request

_LOGGER = logging.getLogger(__name__)

_VIEW_REGISTERED = f"{DOMAIN}_view_registered"


def async_register_http_view(hass: HomeAssistant) -> None:
    """Register the Alexa Assist Bridge HTTP view once."""
    if hass.data.get(_VIEW_REGISTERED):
        return

    hass.http.register_view(AlexaAssistBridgeView)
    hass.http.register_view(AlexaAssistBridgeDiagnosticsView)
    hass.data[_VIEW_REGISTERED] = True


class AlexaAssistBridgeView(HomeAssistantView):
    """Receive Alexa Skill requests and forward user text to Assist."""

    url = "/api/alexa_assist_bridge/{endpoint_id}"
    name = "api:alexa_assist_bridge"
    requires_auth = False

    async def post(self, request: web.Request, endpoint_id: str) -> web.Response:
        """Handle an Alexa Skill request."""
        hass: HomeAssistant = request.app["hass"]
        runtime = _runtime_for_endpoint(hass, endpoint_id)
        if runtime is None:
            return web.json_response(
                alexa_error_response("Unknown Alexa Assist Bridge endpoint."),
                status=404,
            )

        config = runtime["config"]
        diagnostics = runtime["diagnostics"]
        raw_body = await request.read()
        try:
            payload = await request.json()
        except ValueError:
            record_status(
                diagnostics,
                "invalid_json",
                error="The request body was not valid JSON.",
            )
            _notify_diagnostics_update(hass, runtime)
            return web.json_response(
                alexa_error_response("The request body was not valid JSON."),
                status=400,
            )

        record_request(diagnostics, payload)
        allow_debug_requests = bool(config.get(CONF_ALLOW_DEBUG_REQUESTS, False))

        try:
            await async_validate_alexa_request(
                hass=hass,
                request=request,
                payload=payload,
                raw_body=raw_body,
                configured_skill_id=config.get("alexa_skill_id", ""),
                allow_debug_requests=allow_debug_requests,
            )
        except AlexaSecurityError as err:
            _LOGGER.warning("Rejected Alexa request: %s", err)
            record_validation(diagnostics, "failed")
            record_status(diagnostics, "rejected", error=str(err))
            _notify_diagnostics_update(hass, runtime)
            return web.json_response(
                alexa_error_response("The Alexa request was rejected."),
                status=400,
            )

        record_validation(diagnostics, "passed")
        assistant_name = config.get(CONF_ASSISTANT_NAME, DEFAULT_ASSISTANT_NAME)

        try:
            if is_stop_or_cancel_request(payload):
                record_status(
                    diagnostics,
                    "ok",
                    response_length=len("Goodbye."),
                    should_end_session=True,
                    conversation_id_present=bool(_conversation_id(payload)),
                )
                _notify_diagnostics_update(hass, runtime)
                return web.json_response(alexa_plain_text_response("Goodbye."))

            if is_launch_request(payload):
                response_text = f"Hi, I'm {assistant_name}. What do you want to ask?"
                record_status(
                    diagnostics,
                    "launch",
                    response_length=len(response_text),
                    should_end_session=False,
                    conversation_id_present=bool(_conversation_id(payload)),
                )
                _notify_diagnostics_update(hass, runtime)
                return web.json_response(alexa_launch_response(assistant_name))

            query = extract_alexa_query(payload)
        except AlexaRequestError as err:
            record_status(diagnostics, "help", error=str(err))
            _notify_diagnostics_update(hass, runtime)
            return web.json_response(alexa_help_response(assistant_name))

        if not query:
            record_status(diagnostics, "help", error="Empty query")
            _notify_diagnostics_update(hass, runtime)
            return web.json_response(alexa_help_response(assistant_name))

        try:
            result = await async_process_assist(
                hass=hass,
                text=query,
                conversation_id=_conversation_id(payload),
                agent_id=config.get(CONF_AGENT_ID, DEFAULT_AGENT_ID),
                language=config.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
                assistant_name=assistant_name,
                spoken_response_prompt=bool(
                    config.get(
                        CONF_SPOKEN_RESPONSE_PROMPT,
                        DEFAULT_SPOKEN_RESPONSE_PROMPT,
                    )
                ),
            )
        except Exception:
            _LOGGER.exception("Assist processing failed")
            record_status(
                diagnostics,
                "assist_error",
                error="Home Assistant had trouble processing that request.",
            )
            _notify_diagnostics_update(hass, runtime)
            return web.json_response(
                alexa_error_response(
                    "Home Assistant had trouble processing that request."
                ),
                status=500,
            )

        should_end_session = _should_end_session(
            conversation_mode=config.get(
                CONF_CONVERSATION_MODE,
                DEFAULT_CONVERSATION_MODE,
            ),
            assist_continue=result.continue_conversation,
        )
        record_status(
            diagnostics,
            "ok",
            response_length=len(result.speech),
            should_end_session=should_end_session,
            conversation_id_present=bool(result.conversation_id),
        )
        _notify_diagnostics_update(hass, runtime)
        return web.json_response(
            alexa_plain_text_response(
                result.speech,
                should_end_session=should_end_session,
                reprompt_text=_reprompt_text(assistant_name),
                follow_up_text=_follow_up_text(),
            )
        )


class AlexaAssistBridgeDiagnosticsView(HomeAssistantView):
    """Return last-request diagnostics for an endpoint."""

    url = "/api/alexa_assist_bridge/{endpoint_id}/diagnostics"
    name = "api:alexa_assist_bridge:diagnostics"
    requires_auth = True

    async def get(self, request: web.Request, endpoint_id: str) -> web.Response:
        """Handle a diagnostics request."""
        hass: HomeAssistant = request.app["hass"]
        runtime = _runtime_for_endpoint(hass, endpoint_id)
        if runtime is None:
            return web.json_response(
                {"error": "Unknown Alexa Assist Bridge endpoint."},
                status=404,
            )

        config = runtime["config"]
        return web.json_response(
            {
                "endpoint_id": config.get(CONF_ENDPOINT_ID),
                "assistant_name": config.get(
                    CONF_ASSISTANT_NAME,
                    DEFAULT_ASSISTANT_NAME,
                ),
                "agent_id": config.get(CONF_AGENT_ID, DEFAULT_AGENT_ID),
                "language": config.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
                "conversation_mode": config.get(
                    CONF_CONVERSATION_MODE,
                    DEFAULT_CONVERSATION_MODE,
                ),
                "spoken_response_prompt": bool(
                    config.get(
                        CONF_SPOKEN_RESPONSE_PROMPT,
                        DEFAULT_SPOKEN_RESPONSE_PROMPT,
                    )
                ),
                "allow_debug_requests": bool(
                    config.get(CONF_ALLOW_DEBUG_REQUESTS, False)
                ),
                "diagnostics": runtime["diagnostics"],
            }
        )


def _runtime_for_endpoint(
    hass: HomeAssistant,
    endpoint_id: str,
) -> dict[str, Any] | None:
    """Find the runtime data for an endpoint id."""
    for runtime in hass.data.get(DOMAIN, {}).values():
        if runtime["config"].get(CONF_ENDPOINT_ID) == endpoint_id:
            return runtime
    return None


def _notify_diagnostics_update(
    hass: HomeAssistant,
    runtime: dict[str, Any],
) -> None:
    """Notify listeners that runtime diagnostics changed."""
    async_dispatcher_send(
        hass,
        f"{SIGNAL_DIAGNOSTICS_UPDATED}_{runtime['entry_id']}",
    )


def _conversation_id(payload: dict[str, Any]) -> str | None:
    """Return an Alexa session id suitable for HA conversation continuity."""
    session_id = payload.get("session", {}).get("sessionId")
    if isinstance(session_id, str) and session_id:
        return session_id
    return None


def _should_end_session(
    *,
    conversation_mode: str,
    assist_continue: bool,
) -> bool:
    """Return whether Alexa should close the skill after this response."""
    if conversation_mode == CONVERSATION_MODE_ALWAYS:
        return False
    if conversation_mode == CONVERSATION_MODE_NEVER:
        return True
    if conversation_mode != CONVERSATION_MODE_ASSIST:
        return not assist_continue
    return not assist_continue


def _reprompt_text(assistant_name: str) -> str:
    """Return a short Alexa reprompt for open sessions."""
    return f"What else would you like to ask {assistant_name}?"


def _follow_up_text() -> str:
    """Return the short spoken cue that keeps chat mode feeling open."""
    return "Anything else?"
