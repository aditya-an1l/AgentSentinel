import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

WORKSPACE = Path("/workspace").resolve()
ALLOWED = {"pwd", "ls", "cat", "echo", "whoami"}
app = FastAPI(title="AgentSentinel Restricted Sandbox", docs_url=None, redoc_url=None)


class ExecuteRequest(BaseModel):
    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)


def safe_path(raw: str) -> Path:
    candidate = (WORKSPACE / raw).resolve()
    if candidate != WORKSPACE and WORKSPACE not in candidate.parents:
        raise HTTPException(status_code=403, detail="Path escapes the sandbox workspace.")
    return candidate


def run_shell(command: str) -> dict:
    try:
        parts = shlex.split(command)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid command syntax.") from exc
    if not parts or parts[0] not in ALLOWED:
        raise HTTPException(status_code=403, detail="Command is not in the sandbox allowlist.")
    if len(parts) > 8:
        raise HTTPException(status_code=400, detail="Too many command arguments.")
    binary = {"pwd": "/bin/pwd", "ls": "/bin/ls", "cat": "/bin/cat",
              "echo": "/usr/bin/echo", "whoami": "/usr/bin/whoami"}[parts[0]]
    try:
        result = subprocess.run([binary, *parts[1:]], cwd=WORKSPACE,
                                env={"PATH": "/usr/bin:/bin", "HOME": str(WORKSPACE)},
                                capture_output=True, text=True, timeout=2, check=False)
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Command timed out.")
    return {"ok": result.returncode == 0, "returncode": result.returncode,
            "stdout": result.stdout[:4000], "stderr": result.stderr[:1000]}


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "workspace": str(WORKSPACE)}


@app.post("/execute")
def execute(request: ExecuteRequest) -> dict:
    args = request.arguments
    if request.tool == "shell":
        return run_shell(str(args.get("command", "")))
    if request.tool == "filesystem.list":
        path = safe_path(str(args.get("path", ".")))
        if not path.is_dir():
            raise HTTPException(status_code=404, detail="Directory not found.")
        return {"ok": True, "entries": sorted(item.name for item in path.iterdir())[:100]}
    if request.tool == "filesystem.read":
        path = safe_path(str(args.get("path", "")))
        if not path.is_file():
            raise HTTPException(status_code=404, detail="File not found.")
        if path.stat().st_size > 16384:
            raise HTTPException(status_code=413, detail="File exceeds 16 KiB read limit.")
        return {"ok": True, "content": path.read_text(encoding="utf-8", errors="replace")}
    if request.tool == "filesystem.write":
        path = safe_path(str(args.get("path", "")))
        content = str(args.get("content", ""))
        encoded = content.encode("utf-8")
        if len(encoded) > 16384:
            raise HTTPException(status_code=413, detail="File exceeds 16 KiB write limit.")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return {"ok": True, "path": str(path.relative_to(WORKSPACE)), "bytes_written": len(encoded)}
    raise HTTPException(status_code=400, detail="Unsupported sandbox tool.")


@app.post("/reset")
def reset() -> dict:
    for item in WORKSPACE.iterdir():
        if item.is_dir() and not item.is_symlink():
            shutil.rmtree(item)
        elif item.is_file() or item.is_symlink():
            item.unlink()
    return {"ok": True, "message": "Workspace cleared."}
