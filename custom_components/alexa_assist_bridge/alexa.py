"""Alexa Skill request and response helpers."""

from __future__ import annotations

from typing import Any

_ASSIST_INTENT_PREFIXES = {
    "AskAssistIntent": "",
    "AskAssistWhatIntent": "what",
    "AskAssistWhyIntent": "why",
    "AskAssistHowIntent": "how",
    "AskAssistWhereIntent": "where",
    "AskAssistWhenIntent": "when",
    "AskAssistIsIntent": "is",
    "AskAssistAreIntent": "are",
    "AskAssistTurnIntent": "turn",
    "AskAssistSetIntent": "set",
    "AskAssistOpenIntent": "open",
    "AskAssistCloseIntent": "close",
}


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

    if intent_name not in _ASSIST_INTENT_PREFIXES:
        raise AlexaRequestError(f"Unsupported intent: {intent_name}")

    query = (
        intent.get("slots", {})
        .get("query", {})
        .get("value")
    )
    if not isinstance(query, str):
        raise AlexaRequestError(f"{intent_name} did not include query text")

    return _query_with_prefix(_ASSIST_INTENT_PREFIXES[intent_name], query)


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
    reprompt_text: str | None = None,
    follow_up_text: str | None = None,
) -> dict[str, Any]:
    """Build a standard Alexa plain text response."""
    speech_text = _speech_with_follow_up(
        text=text,
        should_end_session=should_end_session,
        follow_up_text=follow_up_text,
    )
    response: dict[str, Any] = {
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "PlainText",
                "text": _clean_speech_text(speech_text),
            },
            "shouldEndSession": should_end_session,
        },
    }
    if not should_end_session and reprompt_text:
        response["response"]["reprompt"] = {
            "outputSpeech": {
                "type": "PlainText",
                "text": _clean_speech_text(reprompt_text),
            }
        }
    return response


def alexa_help_response(assistant_name: str = "Nabu") -> dict[str, Any]:
    """Build the help response."""
    return alexa_plain_text_response(
        f"Ask {assistant_name} a Home Assistant question, like what lights are on.",
        should_end_session=False,
        reprompt_text="What would you like to ask?",
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


def _speech_with_follow_up(
    *,
    text: str,
    should_end_session: bool,
    follow_up_text: str | None,
) -> str:
    """Append a short spoken cue when Alexa should keep listening."""
    if should_end_session or not follow_up_text:
        return text

    speech = text.strip()
    follow_up = follow_up_text.strip()
    if not speech or not follow_up:
        return text
    if speech.lower().endswith(follow_up.lower()):
        return speech
    return f"{speech} {follow_up}"


def _query_with_prefix(prefix: str, query: str) -> str:
    """Reconstruct the natural phrase from an Alexa carrier phrase sample."""
    clean_query = query.strip()
    if not prefix:
        return clean_query
    if clean_query.lower().startswith(f"{prefix} "):
        return clean_query
    return f"{prefix} {clean_query}".strip()
