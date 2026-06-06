"""Design loop meta-agents — programmatic orchestration of the planning pipeline."""
from __future__ import annotations

import re
from typing import Any

from openswarm_builder.builder_swarm import (
    api_researcher,
    proposal_synthesizer,
    requirements_analyst,
    specialist_planner,
    swarm_architect,
    tool_architect,
)
from openswarm_builder.core.swarm_spec import SwarmSpec


def _parse_revision_request(text: str) -> str:
    lowered = text.strip().lower()
    for prefix in ("change:", "revise:", "update:", "edit:"):
        if lowered.startswith(prefix):
            return text.split(":", 1)[1].strip()
    return text.strip()


def run_design_loop(user_request: str, *, revision_of: SwarmSpec | None = None) -> SwarmSpec:
    """Run meta-agent pipeline and return SwarmSpec (does NOT materialize)."""
    context: dict[str, Any] = {
        "user_request": user_request,
        "revision_of": revision_of,
    }

    requirements = requirements_analyst.analyze(user_request, revision_of=revision_of)
    context["requirements"] = requirements

    roster = specialist_planner.plan(requirements)
    context["roster"] = roster

    tools = tool_architect.map_tools(requirements, roster)
    context["tools"] = tools

    if api_researcher.needs_research(requirements):
        research = api_researcher.research(requirements)
        context["api_research"] = research
        tools = tool_architect.merge_research(tools, research)

    flows = swarm_architect.design_flows(roster, tools)
    context["flows"] = flows

    spec = proposal_synthesizer.synthesize(requirements, roster, tools, flows)
    return spec


def parse_user_response(text: str) -> tuple[str, str | None]:
    """Return (action, detail) where action is approve|reject|revise|unknown."""
    lowered = text.strip().lower()
    if lowered in {"approve", "approved", "yes", "lgtm", "looks good", "go", "ship it"}:
        return "approve", None
    if lowered.startswith("reject") or lowered in {"no", "cancel", "abort"}:
        return "reject", text
    if any(lowered.startswith(p) for p in ("change:", "revise:", "update:", "edit:", "swap")):
        return "revise", _parse_revision_request(text)
    if "approve" in lowered and "don't" not in lowered and "not" not in lowered:
        return "approve", None
    return "unknown", text
