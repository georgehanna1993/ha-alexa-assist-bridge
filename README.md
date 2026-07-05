# Home Assistant Alexa Assist Bridge

Let Amazon Alexa devices talk to Home Assistant Assist, so Home Assistant remains the AI brain.

This project is for users who want an Alexa+-like experience in places where Alexa+ is unavailable, while keeping Home Assistant in control of devices, sensors, calendars, scripts, automations, and AI provider selection.

Example:

```text
Alexa, ask Jarvis what lights are on.
Alexa, ask Jarvis what's on my calendar today.
Alexa, ask Jarvis turn off the TV.
```

## Project Status

This repository is in early development.

Current scope:

- Home Assistant custom integration scaffold
- HACS-compatible repository layout
- Alexa custom skill interaction model placeholder
- Architecture and setup documentation

Not yet implemented:

- Alexa request validation
- Home Assistant Assist request forwarding
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
Alexa, ask Jarvis ...
Alexa, open Jarvis ...
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

## Alexa Developer Console

The Alexa Skill cannot be installed by HACS. It must be created in Amazon's Alexa Developer Console.

High-level steps:

1. Create a custom skill.
2. Choose an invocation name, for example `jarvis`.
3. Add a catch-all intent using `AMAZON.SearchQuery`.
4. Configure the endpoint.
5. Test with the Alexa simulator.

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
Alexa, ask Jarvis what lights are on.
Alexa, ask Jarvis what's on today's calendar.
Alexa, ask Jarvis why the living room is hot.
Alexa, ask Jarvis turn off the TV.
Alexa, ask Jarvis summarize yesterday's activity.
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
