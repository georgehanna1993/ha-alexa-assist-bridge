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
    assistant_name: str,
    spoken_response_prompt: bool,
) -> AssistBridgeResult:
    """Send text to Home Assistant Assist and normalize the response."""
    result = await async_converse(
        hass=hass,
        text=_prepare_text_for_agent(
            text=text,
            agent_id=agent_id,
            assistant_name=assistant_name,
            spoken_response_prompt=spoken_response_prompt,
        ),
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


def _prepare_text_for_agent(
    *,
    text: str,
    agent_id: str | None,
    assistant_name: str,
    spoken_response_prompt: bool,
) -> str:
    """Optionally wrap LLM requests with voice-assistant instructions."""
    if not spoken_response_prompt or agent_id == "conversation.home_assistant":
        return text

    return (
        f"You are {assistant_name}, a concise voice assistant inside Home Assistant. "
        "The user is speaking through an Alexa skill, so answer naturally for speech. "
        "Use Home Assistant context and tools when relevant. "
        "Keep most answers to 1-3 short sentences unless the user asks for detail. "
        f"User request: {text}"
    )
