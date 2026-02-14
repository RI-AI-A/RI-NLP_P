import os
from typing import Any, Dict, Optional
import httpx


class CoreBackendClient:
    """
    Async client to talk to the CORE backend (your backend).
    NLP should fetch facts by calling REST APIs instead of reading DB.
    """

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or os.getenv("CORE_API_BASE_URL", "http://127.0.0.1:8000")).rstrip("/")

    async def get(self, path: str, params: Dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            return r.json()

    async def fetch_kpis(self, branch_id: str, start: str | None = None, end: str | None = None, limit: int = 20):
        params = {"branch_id": branch_id, "limit": limit}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        return await self.get("/api/v1/kpis", params=params)

    async def fetch_situations(self, branch_id: str, start: str | None = None, end: str | None = None, limit: int = 20):
        params = {"branch_id": branch_id, "limit": limit}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        return await self.get("/api/v1/situations", params=params)

    async def fetch_recommendations(self, branch_id: str, limit: int = 20):
        params = {"branch_id": branch_id, "limit": limit}
        return await self.get("/api/v1/recommendations", params=params)
