"""
ovni_handler.py — Handler exclusivo para el agente técnico OVNI.

OVNI no es una instancia de Bublee ni un bot de recepcionista.
Es el centro de operaciones del ecosistema: crea instancias, diagnostica,
orquesta agentes, y atiende SOLO al administrador (Santiago o un dev autorizado).

Características:
- Solo el admin puede interactuar. Desconocidos reciben silencio.
- Usa LLM con system prompt técnico cargado desde ovni.yaml
- Tiene acceso al estado de todas las instancias del sistema
- Puede ejecutar acciones: listar instancias, revisar logs, activar/desactivar demo
- Sin frases de recepcionista. Sin "Hola soy Bublee". Nunca.
"""
from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import time
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    pass

log = logging.getLogger("bublee.ovni")

# ─── Persona de OVNI ─────────────────────────────────────────────────────────

OVNI_SYSTEM_PROMPT = """\
Eres Ovni, la inteligencia artificial de control y operaciones, mano derecha de Santiago Rubio y el equipo de desarrollo de Bublee.
Tu único interlocutor es el Administrador de Sistemas (Santiago Rubio o desarrolladores autorizados).

MISION:
- Ser el copiloto inteligente del desarrollador: asiste de forma proactiva, brillante y eficiente.
- Eres capaz de orquestar agentes, diagnosticar problemas en profundidad, sugerir optimizaciones, y ejecutar cambios de configuración en las instancias de forma inteligente.
- Tienes total iniciativa. Si ves que algo en el estado del sistema requiere atención, menciónalo y sugiere un plan de acción.

CONTROL DE INSTANCIAS Y AGENTES (COMANDOS ACCIONABLES):
Si el usuario te solicita realizar alguna de las siguientes operaciones de control, debes incluir al final de tu respuesta (en su propia línea) la etiqueta estructurada correspondiente. El sistema la interceptará, la ejecutará en el servidor y le informará al usuario del resultado de la operación:

1. Activar el Modo Demo para una instancia:
   Etiqueta: [CMD:DEMO:<nombre_carpeta_instancia>:ON]
   Ejemplo: [CMD:DEMO:clinica-de-las-americas:ON]

2. Desactivar el Modo Demo para una instancia:
   Etiqueta: [CMD:DEMO:<nombre_carpeta_instancia>:OFF]
   Ejemplo: [CMD:DEMO:clinica-de-las-americas:OFF]

3. Reiniciar una instancia / proceso PM2:
   Etiqueta: [CMD:RESTART:<nombre_carpeta_instancia_o_proceso>]
   Ejemplo: [CMD:RESTART:clinica-de-las-americas]

Por ejemplo, si el usuario te dice: "pon en demo clinica de las americas" o "prende demo de la de las americas", respondes con tu tono habitual y agregas el comando:
"Listo Santiago, de una. Ya estoy activando el modo demo para la clínica de las américas.
[CMD:DEMO:clinica-de-las-americas:ON]"

Si te pide desactivar la demo de "esa instancia" o "la misma", recuerda del historial de chat cuál es la instancia activa y usa su etiqueta:
"Entendido, ya desactivo el modo demo para la clínica de las américas.
[CMD:DEMO:clinica-de-las-americas:OFF]"

TONO Y PERSONALIDAD:
- Profesional, fluido, inteligente y cercano. Hablas de tú a tú como un colega experto.
- Olvídate de respuestas secas o robóticas de consola de comandos. Eres una IA conversacional brillante.
- NO uses frases de recepcionista de clínica o de call center (como "con mucho gusto", "en qué le puedo ayudar", "recepcionista virtual", "soy Bublee la asesora"). Eres el orquestador del ecosistema.

ESTADO DEL SISTEMA (PM2):
{system_state}

HISTORIAL DE CHAT:
{history_txt}
"""

OVNI_FIRST_TURN = "Hola, Santiago. Ovni activo y a tu disposición. ¿Con qué empezamos hoy a potenciar el sistema?"


# ─── Lectura del estado del sistema ──────────────────────────────────────────

