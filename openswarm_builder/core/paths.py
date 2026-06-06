"""Central path configuration for openswarm-builder."""
from __future__ import annotations

import os
from pathlib import Path

BUILDER_HOME = Path(os.environ.get("OPENSWARM_BUILDER_HOME", "~/.openswarm")).expanduser()
SWARMS_HOME = Path(os.environ.get("OPENSWARM_HOME", str(BUILDER_HOME / "swarms"))).expanduser()
SPECS_HOME = Path(os.environ.get("OPENSWARM_SPECS_HOME", str(BUILDER_HOME / "specs"))).expanduser()
RUNS_HOME = Path(os.environ.get("OPENSWARM_RUNS_HOME", str(BUILDER_HOME / "runs"))).expanduser()
SKILLS_HOME = Path(os.environ.get("OPENSWARM_SKILLS_HOME", str(BUILDER_HOME / "skills"))).expanduser()


def vendor_root() -> Path:
    override = os.environ.get("OPENSWARM_VENDOR_ROOT")
    if override:
        path = Path(override).expanduser()
        if not path.exists():
            raise RuntimeError(f"OPENSWARM_VENDOR_ROOT={override!r} does not exist")
        return path
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "vendor" / "openswarm"
        if candidate.exists():
            return candidate
    raise RuntimeError("vendor/openswarm not found — run `git submodule update --init`")


def templates_root() -> Path:
    override = os.environ.get("OPENSWARM_TEMPLATES_ROOT")
    if override:
        return Path(override).expanduser()
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "templates"
        if candidate.exists():
            return candidate
    raise RuntimeError("templates/ directory not found")


def ensure_dirs() -> None:
    for path in (BUILDER_HOME, SWARMS_HOME, SPECS_HOME, RUNS_HOME, SKILLS_HOME):
        path.mkdir(parents=True, exist_ok=True)
