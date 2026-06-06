---
name: openswarm-builder
description: Design, approve, and run custom OpenSwarm agent teams via openswarm-builder HTTP API or MCP. Use when the user wants to create a multi-agent swarm, approve a swarm proposal, materialize specialists (including Claude Code and Codex agents), or manage the fleet.
---

# OpenSwarm Builder

Portable swarm factory: **design loop → approval gate → materialize → fleet**.

## When to use

- User describes a team/swarm they want built
- User wants Claude Code + Codex coding specialists in a swarm
- User says approve/reject/change a swarm proposal
- User wants to list/start/run custom swarms

## Environment

```bash
export OPENSWARM_BUILDER_URL=http://127.0.0.1:8090
export OPENSWARM_HOME=~/.openswarm/swarms
```

Start API: `openswarm-builder serve` or `uvicorn openswarm_builder.adapters.http_server:app --port 8090`

## Workflow

1. **Design** — `POST /design` with natural language request → returns `spec_id`, `summary_markdown`, `state: pending_approval`
2. **Never build until approved** — show proposal; wait for explicit approve
3. **Approve** — `POST /specs/{spec_id}/approve`
4. **Build** — `POST /specs/{spec_id}/build` → creates `~/.openswarm/swarms/{name}/` with true agent folders
5. **Run** — `POST /swarms/{name}/run`

## Revision

`POST /specs/{spec_id}/respond` with `change: drop codex, add slides agent` — re-runs design loop, stays pending until approve.

## MCP tools (if configured)

- `openswarm_design_swarm`
- `openswarm_approve_spec`
- `openswarm_build_swarm`
- `openswarm_respond_spec`
- `openswarm_list_swarms`
- `openswarm_run_swarm`

## Hermes integration

Point Hermes at the same API via `integrations/hermes/tools.py` — Hermes is a thin client, not the builder home.
