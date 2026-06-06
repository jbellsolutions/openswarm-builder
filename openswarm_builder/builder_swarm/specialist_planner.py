"""Specialist Planner — propose agent roster."""
from __future__ import annotations

from dataclasses import dataclass, field

from openswarm_builder.builder_swarm.requirements_analyst import Requirements


@dataclass
class PlannedAgent:
    id: str
    role: str
    template: str = "scaffold"
    openswarm_builtin: str | None = None
    rationale: str = ""


@dataclass
class Roster:
    name: str
    agents: list[PlannedAgent] = field(default_factory=list)


def plan(requirements: Requirements) -> Roster:
    name = _derive_name(requirements)
    agents: list[PlannedAgent] = []

    agents.append(
        PlannedAgent(
            id="orchestrator",
            role="Route tasks to specialists and synthesize results",
            template="openswarm_builtin",
            openswarm_builtin="orchestrator",
            rationale="Every swarm needs a coordinator",
        )
    )

    if requirements.needs_research:
        agents.append(
            PlannedAgent(
                id="research_specialist",
                role="Deep research, competitor analysis, and synthesis",
                template="openswarm_builtin",
                openswarm_builtin="deep_research",
                rationale="Research depth requested",
            )
        )

    if requirements.needs_content:
        agents.append(
            PlannedAgent(
                id="content_writer",
                role="Write publish-ready content optimized for the channel",
                template="scaffold",
                rationale="Content output requested",
            )
        )

    if requirements.needs_slack:
        agents.append(
            PlannedAgent(
                id="slack_integrator",
                role="Slack messaging, notifications, and Composio integrations",
                template="openswarm_builtin",
                openswarm_builtin="virtual_assistant",
                rationale="Slack/integration channel mentioned",
            )
        )

    if "slides" in requirements.output_types:
        agents.append(
            PlannedAgent(
                id="slides_specialist",
                role="Create slide decks and presentations",
                template="openswarm_builtin",
                openswarm_builtin="slides_agent",
                rationale="Presentation output requested",
            )
        )

    if requirements.needs_coding:
        agents.append(
            PlannedAgent(
                id="claude_code_agent",
                role="Interactive repo edits via Claude Code CLI",
                template="claude_code_agent",
                rationale="Interactive coding / architecture work",
            )
        )

    if requirements.needs_batch_coding or requirements.needs_coding:
        agents.append(
            PlannedAgent(
                id="codex_agent",
                role="Batch implementation via Codex CLI",
                template="codex_agent",
                rationale="Background or batch coding tasks",
            )
        )

    if len(agents) == 1:
        agents.append(
            PlannedAgent(
                id="general_specialist",
                role="Handle general tasks for the swarm purpose",
                template="scaffold",
                rationale="Default specialist when no domain detected",
            )
        )

    return Roster(name=name, agents=agents)


def _derive_name(req: Requirements) -> str:
    import re

    words = re.findall(r"[a-z0-9]+", req.raw_request.lower())
    stop = {"a", "an", "the", "i", "want", "need", "team", "that", "and", "with", "for", "to", "my"}
    filtered = [w for w in words if w not in stop][:3]
    if not filtered:
        return "custom-swarm"
    return "-".join(filtered)
