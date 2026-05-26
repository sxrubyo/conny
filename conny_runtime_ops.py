#!/usr/bin/env python3
"""Runtime inspection helpers for Conny CLI, doctor and config surfaces."""
from __future__ import annotations

import json
import os
import re
import shutil
import select
import shlex
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


CONNY_HOME = Path(os.getenv("CONNY_HOME", str(Path.home() / ".conny")))
CONNY_DIR = Path(os.getenv("CONNY_DIR", str(Path(__file__).resolve().parent)))
INSTANCES_DIR = Path(os.getenv("INSTANCES_DIR", str(CONNY_HOME / "instances")))
ACTIVE_INSTANCE_PATH = Path(os.getenv("CONNY_ACTIVE_INSTANCE", str(CONNY_HOME / "active_instance")))

_TUNNEL_PORT_PATTERNS = (
    re.compile(r"-R\s+\d+:(?:localhost|127\.0\.0\.1|0\.0\.0\.0):(\d+)", re.I),
    re.compile(r"localhost:(\d+)"),
    re.compile(r"127\.0\.0\.1:(\d+)"),
    re.compile(r"0\.0\.0\.0:(\d+)"),
    re.compile(r"ngrok\s+http\s+(?:https?://)?(?:localhost:)?(\d+)", re.I),
    re.compile(r"cloudflared\s+tunnel.*--url\s+(?:https?://)?(?:localhost:)?(\d+)", re.I),
    re.compile(r"lt\s+--port\s+(\d+)", re.I),
)

_PUBLIC_URL_PATTERN = re.compile(r"https://[a-zA-Z0-9.-]+(?:lhr\.life|localhost\.run)(?:/[^\s]*)?")


_ENV_KEY_PATTERN = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=")


def _clean_env_value(value: str) -> str:
    value = str(value or "").strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1].strip()
    if value.lower() in {"pending", "none", "null"}:
        return ""
    return value


def _format_env_line(key: str, value: str) -> str:
    value = _clean_env_value(value)
    if not value:
        return f"{key}="
    if any(ch.isspace() for ch in value) or any(ch in value for ch in ['"', "'", "#"]):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'{key}="{escaped}"'
    return f"{key}={value}"


def load_env_file(path: Path) -> Dict[str, str]:
    data: Dict[str, str] = {}
    if not path.exists():
        return data
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key.startswith("export "):
            key = key.split(None, 1)[1].strip()
        data[key] = _clean_env_value(value)
    return data


def write_env_value(path: Path, key: str, value: str) -> None:
    lines: List[str] = []
    found = False
    if path.exists():
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    updated: List[str] = []
    for raw_line in lines:
        match = _ENV_KEY_PATTERN.match(raw_line)
        if match and match.group(1) == key:
            updated.append(_format_env_line(key, value))
            found = True
        else:
            updated.append(raw_line)
    if not found:
        if updated and updated[-1].strip():
            updated.append("")
        updated.append(_format_env_line(key, value))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(updated).rstrip() + "\n", encoding="utf-8")


def active_instance_name() -> str:
    explicit = os.getenv("CONNY_INSTANCE", "").strip()
    if explicit:
        return explicit
    if ACTIVE_INSTANCE_PATH.exists():
        return ACTIVE_INSTANCE_PATH.read_text(encoding="utf-8", errors="replace").strip()
    return ""


def set_active_instance(instance_name: str) -> None:
    instance_name = str(instance_name or "").strip()
    if not instance_name:
        return
    ACTIVE_INSTANCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    ACTIVE_INSTANCE_PATH.write_text(instance_name + "\n", encoding="utf-8")


def instance_root(instance_name: str) -> Path:
    normalized = (instance_name or "").strip()
    if normalized == "base":
        return CONNY_DIR
    if normalized in {"", "conny", "default"}:
        active = active_instance_name()
        if active:
            active_root = INSTANCES_DIR / active
            if active_root.exists():
                return active_root
        if normalized in {"conny", "default"}:
            candidate = INSTANCES_DIR / normalized
            if candidate.exists():
                return candidate
        return CONNY_DIR
    return INSTANCES_DIR / normalized


def instance_runtime_info(instance_name: str) -> Dict[str, Any]:
    root = instance_root(instance_name)
    env_path = root / ".env"
    env = load_env_file(env_path)
    meta_path = root / "instance.json"
    meta: Dict[str, Any] = {}
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            meta = {}
    port_raw = env.get("PORT") or meta.get("port") or ("8001" if root == CONNY_DIR else "8002")
    try:
        port = int(str(port_raw).strip())
    except Exception:
        port = 8001 if root == CONNY_DIR else 8002
    return {
        "name": root.name if root != CONNY_DIR else "base",
        "root": root,
        "env_path": env_path,
        "env": env,
        "meta": meta,
        "port": port,
        "base_url": str(env.get("BASE_URL", "")).strip(),
        "webhook_secret": str(env.get("WEBHOOK_SECRET", "")).strip(),
        "telegram_token": str(env.get("TELEGRAM_TOKEN", "")).strip(),
        "pm2_name": "conny" if root == CONNY_DIR else f"conny-{root.name}",
        "platform": str(env.get("PLATFORM", meta.get("platform", "telegram"))).strip() or "telegram",
    }


