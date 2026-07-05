# Architecture

## Recommended No-AWS Path

```text
Alexa Echo Device
  -> Alexa Custom Skill
  -> Home Assistant Cloud HTTPS URL
  -> Alexa Assist Bridge custom integration
  -> Home Assistant Conversation API with Alexa session conversation ID
  -> Configured Conversation Agent
```

This is the preferred architecture for Nabu Casa users.

## Why This Fits Home Assistant

- Home Assistant owns entity exposure.
- Home Assistant owns conversation agent selection.
- Home Assistant owns permissions and Assist pipelines.
- HACS can install the Home Assistant side.
- Users avoid port forwarding, reverse proxies, DuckDNS, and manual certificates.
- Alexa sessions can remain open for follow-up turns.
- Home Assistant remains the place where Gemini/OpenAI/Ollama/local agents are selected.

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

## Diagnostics

The integration keeps lightweight runtime diagnostics for the most recent request and exposes them through a diagnostic sensor plus an authenticated diagnostics endpoint:

- request time
- request type
- intent name
- validation result
- final status
- short error message

It does not store the full user utterance.

## Conversation Behavior

The bridge passes the Alexa `sessionId` to Home Assistant as the conversation ID. This allows conversation agents that support context to treat follow-up turns as part of the same conversation.

Alexa session closing is configurable:

- `assist`: respect Home Assistant's `continue_conversation` value.
- `always`: keep Alexa listening after successful responses.
- `never`: close after every response.

For LLM-backed agents, the bridge can optionally wrap each request with concise spoken-assistant instructions. The wrapper is skipped for `conversation.home_assistant` so built-in local intents receive the original phrase.

Live web search depends on the selected Home Assistant conversation agent or future optional tools.

Launch requests are handled locally by the bridge. `Alexa, open Nabu` returns an open-session greeting and does not call Home Assistant Assist until the user asks the first question.

## Optional Lambda Path

Lambda remains useful for users who prefer Amazon-native skill hosting or who cannot expose Home Assistant through Nabu Casa.

Trade-offs:

- Lambda simplifies Alexa trigger security.
- Lambda requires storing a Home Assistant token outside Home Assistant.
- Lambda adds AWS setup, deployment, logs, regions, and timeouts.
