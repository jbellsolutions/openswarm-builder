import pytest

from openswarm_builder.core.approval_gate import ApprovalGate, SpecState
from openswarm_builder.core.design_loop import parse_user_response, run_design_loop
from openswarm_builder.core.swarm_spec import SwarmSpec, AgentSpec


def test_design_loop_produces_spec():
    spec = run_design_loop("Slack integrations and ship PRs with Claude and Codex")
    assert spec.name
    assert any(a.id == "claude_code_agent" for a in spec.agents)
    assert any(a.id == "codex_agent" for a in spec.agents)
    assert "slack" in spec.purpose.lower() or spec.integrations.composio


def test_design_does_not_build_files(isolated_env):
    spec = run_design_loop("A research team")
    assert spec.name
    assert not (isolated_env / "swarms" / spec.name).exists()


def test_approval_gate_fsm(isolated_env):
    gate = ApprovalGate()
    spec = SwarmSpec(name="test-swarm", purpose="Test", agents=[AgentSpec(id="writer", role="Write")])
    record = gate.create_pending(spec, "build a writer swarm")
    assert record.state == SpecState.PENDING_APPROVAL

    with pytest.raises(ValueError):
        gate.mark_building(record.spec_id)

    gate.approve(record.spec_id)
    approved = gate.get(record.spec_id)
    assert approved.state == SpecState.APPROVED


def test_build_requires_approval(isolated_env):
    from openswarm_builder.service import BuilderService

    service = BuilderService()
    proposal = service.design("SEO content team with keyword research")
    with pytest.raises(ValueError, match="approved"):
        service.build(proposal["spec_id"])


def test_parse_user_response():
    assert parse_user_response("approve")[0] == "approve"
    assert parse_user_response("change: drop codex")[0] == "revise"
    assert parse_user_response("reject")[0] == "reject"


def test_swarm_spec_validation():
    spec = SwarmSpec(
        name="my-swarm",
        purpose="Do things",
        agents=[AgentSpec(id="alpha", role="First")],
    )
    md = spec.summary_markdown()
    assert "my-swarm" in md
    assert spec.to_dict()["name"] == "my-swarm"
