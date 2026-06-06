"""Thin Hermes adapter — HTTP client wrappers for native Hermes tools."""
from __future__ import annotations

from typing import Any

from openswarm_builder.adapters.client import BuilderClient

_client: BuilderClient | None = None


def _client() -> BuilderClient:
    global _client
    if _client is None:
        _client = BuilderClient()
    return _client


def openswarm_design(request: str) -> dict[str, Any]:
    """Start design loop; returns proposal without building."""
    return _client().design(request)


def openswarm_approve(spec_id: str) -> dict[str, Any]:
    """Approve a pending SwarmSpec."""
    return _client().approve(spec_id)


def openswarm_build(spec_id: str, *, start: bool = False) -> dict[str, Any]:
    """Materialize an approved spec."""
    return _client().build(spec_id, start=start)


def openswarm_respond(spec_id: str, message: str) -> dict[str, Any]:
    """Approve, reject, or revise (change: ...) a spec."""
    return _client().respond(spec_id, message)


def openswarm_list() -> list[dict[str, Any]]:
    """List fleet swarms."""
    return _client().list_swarms()


def openswarm_run(name: str, message: str, recipient: str | None = None) -> dict[str, Any]:
    """Send a message to a swarm."""
    return _client().run_swarm(name, message, recipient)


def openswarm_status() -> dict[str, Any]:
    """Builder health check."""
    return _client().health()


HERMES_TOOL_DEFINITIONS = [
    {"name": "openswarm_design", "fn": openswarm_design, "params": ["request"]},
    {"name": "openswarm_approve", "fn": openswarm_approve, "params": ["spec_id"]},
    {"name": "openswarm_build", "fn": openswarm_build, "params": ["spec_id", "start"]},
    {"name": "openswarm_respond", "fn": openswarm_respond, "params": ["spec_id", "message"]},
    {"name": "openswarm_list", "fn": openswarm_list, "params": []},
    {"name": "openswarm_run", "fn": openswarm_run, "params": ["name", "message", "recipient"]},
    {"name": "openswarm_status", "fn": openswarm_status, "params": []},
]
