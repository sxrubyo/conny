#!/usr/bin/env python3
"""conny_doctor.py — health check + self-healing for Conny runtime."""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from conny_runtime_ops import (
    detect_tunnel_processes,
    find_pm2_processes,
    health_payload,
    instance_runtime_info,
    port_is_open,
    python_candidates,
    resolve_python,
    telegram_webhook_info,
)


def color(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"


def green(text: str) -> str:
    return color(text, "32")


def yellow(text: str) -> str:
    return color(text, "33")


def red(text: str) -> str:
    return color(text, "31")


def dim(text: str) -> str:
    return color(text, "90")


def bold(text: str) -> str:
    return color(text, "1")


class HealthCheck:
    def __init__(self, name: str, status: str, message: str = "", remedy: str = ""):
        self.name = name
        self.status = status
        self.message = message
        self.remedy = remedy

    def to_dict(self) -> Dict[str, str]:
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "remedy": self.remedy,
        }

    def __str__(self) -> str:
        icon = {"ok": green("✓"), "warning": yellow("⚠"), "error": red("✗")}[self.status]
        message = f" ({self.message})" if self.message else ""
        return f"  {icon} {self.name}{dim(message)}"


class ConnyDoctor:
    def __init__(self, instance_id: str):
        self.instance_id = instance_id or "base"
        self.info = instance_runtime_info(self.instance_id)
        self.checks: List[HealthCheck] = []
        self.health: Dict[str, Any] = {}
        self.webhook: Dict[str, Any] = {}
        self.tunnels: List[Dict[str, Any]] = []
        self.python: Optional[Dict[str, str]] = None

    async def run_all_checks(self) -> List[HealthCheck]:
        self.checks = []
        self.health = health_payload(self.info["port"]) or {}
        self.webhook = telegram_webhook_info(self.info["telegram_token"]) if self.info["platform"] == "telegram" else {}
        self.tunnels = detect_tunnel_processes()
        self.python = resolve_python(self.info["name"])
        await asyncio.gather(
            self._check_pm2(),
            self._check_api_health(),
            self._check_runtime_python(),
            self._check_runtime_dependencies(),
            self._check_tunnel_alignment(),
            self._check_webhook(),
            self._check_memory_files(),
        )
        return self.checks

    async def _check_pm2(self) -> None:
        processes = find_pm2_processes(self.info["name"])
        if not processes:
            self.checks.append(HealthCheck("PM2 instance", "error", "no registrada", f"pm2 start {self.info['root']}/run.sh --name {self.info['pm2_name']}"))
            return
        proc = processes[0]
        status = proc.get("pm2_env", {}).get("status", "unknown")
        if status == "online":
            self.checks.append(HealthCheck("PM2 instance", "ok", f"{self.info['pm2_name']} online"))
        else:
            self.checks.append(HealthCheck("PM2 instance", "error", f"estado {status}", f"pm2 restart {self.info['pm2_name']}"))

    async def _check_api_health(self) -> None:
        if self.health and self.health.get("status") == "online":
            self.checks.append(HealthCheck("API health", "ok", f"v{self.health.get('version', '?')}"))
            return
        if port_is_open(self.info["port"]):
            self.checks.append(HealthCheck("API health", "warning", f"puerto {self.info['port']} abierto pero /health no responde"))
        else:
            self.checks.append(HealthCheck("API health", "error", f"sin respuesta en :{self.info['port']}", f"pm2 restart {self.info['pm2_name']}"))

    async def _check_runtime_python(self) -> None:
        if self.python:
            self.checks.append(HealthCheck("Python runtime", "ok", self.python["path"]))
        else:
            self.checks.append(HealthCheck("Python runtime", "error", "no encontré intérprete válido", "conny config → Environment & Path Tuning"))

    async def _check_runtime_dependencies(self) -> None:
        if not self.python:
            self.checks.append(HealthCheck("Runtime deps", "error", "sin python disponible"))
            return
        probe = subprocess.run(
            [
                self.python["path"],
                "-c",
                "import fastapi,httpx,dotenv;print('ok')",
            ],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        if probe.returncode == 0:
            self.checks.append(HealthCheck("Runtime deps", "ok", "fastapi/httpx/dotenv presentes"))
        else:
            err = probe.stderr.strip().splitlines()[-1] if probe.stderr.strip() else "faltan dependencias"
            self.checks.append(HealthCheck("Runtime deps", "error", err, "doctor --fix reinstala requirements"))

    async def _check_tunnel_alignment(self) -> None:
        if not self.tunnels:
            self.checks.append(HealthCheck("Tunnel routing", "warning", "sin túneles detectados"))
            return
        target_port = self.info["port"]
        matching = [t for t in self.tunnels if target_port in (t.get("ports") or [])]
        if matching:
            self.checks.append(HealthCheck("Tunnel routing", "ok", f"al menos un túnel apunta a :{target_port}"))
            return
        ports = sorted({p for tunnel in self.tunnels for p in tunnel.get("ports", [])})
        detail = ", ".join(str(p) for p in ports) or "sin puertos parseados"
        self.checks.append(HealthCheck("Tunnel routing", "error", f"túneles apuntan a [{detail}] y no a :{target_port}", "conny config → Network Management"))

    async def _check_webhook(self) -> None:
        if self.info["platform"] != "telegram":
            self.checks.append(HealthCheck("Webhook", "warning", "plataforma no Telegram"))
            return
        base_url = self.info["base_url"]
        secret = self.info["webhook_secret"]
        token = self.info["telegram_token"]
        if not base_url or not secret or not token:
            self.checks.append(HealthCheck("Webhook", "warning", "faltan BASE_URL / TELEGRAM_TOKEN / WEBHOOK_SECRET"))
            return
        expected = f"{base_url.rstrip('/')}/webhook/{secret}"
        current = self.webhook.get("url", "")
        if current == expected:
            self.checks.append(HealthCheck("Webhook", "ok", "registrado correctamente"))
        elif current:
            self.checks.append(HealthCheck("Webhook", "error", f"apunta a {current}", "conny config → Gateway & Webhooks"))
        else:
            self.checks.append(HealthCheck("Webhook", "error", "sin webhook registrado", "conny config → Gateway & Webhooks"))

    async def _check_memory_files(self) -> None:
        db_path = Path(self.info["env"].get("DB_PATH") or self.info["root"] / "conny_ultra.db")
        wal_path = Path(str(db_path) + "-wal")
        if db_path.exists():
            msg = f"{db_path.name} presente"
            if wal_path.exists() and wal_path.stat().st_size > 64 * 1024 * 1024:
                self.checks.append(HealthCheck("Memory/DB", "warning", f"WAL grande ({wal_path.stat().st_size // (1024*1024)}MB)"))
            else:
                self.checks.append(HealthCheck("Memory/DB", "ok", msg))
        else:
            self.checks.append(HealthCheck("Memory/DB", "warning", "base de datos aún no creada"))

    def print_report(self) -> None:
        print()
        print(bold(f"Conny Doctor — {self.instance_id}"))
        print("─" * 60)
        for check in self.checks:
            print(str(check))
            if check.remedy and check.status != "ok":
                print(f"     {dim('run:')} {check.remedy}")
        print("─" * 60)
        ok = sum(1 for c in self.checks if c.status == "ok")
        warn = sum(1 for c in self.checks if c.status == "warning")
        err = sum(1 for c in self.checks if c.status == "error")
        print(f"  {green(str(ok) + ' ok')}  {yellow(str(warn) + ' warnings')}  {red(str(err) + ' errors')}")
        print()

    async def auto_heal(self) -> List[str]:
        actions: List[str] = []
        if any(c.name == "Runtime deps" and c.status == "error" for c in self.checks):
            if self.python:
                result = subprocess.run(
                    [
                        self.python["path"],
                        "-m",
                        "pip",
                        "install",
                        "--disable-pip-version-check",
                        "-r",
                        str(Path(self.info["root"]) / "requirements.txt"),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=600,
                    check=False,
                )
                if result.returncode == 0:
                    actions.append("requirements reinstalados")
        if any(c.name in {"PM2 instance", "API health"} and c.status == "error" for c in self.checks):
            run_script = Path(self.info["root"]) / "run.sh"
            if run_script.exists():
                run_script.chmod(run_script.stat().st_mode | 0o111)
                subprocess.run(["pm2", "delete", self.info["pm2_name"]], capture_output=True, check=False)
                result = subprocess.run(
                    [
                        "pm2", "start", str(run_script),
                        "--name", self.info["pm2_name"],
                        "--cwd", str(self.info["root"]),
                        "--restart-delay", "3000",
                        "--max-restarts", "10",
                        "--log", str(Path(self.info["root"]) / "logs" / "conny.log"),
                        "--error", str(Path(self.info["root"]) / "logs" / "error.log"),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    check=False,
                )
                if result.returncode == 0:
                    actions.append(f"PM2 re-registrado para {self.info['pm2_name']}")
        if any(c.name == "Webhook" and c.status == "error" for c in self.checks):
            await self._auto_sync_webhook(actions)
        return actions

    async def _auto_sync_webhook(self, actions: List[str]) -> None:
        base_url = self.info["base_url"]
        secret = self.info["webhook_secret"]
        token = self.info["telegram_token"]
        if not base_url or not secret or not token:
            return
        target = f"{base_url.rstrip('/')}/webhook/{secret}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"https://api.telegram.org/bot{token}/setWebhook",
                    json={"url": target},
                )
            payload = response.json()
            if response.status_code == 200 and payload.get("ok"):
                actions.append(f"Webhook resincronizado → {target}")
        except Exception:
            return

    async def run_self_healing(self) -> List[str]:
        await self.run_all_checks()
        self.print_report()
        actions = await self.auto_heal()
        if actions:
            print(bold("Auto-heal actions"))
            for action in actions:
                print(f"  {green('→')} {action}")
            print()
            await asyncio.sleep(2)
            await self.run_all_checks()
            self.print_report()
        return actions


async def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(prog="conny doctor", description="Health check and self-heal for Conny instances")
    parser.add_argument("instance", nargs="?", default="base", help="Instance name")
    parser.add_argument("--fix", action="store_true", help="Intentar auto-reparación")
    parser.add_argument("--json", action="store_true", help="Salida JSON")
    args = parser.parse_args()

    doctor = ConnyDoctor(args.instance)
    await doctor.run_all_checks()

    if args.fix:
        actions = await doctor.auto_heal()
        await asyncio.sleep(1)
        await doctor.run_all_checks()
    else:
        actions = []

    if args.json:
        print(json.dumps({"checks": [c.to_dict() for c in doctor.checks], "actions": actions}, ensure_ascii=False, indent=2))
    else:
        doctor.print_report()
        if actions:
            print(bold("Auto-heal actions"))
            for action in actions:
                print(f"  {green('→')} {action}")
            print()


if __name__ == "__main__":
    asyncio.run(main())
