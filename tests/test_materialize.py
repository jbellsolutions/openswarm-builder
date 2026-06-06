import pytest

from openswarm_builder.core.materialize import MaterializeExecutor
from openswarm_builder.core.swarm_spec import AgentSpec, SwarmSpec
from openswarm_builder.service import BuilderService


@pytest.fixture
def isolated_env(tmp_path, monkeypatch):
    swarms = tmp_path / "swarms"
    specs = tmp_path / "specs"
    skills = tmp_path / "skills"
    runs = tmp_path / "runs"
    for p in (swarms, specs, skills, runs):
        p.mkdir()
    monkeypatch.setattr("openswarm_builder.core.paths.SWARMS_HOME", swarms)
    monkeypatch.setattr("openswarm_builder.core.paths.SPECS_HOME", specs)
    monkeypatch.setattr("openswarm_builder.core.paths.SKILLS_HOME", skills)
    monkeypatch.setattr("openswarm_builder.core.paths.RUNS_HOME", runs)
    monkeypatch.setattr("openswarm_builder.core.paths.BUILDER_HOME", tmp_path)
    monkeypatch.setattr(
        "openswarm_builder.core.fleet.registry.REGISTRY_PATH",
        swarms / "registry.yaml",
    )
    return tmp_path


def test_materialize_creates_agent_folders(isolated_env):
    spec = SwarmSpec(
        name="mat-test",
        purpose="Materialize test",
        agents=[
            AgentSpec(id="claude_code_agent", role="Code", template="claude_code_agent"),
            AgentSpec(id="codex_agent", role="Batch", template="codex_agent"),
        ],
    )
    executor = MaterializeExecutor()
    result = executor.execute(spec, spec_id="abc123")
    swarm_dir = isolated_env / "swarms" / "mat-test"
    assert swarm_dir.exists()
    assert (swarm_dir / "claude_code_agent" / "instructions.md").exists()
    assert (swarm_dir / "codex_agent" / "tools.py").exists()
    assert (swarm_dir / ".build" / "spec.json").exists()
    assert result["port"] >= 8081


def test_e2e_design_approve_build(isolated_env):
    service = BuilderService()
    proposal = service.design("Team for coding with Claude and Codex")
    assert proposal["state"] == "pending_approval"
    spec_id = proposal["spec_id"]

    service.approve(spec_id)
    build = service.build(spec_id)
    assert build["status"] == "live"
    swarms = service.list_swarms()
    names = [s["name"] for s in swarms]
    assert build["build"]["name"] in names
