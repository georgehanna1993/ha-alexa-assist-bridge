# Home Assistant Alexa Assist Bridge

Let Amazon Alexa devices talk to Home Assistant Assist, so Home Assistant remains the AI brain.

This project is for users who want an Alexa+-like experience in places where Alexa+ is unavailable, while keeping Home Assistant in control of devices, sensors, calendars, scripts, automations, and AI provider selection.

Example:

```text
Alexa, ask Nabu what lights are on.
Alexa, ask Nabu what's on my calendar today.
Alexa, ask Nabu turn off the TV.
```

## Project Status

This repository is in early development.

Current scope:

- Home Assistant custom integration scaffold
- Local debug HTTP endpoint for testing Assist forwarding
- Alexa request parsing and response formatting
- Alexa web-service request validation
- Configurable assistant display name
- Authenticated last-request diagnostics endpoint
- HACS-compatible repository layout
- Alexa custom skill interaction model placeholder
- Architecture and setup documentation

Not yet implemented:

- Optional AWS Lambda bridge
- Release packaging

## Recommended Architecture

The preferred architecture is:

```text
Alexa Echo Device
  -> Custom Alexa Skill
  -> Home Assistant custom integration endpoint
  -> Home Assistant Assist / Conversation API
  -> Configured Conversation Agent
  -> Alexa spoken response
```

For users with Nabu Casa, the Alexa Skill endpoint should use the secure Home Assistant Cloud remote URL:

```text
https://YOUR-NABU-CASA-REMOTE-URL.ui.nabu.casa/api/alexa_assist_bridge/YOUR_ENDPOINT_ID
```

Replace `YOUR-NABU-CASA-REMOTE-URL` and `YOUR_ENDPOINT_ID` with values from your own Home Assistant installation.

## Why Not Replace Alexa Directly?

Amazon does not allow third-party projects to replace Alexa's built-in assistant on Echo devices. This project uses a custom skill invocation such as:

```text
Alexa, ask Nabu ...
Alexa, open Nabu ...
Alexa, ask Home Assistant ...
```

## Supported AI Providers

This project delegates AI behavior to Home Assistant Assist. Any provider supported by Home Assistant conversation agents can work, including:

- Home Assistant Local Conversation Agent
- OpenAI
- Google Gemini
- Ollama
- Local LLMs
- Future Home Assistant conversation agents

## Home Assistant Requirements

- Home Assistant 2026.6 or newer is the initial development target.
- Home Assistant Assist must be configured.
- At least one Assist pipeline must exist.
- For the recommended no-AWS architecture, external HTTPS access is required.
- Nabu Casa Home Assistant Cloud is recommended for external HTTPS access.

## Installation With HACS

This project is not published to the HACS default repository list yet.

When custom repository installation is available:

1. Open Home Assistant.
2. Go to HACS.
3. Open the three-dot menu.
4. Choose **Custom repositories**.
5. Add:

   ```text
   https://github.com/georgehanna1993/ha-alexa-assist-bridge
   ```

6. Select category **Integration**.
7. Install **Alexa Assist Bridge**.
8. Restart Home Assistant.
9. Go to **Settings -> Devices & services -> Add integration**.
10. Search for **Alexa Assist Bridge**.

During setup, Home Assistant asks for:

- `Alexa Skill ID`: leave blank for local debug testing.
- `Conversation agent ID`: usually `conversation.home_assistant`.
- `Assistant name`: the name used in help responses, for example `Nabu`.
- `Endpoint ID`: keep the generated value unless you know why you want to change it.
- `Language`: usually `en`.
- `Allow unsigned local debug requests`: enable for local testing only.

You can change these later from **Settings -> Devices & services -> Alexa Assist Bridge -> Configure**.

## Local Testing

After adding the integration, test from your local network before configuring Alexa.

Replace:

- `HA_LOCAL_URL` with your local Home Assistant URL, for example `http://homeassistant.local:8123`.
- `YOUR_ENDPOINT_ID` with the endpoint ID shown during setup.

```bash
curl -X POST \
  "HA_LOCAL_URL/api/alexa_assist_bridge/YOUR_ENDPOINT_ID" \
  -H "Content-Type: application/json" \
  -H "X-Alexa-Assist-Bridge-Debug: true" \
  -d '{"query":"what lights are on?"}'
```

Expected shape:

```json
{
  "version": "1.0",
  "response": {
    "outputSpeech": {
      "type": "PlainText",
      "text": "..."
    },
    "shouldEndSession": true
  }
}
```

Unsigned debug requests are accepted only when the debug header is present, the caller is loopback/private network, and debug mode is enabled in the integration config entry. Do not expose unsigned debug requests through Nabu Casa.

## Diagnostics

The integration exposes an authenticated diagnostics endpoint for troubleshooting.

Replace `HA_LOCAL_URL` and `YOUR_ENDPOINT_ID`:

