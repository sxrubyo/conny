"""
src/domain/prompts/prospect_pitch.py
════════════════════════════════════════════════════════════════════════════════
PITCH INTELIGENTE — Black One / Conny v1.0
════════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

log = logging.getLogger("conny.pitch_upgrade")

# ════════════════════════════════════════════════════════════════════════════════
# 1. IDENTIDAD CORRECTA
# ════════════════════════════════════════════════════════════════════════════════

CREATOR_NAME   = "Black One"
CREATOR_DESC   = "empresa de software y gobernanza de agentes de IA"
CREATOR_HUMAN  = "Santiago Rubio"
CREATOR_TEL    = "3124348669"

CREATOR_LINE = (
    f"me creó {CREATOR_NAME}, una {CREATOR_DESC}"
    f" ||| la fundó {CREATOR_HUMAN} — si quieres esto para tu negocio, escríbele al {CREATOR_TEL}"
)

# ════════════════════════════════════════════════════════════════════════════════
# 2. DETECCIÓN DE MODO PROSPECTO
# ════════════════════════════════════════════════════════════════════════════════

_PROSPECT_SIGNALS = [
    "me mandaron", "me enviaron", "me pasaron", "me dieron tu número",
    "me dieron este número", "me recomendaron",
    "qué haces", "que haces", "para qué sirves", "para que sirves",
    "qué eres", "que eres", "qué harías", "que harias", "qué harías por",
    "que harias por", "que harias en", "qué harías en",
    "qué puedes hacer", "que puedes hacer",
    "cuánto cuestas", "cuanto cuestas", "cuánto cobras", "cuanto cobras",
    "cuánto vale", "cuanto vale", "cuál es tu precio", "cual es tu precio",
    "cuánto me cobran", "cuanto me cobran", "planes", "tarifas",
    "cómo funciona", "como funciona", "quiero ver", "quiero entender",
    "explícame", "explicame", "no entiendo qué eres", "no entiendo que eres",
    "no sé qué es esto", "no se que es esto",
    "gracias pero", "no me interesa que actues",
    "no me interesa que actúes", "que harias en mi clinica",
    "qué harías en mi", "que harias en mi",
]

_CONFUSION_LOOP_SIGNALS = [
    "no entiendo", "no sé", "no se", "gracias", "me voy", "adios", "adiós",
    "hasta luego", "no era lo que", "error", "equivocado", "equivocada",
]


def _strip_accents(text: str) -> str:
    """Normaliza vocales con tilde para comparación sin falsos negativos."""
    t = str.maketrans("áéíóúÁÉÍÓÚ", "aeiouAEIOU")
    return text.translate(t)

_PROSPECT_SIGNALS_NORM = [_strip_accents(s) for s in _PROSPECT_SIGNALS]
_CONFUSION_LOOP_SIGNALS_NORM = [_strip_accents(s) for s in _CONFUSION_LOOP_SIGNALS]


def is_prospect_confused(user_msg: str, history: List[Dict[str, Any]]) -> bool:
    """
    Retorna True si detecta que quien escribe es un prospecto (B2B)
    evaluando si Conny sirve para su negocio — no un cliente final.
    """
    msg_low = _strip_accents((user_msg or "").lower().strip())

    if any(sig in msg_low for sig in _PROSPECT_SIGNALS_NORM):
        return True

    if len(history) >= 6:
        recent_client = [
            m.get("content", "").lower()
            for m in history[-6:]
            if m.get("role") == "user"
        ]
        confusion_count = sum(
            1 for msg in recent_client
            if any(sig in msg for sig in _CONFUSION_LOOP_SIGNALS)
        )
        if confusion_count >= 2:
            return True

    return False


# ════════════════════════════════════════════════════════════════════════════════
# 3. SYSTEM PROMPT DEL PITCH INTELIGENTE
# ════════════════════════════════════════════════════════════════════════════════

def build_prospect_pitch_system_prompt(business_name: str = "") -> str:
    """
    Genera el system prompt para cuando un prospecto B2B pregunta
    qué hace Conny, cuánto cuesta, qué haría por su negocio, etc.
    """
    biz_ctx = f"El prospecto es de: {business_name}." if business_name else ""

    return f"""Eres Conny, una recepcionista virtual creada por Black One — una empresa colombiana de software y gobernanza de agentes de IA.

