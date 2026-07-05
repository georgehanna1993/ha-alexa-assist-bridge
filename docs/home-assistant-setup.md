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
