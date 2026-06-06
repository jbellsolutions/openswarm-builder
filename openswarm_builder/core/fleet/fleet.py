"""Fleet lifecycle — start/stop/provision swarms."""
from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from openswarm_builder.core import paths
from openswarm_builder.core.fleet.http_client import SwarmHttpClient
from openswarm_builder.core.fleet.ports import DEFAULT_PORT, allocate_port
from openswarm_builder.core.fleet.registry import FleetRegistry, SwarmEntry
from openswarm_builder.core.paths import RUNS_HOME, ensure_dirs, vendor_root
from openswarm_builder.core.validators import validate_swarm_dir


def _pid_alive(pid: int | None) -> bool:
    if pid is None:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


class FleetManager:
    def __init__(self, registry: FleetRegistry | None = None) -> None:
        self.registry = registry or FleetRegistry()
        ensure_dirs()

    def list_swarms(self) -> list[dict[str, Any]]:
        entries = self.registry.load()
        result = []
        for name, entry in entries.items():
            alive = _pid_alive(entry.pid)
            if entry.status == "running" and not alive:
                entry.status = "stopped"
                entry.pid = None
                self.registry.upsert(entry)
            result.append({**entry.to_dict(), "url": f"http://127.0.0.1:{entry.port}"})
        return result

    def get_status(self, name: str) -> dict[str, Any]:
        entry = self.registry.get(name)
        if entry is None:
            raise KeyError(f"Swarm {name!r} not registered")
        alive = _pid_alive(entry.pid)
        if entry.status == "running" and not alive:
            entry.status = "stopped"
            entry.pid = None
            self.registry.upsert(entry)
        out: dict[str, Any] = {**entry.to_dict(), "url": f"http://127.0.0.1:{entry.port}", "alive": alive}
        if alive:
            client = SwarmHttpClient(out["url"])
            out["healthy"] = client.health_sync()
        else:
            out["healthy"] = False
        return out

    def provision_vendor_default(self, name: str = "default", port: int | None = None) -> SwarmEntry:
        """Copy vendor/openswarm into fleet home and register."""
        entries = self.registry.load()
        if name in entries:
            return entries[name]

        swarm_dir = self.registry.swarm_dir(name)
        if swarm_dir.exists():
            shutil.rmtree(swarm_dir)
        shutil.copytree(vendor_root(), swarm_dir, symlinks=True)

        assigned_port = port or DEFAULT_PORT
        if name != "default":
            assigned_port = allocate_port(self.registry, preferred=port)

        entry = SwarmEntry(
            name=name,
            port=assigned_port,
            status="stopped",
            source="vendor",
            description="OpenSwarm vendor default swarm",
            tags=["default", "vendor"],
        )
        self.registry.upsert(entry)
        return entry

    def start(self, name: str) -> dict[str, Any]:
        entry = self.registry.get(name)
        if entry is None:
            raise KeyError(f"Swarm {name!r} not registered")

        swarm_dir = self.registry.swarm_dir(name)
        if not swarm_dir.exists():
            raise FileNotFoundError(f"Swarm directory missing: {swarm_dir}")

        if _pid_alive(entry.pid):
            return {"status": "already_running", **entry.to_dict(), "url": f"http://127.0.0.1:{entry.port}"}

        env = os.environ.copy()
        env["PORT"] = str(entry.port)
        env_file = swarm_dir / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                env.setdefault(key.strip(), val.strip())

        log_path = RUNS_HOME / f"{name}.log"
        RUNS_HOME.mkdir(parents=True, exist_ok=True)
        log_file = open(log_path, "a", encoding="utf-8")

        cmd = [sys.executable, "-m", "uvicorn", "server:app", "--host", "127.0.0.1", "--port", str(entry.port)]
        proc = subprocess.Popen(
            cmd,
            cwd=str(swarm_dir),
            env=env,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        entry.pid = proc.pid
        entry.status = "running"
        self.registry.upsert(entry)

        # Wait briefly for health
        client = SwarmHttpClient(f"http://127.0.0.1:{entry.port}")
        for _ in range(30):
            if client.health_sync():
                break
            if not _pid_alive(proc.pid):
                log_file.close()
                raise RuntimeError(f"Swarm {name} exited during startup — see {log_path}")
            time.sleep(0.5)

        return {"status": "started", **entry.to_dict(), "url": f"http://127.0.0.1:{entry.port}", "log": str(log_path)}

    def stop(self, name: str) -> dict[str, Any]:
        entry = self.registry.get(name)
        if entry is None:
            raise KeyError(f"Swarm {name!r} not registered")
        if entry.pid and _pid_alive(entry.pid):
            os.kill(entry.pid, signal.SIGTERM)
            time.sleep(0.5)
            if _pid_alive(entry.pid):
                os.kill(entry.pid, signal.SIGKILL)
        entry.pid = None
        entry.status = "stopped"
        self.registry.upsert(entry)
        return {"status": "stopped", **entry.to_dict()}

    def destroy(self, name: str, remove_files: bool = True) -> dict[str, Any]:
        if name == "default":
            raise ValueError("Cannot destroy the default swarm")
        self.stop(name)
        self.registry.remove(name)
        swarm_dir = paths.SWARMS_HOME / name
        if remove_files and swarm_dir.exists():
            shutil.rmtree(swarm_dir)
        return {"status": "destroyed", "name": name}

    def run_message(self, name: str, message: str, recipient: str | None = None) -> dict[str, Any]:
        entry = self.registry.get(name)
        if entry is None:
            raise KeyError(f"Swarm {name!r} not registered")
        status = self.get_status(name)
        if not status.get("alive"):
            self.start(name)
            status = self.get_status(name)

        import httpx

        payload: dict[str, Any] = {"message": message}
        if recipient:
            payload["recipient_agent"] = recipient

        url = f"http://127.0.0.1:{entry.port}/open-swarm/send_message"
        with httpx.Client(timeout=300.0) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()
