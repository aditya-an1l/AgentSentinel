# Nebius Token Factory configuration

AgentSentinel uses the OpenAI Python client with an OpenAI-compatible base URL.

1. Configure an endpoint in the Nebius Token Factory console.
2. Add its API key and exact base URL to `.env`.
3. Verify which Nemotron models are available to your account.
4. Set `NEMOTRON_NANO_MODEL` for inline screening and `NEMOTRON_ULTRA_MODEL` for escalation analysis.
5. Restart the backend and check `/api/health` for `model_mode: nebius`.

The model strings in `.env.example` are examples to verify, not a guarantee that they are currently available. With no API key, the mock path makes no model request. This MVP does not use Nemotron Super, and it makes no token-cost or latency claims.
