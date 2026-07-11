from __future__ import annotations
import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from bublee_core.first_turn_ops import _normalize_conv_text

log = logging.getLogger("bublee.onboarding_flow")

_business_confirmation_signals = (
    "sí ese es", "si ese es", "ese sí", "ese si", "ese mismo", "correcto ese",
    "sí, ese", "si, ese", "exacto", "sí es ese", "si es ese",
    "sí", "si", "sip", "claro", "correcto", "ese", "eso", "yes", "yep",
    "thats us", "that's us", "that is us", "yes thats us", "yes that's us",
    "yes thats right", "yes that's right", "thats right", "that's right",
    "ajá", "aja", "dale", "listo", "así es", "asi es", "es ese", "ese es", "exactamente",
    "sí señor", "si señor", "siii", "siiii", "siiiii", "sii",
    "somos nosotros", "somos esos", "somos ese", "ese somos", "eso somos",
    "somos esa", "esa somos", "si somos nosotros", "sí somos nosotros",
    "es de nosotros", "ese es nuestro", "es nuestro", "eso es nuestro",
    "eso somos nosotros", "esos somos", "ese sí somos", "ese si somos",
    "claro que sí somos", "claro que si somos", "somos el negocio", "somos esa clínica",
)

def looks_like_business_confirmation(raw_text: str) -> bool:
    normalized = _normalize_conv_text(raw_text or "")
    if not normalized:
        return False
    return any(
        normalized == signal or (len(signal) > 6 and signal in normalized)
        for signal in _business_confirmation_signals
    )

def owner_confusion_or_language_signal(raw_text: str) -> bool:
    normalized = _normalize_conv_text(raw_text or "")
    if not normalized:
        return False
    signals = (
        "just english sorry", "sorry just english", "english sorry",
        "english only", "speak english", "speak in english", "only english",
        "i dont speak spanish", "i don t speak spanish",
        "i dont talk spanish", "i don t talk spanish",
        "what is this", "sorry what is this",
        "i dont understand", "i don t understand",
        "what did you say", "what did u say",
        "thats not my business", "that s not my business",
        "that is not my business", "not my business",
        "thats not us", "that s not us", "that is not us", "wrong business",
        "wrong company", "wrong one", "not the right one",
        "no hablo español", "no hablo espanol", "solo ingles", "solo inglés",
    )
    return any(signal in normalized for signal in signals)

def looks_like_business_name_candidate_legacy(raw_text: str) -> bool:
    candidate = (raw_text or "").strip()
    if not candidate:
        return False
    normalized = _normalize_conv_text(candidate)
    if len(candidate) > 90:
        return False
    if owner_confusion_or_language_signal(candidate):
        return False
    owner_name_false_positives = (
        "mi nombre es",
        "me llamo",
        "my name is",
        "i am ",
        "i'm ",
        "im ",
    )
    explicit_business_markers = (
        "el nombre de mi negocio se llama",
        "el nombre de nuestro negocio se llama",
        "el nombre de mi empresa se llama",
        "el nombre de nuestra empresa se llama",
        "el nombre de mi negocio es",
        "el nombre del negocio es",
        "el nombre de mi empresa es",
        "el nombre de la empresa es",
        "mi negocio se llama",
        "nuestro negocio se llama",
        "mi empresa se llama",
        "nuestra empresa se llama",
        "la clinica se llama",
        "la clínica se llama",
        "se llama ",
        "negocio es ",
        "empresa es ",
    )
    if (
        any(marker in normalized for marker in owner_name_false_positives)
        and not any(marker in normalized for marker in explicit_business_markers)
    ):
        return False
    conversational_false_positives = (
        "somos nosotros", "somos nosotras", "somos ese", "somos esa",
        "si somos", "sí somos", "siii somos", "siiii somos",
        "that is us", "that's us", "thats us", "yes thats us", "yes that's us",
        "this is us", "we are that", "we are them",
    )
    if any(marker in normalized for marker in conversational_false_positives):
        return False
    if any(marker in normalized for marker in explicit_business_markers):
        return True

    if any(
        marker in normalized
        for marker in (
            "como estas", "cómo estás", "quien eres", "quién eres", "que eres", "qué eres",
            "que haces", "qué haces", "que harias", "qué harías", "como funcionas", "cómo funcionas", "aceptas audios",
            "aceptas pdf", "para que", "para qué", "quien te hizo", "quién te hizo",
            "me mandaron tu numero", "me mandaron tu número", "quiero una demo", "quiero demo",
            "quiero probarte", "tengo un negocio", "tengo una empresa", "hola", "buenas", "?",
            "what is this", "sorry what is this", "what do you do", "who are you",
            "i dont understand", "i don t understand", "english only", "just english sorry",
            "i dont talk spanish", "i don t talk spanish", "i dont speak spanish", "i don t speak spanish",
        )
    ):
        return False
    if looks_like_business_confirmation(candidate):
        return False

    words = re.findall(r"[A-Za-zÁÉÍÓÚáéíóúÑñ0-9&.'-]+", candidate)
    if not (1 <= len(words) <= 8):
        return False
    if any(ch.isupper() for ch in candidate):
        upper_tokens = [word.lower() for word in words if len(word) >= 2]
        blocked_upper_tokens = {
            "sorry", "spanish", "what", "this", "that",
            "dont", "don't", "understand", "talk", "speak", "only", "hello",
            "hi", "hola", "business", "not", "my",
        }
        if any(token in blocked_upper_tokens for token in upper_tokens):
            return False
        return True
    business_tokens = (
        "clinica", "clínica", "clinic", "spa", "dental", "salud", "centro",
        "consultorio", "estetica", "estética", "studio", "group", "lab",
        "restaurante", "hotel", "tienda", "academia", "gym", "gimnasio",
    )
    if any(token in normalized for token in business_tokens):
        return True
    # Marcas de 1-3 palabras sin jerga conversacional también pueden ser válidas.
    if 1 <= len(words) <= 3 and all(len(word) >= 3 for word in words):
        stop_tokens = {
            "sorry", "spanish", "hello", "what", "this", "that",
            "understand", "business", "please", "talk", "speak", "only",
            "dont", "not", "sorry",
        }
        if not any(word.lower() in stop_tokens for word in words):
            return True
    return False

