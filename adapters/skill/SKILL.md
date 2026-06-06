---
name: openswarm-builder
description: Design, approve, and materialize multi-agent OpenSwarm teams via HTTP API. Use when the user wants to create a swarm, review/approve a proposal, build agent folders (Claude Code, Codex, research, etc.), or manage a swarm fleet. Works from any agent with shell curl or HTTP — not Cursor-specific.
---

# OpenSwarm Builder (portable skill)

**Repo:** https://github.com/jbellsolutions/openswarm-builder

**Product:** design loop → user approval gate → materialize swarm on disk → start/run fleet.

This skill is **host-agnostic**. Any agent with `curl` (or HTTP fetch) can drive the builder. Cursor MCP is optional.

---

## Critical: what `127.0.0.1:8090` means

`127.0.0.1` is **loopback on the machine where the API process is running** — not a public URL.

| Where you are | How to reach the API |
|---------------|----------------------|
| Same Mac/PC that runs `openswarm-builder serve` | `http://127.0.0.1:8090` |
| Browser shows JSON + “Pretty print” checkbox | **That is success** — the API returned JSON |
| Your laptop, API on VPS | **Won’t work directly.** Use SSH tunnel (below) or run commands **on the VPS** |
| Public internet | Port 8090 is **not** exposed on the VPS (by design) |

**SSH tunnel (use builder on VPS from your Mac):**

```bash
ssh -N -L 8090:127.0.0.1:8090 root@209.97.152.67
# then on Mac: curl http://127.0.0.1:8090/health
```

**Or run curl on the VPS:**

```bash
ssh root@209.97.152.67 'curl -s http://127.0.0.1:8090/health'
```

Set `OPENSWARM_BUILDER_URL` to wherever **your** agent can reach the API:

```bash
export OPENSWARM_BUILDER_URL=http://127.0.0.1:8090   # local or tunneled
```

---

## Install (once per host)

```bash
git clone https://github.com/jbellsolutions/openswarm-builder.git
cd openswarm-builder
git submodule update --init --recursive
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

Start API (must be running before any curl/CLI calls):

```bash
openswarm-builder serve
# listens on 127.0.0.1:8090 by default
```

Optional env:

```bash
export OPENSWARM_BUILDER_HOME=~/.openswarm
export OPENSWARM_HOME=~/.openswarm/swarms
export OPENSWARM_BUILDER_URL=http://127.0.0.1:8090
```

---

## Rules for agents

1. **Design first** — never materialize without showing the user the proposal.
2. **Never build until explicit user approval** — `state` must be `approved` before `build`.
3. On revision, use `/respond` — stays `pending_approval` until approve again.
4. Live swarm runs need `OPENAI_API_KEY` (and any keys listed in `api_keys_required`) in the swarm `.env`.

---

## HTTP API (copy-paste for any agent)

Base: `$OPENSWARM_BUILDER_URL` (default `http://127.0.0.1:8090`)

### Health

```bash
curl -s "$OPENSWARM_BUILDER_URL/health"
# {"status":"ok","pending_approvals":N,"swarms":N}
```

### Design (creates proposal, does NOT build)

```bash
curl -s -X POST "$OPENSWARM_BUILDER_URL/design" \
  -H 'Content-Type: application/json' \
  -d '{"request":"Two-agent team: researcher + writer"}'
```

Returns: `spec_id`, `state: pending_approval`, `summary_markdown`, `spec`.

**Show `summary_markdown` to the user.** Wait for approve/reject/change.

### List / get specs

```bash
curl -s "$OPENSWARM_BUILDER_URL/specs"
curl -s "$OPENSWARM_BUILDER_URL/specs?state=pending_approval"
curl -s "$OPENSWARM_BUILDER_URL/specs/{spec_id}"
```

### Revise proposal

```bash
curl -s -X POST "$OPENSWARM_BUILDER_URL/specs/{spec_id}/respond" \
  -H 'Content-Type: application/json' \
  -d '{"message":"drop codex, add slides agent"}'
```

### Approve / reject

```bash
curl -s -X POST "$OPENSWARM_BUILDER_URL/specs/{spec_id}/approve"
curl -s -X POST "$OPENSWARM_BUILDER_URL/specs/{spec_id}/reject"
```

### Build (only after approve)

```bash
curl -s -X POST "$OPENSWARM_BUILDER_URL/specs/{spec_id}/build"
# optional: start swarm immediately
curl -s -X POST "$OPENSWARM_BUILDER_URL/specs/{spec_id}/build" \
  -H 'Content-Type: application/json' \
  -d '{"start": true}'
```

Creates swarm under `$OPENSWARM_HOME/{name}/` and registers in fleet.

### Fleet

```bash
curl -s "$OPENSWARM_BUILDER_URL/swarms"
curl -s -X POST "$OPENSWARM_BUILDER_URL/swarms/{name}/start"
curl -s -X POST "$OPENSWARM_BUILDER_URL/swarms/{name}/stop"
curl -s -X POST "$OPENSWARM_BUILDER_URL/swarms/{name}/run" \
  -H 'Content-Type: application/json' \
  -d '{"message":"Your task here","recipient":null}'
curl -s -X POST "$OPENSWARM_BUILDER_URL/swarms/default/provision"
```

---

## CLI (same host as API)

```bash
openswarm-builder health
openswarm-builder design "your swarm idea"
openswarm-builder approve <spec_id>
openswarm-builder build <spec_id>
openswarm-builder list
```

---

## Hermes / VPS (consumer #1)

**Hermes host (DigitalOcean):** droplet `super-agent-nyc3` — `209.97.152.67` — user `claw`

- Hermes: `/home/claw/hermes-super-agent` (includes `src/agent_os/`)
- Builder: `/home/claw/openswarm-builder` — systemd `openswarm-builder-api` on `127.0.0.1:8090`
- Set on Hermes: `OPENSWARM_BUILDER_URL=http://127.0.0.1:8090`

Hermes calls the builder over HTTP; it does not embed the builder. See repo `integrations/hermes/tools.py`.

---

## Optional: Cursor MCP only

If the host is Cursor with MCP configured:

```json
"openswarm-builder": {
  "command": "/path/to/openswarm-builder/.venv/bin/openswarm-builder-mcp"
}
```

Tools: `openswarm_design_swarm`, `openswarm_approve_spec`, `openswarm_build_swarm`, `openswarm_respond_spec`, `openswarm_list_swarms`, `openswarm_run_swarm`.

**Not required** — HTTP above works everywhere.

---

## Give this skill to any agent

1. Copy this file from the repo: `adapters/skill/SKILL.md`
2. Or point the agent at: `https://raw.githubusercontent.com/jbellsolutions/openswarm-builder/main/adapters/skill/SKILL.md`
3. Ensure the builder API is running and `OPENSWARM_BUILDER_URL` points at it.

The agent only needs shell + curl (or HTTP client) — no Cursor, no MCP.
