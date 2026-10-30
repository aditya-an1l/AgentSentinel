import httpx

from app.config import settings


async def search(query: str) -> dict:
    if not settings.tavily_api_key:
        return {"ok": False, "error": "TAVILY_API_KEY is not configured."}
    async with httpx.AsyncClient(timeout=12.0) as client:
        response = await client.post(
            "https://api.tavily.com/search",
            json={"api_key": settings.tavily_api_key, "query": query,
                  "search_depth": "basic", "max_results": 5, "include_answer": False},
        )
        response.raise_for_status()
        data = response.json()
    return {"ok": True, "results": [
        {"title": item.get("title", ""), "url": item.get("url", ""),
         "content": str(item.get("content", ""))[:1200]}
        for item in data.get("results", [])[:5]
    ]}
