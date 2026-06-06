# Hermes integration (thin adapter)

Hermes Super Agent is **consumer #1**, not the builder home.

## Setup

1. Run openswarm-builder API: `openswarm-builder serve`
2. Set `OPENSWARM_BUILDER_URL=http://127.0.0.1:8090` in Hermes environment
3. Import tools from `openswarm_builder.integrations.hermes.tools`

## Tools

| Tool | Description |
|------|-------------|
| `openswarm_design` | Start design loop → proposal |
| `openswarm_approve` | Approve SwarmSpec |
| `openswarm_build` | Materialize after approval |
| `openswarm_respond` | approve / reject / change: |
| `openswarm_list` | List fleet |
| `openswarm_run` | Run swarm message |
| `openswarm_status` | Health + pending count |

## Slack UX

Wire existing Hermes `swarm_commands.py` to call these HTTP wrappers instead of in-process `invoke()`.
