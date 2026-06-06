"""SwarmSpec v1 — contract between design loop and materialization."""
from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

SPEC_VERSION = "1"


class AgentSpec(BaseModel):
    id: str
    role: str
    tools: list[str] = Field(default_factory=list)
    instructions_summary: str = ""
    handoffs_from: list[str] = Field(default_factory=list)
    template: Literal["scaffold", "claude_code_agent", "codex_agent", "openswarm_builtin"] = "scaffold"
    openswarm_builtin: str | None = None  # e.g. deep_research, slides_agent

    @field_validator("id")
    @classmethod
    def valid_id(cls, v: str) -> str:
        if not re.match(r"^[a-z][a-z0-9_]*$", v):
            raise ValueError("agent id must be snake_case starting with a letter")
        return v


class OrchestratorFlows(BaseModel):
    send_message: list[str] = Field(default_factory=lambda: ["orchestrator -> all"])
    handoffs: list[str] = Field(default_factory=list)


class IntegrationsSpec(BaseModel):
    composio: list[str] = Field(default_factory=list)
    api_keys_required: list[str] = Field(default_factory=list)


class SwarmSpec(BaseModel):
    version: str = SPEC_VERSION
    name: str
    purpose: str
    agents: list[AgentSpec]
    orchestrator_flows: OrchestratorFlows = Field(default_factory=OrchestratorFlows)
    integrations: IntegrationsSpec = Field(default_factory=IntegrationsSpec)
    example_prompts: list[str] = Field(default_factory=list)
    estimated_cost_daily_usd: float = 10.0
    shared_context: str = ""

    @field_validator("name")
    @classmethod
    def valid_name(cls, v: str) -> str:
        if v in {"default", "_archive"}:
            raise ValueError(f"name {v!r} is reserved")
        if not re.match(r"^[a-z][a-z0-9-]*$", v):
            raise ValueError("swarm name must be kebab-case")
        return v

    def agent_ids(self) -> set[str]:
        return {a.id for a in self.agents}

    def summary_markdown(self) -> str:
        lines = [
            f"# Swarm proposal: **{self.name}**",
            "",
            f"**Purpose:** {self.purpose}",
            "",
            "## Agents",
        ]
        for agent in self.agents:
            tools = ", ".join(agent.tools) if agent.tools else "(orchestrator routing)"
            lines.append(f"- **{agent.id}** — {agent.role}")
            lines.append(f"  - Tools: {tools}")
            if agent.handoffs_from:
                lines.append(f"  - Handoffs from: {', '.join(agent.handoffs_from)}")
        if self.integrations.api_keys_required:
            lines.extend(["", "## Required API keys", *[f"- `{k}`" for k in self.integrations.api_keys_required]])
        if self.example_prompts:
            lines.extend(["", "## Example prompts", *[f"- {p}" for p in self.example_prompts]])
        lines.append(f"\n**Estimated daily budget:** ${self.estimated_cost_daily_usd:.2f}")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SwarmSpec:
        return cls.model_validate(data)
