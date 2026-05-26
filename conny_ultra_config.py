#!/usr/bin/env python3
"""CONNY ULTRA CONFIG v9.7.0 — interactive runtime control panel."""
from __future__ import annotations

import asyncio
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

from conny_runtime_ops import (
    detect_tunnel_processes,
    find_pm2_processes,
    health_payload,
    instance_runtime_info,
    port_is_open,
    python_candidates,
    resolve_python,
    rewrite_tunnel_command_port,
    telegram_webhook_info,
    write_env_value,
)
from conny_tui_select import (
    BOLD,
    CYAN,
    DIM,
    GREEN,
    MAGENTA,
    RESET,
    WHITE,
    confirm,
    select_menu,
    text_input,
)


def clear_screen() -> None:
    print("\033[H\033[J", end="")


def wait_for_enter() -> None:
    input(f"\n{DIM}[Presiona Enter para continuar]{RESET}")


def _mask(value: str) -> str:
    value = str(value or "").strip()
    if not value:
        return "vacía"
    if len(value) <= 8:
        return "*" * len(value)
    return value[:4] + "…" + value[-4:]


def _load_state(instance_name: str) -> Dict[str, Any]:
    info = instance_runtime_info(instance_name)
    health = health_payload(info["port"]) or {}
    pm2_rows = find_pm2_processes(info["name"])
    python = resolve_python(info["name"])
    webhook = telegram_webhook_info(info["telegram_token"]) if info["platform"] == "telegram" else {}
    tunnels = detect_tunnel_processes()
    return {
        "info": info,
        "health": health,
        "pm2": pm2_rows,
        "python": python,
        "webhook": webhook,
        "tunnels": tunnels,
    }


def _render_header(instance_name: str, subtitle: str) -> None:
    clear_screen()
    print(f"┌{'─'*68}┐")
    print(f"│{BOLD}                    CONNY ULTRA CONFIG v9.7.0                    {RESET}│")
    print(f"├{'─'*68}┤")
    print(f"│ {WHITE}{BOLD}Instancia:{RESET} {instance_name or 'base':<57}│")
    print(f"│ {CYAN}{subtitle:<66}{RESET}│")
    print(f"└{'─'*68}┘")
    print()


def _provider_env_keys() -> List[Tuple[str, str]]:
    return [
        ("GEMINI_API_KEY", "Gemini 1"),
        ("GEMINI_API_KEY_2", "Gemini 2"),
        ("GEMINI_API_KEY_3", "Gemini 3"),
        ("GEMINI_API_KEY_4", "Gemini 4"),
        ("GEMINI_API_KEY_5", "Gemini 5"),
        ("GEMINI_API_KEY_6", "Gemini 6"),
        ("GEMINI_API_KEY_7", "Gemini 7"),
        ("OPENAI_API_KEY", "OpenAI"),
        ("OPENROUTER_API_KEY", "OpenRouter"),
        ("GROQ_API_KEY", "Groq"),
        ("ANTHROPIC_API_KEY", "Anthropic"),
        ("BRAVE_API_KEY", "Brave Search"),
        ("APIFY_API_KEY", "Apify"),
        ("SERP_API_KEY", "SerpAPI"),
    ]


