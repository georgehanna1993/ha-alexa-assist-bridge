# Architecture

## Recommended No-AWS Path

```text
Alexa Echo Device
  -> Alexa Custom Skill
  -> Home Assistant Cloud HTTPS URL
  -> Alexa Assist Bridge custom integration
  -> Home Assistant Conversation API
  -> Configured Conversation Agent
```

This is the preferred architecture for Nabu Casa users.

## Why This Fits Home Assistant

- Home Assistant owns entity exposure.
- Home Assistant owns conversation agent selection.
- Home Assistant owns permissions and Assist pipelines.
- HACS can install the Home Assistant side.
- Users avoid port forwarding, reverse proxies, DuckDNS, and manual certificates.

## Request Validation Requirement

Before the endpoint can be safely exposed, the integration must validate Alexa web-service requests.

Required checks:

- Request body parses as an Alexa Skill request.
- Skill ID matches the configured Skill ID.
- Timestamp is recent enough to prevent replay.
- Signature certificate URL is valid for Alexa.
- Signing certificate is valid for `echo-api.amazon.com`.
- Certificate chain is trusted by the system CA store.
- Request signature matches the body.

The current implementation forwards local debug requests only when the debug header is present, the caller is loopback/private network, and debug mode is explicitly enabled. Public Alexa requests must pass full request validation.

## Optional Lambda Path

Lambda remains useful for users who prefer Amazon-native skill hosting or who cannot expose Home Assistant through Nabu Casa.

Trade-offs:

- Lambda simplifies Alexa trigger security.
- Lambda requires storing a Home Assistant token outside Home Assistant.
- Lambda adds AWS setup, deployment, logs, regions, and timeouts.
