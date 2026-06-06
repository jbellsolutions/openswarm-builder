"""Requirements Analyst — parse user intent and constraints."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from openswarm_builder.core.swarm_spec import SwarmSpec


@dataclass
class Requirements:
    raw_request: str
    purpose: str
    channels: list[str] = field(default_factory=list)
    output_types: list[str] = field(default_factory=list)
    needs_coding: bool = False
    needs_batch_coding: bool = False
    needs_slack: bool = False
    needs_research: bool = False
    needs_content: bool = False
    external_apis: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw_request": self.raw_request,
            "purpose": self.purpose,
            "channels": self.channels,
            "output_types": self.output_types,
            "needs_coding": self.needs_coding,
            "needs_batch_coding": self.needs_batch_coding,
            "needs_slack": self.needs_slack,
            "needs_research": self.needs_research,
            "needs_content": self.needs_content,
            "external_apis": self.external_apis,
            "constraints": self.constraints,
        }


def _slug_words(text: str) -> str:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return "-".join(words[:4]) if words else "custom-swarm"


def analyze(user_request: str, revision_of: SwarmSpec | None = None) -> Requirements:
    text = user_request.lower()
    purpose = user_request.strip()

    channels: list[str] = []
    if "slack" in text:
        channels.append("slack")
    if "telegram" in text:
        channels.append("telegram")
    if "email" in text:
        channels.append("email")

    output_types: list[str] = []
    if any(w in text for w in ("blog", "post", "content", "seo", "article")):
        output_types.append("content")
    if any(w in text for w in ("pr", "pull request", "code", "repo", "github")):
        output_types.append("code")
    if any(w in text for w in ("slide", "deck", "presentation")):
        output_types.append("slides")
    if any(w in text for w in ("research", "competitor", "keyword")):
        output_types.append("research")

    needs_coding = any(
        w in text
        for w in (
            "code",
            "coding",
            "claude code",
            "repo",
            "repository",
            "pr",
            "pull request",
            "implement",
            "ship",
            "github",
        )
    )
    needs_batch = any(w in text for w in ("codex", "batch", "background", "ci", "automated implementation"))
    needs_slack = "slack" in text or "composio" in text
    needs_research = any(w in text for w in ("research", "competitor", "keyword", "analysis", "semrush"))
    needs_content = any(w in text for w in ("blog", "write", "content", "seo", "copy"))

    external_apis: list[str] = []
    if "semrush" in text:
        external_apis.append("SEMRUSH")
    if "github" in text:
        external_apis.append("GITHUB")
    if needs_slack:
        external_apis.append("COMPOSIO")

    constraints: list[str] = []
    if revision_of:
        constraints.append(f"Revise existing swarm {revision_of.name}")

    if not purpose:
        purpose = "Custom multi-agent swarm"

    return Requirements(
        raw_request=user_request,
        purpose=purpose,
        channels=channels or ["api"],
        output_types=output_types or ["general"],
        needs_coding=needs_coding or needs_batch,
        needs_batch_coding=needs_batch or needs_coding,
        needs_slack=needs_slack,
        needs_research=needs_research,
        needs_content=needs_content,
        external_apis=external_apis,
        constraints=constraints,
    )
