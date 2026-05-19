#!/usr/bin/env python3
"""conny init — Infrastructure Provisioning Wizard."""
from __future__ import annotations

import os
import sys
import json
import re
import secrets
import shutil
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from conny_tui_select import select_menu, confirm, text_input

VERSION = "9.3.5"
try: 
    package_path = Path(__file__).parent / "package.json"
    if package_path.exists():
        VERSION = json.loads(package_path.read_text()).get("version", VERSION)
except: pass

# Colors - Vibrant and professional
P1 = "\033[38;5;183m"  # Light Purple
P2 = "\033[38;5;141m"  # Deep Purple
G1 = "\033[38;5;114m"  # Success Green
Y1 = "\033[38;5;221m"  # Warning Yellow
B1 = "\033[1m"         # Bold
D1 = "\033[38;5;242m"  # Professional Gray
W1 = "\033[38;5;231m"  # Bright White
R = "\033[0m"

INSTANCES_DIR = Path("/home/ubuntu/conny-instances")
CONNY_DIR = Path("/home/ubuntu/conny")

SECTORS = [
    ("clinica", "Clínica / Centro médico"),
    ("estetica", "Estética / Belleza"),
    ("restaurante", "Restaurante / Bar"),
    ("salon", "Salón / Peluquería / Barbería"),
    ("inmobiliaria", "Inmobiliaria / Finca raíz"),
    ("gym", "Gimnasio / Fitness"),
    ("ecommerce", "E-commerce / Tienda online"),
    ("hotel", "Hotel / Hospedaje"),
    ("veterinaria", "Veterinaria"),
    ("educacion", "Educación / Academia"),
    ("otro", "Otro"),
]

CHANNELS = [
    ("whatsapp", "WhatsApp (Baileys bridge)"),
    ("whatsapp_cloud", "WhatsApp Cloud API (Meta)"),
    ("telegram", "Telegram"),
    ("both", "WhatsApp + Telegram"),
]

PROVIDERS = [
    ("gemini", "Gemini 2.5 Flash — fast & efficient"),
    ("claude", "Claude 3.5 Sonnet — high quality"),
    ("openrouter", "OpenRouter — multi-model"),
    ("groq", "Groq — ultra low latency"),
]

TONES = [
    ("colombian_warm", "Cálida — professional yet close"),
    ("casual", "Casual — friendly and relaxed"),
    ("formal", "Formal — respectful and direct"),
    ("luxury", "Luxury — sophisticated and exclusive"),
]


def clear():
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def step_header(n, total, title):
    print(f"\n  {P2}{B1}[{n}/{total}]{R} {W1}{B1}{title}{R}")
    print(f"  {D1}{'━' * 54}{R}\n")


def run_wizard():
    clear()
    C1, C2, C3, C4, C5, C6 = "\033[38;5;183m", "\033[38;5;177m", "\033[38;5;141m", "\033[38;5;105m", "\033[38;5;99m", "\033[38;5;63m"
    print(f"""
  {C1}{B1} ██████╗  ██████╗ ███╗   ██╗███╗   ██╗██╗   ██╗{R}
  {C2}{B1}██╔════╝ ██╔═══██╗████╗  ██║████╗  ██║╚██╗ ██╔╝{R}
  {C3}{B1}██║      ██║   ██║██╔██╗ ██║██╔██╗ ██║ ╚████╔╝ {R}
  {C4}{B1}██║      ██║   ██║██║╚██╗██║██║╚██╗██║  ╚██╔╝  {R}
  {C5}{B1}╚██████╗ ╚██████╔╝██║ ╚████║██║ ╚████║   ██║   {R}
  {C6}{B1} ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═══╝   ╚═╝   {R}

  {D1}Enterprise AI Receptionist — Next-Gen Infrastructure{R}
  {P1}✦{R} {W1}{B1}Conny v{VERSION}{R}
  {D1}──────────────────────────────────────────────────────{R}

  {W1}{B1}Infrastructure Provisioning{R} — Automated Setup.
  {D1}Follow the steps to deploy your AI agent.{R}
""")

    if not confirm("Start Configuration?"):
        print(f"\n  {D1}Operation cancelled.{R}\n")
        return

    TOTAL_STEPS = 7

    # 1. Identity
    step_header(1, TOTAL_STEPS, "Identity")
    name = text_input("Business Name", default="Conny Labs")
    instance_id = _slug(name)

    # 2. Domain
    step_header(2, TOTAL_STEPS, "Domain & Industry")
    i = select_menu([s[1] for s in SECTORS], title="Primary Sector")
    sector = SECTORS[i][0]

    # 3. Connectivity
    step_header(3, TOTAL_STEPS, "Connectivity Channels")
    i = select_menu([c[1] for c in CHANNELS], title="Primary Access Channel")
    channel = CHANNELS[i][0]

    # 4. Intelligence
    step_header(4, TOTAL_STEPS, "Intelligence Engine")
    i = select_menu([p[1] for p in PROVIDERS], title="LLM Provider")
    provider = PROVIDERS[i][0]

    # 5. Personality
    step_header(5, TOTAL_STEPS, "Humanization & Tone")
    i = select_menu([t[1] for t in TONES], title="Voice Profile")
    tone = TONES[i][0]

    # 6. Credentials
    step_header(6, TOTAL_STEPS, "Infrastructure & Secrets")
    
    secrets_map = {}
    
    # AI Engine Keys
    if provider == "gemini":
        secrets_map["GEMINI_API_KEY"] = text_input("Gemini API Key", required=True)
    elif provider == "claude":
        secrets_map["ANTHROPIC_API_KEY"] = text_input("Anthropic API Key", required=True)
    elif provider == "groq":
        secrets_map["GROQ_API_KEY"] = text_input("Groq API Key", required=True)
    elif provider == "openrouter":
        secrets_map["OPENROUTER_API_KEY"] = text_input("OpenRouter API Key", required=True)

    # Channel Tokens
    if channel in ["telegram", "both"]:
        secrets_map["TELEGRAM_TOKEN"] = text_input("Telegram Bot Token", required=True)
    
    if channel in ["whatsapp_cloud", "both"]:
        secrets_map["WA_CLOUD_TOKEN"] = text_input("WA Cloud API Token", required=True)
        secrets_map["WA_PHONE_NUMBER_ID"] = text_input("Phone Number ID", required=True)

    # 7. Confirmation
    step_header(7, TOTAL_STEPS, "Final Verification")
    print(f"    {D1}Business:{R}   {P1}{B1}{name}{R}")
    print(f"    {D1}Sector:{R}     {sector}")
    print(f"    {D1}Channel:{R}    {channel}")
    print(f"    {D1}AI Engine:{R}  {provider}")
    print(f"    {D1}Voice:{R}      {tone}")
    print(f"    {D1}Secrets:{R}    {len(secrets_map)} configured")
    print()

    if not confirm("Provision Infrastructure?"):
        print(f"\n  {D1}Cancelled.{R}\n")
        return

    print(f"\n  {D1}Provisioning resources...{R}")
    _create(name, instance_id, sector, channel, provider, tone, secrets_map)
    
    print(f"""
  {G1}{B1}🚀 Infrastructure Deployed Successfully{R}

    {D1}Directory:{R}  {INSTANCES_DIR / instance_id}
    {D1}Control:{R}    {P2}conny status {instance_id}{R}
    {D1}Launch:{R}     {P2}pm2 start {INSTANCES_DIR / instance_id}/run.sh --name conny-{instance_id}{R}
""")