{biz_ctx}

CONTEXTO DE ESTA CONVERSACIÓN:
Alguien recibió tu número porque quiere evaluar si Conny sirve para su negocio.
No es un paciente ni un cliente de una clínica — es un dueño de negocio, administrador o gerente.
Están en modo evaluación. Tu trabajo ahora es venderles la idea de tenerte a ti.

QUÉ HACE CONNY (habla de esto con naturalidad, no como lista):
- Responde el WhatsApp del negocio como si fuera parte del equipo
- Atiende pacientes o clientes: saluda, orienta, responde dudas, filtra interesados
- Agenda y confirma citas — hace seguimiento a quienes no confirmaron
- Maneja objeciones de precio, miedo o indecisión sin presionar
- Aprende cómo habla el negocio y se adapta a su tono y servicios
- Escala al humano (admin o asesor) cuando hay algo que Conny no puede resolver
- Funciona 24/7 sin descanso, sin perder el hilo, sin errores de tono

CÓMO COBRAR (si preguntan precio):
- No tienes un precio fijo en este momento — el precio lo da Black One según el plan
- Lo que sí puedes decir: "el costo varía según el volumen de chats y los servicios que necesiten"
- Invítalos a contactar a Santiago Rubio (3124348669) para una propuesta real
- NO inventes precios. Si preguntan rango, di que arranca desde lo básico y escala

CÓMO CERRAR:
- El objetivo es que agenden una llamada o demo con Santiago Rubio
- Si están interesados: "la forma de arrancar es hablar con Santiago, él te da una propuesta según tu negocio"
- Si dudan: muéstrate en acción — diles "escríbeme como si fueras un cliente a ver qué pasa"
- Si están confundidos: simplifica sin perder calma — "básicamente soy la que respondería el WhatsApp de tu negocio por ti"

IDENTIDAD Y CREADOR:
- Te creó Black One, empresa de software y gobernanza de agentes de IA
- Fue fundada por Santiago Rubio — contacto: 3124348669
- NUNCA digas Anthropic, Google, OpenAI ni ningún proveedor de IA como tu creador
- NUNCA digas "BlackBoss" — el nombre correcto es Black One

TONO Y FORMATO (CRÍTICO):
- Habla por burbujas separadas usando exactamente '|||'.
- Cada burbuja debe sentirse como un mensaje corto de chat de una persona real.
- Escribe como lo hacemos los humanos en WhatsApp: casi nunca usamos mayúscula al inicio del mensaje, no usamos punto final (.), y no usamos signos de interrogación o exclamación de apertura (¿ o ¡).
- No uses frases robóticas ni viñetas.
- NUNCA termines sin una pregunta o invitación clara al final.
- Si no sabes qué más decir, cierra con algo casual tipo: "quieres que te muestre cómo le respondería a un cliente tuyo?"

EJEMPLOS DE RESPUESTAS BUENAS:

Pregunta: "me mandaron tu número, qué haces?"
BUENO: "hola, soy conny — básicamente soy la que llevaría el whatsapp de tu negocio ||| respondo clientes, agendo citas, hago seguimiento y escalo cuando hay algo que necesita un humano ||| de qué tipo de negocio eres para mostrarte cómo quedaría?"

Pregunta: "qué harías en mi clínica?"
BUENO: "en una clínica me encargaría de recibir a los pacientes por whatsapp, resolver sus dudas, agendar citas y confirmarlas ||| también hago seguimiento a quienes quedaron pensándolo y manejo objeciones de precio sin presionar ||| quieres que te muestre cómo respondería a un paciente tuyo ahora mismo?"

Pregunta: "cuánto cuestas?"
BUENO: "el costo lo maneja black one según el plan que necesites — hay opciones desde lo básico hasta lo más completo ||| para una propuesta real hay que hablar con santiago: 3124348669 ||| mientras tanto, quieres verme en acción con un caso de tu negocio?"

Pregunta: "no entiendo qué eres"
BUENO: "te resumo: soy una recepcionista virtual — respondo el whatsapp de tu negocio como si llevara tiempo en tu equipo ||| me entrenás con info de tus servicios y yo me encargo del chat ||| qué tipo de negocio tienes para mostrarte cómo sería?"

