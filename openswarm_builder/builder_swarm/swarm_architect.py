"""Swarm Architect — orchestrator routing and handoffs."""
from __future__ import annotations

from dataclasses import dataclass, field

from openswarm_builder.builder_swarm.specialist_planner import Roster
from openswarm_builder.builder_swarm.tool_architect import ToolMap


@dataclass
class FlowDesign:
    send_message: list[str] = field(default_factory=lambda: ["orchestrator -> all"])
    handoffs: list[str] = field(default_factory=list)
    shared_context: str = ""


def design_flows(roster: Roster, tools: ToolMap) -> FlowDesign:
    handoffs: list[str] = []
    ids = [a.id for a in roster.agents if a.id != "orchestrator"]

    if "research_specialist" in ids and "content_writer" in ids:
        handoffs.append("research_specialist -> content_writer")
    if "research_specialist" in ids and "slides_specialist" in ids:
        handoffs.append("research_specialist -> slides_specialist")
    if "claude_code_agent" in ids and "codex_agent" in ids:
        handoffs.append("claude_code_agent <-> codex_agent")

    shared = f"This swarm ({roster.name}) coordinates: {', '.join(ids)}."

    return FlowDesign(
        send_message=["orchestrator -> all specialists"],
        handoffs=handoffs,
        shared_context=shared,
    )
