import pytest


@pytest.fixture
def tmp_paths(tmp_path):
    return tmp_path


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
        "openswarm_builder.core.fleet.registry.registry_path",
        lambda: swarms / "registry.yaml",
    )
    return tmp_path