async def llm_classify_business_name(raw_text: str, engine: Any) -> Tuple[bool, Optional[str]]:
    candidate = (raw_text or "").strip()
    if not candidate:
        return False, None
    
    if len(candidate) < 2 or len(candidate) > 100:
        return False, None
        
    normalized = _normalize_conv_text(candidate)
    if normalized in {
        "hola", "holaa", "holaaa", "holaaaa", "buenas", "buenasas", "buenasas", "buenasas",
        "hey", "ey", "hi", "hello", "reset", "reiniciar", "menu", "menú"
    }:
        return False, None

    sys_prompt = """Eres un clasificador y extractor de nombres de negocio de alta precisión para un chatbot de WhatsApp en modo demo.
Analiza el mensaje del usuario y determina si está respondiendo a la pregunta de cómo se llama su negocio proporcionando el nombre de una clínica, empresa, marca, local o tienda para la demostración.

REGLAS DE CLASIFICACIÓN:
1. El mensaje debe contener el nombre de un negocio o marca de manera evidente (ej. "Nova", "Clinica de la Costa", "mi negocio es Spa Luna").
2. Conversaciones casuales, saludos, preguntas sobre el funcionamiento del bot ("¿qué me quieres mostrar?", "¿de qué se trata?", "me mandaron tu número", "¿quién eres?"), respuestas afirmativas/negativas generales ("sí", "no", "ok", "claro"), o nombres de personas solos ("Santiago") NO son nombres de negocio.
3. Si el mensaje es una frase donde presenta el negocio (ej. "se llama Peludos"), clasifica como negocio y extrae solo la marca limpia ("Peludos").

EJEMPLOS DE POCAS TOMAS (FEW-SHOT):
- Mensaje: "Nova"
  Respuesta: {"es_negocio": true, "nombre": "Nova"}
- Mensaje: "mi clínica se llama Clínica Dental Americana"
  Respuesta: {"es_negocio": true, "nombre": "Clínica Dental Americana"}
- Mensaje: "de qué se trata esto?"
  Respuesta: {"es_negocio": false, "nombre": null}
- Mensaje: "no quiero darte el nombre"
  Respuesta: {"es_negocio": false, "nombre": null}
- Mensaje: "Spa Luna, hacemos tratamientos faciales"
  Respuesta: {"es_negocio": true, "nombre": "Spa Luna"}
- Mensaje: "Petlandia"
  Respuesta: {"es_negocio": true, "nombre": "Petlandia"}
- Mensaje: "Carlos"
  Respuesta: {"es_negocio": false, "nombre": null}
- Mensaje: "hola buenas"
  Respuesta: {"es_negocio": false, "nombre": null}

Responde ÚNICAMENTE con un JSON válido:
{
  "es_negocio": true o false,
  "nombre": "nombre del negocio limpio" (o null si es_negocio es false)
}"""

    try:
        if not engine:
            raise RuntimeError("LLM no init")
        msgs = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": f"Mensaje del usuario: {raw_text}"}
        ]
        r, meta = await engine.complete(
            msgs,
            model_tier="fast",
            temperature=0.0,
            max_tokens=512,
            use_cache=False,
        )
        log.info(f"[onboarding] classify business name LLM using {meta.get('provider','?')} model={meta.get('model','?')[:30]}")
        if not r:
            return looks_like_business_name_candidate_legacy(raw_text), None

        clean_r = r.strip()
        start_idx = clean_r.find("{")
        end_idx = clean_r.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            clean_r = clean_r[start_idx:end_idx+1]
        
        data = json.loads(clean_r)
        return bool(data.get("es_negocio", False)), data.get("nombre")
    except Exception as e:
        log.error(f"[onboarding] Business name classification LLM failed: {e}")
        legacy_res = looks_like_business_name_candidate_legacy(raw_text)
        return legacy_res, None
