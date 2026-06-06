import pytest
from fastapi.testclient import TestClient

from openswarm_builder.adapters.http_server import app, get_service
from openswarm_builder.service import BuilderService


@pytest.fixture
def client(isolated_env, monkeypatch):
    swarms = isolated_env / "swarms"
    specs = isolated_env / "specs"
    monkeypatch.setattr("openswarm_builder.core.paths.SWARMS_HOME", swarms)
    monkeypatch.setattr("openswarm_builder.core.paths.SPECS_HOME", specs)
    monkeypatch.setattr(
        "openswarm_builder.core.fleet.registry.registry_path",
        lambda: swarms / "registry.yaml",
    )

    import openswarm_builder.adapters.http_server as mod

    mod._service = BuilderService()
    return TestClient(app)


def test_http_design_and_approve(client):
    resp = client.post("/design", json={"request": "Research and write blogs"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["state"] == "pending_approval"
    spec_id = data["spec_id"]

    resp = client.post(f"/specs/{spec_id}/approve")
    assert resp.status_code == 200
    assert resp.json()["state"] == "approved"


def test_http_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
