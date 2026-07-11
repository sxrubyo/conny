#!/usr/bin/env bash
set -euo pipefail

python3 /home/ubuntu/bublee/scripts/audit_agents.py
python3 /home/ubuntu/bublee/scripts/audit_runtime_cleanliness.py
python3 /home/ubuntu/bublee/scripts/audit_static_branding.py
caddy validate --config /etc/caddy/Caddyfile >/dev/null

echo "preflight_agents: ok"
