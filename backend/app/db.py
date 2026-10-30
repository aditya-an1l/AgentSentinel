import json
import os
import sqlite3
from typing import Any

from app.config import settings


def connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(settings.database_path) or ".", exist_ok=True)
    conn = sqlite3.connect(settings.database_path, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def initialize() -> None:
    with connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                session_id TEXT NOT NULL,
                tool TEXT NOT NULL,
                arguments_json TEXT NOT NULL,
                verdict TEXT NOT NULL,
                reason TEXT NOT NULL,
                screening_source TEXT NOT NULL,
                executed INTEGER NOT NULL DEFAULT 0,
                result_json TEXT,
                latency_ms REAL NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at DESC)")


def insert_event(**event: Any) -> int:
    with connect() as conn:
        cursor = conn.execute("""
            INSERT INTO events (
                session_id, tool, arguments_json, verdict, reason,
                screening_source, executed, result_json, latency_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event["session_id"], event["tool"],
            json.dumps(event["arguments"], ensure_ascii=False),
            event["verdict"], event["reason"], event["screening_source"],
            int(event["executed"]),
            json.dumps(event["result"], ensure_ascii=False, default=str) if event["result"] is not None else None,
            round(event["latency_ms"], 3),
        ))
        return int(cursor.lastrowid)


def list_events(limit: int = 100) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?",
                            (max(1, min(limit, 500)),)).fetchall()
    output = []
    for row in rows:
        item = dict(row)
        item["arguments"] = json.loads(item.pop("arguments_json"))
        raw = item.pop("result_json")
        item["result"] = json.loads(raw) if raw else None
        item["executed"] = bool(item["executed"])
        output.append(item)
    return output


def stats() -> dict[str, Any]:
    with connect() as conn:
        total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        rows = conn.execute("SELECT verdict, COUNT(*) AS n FROM events GROUP BY verdict").fetchall()
        average = conn.execute("SELECT AVG(latency_ms) FROM events").fetchone()[0]
    counts = {row["verdict"]: row["n"] for row in rows}
    return {
        "total_events": total, "allow": counts.get("allow", 0),
        "deny": counts.get("deny", 0), "escalate": counts.get("escalate", 0),
        "confirm": counts.get("confirm", 0),
        "average_recorded_latency_ms": round(average, 2) if average is not None else None,
    }


def clear_events() -> None:
    with connect() as conn:
        conn.execute("DELETE FROM events")
        conn.execute("DELETE FROM sqlite_sequence WHERE name='events'")
