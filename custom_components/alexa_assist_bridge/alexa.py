"""Alexa Skill request and response helpers."""

from __future__ import annotations

from typing import Any


class AlexaRequestError(ValueError):
    """Raised when an Alexa request cannot be handled."""


def extract_alexa_query(payload: dict[str, Any]) -> str:
    """Extract the natural-language query from an Alexa or local test payload."""
    direct_query = payload.get("query")
    if isinstance(direct_query, str):
        return direct_query.strip()

    request = _request(payload)
    request_type = request.get("type")

    if request_type == "LaunchRequest":
        raise AlexaRequestError("LaunchRequest does not contain a query")

    if request_type != "IntentRequest":
        raise AlexaRequestError(f"Unsupported request type: {request_type}")

    intent = request.get("intent", {})
    intent_name = intent.get("name")

    if intent_name in {"AMAZON.HelpIntent", "AMAZON.FallbackIntent"}:
        raise AlexaRequestError(f"{intent_name} does not contain a query")

    if intent_name != "AskAssistIntent":
        raise AlexaRequestError(f"Unsupported intent: {intent_name}")

    query = (
        intent.get("slots", {})
        .get("query", {})
        .get("value")
    )
    if not isinstance(query, str):
        raise AlexaRequestError("AskAssistIntent did not include query text")

    return query.strip()


def is_stop_or_cancel_request(payload: dict[str, Any]) -> bool:
    """Return true if the request is an Alexa stop/cancel intent."""
    request = payload.get("request", {})
    if request.get("type") != "IntentRequest":
        return False

    intent_name = request.get("intent", {}).get("name")
    return intent_name in {"AMAZON.CancelIntent", "AMAZON.StopIntent"}


def alexa_plain_text_response(
    text: str,
    *,
    should_end_session: bool = True,
) -> dict[str, Any]:
    """Build a standard Alexa plain text response."""
    return {
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "PlainText",
                "text": _clean_speech_text(text),
            },
            "shouldEndSession": should_end_session,
        },
    }


def alexa_help_response() -> dict[str, Any]:
    """Build the help response."""
    return alexa_plain_text_response(
        "Ask Nabu a Home Assistant question, like what lights are on.",
        should_end_session=False,
    )


def alexa_error_response(text: str) -> dict[str, Any]:
    """Build a user-safe error response."""
    return alexa_plain_text_response(text)


def _request(payload: dict[str, Any]) -> dict[str, Any]:
    request = payload.get("request")
    if not isinstance(request, dict):
        raise AlexaRequestError("Missing request object")
    return request


def _clean_speech_text(text: str) -> str:
    speech = " ".join(text.split())
    if not speech:
        return "I did not get a response from Home Assistant."
    return speech[:8000]
