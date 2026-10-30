# Security notes

- Do not expose the dashboard or API publicly without authentication, rate limiting, request-size limits, and a deployment-specific security review.
- Keep `.env` private. Never place credentials in frontend variables or commit them.
- Session IDs are caller-supplied labels, not an identity boundary.
- Shell commands use an argument vector with `shell=False`, and the sandbox applies a second command allowlist.
- The sandbox is disposable and has no production data or Docker socket.
- Resetting clears the event log and sandbox workspace.
- SQLite records can be modified or deleted by a host/container administrator; they are not immutable.
- The recorder redacts common key names and token-shaped strings, but arbitrary secrets can evade the patterns. Avoid submitting real credentials.
