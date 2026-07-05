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
alexa_help_response = alexa_helpers.alexa_help_response
alexa_launch_response = alexa_helpers.alexa_launch_response
extract_alexa_query = alexa_helpers.extract_alexa_query
is_launch_request = alexa_helpers.is_launch_request
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

    def test_reconstructs_question_intent_prefix(self) -> None:
        """Question carrier intents are reconstructed for Assist."""
        payload = {
            "request": {
                "type": "IntentRequest",
                "intent": {
                    "name": "AskAssistWhatIntent",
                    "slots": {
                        "query": {
                            "name": "query",
                            "value": "lights are on",
                        }
                    },
                },
            }
        }

        self.assertEqual(extract_alexa_query(payload), "what lights are on")

    def test_reconstructs_action_intent_prefix(self) -> None:
        """Action carrier intents are reconstructed for Assist."""
        payload = {
            "request": {
                "type": "IntentRequest",
                "intent": {
                    "name": "AskAssistTurnIntent",
                    "slots": {
                        "query": {
                            "name": "query",
                            "value": "off the TV",
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

    def test_detects_launch_request(self) -> None:
        """LaunchRequest should open chat mode."""
        self.assertTrue(is_launch_request({"request": {"type": "LaunchRequest"}}))
        self.assertFalse(
            is_launch_request(
                {
                    "request": {
                        "type": "IntentRequest",
                        "intent": {"name": "AskAssistIntent"},
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

    def test_help_response_uses_assistant_name(self) -> None:
        """Help responses can use the configured assistant name."""
        response = alexa_help_response("Home Helper")

        self.assertEqual(
            response["response"]["outputSpeech"]["text"],
            "Ask Home Helper a Home Assistant question, like what lights are on.",
        )
        self.assertEqual(
            response["response"]["reprompt"]["outputSpeech"]["text"],
            "What would you like to ask?",
        )

    def test_launch_response_opens_chat_mode(self) -> None:
        """Launch responses should keep the session open for the first question."""
        response = alexa_launch_response("Home Helper")

        self.assertEqual(
            response["response"]["outputSpeech"]["text"],
            "Hi, I'm Home Helper. What do you want to ask?",
        )
        self.assertFalse(response["response"]["shouldEndSession"])
        self.assertEqual(
            response["response"]["reprompt"]["outputSpeech"]["text"],
            "What would you like to ask Home Helper?",
        )

    def test_reprompt_is_included_when_session_stays_open(self) -> None:
        """Open Alexa sessions include a reprompt."""
        response = alexa_plain_text_response(
            "Sure.",
            should_end_session=False,
            reprompt_text="Anything else?",
        )

        self.assertEqual(
            response["response"]["reprompt"]["outputSpeech"]["text"],
            "Anything else?",
        )

    def test_follow_up_is_spoken_when_session_stays_open(self) -> None:
        """Open Alexa sessions can include an audible follow-up cue."""
        response = alexa_plain_text_response(
            "The living room is warm because the blinds are open.",
            should_end_session=False,
            follow_up_text="Anything else?",
        )

        self.assertEqual(
            response["response"]["outputSpeech"]["text"],
            "The living room is warm because the blinds are open. Anything else?",
        )

    def test_follow_up_is_not_spoken_when_session_closes(self) -> None:
        """Closed sessions should not append the follow-up cue."""
        response = alexa_plain_text_response(
            "Done.",
            should_end_session=True,
            follow_up_text="Anything else?",
        )

        self.assertEqual(
            response["response"]["outputSpeech"]["text"],
            "Done.",
        )


if __name__ == "__main__":
    unittest.main()
