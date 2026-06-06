"""Port allocation for swarm fleet."""
from __future__ import annotations

import os
import socket

from openswarm_builder.core.fleet.registry import FleetRegistry

DEFAULT_PORT = int(os.environ.get("OPENSWARM_DEFAULT_PORT", "8080"))
PORT_RANGE_START = int(os.environ.get("OPENSWARM_PORT_START", "8081"))
PORT_RANGE_END = int(os.environ.get("OPENSWARM_PORT_END", "8180"))


def is_port_free(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
            return True
        except OSError:
            return False


def allocate_port(registry: FleetRegistry | None = None, preferred: int | None = None) -> int:
    registry = registry or FleetRegistry()
    used = {entry.port for entry in registry.load().values()}

    if preferred is not None and preferred not in used and is_port_free(preferred):
        return preferred

    for port in range(PORT_RANGE_START, PORT_RANGE_END + 1):
        if port in used:
            continue
        if is_port_free(port):
            return port

    raise RuntimeError(f"No free ports in range {PORT_RANGE_START}-{PORT_RANGE_END}")
