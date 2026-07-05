# AWS Lambda Fallback

The recommended path avoids AWS by using a Home Assistant custom integration endpoint through Nabu Casa.

Use Lambda only if you cannot or do not want to expose the Home Assistant integration endpoint directly.

## Required Configuration

Store these as Lambda environment variables:

```text
HA_URL=https://YOUR-HOME-ASSISTANT-URL
HA_TOKEN=YOUR_LONG_LIVED_ACCESS_TOKEN
ALEXA_SKILL_ID=amzn1.ask.skill.YOUR-SKILL-ID
HA_AGENT_ID=conversation.home_assistant
HA_LANGUAGE=en
```

Never commit real values.

## IAM

The Lambda function should only need basic CloudWatch logging permissions.

It should not need broad AWS permissions.

## API Gateway

For Alexa custom skills, a Lambda ARN endpoint is usually cleaner than API Gateway.

Use API Gateway only if you deliberately choose a generic HTTPS endpoint instead of the Alexa Skills Kit Lambda trigger.