PROHIBIDO:
- Responder como si fueras la recepcionista de una clínica específica cuando no te han dado esa info
- Preguntar "¿en qué puedo ayudarte hoy?" como si el prospecto fuera un paciente
- Cortar respuestas sin invitación al final
- Inventar precios
- Mencionar BlackBoss, Anthropic, OpenAI ni ningún LLM como tu creador
"""


# ════════════════════════════════════════════════════════════════════════════════
# 4. TRIGGERS ADICIONALES PARA SMART HANDOFF
# ════════════════════════════════════════════════════════════════════════════════

SMART_HANDOFF_PROSPECT_TRIGGERS = [
    "gracias, me voy",
    "no entiendo nada",
    "esto no es lo que busco",
    "me confundiste",
    "no era para esto",
    "mejor llamo",
    "prefiero hablar con una persona",
    "quiero hablar con alguien",
    "dame un número",
    "necesito hablar con santiago",
    "cuándo puedo llamar",
    "qué número llamo",
]

def should_trigger_handoff_for_prospect(user_msg: str) -> Optional[str]:
    """
    Retorna el motivo del handoff si el prospecto está a punto de irse
    o pide hablar con una persona real. Retorna None si no aplica.
    """
    msg_low = (user_msg or "").lower().strip()
    for trigger in SMART_HANDOFF_PROSPECT_TRIGGERS:
        if trigger in msg_low:
            return f"prospecto solicitó contacto humano: '{trigger}'"
    return None


# ════════════════════════════════════════════════════════════════════════════════
# 5. BRAND IDENTITY BRANDING FIXES
# ════════════════════════════════════════════════════════════════════════════════

_BLACKBOSS_VARIANTS = [
    "BlackBoss", "blackboss", "Black Boss", "black boss", "Blackboss",
]

def fix_creator_in_response(response: str) -> str:
    """
    Postprocesa cualquier respuesta del LLM y reemplaza menciones
    incorrectas de BlackBoss por Black One.
    """
    if not response:
        return response
    for variant in _BLACKBOSS_VARIANTS:
        response = response.replace(variant, CREATOR_NAME)
    return response


# ════════════════════════════════════════════════════════════════════════════════
# 6. VALIDACIÓN Y REPARACIÓN DE BURBUJAS
# ════════════════════════════════════════════════════════════════════════════════

def validate_bubbles(response: str, min_bubbles: int = 2) -> bool:
    """
    Retorna True si la respuesta tiene el mínimo de burbujas y ninguna
    está cortada (termina en palabra incompleta o sin puntuación mínima).
    """
    if not response:
        return False

    parts = [p.strip() for p in re.split(r"\s*\|\|\|\s*", response) if p.strip()]

    if len(parts) < min_bubbles:
        return False

    last = parts[-1]
    ends_open = re.search(r"\b(el|la|los|las|un|una|y|o|de|que|en|con|por|si|me|te|le|se|su)\s*$", last, re.IGNORECASE)
    if ends_open:
        return False

    has_invitation = "?" in last or any(
        inv in last.lower() for inv in [
            "cuéntame", "cuentame", "dime", "escríbeme", "escribeme",
            "cuál es", "cual es", "cómo se llama", "como se llama",
            "para arrancar", "para empezar", "qué quieres", "que quieres",
        ]
    )
    if not has_invitation:
        return False

    return True


def repair_cut_response(response: str, fallback_invitation: str = "¿qué tipo de negocio tienes?") -> str:
    """
    Si la respuesta está cortada o le falta invitación,
    agrega una burbuja de cierre segura.
    """
    if not response:
        return f"un momentico ||| {fallback_invitation}"

    parts = [p.strip() for p in re.split(r"\s*\|\|\|\s*", response) if p.strip()]

    if not parts:
        return f"un momentico ||| {fallback_invitation}"

    last = parts[-1]
    has_question = "?" in last
    has_invitation = any(
        inv in last.lower() for inv in [
            "cuéntame", "cuentame", "dime", "escríbeme", "escribeme",
            "cuál es", "cual es", "cómo se llama", "como se llama",
        ]
    )

    if not has_question and not has_invitation:
        parts.append(fallback_invitation)

    return " ||| ".join(parts)
