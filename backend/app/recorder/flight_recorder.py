import re
from typing import Any
from app.db import insert_event

SENSITIVE_KEY = re.compile(r"(api[_-]?key|token|secret|password|credential|private[_-]?key)", re.I)
SECRET_VALUE = re.compile(r"(?i)(sk-[A-Za-z0-9_-]{12,}|nvapi-[A-Za-z0-9_-]{12,})")


def redact(value: Any, key: str = "") -> Any:
    if SENSITIVE_KEY.search(key):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {str(k): redact(v, str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, str):
        return SECRET_VALUE.sub("[REDACTED]", value)
    return value


def record_event(**kwargs: Any) -> int:
    kwargs["arguments"] = redact(kwargs.get("arguments", {}))
    kwargs["result"] = redact(kwargs.get("result"))
    return insert_event(**kwargs)
