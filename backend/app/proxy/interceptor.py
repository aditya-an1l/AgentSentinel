import time
from typing import Any
from app.recorder.flight_recorder import record_event
from app.screening.rules import inspect_call
from app.screening.fast_screen import classify
from app.screening.deep_forensics import analyze
from app.tools.sandbox_client import execute_sandbox
from app.tools.tavily import search


async def intercept_tool_call(session_id: str, tool: str, arguments: dict[str, Any]) -> dict:
    started = time.perf_counter()
    result = forensic = None
    executed = False
    blocked, rule_reason = inspect_call(tool, arguments)

    if blocked:
        verdict, reason, source = "deny", rule_reason or "Blocked by deterministic policy.", "rules"
    else:
        verdict, reason, source = classify(tool, arguments)

    if verdict == "escalate":
        forensic = analyze(session_id, tool, arguments, reason)
    elif verdict == "allow":
        try:
            result = await search(str(arguments.get("query", ""))) if tool == "web.search" else await execute_sandbox(tool, arguments)
            executed = True
            if isinstance(result, dict) and result.get("ok") is False:
                reason = f"Screening passed; tool returned an error: {result.get('error', 'unknown error')}"
        except Exception as exc:
            result = {"ok": False, "error": f"Tool execution failed ({type(exc).__name__})."}
            reason = "Screening passed, but the isolated tool service could not complete the request."
    elif verdict == "confirm":
        reason = "Human confirmation is required; this MVP does not execute confirmation-gated actions."

    latency = (time.perf_counter() - started) * 1000
    event_id = record_event(
        session_id=session_id, tool=tool, arguments=arguments, verdict=verdict,
        reason=reason, screening_source=source, executed=executed,
        result=result, latency_ms=latency,
    )
    return {"event_id": event_id, "verdict": verdict, "reason": reason,
            "screening_source": source, "executed": executed, "result": result,
            "forensic_analysis": forensic, "latency_ms": round(latency, 2)}
