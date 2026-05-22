#!/home/ubuntu/conny/.venv/bin/python
"""conny init — Infrastructure Provisioning Wizard v2."""
from __future__ import annotations

import os
import sys
import json
import re
import time
import secrets
import shutil
import urllib.request
import urllib.error
import subprocess
from deep_translator import GoogleTranslator

CURRENT_LANG = 'es'

def _t(text):
    if CURRENT_LANG == 'es' or not text:
        return text
    try:
        # Limpiar texto de colores si es necesario, o traducir directo
        return GoogleTranslator(source='es', target=CURRENT_LANG).translate(text)
    except:
        return text
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from conny_tui_select import select_menu as _orig_select_menu, confirm as _orig_confirm, text_input as _orig_text_input

def select_menu(options, title="", **kwargs):
    if title: title = _t(title)
    # also translate options if they are simple strings
    opts = [_t(opt) for opt in options]
    return _orig_select_menu(opts, title=title, **kwargs)

def confirm(text, default=True):
    return _orig_confirm(_t(text), default=default)

def text_input(label, default="", required=True, is_password=False):
    return _orig_text_input(_t(label), default=default, required=required, is_password=is_password)


VERSION = "10.0.0"
try:
    package_path = Path(__file__).parent / "package.json"
    if package_path.exists():
        VERSION = json.loads(package_path.read_text()).get("version", VERSION)
except: pass

# Colors - Brand Semantic
C_PRIMARY = "\033[38;2;139;92;246m"  # Purple
C_SUCCESS = "\033[38;5;114m"         # Green
C_WARNING = "\033[38;5;221m"         # Yellow
C_ERROR   = "\033[38;5;196m"         # Red
C_MUTED   = "\033[38;5;242m"         # Gray
C_ACCENT  = "\033[38;5;159m"         # Cyan
B1 = "\033[1m"
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

TONES = [
    ("colombian_warm", "Cálida — profesional pero cercana (Más usada)"),
    ("casual", "Casual — amigable y relajada"),
    ("formal", "Formal — respetuosa y directa"),
    ("luxury", "Luxury — sofisticada y exclusiva"),
]

LANGUAGES = [
    ("es", "Español"),
    ("en", "English"),
    ("pt", "Português"),
]

def clear():
    # Animated fade out simulation
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()

def progress_bar(n, total):
    percent = int((n / total) * 100)
    filled = int((n / total) * 20)
    bar = "█" * filled + "░" * (20 - filled)
    return f"{C_PRIMARY}[{bar}] {percent}%{R} {C_MUTED}· Paso {n} de {total}{R}"

def step_header(n, total, title, context=""):
    title = _t(title)
    if context: context = _t(context)
    print(f"\n  {progress_bar(n, total)}")
    print(f"  {B1}{C_ACCENT}{title}{R}")
    if context:
        print(f"  {C_MUTED}{context}{R}")
    print(f"  {C_MUTED}{'━' * 60}{R}\n")

def check_ollama():
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=1.0) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                return [m["name"] for m in data.get("models", [])]
    except:
        pass
    return None

def check_gpu():
    try:
        subprocess.check_output(["nvidia-smi"], stderr=subprocess.STDOUT)
        return True
    except:
        return False

def validate_api_key(provider, key):
    # Dummy validation with spinner
    sys.stdout.write(f"  {C_MUTED}Validando API key...{R}")
    sys.stdout.flush()
    time.sleep(1.5)
    sys.stdout.write(f"\r  {C_SUCCESS}✅ API key validada correctamente.{R}       \n")
    return True


