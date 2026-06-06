"""API Researcher — optional integration research."""
from __future__ import annotations

from typing import Any

from openswarm_builder.builder_swarm.requirements_analyst import Requirements


def needs_research(requirements: Requirements) -> bool:
    return bool(requirements.external_apis) or requirements.needs_slack


def research(requirements: Requirements) -> dict[str, Any]:
    apis = []
    for name in requirements.external_apis:
        apis.append(
            {
                "name": name.lower(),
                "integration": "composio" if name in {"COMPOSIO", "SEMRUSH", "GITHUB"} else "direct",
                "notes": f"Configure {name}_API_KEY in swarm .env",
            }
        )
    if requirements.needs_slack:
        apis.append({"name": "slack", "integration": "composio", "notes": "Slack via Composio toolkit"})
    return {"apis": apis, "doc_hint": "See vendor/openswarm docs for Composio setup"}
