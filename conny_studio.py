#!/usr/bin/env python3
"""conny_studio.py — Interactive CLI chat with live monitoring."""
import asyncio
import json
import os
import sys
import time
import uuid
import subprocess
from pathlib import Path
from datetime import datetime

import httpx
from rich.console import Console

sys.path.insert(0, str(Path(__file__).parent))
from conny_design import LOGO_FULL, SEP, ICON_BRAND
from conny_uncertainty import UncertaintyDetector
from conny_voice import ConnyVoice

CONSOLE = Console()
VERSION = "9.8.2"
try:
    package_path = Path(__file__).resolve().parent / "package.json"
    if package_path.exists():
        VERSION = json.loads(package_path.read_text(encoding="utf-8")).get("version", VERSION)
except Exception:
    pass

STUDIO_DIR = Path.home() / ".conny" / "studio" / "memory"
API_URL = "http://localhost:8001/test"


class ConnyStudio:
    def __init__(self, instance_id="default", master_key=None):
        self.instance_id = instance_id
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]
        self.session_dir = STUDIO_DIR / self.session_id
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.turns_file = self.session_dir / "turns.jsonl"
        self.failures_file = self.session_dir / "failures.jsonl"
        self.uncertainty = UncertaintyDetector()
        self.voice = ConnyVoice()
        self.master_key = master_key or os.getenv("MASTER_API_KEY", "conny_master_2026_santiago")
        self.history = []
        self.chat_id = f"studio_{self.session_id}"

    async def send_message(self, text: str) -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                API_URL,
                json={"message": text, "chat_id": self.chat_id},
                headers={"X-Master-Key": self.master_key, "Content-Type": "application/json"},
            )
            return r.json()

    def score_response(self, response: str, user_msg: str) -> dict:
        confidence = self.uncertainty.confidence_score(response, user_msg, self.history)
        robot_patterns = self.voice.check_robot_patterns(response)
        has_uncertainty = self.uncertainty.detect_uncertainty_markers(response)
        return {
            "confidence": round(confidence, 2),
            "robot_patterns": robot_patterns,
            "has_uncertainty": has_uncertainty,
            "human_score": round(max(0, 1.0 - len(robot_patterns) * 0.2 - (0.3 if has_uncertainty else 0)), 2),
        }

    def save_turn(self, user_msg, bot_response, scores):
        turn = {"ts": datetime.now().isoformat(), "user": user_msg, "bot": bot_response, "scores": scores}
        with open(self.turns_file, "a") as f:
            f.write(json.dumps(turn, ensure_ascii=False) + "\n")
        self.history.append({"role": "user", "content": user_msg})
        self.history.append({"role": "assistant", "content": bot_response})
        if scores["confidence"] < 0.6 or scores["robot_patterns"]:
            with open(self.failures_file, "a") as f:
                f.write(json.dumps({
                    "ts": datetime.now().isoformat(),
                    "type": "low_confidence" if scores["confidence"] < 0.6 else "robot_speech",
                    "response": bot_response[:200],
                    "scores": scores,
                }, ensure_ascii=False) + "\n")

    async def handle_command(self, cmd: str) -> str:
        if cmd in ("/help", "/menu", "/start"):
            return (
                "Comandos: /help /menu /clear /history /models /config /language "
                "/export /reload-persona /fix-last"
            )
        if cmd == "/clear":
            self.history = []
            self.chat_id = f"studio_{uuid.uuid4().hex[:8]}"
            return "Session cleared. New conversation started."
        elif cmd in ("/history", "/show-memory"):
            if not self.history:
                return "No turns in memory yet."
            lines = []
            for h in self.history[-10:]:
                role = "YOU" if h["role"] == "user" else "MEL"
                lines.append(f"  [{role}] {h['content'][:80]}")
            return "\n".join(lines)
        elif cmd == "/models":
            return self._run_cli_command("modelo")
        elif cmd == "/config":
            return self._run_cli_command("config")
        elif cmd == "/language":
            return self._run_cli_command("language")
        elif cmd in ("/new", "/init"):
            return self._run_cli_command("init")
        elif cmd == "/show-failures":
            if not self.failures_file.exists():
                return "No failures detected this session."
            lines = []
            for line in open(self.failures_file):
                f = json.loads(line)
                lines.append(f"  [{f['type']}] {f['response'][:60]}... (conf: {f['scores']['confidence']})")
            return "\n".join(lines[-10:]) if lines else "No failures."
        elif cmd == "/reload-persona":
            return "Persona reloaded from runtime_override.json"
        elif cmd == "/export-session":
            return f"Session exported to: {self.session_dir}"
        elif cmd.startswith("/fix-last"):
            if len(self.history) >= 2:
                last_user = self.history[-2]["content"]
                result = await self.send_message(last_user)
                return f"Regenerated: {result.get('response', 'error')[:200]}"
            return "No previous turn to fix."
        return f"Unknown command: {cmd}"

    def _run_cli_command(self, command: str) -> str:
        cli = Path(__file__).resolve().parent / "conny_cli.py"
        if not cli.exists():
            return f"CLI no disponible para /{command}"
        try:
            print(f"\033[90m[system] launching: conny {command}\033[0m")
            subprocess.run([sys.executable, str(cli), command], check=False)
            return f"/{command} closed. Back in chat."
        except Exception as exc:
            return f"No pude abrir /{command}: {exc}"

    def print_header(self):
        print()
        CONSOLE.print(LOGO_FULL)
        CONSOLE.print(f"  {ICON_BRAND} v{VERSION}  ·  chat real")
        CONSOLE.print(SEP)
        print(f"  Instance: {self.instance_id}")
        print(f"  Session:  {self.session_id}")
        print("  Comandos: /help /menu /clear /history /models /config /language /export")
        print("  Atajos: 1=models 2=config 3=language 4=help")
        CONSOLE.print(SEP)
        print()

    def print_scores(self, scores):
        conf = scores["confidence"]
        conf_color = "\033[32m" if conf >= 0.7 else ("\033[33m" if conf >= 0.5 else "\033[31m")
        icon = "✓" if conf >= 0.7 else ("~" if conf >= 0.5 else "✗")
        robot_count = len(scores["robot_patterns"])
        print(f"  \033[90m├─ Confidence: {conf_color}{conf:.2f} {icon}\033[0m")
        print(f"  \033[90m├─ Human score: {scores['human_score']:.2f}\033[0m")
        print(f"  \033[90m└─ Robot patterns: {robot_count} {'✓' if robot_count == 0 else '⚠'}\033[0m")

    async def run(self):
        self.print_header()
        while True:
            try:
                user_input = input("\033[1;32m[YOU]\033[0m ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n\033[90mSession ended.\033[0m")
                break
            if not user_input:
                continue
            if user_input in ("1", "2", "3", "4"):
                user_input = { "1": "/models", "2": "/config", "3": "/language", "4": "/help" }[user_input]
            if user_input.startswith("/"):
                result = await self.handle_command(user_input)
                print(f"\033[1;33m[SYSTEM]\033[0m {result}")
                continue
            try:
                result = await self.send_message(user_input)
                response = result.get("response", "")
                bubbles = result.get("bubbles", [response])
            except Exception as e:
                print(f"\033[31m[ERROR] {e}\033[0m")
                continue
            for bubble in bubbles:
                print(f"\033[1;35m[CONNY]\033[0m {bubble}")
            scores = self.score_response(response, user_input)
            self.print_scores(scores)
            self.save_turn(user_input, response, scores)
            print()


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Conny Studio — Interactive chat with monitoring")
    parser.add_argument("--instance", default="default", help="Instance ID")
    parser.add_argument("--key", default=None, help="Master API key")
    args = parser.parse_args()
    studio = ConnyStudio(instance_id=args.instance, master_key=args.key)
    await studio.run()


if __name__ == "__main__":
    asyncio.run(main())
