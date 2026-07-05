# Contributing

Thanks for helping improve Home Assistant Alexa Assist Bridge.

## Project Principles

- Home Assistant remains the source of truth.
- No secrets in code, docs, issues, logs, screenshots, or tests.
- Prefer Nabu Casa remote access over manual tunnels or port forwarding.
- Keep the Home Assistant integration HACS-friendly.
- Keep Alexa and backend setup beginner-friendly.
- Validate public requests before forwarding anything to Home Assistant Assist.

## Development Setup

This repository starts as a Home Assistant custom integration plus Alexa Skill assets.

Useful checks:

```bash
python -m compileall custom_components
python -m json.tool custom_components/alexa_assist_bridge/manifest.json
python -m json.tool hacs.json
python -m json.tool skill/interaction-model/en-US.json
```

## Pull Requests

Before opening a pull request:

- Explain the user-facing behavior change.
- Add or update docs.
- Add tests where practical.
- Avoid unrelated formatting churn.
- Confirm no secrets are included.

## Security Issues

Please do not open public issues for suspected security vulnerabilities. See `SECURITY.md`.
