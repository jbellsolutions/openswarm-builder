"""Proposal Synthesizer — render SwarmSpec from meta-agent outputs."""
from __future__ import annotations

from openswarm_builder.builder_swarm.requirements_analyst import Requirements
from openswarm_builder.builder_swarm.specialist_planner import Roster
from openswarm_builder.builder_swarm.swarm_architect import FlowDesign
from openswarm_builder.builder_swarm.tool_architect import ToolMap
from openswarm_builder.core.swarm_spec import (
    AgentSpec,
    IntegrationsSpec,
    OrchestratorFlows,
    SwarmSpec,
)


def synthesize(
    requirements: Requirements,
    roster: Roster,
    tools: ToolMap,
    flows: FlowDesign,
) -> SwarmSpec:
    agents: list[AgentSpec] = []

    handoff_map: dict[str, list[str]] = {}
    for edge in flows.handoffs:
        if "->" in edge:
            src, _, dst = edge.partition("->")
            src, dst = src.strip(), dst.strip()
            handoff_map.setdefault(dst, []).append(src)
        elif "<->" in edge:
            a, _, b = edge.partition("<->")
            a, b = a.strip(), b.strip()
            handoff_map.setdefault(a, []).append(b)
            handoff_map.setdefault(b, []).append(a)

    for planned in roster.agents:
        if planned.id == "orchestrator":
            continue
        agent_tools = tools.agents.get(planned.id)
        tool_list = agent_tools.tools if agent_tools else []
        agents.append(
            AgentSpec(
                id=planned.id,
                role=planned.role,
                tools=tool_list,
                instructions_summary=planned.rationale or planned.role,
                handoffs_from=handoff_map.get(planned.id, []),
                template=planned.template,  # type: ignore[arg-type]
                openswarm_builtin=planned.openswarm_builtin,
            )
        )

    example_prompts = [_example_prompt(requirements, roster)]

    return SwarmSpec(
        name=roster.name,
        purpose=requirements.purpose,
        agents=agents,
        orchestrator_flows=OrchestratorFlows(
            send_message=flows.send_message,
            handoffs=flows.handoffs,
        ),
        integrations=IntegrationsSpec(
            composio=tools.composio,
            api_keys_required=tools.global_api_keys,
        ),
        example_prompts=example_prompts,
        estimated_cost_daily_usd=_estimate_cost(agents),
        shared_context=flows.shared_context,
    )


def _example_prompt(requirements: Requirements, roster: Roster) -> str:
    return requirements.raw_request[:200] if requirements.raw_request else f"Run a task with the {roster.name} swarm"


def _estimate_cost(agents: list[AgentSpec]) -> float:
    base = 5.0
    per_agent = 2.0
    coding_bonus = 3.0 if any(a.template in {"claude_code_agent", "codex_agent"} for a in agents) else 0
    return base + len(agents) * per_agent + coding_bonus
