"""MaterializeExecutor — SwarmSpec → filesystem after approval."""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

import yaml

from openswarm_builder.core.fleet.fleet import FleetManager
from openswarm_builder.core.fleet.ports import allocate_port
from openswarm_builder.core.fleet.registry import SwarmEntry
from openswarm_builder.core.paths import templates_root, vendor_root
from openswarm_builder.core.swarm_spec import AgentSpec, SwarmSpec
from openswarm_builder.core.validators import validate_swarm_dir


BUILTIN_AGENT_DIRS = {
    "deep_research": "deep_research",
    "slides_agent": "slides_agent",
    "virtual_assistant": "virtual_assistant",
}


class MaterializeExecutor:
    def __init__(self, fleet: FleetManager | None = None) -> None:
        self.fleet = fleet or FleetManager()

    def execute(self, spec: SwarmSpec, *, spec_id: str | None = None, start: bool = False) -> dict[str, Any]:
        swarm_dir = self.fleet.registry.swarm_dir(spec.name)
        if swarm_dir.exists():
            raise FileExistsError(f"Swarm {spec.name!r} already exists at {swarm_dir}")

        port = allocate_port(self.fleet.registry)
        shutil.copytree(vendor_root(), swarm_dir, symlinks=True)

        build_dir = swarm_dir / ".build"
        build_dir.mkdir(parents=True, exist_ok=True)
        (build_dir / "spec.json").write_text(json.dumps(spec.to_dict(), indent=2), encoding="utf-8")

        for agent in spec.agents:
            self._materialize_agent(swarm_dir, agent, spec)

        self._patch_swarm_py(swarm_dir, spec)
        self._write_manifest(swarm_dir, spec, port)
        self._write_env_template(swarm_dir, spec)
        self._render_skill_snippet(spec)

        validation = validate_swarm_dir(swarm_dir, smoke=True)
        if not validation.ok:
            shutil.rmtree(swarm_dir)
            raise RuntimeError(f"Validation failed: {'; '.join(validation.errors)}")

        entry = SwarmEntry(
            name=spec.name,
            port=port,
            status="stopped",
            source="built",
            description=spec.purpose,
            tags=["custom", "built"],
            spec_id=spec_id,
        )
        self.fleet.registry.upsert(entry)

        result: dict[str, Any] = {
            "name": spec.name,
            "port": port,
            "path": str(swarm_dir),
            "validation": {
                "ok": validation.ok,
                "warnings": validation.warnings,
            },
        }

        if start:
            result["start"] = self.fleet.start(spec.name)

        return result

    def _materialize_agent(self, swarm_dir: Path, agent: AgentSpec, spec: SwarmSpec) -> None:
        if agent.template == "openswarm_builtin" and agent.openswarm_builtin:
            return  # already in vendor copy

        agent_dir = swarm_dir / agent.id
        template_name = agent.template if agent.template != "scaffold" else "agent_scaffold"
        template_dir = templates_root() / template_name

        if not template_dir.exists():
            template_dir = templates_root() / "agent_scaffold"

        if agent_dir.exists():
            shutil.rmtree(agent_dir)
        shutil.copytree(template_dir, agent_dir)

        instructions = agent_dir / "instructions.md"
        content = instructions.read_text(encoding="utf-8")
        content = content.replace("{{AGENT_ID}}", agent.id)
        content = content.replace("{{ROLE}}", agent.role)
        content = content.replace("{{PURPOSE}}", spec.purpose)
        content = content.replace("{{INSTRUCTIONS_SUMMARY}}", agent.instructions_summary or agent.role)
        instructions.write_text(content, encoding="utf-8")

        init_path = agent_dir / "__init__.py"
        if init_path.exists():
            init_content = init_path.read_text(encoding="utf-8")
            init_content = init_content.replace("{{AGENT_CLASS}}", _class_name(agent.id))
            init_path.write_text(init_content, encoding="utf-8")

    def _patch_swarm_py(self, swarm_dir: Path, spec: SwarmSpec) -> None:
        swarm_py = swarm_dir / "swarm.py"
        if not swarm_py.exists():
            return

        content = swarm_py.read_text(encoding="utf-8")
        custom_ids = [a.id for a in spec.agents if a.template != "openswarm_builtin"]

        register_block = self._generate_register_block(spec, custom_ids)
        marker_start = "# OPENSWARM_BUILDER:START"
        marker_end = "# OPENSWARM_BUILDER:END"

        if marker_start in content:
            pattern = re.compile(
                re.escape(marker_start) + r".*?" + re.escape(marker_end),
                re.DOTALL,
            )
            content = pattern.sub(register_block, content)
        else:
            content += f"\n\n{register_block}\n"

        if spec.shared_context and "shared_instructions" in content:
            content = re.sub(
                r'shared_instructions\s*=\s*"""[^"]*"""',
                f'shared_instructions = """{spec.shared_context}"""',
                content,
                count=1,
            )

        swarm_py.write_text(content, encoding="utf-8")

    def _generate_register_block(self, spec: SwarmSpec, custom_ids: list[str]) -> str:
        lines = [
            "# OPENSWARM_BUILDER:START",
            "# Auto-generated agent registrations",
        ]
        for agent_id in custom_ids:
            class_name = _class_name(agent_id)
            lines.append(f"from {agent_id} import {class_name}")
        lines.append("")
        lines.append("_builder_agents = [")
        for agent_id in custom_ids:
            lines.append(f"    {_class_name(agent_id)}(),")
        lines.append("]")
        lines.append("# OPENSWARM_BUILDER:END")
        return "\n".join(lines)

    def _write_manifest(self, swarm_dir: Path, spec: SwarmSpec, port: int) -> None:
        manifest = {
            "name": spec.name,
            "purpose": spec.purpose,
            "port": port,
            "agents": [a.id for a in spec.agents],
            "built_by": "openswarm-builder",
            "spec_version": spec.version,
        }
        (swarm_dir / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

    def _write_env_template(self, swarm_dir: Path, spec: SwarmSpec) -> None:
        env_path = swarm_dir / ".env"
        lines = ["# Generated by openswarm-builder", "OPENAI_API_KEY=", "PORT=8080"]
        for key in spec.integrations.api_keys_required:
            lines.append(f"{key}=")
        if env_path.exists():
            existing = env_path.read_text(encoding="utf-8")
            for line in existing.splitlines():
                if line.strip() and not line.startswith("#"):
                    key = line.split("=", 1)[0]
                    if key not in lines:
                        lines.append(line)
        env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _render_skill_snippet(self, spec: SwarmSpec) -> None:
        from openswarm_builder.core.paths import SKILLS_HOME

        SKILLS_HOME.mkdir(parents=True, exist_ok=True)
        snippet = SKILLS_HOME / f"{spec.name}.md"
        snippet.write_text(
            f"# Skill snippet for swarm `{spec.name}`\n\n"
            f"Run via openswarm-builder API: `POST /run` with swarm `{spec.name}`\n\n"
            f"Example: {spec.example_prompts[0] if spec.example_prompts else 'Hello'}\n",
            encoding="utf-8",
        )


def _class_name(agent_id: str) -> str:
    parts = agent_id.split("_")
    return "".join(p.capitalize() for p in parts) + "Agent"
