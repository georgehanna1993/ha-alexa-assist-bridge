# Alexa Skill Setup

## Create the Skill

1. Open the Alexa Developer Console.
2. Create a new skill.
3. Choose **Custom**.
4. Choose **Provision your own** backend.
5. Pick a default language such as `English (US)`.

## Invocation Name

Recommended examples:

```text
nabu
home assistant
my home
```

Example phrases:

```text
Alexa, ask Nabu what lights are on.
Alexa, ask Nabu turn off the TV.
Alexa, open Nabu.
```

## Interaction Model

Use the starter model in:

```text
skill/interaction-model/en-US.json
```

The interaction model uses `AMAZON.SearchQuery` slots with multiple carrier intents, such as `what {query}` and `turn {query}`, so Alexa passes the user's request text to Home Assistant Assist.

If the Alexa simulator shows `AMAZON.FallbackIntent` in JSON Input, re-import the interaction model, save it, and build the model again.

## Endpoint

For the recommended no-AWS path, the endpoint will be your Home Assistant Cloud URL plus the bridge endpoint path:

```text
https://YOUR-NABU-CASA-REMOTE-URL.ui.nabu.casa/api/alexa_assist_bridge/YOUR_ENDPOINT_ID
```

## Skill ID

After you create the skill, copy the Alexa Skill ID from the Alexa Developer Console and paste it into **Settings -> Devices & services -> Alexa Assist Bridge -> Configure**.

The Skill ID must match exactly, for example:

```text
amzn1.ask.skill.YOUR-SKILL-ID
```

## HTTPS Endpoint Test

Use the Alexa simulator with:

```text
ask nabu what lights are on
```

Alexa public requests are validated with the Alexa Skill ID, timestamp freshness, certificate-chain URL checks, certificate validity, and request signature verification. Keep unsigned debug requests for local LAN testing only.
