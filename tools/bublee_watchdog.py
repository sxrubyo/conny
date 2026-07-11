#!/usr/bin/env python3
"""Watchdog que monitorea el bridge y lo reinicia si está desconectado."""
import json
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen, Request

BRIDGE_STATUS_URL = "http://localhost:8002/status"
BUBLEE_HEALTH_URL = "http://localhost:8004/health"
LOCK_FILE = Path("/tmp/bublee-watchdog.lock")


def check_bridge():
    try:
        req = Request(BRIDGE_STATUS_URL, headers={"Accept": "application/json"})
        with urlopen(req, timeout=5) as r:
            data = json.loads(r.read())
        return data.get("status") == "open", data
    except Exception:
        return False, {}


def check_bublee():
    try:
        req = Request(BUBLEE_HEALTH_URL, headers={"Accept": "application/json"})
        with urlopen(req, timeout=5) as r:
            data = json.loads(r.read())
        return data.get("status") == "online", data
    except Exception:
        return False, {}


def restart_bridge():
    subprocess.run(["pm2", "restart", "whatsapp-bridge"], capture_output=True, timeout=30)
    return "whatsapp-bridge reiniciado via watchdog"


def restart_bublee():
    subprocess.run(["pm2", "restart", "bublee"], capture_output=True, timeout=30)
    return "bublee reiniciado via watchdog"


def main():
    if LOCK_FILE.exists():
        age = time.time() - LOCK_FILE.stat().st_mtime
        if age < 60:
            return
    LOCK_FILE.touch()

    actions = []

    conn_ok, bridge_data = check_bridge()
    if not conn_ok:
        actions.append(restart_bridge())
    else:
        stats = bridge_data.get("stats", {})
        if stats.get("failed", 0) > stats.get("sent", 0) and stats.get("failed", 0) > 3:
            actions.append(restart_bridge())

    bublee_ok, _ = check_bublee()
    if not bublee_ok:
        actions.append(restart_bublee())

    if actions:
        with open("/home/ubuntu/bublee/logs/watchdog.log", "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {' | '.join(actions)}\n")

    LOCK_FILE.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
