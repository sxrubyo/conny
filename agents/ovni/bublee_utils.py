from __future__ import annotations
import hashlib
import json
import logging
import secrets
import re
from typing import Any, Callable, Dict, List, Optional

log = logging.getLogger("bublee.utils")

ACTIVATION_PREFIX = "ACTV-"
INVITE_PREFIX = "JINV-"

def is_activation_token(text: str) -> bool:
    """Detecta si el mensaje es un token de activacion."""
    t = text.strip().upper()
    return (t.startswith(ACTIVATION_PREFIX) or t.startswith("ADMN-")) and len(t) >= 30

def is_admin_activation_token(text: str) -> bool:
    """Detecta si el mensaje es un token de activacion de administrador."""
    t = text.strip().upper()
    return t.startswith("ADMN-") and len(t) >= 30

def is_invite_token(text: str) -> bool:
    """Detecta si el mensaje es un token de invitacion."""
    t = text.strip().upper()
    return t.startswith(INVITE_PREFIX) and len(t) >= 15

def generate_activation_token(label: str) -> str:
    """
    Genera un token de activacion de alta entropia.
    Formato: ACTV-[label_sanitizado]-[32_chars_hex]
    """
    import string
    sanitized = re.sub(r'[^a-zA-Z0-9]', '', label.lower())[:10]
    if not sanitized:
        sanitized = "generic"
    entropy = secrets.token_hex(16).upper()
    return f"{ACTIVATION_PREFIX}{sanitized.upper()}-{entropy}"

def generate_admin_activation_token(label: str) -> str:
    """
    Genera un token de activacion de administrador de alta entropia.
    Formato: ADMN-[label_sanitizado]-[32_chars_hex]
    """
    import string
    sanitized = re.sub(r'[^a-zA-Z0-9]', '', label.lower())[:10]
    if not sanitized:
        sanitized = "generic"
    entropy = secrets.token_hex(16).upper()
    return f"ADMN-{sanitized.upper()}-{entropy}"

