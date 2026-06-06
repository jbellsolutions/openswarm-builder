# OpenSwarm Builder

Standalone portable swarm factory: **design loop → approval gate → materialize → fleet**.

## Features

- **Agent Builder meta-swarm** — requirements, specialist roster, tools, architecture, proposal
- **Approval gate** — no build until explicit `approve`
- **MaterializeExecutor** — true agent folders including `claude_code_agent` and `codex_agent`
- **Portable adapters** — HTTP API, MCP server, SKILL.md
- **Thin Hermes integration** — first consumer, not the product home

## Quick start

```bash
git submodule update --init --recursive
pip install -e ".[dev]"

# Start API
openswarm-builder serve

# Design (returns proposal, does NOT build)
openswarm-builder design "Slack team that ships PRs with Claude and Codex"

# Approve + build
openswarm-builder approve <spec_id>
openswarm-builder build <spec_id>
```

## Environment

| Variable | Default |
|----------|---------|
| `OPENSWARM_BUILDER_HOME` | `~/.openswarm` |
| `OPENSWARM_HOME` | `~/.openswarm/swarms` |
| `OPENSWARM_BUILDER_URL` | `http://127.0.0.1:8090` |

## Tests

```bash
pytest
```

## VPS

See [deploy/VPS_RUNBOOK.md](deploy/VPS_RUNBOOK.md) and `docker compose up`.
