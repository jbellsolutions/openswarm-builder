"""MCP server adapter for Cursor, Claude Desktop, etc."""
from __future__ import annotations

import asyncio
import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from openswarm_builder.service import BuilderService

server = Server("openswarm-builder")
_service: BuilderService | None = None


def svc() -> BuilderService:
    global _service
    if _service is None:
        _service = BuilderService()
    return _service


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="openswarm_design_swarm",
            description="Start design loop; returns proposal (does NOT build until approved)",
            inputSchema={
                "type": "object",
                "properties": {"request": {"type": "string", "description": "Swarm description"}},
                "required": ["request"],
            },
        ),
        Tool(
            name="openswarm_approve_spec",
            description="Approve a pending SwarmSpec by id",
            inputSchema={
                "type": "object",
                "properties": {"spec_id": {"type": "string"}},
                "required": ["spec_id"],
            },
        ),
        Tool(
            name="openswarm_build_swarm",
            description="Materialize an approved SwarmSpec",
            inputSchema={
                "type": "object",
                "properties": {
                    "spec_id": {"type": "string"},
                    "start": {"type": "boolean", "default": False},
                },
                "required": ["spec_id"],
            },
        ),
        Tool(
            name="openswarm_respond_spec",
            description="Approve, reject, or revise a spec (e.g. change: drop codex)",
            inputSchema={
                "type": "object",
                "properties": {
                    "spec_id": {"type": "string"},
                    "message": {"type": "string"},
                },
                "required": ["spec_id", "message"],
            },
        ),
        Tool(
            name="openswarm_list_swarms",
            description="List fleet swarms",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="openswarm_run_swarm",
            description="Send a message to a running swarm",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "message": {"type": "string"},
                    "recipient": {"type": "string"},
                },
                "required": ["name", "message"],
            },
        ),
        Tool(
            name="openswarm_health",
            description="Builder health and pending approval count",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    s = svc()
    try:
        if name == "openswarm_design_swarm":
            result = s.design(arguments["request"])
        elif name == "openswarm_approve_spec":
            result = s.approve(arguments["spec_id"])
        elif name == "openswarm_build_swarm":
            result = s.build(arguments["spec_id"], start=arguments.get("start", False))
        elif name == "openswarm_respond_spec":
            result = s.respond(arguments["spec_id"], arguments["message"])
        elif name == "openswarm_list_swarms":
            result = s.list_swarms()
        elif name == "openswarm_run_swarm":
            result = s.run_swarm(
                arguments["name"],
                arguments["message"],
                arguments.get("recipient"),
            )
        elif name == "openswarm_health":
            result = s.health()
        else:
            result = {"error": f"Unknown tool {name}"}
    except Exception as exc:
        result = {"error": str(exc)}

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _run() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main() -> None:
    asyncio.run(_run())
