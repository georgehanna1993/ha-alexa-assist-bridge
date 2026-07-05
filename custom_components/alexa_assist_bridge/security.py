"""Security checks for Alexa web-service requests."""

from __future__ import annotations

import asyncio
import base64
from datetime import UTC, datetime
import ipaddress
import posixpath
import ssl
from typing import Any
from urllib.parse import SplitResult, urlsplit, urlunsplit

from aiohttp import web

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

MAX_ALEXA_TIMESTAMP_DRIFT_SECONDS = 150
DEBUG_HEADER = "X-Alexa-Assist-Bridge-Debug"
CERTIFICATE_CACHE_SECONDS = 3600
CERTIFICATE_CACHE_KEY = "alexa_assist_bridge_certificate_cache"
TRUSTED_CA_CACHE_KEY = "alexa_assist_bridge_trusted_ca_cache"
MAX_CERTIFICATE_CHAIN_BYTES = 65536


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
    if (
        allow_debug_requests
        and request.headers.get(DEBUG_HEADER) == "true"
        and _is_local_or_private_request(request)
    ):
        return

    _validate_skill_id(payload, configured_skill_id)
    _validate_timestamp(payload)
    _validate_required_signature_headers(request)
    cert_url = _validated_signature_certificate_url(
        request.headers["SignatureCertChainUrl"]
    )
    certs = await _async_get_certificate_chain(hass, cert_url)
    _validate_certificate_chain(hass, certs)
    _validate_request_signature(
        certs[0],
        request.headers["Signature-256"],
        raw_body,
    )

    return


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


def _validated_signature_certificate_url(url: str) -> str:
    """Validate and normalize the Alexa signing certificate URL."""
    parsed = _normalize_url(url)

    if parsed.scheme.lower() != "https":
        raise AlexaSecurityError("Signature certificate URL must use HTTPS")
    if parsed.hostname is None or parsed.hostname.lower() != "s3.amazonaws.com":
        raise AlexaSecurityError("Signature certificate URL host is not allowed")
    try:
        port = parsed.port
    except ValueError as err:
        raise AlexaSecurityError("Signature certificate URL port is invalid") from err
    if port not in {None, 443}:
        raise AlexaSecurityError("Signature certificate URL port is not allowed")
    if not parsed.path.startswith("/echo.api/"):
        raise AlexaSecurityError("Signature certificate URL path is not allowed")

    return urlunsplit(parsed)


async def _async_get_certificate_chain(hass: HomeAssistant, url: str) -> list:
    """Download and cache the Alexa certificate chain."""
    cache = hass.data.setdefault(CERTIFICATE_CACHE_KEY, {})
    now = datetime.now(UTC).timestamp()
    cached = cache.get(url)
    if cached and cached["expires_at"] > now:
        return cached["certs"]

    session = async_get_clientsession(hass)
    try:
        async with asyncio.timeout(10):
            response = await session.get(url, allow_redirects=False)
            response.raise_for_status()
            if (
                response.content_length is not None
                and response.content_length > MAX_CERTIFICATE_CHAIN_BYTES
            ):
                raise AlexaSecurityError("Alexa certificate chain is too large")
            pem_bytes = await response.read()
    except AlexaSecurityError:
        raise
    except Exception as err:
        raise AlexaSecurityError("Failed to download Alexa certificate chain") from err

    if len(pem_bytes) > MAX_CERTIFICATE_CHAIN_BYTES:
        raise AlexaSecurityError("Alexa certificate chain is too large")

    certs = _load_pem_certificate_chain(pem_bytes)
    cache[url] = {
        "certs": certs,
        "expires_at": now + CERTIFICATE_CACHE_SECONDS,
    }
    return certs


def _normalize_url(url: str) -> SplitResult:
    """Normalize URL dot segments, duplicate slashes, and fragments."""
    parsed = urlsplit(url)
    path = parsed.path
    while "//" in path:
        path = path.replace("//", "/")
    normalized_path = posixpath.normpath(path)
    if not normalized_path.startswith("/"):
        normalized_path = f"/{normalized_path}"
    if parsed.path.endswith("/") and not normalized_path.endswith("/"):
        normalized_path = f"{normalized_path}/"

    return SplitResult(
        scheme=parsed.scheme,
        netloc=parsed.netloc,
        path=normalized_path,
        query=parsed.query,
        fragment="",
    )


def _load_pem_certificate_chain(pem_bytes: bytes) -> list:
    """Load PEM-encoded certificates from the Alexa certificate chain."""
    x509 = _crypto_x509()

    marker = b"-----END CERTIFICATE-----"
    certs = []
    for block in pem_bytes.split(marker):
        if b"-----BEGIN CERTIFICATE-----" not in block:
            continue
        certs.append(x509.load_pem_x509_certificate(block + marker))

    if not certs:
        raise AlexaSecurityError("Alexa certificate chain is empty")

    return certs


def _validate_certificate_chain(hass: HomeAssistant, certs: list) -> None:
    """Validate the Alexa signing certificate and chain."""
    _validate_signing_certificate(certs[0])

    for cert in certs[1:]:
        _validate_certificate_time_bounds(cert)

    for issuer_cert, subject_cert in zip(certs[1:], certs, strict=False):
        _verify_certificate_signed_by(subject_cert, issuer_cert)

    if len(certs) == 1:
        chain_anchor = certs[0]
    else:
        chain_anchor = certs[-1]

    trusted_issuer = _find_trusted_issuer(hass, chain_anchor)
    if trusted_issuer is None:
        raise AlexaSecurityError("Alexa certificate chain is not trusted")

    _verify_certificate_signed_by(chain_anchor, trusted_issuer)