def _test_provider(provider_key: str, secret: str) -> Tuple[bool, str]:
    provider_key = provider_key.upper()
    secret = str(secret or "").strip()
    if not secret:
        return False, "sin API key"
    try:
        import httpx
    except Exception:
        return False, "httpx no disponible"
    try:
        with httpx.Client(timeout=12.0) as client:
            if provider_key.startswith("GEMINI"):
                response = client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={secret}",
                    json={"contents": [{"parts": [{"text": "ping"}]}]},
                )
            elif provider_key == "OPENAI_API_KEY":
                response = client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {secret}"},
                )
            elif provider_key == "OPENROUTER_API_KEY":
                response = client.get(
                    "https://openrouter.ai/api/v1/models",
                    headers={"Authorization": f"Bearer {secret}"},
                )
            elif provider_key == "GROQ_API_KEY":
                response = client.get(
                    "https://api.groq.com/openai/v1/models",
                    headers={"Authorization": f"Bearer {secret}"},
                )
            elif provider_key == "ANTHROPIC_API_KEY":
                response = client.get(
                    "https://api.anthropic.com/v1/models",
                    headers={"x-api-key": secret, "anthropic-version": "2023-06-01"},
                )
            elif provider_key == "BRAVE_API_KEY":
                response = client.get(
                    "https://api.search.brave.com/res/v1/web/search",
                    params={"q": "Conny AI"},
                    headers={"X-Subscription-Token": secret},
                )
            elif provider_key == "APIFY_API_KEY":
                response = client.get(
                    "https://api.apify.com/v2/users/me",
                    params={"token": secret},
                )
            elif provider_key == "SERP_API_KEY":
                response = client.get(
                    "https://serpapi.com/account",
                    params={"api_key": secret},
                )
            else:
                return False, "proveedor no soportado"
    except Exception as exc:
        return False, str(exc)[:90]
    if response.status_code < 300:
        return True, f"HTTP {response.status_code}"
    return False, f"HTTP {response.status_code}"


def _sync_telegram_webhook(state: Dict[str, Any]) -> Tuple[bool, str]:
    info = state["info"]
    token = info["telegram_token"]
    base_url = info["base_url"]
    secret = info["webhook_secret"]
    if not token or not base_url or not secret:
        return False, "faltan TELEGRAM_TOKEN, BASE_URL o WEBHOOK_SECRET"
    target_url = f"{base_url.rstrip('/')}/webhook/{secret}"
    try:
        import httpx
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                f"https://api.telegram.org/bot{token}/setWebhook",
                json={"url": target_url},
            )
        payload = response.json()
        if response.status_code == 200 and payload.get("ok"):
            return True, target_url
        return False, payload.get("description", f"HTTP {response.status_code}")
    except Exception as exc:
        return False, str(exc)[:90]


