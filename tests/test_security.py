"""Tests for Alexa request security helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import importlib.util
from pathlib import Path
import sys
import types
import unittest


def _install_import_stubs() -> None:
    """Install lightweight stubs for optional Home Assistant runtime imports."""
    aiohttp = types.ModuleType("aiohttp")
    web = types.SimpleNamespace(Request=object)
    aiohttp.web = web
    sys.modules.setdefault("aiohttp", aiohttp)

    homeassistant = types.ModuleType("homeassistant")
    homeassistant_core = types.ModuleType("homeassistant.core")
    homeassistant_core.HomeAssistant = object

    homeassistant_helpers = types.ModuleType("homeassistant.helpers")
    aiohttp_client = types.ModuleType("homeassistant.helpers.aiohttp_client")
    aiohttp_client.async_get_clientsession = lambda hass: None

    sys.modules.setdefault("homeassistant", homeassistant)
    sys.modules.setdefault("homeassistant.core", homeassistant_core)
    sys.modules.setdefault("homeassistant.helpers", homeassistant_helpers)
    sys.modules.setdefault("homeassistant.helpers.aiohttp_client", aiohttp_client)


_install_import_stubs()

_SECURITY_MODULE_PATH = (
    Path(__file__).parents[1]
    / "custom_components"
    / "alexa_assist_bridge"
    / "security.py"
)

_SPEC = importlib.util.spec_from_file_location("security_helpers", _SECURITY_MODULE_PATH)
assert _SPEC is not None
security_helpers = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(security_helpers)

AlexaSecurityError = security_helpers.AlexaSecurityError


class SecurityHelperTest(unittest.TestCase):
    """Tests for public Alexa security helper behavior."""

    def test_normalizes_valid_alexa_certificate_url(self) -> None:
        """Alexa certificate URLs are normalized before validation."""
        url = security_helpers._validated_signature_certificate_url(
            "https://s3.amazonaws.com/echo.api/../echo.api/echo-api-cert.pem#x"
        )

        self.assertEqual(
            url,
            "https://s3.amazonaws.com/echo.api/echo-api-cert.pem",
        )

    def test_rejects_invalid_certificate_url_host(self) -> None:
        """Certificate URLs must be hosted by Amazon's expected S3 host."""
        with self.assertRaises(AlexaSecurityError):
            security_helpers._validated_signature_certificate_url(
                "https://example.com/echo.api/echo-api-cert.pem"
            )

    def test_rejects_invalid_certificate_url_path_case(self) -> None:
        """The normalized path prefix is case-sensitive."""
        with self.assertRaises(AlexaSecurityError):
            security_helpers._validated_signature_certificate_url(
                "https://s3.amazonaws.com/EcHo.aPi/echo-api-cert.pem"
            )

    def test_rejects_invalid_certificate_url_port(self) -> None:
        """Malformed ports are rejected as security errors."""
        with self.assertRaises(AlexaSecurityError):
            security_helpers._validated_signature_certificate_url(
                "https://s3.amazonaws.com:bad/echo.api/echo-api-cert.pem"
            )

    def test_validates_matching_skill_id(self) -> None:
        """Configured Skill IDs must match the request application ID."""
        security_helpers._validate_skill_id(
            {
                "session": {
                    "application": {
                        "applicationId": "amzn1.ask.skill.test",
                    }
                }
            },
            "amzn1.ask.skill.test",
        )

    def test_rejects_mismatched_skill_id(self) -> None:
        """Mismatched Skill IDs are rejected."""
        with self.assertRaises(AlexaSecurityError):
            security_helpers._validate_skill_id(
                {
                    "session": {
                        "application": {
                            "applicationId": "amzn1.ask.skill.wrong",
                        }
                    }
                },
                "amzn1.ask.skill.expected",
            )

    def test_accepts_fresh_timestamp(self) -> None:
        """Fresh Alexa timestamps are accepted."""
        timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        security_helpers._validate_timestamp({"request": {"timestamp": timestamp}})

    def test_rejects_stale_timestamp(self) -> None:
        """Requests older than Alexa's tolerance are rejected."""
        timestamp = (
            datetime.now(UTC) - timedelta(seconds=151)
        ).isoformat().replace("+00:00", "Z")

        with self.assertRaises(AlexaSecurityError):
            security_helpers._validate_timestamp({"request": {"timestamp": timestamp}})

    def test_rejects_non_base64_request_signature(self) -> None:
        """Malformed signature headers fail before cryptography work."""
        with self.assertRaises(AlexaSecurityError):
            security_helpers._validate_request_signature(
                signing_cert=object(),
                signature_header="not base64!",
                raw_body=b"{}",
            )


if __name__ == "__main__":
    unittest.main()