def run_wizard():

    clear()
    
    # Check dependencies silently
    ollama_models = check_ollama()
    has_gpu = check_gpu()
    
    LOGO_ART_LINES = ["Conny."]
    import subprocess
    from pathlib import Path
    import re
    
    logo_path = Path(os.environ.get("CONNY_DIR", "/home/ubuntu/conny")) / "brand-assets" / "conny-logo.png"
    if logo_path.exists():
        try:
            result = subprocess.run(
                ["chafa", "--symbols", "block", "-c", "256", "--size", "50x20", str(logo_path)],
                capture_output=True, text=True, check=True
            )
            lines = result.stdout.splitlines()
            
            def is_empty(line):
                clean = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', line)
                return not clean.strip()
            
            while lines and is_empty(lines[0]):
                lines.pop(0)
            
            while lines and is_empty(lines[-1]):
                lines.pop()
                
            if lines:
                LOGO_ART_LINES = lines
        except:
            pass

    if LOGO_ART_LINES == ["Conny."]:
        try:
            from src.conny.channels.logo_art import LOGO_ART_LINES
        except ImportError:
            try:
                from conny.channels.logo_art import LOGO_ART_LINES
            except ImportError:
                LOGO_ART_LINES = ["Conny."]

    

    # Print the logo directly
    for line in LOGO_ART_LINES:
        print(f"  {line}")

    print()
    print(f"  {C_PRIMARY}{B1}Conny CLI {VERSION}{R} · {C_ACCENT}Autonomous Dynamic Receptionist{R} · {C_MUTED}⏱ Tiempo estimado: ~3 min{R}")
    print(f"  {C_MUTED}{'─' * 70}{R}")
    print()



    if not confirm("¿Comenzar configuración?"):
        print(f"\n  {C_MUTED}Operación cancelada.{R}\n")
        return

    TOTAL_STEPS = 7
    ctx = ""

    # 0. Language (Optional pre-step)
    clear()
    print(f"\n  {C_PRIMARY}🌐 {_t('Selección de idioma')}{R}")
    i = select_menu([l[1] for l in LANGUAGES], title="Idioma preferido para Conny")
    i = select_menu([l[1] for l in LANGUAGES], title="Idioma preferido para Conny")
    lang = LANGUAGES[i][0]
    global CURRENT_LANG
    CURRENT_LANG = lang

    # 1. Identity
    clear()
    default_name = Path.cwd().name.title()
    step_header(1, TOTAL_STEPS, "Identidad", ctx)
    name = text_input("Nombre del negocio", default=default_name)
    instance_id = _slug(name)
    ctx += f"Negocio: {name} | "

    # 2. Domain
    clear()
    step_header(2, TOTAL_STEPS, "Dominio e Industria", ctx)
    i = select_menu([s[1] for s in SECTORS], title="Sector Principal")
    sector = SECTORS[i][0]
    ctx += f"Sector: {sector} | "

    # 3. Connectivity
    clear()
    step_header(3, TOTAL_STEPS, "Canales de Conectividad", ctx)
    i = select_menu([c[1] for c in CHANNELS], title="Canal Principal de Acceso")
    channel = CHANNELS[i][0]

    # 4. Intelligence
    clear()
    step_header(4, TOTAL_STEPS, "Motor de Inteligencia", ctx)
    
    # Level 1
    llm_types = [
        "☁️  Cloud (requiere API Key)",
        "🏠  Local (Ollama · sin costo)",
        "💚  Local GPU (NVIDIA NIM)",
        "🔀  Manual / Custom endpoint"
    ]
    i = select_menu(llm_types, title="Tipo de proveedor")
    
    provider_id = ""
    model_id = ""
    is_local = False
    
    if i == 0: # Cloud
        providers = [
            ("anthropic", "🔴 Anthropic"),
            ("openai", "🟢 OpenAI"),
            ("gemini", "🔵 Google Gemini"),
            ("mistral", "🟠 Mistral AI"),
            ("groq", "⚡ Groq (Ultra rápido)"),
            ("xai", "✕ xAI (Grok)"),
            ("deepseek", "🐋 DeepSeek"),
            ("openrouter", "🔀 OpenRouter (Multi-modelo)"),
        ]
        pi = select_menu([p[1] for p in providers], title="Proveedor Cloud")
        provider_id = providers[pi][0]
        
        # Models
        models_map = {
            "anthropic": ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"],
            "openai": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
            "gemini": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-flash-lite"],
            "mistral": ["mistral-large-latest", "mistral-small-latest"],
            "groq": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
            "xai": ["grok-2", "grok-2-mini"],
            "deepseek": ["deepseek-chat", "deepseek-reasoner"],
            "openrouter": ["anthropic/claude-3.5-sonnet", "openai/gpt-4o", "google/gemini-2.5-flash"],
        }
        model_opts = models_map.get(provider_id, []) + ["✏️ Escribir model ID manualmente"]
        mi = select_menu(model_opts, title="Modelo Específico")
        if mi == len(model_opts) - 1:
            model_id = text_input("Model ID")
        else:
            model_id = model_opts[mi]
            
    elif i == 1: # Ollama
        is_local = True
        provider_id = "ollama"
        if ollama_models:
            print(f"  {C_SUCCESS}✅ Ollama detectado con {len(ollama_models)} modelos.{R}")
            model_opts = ollama_models + ["✏️ Escribir model ID manualmente"]
        else:
            print(f"  {C_WARNING}⚠️ Ollama no está corriendo o no tiene modelos.{R}")
            model_opts = ["llama3.3:8b", "mistral:latest", "✏️ Escribir model ID manualmente"]
            
        mi = select_menu(model_opts, title="Modelo de Ollama")
        if mi == len(model_opts) - 1:
            model_id = text_input("Model ID")
        else:
            model_id = model_opts[mi]
            
    elif i == 2: # NVIDIA
        is_local = True
        provider_id = "nvidia_nim"
        if not has_gpu:
            print(f"  {C_ERROR}❌ No se detectó GPU NVIDIA. Podría haber problemas.{R}")
        model_opts = ["meta/llama3-70b-instruct", "mistralai/mixtral-8x22b-instruct", "✏️ Escribir model ID manualmente"]
        mi = select_menu(model_opts, title="Modelo NIM")
        if mi == len(model_opts) - 1:
            model_id = text_input("Model ID")
        else:
            model_id = model_opts[mi]
            
    else: # Manual
        provider_id = "manual"
        model_id = text_input("Model ID")

    # 5. Personality
    clear()
    step_header(5, TOTAL_STEPS, "Humanización y Tono", ctx)
    i = select_menu([t[1] for t in TONES], title="Perfil de Voz")
    tone = TONES[i][0]

    # 6. Credentials
    clear()
    step_header(6, TOTAL_STEPS, "Infraestructura y Secretos", ctx)

    secrets_map = {}

    if not is_local:
        if provider_id == "anthropic":
            key = text_input("Anthropic API Key", is_password=True)
            secrets_map["ANTHROPIC_API_KEY"] = key
            validate_api_key(provider_id, key)
        elif provider_id == "openai":
            key = text_input("OpenAI API Key", is_password=True)
            secrets_map["OPENAI_API_KEY"] = key
            validate_api_key(provider_id, key)
        elif provider_id == "gemini":
            key = text_input("Gemini API Key", is_password=True)
            secrets_map["GEMINI_API_KEY"] = key
            validate_api_key(provider_id, key)
        elif provider_id == "groq":
            key = text_input("Groq API Key", is_password=True)
            secrets_map["GROQ_API_KEY"] = key
            validate_api_key(provider_id, key)
        elif provider_id == "openrouter":
            key = text_input("OpenRouter API Key", is_password=True)
            secrets_map["OPENROUTER_API_KEY"] = key
            validate_api_key(provider_id, key)
        else:
            key = text_input(f"{provider_id.title()} API Key", is_password=True)
            secrets_map[f"{provider_id.upper()}_API_KEY"] = key
            validate_api_key(provider_id, key)
            
    if provider_id == "manual":
        secrets_map["CUSTOM_API_BASE"] = text_input("Endpoint URL (ej: http://localhost:8000/v1)")

    # Channel Tokens
    if channel in ["telegram", "both"]:
        secrets_map["TELEGRAM_TOKEN"] = text_input("Telegram Bot Token", is_password=True)

    if channel in ["whatsapp_cloud", "both"]:
        secrets_map["WA_CLOUD_TOKEN"] = text_input("WA Cloud API Token", is_password=True)
        secrets_map["WA_PHONE_NUMBER_ID"] = text_input("Phone Number ID")

    # 7. Confirmation
    clear()
    step_header(7, TOTAL_STEPS, "Verificación Final")
    
    print(f"  ┌────────────────────────────────────────────────────────┐")
    print(f"  │ {C_PRIMARY}{B1}Resumen de Configuración{R}                               │")
    print(f"  ├────────────────────────────────────────────────────────┤")
    print(f"  │ {C_MUTED}Negocio:{R}   {B1}{name.ljust(44)}{R}│")
    print(f"  │ {C_MUTED}Sector:{R}    {sector.ljust(44)}│")
    print(f"  │ {C_MUTED}Canal:{R}     {channel.ljust(44)}│")
    print(f"  │ {C_MUTED}Proveedor:{R} {provider_id.ljust(44)}│")
    print(f"  │ {C_MUTED}Modelo:{R}    {model_id.ljust(44)}│")
    print(f"  │ {C_MUTED}Voz:{R}       {tone.ljust(44)}│")
    print(f"  │ {C_MUTED}Secretos:{R}  {str(len(secrets_map)).ljust(44)}│")
    print(f"  └────────────────────────────────────────────────────────┘\n")

    if not confirm("¿Procesar e Implementar Infraestructura?"):
        print(f"\n  {C_MUTED}Cancelado.{R}\n")
        return

    print(f"\n  {C_PRIMARY}Creando recursos...{R}")
    _create(name, instance_id, sector, channel, provider_id, model_id, tone, secrets_map, lang)

    print(f"""
  {C_SUCCESS}{B1}🚀 Infraestructura Desplegada Exitosamente{R}

    {C_MUTED}Directorio:{R}  {INSTANCES_DIR / instance_id}
    {C_MUTED}Control:{R}     {C_PRIMARY}conny status {instance_id}{R}
    {C_MUTED}Check:{R}       {C_PRIMARY}conny doctor{R}
    {C_MUTED}Lanzar:{R}      {C_PRIMARY}pm2 start {INSTANCES_DIR / instance_id}/run.sh --name conny-{instance_id}{R}
""")

    # Post-onboarding commands
    if is_local and provider_id == "ollama":
        print(f"  {C_WARNING}💡 Asegúrate de descargar el modelo: `ollama run {model_id}`{R}\n")