def hash_password(password: str) -> str:
    """Hash de contrasena con PBKDF2 + salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        260_000
    ).hex()
    return f"{salt}:{key}"

def verify_password(password: str, stored_hash: str) -> bool:
    """Verifica contrasena contra hash almacenado."""
    try:
        salt, key = stored_hash.split(":", 1)
        test = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            260_000
        ).hex()
        return test == key
    except Exception:
        return False

def _parse_admin_ids(raw) -> list:
    """Parsea admin_chat_ids de forma segura."""
    if not raw: return []
    if isinstance(raw, list): return [str(i) for i in raw]
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
            if isinstance(data, list): return [str(i) for i in data]
            return [str(data)]
        except Exception:
            return [i.strip() for i in raw.split(",") if i.strip()]
    return []

def extract_model_request_from_text(text: str) -> Optional[str]:
    """Extrae solicitud de cambio de modelo del lenguaje natural."""
    t = text.lower().strip()
    if not t.startswith("/modelo"):
        if "cambia el modelo a" in t: return t.split("cambia el modelo a")[-1].strip()
        if "usa el modelo" in t: return t.split("usa el modelo")[-1].strip()
        return None
    parts = t.split()
    return parts[1] if len(parts) > 1 else "reset"

def normalize_model_arg(arg: str) -> str:
    """Normaliza el nombre del modelo solicitado."""
    m = arg.lower().strip()
    if m in ("flash", "gemini"): return "google/gemini-2.5-flash"
    if m in ("pro", "sonnet"): return "anthropic/claude-3-5-sonnet"
    if m in ("fast", "haiku"): return "anthropic/claude-3-haiku"
    return m


# ══════════════════════════════════════════════════════════════════════════
# NUEVO — Detección robusta de afirmación/negación en español coloquial
# ══════════════════════════════════════════════════════════════════════════
#
# Por qué existe: comparaciones como `text.lower().strip() in ["si","ok","claro"]`
# fallan con variantes muy comunes en WhatsApp colombiano ("dale", "de una",
# "claro que si", "sisas", etc). Eso causa que un flujo de confirmación
# (ej. onboarding, activación de cuenta) interprete un "sí" real como si
# fuera una respuesta distinta. Estas funciones reemplazan ese tipo de
# comparación exacta en cualquier punto del código que necesite leer sí/no.

_ACCENT_MAP = str.maketrans({
    "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ü": "u", "ñ": "n",
})


def _normalize_yn(text: str) -> str:
    t = (text or "").strip().lower().translate(_ACCENT_MAP)
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


# Palabras cortas AMBIGUAS: "si" y "no" también son conjunción/negación
# dentro de oraciones más largas ("si tienes tiempo...", "no vas a poder...").
# Por eso solo cuentan cuando son el mensaje COMPLETO, no como substring.
_AMBIGUOUS_YES = {"si", "sisas", "siii", "ok", "oki", "va", "sip", "simon"}
_AMBIGUOUS_NO = {"no", "nel", "nop", "nope"}

# Frases NO ambiguas: seguras para detectar aunque vengan acompañadas
# de otras palabras ("dale pues", "claro que si", "de una vez entonces").
_UNAMBIGUOUS_YES = {
    "dale", "claro", "obvio", "de una", "de una vez", "correcto",
    "asi es", "eso es", "eso mismo", "exacto", "exactamente", "vale",
    "listo", "perfecto", "bacano", "hagale", "confirmo", "confirmado",
    "afirmativo", "positivo", "yes", "yep", "yeah", "de acuerdo",
    "estoy de acuerdo", "me parece bien", "asi mismo",
}
_UNAMBIGUOUS_NO = {
    "negativo", "para nada", "que va", "ni de riesgos", "no gracias",
    "no quiero", "cancela", "cancelar", "olvidalo", "mejor no",
    "ni de vainas", "nada que ver",
}


def _contains_phrase(t: str, phrases) -> bool:
    for p in phrases:
        if re.search(r"\b" + re.escape(p) + r"\b", t):
            return True
    return False


def is_affirmative(text: str) -> bool:
    """
    True si el texto es una afirmación clara en español coloquial/colombiano,
    con o sin tildes ("si", "dale", "de una", "claro que si", "sisas"...).
    Diseñada para leer respuestas CORTAS a una pregunta de confirmación
    explícita — no para detectar "sí" perdido dentro de una oración larga.
    """
    t = _normalize_yn(text)
    if not t:
        return False
    if t in _AMBIGUOUS_YES:
        return True
    return _contains_phrase(t, _UNAMBIGUOUS_YES)


def is_negative(text: str) -> bool:
    """True si el texto es una negación clara en español coloquial/colombiano."""
    t = _normalize_yn(text)
    if not t:
        return False
    if t in _AMBIGUOUS_NO:
        return True
    return _contains_phrase(t, _UNAMBIGUOUS_NO)


def get_key_cascade(env: Dict[str, str], base_name: str, max_keys: int = 20) -> List[str]:
    """
    Devuelve todas las keys disponibles de una cascada tipo KEY, KEY_2, KEY_3...
    (el patrón que ya usa clinica.env para GEMINI_API_KEY y APIFY_API_KEY).

    Uso: get_key_cascade(os.environ, "GEMINI_API_KEY") -> ["key1", "key2", ...]
    Sirve para rotar automáticamente cuando una key pega rate-limit.
    """
    keys: List[str] = []
    base = env.get(base_name)
    if base:
        keys.append(base)
    i = 2
    while i <= max_keys:
        k = env.get(f"{base_name}_{i}")
        if k:
            keys.append(k)
        i += 1
    return keys


# ══════════════════════════════════════════════════════════════════════════
# NUEVO — "Nunca fallback al cliente. Si la IA no responde, se avisa al dueño"
# ══════════════════════════════════════════════════════════════════════════
#
# Reemplaza el patrón que existía en varios lugares del código:
#     _fallbacks = ["perdona, me perdí un momento...", ...]
#     return [_r.choice(_fallbacks)]
# Ese texto es exactamente lo que no se quiere: una respuesta genérica y
# repetida que delata que el bot se rompió. La regla ahora es: si de verdad
# no hay ninguna respuesta real de IA disponible (se agotaron reintentos y
# cascada de proveedores), al cliente/paciente NO se le manda nada — se le
# avisa DE INMEDIATO al dueño vinculado (admin_chat_ids, el mismo mecanismo
# de los tokens de activación) para que entre en persona. Es preferible un
# silencio breve seguido de un humano real, a un mensaje falso repetido.

async def notify_owner_of_ai_failure(
    send_fn: Callable[[str, str], Any],
    admin_ids: List[str],
    chat_id: str,
    last_message: str,
    context: str = "paciente",
) -> bool:
    """
    Avisa a todos los admins vinculados que la IA no pudo generar ninguna
    respuesta para este chat. No le manda nada al remitente original —
    eso queda en silencio a propósito, en vez de un texto genérico.

    Args:
        send_fn: función async(chat_id, texto) para enviar — normalmente
                  bublee._send_message, igual que en notify_admin_availability_request.
        admin_ids: chat_ids de los admins/dueños vinculados a esta instancia.
        chat_id: quién le escribió a Bublee y se quedó sin respuesta.
        last_message: su último mensaje, para que el dueño tenga contexto.
        context: "paciente" o "prospecto (demo)" — para que el dueño sepa
                  qué tan urgente es.

    Returns:
        True si se pudo avisar al menos a un admin, False si no había
        ninguno vinculado (en ese caso queda solo en el log — es una señal
        de que esta instancia no tiene admin_chat_ids configurado, lo cual
        es un problema aparte que vale la pena resolver).
    """
    if not admin_ids:
        log.error(
            f"[ai_failure] la IA no pudo responderle a {chat_id} ({context}) y "
            f"NO hay ningún admin vinculado para avisar — nadie se entera de esto."
        )
        return False

    alert = (
        f"⚠️ Bublee no pudo generarle ninguna respuesta a un {context} — "
        f"no le mandé nada (así lo configuraste, nunca un mensaje genérico).\n\n"
        f"Chat: {chat_id}\n"
        f"Su último mensaje: \"{(last_message or '').strip()[:300]}\"\n\n"
        f"Escríbele directo en cuanto puedas."
    )
    notified = 0
    for admin_id in admin_ids:
        try:
            await send_fn(admin_id, alert)
            notified += 1
        except Exception as e:
            log.error(f"[ai_failure] no pude avisarle al admin {admin_id}: {e}")

    if notified == 0:
        log.error(f"[ai_failure] había {len(admin_ids)} admin(es) vinculados pero no le pude avisar a NINGUNO")
    return notified > 0
