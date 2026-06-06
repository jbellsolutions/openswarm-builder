# VPS bootstrap

## 1. Install

```bash
git clone <repo> /opt/openswarm-builder
cd /opt/openswarm-builder
git submodule update --init --recursive
python3 -m venv .venv
source .venv/bin/activate
pip install .
```

## 2. Configure

```bash
export OPENSWARM_BUILDER_HOME=/var/lib/openswarm
export OPENSWARM_HOME=/var/lib/openswarm/swarms
mkdir -p /var/lib/openswarm/swarms
```

Copy `.env.example` to swarm `.env` files as needed (`OPENAI_API_KEY`, etc.).

## 3. systemd

```bash
sudo cp deploy/systemd/openswarm-builder-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now openswarm-builder-api
```

## 4. Health preflight

```bash
curl -s http://127.0.0.1:8090/health | jq .
```

Check `pending_approvals` and swarm count. For each live swarm:

```bash
curl -s http://127.0.0.1:<port>/open-swarm/get_metadata
```

## 5. Docker alternative

```bash
docker compose up -d
```

## 6. Hermes (optional)

Set `OPENSWARM_BUILDER_URL=http://127.0.0.1:8090` on the Hermes host.