MIRRORED_ENV_KEYS = {
    "INSTANCE_ID",
    "PORT",
    "HOST",
    "BASE_URL",
    "PUBLIC_BASE_URL",
    "DASHBOARD_URL",
    "PUBLIC_DASHBOARD_URL",
    "DEMO_MODE",
    "PLATFORM",
    "SECTOR",
    "BUSINESS_NAME",
    "WEBHOOK_SECRET",
    "TUNNEL_PROVIDER",
    "TUNNEL_PID",
    "TUNNEL_COMMAND",
    "TELEGRAM_TOKEN",
    "LLM_PROVIDER",
    "LLM_MODEL",
    "LLM_REASONING",
    "LLM_FAST",
    "LLM_LITE",
    "CUSTOM_API_BASE",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GEMINI_API_KEY",
    "GEMINI_API_KEY_2",
    "GEMINI_API_KEY_3",
    "GEMINI_API_KEY_4",
    "GEMINI_API_KEY_5",
    "GEMINI_API_KEY_6",
    "GEMINI_API_KEY_7",
    "GROQ_API_KEY",
    "OPENROUTER_API_KEY",
    "BRAVE_API_KEY",
    "APIFY_API_KEY",
    "SERP_API_KEY",
    "WA_CLOUD_TOKEN",
    "WA_PHONE_NUMBER_ID",
    "CONNY_PYTHON_BIN",
}


def mirror_instance_env_to_base(instance_name: str) -> None:
    info = instance_runtime_info(instance_name)
    if info["root"] == CONNY_DIR:
        return
    env = load_env_file(info["env_path"])
    if not env:
        return
    base_env_path = CONNY_DIR / ".env"
    for key in sorted(MIRRORED_ENV_KEYS):
        if key in env:
            write_env_value(base_env_path, key, env.get(key, ""))
    write_env_value(base_env_path, "ACTIVE_INSTANCE", info["name"])
    set_active_instance(info["name"])


