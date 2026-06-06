"""Fleet registry — adapted from hermes-super-agent-openswarm for standalone use."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from openswarm_builder.core import paths
from openswarm_builder.core.paths import ensure_dirs


def registry_path() -> Path:
    import os

    return Path(
        os.environ.get("OPENSWARM_REGISTRY", str(paths.SWARMS_HOME / "registry.yaml"))
    ).expanduser()


REGISTRY_PATH = registry_path()  # default at import; tests should patch registry_path target


@dataclass
class SwarmEntry:
    name: str
    port: int
    status: str = "stopped"
    pid: int | None = None
    created_at: str = ""
    updated_at: str = ""
    source: str = "vendor"
    description: str = ""
    tags: list[str] = field(default_factory=list)
    spec_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "port": self.port,
            "status": self.status,
            "pid": self.pid,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "source": self.source,
            "description": self.description,
            "tags": self.tags,
            "spec_id": self.spec_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SwarmEntry:
        return cls(
            name=data["name"],
            port=int(data["port"]),
            status=data.get("status", "stopped"),
            pid=data.get("pid"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            source=data.get("source", "vendor"),
            description=data.get("description", ""),
            tags=list(data.get("tags") or []),
            spec_id=data.get("spec_id"),
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class FleetRegistry:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or registry_path()
        ensure_dirs()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict[str, SwarmEntry]:
        if not self.path.exists():
            return {}
        raw = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
        swarms = raw.get("swarms") or {}
        return {name: SwarmEntry.from_dict(entry) for name, entry in swarms.items()}

    def save(self, entries: dict[str, SwarmEntry]) -> None:
        payload = {
            "version": 1,
            "updated_at": _now(),
            "swarms": {name: entry.to_dict() for name, entry in entries.items()},
        }
        self.path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    def get(self, name: str) -> SwarmEntry | None:
        return self.load().get(name)

    def upsert(self, entry: SwarmEntry) -> None:
        entries = self.load()
        existing = entries.get(entry.name)
        now = _now()
        if existing:
            entry.created_at = existing.created_at or now
        else:
            entry.created_at = now
        entry.updated_at = now
        entries[entry.name] = entry
        self.save(entries)

    def remove(self, name: str) -> bool:
        entries = self.load()
        if name not in entries:
            return False
        del entries[name]
        self.save(entries)
        return True

    def list_names(self) -> list[str]:
        return sorted(self.load().keys())

    def swarm_dir(self, name: str) -> Path:
        return paths.SWARMS_HOME / name
