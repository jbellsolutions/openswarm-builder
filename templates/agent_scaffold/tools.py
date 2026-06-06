from agency_swarm.tools import BaseTool
from pydantic import Field


class WebSearchTool(BaseTool):
    query: str = Field(..., description="Search query")

    def run(self):
        return f"[WebSearch stub] Query: {self.query} — configure SEARCH_API_KEY for live results."


class FileWriteTool(BaseTool):
    path: str = Field(..., description="Output path")
    content: str = Field(..., description="Content")

    def run(self):
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(self.content)
        return f"Wrote {self.path}"
