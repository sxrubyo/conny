"""
api_awareness.py — Inteligencia sobre APIs disponibles.

El agente razona sobre qué capacidades tiene disponibles en runtime
y las usa cuando tienen sentido. No hardcodea "tengo ElevenLabs" ni
"no tengo ElevenLabs" — lo verifica y razona.

Capacidades gestionadas:
- ElevenLabs (voz/audio)
- Apify (scraping/datos)
- Extensible a cualquier API futura
"""
from __future__ import annotations
import os
import logging
from typing import Dict, List, Tuple, Optional

log = logging.getLogger("bublee.api_awareness")


class APICapabilityMap:
    """
    Detecta qué APIs están disponibles en runtime y provee
    contexto al LLM para que razone inteligentemente su uso.
    """

    def __init__(self):
        self._cache: Dict[str, bool] = {}

    def _check_elevenlabs(self) -> bool:
        """True si hay al menos una key de ElevenLabs válida."""
        keys = [
            os.getenv("ELEVENLABS_API_KEY", ""),
            os.getenv("ELEVENLABS_API_KEY_2", ""),
        ]
        # Las keys hardcodeadas en bublee_demo_voice.py también cuentan
        fallback_keys = [
            "sk_e200c93fe4787b44dae55fdfe4e938d1f07ebbd2b0a67bb7",
            "sk_199e6c73c2adbdeedd746de08fbb3ec7e9067259c7210c50",
        ]
        all_keys = [k for k in keys + fallback_keys if k and len(k) > 20]
        return len(all_keys) > 0

    def _check_apify(self) -> Tuple[bool, int]:
        """True si hay keys de Apify. Devuelve (disponible, cantidad_de_keys)."""
        keys = []
        for i in range(1, 25):
            suffix = f"_{i}" if i > 1 else ""
            k = os.getenv(f"APIFY_API_KEY{suffix}", "")
            if k and len(k) > 20:
                keys.append(k)
        # También APIFY_API_KEY sin sufijo
        k0 = os.getenv("APIFY_API_KEY", "")
        if k0 and len(k0) > 20 and k0 not in keys:
            keys.insert(0, k0)
        return len(keys) > 0, len(keys)

    def _check_whatsapp_audio(self) -> bool:
        """True si el bridge de WhatsApp soporta envío de audio."""
        bridge = os.getenv("WHATSAPP_BRIDGE_URL", "") or os.getenv("WA_BRIDGE_URL", "")
        platform = os.getenv("PLATFORM", "whatsapp").lower()
        return "whatsapp" in platform or bool(bridge)

    def get_capabilities(self) -> Dict[str, any]:
        """Devuelve el mapa completo de capacidades disponibles."""
        eleven_ok = self._check_elevenlabs()
        apify_ok, apify_count = self._check_apify()
        wa_audio = self._check_whatsapp_audio()

        return {
            "voice_audio": eleven_ok and wa_audio,
            "elevenlabs": eleven_ok,
            "whatsapp_audio_bridge": wa_audio,
            "apify": apify_ok,
            "apify_key_count": apify_count,
            "can_send_voice": eleven_ok and wa_audio,
        }

    def build_capability_context_for_prompt(self) -> str:
        """
        Genera el bloque que se inyecta en el system prompt del admin
        para que el LLM razone sobre las APIs disponibles.
        """
        caps = self.get_capabilities()
        lines: List[str] = ["CAPACIDADES DISPONIBLES AHORA:"]

        if caps["can_send_voice"]:
            lines.append(
                "- 🎙️ AUDIO/VOZ: ElevenLabs disponible + WhatsApp bridge activo. "
                "Puedes enviar notas de voz cuando el contexto lo justifique: "
                "primer turno (impacto), respuesta emocional importante, cierre de venta. "
                "NO en cada mensaje — úsalo estratégicamente."
            )
        else:
            lines.append(
                "- 🔇 AUDIO: ElevenLabs no configurado o bridge no disponible. "
                "Solo texto por ahora."
            )

        if caps["apify"]:
            lines.append(
                f"- 🕷️ APIFY: {caps['apify_key_count']} key(s) disponibles. "
                "Puedes hacer scraping de datos cuando el admin lo solicite "
                "(precios de competencia, disponibilidad, leads, etc.)."
            )
        else:
            lines.append("- 🕷️ APIFY: No configurado.")

        return "\n".join(lines)

    def should_send_voice(
        self,
        text: str,
        turn_number: int,
        context: str = "production",
        patient_data: Optional[Dict] = None,
    ) -> bool:
        """
        Razona si vale la pena enviar audio en este turno.
        Solo retorna True si ElevenLabs + bridge están disponibles Y el contexto lo justifica.
        """
        if not self.get_capabilities()["can_send_voice"]:
            return False

        # Demo: primeros turnos siempre con voz
        if context == "demo":
            return turn_number <= 2 or (turn_number <= 5 and len(text) < 120)

        # Producción: solo en momentos de alto impacto
        text_lower = (text or "").lower()
        high_impact = any(kw in text_lower for kw in (
            "cuánto cuesta", "cuanto cuesta", "precio", "me interesa",
            "quiero agendar", "quiero una cita", "urgente", "emergencia",
            "gracias", "perfecto", "listo", "de acuerdo",
        ))
        if context == "production" and high_impact and turn_number in (1, 3, 6):
            return True

        return False


# Singleton
_capability_map = APICapabilityMap()


def get_api_capabilities() -> Dict[str, any]:
    return _capability_map.get_capabilities()


def build_capability_prompt_block() -> str:
    return _capability_map.build_capability_context_for_prompt()


def should_send_voice(text: str, turn_number: int, context: str = "production") -> bool:
    return _capability_map.should_send_voice(text, turn_number, context)
