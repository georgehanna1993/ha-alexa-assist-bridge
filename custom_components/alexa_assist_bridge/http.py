"""HTTP endpoint scaffolding for Alexa Assist Bridge.

The public Alexa endpoint is intentionally not registered yet. The next design
step is request validation, including Alexa Skill ID checks and signature
verification for HTTPS web-service endpoints.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AlexaEndpointDesign:
    """Describe the endpoint contract shown to users during setup."""

    path_template: str = "/api/alexa_assist_bridge/{endpoint_id}"
    method: str = "POST"
    content_type: str = "application/json"
