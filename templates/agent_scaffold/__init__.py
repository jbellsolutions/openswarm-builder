# {{AGENT_CLASS}}
from agency_swarm import Agent

from .tools import FileWriteTool, WebSearchTool


class {{AGENT_CLASS}}(Agent):
    def __init__(self):
        super().__init__(
            name="{{AGENT_ID}}",
            description="{{ROLE}}",
            instructions="./instructions.md",
            tools=[WebSearchTool, FileWriteTool],
            model="gpt-4o",
        )