def _validate_signing_certificate(cert: Any) -> None:
    """Validate leaf certificate time bounds and SAN."""
    _validate_certificate_time_bounds(cert)

    x509 = _crypto_x509()
    try:
        san = cert.extensions.get_extension_for_class(
            x509.SubjectAlternativeName
        ).value
    except x509.ExtensionNotFound as err:
        raise AlexaSecurityError("Alexa signing certificate has no SAN") from err

    if "echo-api.amazon.com" not in san.get_values_for_type(x509.DNSName):
        raise AlexaSecurityError("Alexa signing certificate SAN is not allowed")


def _validate_certificate_time_bounds(cert: Any) -> None:
    """Validate certificate time bounds."""
    now = datetime.now(UTC)
    not_before = _cert_not_valid_before(cert)
    not_after = _cert_not_valid_after(cert)

    if not_before > now or not_after < now:
        raise AlexaSecurityError("Certificate is not currently valid")


def _find_trusted_issuer(hass: HomeAssistant, cert: Any) -> Any | None:
    """Find a trusted CA certificate that signed the supplied certificate."""
    for trusted_cert in _trusted_ca_certificates(hass):
        if cert.issuer != trusted_cert.subject:
            continue
        try:
            _verify_certificate_signed_by(cert, trusted_cert)
        except AlexaSecurityError:
            continue
        return trusted_cert

    return None


def _trusted_ca_certificates(hass: HomeAssistant) -> list:
    """Load trusted CA certificates from Python's default SSL context."""
    if TRUSTED_CA_CACHE_KEY in hass.data:
        return hass.data[TRUSTED_CA_CACHE_KEY]

    x509 = _crypto_x509()
    context = ssl.create_default_context()
    certs = [
        x509.load_der_x509_certificate(cert_bytes)
        for cert_bytes in context.get_ca_certs(binary_form=True)
    ]
    hass.data[TRUSTED_CA_CACHE_KEY] = certs
    return certs


def _verify_certificate_signed_by(cert: Any, issuer_cert: Any) -> None:
    """Verify that issuer_cert signed cert."""
    padding = _crypto_padding()
    ec = _crypto_ec()
    rsa = _crypto_rsa()
    invalid_signature = _crypto_invalid_signature()

    public_key = issuer_cert.public_key()
    try:
        if isinstance(public_key, rsa.RSAPublicKey):
            public_key.verify(
                cert.signature,
                cert.tbs_certificate_bytes,
                padding.PKCS1v15(),
                cert.signature_hash_algorithm,
            )
        elif isinstance(public_key, ec.EllipticCurvePublicKey):
            public_key.verify(
                cert.signature,
                cert.tbs_certificate_bytes,
                ec.ECDSA(cert.signature_hash_algorithm),
            )
        else:
            raise AlexaSecurityError("Unsupported certificate public key type")
    except invalid_signature as err:
        raise AlexaSecurityError("Certificate signature verification failed") from err


def _validate_request_signature(
    signing_cert: Any,
    signature_header: str,
    raw_body: bytes,
) -> None:
    """Validate the Alexa request body signature."""
    try:
        signature = base64.b64decode(signature_header, validate=True)
    except ValueError as err:
        raise AlexaSecurityError("Alexa request signature is not base64") from err

    padding = _crypto_padding()
    hashes = _crypto_hashes()
    invalid_signature = _crypto_invalid_signature()

    try:
        signing_cert.public_key().verify(
            signature,
            raw_body,
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
    except invalid_signature as err:
        raise AlexaSecurityError("Alexa request signature is invalid") from err


def _cert_not_valid_before(cert: Any) -> datetime:
    """Return certificate not-before as a timezone-aware datetime."""
    value = getattr(cert, "not_valid_before_utc", None)
    if value is not None:
        return value
    return cert.not_valid_before.replace(tzinfo=UTC)


def _cert_not_valid_after(cert: Any) -> datetime:
    """Return certificate not-after as a timezone-aware datetime."""
    value = getattr(cert, "not_valid_after_utc", None)
    if value is not None:
        return value
    return cert.not_valid_after.replace(tzinfo=UTC)


def _crypto_x509() -> Any:
    """Import cryptography.x509 lazily for Home Assistant runtime."""
    from cryptography import x509

    return x509


def _crypto_padding() -> Any:
    """Import cryptography padding lazily for Home Assistant runtime."""
    from cryptography.hazmat.primitives.asymmetric import padding

    return padding


def _crypto_rsa() -> Any:
    """Import cryptography RSA helpers lazily for Home Assistant runtime."""
    from cryptography.hazmat.primitives.asymmetric import rsa

    return rsa


def _crypto_ec() -> Any:
    """Import cryptography EC helpers lazily for Home Assistant runtime."""
    from cryptography.hazmat.primitives.asymmetric import ec

    return ec


def _crypto_hashes() -> Any:
    """Import cryptography hashes lazily for Home Assistant runtime."""
    from cryptography.hazmat.primitives import hashes

    return hashes


def _crypto_invalid_signature() -> type[Exception]:
    """Import cryptography InvalidSignature lazily for Home Assistant runtime."""
    from cryptography.exceptions import InvalidSignature

    return InvalidSignature


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