def _create(name, iid, sector, channel, provider, tone, secrets_map):
    idir = INSTANCES_DIR / iid
    idir.mkdir(parents=True, exist_ok=True)
    
    # Calculate next port
    existing_ports = []
    if INSTANCES_DIR.exists():
        for d in INSTANCES_DIR.iterdir():
            env = d / ".env"
            if env.exists():
                for line in env.read_text().splitlines():
                    if line.startswith("PORT="):
                        try: 
                            parts = line.split("=")
                            if len(parts) > 1:
                                existing_ports.append(int(parts[1]))
                        except: pass
    
    port = max(existing_ports + [8003]) + 1
    webhook_secret = f"conny_{iid}_{secrets.token_hex(6)}"

    # Generate .env
    env_lines = [
        f"INSTANCE_ID={iid}",
        f"PORT={port}",
        "DEMO_MODE=false",
        f"PLATFORM={channel}",
        f"SECTOR={sector}",
        f"BUSINESS_NAME=\"{name}\"",
        f"WEBHOOK_SECRET={webhook_secret}",
        f"LLM_PROVIDER={provider}",
        "DEBUG=false"
    ]
    for k, v in secrets_map.items():
        env_lines.append(f"{k}={v}")
    
    (idir / ".env").write_text("\n".join(env_lines) + "\n")

    # Persona file
    (idir / "personas").mkdir(exist_ok=True)
    (idir / "personas" / "persona.yaml").write_text(f"""identity:
  name: Conny
  business: "{name}"
  sector: {sector}
voice:
  tone: {tone}
  language: es_CO
llm:
  provider: {provider}
""")

    # Copy core files
    core = ["conny.py", "conny_admin.py", "conny_production.py", "conny_config.py",
            "conny_utils.py", "conny_commands.py", "conny_learning.py", "conny_voice.py",
            "conny_uncertainty.py", "conny_memory_engine.py", "conny_admin_api.py",
            "conny_cron.py", "conny_nova_proxy.py", "conny_smart_features.py",
            "conny_web_search.py", "conny_google_auth.py", "run.sh", "requirements.txt",
            "conny_design.py", "conny_i18n.py", "conny_cli_bb.py"]
    
    for f in core:
        src = CONNY_DIR / f
        if src.exists(): shutil.copy2(src, idir / f)

    # Directories
    for d in ["soul", "teachings", "memory_store", "knowledge_gaps", "integrations/vault", "logs"]:
        (idir / d).mkdir(parents=True, exist_ok=True)

    # Shell script
    (idir / "run.sh").write_text(f"#!/bin/bash\ncd {idir}\nexec {CONNY_DIR}/.venv/bin/python conny.py\n")
    os.chmod(idir / "run.sh", 0o755)


def _slug(name):
    s = name.lower().strip()
    for a, b in [("á","a"),("é","e"),("í","i"),("ó","o"),("ú","u"),("ñ","n")]:
        s = s.replace(a, b)
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')[:40]


def main():
    try:
        run_wizard()
    except KeyboardInterrupt:
        print(f"\n\n  {D1}Cancelled.{R}\n")

if __name__ == "__main__":
    main()
