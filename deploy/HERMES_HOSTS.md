# Hermes / Agent OS infrastructure

Last verified: 2026-06-06 via `doctl compute droplet list` and SSH.

## Primary Hermes + Agent OS host

| Field | Value |
|-------|--------|
| Droplet name | **super-agent-nyc3** |
| Droplet ID | 570862075 |
| Public IP | **209.97.152.67** |
| Region | NYC3 |
| Tags | `super-agent`, `super-saiyan` |
| SSH | `ssh root@209.97.152.67` (app user: `claw`) |

### Paths on box

| Path | Purpose |
|------|---------|
| `/home/claw/hermes-super-agent` | Hermes super-agent repo (`main`) |
| `/home/claw/hermes-super-agent/src/agent_os` | Agent OS module |
| `/home/claw/.hermes/hermes-agent` | Hermes gateway install + venv |
| `/home/claw/openswarm-builder` | OpenSwarm Builder API (git clone) |
| `/home/claw/.openswarm/swarms` | Materialized swarms |

### Services

| Service | Command / unit |
|---------|------------------|
| OpenSwarm Builder API | `systemctl status openswarm-builder-api` → `127.0.0.1:8090` |
| OpenSwarm default orchestrator | `systemctl --user status openswarm-default` → port **8080** |
| Hermes webapp (chat/voice) | `systemctl --user status hermes-webapp` → port **9119** |
| Hermes gateway | `systemctl --user status hermes-supersan` → Telegram/Slack/etc. |

### Public URLs (HTTP basic auth — `/etc/nginx/.htpasswd`)

| URL | What |
|-----|------|
| http://209.97.152.67/ | Hermes Super Agent web chat (`/chat`) and voice (`/voice`) |
| http://209.97.152.67/openswarm/docs | OpenSwarm orchestrator API docs (Swagger) |
| http://209.97.152.67/openswarm/open-swarm/get_metadata | Orchestrator metadata (programmatic) |

Builder API stays localhost-only: `http://127.0.0.1:8090` (SSH tunnel if needed from laptop).

### Skills installed

- `vault/skills/active/tools/openswarm-builder.md` — portable builder skill (design → approve → build)
- `vault/skills/active/tools/openswarm.md` — Hermes runtime routing skill

### Env

- Hermes: `/home/claw/.hermes/hermes-agent/.env`
- Builder URL for Hermes: `OPENSWARM_BUILDER_URL=http://127.0.0.1:8090`

### Known issues (2026-06-06)

- Slack gateway: `invalid_auth` on `auth.test` — rotate `SLACK_BOT_TOKEN` / `SLACK_APP_TOKEN` in Hermes `.env` and restart gateway.

## Other DO droplets (not Hermes primary)

| Name | IP | Notes |
|------|-----|--------|
| single-brain | 104.236.11.200 | separate stack |
| openhuman | 159.203.123.32 | OpenHuman |
| cold-email-agent | 134.122.17.43 | automation |
| skool-bot | 152.42.231.109 | automation |
| video-editing-studio | 167.99.75.167 | video pipeline |

## Verify anytime

```bash
doctl compute droplet list
ssh root@209.97.152.67 'curl -s http://127.0.0.1:8090/health; hostname'
```
