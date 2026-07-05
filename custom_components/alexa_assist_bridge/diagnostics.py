"""Runtime diagnostics for Alexa Assist Bridge."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def initial_diagnostics() -> dict[str, Any]:
    """Create an empty diagnostics payload."""
    return {
        "last_request_at": None,
        "last_request_type": None,
        "last_intent_name": None,
        "last_status": "never_called",
        "last_error": None,
        "last_validation": None,
        "last_response_length": None,
    }


def record_request(
    diagnostics: dict[str, Any],
    payload: dict[str, Any],
) -> None:
    """Record the incoming Alexa request shape without storing utterance text."""
    request = payload.get("request", {})
    intent = request.get("intent", {})

    diagnostics.update(
        {
            "last_request_at": datetime.now(UTC).isoformat(),
            "last_request_type": request.get("type"),
            "last_intent_name": intent.get("name"),
            "last_status": "received",
            "last_error": None,
            "last_response_length": None,
        }
    )


def record_validation(
    diagnostics: dict[str, Any],
    validation: str,
) -> None:
    """Record request validation result."""
    diagnostics["last_validation"] = validation


def record_status(
    diagnostics: dict[str, Any],
    status: str,
    *,
    error: str | None = None,
    response_length: int | None = None,
) -> None:
    """Record the final request status."""
    diagnostics.update(
        {
            "last_status": status,
            "last_error": error,
            "last_response_length": response_length,
        }
    )
