# Security Policy

## Reporting a Vulnerability

Please do not disclose security issues publicly until they have been reviewed.

Open a private security advisory on GitHub or contact the maintainer privately.

## Secrets

Never include these in issues, pull requests, logs, screenshots, or documentation:

- Home Assistant Long-Lived Access Tokens
- Nabu Casa remote URLs if you consider them private
- Alexa Skill IDs for private skills
- AWS access keys
- Lambda environment variable values

## Public Endpoint Safety

The Home Assistant endpoint must validate Alexa requests before forwarding text to Assist. Until request validation is implemented and reviewed, do not expose development endpoints to the public internet.
