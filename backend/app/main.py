from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.db import initialize, list_events, stats, clear_events
from app.schemas import ToolCallRequest
from app.proxy.interceptor import intercept_tool_call
from app.demo_agent.scenarios import SCENARIOS
from app.tools.sandbox_client import reset_sandbox

app = FastAPI(title="AgentSentinel API", version="0.1.0",
              description="MVP runtime screening proxy and event recorder.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:3000"],
    allow_credentials=False, allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.on_event("startup")
def startup() -> None:
    initialize()


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok", "service": "agentsentinel-api",
        "model_mode": settings.model_mode,
        "nano_model": settings.nano_model if settings.nebius_api_key else None,
        "ultra_configured": bool(settings.nebius_api_key and settings.ultra_model),
        "tavily_configured": bool(settings.tavily_api_key),
        "notes": ["Mock mode does not make a live model request."
                  if settings.model_mode == "mock"
                  else "Nebius credentials are present; verify configured model IDs in your console."],
    }


@app.get("/api/stats")
def get_stats() -> dict:
    return stats()


@app.get("/api/events")
def get_events(limit: int = 100) -> list[dict]:
    return list_events(limit)


@app.get("/api/scenarios")
def get_scenarios() -> list[dict]:
    return SCENARIOS


@app.post("/api/tool-calls")
async def tool_calls(request: ToolCallRequest) -> dict:
    return await intercept_tool_call(request.session_id, request.tool, request.arguments)


@app.post("/api/demo/run/{scenario_id}")
async def run_scenario(scenario_id: str) -> dict:
    scenario = next((item for item in SCENARIOS if item["id"] == scenario_id), None)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Unknown demo scenario.")
    result = await intercept_tool_call(f"demo-{scenario_id}", scenario["tool"], scenario["arguments"])
    return {**result, "scenario": scenario}


@app.get("/api/reports")
def get_reports() -> list[dict]:
    return [event for event in list_events(500)
            if event["verdict"] in {"deny", "escalate", "confirm"}]


@app.post("/api/reset")
async def reset_demo() -> dict:
    clear_events()
    try:
        sandbox_result = await reset_sandbox()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Could not reset sandbox ({type(exc).__name__}).") from exc
    return {"ok": True, "message": "Demo event log and sandbox workspace reset.", "sandbox": sandbox_result}
