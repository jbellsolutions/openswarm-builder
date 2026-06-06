# {{AGENT_CLASS}} — batch coding via Codex CLI
from agency_swarm import Agent

from .tools import CodexCLITool, FileReadTool, FileWriteTool


class {{AGENT_CLASS}}(Agent):
    def __init__(self):
        super().__init__(
            name="{{AGENT_ID}}",
            description="{{ROLE}}",
            instructions="./instructions.md",
            tools=[CodexCLITool, FileReadTool, FileWriteTool],
            model="gpt-4o",
        )
