from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from .persona_registry import PersonaProfile, PersonaRegistry


@dataclass
class ConversationTurnResult:
    handled: bool
    bubbles: List[str]
    reason: str = ""
    persona_key: str = "default"


class ConversationEngine:
    def __init__(self, registry: PersonaRegistry):
        self.registry = registry

    def handle(
        self,
        *,
        clinic: Dict[str, Any],
        user_msg: str,
        history: Optional[List[Dict[str, Any]]] = None,
        is_admin: bool = False,
        channel: str = "",
    ) -> ConversationTurnResult:
        history = history or []
        persona = self.registry.resolve_for_clinic(clinic)
        first_turn = not any(msg.get("role") == "assistant" for msg in history)
        normalized = self._normalize(user_msg)

        if is_admin:
            return ConversationTurnResult(False, [], reason="admin_route", persona_key=persona.key)

        # identity probe → LLM siempre — el system prompt ya sabe cómo responder "¿eres un bot?"
        # if self._is_identity_probe(normalized): disabled — no hardcoded

        # meta_followup → LLM siempre
        # if self._is_meta_followup_probe(normalized): disabled — no hardcoded

        if self._is_greeting_only(normalized):
            return ConversationTurnResult(False, [], reason="llm_greeting", persona_key=persona.key)

        # primer turno con contexto → LLM siempre (no hardcoded)
        # if first_turn and self._looks_like_contextual_first_turn(persona, clinic, normalized):
        #     disabled: el LLM genera una respuesta más natural

        return ConversationTurnResult(False, [], reason="not_handled", persona_key=persona.key)

    def _normalize(self, text: str) -> str:
        return (text or "").strip().lower()

    def _is_greeting_only(self, normalized: str) -> bool:
        cleaned = normalized.replace("0", "o")
        cleaned = cleaned.replace("!", "").replace("?", "").replace("¡", "").replace("¿", "").strip()
        cleaned = cleaned.replace(",", " ").replace(".", " ")
        cleaned = " ".join(cleaned.split())
        return cleaned in {
            "hola",
            "hola que tal",
            "hola como vas",
            "hola como estas",
            "hola que mas",
            "hola buenas",
            "buenas",
            "buenas tardes",
            "buenos dias",
            "buenos días",
            "buenas noches",
            "hey",
            "holi",
            "como vas",
            "como estas",
            "todo bien",
            "que mas",
            "qué más",
            "que tal",
        }

    def _is_identity_probe(self, normalized: str) -> bool:
        probes = (
            "que eres",
            "qué eres",
            "quien eres",
            "quién eres",
            "eres una ia",
            "eres ia",
            "eres un bot",
            "eres bot",
            "como funcionas",
            "cómo funcionas",
            "que haces",
            "qué haces",
            "quiero probarte",
            "me gustaria probarte",
            "me gustaría probarte",
            "tengo un negocio",
            "tengo una empresa",
            "quiero una demo",
            "quiero demo",
            "soy curioso",
            "quiero saber quien eres",
            "quiero saber quién eres",
        )
        return any(marker in normalized for marker in probes)

    def _is_meta_followup_probe(self, normalized: str) -> bool:
        probes = (
            "como trabajas aqui",
            "cómo trabajas aquí",
            "como trabajas por aqui",
            "cómo trabajas por aquí",
            "lo llevas tu sola",
            "lo llevas tú sola",
            "atiendes como secretaria",
            "atiendes como asesora",
            "si te pregunto por un procedimiento",
            "si te pregunto por precio",
            "quiero entender si recuerdas",
            "recuerdas lo que te digo",
            "como recuerdas",
            "cómo recuerdas",
        )
        return any(marker in normalized for marker in probes)

    def _looks_like_first_contact_request(self, normalized: str) -> bool:
        signals = (
            "hola",
            "buenas",
            "quiero probarte",
            "me gustaria probarte",
            "me gustaría probarte",
            "tengo un negocio",
            "tengo una empresa",
        )
        return any(sig in normalized for sig in signals)

    def _looks_like_contextual_first_turn(
        self,
        persona: PersonaProfile,
        clinic: Dict[str, Any],
        normalized: str,
    ) -> bool:
        if self._looks_like_first_contact_request(normalized):
            return True
        if self._extract_topic(persona, clinic, normalized):
            return True
        return any(token in normalized for token in ("precio", "cuanto", "cuánto", "horario", "agenda", "cita", "disponibilidad"))

    def _build_first_turn(self, persona: PersonaProfile, clinic: Dict[str, Any]) -> List[str]:
        clinic_name = str(clinic.get("name") or "").strip()
        intro_template = self._choose(
            persona.first_turn_variants
            or [f"Hola! {f'{clinic_name}. ' if clinic_name else ''}¿Qué te trae por acá?"],
            clinic_name or persona.identity,
        )
        intro = self._render_persona_line(intro_template, persona, clinic_name)

        if persona.capabilities:
            if clinic.get("sector") == "estetica":
                capabilities = (
                    f"Te ayudo con {', '.join(persona.capabilities[:3])}. "
                    "Si quieres, cuéntame qué te interesa o qué tratamiento estás mirando."
                )
            else:
                capabilities = (
                    f"Te ayudo con {', '.join(persona.capabilities[:3])}. "
                    "¿Qué estás buscando?"
                )
        else:
            capabilities = ""

        return [intro, capabilities] if capabilities else [intro]

    def _build_returning_greeting(
        self,
        persona: PersonaProfile,
        clinic: Dict[str, Any],
        history: Optional[List[Dict[str, Any]]],
        normalized: str,
    ) -> List[str]:
        history = history or []
        gap_hours = self._hours_since_last_turn(history)
        recent_topic = self._extract_recent_topic_from_history(persona, clinic, history)

        if any(marker in normalized for marker in ("como estas", "cómo estás", "como vas", "cómo vas", "que tal", "qué tal")):
            if gap_hours is not None and gap_hours >= 24:
                intro = "Hola. Todo bien por acá."
            else:
                intro = "Hola. Todo bien por acá, gracias por preguntar."
        else:
            intro = "Hola."

        if recent_topic:
            followup = f"Si sigues con lo de {recent_topic}, dime y lo vemos."
        else:
            followup = "Cuéntame qué quieres revisar y lo vemos."

        return [intro, followup]

    def _build_identity_probe(
        self,
        persona: PersonaProfile,
        clinic: Dict[str, Any],
        normalized: str,
        history: Optional[List[Dict[str, Any]]] = None,
        first_turn: bool = True,
    ) -> List[str]:
        clinic_name = str(clinic.get("name") or "").strip()
        history = history or []
        if not first_turn and any(marker in normalized for marker in (
            "eres una ia",
            "eres ia",
            "eres una persona",
            "persona real",
            "eres un bot",
            "eres bot",
        )):
            agent_id = getattr(persona, "identity", "Bublee")
            return [
                f"Sí, soy {agent_id} — una IA{f' de {clinic_name}' if clinic_name else ''}. Ayudo al equipo a atender este chat.",
                "¿En qué te ayudo?",
            ]
        prior_identity = any(
            any(marker in self._normalize(str(msg.get("content") or "")) for marker in (
                "recepcionista virtual",
                "asesora virtual",
                "soy bublee",
                "trabaja por tu negocio",
                "disponible por aqui",
                "disponible por aquí",
            ))
            for msg in history
            if msg.get("role") == "assistant"
        )
        if prior_identity:
            agent_id = getattr(persona, "identity", "Bublee")
            return [
                f"Sigo siendo {agent_id}{f' de {clinic_name}' if clinic_name else ''} — una IA, no una persona.",
                "¿En qué más te ayudo?",
            ]

        intro = self._choose(
            persona.identity_probe_variants or [
                f"Soy {persona.identity} — una IA{f' de {clinic_name}' if clinic_name else ''}. Ayudo al equipo a atender este chat.",
                f"Soy {persona.identity}, una IA. Oriento, respondo y ayudo a avanzar{f' en {clinic_name}' if clinic_name else ''}.",
            ],
            normalized,
        )
        intro = self._render_persona_line(intro, persona, clinic_name)
        if persona.capabilities:
            cta = "¿Qué necesitas?"
        else:
            cta = "¿En qué te ayudo?"
        return [intro, cta]

    def _render_persona_line(self, template: str, persona: PersonaProfile, clinic_name: str) -> str:
        raw = str(template or "").strip()
        if not raw:
            return f"Hola{f', {clinic_name}' if clinic_name else ''}! ¿Qué buscas?"
        clinic_label = clinic_name.strip() if clinic_name else ""
        if "{clinic_name}" in raw and not clinic_label:
            clinic_label = "la clínica"
        try:
            rendered = raw.format(clinic_name=clinic_label, identity=persona.identity).strip()
        except Exception:
            rendered = raw
        rendered = rendered.replace("de .", "de la clínica")
        rendered = " ".join(rendered.split())
        return rendered

    def _build_meta_followup(
        self,
        persona: PersonaProfile,
        clinic: Dict[str, Any],
        normalized: str,
    ) -> List[str]:
        if any(marker in normalized for marker in (
            "lo llevas tu sola",
            "lo llevas tú sola",
        )):
            return [
                "Yo sostengo este canal y el hilo de la conversación, pero no me pongo a improvisar donde toca confirmación real.",
                "Si algo depende de una valoración o de validar un dato del negocio, te lo digo directo y lo aterrizo sin humo.",
            ]

        if any(marker in normalized for marker in (
            "como trabajas aqui",
            "cómo trabajas aquí",
            "como trabajas por aqui",
            "cómo trabajas por aquí",
        )):
            return [
                "Trabajo llevando la conversación, entendiendo qué necesitas y guiándote hacia lo útil, no soltando respuestas al azar.",
                "Y si algo toca confirmarlo con el negocio, te lo digo claro en vez de inventártelo.",
            ]

        if any(marker in normalized for marker in ("atiendes como secretaria", "atiendes como asesora")):
            return [
                "Un poco de las dos, pero bien hecho: recibo, oriento y también ayudo a mover la conversación hacia una decisión o una cita.",
                "La idea es que se sienta como alguien del equipo, no como un formulario con patas.",
            ]

        if any(marker in normalized for marker in ("si te pregunto por un procedimiento", "si te pregunto por precio")):
            return [
                "Te respondo lo que sí pueda orientarte con claridad y te aterrizo el siguiente paso útil.",
                "Si algo depende de valoración o de confirmación del negocio, te lo digo así, sin humo ni datos inventados.",
            ]

        if any(marker in normalized for marker in (
            "quiero entender si recuerdas",
            "recuerdas lo que te digo",
            "como recuerdas",
            "cómo recuerdas",
        )):
            return [
                "Sí, la idea es ir guardando lo importante de la conversación para no hacerte repetir todo.",
                "Y si algo no me queda claro, prefiero confirmártelo a fingir que me acuerdo de algo que no tengo bien amarrado.",
            ]

        clinic_name = str(clinic.get("name") or "").strip()
        agent_id = getattr(persona, "identity", "Bublee")
        return [
            f"Soy {agent_id}{f', de {clinic_name}' if clinic_name else ''} — una IA que lleva este chat.",
            "Respondo lo que puedo con certeza. Lo que no sé, lo escalo al equipo.",
        ]

    def _build_first_contextual_followup(
        self,
        persona: PersonaProfile,
        clinic: Dict[str, Any],
        normalized: str,
    ) -> List[str]:
        intro = self._build_first_turn(persona, clinic)[0]
        topic = self._extract_topic(persona, clinic, normalized)
        if topic:
            if persona.contextual_followups:
                for key, value in persona.contextual_followups.items():
                    if self._normalize(str(key)) == self._normalize(topic):
                        return [intro, str(value).strip()]
            sector = clinic.get("sector")
            if sector == "estetica":
                return [intro, f"{topic} lo manejan acá. Si quieres, te cuento cómo lo trabajan y qué suelen revisar para que se vea natural."]
            return [intro, f"{topic} lo manejan acá. Si quieres, te cuento cómo lo trabajan o revisamos valoración y disponibilidad."]
        followup = "Cuéntame qué estás buscando y te ubico rápido."
        if clinic.get("sector") == "estetica":
            followup = "Cuéntame qué te gustaría mejorar o qué tratamiento estás mirando, y te ubico rápido."
        return [intro, followup]

    def _extract_topic(self, persona: PersonaProfile, clinic: Dict[str, Any], normalized: str) -> str:
        overrides = persona.contextual_followups or {}
        for key in overrides.keys():
            key_norm = self._normalize(str(key))
            if key_norm and key_norm in normalized:
                return str(key).strip()

        services = clinic.get("services") if isinstance(clinic.get("services"), list) else []
        for service in services:
            service_text = str(service).strip()
            if not service_text:
                continue
            if self._normalize(service_text) in normalized:
                return service_text

        topics = {
            "botox": "Botox",
            "relleno": "Rellenos",
            "rellenos": "Rellenos",
            "laser": "Láser",
            "láser": "Láser",
            "peeling": "Peeling",
            "mesoterapia": "Mesoterapia",
            "precio": "Precio",
            "horario": "Horario",
            "agenda": "Cita",
            "cita": "Cita",
            "disponibilidad": "Disponibilidad",
        }
        for marker, label in topics.items():
            if marker in normalized:
                return label
        return ""

    def _extract_recent_topic_from_history(
        self,
        persona: PersonaProfile,
        clinic: Dict[str, Any],
        history: Optional[List[Dict[str, Any]]],
    ) -> str:
        history = history or []
        generic_fallback = ""
        generic_labels = {"Precio", "Horario", "Cita", "Disponibilidad"}
        for msg in reversed(history):
            if msg.get("role") != "user":
                continue
            topic = self._extract_topic(persona, clinic, self._normalize(str(msg.get("content") or "")))
            if not topic:
                continue
            if topic not in generic_labels:
                return topic
            if not generic_fallback:
                generic_fallback = topic
        return generic_fallback

    def _hours_since_last_turn(self, history: Optional[List[Dict[str, Any]]]) -> Optional[float]:
        history = history or []
        for msg in reversed(history):
            raw_ts = str(msg.get("ts") or "").strip()
            if not raw_ts:
                continue
            try:
                then = datetime.fromisoformat(raw_ts)
            except ValueError:
                continue
            return max(0.0, (datetime.now() - then).total_seconds() / 3600.0)
        return None

    def _choose(self, variants: List[str], normalized: str) -> str:
        if not variants:
            return ""
        index = sum(ord(ch) for ch in normalized) % len(variants)
        return variants[index]
