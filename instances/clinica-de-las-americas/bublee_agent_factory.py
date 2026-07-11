"""
Bublee Agent Factory — Crea sub-agentes dinámicos desde WhatsApp.

Cuando el admin pide "Bublee crea un agente que haga X":
1. Bublee pregunta los detalles necesarios (bot token, API key, etc.)
2. Genera una nueva instancia con su propia personalidad y función
3. La conecta a Telegram/WhatsApp
4. La entrena con búsqueda web sobre el tema
5. La deja corriendo independiente

Cada agente creado es una instancia de Bublee con:
- Su propio puerto
- Su propia DB
- Su propio prompt/personalidad
- Conectada a su propia plataforma (Telegram/WhatsApp)
"""
from __future__ import annotations
import os
import json
import shutil
import logging
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List

log = logging.getLogger("bublee.factory")

INSTANCES_DIR = Path(os.getenv("INSTANCES_DIR", "/home/ubuntu/bublee/instances"))
TEMPLATE_DIR = INSTANCES_DIR / "clinica-de-las-americas"  # Bublee herself as template
BUBLEE_VENV = Path("/home/ubuntu/bublee/.venv/bin/python")


class AgentSpec:
    """Especificación de un agente a crear."""
    def __init__(self, name: str, function: str, platform: str = "telegram",
                 sector: str = "general", language: str = "es",
                 telegram_token: str = "", whatsapp_config: Dict = None):
        self.name = name
        self.slug = name.lower().replace(" ", "-").replace("_", "-")
        self.function = function
        self.platform = platform
        self.sector = sector
        self.language = language
        self.telegram_token = telegram_token
        self.whatsapp_config = whatsapp_config or {}
        self.port = self._next_port()
        self.created_at = datetime.utcnow().isoformat()

    def _next_port(self) -> int:
        """Find next available port starting from 8010."""
        used = set()
        for d in INSTANCES_DIR.iterdir():
            if d.is_dir():
                instance_json = d / "instance.json"
                if instance_json.exists():
                    try:
                        data = json.loads(instance_json.read_text())
                        used.add(data.get("port", 0))
                    except:
                        pass
        port = 8010
        while port in used:
            port += 1
        return port


