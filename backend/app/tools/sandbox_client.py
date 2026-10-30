import httpx
from app.config import settings


async def execute_sandbox(tool: str, arguments: dict) -> dict:
    async with httpx.AsyncClient(timeout=httpx.Timeout(8.0, connect=2.0)) as client:
        response = await client.post(f"{settings.sandbox_url}/execute",
                                     json={"tool": tool, "arguments": arguments})
        response.raise_for_status()
        return response.json()


async def reset_sandbox() -> dict:
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.post(f"{settings.sandbox_url}/reset")
        response.raise_for_status()
        return response.json()
