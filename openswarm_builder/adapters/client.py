"""HTTP client for remote openswarm-builder instances."""
from __future__ import annotations

import os
from typing import Any

import httpx


class BuilderClient:
    def __init__(self, base_url: str | None = None, timeout: float = 120.0) -> None:
        self.base_url = (base_url or os.environ.get("OPENSWARM_BUILDER_URL", "http://127.0.0.1:8090")).rstrip("/")
        self.timeout = timeout

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.request(method, f"{self.base_url}{path}", **kwargs)
            resp.raise_for_status()
            return resp.json()

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/health")

    def design(self, request: str) -> dict[str, Any]:
        return self._request("POST", "/design", json={"request": request})

    def approve(self, spec_id: str) -> dict[str, Any]:
        return self._request("POST", f"/specs/{spec_id}/approve")

    def build(self, spec_id: str, *, start: bool = False) -> dict[str, Any]:
        return self._request("POST", f"/specs/{spec_id}/build", json={"start": start})

    def respond(self, spec_id: str, message: str) -> dict[str, Any]:
        return self._request("POST", f"/specs/{spec_id}/respond", json={"message": message})

    def list_swarms(self) -> list[dict[str, Any]]:
        return self._request("GET", "/swarms")

    def run_swarm(self, name: str, message: str, recipient: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"message": message}
        if recipient:
            payload["recipient"] = recipient
        return self._request("POST", f"/swarms/{name}/run", json=payload)