def _retarget_tunnels(target_port: int, tunnels: List[Dict[str, Any]]) -> Tuple[bool, str]:
    changed = 0
    for tunnel in tunnels:
        current_cmd = str(tunnel.get("command", "")).strip()
        new_cmd = rewrite_tunnel_command_port(current_cmd, target_port)
        if not current_cmd or new_cmd == current_cmd:
            continue
        try:
            subprocess.run(["kill", str(tunnel["pid"])], capture_output=True, check=False)
            subprocess.Popen(
                ["bash", "-lc", f"nohup {new_cmd} >/tmp/conny-tunnel-{tunnel['pid']}.log 2>&1 &"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            changed += 1
        except Exception:
            continue
    if changed:
        return True, f"{changed} túnel(es) reorientados a :{target_port}"
    return False, "no encontré túneles compatibles para reorientar"


def module_network(instance_name: str) -> None:
    state = _load_state(instance_name)
    info = state["info"]
    pm2_rows = state["pm2"]
    tunnels = state["tunnels"]
    port = info["port"]
    _render_header(instance_name or "base", "NETWORK MANAGEMENT")
    pm2_status = pm2_rows[0].get("pm2_env", {}).get("status", "offline") if pm2_rows else "not registered"
    print(f"{GREEN}Puerto local esperado:{RESET} {port}")
    print(f"{GREEN}Escucha en localhost:{RESET} {'sí' if port_is_open(port) else 'no'}")
    print(f"{GREEN}Proceso PM2:{RESET} {info['pm2_name']} ({pm2_status})")
    print(f"{GREEN}Túneles detectados:{RESET}")
    if tunnels:
        for tunnel in tunnels:
            ports = ", ".join(str(p) for p in tunnel.get("ports", [])) or "sin puerto parseado"
            print(f"  {DIM}pid={tunnel['pid']} ports={ports} :: {tunnel['command'][:100]}{RESET}")
    else:
        print(f"  {DIM}ninguno detectado{RESET}")

    options = [
        "Cambiar puerto de la instancia",
        "Reorientar túneles al puerto actual",
        "Volver",
    ]
    choice = select_menu(options, title="Acción de red")
    if choice == 0:
        new_port = text_input("Nuevo puerto", default=str(port))
        if new_port.isdigit():
            write_env_value(info["env_path"], "PORT", new_port)
            meta_path = Path(info["root"]) / "instance.json"
            if meta_path.exists():
                try:
                    meta = json.loads(meta_path.read_text(encoding="utf-8"))
                    meta["port"] = int(new_port)
                    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
                except Exception:
                    pass
            print(f"\n{GREEN}✓ Puerto actualizado a {new_port}. Reinicia la instancia para aplicarlo.{RESET}")
    elif choice == 1:
        ok, msg = _retarget_tunnels(port, tunnels)
        tone = GREEN if ok else MAGENTA
        print(f"\n{tone}{msg}{RESET}")
    wait_for_enter()


def module_models(instance_name: str) -> None:
    state = _load_state(instance_name)
    info = state["info"]
    env = info["env"]
    _render_header(instance_name or "base", "MODELS & LLM PROVIDERS")
    print(f"{GREEN}Modelos activos:{RESET}")
    print(f"  reasoning: {env.get('LLM_REASONING', 'google/gemini-2.5-pro')}")
    print(f"  fast:      {env.get('LLM_FAST', 'google/gemini-2.5-flash')}")
    print(f"  lite:      {env.get('LLM_LITE', 'google/gemini-2.5-flash-lite')}")
    print()
    for key, label in _provider_env_keys():
        print(f"  {label:<14} {DIM}{_mask(env.get(key, ''))}{RESET}")
    print()

    options = [
        "Editar API key",
        "Probar API key",
        "Cambiar modelo por tier",
        "Volver",
    ]
    choice = select_menu(options, title="Acción de modelos")
    if choice == 0:
        idx = select_menu([label for _, label in _provider_env_keys()], title="¿Cuál key quieres editar?")
        key, label = _provider_env_keys()[idx]
        current = env.get(key, "")
        new_value = text_input(f"{label} API key", default=current, is_password=bool(current), required=False)
        write_env_value(info["env_path"], key, new_value)
        print(f"\n{GREEN}✓ {label} actualizada{RESET}")
    elif choice == 1:
        idx = select_menu([label for _, label in _provider_env_keys()], title="¿Cuál key quieres probar?")
        key, label = _provider_env_keys()[idx]
        ok, msg = _test_provider(key, env.get(key, ""))
        print(f"\n{GREEN if ok else MAGENTA}{label}: {msg}{RESET}")
    elif choice == 2:
        tier = select_menu(["LLM_REASONING", "LLM_FAST", "LLM_LITE"], title="Tier")
        keys = ["LLM_REASONING", "LLM_FAST", "LLM_LITE"]
        selected = keys[tier]
        current = env.get(selected, "")
        new_value = text_input(f"{selected}", default=current or "google/gemini-2.5-flash")
        write_env_value(info["env_path"], selected, new_value)
        print(f"\n{GREEN}✓ {selected} actualizado{RESET}")
    wait_for_enter()


def module_gateway(instance_name: str) -> None:
    state = _load_state(instance_name)
    info = state["info"]
    webhook = state["webhook"]
    _render_header(instance_name or "base", "GATEWAY & WEBHOOKS")
    expected = f"{info['base_url'].rstrip('/')}/webhook/{info['webhook_secret']}" if info["base_url"] and info["webhook_secret"] else "incompleto"
    print(f"{GREEN}BASE_URL:{RESET} {info['base_url'] or 'vacío'}")
    print(f"{GREEN}Webhook esperado:{RESET} {expected}")
    print(f"{GREEN}Webhook Telegram actual:{RESET} {webhook.get('url', 'sin registrar')}")
    print(f"{GREEN}Pendientes:{RESET} {webhook.get('pending_update_count', 0)}")
    if webhook.get("last_error_message"):
        print(f"{MAGENTA}Último error:{RESET} {webhook['last_error_message']}")
    print()
    choice = select_menu(
        ["Auto-sincronizar webhook", "Editar BASE_URL", "Volver"],
        title="Acción de gateway",
    )
    if choice == 0:
        ok, msg = _sync_telegram_webhook(state)
        print(f"\n{GREEN if ok else MAGENTA}{msg}{RESET}")
    elif choice == 1:
        new_url = text_input("Nueva BASE_URL", default=info["base_url"], required=False)
        write_env_value(info["env_path"], "BASE_URL", new_url)
        print(f"\n{GREEN}✓ BASE_URL actualizada{RESET}")
    wait_for_enter()


def module_environment(instance_name: str) -> None:
    state = _load_state(instance_name)
    info = state["info"]
    _render_header(instance_name or "base", "ENVIRONMENT & PATH TUNING")
    print(f"{GREEN}Intérprete activo detectado:{RESET} {state['python']['path'] if state['python'] else 'ninguno'}")
    print(f"{GREEN}Candidatos:{RESET}")
    candidates = python_candidates(info["name"])
    for candidate in candidates:
        marker = "✓" if candidate["exists"] else "·"
        print(f"  {marker} {candidate['source']:<18} {DIM}{candidate['path']}{RESET}")
    print()
    choice = select_menu(
        ["Fijar intérprete manual para esta instancia", "Verificar run.sh", "Volver"],
        title="Acción de entorno",
    )
    if choice == 0:
        valid = [c for c in candidates if c["exists"]]
        if not valid:
            print(f"\n{MAGENTA}No encontré candidatos válidos.{RESET}")
        else:
            idx = select_menu([f"{c['source']} :: {c['path']}" for c in valid], title="Selecciona intérprete")
            selected = valid[idx]
            write_env_value(info["env_path"], "CONNY_PYTHON_BIN", selected["path"])
            print(f"\n{GREEN}✓ CONNY_PYTHON_BIN fijado a {selected['path']}{RESET}")
    elif choice == 1:
        run_path = Path(info["root"]) / "run.sh"
        print(f"\n{GREEN}{run_path}{RESET}")
        print(run_path.read_text(encoding="utf-8", errors="replace")[:2000] if run_path.exists() else "run.sh no existe")
    wait_for_enter()


def module_doctor(instance_name: str) -> None:
    _render_header(instance_name or "base", "ADVANCED SYSTEM DOCTOR")
    print(f"{MAGENTA}Iniciando Self-Healing...{RESET}\n")
    try:
        import conny_doctor
        doctor = conny_doctor.ConnyDoctor(instance_name or "base")
        asyncio.run(doctor.run_self_healing())
    except Exception as exc:
        print(f"{MAGENTA}Error ejecutando doctor: {exc}{RESET}")
    wait_for_enter()


def run_ultra_config(instance_name: str = "") -> None:
    active = (instance_name or "base").strip()
    while True:
        _render_header(active, "CONTROL TOTAL DEL USUARIO")
        state = _load_state(active)
        port = state["info"]["port"]
        health = "online" if state["health"].get("status") == "online" else "offline"
        print(f"{GREEN}Estado rápido:{RESET} puerto :{port} · health {health} · pm2 {state['info']['pm2_name']}")
        print()
        options = [
            "NETWORK MANAGEMENT",
            "MODELS & LLM PROVIDERS",
            "GATEWAY & WEBHOOKS",
            "ENVIRONMENT & PATH TUNING",
            "ADVANCED SYSTEM DOCTOR",
            "SALIR",
        ]
        descs = [
            "Puertos locales, PM2 y túneles públicos",
            "API keys, pruebas y tiering de modelos",
            "Webhook esperado, URL activa y resincronización",
            "Intérprete Python, overrides y run.sh",
            "Autorreparación de runtime, deps y procesos",
            "Cerrar configuración",
        ]
        choice = select_menu(options, title="Conny config", descriptions=descs)
        if choice == 0:
            module_network(active)
        elif choice == 1:
            module_models(active)
        elif choice == 2:
            module_gateway(active)
        elif choice == 3:
            module_environment(active)
        elif choice == 4:
            module_doctor(active)
        else:
            clear_screen()
            return


if __name__ == "__main__":
    selected = sys.argv[1] if len(sys.argv) > 1 else ""
    run_ultra_config(selected)
