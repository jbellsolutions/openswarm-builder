# {{AGENT_CLASS}} — interactive coding via Claude Code CLI
from agency_swarm import Agent

from .tools import FileReadTool, FileWriteTool, RunTestsTool, ShellTool


class {{AGENT_CLASS}}(Agent):
    def __init__(self):
        super().__init__(
            name="{{AGENT_ID}}",
            description="{{ROLE}}",
            instructions="./instructions.md",
            tools=[ShellTool, FileReadTool, FileWriteTool, RunTestsTool],
            model="gpt-4o",
        )
