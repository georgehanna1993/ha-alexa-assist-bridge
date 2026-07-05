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

The first implementation uses a catch-all `AMAZON.SearchQuery` slot so Alexa passes the user's request text to Home Assistant Assist.

## Endpoint

For the recommended no-AWS path, the endpoint will be your Home Assistant Cloud URL plus the bridge endpoint path:

```text
https://YOUR-NABU-CASA-REMOTE-URL.ui.nabu.casa/api/alexa_assist_bridge/YOUR_ENDPOINT_ID
```

The local debug endpoint exists for LAN testing, but public Alexa signature verification is not complete yet. Do not expose unsigned debug requests through Nabu Casa.
