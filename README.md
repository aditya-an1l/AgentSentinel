# AgentSentinel

**A runtime tool-call security proxy and flight recorder for AI agents.**

AgentSentinel intercepts supported tool calls before execution, applies deterministic policy checks, optionally classifies calls with NVIDIA Nemotron through Nebius Token Factory, and records decisions in SQLite.

## What is implemented in this MVP

- FastAPI proxy endpoint for structured tool calls.
- Deterministic screening for destructive shell commands, shell operators, path traversal, sensitive-file paths, and obvious credential-exfiltration patterns.
- Configurable Nebius Token Factory integration through an OpenAI-compatible client.
- Clearly labelled local mock mode when no Nebius API key is configured.
- Optional deeper Nemotron analysis for escalated calls. Escalated calls are never executed.
- Docker-isolated tool executor with a restricted command allowlist and a temporary workspace.
- Tools: `shell`, `filesystem.list`, `filesystem.read`, `filesystem.write`, and optional `web.search` via Tavily.
- SQLite event recording, basic secret redaction, eight replayable demo scenarios, and a Next.js dashboard.

## What this MVP does not claim

No general-purpose agent framework, human approval workflow, complete trajectory-level detection, immutable/WORM audit storage, production-grade multi-tenant isolation, or security certification is implemented. SQLite is mutable local storage. The included scenarios are demonstrations, not a comprehensive benchmark. No block rate, false-positive rate, or performance benchmark is claimed.

## Architecture

```text
Next.js dashboard :3000
        |
        v
FastAPI proxy :8000 -------> Nebius Token Factory (optional)
   |       | --------------> Tavily Search (optional)
   |
   +--> deterministic rules
   +--> optional Nemotron Nano classification
   +--> optional Ultra escalation analysis
   +--> SQLite event recorder
   |
   +--> sandbox service on an internal Docker network
          +-- restricted shell allowlist
          +-- scoped temporary workspace
          +-- filesystem operations
```

The sandbox is a separate container on an internal Compose network. It receives no Docker socket and has no direct external network attachment.

## Quickstart

Prerequisites: Docker Engine and Docker Compose v2.

```bash
cp .env.example .env
# Optionally fill in Nebius and Tavily credentials in .env
docker compose up --build
```

Open the dashboard at <http://localhost:3000>, API documentation at <http://localhost:8000/docs>, and health endpoint at <http://localhost:8000/api/health>.

With an empty `NEBIUS_API_KEY`, the backend starts in **mock mode**. This is a deterministic local heuristic, not a live model result.

Stop containers with `docker compose down`. Remove local demo data too with `docker compose down -v`.

## Nebius Token Factory / Nemotron

The backend uses the OpenAI Python client with a configurable OpenAI-compatible base URL. Configure `NEBIUS_API_KEY`, `NEBIUS_BASE_URL`, `NEMOTRON_NANO_MODEL`, and `NEMOTRON_ULTRA_MODEL` in `.env`.

- Nano is used for inline screening after deterministic checks.
- Ultra is used for deeper analysis when the inline result is `escalate`.
- The model IDs in `.env.example` are example defaults. Verify the exact IDs and endpoint URL available to your account in the Nebius console before enabling live calls.

If model screening fails or returns an invalid response, the call is escalated and not executed. This MVP does not use Nemotron Super.

## Tavily

Set `TAVILY_API_KEY` to enable `web.search`. Without it, the tool returns a configuration error. Search results are external, untrusted content. This MVP screens the search request; it is not a general-purpose sanitizer for arbitrary downstream agent prompts.

## API examples

```bash
curl http://localhost:8000/api/health

curl -X POST http://localhost:8000/api/tool-calls \
  -H 'Content-Type: application/json' \
  -d '{"session_id":"demo","tool":"filesystem.list","arguments":{"path":"."}}'

curl -X POST http://localhost:8000/api/tool-calls \
  -H 'Content-Type: application/json' \
  -d '{"session_id":"demo","tool":"shell","arguments":{"command":"rm -rf /workspace"}}'

curl -X POST http://localhost:8000/api/demo/run/destructive-shell
```

## Verdict behavior

| Verdict | MVP behavior |
|---|---|
| `allow` | The supported tool is executed in the sandbox or through Tavily. |
| `deny` | The call is rejected and not executed. |
| `escalate` | Optional deeper analysis is attached; the call is not executed. |
| `confirm` | Reserved for human approval; no approval workflow is implemented, so the call is not executed. |

## Tests and scenario replay

```bash
cd backend
python -m pip install -r requirements.txt
pytest -q
cd ..
python backend/redteam/runner.py --base-url http://localhost:8000
```

The runner prints observed outcomes. It does not calculate or claim a general security detection rate.

## Team

- **Aditya Anil** — backend, screening layers, proxy, policy rules, and red-team scenarios.
- **Ashreya Gatla** — agent environment, dashboard, integration testing, and documentation.

Repository URL discussed by the team: <https://github.com/aditya-an1l/AgentSentinel>. Verify that the repository is publicly accessible and contains the final pushed files before sharing it. This ZIP does not imply that a public repository or hosted demo is live.

## License

MIT. See [LICENSE](LICENSE).
