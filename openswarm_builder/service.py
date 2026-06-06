"""High-level service API for design → approve → build → run."""
from __future__ import annotations

from typing import Any

from openswarm_builder.core.approval_gate import ApprovalGate, SpecRecord, SpecState
from openswarm_builder.core.design_loop import parse_user_response, run_design_loop
from openswarm_builder.core.fleet.fleet import FleetManager
from openswarm_builder.core.materialize import MaterializeExecutor
from openswarm_builder.core.swarm_spec import SwarmSpec


class BuilderService:
    def __init__(self) -> None:
        self.gate = ApprovalGate()
        self.fleet = FleetManager()
        self.materializer = MaterializeExecutor(self.fleet)

    def design(self, user_request: str) -> dict[str, Any]:
        spec = run_design_loop(user_request)
        record = self.gate.create_pending(spec, user_request)
        return self._proposal_response(record)

    def get_spec(self, spec_id: str) -> dict[str, Any]:
        record = self.gate.get(spec_id)
        if record is None:
            raise KeyError(f"Spec {spec_id!r} not found")
        return record.to_dict()

    def list_specs(self, state: str | None = None) -> list[dict[str, Any]]:
        st = SpecState(state) if state else None
        return [r.to_dict() for r in self.gate.list_records(st)]

    def respond(self, spec_id: str, message: str) -> dict[str, Any]:
        action, detail = parse_user_response(message)
        record = self.gate.get(spec_id)
        if record is None:
            raise KeyError(f"Spec {spec_id!r} not found")

        if action == "approve":
            record = self.gate.approve(spec_id)
            return {"action": "approved", **self._proposal_response(record)}

        if action == "reject":
            record = self.gate.reject(spec_id)
            return {"action": "rejected", **self._proposal_response(record)}

        if action == "revise":
            revision_request = detail or message
            combined = f"{record.user_request}\n\nRevision: {revision_request}"
            spec = run_design_loop(combined, revision_of=record.spec)
            record = self.gate.apply_revision(spec_id, spec, combined)
            return {"action": "revised", **self._proposal_response(record)}

        return {
            "action": "unknown",
            "message": "Reply with approve, reject, or change: <your edits>",
            **self._proposal_response(record),
        }

    def approve(self, spec_id: str) -> dict[str, Any]:
        record = self.gate.approve(spec_id)
        return self._proposal_response(record)

    def reject(self, spec_id: str) -> dict[str, Any]:
        record = self.gate.reject(spec_id)
        return self._proposal_response(record)

    def build(self, spec_id: str, *, start: bool = False) -> dict[str, Any]:
        record = self.gate.get(spec_id)
        if record is None:
            raise KeyError(f"Spec {spec_id!r} not found")
        if record.state != SpecState.APPROVED:
            raise ValueError(f"Spec must be approved before build (current: {record.state.value})")

        self.gate.mark_building(spec_id)
        try:
            result = self.materializer.execute(record.spec, spec_id=spec_id, start=start)
            self.gate.mark_live(spec_id, record.spec.name)
            return {"status": "live", "build": result, "spec_id": spec_id}
        except Exception as exc:
            self.gate.mark_failed(spec_id, str(exc))
            raise

    def list_swarms(self) -> list[dict[str, Any]]:
        return self.fleet.list_swarms()

    def swarm_status(self, name: str) -> dict[str, Any]:
        return self.fleet.get_status(name)

    def start_swarm(self, name: str) -> dict[str, Any]:
        return self.fleet.start(name)

    def stop_swarm(self, name: str) -> dict[str, Any]:
        return self.fleet.stop(name)

    def run_swarm(self, name: str, message: str, recipient: str | None = None) -> dict[str, Any]:
        return self.fleet.run_message(name, message, recipient)

    def provision_default(self) -> dict[str, Any]:
        entry = self.fleet.provision_vendor_default()
        return entry.to_dict()

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "pending_approvals": self.gate.pending_count(),
            "swarms": len(self.fleet.list_swarms()),
        }

    def _proposal_response(self, record: SpecRecord) -> dict[str, Any]:
        return {
            "spec_id": record.spec_id,
            "state": record.state.value,
            "summary_markdown": record.summary_markdown,
            "spec": record.spec.to_dict(),
            "user_request": record.user_request,
            "revision": record.revision,
        }
