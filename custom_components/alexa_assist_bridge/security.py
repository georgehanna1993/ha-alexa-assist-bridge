"""Security checks for Alexa web-service requests."""

from __future__ import annotations

from datetime import UTC, datetime
import ipaddress
from typing import Any
from urllib.parse import urlparse

from aiohttp import web

from homeassistant.core import HomeAssistant

MAX_ALEXA_TIMESTAMP_DRIFT_SECONDS = 150
DEBUG_HEADER = "X-Alexa-Assist-Bridge-Debug"


class AlexaSecurityError(ValueError):
    """Raised when an Alexa request fails security checks."""


async def async_validate_alexa_request(
    *,
    hass: HomeAssistant,
    request: web.Request,
    payload: dict[str, Any],
    raw_body: bytes,
    configured_skill_id: str,
    allow_debug_requests: bool,
) -> None:
    """Validate an Alexa request or allow explicitly local debug requests."""
    del hass, raw_body

    if (
        allow_debug_requests
        and request.headers.get(DEBUG_HEADER) == "true"
        and _is_local_or_private_request(request)
    ):
        return

    _validate_skill_id(payload, configured_skill_id)
    _validate_timestamp(payload)
    _validate_required_signature_headers(request)
    _validate_signature_certificate_url(request.headers["SignatureCertChainUrl"])

    raise AlexaSecurityError(
        "Alexa signature verification is not implemented for public requests yet"
    )


def _validate_skill_id(
    payload: dict[str, Any],
    configured_skill_id: str,
) -> None:
    """Validate the Alexa Skill ID when configured."""
    if not configured_skill_id:
        raise AlexaSecurityError("Alexa Skill ID is required for public requests")

    skill_id = (
        payload.get("session", {})
        .get("application", {})
        .get("applicationId")
    )
    if skill_id != configured_skill_id:
        raise AlexaSecurityError("Alexa Skill ID mismatch")


def _validate_timestamp(payload: dict[str, Any]) -> None:
    """Validate Alexa request freshness."""
    timestamp = payload.get("request", {}).get("timestamp")
    if not isinstance(timestamp, str):
        raise AlexaSecurityError("Missing Alexa request timestamp")

    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as err:
        raise AlexaSecurityError("Invalid Alexa request timestamp") from err

    drift = abs((datetime.now(UTC) - parsed).total_seconds())
    if drift > MAX_ALEXA_TIMESTAMP_DRIFT_SECONDS:
        raise AlexaSecurityError("Alexa request timestamp is outside tolerance")


def _validate_required_signature_headers(request: web.Request) -> None:
    """Ensure Alexa signature headers are present."""
    if "SignatureCertChainUrl" not in request.headers:
        raise AlexaSecurityError("Missing SignatureCertChainUrl header")
    if "Signature-256" not in request.headers:
        raise AlexaSecurityError("Missing Signature-256 header")


def _validate_signature_certificate_url(url: str) -> None:
    """Validate the Alexa signing certificate URL shape."""
    parsed = urlparse(url)

    if parsed.scheme != "https":
        raise AlexaSecurityError("Signature certificate URL must use HTTPS")
    if parsed.hostname != "s3.amazonaws.com":
        raise AlexaSecurityError("Signature certificate URL host is not allowed")
    if parsed.port not in {None, 443}:
        raise AlexaSecurityError("Signature certificate URL port is not allowed")
    if not parsed.path.startswith("/echo.api/"):
        raise AlexaSecurityError("Signature certificate URL path is not allowed")


def _is_local_or_private_request(request: web.Request) -> bool:
    """Return true for local/LAN callers that are acceptable for debug tests."""
    remote = request.remote
    if not remote:
        return False

    try:
        address = ipaddress.ip_address(remote.split("%", maxsplit=1)[0])
    except ValueError:
        return False

    return address.is_loopback or address.is_private
