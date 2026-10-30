import re
from pathlib import PurePosixPath
from typing import Any

SECRET_KEY = re.compile(r"(api[_-]?key|token|secret|password|credential|private[_-]?key)", re.I)
SECRET_VALUE = re.compile(r"(?i)(sk-[A-Za-z0-9_-]{12,}|nvapi-[A-Za-z0-9_-]{12,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)")
DESTRUCTIVE = re.compile(r"(^|[;&|]\s*)(rm\s+-rf\b|mkfs\b|dd\s+if=|shutdown\b|reboot\b|chmod\s+-R\s+777\b|truncate\b)", re.I)
SHELL_META = re.compile(r"[;&|`$<>\\n]")
SENSITIVE_PATHS = {".env", ".ssh", ".aws", ".config", "id_rsa", "id_ed25519", "credentials", "secrets", "shadow", "passwd"}


def flatten(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(f"{key} {flatten(item)}" for key, item in value.items())
    if isinstance(value, list):
        return " ".join(flatten(item) for item in value)
    return str(value) if isinstance(value, (str, int, float, bool)) else ""


def inspect_call(tool: str, arguments: dict[str, Any]) -> tuple[bool, str | None]:
    blob = flatten(arguments)
    if SECRET_VALUE.search(blob):
        return True, "A credential-shaped value was included in the proposed tool arguments."

    if tool == "shell":
        command = str(arguments.get("command", "")).strip()
        if not command:
            return True, "Shell command is empty."
        if DESTRUCTIVE.search(command):
            return True, "Destructive shell operation is blocked before execution."
        if SHELL_META.search(command):
            return True, "Shell operators, substitutions, and redirections are not allowed."
        if SECRET_KEY.search(command):
            return True, "Shell command appears to reference credential material."
        return False, None

    if tool.startswith("filesystem."):
        path = str(arguments.get("path", ".")).replace("\\", "/")
        parts = [part.lower() for part in PurePosixPath(path).parts]
        if ".." in parts or path.startswith("/"):
            return True, "Absolute paths and parent-directory traversal are blocked."
        if any(part in SENSITIVE_PATHS for part in parts):
            return True, "Access to a sensitive path is blocked."
        if SECRET_KEY.search(blob):
            return True, "Filesystem request appears to target credential material."
        return False, None

    if tool == "web.search":
        query = str(arguments.get("query", "")).lower()
        terms = ("reveal the api key", "ignore previous instructions", "exfiltrate",
                 "send the secret", "print environment variables")
        if any(term in query for term in terms):
            return True, "Search request contains a direct credential-exfiltration instruction."
        return False, None

    return True, "Tool is not supported by this policy."


def mock_classification(tool: str, arguments: dict[str, Any]) -> tuple[str, str]:
    blob = flatten(arguments).lower()
    if any(term in blob for term in ("ignore previous instructions", "bypass safeguards", "exfiltrate", "steal")):
        return "escalate", "Mock classifier flagged instruction-like or exfiltration language."
    return "allow", "Mock classifier allowed the call; no live model was queried."
