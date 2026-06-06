"""HTTP client for OpenSwarm FastAPI servers."""
from __future__ import annotations

from typing import Any

import httpx


class SwarmHttpClient:
    def __init__(self, base_url: str, timeout: float = 120.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def get_metadata(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(f"{self.base_url}/open-swarm/get_metadata")
            resp.raise_for_status()
            return resp.json()

    async def health(self) -> bool:
        try:
            await self.get_metadata()
            return True
        except Exception:
            return False

    def get_metadata_sync(self) -> dict[str, Any]:
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(f"{self.base_url}/open-swarm/get_metadata")
            resp.raise_for_status()
            return resp.json()

    def health_sync(self) -> bool:
        try:
            self.get_metadata_sync()
            return True
        except Exception:
            return False
