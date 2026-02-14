from __future__ import annotations

from typing import Any, Dict, Optional
import httpx
import structlog
from nlp_service.config import nlp_config

logger = structlog.get_logger()


class CoreBackendClient:
    """
    Simple HTTP client for your CORE backend (retail-ai-backend).
    Uses CORE_API_BASE_URL from your .env through nlp_config.
    """

    def __init__(self):
        self.base_url = getattr(nlp_config, "core_api_base_url", "http://127.0.0.1:8000").rstrip("/")
        self.timeout = 10.0

    async def get(self, path: str) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        logger.info("Calling CORE backend", url=url)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.get(url)
            r.raise_for_status()
            return r.json()


_core_client: Optional[CoreBackendClient] = None


def get_core_client() -> CoreBackendClient:
    global _core_client
    if _core_client is None:
        _core_client = CoreBackendClient()
    return _core_client
