"""Tests for Alexa request and response helpers."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

_ALEXA_MODULE_PATH = (
    Path(__file__).parents[1]
    / "custom_components"
    / "alexa_assist_bridge"
    / "alexa.py"
)

_SPEC = importlib.util.spec_from_file_location("alexa_helpers", _ALEXA_MODULE_PATH)
assert _SPEC is not None
alexa_helpers = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(alexa_helpers)

AlexaRequestError = alexa_helpers.AlexaRequestError
alexa_plain_text_response = alexa_helpers.alexa_plain_text_response
extract_alexa_query = alexa_helpers.extract_alexa_query
is_stop_or_cancel_request = alexa_helpers.is_stop_or_cancel_request


class AlexaHelperTest(unittest.TestCase):
    """Tests for Alexa helper functions."""

    def test_extracts_query_from_local_debug_payload(self) -> None:
        """Local debug payloads can use a simple query field."""
        self.assertEqual(
            extract_alexa_query({"query": " what lights are on? "}),
            "what lights are on?",
        )

    def test_extracts_query_from_alexa_intent_request(self) -> None:
        """Alexa AskAssistIntent slot values are forwarded to Assist."""
        payload = {
            "request": {
                "type": "IntentRequest",
                "intent": {
                    "name": "AskAssistIntent",
                    "slots": {
                        "query": {
                            "name": "query",
                            "value": "turn off the TV",
                        }
                    },
                },
            }
        }

        self.assertEqual(extract_alexa_query(payload), "turn off the TV")

    def test_launch_request_raises_for_help_response(self) -> None:
        """LaunchRequest should produce help instead of forwarding empty text."""
        with self.assertRaises(AlexaRequestError):
            extract_alexa_query({"request": {"type": "LaunchRequest"}})

    def test_detects_stop_and_cancel_requests(self) -> None:
        """Stop and cancel intents should close the skill cleanly."""
        self.assertTrue(
            is_stop_or_cancel_request(
                {
                    "request": {
                        "type": "IntentRequest",
                        "intent": {"name": "AMAZON.StopIntent"},
                    }
                }
            )
        )

    def test_plain_text_response_shape(self) -> None:
        """Alexa responses include the expected outputSpeech shape."""
        response = alexa_plain_text_response("Done", should_end_session=False)

        self.assertEqual(
            response,
            {
                "version": "1.0",
                "response": {
                    "outputSpeech": {
                        "type": "PlainText",
                        "text": "Done",
                    },
                    "shouldEndSession": False,
                },
            },
        )


if __name__ == "__main__":
    unittest.main()