def port_is_open(port: int, host: str = "127.0.0.1", timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except Exception:
        return False


def python_candidates(instance_name: str = "base") -> List[Dict[str, str]]:
    info = instance_runtime_info(instance_name)
    env = info["env"]
    explicit = [
        ("env:CONNY_PYTHON_BIN", env.get("CONNY_PYTHON_BIN", "")),
        ("env:PYTHON_BIN", env.get("PYTHON_BIN", "")),
        ("process:CONNY_PYTHON_BIN", os.getenv("CONNY_PYTHON_BIN", "")),
        ("process:PYTHON_BIN", os.getenv("PYTHON_BIN", "")),
    ]
    path_candidates = [
        ("instance:.venv", str(info["root"] / ".venv" / "bin" / "python")),
        ("instance:.venv3", str(info["root"] / ".venv" / "bin" / "python3")),
        ("base:.venv", str(CONNY_DIR / ".venv" / "bin" / "python")),
        ("base:.venv3", str(CONNY_DIR / ".venv" / "bin" / "python3")),
        ("home:runtime", str(CONNY_HOME / "runtime" / "bin" / "python")),
        ("home:runtime3", str(CONNY_HOME / "runtime" / "bin" / "python3")),
        ("sys.executable", sys.executable),
        ("PATH:python3", shutil.which("python3") or ""),
        ("PATH:python", shutil.which("python") or ""),
    ]
    seen: set[str] = set()
    resolved: List[Dict[str, str]] = []
    for source, candidate in [*explicit, *path_candidates]:
        candidate = str(candidate or "").strip()
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        exists = Path(candidate).exists()
        resolved.append({"source": source, "path": candidate, "exists": exists})
    return resolved


def resolve_python(instance_name: str = "base") -> Optional[Dict[str, str]]:
    for candidate in python_candidates(instance_name):
        if candidate["exists"]:
            return candidate
    return None


def pm2_processes() -> List[Dict[str, Any]]:
    try:
        result = subprocess.run(
            ["pm2", "jlist"],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return []
        return json.loads(result.stdout)
    except Exception:
        return []


def find_pm2_processes(instance_name: str) -> List[Dict[str, Any]]:
    expected = instance_runtime_info(instance_name)["pm2_name"]
    return [proc for proc in pm2_processes() if proc.get("name") == expected]


def extract_tunnel_target_ports(command_line: str) -> List[int]:
    ports: List[int] = []
    for pattern in _TUNNEL_PORT_PATTERNS:
        for match in pattern.findall(command_line or ""):
            try:
                ports.append(int(match))
            except Exception:
                continue
    deduped: List[int] = []
    seen: set[int] = set()
    for port in ports:
        if port not in seen:
            seen.add(port)
            deduped.append(port)
    return deduped


def rewrite_tunnel_command_port(command_line: str, new_port: int) -> str:
    updated = str(command_line or "")
    replacements = [
        (re.compile(r"(-R\s+\d+:(?:localhost|127\.0\.0\.1|0\.0\.0\.0):)(\d+)", re.I), rf"\g<1>{int(new_port)}"),
        (re.compile(r"(localhost:)(\d+)"), rf"\g<1>{int(new_port)}"),
        (re.compile(r"(127\.0\.0\.1:)(\d+)"), rf"\g<1>{int(new_port)}"),
        (re.compile(r"(0\.0\.0\.0:)(\d+)"), rf"\g<1>{int(new_port)}"),
        (re.compile(r"(\bngrok\s+http\s+)(?:https?://)?(?:localhost:)?(\d+)", re.I), rf"\g<1>{int(new_port)}"),
        (re.compile(r"(\bcloudflared\s+tunnel.*--url\s+)(?:https?://)?(?:localhost:)?(\d+)", re.I), rf"\g<1>http://localhost:{int(new_port)}"),
        (re.compile(r"(\blt\s+--port\s+)(\d+)", re.I), rf"\g<1>{int(new_port)}"),
    ]
    for pattern, replacement in replacements:
        candidate = pattern.sub(replacement, updated)
        if candidate != updated:
            updated = candidate
    return updated


def localhost_run_command(port: int) -> List[str]:
    return [
        "ssh",
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "ServerAliveInterval=60",
        "-N",
        "-R", f"80:localhost:{int(port)}",
        "nokey@localhost.run",
    ]


def start_localhost_run_tunnel(port: int, timeout: float = 25.0) -> Dict[str, Any]:
    if not shutil.which("ssh"):
        return {"ok": False, "url": "", "pid": None, "error": "ssh no está instalado"}
    command = localhost_run_command(port)
    try:
        proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            start_new_session=True,
        )
    except Exception as exc:
        return {"ok": False, "url": "", "pid": None, "error": str(exc)}

    deadline = time.time() + float(timeout)
    output: List[str] = []
    stream = proc.stdout
    while time.time() < deadline:
        if proc.poll() is not None:
            break
        if stream is None:
            time.sleep(0.25)
            continue
        try:
            ready, _, _ = select.select([stream], [], [], 0.5)
        except Exception:
            ready = []
        if not ready:
            continue
        line = stream.readline()
        if not line:
            continue
        output.append(line.rstrip())
        match = _PUBLIC_URL_PATTERN.search(line)
        if match:
            return {
                "ok": True,
                "url": match.group(0).rstrip("/"),
                "pid": proc.pid,
                "command": shlex.join(command),
                "port": int(port),
                "output": "\n".join(output[-10:]),
            }

    try:
        proc.terminate()
    except Exception:
        pass
    return {
        "ok": False,
        "url": "",
        "pid": proc.pid,
        "command": shlex.join(command),
        "port": int(port),
        "error": "\n".join(output[-10:]) or f"no public URL received after {int(timeout)}s",
    }


def detect_tunnel_processes() -> List[Dict[str, Any]]:
    try:
        result = subprocess.run(
            ["ps", "-eo", "pid,args"],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
    except Exception:
        return []
    found: List[Dict[str, Any]] = []
    for raw_line in result.stdout.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        lower = line.lower()
        if not any(token in lower for token in ("ngrok", "cloudflared", "localhost.run", "serveo", "localtunnel", "ssh -r", "ssh -l")):
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            continue
        try:
            pid = int(parts[0])
        except Exception:
            continue
        command = parts[1]
        found.append(
            {
                "pid": pid,
                "command": command,
                "ports": extract_tunnel_target_ports(command),
            }
        )
    return found


def health_payload(port: int) -> Optional[Dict[str, Any]]:
    try:
        import httpx
    except Exception:
        return None
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"http://127.0.0.1:{int(port)}/health")
            if response.status_code == 200:
                return response.json()
    except Exception:
        return None
    return None


def telegram_webhook_info(token: str) -> Dict[str, Any]:
    token = str(token or "").strip()
    if not token:
        return {}
    try:
        import httpx
    except Exception:
        return {}
    try:
        with httpx.Client(timeout=8.0) as client:
            response = client.get(f"https://api.telegram.org/bot{token}/getWebhookInfo")
            payload = response.json()
            if response.status_code == 200 and payload.get("ok"):
                return payload.get("result", {}) or {}
    except Exception:
        return {}
    return {}
