"""Tool Architect — map tools/skills/MCP per agent."""
from __future__ import annotations

from dataclasses import dataclass, field

from openswarm_builder.builder_swarm.requirements_analyst import Requirements
from openswarm_builder.builder_swarm.specialist_planner import PlannedAgent, Roster


@dataclass
class AgentTools:
    agent_id: str
    tools: list[str] = field(default_factory=list)
    api_keys: list[str] = field(default_factory=list)


@dataclass
class ToolMap:
    agents: dict[str, AgentTools] = field(default_factory=dict)
    composio: list[str] = field(default_factory=list)
    global_api_keys: list[str] = field(default_factory=list)


def map_tools(requirements: Requirements, roster: Roster) -> ToolMap:
    result = ToolMap()
    global_keys: set[str] = set()

    for agent in roster.agents:
        tools: list[str] = []
        keys: list[str] = []

        if agent.template == "claude_code_agent":
            tools = ["ShellTool", "FileReadTool", "FileWriteTool", "RunTestsTool"]
        elif agent.template == "codex_agent":
            tools = ["CodexCLITool", "FileReadTool", "FileWriteTool"]
        elif agent.openswarm_builtin == "deep_research":
            tools = ["WebSearchTool", "FetchUrlTool"]
            keys.append("SEARCH_API_KEY")
        elif agent.openswarm_builtin == "virtual_assistant":
            tools = ["ComposioTool", "SlackTool"]
            keys.extend(["COMPOSIO_API_KEY", "SLACK_BOT_TOKEN"])
            result.composio.append("slack")
        elif agent.id == "content_writer":
            tools = ["WebSearchTool", "FileWriteTool"]
        elif agent.id == "orchestrator":
            tools = ["SendMessageTool", "HandoffTool"]
        else:
            tools = ["WebSearchTool", "FileWriteTool"]

        for api in requirements.external_apis:
            if api == "SEMRUSH" and agent.id in {"research_specialist", "content_writer"}:
                tools.append("composio:SEMRUSH_*")
                keys.append("COMPOSIO_API_KEY")
            if api == "GITHUB" and agent.template in {"claude_code_agent", "codex_agent"}:
                tools.append("composio:GITHUB_*")
                keys.append("COMPOSIO_API_KEY")

        global_keys.update(keys)
        result.agents[agent.id] = AgentTools(agent_id=agent.id, tools=tools, api_keys=keys)

    result.global_api_keys = sorted(global_keys)
    if requirements.needs_slack and "slack" not in result.composio:
        result.composio.append("slack")
    return result


def merge_research(tool_map: ToolMap, research: dict) -> ToolMap:
    for api in research.get("apis", []):
        name = api.get("name", "").upper()
        if name and name not in tool_map.global_api_keys:
            tool_map.global_api_keys.append(f"{name}_API_KEY")
    return tool_map
