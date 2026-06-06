# Claude Code specialist tools
from agency_swarm.tools import BaseTool
from pydantic import Field
import subprocess
import os


class ShellTool(BaseTool):
    """Run Claude Code CLI non-interactively in the swarm workspace."""

    command: str = Field(..., description="Shell command to run (typically claude --print ...)")

    def run(self):
        swarm_root = os.environ.get("SWARM_ROOT", os.getcwd())
        result = subprocess.run(
            self.command,
            shell=True,
            cwd=swarm_root,
            capture_output=True,
            text=True,
            timeout=600,
        )
        return result.stdout or result.stderr or f"exit code {result.returncode}"


class FileReadTool(BaseTool):
    path: str = Field(..., description="Relative path to read")

    def run(self):
        with open(self.path, encoding="utf-8") as f:
            return f.read()


class FileWriteTool(BaseTool):
    path: str = Field(..., description="Relative path to write")
    content: str = Field(..., description="File content")

    def run(self):
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(self.content)
        return f"Wrote {self.path}"


class RunTestsTool(BaseTool):
    command: str = Field(default="pytest -q", description="Test command")

    def run(self):
        result = subprocess.run(self.command, shell=True, capture_output=True, text=True, timeout=300)
        return (result.stdout or "") + (result.stderr or "")
