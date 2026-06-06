"""HTTP adapter — REST API for any host agent."""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from openswarm_builder.service import BuilderService

app = FastAPI(title="openswarm-builder", version="0.1.0")
_service: BuilderService | None = None


def get_service() -> BuilderService:
    global _service
    if _service is None:
        _service = BuilderService()
    return _service


class DesignRequest(BaseModel):
    request: str = Field(..., description="Natural language swarm description")


class RespondRequest(BaseModel):
    message: str


class BuildRequest(BaseModel):
    start: bool = False


class RunRequest(BaseModel):
    message: str
    recipient: str | None = None


@app.get("/health")
def health() -> dict[str, Any]:
    return get_service().health()


@app.post("/design")
def design(body: DesignRequest) -> dict[str, Any]:
    return get_service().design(body.request)


@app.get("/specs")
def list_specs(state: str | None = None) -> list[dict[str, Any]]:
    return get_service().list_specs(state)


@app.get("/specs/{spec_id}")
def get_spec(spec_id: str) -> dict[str, Any]:
    try:
        return get_service().get_spec(spec_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/specs/{spec_id}/respond")
def respond(spec_id: str, body: RespondRequest) -> dict[str, Any]:
    try:
        return get_service().respond(spec_id, body.message)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/specs/{spec_id}/approve")
def approve(spec_id: str) -> dict[str, Any]:
    try:
        return get_service().approve(spec_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/specs/{spec_id}/reject")
def reject(spec_id: str) -> dict[str, Any]:
    try:
        return get_service().reject(spec_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/specs/{spec_id}/build")
def build(spec_id: str, body: BuildRequest | None = None) -> dict[str, Any]:
    start = body.start if body else False
    try:
        return get_service().build(spec_id, start=start)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/swarms")
def list_swarms() -> list[dict[str, Any]]:
    return get_service().list_swarms()


@app.post("/swarms/default/provision")
def provision_default() -> dict[str, Any]:
    return get_service().provision_default()


@app.get("/swarms/{name}/status")
def swarm_status(name: str) -> dict[str, Any]:
    try:
        return get_service().swarm_status(name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/swarms/{name}/start")
def start_swarm(name: str) -> dict[str, Any]:
    try:
        return get_service().start_swarm(name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (FileNotFoundError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/swarms/{name}/stop")
def stop_swarm(name: str) -> dict[str, Any]:
    try:
        return get_service().stop_swarm(name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/swarms/{name}/run")
def run_swarm(name: str, body: RunRequest) -> dict[str, Any]:
    try:
        return get_service().run_swarm(name, body.message, body.recipient)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def main() -> None:
    import uvicorn

    uvicorn.run("openswarm_builder.adapters.http_server:app", host="127.0.0.1", port=8090, reload=False)