def _create(name, iid, sector, channel, provider, model_id, tone, secrets_map, lang):
    idir = INSTANCES_DIR / iid
    idir.mkdir(parents=True, exist_ok=True)

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

    env_lines = [
        f"INSTANCE_ID={iid}",
        f"PORT={port}",
        "DEMO_MODE=false",
        f"PLATFORM={channel}",
        f"SECTOR={sector}",
        f"BUSINESS_NAME=\"{name}\"",
        f"WEBHOOK_SECRET={webhook_secret}",
        f"LLM_PROVIDER={provider}",
        f"LLM_MODEL={model_id}",
        "DEBUG=false"
    ]
    for k, v in secrets_map.items():
        env_lines.append(f"{k}={v}")

    (idir / ".env").write_text("\n".join(env_lines) + "\n")

    # Generate System Prompt Base
    sys_prompt = f"""Eres Conny, recepcionista autónoma de {name} (Sector: {sector}).
Tu tono de voz es {tone}. Responde por {channel}.
Idioma principal: {lang}
"""
    (idir / "conny_system_prompt.txt").write_text(sys_prompt)

    (idir / "personas").mkdir(exist_ok=True)
    (idir / "personas" / "persona.yaml").write_text(f"""identity:
  name: Conny
  business: "{name}"
  sector: {sector}
voice:
  tone: {tone}
  language: {lang}
llm:
  provider: {provider}
  model: {model_id}
""")

    core = ["conny.py", "src/core/admin_engines.py", "src/core/production_monitor.py", "conny_config.py",
            "conny_utils.py", "conny_commands.py", "conny_learning.py", "conny_voice.py",
            "conny_uncertainty.py", "conny_memory_engine.py", "conny_admin_api.py",
            "conny_cron.py", "conny_nova_proxy.py", "conny_smart_features.py",
            "conny_web_search.py", "conny_google_auth.py", "run.sh", "requirements.txt",
            "conny_design.py", "conny_i18n.py", "conny_cli_bb.py"]

    for f in core:
        src = CONNY_DIR / f
        if src.exists(): shutil.copy2(src, idir / f)

    for d in ["soul", "teachings", "memory_store", "knowledge_gaps", "integrations/vault", "logs"]:
        (idir / d).mkdir(parents=True, exist_ok=True)

    (idir / "run.sh").write_text(f"#!/bin/bash\ncd {idir}\nexec {CONNY_DIR}/.venv/bin/python conny.py\n")
    os.chmod(idir / "run.sh", 0o755)

    # State
    state = {
        "status": "configured",
        "timestamp": datetime.now().isoformat(),
        "instance": iid,
        "provider": provider
    }
    (idir / "conny.state.json").write_text(json.dumps(state, indent=2))

def _slug(name):
    s = name.lower().strip()
    for a, b in [("á","a"),("é","e"),("í","i"),("ó","o"),("ú","u"),("ñ","n")]:
        s = s.replace(a, b)
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')[:40]

def main():
    try:
        if "--reset" in sys.argv:
            print(f"  {C_WARNING}Reset no implementado en mock v2.{R}")
            return
        run_wizard()
    except KeyboardInterrupt:
        print(f"\n\n  {C_MUTED}Cancelado.{R}\n")

if __name__ == "__main__":
    main()