class AgentFactory:
    """Fábrica de agentes dinámicos."""

    def __init__(self):
        self.pending_specs: Dict[str, AgentSpec] = {}

    def parse_request(self, text: str, chat_id: str) -> Optional[Dict]:
        """
        Detecta si un mensaje del admin es una solicitud de creación de agente.
        Returns dict con la info parsed o None si no es una solicitud.
        """
        triggers = [
            "crea un agente", "crear un agente", "crea un bot",
            "quiero un agente", "necesito un agente", "hazme un agente",
            "create an agent", "make an agent", "i need an agent",
        ]
        text_lower = text.lower().strip()
        for trigger in triggers:
            if trigger in text_lower:
                # Extract what comes after the trigger
                idx = text_lower.index(trigger)
                description = text[idx + len(trigger):].strip()
                if description.startswith("que ") or description.startswith("that "):
                    description = description[4:]
                return {
                    "action": "create_agent",
                    "description": description,
                    "chat_id": chat_id,
                }
        return None

    def build_questions(self, spec_partial: Dict) -> List[str]:
        """Genera las preguntas que Bublee debe hacer al admin."""
        questions = []
        if not spec_partial.get("name"):
            questions.append("Como quieres que se llame el agente?")
        if not spec_partial.get("platform"):
            questions.append("En que plataforma lo quieres? Telegram o WhatsApp?")
        if spec_partial.get("platform") == "telegram" and not spec_partial.get("telegram_token"):
            questions.append("Necesito el Bot Token de Telegram. Lo puedes crear con @BotFather")
        if not spec_partial.get("sector"):
            questions.append("De que tema o sector se encarga? (ej: ventas, soporte, reservas)")
        return questions

    def create_instance(self, spec: AgentSpec) -> Dict:
        """
        Crea una nueva instancia de agente basada en la arquitectura de Bublee.
        """
        instance_dir = INSTANCES_DIR / spec.slug

        if instance_dir.exists():
            return {"ok": False, "error": f"Ya existe un agente con el nombre '{spec.slug}'"}

        # Create directory
        instance_dir.mkdir(parents=True)

        # Copy core files from template
        core_files = [
            "bublee.py", "bublee_bridge.py", "bublee_memory_engine.py",
            "bublee_cron.py", "bublee_uncertainty.py", "bublee_smart_features.py",
            "bublee_i18n.py", "bublee_learning.py", "bublee_production.py",
            "knowledge_base.py", "brand_assets.py",
        ]
        for f in core_files:
            src = TEMPLATE_DIR / f
            if src.exists():
                shutil.copy2(src, instance_dir / f)

        # Create .env
        env_content = f"""PORT={spec.port}
HOST=0.0.0.0
PLATFORM={spec.platform}
WEBHOOK_SECRET={spec.slug}_{os.urandom(8).hex()}
BASE_URL=http://3.130.46.55:{spec.port}
WHATSAPP_BRIDGE_URL=http://127.0.0.1:8002
GEMINI_API_KEY={os.getenv('GEMINI_API_KEY', '')}
GEMINI_API_KEY_2={os.getenv('GEMINI_API_KEY_2', '')}
GEMINI_API_KEY_3={os.getenv('GEMINI_API_KEY_3', '')}
LLM_REASONING=google/gemini-2.5-flash
LLM_FAST=google/gemini-2.5-flash
GREETING_ONLY_IDLE_SECONDS=15
DEMO_MODE=false
"""
        if spec.platform == "telegram" and spec.telegram_token:
            env_content += f"TELEGRAM_TOKEN={spec.telegram_token}\n"

        (instance_dir / ".env").write_text(env_content)

        # Create instance.json
        instance_config = {
            "name": spec.slug,
            "label": spec.name,
            "sector": spec.sector,
            "port": spec.port,
            "base_url": f"http://3.130.46.55:{spec.port}",
            "platform": spec.platform,
            "created_at": spec.created_at,
            "created_by": "bublee_agent_factory",
            "function": spec.function,
            "language": spec.language,
        }
        (instance_dir / "instance.json").write_text(json.dumps(instance_config, indent=2))

        # Create identity
        identity_dir = instance_dir / "identity"
        identity_dir.mkdir(exist_ok=True)
        (identity_dir / "IDENTITY.md").write_text(f"""# IDENTITY

- nombre: {spec.name}
- funcion: {spec.function}
- sector: {spec.sector}
- idioma: {spec.language}
- creado_por: Bublee (Kimika AI Agent Factory)
- fecha: {spec.created_at}

## INSTRUCCIONES
{spec.function}
""")

        # Create run.sh
        run_script = f"""#!/bin/bash
cd {instance_dir}
exec {BUBLEE_VENV} bublee.py
"""
        run_sh = instance_dir / "run.sh"
        run_sh.write_text(run_script)
        run_sh.chmod(0o755)

        # Create logs dir
        (instance_dir / "logs").mkdir(exist_ok=True)

        # Initialize DB
        db_path = instance_dir / "bublee.db"
        db = sqlite3.connect(str(db_path))
        db.execute("CREATE TABLE IF NOT EXISTS conversations (id INTEGER PRIMARY KEY)")
        db.commit()
        db.close()

        return {
            "ok": True,
            "instance_dir": str(instance_dir),
            "port": spec.port,
            "slug": spec.slug,
            "pm2_command": f"pm2 start {run_sh} --name {spec.slug} --cwd {instance_dir}",
        }

    def start_instance(self, slug: str) -> Dict:
        """Arranca la instancia con pm2."""
        import subprocess
        instance_dir = INSTANCES_DIR / slug
        run_sh = instance_dir / "run.sh"

        if not run_sh.exists():
            return {"ok": False, "error": "run.sh not found"}

        result = subprocess.run(
            ["pm2", "start", str(run_sh), "--name", slug, "--cwd", str(instance_dir)],
            capture_output=True, text=True
        )
        return {
            "ok": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }


# Singleton
agent_factory = AgentFactory()
