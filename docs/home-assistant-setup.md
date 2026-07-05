# Home Assistant Setup

## Assist

Confirm that Assist is configured:

1. Open Home Assistant.
2. Go to **Settings -> Voice assistants**.
3. Confirm at least one Assist pipeline exists.
4. Choose the conversation agent you want Alexa requests to use.

## Nabu Casa

For the recommended architecture:

1. Open **Settings -> Home Assistant Cloud**.
2. Confirm Remote Control is enabled.
3. Copy your remote URL.
4. Confirm it starts with `https://`.

Example placeholder:

```text
https://YOUR-NABU-CASA-REMOTE-URL.ui.nabu.casa
```

Do not commit your real URL if you consider it private.

## Entity Exposure

Assist can only control and reason about what Home Assistant allows it to use.

Review exposed entities in Home Assistant and keep the list intentional.

## Choosing A Conversation Agent

For basic Home Assistant intents, use:

```text
conversation.home_assistant
```

For reasoning and chat, install and configure a Home Assistant conversation integration such as Google Generative AI Conversation, OpenAI Conversation, Ollama, or another local LLM provider. Then set `Conversation agent ID` to that entity, for example:

```text
conversation.google_generative_ai
```

If the new conversation agent does not appear after installation, restart Home Assistant and check the bridge options again.

## Conversation Mode

Use one of:

- `assist`: follow the conversation agent's `continue_conversation` value.
- `always`: keep Alexa listening after successful answers.
- `never`: close the Alexa session after every answer.

For an Alexa+-like chat experience, start with `always`. You can still say `stop` or `cancel` to close the skill.

## Spoken LLM Prompting

When enabled, the bridge adds voice-oriented instructions before sending a request to non-default LLM agents. This helps Gemini/OpenAI/Ollama answer briefly and naturally through Alexa.

The bridge intentionally skips this wrapper for `conversation.home_assistant`, because built-in Home Assistant intents work best with the exact phrase the user said.

## Local Debug Test

The integration supports local unsigned debug requests so you can verify Assist forwarding before configuring Alexa.

Replace:

- `HA_LOCAL_URL` with your local Home Assistant URL.
- `YOUR_ENDPOINT_ID` with the endpoint ID from the integration setup form.

```bash
curl -X POST \
  "HA_LOCAL_URL/api/alexa_assist_bridge/YOUR_ENDPOINT_ID" \
  -H "Content-Type: application/json" \
  -H "X-Alexa-Assist-Bridge-Debug: true" \
  -d '{"query":"what lights are on?"}'
```

Only keep unsigned debug requests enabled while testing locally.

## Updating Options

After creating the Alexa Skill, open:

```text
Settings -> Devices & services -> Alexa Assist Bridge -> Configure
```

Paste the Alexa Skill ID exactly as shown in the Alexa Developer Console.

You can also update the assistant display name, conversation agent, conversation mode, and spoken-response prompt setting here. The assistant display name controls help text only; Alexa recognition is controlled by the invocation name in the Alexa Developer Console.

## Diagnostics

The integration creates a diagnostic entity named **Alexa Assist Bridge Status**. Use it to check whether the most recent request was accepted, rejected, routed to help, or failed while calling Assist.

After signing in to Home Assistant, open:

```text
HA_LOCAL_URL/api/alexa_assist_bridge/YOUR_ENDPOINT_ID/diagnostics
```

The response shows the last request type, intent name, validation result, status, and error without storing the full utterance.
