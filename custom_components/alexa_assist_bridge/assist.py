"""Home Assistant Assist integration helpers."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.conversation import async_converse
from homeassistant.core import Context, HomeAssistant


@dataclass(frozen=True)
class AssistBridgeResult:
    """Normalized Assist response for Alexa."""

    speech: str
    continue_conversation: bool
    conversation_id: str | None


async def async_process_assist(
    hass: HomeAssistant,
    text: str,
    conversation_id: str | None,
    agent_id: str | None,
    language: str | None,
) -> AssistBridgeResult:
    """Send text to Home Assistant Assist and normalize the response."""
    result = await async_converse(
        hass=hass,
        text=text,
        conversation_id=conversation_id,
        context=Context(),
        language=language,
        agent_id=agent_id,
    )
    result_dict = result.as_dict()

    speech = _extract_speech(result_dict)
    return AssistBridgeResult(
        speech=speech,
        continue_conversation=bool(result_dict.get("continue_conversation")),
        conversation_id=result_dict.get("conversation_id"),
    )


def _extract_speech(result: dict) -> str:
    """Extract plain or SSML speech from a conversation response dictionary."""
    response = result.get("response", {})
    speech = response.get("speech", {})

    plain = speech.get("plain")
    if isinstance(plain, dict) and isinstance(plain.get("speech"), str):
        return plain["speech"]

    ssml = speech.get("ssml")
    if isinstance(ssml, dict) and isinstance(ssml.get("speech"), str):
        return ssml["speech"]

    return "Home Assistant processed the request."
