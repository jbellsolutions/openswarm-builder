from agency_swarm.tools import BaseTool
from pydantic import Field
import subprocess
import os


class CodexCLITool(BaseTool):
    """Run OpenAI Codex CLI for batch/non-interactive implementation."""

    prompt: str = Field(..., description="Task prompt for codex")
    sandbox: str = Field(default="workspace-write", description="Codex sandbox mode")

    def run(self):
        swarm_root = os.environ.get("SWARM_ROOT", os.getcwd())
        cmd = f'codex exec --sandbox {self.sandbox} -- "{self.prompt.replace(chr(34), chr(39))}"'
        result = subprocess.run(cmd, shell=True, cwd=swarm_root, capture_output=True, text=True, timeout=900)
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