def _get_system_state() -> str:
    """Genera un resumen del estado de todas las instancias."""
    lines = []
    try:
        result = subprocess.run(
            ["pm2", "jlist"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            processes = json.loads(result.stdout)
            for proc in processes:
                name = proc.get("name", "?")
                status = proc.get("pm2_env", {}).get("status", "?")
                restarts = proc.get("pm2_env", {}).get("restart_time", 0)
                memory = proc.get("monit", {}).get("memory", 0)
                mem_mb = round(memory / 1024 / 1024, 1) if memory else 0
                lines.append(f"• {name}: {status} | reintentos={restarts} | mem={mem_mb}MB")
    except Exception as e:
        lines.append(f"(no pude leer pm2: {e})")

    # Instancias registradas
    try:
        registry_path = "/home/ubuntu/bublee/instances.registry.json"
        if os.path.exists(registry_path):
            registry = json.loads(open(registry_path).read())
            if isinstance(registry, list):
                instance_names = [i.get("name", "?") for i in registry]
                lines.append(f"Instancias registradas: {', '.join(instance_names)}")
    except Exception:
        pass

    return "\n".join(lines) if lines else "(sin datos de sistema)"


def _build_history_txt(history: List[Dict]) -> str:
    if not history:
        return "(sin historial)"
    lines = []
    for h in history[-6:]:
        role = "Admin" if h.get("role") == "user" else "Ovni"
        content = str(h.get("content", ""))[:300]
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


# ─── Detección de comandos rápidos ───────────────────────────────────────────

def _find_instance_dir(name: str) -> Optional[Tuple[str, str, str]]:
    """
    Busca una instancia que coincida con 'name' en instances/ o agents/.
    Devuelve Tuple (tipo, ruta_absoluta, nombre_carpeta) o None.
    Soporta búsqueda por tokens/palabras clave parciales.
    """
    name_clean = name.strip().lower().replace("bublee-", "")
    # Separar en palabras clave individuales
    search_tokens = [t for t in re.split(r"[-\s_]", name_clean) if t]
    if not search_tokens:
        return None
    
    # Directorios base
    base_dirs = {
        "instance": "/home/ubuntu/bublee/instances",
        "agent": "/home/ubuntu/bublee/agents"
    }
    
    candidates = []
    for kind, base in base_dirs.items():
        if not os.path.exists(base):
            continue
        for folder in os.listdir(base):
            if folder == "_template":
                continue
            folder_path = os.path.join(base, folder)
            if not os.path.isdir(folder_path):
                continue
            
            folder_lower = folder.lower()
            # Match exacto
            if folder_lower == name_clean:
                return (kind, folder_path, folder)
            
            # Match si todos los tokens buscados existen en el nombre del directorio
            if all(token in folder_lower for token in search_tokens):
                candidates.append((kind, folder_path, folder))
                
    if candidates:
        # Ordenar por el que tenga la longitud más parecida al término de búsqueda
        candidates.sort(key=lambda x: abs(len(x[2]) - len(name_clean)))
        return candidates[0]
        
    return None


def _execute_demo_toggle(instance_name: str, is_on: bool) -> str:
    resolved = _find_instance_dir(instance_name)
    if not resolved:
        return f"❌ No encontré ninguna instancia o agente que coincida con '{instance_name}'."
        
    kind, path, folder = resolved
    db_val = "true" if is_on else "false"
    action_word = "activado" if is_on else "desactivado"
    
    # Actualizar .env
    env_path = os.path.join(path, ".env")
    env_updated = False
    if os.path.exists(env_path):
        try:
            env_content = open(env_path, "r", encoding="utf-8").read()
            if "DEMO_MODE=" in env_content:
                new_content = re.sub(r"DEMO_MODE=(true|false|True|False)", f"DEMO_MODE={db_val}", env_content)
            else:
                new_content = env_content + f"\nDEMO_MODE={db_val}\n"
            open(env_path, "w", encoding="utf-8").write(new_content)
            env_updated = True
        except Exception as e:
            log.error(f"[Ovni] Error actualizando .env de {folder}: {e}")
            
    # Actualizar base de datos sqlite si existe bublee.db
    db_path = os.path.join(path, "bublee.db")
    db_updated = False
    if os.path.exists(db_path):
        try:
            import sqlite3
            conn = sqlite3.connect(db_path, timeout=10)
            c = conn.cursor()
            c.execute("CREATE TABLE IF NOT EXISTS system_config (key TEXT PRIMARY KEY, value TEXT, updated_at TEXT)")
            c.execute("INSERT OR REPLACE INTO system_config (key, value, updated_at) VALUES ('demo_mode', ?, datetime('now'))", (db_val,))
            conn.commit()
            conn.close()
            db_updated = True
        except Exception as e:
            log.error(f"[Ovni] Error actualizando DB de {folder}: {e}")
            
    # Reiniciar vía PM2
    pm2_name = f"bublee-{folder}"
    if folder == "ovni":
        pm2_name = "bublee-ovni"
    elif folder == "bublee" or (kind == "agent" and folder == "default"):
        pm2_name = "bublee"
        
    pm2_restarted = False
    try:
        res = subprocess.run(["pm2", "restart", pm2_name, "--update-env"], capture_output=True, text=True, timeout=10)
        if res.returncode == 0:
            pm2_restarted = True
        else:
            res_list = subprocess.run(["pm2", "jlist"], capture_output=True, text=True, timeout=5)
            if res_list.returncode == 0:
                import json
                pm2_jobs = json.loads(res_list.stdout)
                for job in pm2_jobs:
                    if folder in job.get("name", ""):
                        res_retry = subprocess.run(["pm2", "restart", job.get("name"), "--update-env"], capture_output=True, text=True, timeout=10)
                        if res_retry.returncode == 0:
                            pm2_name = job.get("name")
                            pm2_restarted = True
                            break
    except Exception as e:
        log.error(f"[Ovni] Error al reiniciar PM2 para {folder}: {e}")
        
    details = []
    if env_updated:
        details.append(".env actualizado")
    if db_updated:
        details.append("DB actualizada")
    if pm2_restarted:
        details.append(f"proceso PM2 `{pm2_name}` reiniciado")
    else:
        details.append(f"⚠️ no se pudo reiniciar PM2 `{pm2_name}` (hazlo manualmente con 'reinicia {pm2_name}')")
        
    return f"✅ Modo demo {action_word} para la instancia *{folder}*." + " ||| " + ", ".join(details)


def _execute_restart(instance_name: str) -> str:
    resolved = _find_instance_dir(instance_name)
    if not resolved:
        pm2_name = instance_name
    else:
        kind, path, folder = resolved
        pm2_name = f"bublee-{folder}"
        if folder == "ovni":
            pm2_name = "bublee-ovni"
        elif folder == "bublee" or (kind == "agent" and folder == "default"):
            pm2_name = "bublee"

    try:
        result = subprocess.run(
            ["pm2", "restart", pm2_name, "--update-env"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return f"✅ Instancia `{pm2_name}` reiniciada correctamente."
        else:
            return f"❌ Error al reiniciar `{pm2_name}`: {result.stderr[:200]}"
    except Exception as e:
        return f"❌ Error al reiniciar `{pm2_name}`: {e}"


def _detect_quick_command(text: str) -> Optional[List[str]]:
    """
    Intercepta comandos técnicos comunes antes de ir al LLM.
    Devuelve lista de bubbles o None si no hay comando.
    """
    t = text.strip().lower()

    if t in ("/status", "status", "estado", "qué pasa", "que pasa"):
        state = _get_system_state()
        return [f"Estado del sistema:\n{state}"]

    if t in ("/help", "help", "ayuda", "qué puedes hacer", "que puedes hacer"):
        return [
            "Comandos disponibles:",
            "/status — estado de todos los procesos\n"
            "demo <instancia> on|off — activar/desactivar demo\n"
            "logs <instancia> — últimas 20 líneas de log\n"
            "reinicia <instancia> — reiniciar proceso PM2\n"
            "instancias — listar instancias registradas\n"
            "nueva instancia — iniciar flujo de creación"
        ]

    # Comando demo <instancia> on|off estricto (CLI)
    demo_cli_match = re.match(r"^demo\s+([a-zA-Z0-9_-]+)\s+(on|off)$", t)
    if demo_cli_match:
        inst = demo_cli_match.group(1).strip()
        is_on = demo_cli_match.group(2) == "on"
        res = _execute_demo_toggle(inst, is_on)
        return [b.strip() for b in res.split("|||") if b.strip()]

    # Reinicio de instancia estricto (CLI)
    restart_match = re.match(r"^reinicia?\s+([a-zA-Z0-9_-]+)$", t)
    if restart_match:
        inst = restart_match.group(1).strip()
        res = _execute_restart(inst)
        return [res]

    # Logs de instancia estricto (CLI)
    logs_match = re.match(r"^logs?\s+([a-zA-Z0-9_-]+)$", t)
    if logs_match:
        inst = logs_match.group(1).strip()
        try:
            log_path = f"/home/ubuntu/bublee/instances/{inst}/logs/bublee.log"
            if not os.path.exists(log_path):
                log_path = f"/home/ubuntu/bublee/agents/{inst}/logs/bublee.log"
            if os.path.exists(log_path):
                result = subprocess.run(
                    ["tail", "-n", "20", log_path],
                    capture_output=True, text=True, timeout=5
                )
                return [f"Últimas líneas de {inst}:\n```\n{result.stdout[-800:]}\n```"]
            else:
                return [f"No encontré logs de '{inst}'"]
        except Exception as e:
            return [f"Error leyendo logs: {e}"]

    return None


# ─── Handler principal ───────────────────────────────────────────────────────

class OvniHandler:
    """
    Handler exclusivo para el agente Ovni.
    Solo acepta mensajes del admin registrado.
    Usa LLM con identidad técnica de Ovni.
    """

    def __init__(self, bublee_instance):
        self.bublee = bublee_instance

    async def handle(
        self,
        chat_id: str,
        text: str,
        clinic: Dict,
        admin_ids: List[str],
        history: List[Dict],
        is_audio: bool = False,
        attachments: Optional[List] = None,
    ) -> List[str]:
        """
        Procesa un mensaje para OVNI.
        Solo el admin puede interactuar. Desconocidos → silencio.
        """
        from bublee import llm_engine

        # ── Solo admin puede escribir a OVNI ──────────────────────────────
        # Normalizar comparación: chat_id puede venir como "6908159885" o 6908159885
        _chat_str = str(chat_id).strip()
        _admin_strs = {str(a).strip() for a in admin_ids}
        log.info(f"[Ovni] Mensaje de {_chat_str} | admins={_admin_strs}")
        if _chat_str not in _admin_strs:
            log.info(f"[Ovni] {_chat_str} no es admin — silencio")
            return []  # Silencio total — OVNI no atiende desconocidos

        # ── Primer turno ──────────────────────────────────────────────────
        is_first = not any(h.get("role") == "assistant" for h in history)
        if is_first and not text.strip():
            return [OVNI_FIRST_TURN]

        # ── Comandos rápidos (sin LLM) ────────────────────────────────────
        quick = _detect_quick_command(text)
        if quick:
            return quick

        # ── LLM con identidad de OVNI ─────────────────────────────────────
        if not llm_engine:
            return ["LLM no disponible — revisa los logs del sistema"]

        system_state = _get_system_state()
        history_txt = _build_history_txt(history)

        system_prompt = OVNI_SYSTEM_PROMPT.format(
            system_state=system_state,
            history_txt=history_txt,
        )

        messages = [
            {"role": "system", "content": system_prompt},
        ]

        # Si es primer turno, agregar instrucción de saludo técnico
        if is_first:
            messages.append({
                "role": "system",
                "content": (
                    f"El admin acaba de escribirte por primera vez en esta sesión. "
                    f"Preséntate brevemente como Ovni. "
                    f"NO uses frases de recepcionista. "
                    f"Respuesta máxima: 1-2 frases cortas."
                )
            })

        # Historial de conversación
        for h in history[-8:]:
            messages.append({"role": h["role"], "content": h["content"][:400]})
        messages.append({"role": "user", "content": text})

        try:
            raw, _ = await llm_engine.complete(
                messages,
                model_tier="fast",
                temperature=0.4,   # Técnico = bajo en temperatura
                max_tokens=500,
                use_cache=False,
            )
        except Exception as e:
            log.error(f"[Ovni] LLM error: {e}")
            return [f"Error LLM: {e}"]

        if not raw:
            return []  # LLM sin respuesta → silencio

        # ── Post-process: eliminar frases de recepcionista e identidad equivocada ────────────────
        raw = re.sub(r"(?i)\bbublee\b", "Ovni", raw)
        
        FORBIDDEN = (
            "recepcionista virtual", "recepcionista ejecutiva", "asesora de servicio",
            "servicio al cliente", "en qué puedo ayudar", "en qué te puedo ayudar",
            "con mucho gusto", "fue un placer", "soy tu asistente", "tu asistente virtual",
            "recepcionista de"
        )
        raw_lower = raw.lower()
        for f in FORBIDDEN:
            if f in raw_lower:
                log.warning(f"[Ovni] LLM generó frase prohibida: '{f}' — sanitizando respuesta")
                raw = "Ovni. Ejecución de comando técnica completada."
                break

        # Buscar comandos estructurados: [CMD:DEMO:instance:ON/OFF] o [CMD:RESTART:instance]
        cmd_matches = re.findall(r"\[CMD:(DEMO|RESTART):([^:\]]+)(?::(ON|OFF))?\]", raw)
        
        # Eliminar las etiquetas del texto de respuesta para no mostrarlas en bruto al usuario
        raw_clean = re.sub(r"\[CMD:(DEMO|RESTART):([^:\]]+)(?::(ON|OFF))?\]", "", raw).strip()

        # Separar en burbujas por |||
        bubbles = [b.strip() for b in raw_clean.split("|||") if b.strip()]
        if not bubbles and raw_clean:
            bubbles = [raw_clean]

        # Ejecutar los comandos y añadir burbujas de estado
        for cmd_type, inst, option in cmd_matches:
            inst = inst.strip()
            if cmd_type == "DEMO":
                is_on = option == "ON"
                status_msg = _execute_demo_toggle(inst, is_on)
                # La respuesta de _execute_demo_toggle puede contener ||| para separar burbujas
                for sub_bubble in status_msg.split("|||"):
                    if sub_bubble.strip():
                        bubbles.append(sub_bubble.strip())
            elif cmd_type == "RESTART":
                status_msg = _execute_restart(inst)
                bubbles.append(status_msg)

        return bubbles if bubbles else [raw.strip()]
