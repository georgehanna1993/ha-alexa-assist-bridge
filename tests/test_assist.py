"""Tests for Assist request preparation helpers."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import types
import unittest

_HA_MODULE = types.ModuleType("homeassistant")
_HA_COMPONENTS_MODULE = types.ModuleType("homeassistant.components")
_CONVERSATION_MODULE = types.ModuleType("homeassistant.components.conversation")
_CORE_MODULE = types.ModuleType("homeassistant.core")


async def _async_converse_stub(**_kwargs):
    raise AssertionError("async_converse should not be called in these tests")


class _ContextStub:
    pass


class _HomeAssistantStub:
    pass


_CONVERSATION_MODULE.async_converse = _async_converse_stub
_CORE_MODULE.Context = _ContextStub
_CORE_MODULE.HomeAssistant = _HomeAssistantStub

sys.modules.setdefault("homeassistant", _HA_MODULE)
sys.modules.setdefault("homeassistant.components", _HA_COMPONENTS_MODULE)
sys.modules.setdefault("homeassistant.components.conversation", _CONVERSATION_MODULE)
sys.modules.setdefault("homeassistant.core", _CORE_MODULE)

_ASSIST_MODULE_PATH = (
    Path(__file__).parents[1]
    / "custom_components"
    / "alexa_assist_bridge"
    / "assist.py"
)

_SPEC = importlib.util.spec_from_file_location("assist_helpers", _ASSIST_MODULE_PATH)
assert _SPEC is not None
assist_helpers = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
sys.modules["assist_helpers"] = assist_helpers
_SPEC.loader.exec_module(assist_helpers)

prepare_text_for_agent = assist_helpers._prepare_text_for_agent


class AssistHelperTest(unittest.TestCase):
    """Tests for Assist helper functions."""

    def test_keeps_builtin_home_assistant_agent_text_unchanged(self) -> None:
        """The built-in agent should receive the exact user phrase."""
        self.assertEqual(
            prepare_text_for_agent(
                text="turn off the TV",
                agent_id="conversation.home_assistant",
                assistant_name="Nabu",
                spoken_response_prompt=True,
            ),
            "turn off the TV",
        )

    def test_wraps_llm_agent_text_for_spoken_response(self) -> None:
        """LLM agents receive voice-oriented instructions."""
        prepared = prepare_text_for_agent(
            text="why is the living room hot?",
            agent_id="conversation.google_generative_ai",
            assistant_name="Nabu",
            spoken_response_prompt=True,
        )

        self.assertIn("You are Nabu", prepared)
        self.assertIn("Alexa skill", prepared)
        self.assertIn("User request: why is the living room hot?", prepared)

    def test_can_disable_spoken_response_prompt(self) -> None:
        """Users can disable prompt wrapping."""
        self.assertEqual(
            prepare_text_for_agent(
                text="what is on my calendar?",
                agent_id="conversation.google_generative_ai",
                assistant_name="Nabu",
                spoken_response_prompt=False,
            ),
            "what is on my calendar?",
        )


if __name__ == "__main__":
    unittest.main()
