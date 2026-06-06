"""Approval gate FSM for SwarmSpec lifecycle."""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from openswarm_builder.core.paths import SPECS_HOME, ensure_dirs
from openswarm_builder.core.swarm_spec import SwarmSpec


class SpecState(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    BUILDING = "building"
    LIVE = "live"
    FAILED = "failed"


@dataclass
class SpecRecord:
    spec_id: str
    state: SpecState
    spec: SwarmSpec
    user_request: str
    summary_markdown: str
    created_at: str
    updated_at: str
    revision: int = 1
    build_error: str | None = None
    swarm_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "spec_id": self.spec_id,
            "state": self.state.value,
            "spec": self.spec.to_dict(),
            "user_request": self.user_request,
            "summary_markdown": self.summary_markdown,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "revision": self.revision,
            "build_error": self.build_error,
            "swarm_name": self.swarm_name,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SpecRecord:
        return cls(
            spec_id=data["spec_id"],
            state=SpecState(data["state"]),
            spec=SwarmSpec.from_dict(data["spec"]),
            user_request=data["user_request"],
            summary_markdown=data.get("summary_markdown", ""),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            revision=data.get("revision", 1),
            build_error=data.get("build_error"),
            swarm_name=data.get("swarm_name"),
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _record_path(spec_id: str) -> Path:
    return SPECS_HOME / spec_id / "record.json"


class ApprovalGate:
    """Persisted FSM: draft → pending_approval → approved → building → live | failed."""

    def __init__(self) -> None:
        ensure_dirs()

    def create_pending(
        self,
        spec: SwarmSpec,
        user_request: str,
        summary_markdown: str | None = None,
    ) -> SpecRecord:
        spec_id = str(uuid.uuid4())[:12]
        now = _now()
        record = SpecRecord(
            spec_id=spec_id,
            state=SpecState.PENDING_APPROVAL,
            spec=spec,
            user_request=user_request,
            summary_markdown=summary_markdown or spec.summary_markdown(),
            created_at=now,
            updated_at=now,
        )
        self._save(record)
        return record

    def get(self, spec_id: str) -> SpecRecord | None:
        path = _record_path(spec_id)
        if not path.exists():
            return None
        return SpecRecord.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def list_records(self, state: SpecState | None = None) -> list[SpecRecord]:
        records: list[SpecRecord] = []
        if not SPECS_HOME.exists():
            return records
        for entry in SPECS_HOME.iterdir():
            path = entry / "record.json"
            if not path.is_file():
                continue
            record = SpecRecord.from_dict(json.loads(path.read_text(encoding="utf-8")))
            if state is None or record.state == state:
                records.append(record)
        return sorted(records, key=lambda r: r.updated_at, reverse=True)

    def approve(self, spec_id: str) -> SpecRecord:
        record = self._require(spec_id)
        if record.state not in {SpecState.PENDING_APPROVAL, SpecState.DRAFT}:
            raise ValueError(f"Cannot approve spec in state {record.state.value}")
        record.state = SpecState.APPROVED
        record.updated_at = _now()
        self._save(record)
        return record

    def reject(self, spec_id: str) -> SpecRecord:
        record = self._require(spec_id)
        if record.state not in {SpecState.PENDING_APPROVAL, SpecState.DRAFT}:
            raise ValueError(f"Cannot reject spec in state {record.state.value}")
        record.state = SpecState.REJECTED
        record.updated_at = _now()
        self._save(record)
        return record

    def apply_revision(
        self,
        spec_id: str,
        spec: SwarmSpec,
        user_request: str,
        summary_markdown: str | None = None,
    ) -> SpecRecord:
        record = self._require(spec_id)
        if record.state == SpecState.REJECTED:
            raise ValueError("Cannot revise a rejected spec — start a new design")
        record.spec = spec
        record.user_request = user_request
        record.summary_markdown = summary_markdown or spec.summary_markdown()
        record.state = SpecState.PENDING_APPROVAL
        record.revision += 1
        record.updated_at = _now()
        self._save(record)
        return record

    def mark_building(self, spec_id: str) -> SpecRecord:
        record = self._require(spec_id)
        if record.state != SpecState.APPROVED:
            raise ValueError(f"Cannot build from state {record.state.value}")
        record.state = SpecState.BUILDING
        record.updated_at = _now()
        self._save(record)
        return record

    def mark_live(self, spec_id: str, swarm_name: str) -> SpecRecord:
        record = self._require(spec_id)
        record.state = SpecState.LIVE
        record.swarm_name = swarm_name
        record.updated_at = _now()
        self._save(record)
        return record

    def mark_failed(self, spec_id: str, error: str) -> SpecRecord:
        record = self._require(spec_id)
        record.state = SpecState.FAILED
        record.build_error = error
        record.updated_at = _now()
        self._save(record)
        return record

    def pending_count(self) -> int:
        return len(self.list_records(SpecState.PENDING_APPROVAL))

    def _require(self, spec_id: str) -> SpecRecord:
        record = self.get(spec_id)
        if record is None:
            raise KeyError(f"Spec {spec_id!r} not found")
        return record

    def _save(self, record: SpecRecord) -> None:
        folder = SPECS_HOME / record.spec_id
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "spec.json").write_text(
            json.dumps(record.spec.to_dict(), indent=2), encoding="utf-8"
        )
        _record_path(record.spec_id).write_text(
            json.dumps(record.to_dict(), indent=2), encoding="utf-8"
        )