```text
HA_LOCAL_URL/api/alexa_assist_bridge/YOUR_ENDPOINT_ID/diagnostics
```

This endpoint requires Home Assistant authentication. It reports the last request type, last intent name, validation status, final status, and last error. It does not store the full spoken query.

## Alexa Developer Console

The Alexa Skill cannot be installed by HACS. It must be created in Amazon's Alexa Developer Console.

High-level steps:

1. Create a custom skill.
2. Choose an invocation name, for example `nabu`.
3. Add a catch-all intent using `AMAZON.SearchQuery`.
4. Configure the endpoint.
5. Test with the Alexa simulator.

Recommended first Alexa test path:

1. In the Alexa Developer Console, create a **Custom** skill.
2. Choose **Provision your own** backend.
3. Set the invocation name to `nabu`.
4. Import the interaction model from `skill/interaction-model/en-US.json`.
   This model contains multiple carrier intents such as `what {query}` and `turn {query}` so Alexa routes free-form phrases to Home Assistant Assist instead of `AMAZON.FallbackIntent`.
5. Copy the Alexa Skill ID.
6. In Home Assistant, open **Settings -> Devices & services -> Alexa Assist Bridge -> Configure** and paste the Alexa Skill ID exactly.
7. Set the Alexa endpoint type to **HTTPS**.
8. Use your Nabu Casa endpoint URL:

   ```text
   https://YOUR-NABU-CASA-REMOTE-URL.ui.nabu.casa/api/alexa_assist_bridge/YOUR_ENDPOINT_ID
   ```

9. Test in the Alexa simulator:

   ```text
   ask nabu what lights are on
   ```

The no-AWS Nabu Casa HTTPS path has been tested successfully with the Alexa simulator and an Echo device.

Required values:

- `Alexa Skill ID`
- `Invocation name`
- `Endpoint URL`
- `Region`

Never commit these values if they are private to your installation.

## Backend Options

### Recommended: No AWS

Use the Home Assistant custom integration endpoint through Nabu Casa.

Pros:

- No Lambda to deploy.
- No Long-Lived Access Token stored in AWS.
- Home Assistant remains the security boundary.
- Best fit for HACS users.

Cons:

- The integration must validate Alexa web-service requests correctly.
- Users need Home Assistant Cloud or another trusted HTTPS endpoint.

### Fallback: AWS Lambda

Use Lambda as a small translator between Alexa and Home Assistant's Conversation API.

Required environment variables:

```text
HA_URL=https://YOUR-HOME-ASSISTANT-URL
HA_TOKEN=YOUR_LONG_LIVED_ACCESS_TOKEN
ALEXA_SKILL_ID=amzn1.ask.skill.YOUR-SKILL-ID
HA_AGENT_ID=conversation.home_assistant
HA_LANGUAGE=en
```

Never commit real values.

## Home Assistant Setup

1. Configure Assist.
2. Configure your preferred conversation agent.
3. Configure an Assist pipeline.
4. Expose only the entities you want Assist to control.
5. Confirm your Nabu Casa remote URL works over HTTPS.

For Lambda fallback only:

1. Create a Home Assistant Long-Lived Access Token.
2. Store it as a Lambda environment variable.
3. Never place it in source code, documentation, screenshots, or issue reports.

## Testing Phrases

```text
Alexa, ask Nabu what lights are on.
Alexa, ask Nabu what's on today's calendar.
Alexa, ask Nabu why the living room is hot.
Alexa, ask Nabu turn off the TV.
Alexa, ask Nabu summarize yesterday's activity.
```

## Troubleshooting

Common issues:

- Invalid Home Assistant token
- Nabu Casa remote URL unavailable
- HTTPS endpoint misconfigured
- Alexa Skill ID mismatch
- Alexa endpoint region mismatch
- Home Assistant Assist pipeline not configured
- Conversation agent missing
- Lambda timeout
- Home Assistant unreachable from Lambda
- Alexa session timeout
- Incorrect Alexa intent model
- Alexa routes requests to `AMAZON.FallbackIntent`; re-import `skill/interaction-model/en-US.json`, save, and build the model
- Home Assistant returns help text for routed intents; redownload the HACS integration and restart Home Assistant so the latest parser code is loaded

## Security

- Never commit secrets.
- Use environment variables for backend secrets.
- Prefer the no-AWS Home Assistant endpoint when possible.
- Use HTTPS only.
- Use least-privilege access.
- Rotate Long-Lived Access Tokens if exposed.
- Treat Alexa request validation as mandatory before using any public endpoint.

## Development

This repository is intentionally structured as one project:

- `custom_components/alexa_assist_bridge/` for the Home Assistant integration
- `skill/` for Alexa Skill interaction model assets
- `docs/` for architecture and setup guides
- `.github/` for contribution workflow

## License

MIT
