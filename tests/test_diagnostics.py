"""Tests for runtime diagnostics helpers."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

_DIAGNOSTICS_MODULE_PATH = (
    Path(__file__).parents[1]
    / "custom_components"
    / "alexa_assist_bridge"
    / "diagnostics.py"
)

_SPEC = importlib.util.spec_from_file_location(
    "diagnostics_helpers",
    _DIAGNOSTICS_MODULE_PATH,
)
assert _SPEC is not None
diagnostics_helpers = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(diagnostics_helpers)


class DiagnosticsHelperTest(unittest.TestCase):
    """Tests for diagnostics helper functions."""

    def test_records_request_shape_without_utterance_text(self) -> None:
        """Diagnostics should capture intent metadata without slot text."""
        diagnostics = diagnostics_helpers.initial_diagnostics()
        diagnostics_helpers.record_request(
            diagnostics,
            {
                "request": {
                    "type": "IntentRequest",
                    "intent": {
                        "name": "AskAssistWhatIntent",
                        "slots": {"query": {"value": "private text"}},
                    },
                }
            },
        )

        self.assertEqual(diagnostics["last_request_type"], "IntentRequest")
        self.assertEqual(diagnostics["last_intent_name"], "AskAssistWhatIntent")
        self.assertEqual(diagnostics["last_status"], "received")
        self.assertNotIn("private text", str(diagnostics))

    def test_records_status(self) -> None:
        """Final status and response length are stored."""
        diagnostics = diagnostics_helpers.initial_diagnostics()
        diagnostics_helpers.record_status(
            diagnostics,
            "ok",
            response_length=12,
        )

        self.assertEqual(diagnostics["last_status"], "ok")
        self.assertEqual(diagnostics["last_response_length"], 12)


if __name__ == "__main__":
    unittest.main()
