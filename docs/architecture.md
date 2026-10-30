# Architecture and trust boundaries

1. A caller submits a structured tool call to `POST /api/tool-calls`.
2. The interceptor applies deterministic rules.
3. If no rule blocks the call, the classifier uses Nebius Token Factory when configured or a clearly labelled local mock classifier otherwise.
4. Only an `allow` verdict executes. Shell and filesystem tools are sent to the isolated sandbox; `web.search` is sent to Tavily when configured.
5. `deny`, `escalate`, and `confirm` do not execute. Escalation may call the configured deeper-analysis model.
6. Event details are redacted using a small set of patterns and stored in SQLite.

## Boundaries

- The rules are a small demonstrator deny-list, not a complete policy engine.
- Model decisions are fallible. An unavailable or malformed live-model response fails closed.
- The sandbox runs separately on an internal Compose network, as an unprivileged user, with dropped capabilities, a read-only root filesystem, and a temporary workspace.
- The backend needs external network access for Nebius and Tavily. The sandbox does not have an external network attachment.
- SQLite is mutable local storage. Redaction is basic hygiene, not a guarantee that every secret is removed.

## MVP limitations

No dashboard authentication, tenant model, human approval flow, complete trajectory analysis, general-purpose agent, comprehensive egress filter, or production-grade sandboxing is included. Review and harden the system before any public or production deployment.
