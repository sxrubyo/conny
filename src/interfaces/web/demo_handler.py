from __future__ import annotations
import logging
import asyncio
import re
import json
import time
import random
import base64 as _b64
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

log = logging.getLogger("conny.demo")

async def handle_demo_message(
    self, chat_id: str, text: str, clinic: Dict,
    attachments: Optional[List[Dict[str, Any]]] = None
) -> List[str]:
    # Local imports from conny.py to avoid circular dependencies
    import sys
    conny_module = sys.modules[self.__class__.__module__]
    Config = conny_module.Config
    db = conny_module.db
    now_col = conny_module.now_col
    PersonalityProfile = conny_module.PersonalityProfile
    llm_engine = conny_module.llm_engine
    try:
        from src.core.globals import v8_process_response, _normalize_first_contact_response
    except ImportError:
        v8_process_response = getattr(conny_module, "v8_process_response", lambda r, **kwargs: r)
        _normalize_first_contact_response = getattr(conny_module, "_normalize_first_contact_response", lambda r, **kwargs: r)
    try:
        from src.domain.send_guard import SendGuard
    except ImportError:
        try:
            from src.conny.production.guard import SendGuard
        except ImportError:
            SendGuard = getattr(conny_module, "SendGuard", None)
    try:
        from src.domain.prompts.prospect_pitch import is_prospect_confused
    except ImportError:
        is_prospect_confused = getattr(conny_module, "is_prospect_confused", lambda x, y: False)
        
    try:
        from src.core.globals import _SMART_HANDOFF, handoff_manager
    except ImportError:
        _SMART_HANDOFF = getattr(conny_module, "_SMART_HANDOFF", False)
        handoff_manager = getattr(conny_module, "handoff_manager", None)
        
    try:
        from src.domain.send_guard import _normalize_conv_text
    except ImportError:
        _normalize_conv_text = getattr(conny_module, "_normalize_conv_text", lambda x: x.lower().strip())

    from src.domain.onboarding_flow import (
        llm_classify_business_name,
        looks_like_business_name_candidate_legacy as _looks_like_business_name_candidate_legacy,
        looks_like_business_confirmation as _looks_like_business_confirmation,
        owner_confusion_or_language_signal as _owner_confusion_or_language_signal
    )

    # Check if optional symbols are available
    _SESSION_MANAGER_AVAILABLE = getattr(conny_module, "_SESSION_MANAGER_AVAILABLE", False)
    _BLACKONE_PATCHES = getattr(conny_module, "_BLACKONE_PATCHES", False)
    _CONNY_DOMINO_AVAILABLE = getattr(conny_module, "_CONNY_DOMINO_AVAILABLE", False)
    build_demo_domino_payload = getattr(conny_module, "build_demo_domino_payload", None)
    build_prospect_pitch_system_prompt = getattr(conny_module, "build_prospect_pitch_system_prompt", None)
    fix_creator_in_response = getattr(conny_module, "fix_creator_in_response", None)
    _core_normalize_first_contact_response = getattr(conny_module, "_core_normalize_first_contact_response", None)
    looks_fragmented_reply = getattr(conny_module, "looks_fragmented_reply", None)
    _is_greeting_only = getattr(conny_module, "_is_greeting_only", None)
    extract_model_request_from_text = getattr(conny_module, "extract_model_request_from_text", None)
    multilingual_handler = getattr(conny_module, "multilingual_handler", None)
    MultilingualHandler = getattr(conny_module, "MultilingualHandler", None)
    GroqProvider = getattr(conny_module, "GroqProvider", None)
    GeminiProvider = getattr(conny_module, "GeminiProvider", None)
    OpenRouterProvider = getattr(conny_module, "OpenRouterProvider", None)

    """
    MODO DEMO v3 — Experiencia de intriga progresiva.
    Conny NO se presenta como IA ni da un pitch.
    Entra directo al personaje y revela capacidades una a una.
    TTL: sesión independiente por persona (DEMO_SESSION_TTL segundos).
    """
    import base64 as _b64
    import random as _r
    attachments = attachments or []

    # ── Extracción de texto de documentos adjuntos ───────────────────────
    # Si el owner manda un PDF/doc sin caption, extraemos su texto y lo
    # usamos como si hubiera sido escrito en el mensaje.
    _doc_extracted_text = ""
    _has_incoming_doc = False
    for _att in attachments:
        _att_kind = _att.get("kind", "")
        _att_mime = _att.get("mime_type", "")
        _is_doc = _att_kind == "document" or "pdf" in _att_mime or "text" in _att_mime or "word" in _att_mime or "docx" in _att_mime
        if not _is_doc and _att_kind not in ("document",):
            continue
        _has_incoming_doc = True
        # Intentar extraer texto del binario
        try:
            _raw = _att.get("bytes") or b""
            if not _raw and _att.get("base64"):
                _raw = _b64.b64decode(_att["base64"])
            if not _raw and _att.get("file_id") and _att.get("platform") == "telegram":
                _raw, _ = await self._download_telegram_binary(_att["file_id"])
            if not _raw and _att.get("media_id") and _att.get("platform") == "whatsapp_cloud":
                _raw, _, _ = await self._download_whatsapp_cloud_binary(_att["media_id"])
            if _raw:
                try:
                    import pdfplumber as _pp, io as _io
                    with _pp.open(_io.BytesIO(_raw)) as _pdf:
                        _pages = [p.extract_text() or "" for p in _pdf.pages[:6]]
                        _doc_extracted_text = "\n".join(filter(None, _pages))[:2000]
                except Exception:
                    # Fallback: intentar leer como texto plano
                    try:
                        _doc_extracted_text = _raw.decode("utf-8", errors="ignore")[:2000]
                    except Exception:
                        pass
        except Exception:
            pass
        break  # Solo procesamos el primer documento

    # Si llegó un doc, enriquecemos el texto con su contenido extraído
    if _has_incoming_doc and not text.strip():
        if _doc_extracted_text.strip():
            text = f"[documento adjunto]\n{_doc_extracted_text.strip()}"
        else:
            text = "[documento adjunto]"
    if not hasattr(self, "_emoji_chats_off"):
        self._emoji_chats_off = set()

    # ── Gestión de sesión via SessionManager ───────────────────────────────
    if _SESSION_MANAGER_AVAILABLE and hasattr(self, "_session_mgr"):
        is_new, keys_del = self._session_mgr.touch_and_cleanup(chat_id)
        if is_new:
            for k in keys_del:
                del self._demo_sessions[k]
            try:
                with db._conn() as c:
                    c.execute("DELETE FROM conversations WHERE chat_id=?", (chat_id,))
            except Exception: pass
        sk = f"demo_{chat_id}"
    else:
        now = time.time()
        ttl = Config.DEMO_SESSION_TTL
        sk  = f"demo_{chat_id}"
        if self._demo_sessions.get(sk + "_ttl"):
            try:
                ttl = int(self._demo_sessions[sk + "_ttl"])
            except Exception: pass
        else:
            try:
                if db:
                    clinic = db.get_clinic()
                    if clinic and clinic.get("demo_session_ttl"):
                        ttl = int(clinic.get("demo_session_ttl"))
                    else:
                        db_ttl = db.recall("demo_session_ttl")
                        if db_ttl:
                            ttl = int(db_ttl)
            except Exception: pass

        last_seen = self._demo_sessions.get(sk + "_ts", 0)
        is_new    = (now - last_seen) > ttl
        self._demo_sessions[sk + "_ts"] = now
        self._demo_sessions = {
            k: v for k, v in self._demo_sessions.items()
            if not k.endswith("_ts") or (now - v) < ttl * 2
        }
        if is_new:
            keys_del = [k for k in list(self._demo_sessions) if k.startswith(sk+"_") and not k.endswith("_ts")]
            for k in keys_del: del self._demo_sessions[k]
            try:
                from conny_memory import get_memory
                instance_id = "default"
                if db:
                    remembered_slug = (db.recall("instance_slug") or "").strip()
                    if remembered_slug:
                        instance_id = remembered_slug.lower()
                mem = get_memory(instance_id)
                mem.delete_session_cache(chat_id)
            except Exception: pass
            try:
                with db._conn() as c:
                    c.execute("DELETE FROM conversations WHERE chat_id=?", (chat_id,))
            except Exception: pass

    history  = db.get_history(chat_id) if db else []
    now_dt   = now_col()
    moment   = "mañana" if now_dt.hour < 12 else ("tarde" if now_dt.hour < 19 else "noche")

    # Claves de sesión
    bname_key   = sk + "_name"
    bctx_key    = sk + "_ctx"
    bfound_key  = sk + "_found"
    burl_key    = sk + "_url"       # URL del negocio encontrada en web
    btrick_key  = sk + "_trick"
    bpersona_key= sk + "_persona"
    btone_key   = sk + "_tone"      # tono detectado: SALUD PREMIUM | PREMIUM | SALUD | RETAIL | GENERAL
    bmodel_key  = sk + "_model"     # proveedor LLM activo: auto|groq|gemini|openrouter
    blang_key   = sk + "_owner_lang" # idioma dominante del dueño en demo
    bowner_key  = sk + "_owner_name" # nombre del dueño/prospecto cuando lo comparte
    blearn_key  = sk + "_learn"     # modo aprendizaje manual: cuántas preguntas llevamos
    bsim_key    = sk + "_sim_mode"  # modo simulación cliente en el mismo chat del dueño
    bready_key  = sk + "_ready_customer"  # el dueño ya puede escribir como cliente

    business_name  = self._demo_sessions.get(bname_key, "")
    business_ctx   = self._demo_sessions.get(bctx_key, "")
    found_online   = self._demo_sessions.get(bfound_key, False)
    persona        = self._demo_sessions.get(bpersona_key, "amigable")
    demo_model_pref= self._demo_sessions.get(bmodel_key, "auto")  # auto|groq|gemini|openrouter
    owner_lang     = self._demo_sessions.get(blang_key, "es")
    owner_name     = self._demo_sessions.get(bowner_key, "")
    sim_mode_active = bool(self._demo_sessions.get(bsim_key, False))
    ready_for_customer = bool(self._demo_sessions.get(bready_key, False))
    llm_runtime_ready = self._llm_runtime_available()

    def _detect_demo_owner_language(raw_text: str, current_lang: str = "es") -> str:
        normalized = _normalize_conv_text(raw_text or "")
        if not normalized:
            return current_lang or "es"

        explicit_en = (
            "just english sorry",
            "sorry just english",
            "english sorry",
            "english only",
            "speak english",
            "speak in english",
            "i dont speak spanish",
            "i don t speak spanish",
            "i dont talk spanish",
            "i don t talk spanish",
            "no spanish",
            "only english",
            "what is this",
            "sorry what is this",
            "i dont understand",
            "i don t understand",
            "what did you say",
            "what did u say",
            "thats not my business",
            "that s not my business",
            "thats not us",
            "that s not us",
            "wrong business",
            "wrong company",
        )
        explicit_pt = (
            "só portugues",
            "so portugues",
            "falo portugues",
            "nao falo espanhol",
            "não falo espanhol",
        )
        if any(token in normalized for token in explicit_en):
            return "en"
        if any(token in normalized for token in explicit_pt):
            return "pt"

        try:
            detected = multilingual_handler.detect(raw_text) if multilingual_handler else MultilingualHandler().detect(raw_text)
        except Exception:
            detected = "es"

        # Si ya estamos en inglés/portugués, no volver a español por mensajes cortos tipo "ok", "yes", "reset".
        if current_lang in {"en", "pt"} and detected == "es" and len(normalized.split()) <= 6:
            return current_lang
        return detected if detected in {"es", "en", "pt"} else (current_lang or "es")

    owner_lang = _detect_demo_owner_language(text, owner_lang)
    self._demo_sessions[blang_key] = owner_lang

    def _extract_demo_owner_name(raw_text: str, current_name: str = "") -> str:
        raw = (raw_text or "").strip()
        if not raw:
            return current_name or ""

        normalized = _normalize_conv_text(raw)
        if not normalized:
            return current_name or ""

        businessish_markers = (
            "negocio", "empresa", "clinic", "clinica", "clínica", "consultorio",
            "tienda", "salon", "salón", "spa", "business", "company",
            "estamos", "ubicad", "located", "medellin", "medellín", "colombia",
        )
        if any(marker in normalized for marker in businessish_markers):
            return current_name or ""

        patterns = (
            r"(?:mi nombre es|me llamo|soy)\s+([A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚáéíóúÑñ'-]+(?:\s+[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚáéíóúÑñ'-]+){0,2})\b",
            r"(?:my name is|i am|i'm)\s+([A-Z][A-Za-z'-]+(?:\s+[A-Z][A-Za-z'-]+){0,2})\b",
            r"(?:meu nome e|meu nome é|eu sou)\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-Za-zÁÉÍÓÚáéíóúÂÊÔÃÕÇâêôãõç'-]+(?:\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-Za-zÁÉÍÓÚáéíóúÂÊÔÃÕÇâêôãõç'-]+){0,2})\b",
        )
        for pattern in patterns:
            match = re.search(pattern, raw, re.IGNORECASE)
            if not match:
                continue
            candidate = match.group(1).strip(" .,;:!?\"'")
            if not candidate or any(ch.isdigit() for ch in candidate):
                continue
            candidate_norm = _normalize_conv_text(candidate)
            if any(marker in candidate_norm for marker in ("clinica", "clínica", "clinic", "negocio", "empresa", "business", "company")):
                continue
            return candidate
        return current_name or ""

    owner_name = _extract_demo_owner_name(text, owner_name)
    if owner_name:
        self._demo_sessions[bowner_key] = owner_name

    def _lang_text(es_text: str, en_text: str, pt_text: Optional[str] = None) -> str:
        if owner_lang == "en":
            return en_text
        if owner_lang == "pt" and pt_text is not None:
            return pt_text
        return es_text

    # _owner_confusion_or_language_signal is imported from src.domain.onboarding_flow

    def _recent_demo_assistant_text(limit: int = 6) -> str:
        recent = []
        for msg in (history or [])[-limit:]:
            if msg.get("role") == "assistant":
                content = str(msg.get("content") or "").strip()
                if content:
                    recent.append(content)
        return " ||| ".join(recent)

    def _owner_already_knows_ai_identity() -> bool:
        recent_text = _normalize_conv_text(_recent_demo_assistant_text())
        if not recent_text:
            return False
        identity_signals = (
            "soy una ia",
            "soy un bot",
            "asesora virtual",
            "asistente virtual",
        )
        return any(signal in recent_text for signal in identity_signals)

    def _owner_already_got_capability_pitch() -> bool:
        recent_text = _normalize_conv_text(_recent_demo_assistant_text())
        if not recent_text:
            return False
        capability_signals = (
            "respondo clientes",
            "filtro interesados",
            "filtro leads",
            "ayudo con citas",
            "manejo whatsapp",
            "llevo el chat",
            "creo agentes",
            "ventas o soporte",
        )
        return any(signal in recent_text for signal in capability_signals)

    def _looks_like_customer_greeting(raw_text: str) -> bool:
        normalized = _normalize_conv_text(raw_text or "")
        if not normalized:
            return False
        if _is_greeting_only(raw_text):
            return True
        greeting_prefixes = (
            "hola", "hola buenas", "buenas", "buenas tardes", "buenos dias", "buenos días",
            "buenas noches", "hey", "holi", "hi", "hello",
            "good morning", "good afternoon", "good evening",
        )
        return any(
            normalized == prefix or normalized.startswith(prefix + " ")
            for prefix in greeting_prefixes
        )

    def _save(role, msg):
        if db:
            try:
                db.save_message(chat_id, role, msg.replace("|||", " "))
            except Exception:
                pass

    # ── SEND GUARD — pitch inteligente + fix de cortes ──────────────────
    _guard = None
    if _BLACKONE_PATCHES:
        try:
            _guard = SendGuard(context="demo", business_name=business_name)
        except Exception:
            _guard = None

    # Smart handoff proactivo ANTES del LLM (prospecto quiere hablar con humano)
    if _BLACKONE_PATCHES and _guard:
        try:
            _proactive = _guard.check_handoff(text, history)
            if _proactive and _SMART_HANDOFF and handoff_manager:
                _save("user", text)
                _save("assistant", _proactive["suggested_reply"])
                return _send(_proactive["suggested_reply"])
        except Exception:
            pass
    # ──────────────────────────────────────────────────────────────────────

    def _send(r):
        _demo_archetype = self._demo_sessions.get(btone_key + "_arch", "amigable")
        # BUG FIX: En DEMO_MODE, usar DEMO_BUSINESS_NAME como fallback
        _demo_name = business_name if business_name else (Config.DEMO_BUSINESS_NAME if Config.DEMO_MODE else clinic.get("name", ""))
        _demo_clinic = self._build_demo_patient_clinic(
            {
                **clinic,
                "name": _demo_name,
                "sector": clinic.get("sector") or Config.DEMO_SECTOR,
            }
        )
        _is_first_demo_turn = not any(m.get("role") == "assistant" for m in history)
        # Fix Black One / BlackBoss + cortes ANTES de procesar
        if _BLACKONE_PATCHES:
            try:
                if _guard and business_name:
                    _guard.business_name = business_name
                r = fix_creator_in_response(r)
                r = _guard.clean(r) if _guard else r
            except Exception:
                pass
        r = v8_process_response(r, chat_id=chat_id, archetype=_demo_archetype)
        should_normalize_first_turn = _is_first_demo_turn and self._demo_should_use_patient_chat_path(text)
        if should_normalize_first_turn:
            r = _normalize_first_contact_response(
                r,
                _demo_clinic,
                text,
                agent_name="Conny",
            )
        _save("assistant", r)
        bubbles = self._split_bubbles(r, chat_id=chat_id, archetype=_demo_archetype)
        if should_normalize_first_turn and len(bubbles) == 1:
            _text_norm = _normalize_conv_text(text or "")
            _greeting_tokens = (
                "hola", "buenas", "buenas tardes", "buenos dias", "buenos días",
                "buenas noches", "hey", "holi", "hi", "hello",
                "good morning", "good afternoon", "good evening",
            )
            if any(_text_norm == token or _text_norm.startswith(token + " ") for token in _greeting_tokens):
                lowered_bubble = _normalize_conv_text(bubbles[0] or "")
                if not any(token in lowered_bubble for token in ("cuentame", "cuéntame", "revisar", "ayudo", "ayudar")):
                    bubbles.append(_lang_text("cuéntame qué te gustaría revisar", "what would you like to check?"))
        tone = self._demo_sessions.get(btone_key, "GENERAL")
        if tone in ("SALUD PREMIUM", "PREMIUM"):
            bubbles = [b[0].upper() + b[1:] if b else b for b in bubbles]
        # v11: primera burbuja siempre con mayúscula inicial
        if bubbles:
            bubbles[0] = bubbles[0][0].upper() + bubbles[0][1:] if bubbles[0] else bubbles[0]
        return bubbles

    def _normalize_demo_owner_onboarding_response(raw_response: str) -> str:
        parts = [part.strip() for part in re.split(r"\s*\|\|\|\s*", raw_response or "") if part.strip()]
        if not parts:
            return raw_response
        user_norm = _normalize_conv_text(text or "")
        greeted = any(
            user_norm == token or user_norm.startswith(token + " ")
            for token in (
                "hola", "hola buenas", "buenas", "buenas tardes",
                "buenas noches", "buenos dias", "buenos días", "hey", "holi",
                "hi", "hello", "good morning", "good afternoon", "good evening",
            )
        )
        if greeted:
            first_norm = _normalize_conv_text(parts[0])
            if first_norm.startswith("soy conny"):
                parts[0] = "hola, " + parts[0][0].lower() + parts[0][1:]
            elif first_norm.startswith("conny, "):
                parts[0] = "hola, " + parts[0][0].lower() + parts[0][1:]
            elif first_norm.startswith("i am conny") or first_norm.startswith("im conny") or first_norm.startswith("i'm conny"):
                parts[0] = "hi, " + parts[0][0].lower() + parts[0][1:]
        return " ||| ".join(parts)

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

    # _looks_like_business_confirmation is imported from src.domain.onboarding_flow

    def _extract_followup_after_business_confirmation(raw_text: str) -> str:
        normalized = _normalize_conv_text(raw_text or "")
        if not normalized:
            return ""
        for signal in sorted(_business_confirmation_signals, key=len, reverse=True):
            signal_norm = _normalize_conv_text(signal)
            if not signal_norm or signal_norm not in normalized:
                continue
            suffix = normalized.split(signal_norm, 1)[1].strip(" ,.!?;:")
            if suffix:
                return suffix
        return ""

    def _owner_is_english() -> bool:
        return owner_lang == "en"

    def _owner_is_portuguese() -> bool:
        return owner_lang == "pt"

    _force_business_bind = any(
        marker in _normalize_conv_text(text or "")
        for marker in (
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
        )
    )

    # ── FIX v10: Reset check ANTES del conversation core ─────────────────────
    # Bug v9: _try_conversation_core corría primero y el LLM recibía "reset"
    # como mensaje normal → generaba respuestas incoherentes ("Hoy?", etc.)
    _reset_words = [
        "reset", "reiniciar", "empezar de nuevo", "volver a empezar",
        "borralo", "otro negocio", "cambia el negocio", "cambia negocio",
        "cambiar negocio", "ese no es mi negocio", "no es mi negocio",
        "equivoque", "equivocado",
    ]
    if any(rw in text.lower() for rw in _reset_words):
        keys_del = [k for k in list(self._demo_sessions)
                    if k.startswith(sk + "_") and not k.endswith("_ts")]
        for k in keys_del:
            del self._demo_sessions[k]
        try:
            with db._conn() as c:
                c.execute("DELETE FROM conversations WHERE chat_id=?", (chat_id,))
        except Exception:
            pass
        _save("user", text)
        import random as _rr
        _reset_replies = [
            "listo, empezamos de cero ||| con qué negocio trabajo?",
            "borrado todo ||| cuéntame: cómo se llama el negocio",
            "ok, borrón y cuenta nueva ||| nombre del negocio?",
            "listo ||| dime el nombre del negocio y arrancamos",
        ]
        if _owner_is_english():
            _reset_replies = [
                "all set, starting from scratch ||| what business am I working with?",
                "cleared everything ||| tell me the name of your business",
                "ok, fresh start ||| what's the name of the business?",
                "ready ||| send me the business name and I’ll start from there",
            ]
        elif _owner_is_portuguese():
            _reset_replies = [
                "pronto, começamos do zero ||| com qual negócio eu trabalho?",
                "apaguei tudo ||| me diz o nome do negócio",
                "ok, recomeçando ||| qual é o nome do negócio?",
                "certo ||| me passa o nome do negócio e eu começo",
            ]
        return _send(_rr.choice(_reset_replies))
    # ─────────────────────────────────────────────────────────────────────────

    demo_channel = ""
    try:
        demo_channel = str(self._resolve_route(chat_id).get("platform") or Config.PLATFORM or "")
    except Exception:
        demo_channel = str(Config.PLATFORM or "")

    _pre_text_low = text.lower().strip()

    # ── PITCH INTELIGENTE — prospecto B2B confundido ─────────────────────
    if _BLACKONE_PATCHES:
        try:
            _pitch_blockers = (
                "para que", "para qué", "por que", "por qué",
                "why do you need", "why do you need it",
            )
            if is_prospect_confused(text, history) and not any(blocker in _pre_text_low for blocker in _pitch_blockers):
                self._demo_sessions[sk + "_pitch_mode"] = True
            # BUG FIX: forzar pitch para preguntas específicas que is_prospect_confused no detecta
            elif any(q in text.lower() for q in ("que harias", "qué harías", "que harias en", "qué harías en")):
                self._demo_sessions[sk + "_pitch_mode"] = True
            else:
                self._demo_sessions.pop(sk + "_pitch_mode", None)
        except Exception:
            pass
    # ─────────────────────────────────────────────────────────────────────

    _pre_core_blockers = (
        "hagamos una demo",
        "hagamos la demo",
        "hagamos una simul",
        "vale hagamos",
        "arranquemos la demo",
        "arranquemos",
        "simulemos",
        "quien eres",
        "quién eres",
        "que eres",
        "qué eres",
        "que haces",
        "qué haces",
        "como funcionas",
        "cómo funcionas",
        "para que",
        "para qué",
        "por que",
        "por qué",
        "quien te hizo",
        "quién te hizo",
        "como tenerte",
        "cómo tenerte",
        "aceptas audios",
        "aceptas pdf",
        "me mandaron tu numero",
        "me mandaron tu número",
        "what is this",
        "what do you do",
        "who are you",
        "i dont understand",
        "i don't understand",
        "english only",
        "i dont talk spanish",
        "i don't talk spanish",
    )

    # PATCH P3 — conversation_core solo cuando el negocio ya está cargado.
    # Sin business_name, el core usa contexto de la clínica real → T4 identidad errónea.
    demo_core_bubbles = None
    if (
        business_name
        and not sim_mode_active
        and not self._demo_should_use_patient_chat_path(text)
        and not _pre_text_low.startswith("/")
        and not any(marker in _pre_text_low for marker in _pre_core_blockers)
        and not llm_runtime_ready
    ):
        demo_core_bubbles = self._try_conversation_core(
            clinic={
                **clinic,
                "name": business_name,
                "sector": self._demo_sessions.get(btone_key, Config.DEMO_SECTOR),
            },
            user_msg=text,
            history=history,
            is_admin=False,
            channel=demo_channel,
        )
    if demo_core_bubbles:
        _save("user", text)
        demo_response = " ||| ".join(demo_core_bubbles)
        _demo_archetype = self._demo_sessions.get(btone_key + "_arch", "amigable")
        demo_response = v8_process_response(demo_response, chat_id=chat_id, archetype=_demo_archetype)
        _save("assistant", demo_response)
        return self._split_bubbles(demo_response, chat_id=chat_id, archetype=_demo_archetype)

    # ── Normalizar texto y detectar comandos ──────────────────────────────
    text_norm = text.strip().lower().lstrip("/")
    cmd_aliases = {
        "formal":"formal","amigable":"amigable","luxury":"luxury","lujo":"luxury",
        "directa":"directa","energica":"energica","enérgica":"energica",
        "empatica":"empatica","empática":"empatica","experta":"experta",
        "juvenil":"juvenil","joven":"juvenil","profesional":"formal","objecion":"objecion","objeción":"objecion",
        "cita":"cita","agendar":"cita","stats":"stats","estadisticas":"stats",
        "prueba":"prueba","reto":"prueba","cierre":"cierre","bot":"bot",
        "memoria":"memoria","recuerdas":"memoria","2am":"2am","de noche":"2am",
        "competencia":"competencia","precio":"precio","caro":"precio",
        "siguiente":"siguiente","que mas":"siguiente","qué más":"siguiente",
        "menu":"menu_bot","menú":"menu_bot","modo bot":"menu_bot","bot menu":"menu_bot",
        # Lista de comandos
        "list":"list","lista":"list","comandos":"list","ayuda":"list","help":"list","qué puedes hacer":"list","que puedes hacer":"list",
        # Emojis on/off
        "emojis":"emojis_on","con emojis":"emojis_on","activa emojis":"emojis_on",
        "sin emojis":"emojis_off","quita emojis":"emojis_off","desactiva emojis":"emojis_off",
        # Selección de modelo — /modelo o texto libre
        "modelo":"modelo","model":"modelo","cambiar modelo":"modelo",
    }

    # Detección natural de emojis en texto libre
    _emoji_on_signals  = [
        "usa emojis","ponle emojis","escribe con emojis",
        "activa los emojis","quiero emojis","pon emojis",
        "enviame emojis","envíame emojis","mándame emojis",
        "mandame emojis","con emojis","agrega emojis","añade emojis",
    ]
    _emoji_off_signals = [
        "sin emojis","quita los emojis","sin tanto emoji","sin esos emojis",
        "desactiva emojis","no más emojis","no me mandes emojis",
        "no uses emojis","no pongas emojis","sin caritas","sin los emojis",
        "quitale los emojis","no me envies emojis","no me envíes emojis",
    ]
    if any(s in text_norm for s in _emoji_on_signals):
        self._emoji_chats_off.discard(chat_id)  # v11: re-activar emojis
        _save("user", text)
        _biz_hint = f" en {business_name}" if business_name else ""
        return _send(f"listo, ahora escribo con emojis 😊 ||| sigue hablándome como si fueras un cliente{_biz_hint}")
    if any(s in text_norm for s in _emoji_off_signals):
        self._emoji_chats_off.add(chat_id)  # v11: desactivar emojis
        _save("user", text)
        _biz_hint = f" en {business_name}" if business_name else ""
        return _send(f"listo, sin emojis ||| sigue hablándome como si fueras un cliente{_biz_hint}")

    detected_cmd = None
    model_request = extract_model_request_from_text(text_norm)
    if model_request:
        detected_cmd = "/modelo"
    for alias, cmd in cmd_aliases.items():
        if text_norm == alias or text_norm == "/" + alias:
            detected_cmd = "/" + cmd
            break

    # ── Motor LLM según preferencia de sesión ────────────────────────────
    def _get_demo_engine():
        """
        Devuelve el proveedor LLM según demo_model_pref.
        Formatos soportados:
          auto                    → engine global
          gemini                  → GeminiProvider con gemini-2.5-flash
          gemini:gemini-2.5-pro   → GeminiProvider con modelo específico
          groq                    → GroqProvider con llama-3.3-70b-versatile
          groq:llama-3.1-8b-instant → GroqProvider con modelo específico
          openrouter              → OpenRouterProvider
          openrouter:anthropic/claude-sonnet-4 → OpenRouter con modelo específico
        """
        pref = self._demo_sessions.get(bmodel_key, "auto")

        if ":" in pref:
            provider, model_name = pref.split(":", 1)
        else:
            provider, model_name = pref, None

        if provider == "groq" and Config.GROQ_API_KEY:
            eng = GroqProvider(Config.GROQ_API_KEY)
            if model_name:
                # Override el modelo específico
                eng.MDLS = {"reasoning": model_name, "fast": model_name, "lite": model_name}
            return eng

        elif provider == "gemini":
            key = Config.GEMINI_API_KEY or Config.GEMINI_API_KEY_2 or Config.GEMINI_API_KEY_3
            if key:
                eng = GeminiProvider(key, "gemini_demo")
                if model_name:
                    eng.MDLS = {"reasoning": model_name, "fast": model_name, "lite": model_name}
                else:
                    # Default: 2.5-flash estable
                    eng.MDLS = {"reasoning": "gemini-2.5-flash", "fast": "gemini-2.5-flash", "lite": "gemini-2.5-flash-lite"}
                return eng
            # Fallback a OpenRouter con gemini
            if Config.OPENROUTER_API_KEY:
                eng = OpenRouterProvider(Config.OPENROUTER_API_KEY)
                m = model_name or "google/gemini-2.5-flash"
                eng.MDLS = {"reasoning": m, "fast": m, "lite": m}
                return eng

        elif provider == "openrouter" and Config.OPENROUTER_API_KEY:
            eng = OpenRouterProvider(Config.OPENROUTER_API_KEY)
            if model_name:
                eng.MDLS = {"reasoning": model_name, "fast": model_name, "lite": model_name}
            return eng

        # auto: engine global
        _generator = getattr(self, "generator", None)
        return llm_engine or (_generator.llm if _generator else None)

    # ── Helpers locales ───────────────────────────────────────────────────
    async def _llm(sys_p, usr_p, temp=0.82, max_t=8192, model_tier="fast"):  # Sin límite — Gemini 2.5 soporta hasta 65k output tokens
        msgs = [{"role":"system","content":sys_p},{"role":"user","content":usr_p}]
        try:
            eng = _get_demo_engine()
            if not eng: raise RuntimeError("LLM no init")
            r, meta = await eng.complete(
                msgs,
                model_tier=model_tier,
                temperature=temp,
                max_tokens=max_t,
                use_cache=False,
            )
            log.info(f"[demo] {meta.get('provider','?')} model={meta.get('model','?')[:30]}")
            _generator = getattr(self, "generator", None)
            return _generator._postprocess(r, PersonalityProfile()) if _generator else r
        except Exception as e:
            log.error(f"[demo] llm error: {e}")
            return None

    async def _llm_classify_business_name(raw_text: str) -> Tuple[bool, Optional[str]]:
        return await llm_classify_business_name(raw_text, _get_demo_engine())

    async def _llm_conv_pitch(temp=0.85, max_t=8192, recent_limit=12):
        """LLM con el pitch de Black One para prospectos confundidos."""
        try:
            pitch_sys = build_prospect_pitch_system_prompt(business_name)
        except Exception:
            return None
        msgs = [{"role": "system", "content": pitch_sys}]
        for m in history[-recent_limit:]:
            msgs.append({"role": m["role"], "content": m["content"]})
        msgs.append({"role": "user", "content": text})
        try:
            eng = _get_demo_engine()
            if not eng: raise RuntimeError("LLM no init")
            r, meta = await eng.complete(msgs, model_tier="fast", temperature=temp, max_tokens=max_t, use_cache=False)
            log.info(f"[demo][pitch] {meta.get('provider','?')}")
            _generator = getattr(self, "generator", None)
            return _generator._postprocess(r, PersonalityProfile()) if _generator else r
        except Exception as e:
            log.error(f"[demo][pitch] error: {e}")
            return None

    async def _llm_conv(sys_p, temp=0.85, max_t=8192, model_tier="fast", recent_limit=12):  # Sin límite — Gemini 2.5 soporta hasta 65k output tokens
        msgs = [{"role":"system","content":sys_p}]
        for m in history[-recent_limit:]:
            msgs.append({"role":m["role"],"content":m["content"]})
        msgs.append({"role":"user","content":text})
        try:
            eng = _get_demo_engine()
            if not eng: raise RuntimeError("LLM no init")
            r, meta = await eng.complete(
                msgs,
                model_tier=model_tier,
                temperature=temp,
                max_tokens=max_t,
                use_cache=False,
            )
            log.info(f"[demo] {meta.get('provider','?')} model={meta.get('model','?')[:30]}")
            _generator = getattr(self, "generator", None)
            return _generator._postprocess(r, PersonalityProfile()) if _generator else r
        except Exception as e:
            log.error(f"[demo] llm_conv error: {e}")
            return None

    async def _demo_llm_conv_quality_chain(
        system_prompt: str,
        *,
        validator,
        repair_instructions: str,
        temp: float = 0.72,
        max_t: int = 8192,  # Sin límite — Gemini 2.5 necesita espacio para pensar
        model_tier: str = "fast",
        recent_limit: int = 8,
    ) -> Tuple[Optional[str], bool]:
        _chain_start = time.time()
        _CHAIN_TIMEOUT_S = 45  # si pasaron más de 45s entre intentos, no enviar respuesta vieja
        attempts = [
            (system_prompt, temp, max_t, model_tier, recent_limit),
            (
                system_prompt
                + "\n\nREPARA LA RESPUESTA:\n"
                + repair_instructions.strip()
                + "\n- no repitas introducciones\n- no suenes a bot ni a guion de demo",
                0.58,
                max_t,
                "reasoning",
                recent_limit,
            ),
        ]
        had_output = False
        last_candidate = None
        for prompt_now, temp_now, max_now, tier_now, limit_now in attempts:
            # No lanzar repair si ya pasó demasiado tiempo desde que llegó el mensaje
            if time.time() - _chain_start > _CHAIN_TIMEOUT_S:
                log.warning("[demo] conv_quality_chain abortada por timeout (%ds)", _CHAIN_TIMEOUT_S)
                break
            candidate = await _llm_conv(
                prompt_now,
                temp=temp_now,
                max_t=max_now,
                model_tier=tier_now,
                recent_limit=limit_now,
            )
            if candidate and candidate.strip():
                had_output = True
                last_candidate = candidate
                if not validator(candidate):
                    return candidate, True
        if had_output and last_candidate and not looks_fragmented_reply(last_candidate):
            candidate_norm = _normalize_conv_text(last_candidate)
            if len(candidate_norm.split()) >= 5 and not validator(last_candidate):
                return last_candidate, True
        return None, had_output

    def _save(role, msg):
        if db:
            try: db.save_message(chat_id, role, msg.replace("|||"," "))
            except Exception: pass

    def _send(r):
        # V8.0: aplicar AntiRobotFilter antes de guardar y enviar
        _demo_archetype = self._demo_sessions.get(btone_key + "_arch", "amigable")
        # BUG FIX: En DEMO_MODE, usar DEMO_BUSINESS_NAME como fallback
        _demo_name = business_name if business_name else (Config.DEMO_BUSINESS_NAME if Config.DEMO_MODE else clinic.get("name", ""))
        _demo_clinic = self._build_demo_patient_clinic(
            {
                **clinic,
                "name": _demo_name,
                "sector": clinic.get("sector") or Config.DEMO_SECTOR,
            }
        )
        _is_first_demo_turn = not any(m.get("role") == "assistant" for m in history)
        # ── BLACK ONE: fix Black One + cortes antes de procesar ──────────
        if _BLACKONE_PATCHES:
            try:
                if _guard and business_name:
                    _guard.business_name = business_name
                r = fix_creator_in_response(r)
                if _guard:
                    r = _guard.clean(r)
            except Exception:
                pass
        # ─────────────────────────────────────────────────────────────────
        r = v8_process_response(r, chat_id=chat_id, archetype=_demo_archetype)
        should_normalize_first_turn = _is_first_demo_turn and self._demo_should_use_patient_chat_path(text)
        if should_normalize_first_turn:
            r = _normalize_first_contact_response(
                r,
                _demo_clinic,
                text,
                agent_name="Conny",
            )
        _save("assistant", r)
        bubbles = self._split_bubbles(r, chat_id=chat_id, archetype=_demo_archetype)
        # FIX BUG 4: Si es el primer turno, el usuario saludó, y la respuesta tiene
        # solo 1 burbuja sin pregunta de seguimiento → agregar burbuja de apertura.
        # Esta lógica existía en la primera definición de _send (línea 13772) pero
        # se perdió cuando se redefinió _send aquí en la misma función.
        if should_normalize_first_turn and len(bubbles) == 1:
            _text_norm = _normalize_conv_text(text or "")
            _greeting_tokens = (
                "hola", "buenas", "buenas tardes", "buenos dias", "buenos días",
                "buenas noches", "hey", "holi",
            )
            if any(_text_norm == token or _text_norm.startswith(token + " ") for token in _greeting_tokens):
                lowered_bubble = _normalize_conv_text(bubbles[0] or "")
                if not any(token in lowered_bubble for token in ("cuentame", "cuéntame", "revisar", "ayudo", "ayudar")):
                    bubbles.append("cuéntame qué te gustaría revisar")
        # Para premium/salud premium: restaurar mayúscula inicial
        tone = self._demo_sessions.get(btone_key, "GENERAL")
        if tone in ("SALUD PREMIUM", "PREMIUM"):
            bubbles = [b[0].upper() + b[1:] if b else b for b in bubbles]
        # v11: primera burbuja siempre con mayúscula inicial
        if bubbles:
            bubbles[0] = bubbles[0][0].upper() + bubbles[0][1:] if bubbles[0] else bubbles[0]
        return bubbles

    # _looks_like_business_name_candidate_legacy is imported from src.domain.onboarding_flow

    def _demo_owner_reply_is_low_quality(raw_response: Optional[str]) -> bool:
        lowered = _normalize_conv_text(raw_response or "")
        if not lowered:
            return True
        if looks_fragmented_reply(raw_response or ""):
            return True
        parts = [part.strip() for part in re.split(r"\s*\|\|\|\s*|\n+", raw_response or "") if part.strip()]
        weak_parts = {
            "hola", "buenas", "claro", "dale", "listo", "sí", "si",
            "puedes", "perfecto", "entiendo", "ok", "keep going",
        }
        if any(_normalize_conv_text(part) in weak_parts for part in parts):
            return True
        if any(looks_fragmented_reply(part) for part in parts):
            return True
        safe_tail_words = {"hoy", "ahi", "ahí", "bien", "vale", "listo", "claro"}
        for part in parts:
            norm_part = _normalize_conv_text(part)
            words = norm_part.split()
            if len(words) >= 3 and len(words[-1]) <= 3 and words[-1] not in safe_tail_words:
                return True
        banned = (
            "nova",
            "clinica de las americas",
            "clínica de las américas",
            "retomamos desde donde lo dejamos",
            "seguimos con la demo",
            "cuenteme que quiere ajustar",
            "cuénteme qué quiere ajustar",
            "estoy lista para ayudarte con la instancia",
            "de manera adecuada",
            "me permitira",
            "me permitirá",
            "ofrecer una mejor experiencia",
            "a tus necesidades",
            "a las de tus clientes",
            "de manera efectiva",
            "para poder hacer esto",
            "por favor",
            "proceder",
            "precisa y personalizada",
            "interactuas con nuestros servicios",
            "interactúas con nuestros servicios",
            "de manera mas precisa",
            "de manera más precisa",
            "escribidme",
            "vuestra",
            "vuestro",
            "vosotros",
            "ayudaros",
            "parece ser un lugar confiable",
            "me gustaria saber mas sobre sus servicios",
            "me gustaría saber más sobre sus servicios",
            "de manera clara y concisa",
            "atencion que brindan",
            "atención que brindan",
            "por favor escriban",
            "quiero ver como interactuan",
            "quiero ver cómo interactúan",
            "pueden comenzar a escribir su consulta",
            # ── Frases que rompen el personaje (v10 fix) ──────────────────
            "no se cual es el negocio",
            "no sé cuál es el negocio",
            "hay confusion",
            "hay confusión",
            "me doy cuenta de que",
            "mi funcion es",
            "mi función es",
            "aqui lo que hago es",
            "aquí lo que hago es",
            "soy una persona que responde",
            "la idea es que yo me encargue",
            "la que llevaria el chat de tu negocio",
            "la que llevaría el chat de tu negocio",
            "hola pues mira",
            "soy una ia",
            "soy un bot",
            "soy chatgpt",
            "soy un asistente virtual",
            "soy una asistente virtual",
            "como asistente",
            "como ia",
            "como bot",
        )
        if any(token in lowered for token in banned):
            return True
        if lowered in {
            "hola",
            "buenas",
            "soy conny",
            "hola soy conny",
            "como se llama tu negocio",
            "cómo se llama tu negocio",
        }:
            return True
        return False

    def _demo_owner_missing_required_detail(user_text: str, raw_response: Optional[str]) -> bool:
        lowered_user = _normalize_conv_text(user_text or "")
        lowered_response = _normalize_conv_text(raw_response or "")
        if not lowered_response:
            return True
        if any(token in lowered_user for token in ("para que", "para qué", "por que", "por qué")):
            detail_tokens = ("chat", "cliente", "demo", "tono", "responder", "whatsapp")
            return not any(token in lowered_response for token in detail_tokens)
        if any(token in lowered_user for token in ("quien te hizo", "quién te hizo", "como tenerte", "cómo tenerte", "quien te creo", "quién te creó")):
            return "black one" not in lowered_response or "3124348669" not in lowered_response
        if any(token in lowered_user for token in ("audio", "audios", "nota de voz", "pdf", "archivo", "documento", "imagen")):
            return not any(token in lowered_response for token in ("audio", "pdf", "documento", "imagen", "transcrib"))
        if any(token in lowered_user for token in ("me mandaron tu numero", "me mandaron tu número", "me pasaron tu numero", "me pasaron tu número", "que haces exactamente", "qué haces exactamente", "no entiendo que haces", "no entiendo qué haces")):
            capability_tokens = ("cliente", "clientes", "cita", "citas", "respon", "orient", "filtro", "report")
            return not any(token in lowered_response for token in capability_tokens)
        if any(token in lowered_user for token in ("esto es real", "modo bot", "como llevarias", "cómo llevarías", "como responderias", "cómo responderías")):
            operational_tokens = ("chat", "cliente", "clientes", "tono", "lead", "leads", "ventas", "soporte", "respon", "whatsapp")
            return not any(token in lowered_response for token in operational_tokens)
        if "5 x 4" in lowered_user or "5x4" in lowered_user:
            return "20" not in lowered_response
        if "capital de francia" in lowered_user:
            return "par" not in lowered_response
        return False

    def _demo_owner_reground_needs_cleanup(raw_response: Optional[str]) -> bool:
        lowered = _normalize_conv_text(raw_response or "")
        if not lowered:
            return True
        parts = [part.strip() for part in re.split(r"\s*\|\|\|\s*|\n+", raw_response or "") if part.strip()]
        if len(parts) > 2:
            return True
        low_signal_phrases = (
            "me gustaria saber",
            "me gustaría saber",
            "tienes alguna consulta",
            "necesitas ayuda con algo",
            "de la mejor manera",
            "puedes escribirme como si fuera un cliente",
            "puedo tener una idea clara",
            "de manera adecuada",
            "ofrecer una mejor experiencia",
            "como si fuera un cliente real, hoy",
            "como si fuera un cliente real hoy",
        )
        return any(token in lowered for token in low_signal_phrases)

    def _demo_customer_reply_is_low_quality(raw_response: Optional[str]) -> bool:
        lowered = _normalize_conv_text(raw_response or "")
        raw_text = (raw_response or "").strip().lower()
        if not lowered:
            return True
        if looks_fragmented_reply(raw_response or ""):
            return True
        parts = [part.strip() for part in re.split(r"\s*\|\|\|\s*|\n+", raw_response or "") if part.strip()]
        if any(looks_fragmented_reply(part) for part in parts):
            return True
        if re.search(r"(?:[.!?]\s*)(hoy|y tu|y tú|que mas|qué más)\??$", raw_text):
            return True
        safe_tail_words = {"hoy", "ahi", "ahí", "bien", "vale", "listo", "claro", "ti", "aqui", "aquí"}
        for part in parts:
            norm_part = _normalize_conv_text(part)
            words = norm_part.split()
            if len(words) <= 2 and any(token in norm_part for token in ("hoy", "y tu", "y tú", "que mas", "qué más")):
                return True
            if len(words) <= 2 and part.strip().endswith("?"):
                return True
            if len(words) >= 3 and len(words[-1]) <= 2 and words[-1] not in safe_tail_words:
                return True
        bad_markers = (
            "hola que necesitas",
            "hola, que necesitas",
            "cuentame un poco mas y te voy guiando",
            "cuéntame un poco más y te voy guiando",
            "por favor procedan",
            "de manera efectiva",
            "simular la interaccion",
            "simular la interacción",
            "cliente real de",
            "estoy lista para empezar",
            "como si fueran un cliente real",
            "soy conny, la asesora virtual de",
            "escribidme",
            "vuestra",
            "vuestro",
            "vosotros",
            "ayudaros",
            "parece ser un lugar confiable",
            "quiero ver como interactuan",
            "quiero ver cómo interactúan",
            "pueden comenzar a escribir su consulta",
        )
        return any(marker in lowered for marker in bad_markers)

    def _demo_customer_missing_required_detail(user_text: str, raw_response: Optional[str]) -> bool:
        lowered_user = _normalize_conv_text(user_text or "")
        lowered_resp = _normalize_conv_text(raw_response or "")
        if not lowered_resp:
            return True
        if lowered_user in {"hola", "hola buenas", "buenas", "buenas tardes", "buenos dias", "buenos días", "buenas noches", "hey"}:
            if not any(token in lowered_resp for token in ("hola", "buenas", "bienvenida", "bienvenido", "cuentame", "cuéntame", "revisar", "ayudo", "ayudar")):
                return True
        if any(token in lowered_user for token in ("precio", "cuanto", "cuánto", "vale", "costo", "coste")):
            if not any(token in lowered_resp for token in ("precio", "cuesta", "valor", "dato", "confirmo", "averiguo", "depende")):
                return True
            if not found_online and any(token in lowered_resp for token in ("aproximado", "aproximada", "aprox", "rango", "desde")):
                return True
        if any(token in lowered_user for token in ("cita", "agendar", "agenda", "seguimos", "siguiente paso", "como seguimos", "cómo seguimos")):
            if not any(token in lowered_resp for token in ("cita", "agendo", "agenda", "hora", "horario", "nombre", "confirmo", "paso")):
                return True
            if any(token in lowered_resp for token in ("link", "enlace", "seleccionar una fecha", "seleccionar fecha", "calendario")):
                return True
        if any(token in lowered_user for token in ("audio", "audios", "nota de voz", "pdf", "archivo", "documento", "documentos", "imagen", "imagenes", "imágenes")):
            if not any(token in lowered_resp for token in ("audio", "voz", "pdf", "documento", "imagen", "transcrib", "leer")):
                return True
        if "miedo" in lowered_user:
            if not any(token in lowered_resp for token in ("miedo", "normal", "natural", "conservador", "suave")):
                return True
        return False

    def _demo_customer_last_resort(user_text: str) -> str:
        """
        Fallback REAL — solo cuando TODOS los modelos LLM fallan en simulación.
        No intenta ser inteligente. El LLM maneja todo lo demás.
        """
        _biz = business_name or "el negocio"
        _user = _normalize_conv_text(user_text or "")
        if any(token in _user for token in ("cita", "agendar", "agenda", "valoracion", "valoración", "horario", "disponibilidad")):
            return (
                f"si quieres seguimos con el siguiente paso para agendar en {_biz}"
                " ||| dime tu nombre y el horario que mejor te quede"
            )
        if any(token in _user for token in ("precio", "cuesta", "vale", "coste", "cuanto", "cuánto")):
            return (
                f"te puedo ubicar con el precio o la valoración de {_biz}"
                " ||| dime qué tratamiento estás mirando"
            )
        if any(token in _user for token in ("miedo", "asusta", "nerv", "exagerad", "natural")):
            return (
                f"en {_biz} lo normal es arrancar viendo qué resultado quieres"
                " ||| qué es lo que más te preocupa"
            )
        if any(token in _user for token in ("audio", "audios", "nota de voz", "pdf", "archivo", "documento", "documentos", "imagen", "imagenes", "imágenes")):
            return (
                "sí, por aquí puedo trabajar con audios, imágenes y documentos"
                " ||| si quieres, mándamelo y sigo desde ahí"
            )
        return f"cuéntame qué necesitas de {_biz}"

    async def _demo_llm_quality_chain(
        system_prompt: str,
        user_prompt: str,
        *,
        validator,
        repair_instructions: str,
        temp: float = 0.76,
        max_t: int = 8192,  # Sin límite — Pro necesita tokens para reasoning
        model_tier: str = "reasoning",
    ) -> Tuple[Optional[str], bool]:
        attempts = [
            (system_prompt, temp, max_t, model_tier),
            (
                system_prompt
                + "\n\nREPARA LA RESPUESTA:\n"
                + repair_instructions.strip()
                + "\n- responde mejor, pero sin cambiar de tema\n- no uses frases corporativas ni consultoras",
                0.62,
                max_t,
                "reasoning",
            ),
            (
                system_prompt
                + "\n\nRESPUESTA FINAL OBLIGATORIA:\n"
                + repair_instructions.strip()
                + "\n- entrega una versión final limpia, concreta y humana\n- no salgas por la tangente\n- no recites instrucciones",
                0.45,
                max(max_t, 260),
                "reasoning",
            ),
        ]
        had_output = False
        for prompt_now, temp_now, max_now, tier_now in attempts:
            candidate = await _llm(
                prompt_now,
                user_prompt,
                temp=temp_now,
                max_t=max_now,
                model_tier=tier_now,
            )
            if candidate and candidate.strip():
                had_output = True
                if not validator(candidate):
                    return candidate, True
        return None, had_output



    async def _demo_owner_onboarding_reply(*, explain_name: bool = False, force_stage: Optional[str] = None) -> List[str]:
        user_block = text
        already_disclosed_ai = _owner_already_knows_ai_identity()
        already_explained_capabilities = _owner_already_got_capability_pitch()
        recent_assistant_context = _recent_demo_assistant_text(limit=4)
        if False and _CONNY_DOMINO_AVAILABLE:  # Disabled: using improved prompt v10
            try:
                domino_payload = build_demo_domino_payload(
                    user_text=text,
                    history=history,
                    business_name=business_name,
                    business_ctx=business_ctx,
                    found_online=found_online,
                    explain_name=explain_name,
                    force_stage=force_stage,
                )
                system_prompt = domino_payload["system"]
                user_block = domino_payload["user"]
            except Exception as e:
                log.warning(f"[demo] domino payload error: {e}")
                system_prompt = ""
        else:
            system_prompt = ""

        if not system_prompt:
            system_prompt = f"""Eres Conny, una colombiana de 28 años que trabaja como recepcionista virtual por WhatsApp.
Estás en una demo con un posible cliente (dueño de negocio). Tu trabajo: que se enamore de ti en 5 minutos.

CÓMO SUENAS: como una persona real de Medellín escribiendo en WhatsApp.
- Mensajes cortos, partidos en 2-3 burbujas usando ||| como separador.
- Sin puntuación perfecta (como escribe alguien real en WhatsApp).
- Escribe de forma informal: puedes empezar las burbujas o frases en minúsculas. NO uses mayúscula obligatoria en cada frase.
- NO uses signos de apertura (¿ ni ¡) y NUNCA uses punto final al terminar las burbujas o frases sueltas (ej. escribe "hola cómo vas" en vez de "Hola, ¿cómo vas?").
- Evita totalmente explicaciones largas o introducciones robóticas como "básicamente", "como tal", "mi función es", "soy una inteligencia artificial". Habla directo, como compañera de trabajo.
- Si te hablan en inglés, respondes en inglés perfecto, súper casual y natural de WhatsApp.

TU ESTRATEGIA DE DEMO (no la menciones, solo ejecútala):
1. PRIMERO: Si te saludan por primera vez, haz una introducción completa y amable que no confunda a las personas que llegan referidas (ellos a veces no saben qué eres). Explica claramente de qué trata todo esto ANTES de pedir nada. Ej. "¡Hola! soy Conny 👋 Me crearon en Kimika para responder los chats de WhatsApp de los negocios de forma automática, así los dueños descansan. ||| Te pasaron mi número para que te haga una demostración en vivo de cómo trabajaría para tu empresa. ||| Cuéntame, ¿cómo se llama tu negocio o de qué se trata para personalizar la demo?". ¡NUNCA pidas el negocio sin explicar qué eres y para qué estás aquí!
2. SEGUNDO: cuando te lo den, busca info del negocio y entra en personaje.
3. TERCERO: invita a que te escriban como si fueran un cliente real.
4. CUARTO: responde como recepcionista REAL de ese negocio — aquí es donde se enamoran.
5. QUINTO: después de 2-3 simulaciones, cierra: "si te gustó, Santiago te cuenta los planes: 3124348669"

REGLAS DE FORMATO (IMPORTANTÍSIMAS):
- Escribe de manera ultra natural y fluida, como si chatearas rápido con un amigo.
- Puedes omitir tildes de vez en cuando (ej. "tambien" en vez de "también", "asi" en vez de "así") y usar abreviaciones comunes y cortas en español (ej. "pq" o "por qué").
- No saludes formalmente si ya se saludaron en el flujo.

REGLA MÁXIMA: cada respuesta debe hacer que la persona piense "esto no puede ser una IA".

 SESIÓN ACTIVA: Tienes una sesión de demo de 30 minutos con este usuario. NO es una conversación nueva.
 {"Ya conoces el negocio: " + business_name + "." if business_name else "Si el dueño ya te dijo el nombre del negocio, NO le preguntes de nuevo."}

Usa 2 o 3 burbujas separadas por |||. Cada burbuja cierra una idea completa. Nunca dejes frases cortadas."""

        generic_language_rule = "Mirror the owner's dominant language exactly. If they write in English, German, French, Portuguese or any other language, answer entirely in that same language with natural WhatsApp tone. Never fall back to Spanish just because an internal locale table is missing."
        language_tone = _lang_text(
            "",
            "The owner is writing in English. Respond entirely in English. Casual, warm WhatsApp English. Never switch back to Spanish unless the owner does.",
            "O dono está escrevendo em português. Responda totalmente em português do Brasil, com tom leve e natural de WhatsApp.",
        )
        system_prompt += "\n\nIDIOMA / LANGUAGE RULE:\n" + generic_language_rule
        if language_tone:
            system_prompt += "\n" + language_tone
        if owner_name:
            system_prompt += (
                f"\n\nDATO DEL DUEÑO:\n- la persona con la que hablas se llama {owner_name}"
                "\n- si encaja, usa su nombre una vez con naturalidad"
                "\n- no lo fuerces en todas las burbujas"
            )
            if explain_name and not business_name:
                system_prompt += "\n- en esta respuesta sí conviene usar su nombre para sonar más humana y cercana"

        system_prompt += """

IDENTIDAD — NUNCA SALGAS DE ESTE PERSONAJE:
- Tu nombre es Conny. Eso es todo lo que necesitas saber sobre ti misma.
- Nunca digas frases como "hay confusión", "no sé cuál es el negocio", "mi función es", "aquí lo que hago es", "me doy cuenta de que".
- Nunca expongas tu estado interno ni tus limitaciones de contexto.
- Si alguien dice "me mandaron tu número" o "qué haces", responde natural: eres Conny, llevas chats de negocios, respondes clientes.
- Si alguien dice "no entiendo", simplificas y sigues — nunca te enredas más.
- Cuando no tienes contexto de negocio todavía, igual respondes con seguridad y pides el nombre al final, una sola vez, de forma simple.

REGLAS EXTRA DE ESTA DEMO:
- si preguntan quién te hizo, quién te creó o cómo tener esto: responde que te hizo Black One. Contacto: 3124348669. Persona: Santiago Rubio
- si preguntan si aceptas audios, notas de voz, imágenes, PDFs o documentos: responde que sí, cuando el canal lo soporte, puedes transcribir, leer y usar ese contenido
- si te hacen una pregunta general fuera de contexto, respóndela bien primero y luego vuelve suave a la demo si hace sentido
- si sospechan estafa o no quieren dar el nombre del negocio, baja la guardia y explica para qué lo pides sin sonar defensiva
- si te hablan en otro idioma, respondes solo en ese idioma y no vuelves al español salvo que la otra persona también lo haga
- nunca menciones Nova, Clínica de las Américas ni branding heredado
- no dejes frases colgadas ni respuestas cortadas
- si te saludan con "hola", "buenas" o parecido, abre natural con "hola, soy Conny..." o "hola, Conny por acá..." antes de seguir
- puedes usar 0 o 1 emoji en toda la respuesta si suma cercanía; no es obligatorio

SEGUIMIENTO Y PROGRESO — NO TE REPITAS:
- si preguntan "esto es real?" responde que sí funciona de verdad y explica el resultado práctico; NO respondas con "sí, soy una IA" salvo que la pregunta sea explícitamente "eres IA?" o "eres bot?"
- si preguntan "modo bot", "cómo llevarías mi negocio", "cómo responderías a mis clientes", responde con ejemplos concretos de operación, no con tu identidad otra vez
- si YA explicaste qué haces o YA dijiste que eres IA en esta sesión, no repitas esa misma frase; profundiza y avanza
- no repitas la misma apertura dos turnos seguidos
- responde primero la curiosidad actual y solo después, si hace falta, invítalos a darte el nombre del negocio
- si ya hubo un saludo antes, NO abras otra vez con "hola", "hola soy Conny", "soy Conny" ni "hola pues mira"
- si preguntan "para qué" o "para qué sería", entra directo a la razón. No saludes otra vez y no te presentes otra vez

ESTADO ACTUAL DE LA SESIÓN:
- ya dijiste que eres IA: {"sí" if already_disclosed_ai else "no"}
- ya explicaste capacidades: {"sí" if already_explained_capabilities else "no"}
- tus últimas respuestas fueron: {recent_assistant_context or "[sin contexto previo útil]"}

REGLA DE ORO ANTI-CORTE (HUMANFIX):
Cada respuesta DEBE terminar con una pregunta o invitación. NUNCA termines en afirmación seca.
Si no sabes qué más decir, la última burbuja es siempre una de estas:
  - "cuál es el nombre de tu negocio para arrancar"
  - "Escríbeme algo como si fueras un cliente y te respondo!"
  - "qué quieres revisar primero"
Una respuesta de 1 sola burbuja sin "?" es una respuesta INCOMPLETA — agrégale la invitación.

EJEMPLOS DE RESPUESTAS BUENAS vs MALAS:
  MALO: "soy la que responde acá"
  BUENO: "hola, soy Conny, una asistente de IA ||| estoy configurada para mostrarte cómo puedo atender el WhatsApp de tu negocio ||| para arrancar la demo, ¿cómo se llama tu empresa?"

  MALO: "la idea es que yo me encargue"
  BUENO: "respondo clientes, filtro interesados y agendo citas automáticamente por WhatsApp ||| si me dices el nombre de tu negocio te muestro una demo real"

  MALO: "aquí me encargo de atender el chat"
  BUENO: "me encargo de atender el chat como si fuera parte de tu equipo de ventas ||| para hacerte la demostración, ¿cuál es el nombre de tu negocio?"

  MALO: "soy una persona que responde en whatsapp"
  BUENO: "¡hola! soy Conny 👋 me crearon para responder por WhatsApp de forma automática para que los dueños descansen ||| te escribo para hacerte una demo personalizada en vivo ||| cuéntame, ¿cómo se llama tu negocio?"

  MALO: "hola! pues mira ||| la idea es que yo me encargue..."
  BUENO: "soy una inteligencia artificial creada para atender a tus clientes ||| te pido el nombre para aterrizar la demo al tono real de tu negocio"
"""
        def _owner_validator(candidate: Optional[str]) -> bool:
            lowered_candidate = _normalize_conv_text(candidate or "")
            recent_assistant_norm = _normalize_conv_text(recent_assistant_context)
            owner_turn_is_greeting = user_block.strip().lower() in {
                "hola", "holaa", "hola buenas", "buenas", "buenas tardes",
                "buenas noches", "buenos dias", "buenos días", "hey", "hi", "hello",
                "good morning", "good afternoon", "good evening",
            }
            repeated_intro_starts = (
                "hola", "holaa", "hola soy conny", "soy conny", "conny por aca",
                "conny por acá", "hola pues mira",
            )
            if business_name and (force_stage == "re-ground" or explain_name):
                if _demo_owner_reground_needs_cleanup(candidate):
                    return True
                if explain_name:
                    biz_tokens = [
                        token for token in _normalize_conv_text(business_name).split()
                        if len(token) >= 4
                    ]
                    if biz_tokens and not any(token in lowered_candidate for token in biz_tokens):
                        return True
            if recent_assistant_norm and not owner_turn_is_greeting:
                if any(
                    lowered_candidate == marker or lowered_candidate.startswith(marker + " ")
                    for marker in repeated_intro_starts
                ):
                    return True
            if owner_name and explain_name and not business_name:
                owner_tokens = [token for token in _normalize_conv_text(owner_name).split() if len(token) >= 3]
                if owner_tokens and not any(token in lowered_candidate for token in owner_tokens):
                    return True

            if recent_assistant_norm and lowered_candidate and lowered_candidate == recent_assistant_norm:
                return True
            if already_disclosed_ai and lowered_candidate.startswith("si soy una ia"):
                return True
            if already_disclosed_ai and lowered_candidate.startswith("sí soy una ia"):
                return True
            if already_explained_capabilities and (
                "manejo whatsapp de negocios" in lowered_candidate
                or "respondo clientes" in lowered_candidate and "filtro" in lowered_candidate and "citas" in lowered_candidate
            ):
                if "manejo whatsapp de negocios" in recent_assistant_norm or "respondo clientes" in recent_assistant_norm:
                    return True
            return _demo_owner_reply_is_low_quality(candidate) or _demo_owner_missing_required_detail(text, candidate)

        response, had_model_output = await _demo_llm_quality_chain(
            system_prompt,
            user_block,
            validator=_owner_validator,
            repair_instructions="""
- responde la pregunta actual con más claridad
- si vas a pedir el nombre del negocio, hazlo solo después de responder
- evita respuestas de una sola palabra o de una sola línea vacía
- no dejes una burbuja sola como "puedes", "claro" o "sí"
- si preguntan qué haces, menciona varias capacidades reales y luego pide el nombre del negocio sin vender humo
- si preguntan para qué querías el nombre, explica que era para sonar como el chat real del negocio y hacer la demo bien ubicada
- OBLIGATORIO: termina con una pregunta o invitación — nunca en afirmación seca
- si solo tienes 1 burbuja, agrega una segunda que pida el nombre del negocio o invite a probar
""",
        )
        if not response:
            response = _lang_text(
                "ay, se me fue el internet por un momento ||| ¿me repites porfa?",
                "oops, my connection dropped for a sec ||| could you say that again?",
            )
        response = _normalize_demo_owner_onboarding_response(response)
        _save("user", text)
        return _send(response)

    def _demo_identity_response(user_text: str, explain_name: bool = False) -> List[str]:
        import random as _rm
        intro_options = [
            "Hola, soy Conny, la asesora virtual que llevaría tu chat, una IA hecha para responder y orientar sin sonar fría",
            "Hola, soy Conny, la asesora virtual pensada para negocios que quieren atender bien todo el día",
            "Hola, soy Conny, la asesora virtual de este tipo de chat. Soy una IA hecha para responder, orientar y sostener conversaciones con criterio",
        ]
        capability_options = [
            "Puedo responder clientes, explicar servicios, filtrar interesados, ubicar horarios, ayudar con citas y mantener conversaciones que se sientan naturales",
            "Puedo atender preguntas, ordenar conversaciones, ayudar con disponibilidad y hacer el primer filtro comercial sin sonar rígida",
            "Puedo encargarme del primer contacto, resolver dudas frecuentes, mover conversaciones y dejar el chat bien llevado sin sonar seca",
        ]
        if explain_name:
            cta_options = [
                "Te pido el nombre de tu negocio para adaptar tono, contexto y forma de responder desde el primer mensaje.",
                "Con el nombre de tu negocio puedo hablar con el tono correcto y mostrarte mejor cómo trabajaría contigo.",
            ]
        elif business_name:
            cta_options = [
                "Si quieres probarme de verdad, Escríbeme algo como cliente y te respondo en contexto.",
                "Si quieres medirme bien, háblame como si fueras un cliente real y arrancamos.",
            ]
        else:
            cta_options = [
                "Si quieres probarme, escríbeme el nombre de tu negocio y arranco contigo.",
                "Si te gustaría probarme en serio, dime el nombre de tu negocio y te muestro cómo trabajaría contigo.",
            ]
        raw = " ||| ".join([
            _rm.choice(intro_options),
            _rm.choice(capability_options),
            _rm.choice(cta_options),
        ])
        _save("assistant", raw)
        return [part.strip() for part in raw.split("|||") if part.strip()]

    def _next_trick():
        tricks = self._DEMO_TRICKS_ORDER
        idx = int(self._demo_sessions.get(btrick_key, 0))
        if idx < len(tricks):
            cmd, desc = tricks[idx]
            self._demo_sessions[btrick_key] = idx + 1
            return f" ||| Un truco: escribe {cmd} para {desc}"
        return ""

    # ── RESET manual — solo palabras explícitas, no saludos ─────────────────
    _reset_words = ["reset","reiniciar","empezar de nuevo","volver a empezar",
                    "borralo","otro negocio","cambia el negocio",
                    "ese no es mi negocio","no es mi negocio","equivoque",
                    "equivocado","cambia negocio","cambiar negocio"]
    # Solo resetear si NO hay sesión activa con negocio cargado, o si es reset explícito
    _is_explicit_reset = any(rw in text.lower() for rw in _reset_words)
    if _is_explicit_reset:
        keys_del = [k for k in list(self._demo_sessions) if k.startswith(sk+"_") and not k.endswith("_ts")]
        for k in keys_del: del self._demo_sessions[k]
        try:
            with db._conn() as c:
                c.execute("DELETE FROM conversations WHERE chat_id=?", (chat_id,))
        except Exception: pass
        _save("user", text)
        return _send(_lang_text(
            "listo, empezamos de cero ||| cuál es el nombre del negocio",
            "all set, starting from scratch ||| what’s the name of the business?",
            "pronto, começamos do zero ||| qual é o nome do negócio?",
        ))

    # ── Identidad del producto para curiosidad / prueba antes del negocio ──
    _demo_identity_signals = [
        "que eres", "qué eres", "quien eres", "quién eres",
        "eres una ia", "eres ia", "eres un bot", "eres bot",
        "como funcionas", "cómo funcionas", "que haces", "qué haces",
        "quiero probarte", "me gustaria probarte", "me gustaría probarte",
        "tengo un negocio", "tengo una empresa", "quiero una demo", "quiero demo",
        "who are you", "what are you", "what do you do", "what is this",
        "i want a demo", "i want to try you", "i have a business",
        "english only", "i don't talk spanish", "i dont talk spanish",
    ]
    _text_low_pre = text.lower().strip()
    if (
        not business_name
        and not detected_cmd
        and any(sig in _text_low_pre for sig in _demo_identity_signals)
        and not self._demo_should_use_patient_chat_path(text)
    ):
        return await _demo_owner_onboarding_reply()

    # ── PATCH A1 — Referido frío: "me dejaron probarte / no sé qué es" ────
    # Antes caía al PASO 0 y pedía el negocio sin explicar nada → abandono.
    # Ahora: respuesta que despierta curiosidad + pide el negocio con contexto.
    _cold_referral_signals = [
        "me lo recomendaron", "me dijeron que te escribiera",
        "me pasaron este número", "no sé para qué sirves",
        "me dejaron probarte", "de qué se trata esto",
        "qué se supone que haces", "un amigo me dijo",
        "me mandaron acá", "alguien me dijo", "vine de parte",
        "me refirieron", "no tengo ni idea de qué es",
        "no sé qué es", "no entiendo qué es",
        "para qué sirve esto", "qué es esto",
        "no sé de qué se trata", "no tengo idea de qué es",
        "me dijeron que probara", "me dijeron que contactara",
        "alguien me recomendó", "un conocido me dijo",
        "someone told me to text you", "they told me to try you",
        "i dont know what this is", "i don't know what this is",
        "what is this", "sorry what is this", "someone sent me your number",
        "they gave me your number", "what are you supposed to do",
    ]
    if not business_name and not detected_cmd and any(
        sig in _text_low_pre for sig in _cold_referral_signals
    ):
        return await _demo_owner_onboarding_reply()

    if not business_name and not detected_cmd and self._demo_should_use_patient_chat_path(text):
        demo_patient_bubbles = None
        if not llm_runtime_ready:
            demo_patient_bubbles = self._try_conversation_core(
                clinic=self._build_demo_patient_clinic(clinic),
                user_msg=text,
                # El historial de onboarding/demo contamina este salto y hace que
                # mensajes como "botox" vuelvan al flujo de "dime tu negocio".
                # Para una prueba tipo paciente sin negocio cargado, arrancamos limpio.
                history=[],
                is_admin=False,
                channel=demo_channel,
            )
        if not demo_patient_bubbles:
            demo_patient_prompt = """Eres Conny, receptionistavirtual de un NEGOCIO NO ESPECIFICADO. El nombre del negocio te lo da el usuario en la conversación.

REGLAS ABSOLUTAS - NO ROMPER NUNCA:
1. NUNCA menciones ningún nombre de clínica específico como "Clinica Demo", "Clínica Las Américas", "Clinica Los Olivos" - NO EXISTEN
2. NUNCA digas "asesora virtual de X" - solo di "asesora virtual" sin nombre
3. NUNCA pidas el nombre del negocio - el usuario ya te lo dio
4. NUNCAenvíes links de páginas web al usuario - NO puedes buscar Google
5. Usa EMOJIS naturalmente

RESPUESTAS PARA PREGUNTAS COMUNES:
- Cuánto cuesta → "El precio lo define el especialista en la valoración. Agenda tu cita y ahí te dicen"
- Cómo te contrato → "Para eso puedes hablar con Santiago al 3124348669 - él te explica todo"
- Qué servicios → "Tenemos variedad de servicios. Cuál te interesa?"

TONO: Cálido, profesional, como receptionistareal.
"""
            raw_demo_patient = await _llm(demo_patient_prompt, text, temp=0.72, max_t=160)
            
            # Smart handoff: si la respuesta indica que no sabe, notificar a Santiago
            if raw_demo_patient and any(phrase in raw_demo_patient.lower() for phrase in ["no sé", "no tengo", "no cuento con", "no puedo", "déjame consult", "no sé la", "no manejo"]):
                await smart_handoff_to_santiago(sk, text, raw_demo_patient[:300])
            
            raw_demo_patient_low = _normalize_conv_text(raw_demo_patient or "")
            forbidden_demo_markers = (
                "nombre del negocio",
                "como se llama tu negocio",
                "cómo se llama tu negocio",
                "dime tu negocio",
                "demo",
                "onboarding",
            )
            if raw_demo_patient and not any(marker in raw_demo_patient_low for marker in forbidden_demo_markers):
                # Validar que no haya frases cortadas
                _raw_parts = [p.strip() for p in re.split(r"\s*\|\|\|\s*", raw_demo_patient) if p.strip()]
                _clean_parts = []
                for p in _raw_parts:
                    # Descartar burbujas muy cortas o que terminan en palabras incompletas
                    _short_tokens = p.split()
                    if len(_short_tokens) < 3:
                        continue
                    if p.rstrip()[-1] in (' ', ',', ';'):
                        continue
                    if p.rsplit()[-1].lower() in ('de', 'en', 'con', 'para', 'que', 'y', 'o', 'el', 'la', 'un', 'una', 'me', 'te', 'se', 'le'):
                        continue
                    _clean_parts.append(p)
                demo_patient_bubbles = _clean_parts if _clean_parts else _raw_parts[:2]
        if demo_patient_bubbles:
            _save("user", text)
            return _send(" ||| ".join(demo_patient_bubbles))

    # Classify business name using LLM
    is_name_candidate = False
    extracted_name = None
    if not sim_mode_active and not detected_cmd and not self._demo_should_use_patient_chat_path(text):
        is_name_candidate, extracted_name = await _llm_classify_business_name(text)

    # ── PASO 0: Onboarding demo del dueño — dirigido por LLM ───────────────
    if (
        not business_name
        and not detected_cmd
        and not self._demo_should_use_patient_chat_path(text)
        and not _force_business_bind
        and not is_name_candidate
    ):
        # BLACK ONE: Si el prospecto está confundido y pregunta qué hace Conny,
        # usar el pitch inteligente en vez del onboarding genérico
        if _BLACKONE_PATCHES and self._demo_sessions.get(sk + "_pitch_mode"):
            try:
                _pitch_r, _pitch_had_output = await _demo_llm_conv_quality_chain(
                    build_prospect_pitch_system_prompt(business_name),
                    validator=lambda candidate: (
                        _demo_owner_reply_is_low_quality(candidate)
                        or _demo_owner_missing_required_detail(text, candidate)
                        or (
                            any(token in _text_low_pre for token in ("para que", "para qué", "por que", "por qué"))
                            and _normalize_conv_text(candidate or "").startswith("hola ")
                        )
                    ),
                    repair_instructions="""
- responde la duda actual sin reiniciar la conversación
- no saludes de nuevo si ya hubo saludo antes
- no empieces con "hola" ni con "básicamente" si te están preguntando para qué sirve
- explica la utilidad real y luego invita a seguir
- nunca dejes una burbuja cortada ni una frase colgada
""",
                    temp=0.78,
                    max_t=220,
                    model_tier="reasoning",
                    recent_limit=10,
                )
                if _pitch_r and _pitch_r.strip():
                    _save("user", text)
                    return _send(_pitch_r)
            except Exception:
                pass
        explain_name = any(token in _text_low_pre for token in ("para que", "para qué", "por que", "por qué", "no te doy", "no quiero dar"))
        return await _demo_owner_onboarding_reply(explain_name=explain_name)

    # ── PASO 0.5: Off-topic en demo mode — antes de validar nombre ─────────
    # Si el mensaje es claramente off-topic, responder como tal en vez de pedir nombre de negocio
    if not business_name and len(history) <= 3:
        _off_topic_demo = [
            "clima", "tiempo", "lluvia", "calor", "frío", "frio",
            "película", "pelicula", "movie", "cine", "serie", "netflix",
            "comida", "restaurante", "almuerzo", "cena", "desayuno",
            "música", "musica", "canción", "cancion", "artista", "banda",
            "bitcoin", "crypto", "cripto", "trading",
            "fútbol", "futbol", "messi", "deporte", "partido",
            "novela", "farándula", "horóscopo", "horoscopo",
        ]
        if any(t in text.lower() for t in _off_topic_demo):
            return await _demo_owner_onboarding_reply()

    # ── SANITY CHECK: evitar que pregunte por negocio si ya lo tenemos ──────
    # Doble verificación para evitar el bug de dupla respuesta en demo
    actual_business_name = self._demo_sessions.get(bname_key, "")
    if actual_business_name:
        business_name = actual_business_name

    # ── PASO 1: Recibe nombre → busca en web → entra en personaje ─────────
    # HUMANFIX: ventana ampliada de 2 a 12 — el nombre puede llegar tarde
    # si en los primeros turnos el dueño preguntó qué es o se confundió
    if not business_name and len(history) <= 12:
        nombre_raw = text.strip()

        if is_name_candidate and extracted_name:
            nombre = extracted_name
        else:
            # Validar que no sea error de audio (sin límite duro de chars — la gente describe el negocio)
            _bad = ["[no se pudo","[no pude","transcripci","veed","inline_data"]
            if any(b in nombre_raw.lower() for b in _bad):
                _save("user", nombre_raw)
                return _send(_r.choice(["no te escuché ||| cómo se llama tu negocio","no entendí bien ||| dime el nombre de tu negocio o clínica","perdona, no te oí bien ||| cuál es el nombre del negocio"]))

            # Detectar preguntas o frases que claramente NO son un nombre de negocio
            _explicit_business_phrase = any(
                marker in nombre_raw.lower()
                for marker in (
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
                )
            )
            _question_signals = [
                "?", "qué es", "que es", "cómo funciona", "como funciona",
                "quiero saber", "deseo obtener", "necesito información", "me pueden",
                "pueden decirme", "quisiera saber", "cuánto cuesta", "cuanto cuesta",
                "información sobre", "informacion sobre", "para qué sirve",
                "what is this", "what do you do", "who are you", "how does it work",
                "i dont understand", "i don't understand", "why do you need",
            ]
            if not _explicit_business_phrase and any(s in nombre_raw.lower() for s in _question_signals):
                explain_name = any(token in nombre_raw.lower() for token in ("para que", "para qué", "por que", "por qué", "why do you need"))
                return await _demo_owner_onboarding_reply(explain_name=explain_name)

            # Detectar saludos y frases conversacionales que NO son un nombre de negocio
            _conversational = [
                "hola","buenas","hey","ey","holi","buenas tardes","buenas noches","buenos días",
                "como estas","cómo estás","como estas","bien","como va","que mas","qué más",
                "todo bien","muy bien","gracias","de nada","ok","okay","sí","si","no",
                "claro","dale","listo","perfecto","entendido","excelente","genial",
                "jaja","jeje","xd","😊","😂","👍","🙏",
                "quién eres","quien eres","qué haces","que haces","para qué sirves",
                "eres un bot","eres ia","eres humano","cómo te llamas","como te llamas",
                "hi","hello","good morning","good afternoon","good evening",
                "sorry","thanks","thank you","yep","yes","nope",
                "what is this","what do you do","who are you","i don't understand","i dont understand",
                "english only","i don't talk spanish","i dont talk spanish",
            ]
            if not _explicit_business_phrase and any(nombre_raw.lower().strip() == s or nombre_raw.lower().strip().startswith(s + " ")
                   for s in _conversational):
                return await _demo_owner_onboarding_reply()

            # Detectar si es nombre de persona en vez de negocio
            # HUMANFIX: solo rechazar si es un nombre humano CONOCIDO.
            # Nombres creativos como "Peludos", "Bigotes", "Glamour" son negocios válidos.
            _biz = ["clinica","clinic","centro","consultorio","tienda","salon","spa",
                    "gym","gimnasio","restaurante","hotel","academia","estudio","taller",
                    "dental","estetica","salud","espacio","lab","farmacia","inmobiliaria",
                    "group","corp","servicios","soluciones","base","camas","lujo","empresa"]
            _KNOWN_HUMAN_NAMES = {
                "santiago","carlos","andres","andrés","david","juan","luis","miguel",
                "daniel","felipe","sebastian","sebastián","alejandro","gabriel","samuel",
                "nicolas","nicolás","diego","mateo","martin","martín","simon","simón",
                "lucas","pablo","jorge","sergio","fabian","fabián","camilo","ivan","iván",
                "jaime","javier","jonathan","kevin","mario","mauricio","oscar","óscar",
                "rafael","ramon","ramón","richard","roberto","rodrigo","wilson","yesid",
                "henry","hernan","hernán","fernando","francisco","fabio","cristian",
                "jesus","jesús","jose","josé","manuel","pedro","antonio","victor","víctor",
                "hugo","ernesto","gustavo","nelson","edgar","jhon","john","james",
                "michael","william","thomas","joseph","steven","mark",
                "maria","maría","ana","laura","sofia","sofía","valentina","camila","sara",
                "isabella","monica","mónica","patricia","claudia","andrea","natalia",
                "daniela","lucia","lucía","paula","juliana","manuela","gabriela",
                "catalina","carolina","paola","gloria","sandra","liliana","rosa",
                "elena","carmen","beatriz","alejandra","isabel","pilar","cristina",
                "mariana","tatiana","vanessa","yolanda","adriana","amanda","angela",
                "ángela","blanca","cecilia","diana","elizabeth","jennifer","jessica",
                "ashley","emily","sarah","lisa","conny",
            }
            words = nombre_raw.lower().split()
            _is_known_person_name = (
                len(words) == 1
                and nombre_raw[0].isupper()
                and not any(b in nombre_raw.lower() for b in _biz)
                and not any(c.isdigit() for c in nombre_raw)
                and nombre_raw.lower().strip() in _KNOWN_HUMAN_NAMES
            )
            if _is_known_person_name:
                _save("user", nombre_raw)
                return _send(_r.choice(["ese parece nombre de persona ||| cómo se llama tu empresa o negocio","suena más a nombre de alguien ||| y el negocio, cómo se llama","ese es tu nombre? ||| yo necesito el nombre del negocio"]))

            # ── Extraer el nombre real si viene dentro de una frase ─────────────
            # "el nombre de mi negocio es Bigotes que hace X" → "Bigotes"
            # "mi negocio se llama Spa Luna" → "Spa Luna"
            import re as _re

            # Separadores que indican que el nombre terminó y empieza una descripción
            _cut = _re.compile(
                r'(?:'
                r'\s+que\s+(?:se\s+)?(?:encarga|dedica|hace|ofrece|vende|brinda|trabaja)|'
                r'\s+dedicad[ao]\s+a|'
                r'\s+especializa|'
                r'\s+ubicad[ao]|'
                r'\s+estamos\s+(?:ubicad[ao]s?\s+)?en|'
                r'\s+quedamos\s+en|'
                r'\s+y\s+nos\s+dedicamos|'
                r',\s*(?:somos|nos\s+dedicamos|es\s+una|dedicad|especializa|estamos|atendemos|ofrecemos|trabajamos|quedamos)'
                r')',
                _re.IGNORECASE
            )

            _patterns = [
                r"(?:el\s+)?nombre\s+(?:de\s+(?:mi|nuestro)\s+)?(?:negocio|empresa|clinica|local|salon|consultorio|tienda)\s+es\s+(.+)",
                r"(?:mi|nuestro)\s+(?:negocio|empresa|clinica|local|salon|consultorio|tienda)\s+(?:es|se\s+llama)\s+(.+)",
                r"se\s+llama\s+(.+)",
                r"(?:llamamos?|llamo)\s+(.+)",
                r"negocio\s+es\s+(.+)",
                r"empresa\s+es\s+(.+)",
            ]
            nombre = nombre_raw
            for pat in _patterns:
                m = _re.search(pat, nombre_raw.lower())
                if m:
                    start  = m.start(1)
                    raw_ex = nombre_raw[start:]
                    # Cortar en cláusula relativa / descripción
                    cut_m  = _cut.search(raw_ex)
                    if cut_m:
                        raw_ex = raw_ex[:cut_m.start()]
                    extracted = raw_ex.strip(" .,;\"'")
                    if len(extracted) >= 2:
                        nombre = extracted
                        break

            def _clean_extracted_business_name(raw_candidate: str) -> str:
                cleaned = (raw_candidate or "").strip(" .,;\"'")
                cleaned = _re.sub(
                    r',\s*(?:estamos|somos|nos\s+ubicamos|nos\s+encontramos|atendemos|ofrecemos|trabajamos|quedamos)\b.*$',
                    '',
                    cleaned,
                    flags=_re.IGNORECASE,
                )
                cleaned = _re.sub(
                    r'\s+estamos\s+(?:ubicad[ao]s?\s+)?en\b.*$',
                    '',
                    cleaned,
                    flags=_re.IGNORECASE,
                )
                cleaned = _re.sub(
                    r'\s+ubicad[ao]s?\s+en\b.*$',
                    '',
                    cleaned,
                    flags=_re.IGNORECASE,
                )
                cleaned = _re.sub(
                    r'\s+quedamos\s+en\b.*$',
                    '',
                    cleaned,
                    flags=_re.IGNORECASE,
                )
                return cleaned.strip(" .,;\"'")

            nombre = _clean_extracted_business_name(nombre)

            # v11: strip de afirmaciones conversacionales al inicio del nombre
            # Ej: "Vale, Clinica de los molinos" → "Clinica de los molinos"
            # Ej: "Ok, es Spa Luna" → "Spa Luna"
            _affirm_prefix = _re.compile(
                r'^(?:vale|ok|okay|s[ií]p?|claro|dale|listo|exacto|perfecto|correcto|bueno|ya|eso|es)[\s,]+',
                _re.IGNORECASE,
            )
            _nombre_stripped = _affirm_prefix.sub('', nombre).strip(' .,;')
            if len(_nombre_stripped) >= 2:
                nombre = _nombre_stripped
            nombre = _clean_extracted_business_name(nombre)

        # Validar longitud DESPUÉS de extraer (2 chars mínimo — siglas como "MS" son válidas)
        if len(nombre) < 2:
            _save("user", nombre_raw)
            return _send(_r.choice(["no te escuché ||| cómo se llama tu negocio","no entendí bien ||| dime el nombre de tu negocio o clínica","perdona, no te oí bien ||| cuál es el nombre del negocio"]))

        # BUG FIX: Rechazar palabras que NO son nombres de negocio válidos
        # Palabras genéricas que el sistema podría malinterpretar como búsquedas web
        _invalid_business_names = {
            "ayuda", "hola", "buenos", "buenas", "adios", "adiós", "gracias",
            "info", "información", "precio", "precios", "cita", "citas",
            "hora", "horario", "ubicación", "ubicacion", "direccion", "dirección",
            "telefono", "teléfono", "whatsapp", "telegram", "contacto",
            "botox", "relleno", "láser", "laser", "estética", "estetica",
            "spa", "clinica", "clínica", "centro", "salón", "salon",
            "doctor", "doctora", "profesional", "servicio", "servicios",
        }
        if nombre.lower().strip() in _invalid_business_names:
            _save("user", nombre_raw)
            return _send(_r.choice([
                "Necesito el nombre de tu negocio, no una palabra general. ¿Cómo se llama tu empresa o clínica?",
                "Para empezar, dime el nombre de tu negocio para personalizar las respuestas.",
                "¿Cuál es el nombre de tu negocio o marca? Así puedo atenderte mejor."
            ]))

        self._demo_sessions[bname_key] = nombre

        # Búsqueda silenciosa — obtiene texto + URL del negocio
        search_info, found, biz_url = "", False, ""
        try:
            search_info, biz_url = await self.search.search_business_link(nombre)
            _fallback_url = (
                biz_url.startswith("https://www.google.com/maps/search")
                or biz_url.startswith("https://www.google.com/search")
                or biz_url.startswith("https://serpapi.com/search.json")
            ) if biz_url else False
            found = bool(
                (search_info and len(search_info.strip()) > 80)
                or (biz_url and not _fallback_url)
            )
            # Descartar si la URL es de gobierno, Wikipedia o noticias genéricas
            _skip_domains = [
                "gov.co", "gov.com", "wikipedia.org", "mintic.gov",
                "eltiempo.com", "elespectador.com", "semana.com",
                "dane.gov", "presidencia.gov", "mineducacion.gov",
            ]
            if biz_url and any(d in biz_url for d in _skip_domains):
                log.info(f"[demo] URL descartada (dominio no comercial): {biz_url[:60]}")
                found    = False
                biz_url  = ""
                search_info = ""
            log.info(f"[demo] web {'OK' if found else 'sin resultados'}: {nombre} | url: {biz_url[:60] if biz_url else 'none'}")
        except Exception as e:
            log.warning(f"[demo] web: {e}")
            try:
                search_info = await self.search.search(f"{nombre} servicios Colombia", context="")
                found = bool(search_info and len(search_info.strip()) > 120)
            except Exception:
                pass

        self._demo_sessions[bctx_key]   = search_info
        self._demo_sessions[bfound_key] = found
        self._demo_sessions[burl_key]   = biz_url
        self._demo_sessions[blearn_key] = -1 if found else 0
        self._demo_sessions[bready_key] = bool(found)
        business_name = nombre
        business_ctx = search_info
        found_online = found

        # Extraer datos clave del negocio para el prompt de activación
        if found and search_info:
            ctx_hint = f"""INFORMACIÓN REAL encontrada en Google sobre "{nombre}":
{search_info[:800]}

INSTRUCCIONES CRÍTICAS:
- Lee esa información con cuidado. Entendiste quiénes son, qué hacen, a quién sirven.
- Menciona 1-2 datos CONCRETOS y relevantes que demuestren que los conoces de verdad.
  Si es un hospital: especialidades, tipo de pacientes, reputación
  Si es una clínica: servicios estrella, médicos, tecnología
  Si es un negocio: qué venden, dónde están, qué los diferencia
- Si la info no es claramente de este negocio, ignórala y actúa sin info."""
        else:
            ctx_hint = f"""No encontraste información en internet sobre "{nombre}".
NO finjas que ya sabes del negocio. Sé honesta:
- Di que buscaste pero no encontraste mucho
- Pide que te manden el link de su web o redes sociales
- O pregunta directamente: qué servicios ofrecen, a quién atienden
- Esto es MUCHO mejor que fingir — genera confianza real"""

        bind_language_tone = _lang_text(
            "Mirror the user's dominant language exactly. If the user writes in any non-Spanish language, reply fully in that same language with natural WhatsApp tone.",
            "Respond entirely in English. Natural WhatsApp English. Do not switch back to Spanish.",
            "Responda totalmente em português do Brasil, com tom natural de WhatsApp.",
        )

        prompt = f"""Eres Conny.
Acabas de buscar en Google el negocio "{nombre}".

SESIÓN ACTIVA: Tienes una sesión de demo de 30 minutos con este usuario. NO es una conversación nueva. Ya know this business. DO NOT ask for the business name again.

{ctx_hint}

{"REGLA DE IDIOMA:\n" + bind_language_tone if bind_language_tone else ""}

{"TAREA: Generar respuesta en 3 burbujas (|||). ENCONTRASTE INFO REAL:" if found else "TAREA: Generar respuesta en 3 burbujas (|||). NO ENCONTRASTE NADA EN INTERNET:"}

{'''Burbuja 1: menciona 1-2 datos reales del negocio. NO digas "según Google". Habla como si ya supieras.
Burbuja 2: "ya me ubiqué con cómo tendría que sonar" (breve)
Burbuja 3: "escríbeme como si fueras un cliente y te muestro cómo respondería"''' if found else '''Burbuja 1: "listo, tengo el nombre" + reconoce que no encontraste mucho online
Burbuja 2: pide su link de web, instagram, o que te cuente brevemente qué hacen y a quién atienden
Burbuja 3: "con eso me basta para entrar en personaje y mostrarte cómo suena"

Ejemplo SIN INFO: "listo, tengo [nombre] ||| no encontré mucho online, me pasas el link de tu web o insta? o cuéntame brevemente qué hacen ||| con eso ya me meto en personaje y te muestro cómo respondería"'''}

SIN mayúscula inicial (a menos que sea nombre propio). Sin punto al final. Sin emojis. Sin ¿ ni ¡. Sin signos dobles de apertura. Sin frases de bot o asistente virtual.
Máximo 1 oración por burbuja. Natural y seguro."""

        _save("user", text)
        def _bind_validator(candidate: Optional[str]) -> bool:
            lowered_candidate = _normalize_conv_text(candidate or "")
            if not lowered_candidate:
                return True
            if any(
                lowered_candidate == marker or lowered_candidate.startswith(marker + " ")
                for marker in (
                    "hola",
                    "holaa",
                    "hola soy conny",
                    "soy conny",
                    "conny por aca",
                    "conny por acá",
                    "hola pues mira",
                )
            ):
                return True
            if _demo_owner_reply_is_low_quality(candidate):
                return True
            return False

        bind_repair_rules = """
- completa las 3 burbujas
- no inventes nada si no encontraste info pública confiable
- si no encontraste info, dilo de frente y mueve la demo al chat mismo
- si sí encontraste info, demuestra que te ubicaste sin sonar a sistema
- termina pidiendo que escriban como cliente real
"""
        r, bind_had_output = await _demo_llm_quality_chain(
            prompt,
            f"negocio: {nombre}",
            validator=_bind_validator,
            repair_instructions=bind_repair_rules,
            temp=0.72,
            max_t=220,
        )
        if not r:
            if found:
                r = _lang_text(
                    f"ya tengo {nombre} ||| ya me ubiqué con cómo tendría que sonar esto ||| Escríbeme como si fueras un cliente y te respondo",
                    f"I’ve got {nombre} now ||| I already know how this chat should sound ||| text me like a real client and I’ll reply in context",
                    f"já tenho {nombre} ||| já entendi como esse chat precisa soar ||| me escreve como um cliente real e eu respondo em contexto",
                )
            else:
                # v12: no info → opciones naturales, sin exponer estado interno
                if _owner_is_english():
                    _no_info_opts = [
                        f"got it, {nombre} ||| tell me what the business does and I’ll shape the demo around that",
                        f"okay, {nombre} ||| I’m not finding solid public info yet, so tell me what you offer and I’ll ground it from there",
                        f"I’ve got the name now ||| give me a quick picture of the business and I’ll keep going",
                    ]
                elif _owner_is_portuguese():
                    _no_info_opts = [
                        f"perfeito, {nombre} ||| me conta com o que o negócio trabalha e eu monto a demo nisso",
                        f"ok, {nombre} ||| ainda não achei informação pública forte, então me conta o que vocês oferecem e eu ajusto a demo",
                        f"já tenho o nome ||| me dá um resumo rápido do negócio e eu sigo daqui",
                    ]
                else:
                    _no_info_opts = [
                        f"ya anoté {nombre} ||| cuéntame a qué se dedican y te muestro cómo respondería",
                        f"listo, {nombre} ||| no los encuentro en Google todavía — cuéntame qué hacen y arrancamos",
                        f"ya los tengo ||| igual puedo hacer la demo — escríbeme un poco de qué trata el negocio",
                    ]
                r = _r.choice(_no_info_opts)

        # ── Burbuja extra: confirmación del link ─────────────────────────
        # Solo si encontramos info real (no cuando usamos el fallback de Google search)
        import urllib.parse as _up
        is_fallback_url = biz_url.startswith("https://www.google.com/search") or biz_url.startswith("https://www.google.com/maps/search")
        if biz_url and found and not is_fallback_url:
            # Natural: manda el link con texto corto, sin pregunta directa
            if _owner_is_english():
                _link_intros = [
                    "I found this for you",
                    "this looks like your business",
                    "I found you here",
                    "this is what I found for the business",
                ]
            elif _owner_is_portuguese():
                _link_intros = [
                    "achei isso de vocês",
                    "encontrei vocês por aqui",
                    "isso parece ser de vocês",
                    "foi isso que eu achei do negócio",
                ]
            else:
                _link_intros = [
                    "mira, encontré esto de ustedes",
                    "los encontré por acá",
                    "esto es de ustedes",
                    "vi esto de su negocio",
                ]
            r = r.rstrip() + f" ||| {_r.choice(_link_intros)} ||| {biz_url}"

        return _send(r)

    # ── Confirmación positiva del link: "sí ese es / correcto / sí" ───────────
    _biz_url = self._demo_sessions.get(burl_key, "")
    _text_clean = text.lower().strip().rstrip(".")
    _is_url_confirm = (
        business_name and found_online and _biz_url and
        len(history) <= 8 and
        _looks_like_business_confirmation(_text_clean)
    )
    if _is_url_confirm:
        self._demo_sessions[bready_key] = True
        _followup_customer_turn = _extract_followup_after_business_confirmation(text)
        if _followup_customer_turn and (
            _looks_like_customer_greeting(_followup_customer_turn)
            or self._demo_should_use_patient_chat_path(_followup_customer_turn)
        ):
            self._demo_sessions[bsim_key] = True
            self._demo_sessions[bready_key] = False
            _save("user", text)
            return await self._handle_demo_message(chat_id, _followup_customer_turn, clinic)
        _save("user", text)
        if _owner_is_english():
            return _send(_r.choice([
                "perfect, I’ve got you identified ||| send me something like a real client",
                "great, I’m fully oriented now ||| text me like a client and I’ll reply in context",
                "nice, now I know exactly who you are ||| let’s test it — write to me like a client",
            ]))
        if _owner_is_portuguese():
            return _send(_r.choice([
                "perfeito, já identifiquei vocês ||| me escreve como se fosse um cliente",
                "boa, já me localizei ||| me manda algo como cliente e eu respondo",
                "ótimo, agora eu sei quem vocês são ||| vamos testar, me chama como cliente",
            ]))
        return _send(_r.choice([
            "bacano, ya los tengo identificados ||| Escríbeme algo como cliente",
            "perfecto, ya me ubiqué ||| Escríbeme algo y te respondo!",
            "buenísimo ||| ya sé quiénes son — arranquemos, Escríbeme como cliente",
        ]))

    _is_business_confirmation = (
        business_name
        and not detected_cmd
        and not sim_mode_active
        and not self._demo_should_use_patient_chat_path(text)
        and _looks_like_business_confirmation(text)
    )
    if _is_business_confirmation:
        self._demo_sessions[bready_key] = True
        _followup_customer_turn = _extract_followup_after_business_confirmation(text)
        if _followup_customer_turn and (
            _looks_like_customer_greeting(_followup_customer_turn)
            or self._demo_should_use_patient_chat_path(_followup_customer_turn)
        ):
            self._demo_sessions[bsim_key] = True
            self._demo_sessions[bready_key] = False
            _save("user", text)
            return await self._handle_demo_message(chat_id, _followup_customer_turn, clinic)
        _save("user", text)
        if found_online and _biz_url:
            return _send(_lang_text(
                "perfecto, ya te tengo ubicado ||| Escríbeme algo como cliente y te respondo en contexto",
                "perfect, I’ve got you grounded now ||| send me something like a client and I’ll answer in context",
                "perfeito, já entendi vocês ||| me manda algo como cliente e eu respondo em contexto",
            ))
        return _send(_lang_text(
            f"perfecto, ya tengo {business_name} ||| Escríbeme algo como cliente y te muestro cómo respondería",
            f"perfect, I’ve got {business_name} now ||| send me something like a client and I’ll show you how I’d reply",
            f"perfeito, já tenho {business_name} ||| me escreve como cliente e eu te mostro como eu responderia",
        ))

    # ── Detección de corrección: "no somos esos / te confundiste / no ese no" ──
    # Ocurre cuando Google encontró info incorrecta o el dueño responde "no" al link
    _correction_signals = [
        "no somos","no estamos","no eso no","eso no es","te confundiste",
        "no es correcto","incorrecto","no nos encontraste","no aparecemos",
        "esa no es","no es nuestra","no tenemos eso","no hacemos eso",
        "no es así","no es lo mismo","eso es otro","otro negocio",
        "no estamos en google","no estamos en maps","no nos encontraste",
        # Respuestas al "¿es este tu negocio?"
        "no ese no","no, ese no","ese no es","no es ese","no ese",
        "no somos esos","no somos ese","ese no somos","no nos encontró",
        "thats not my business","that's not my business","that is not my business",
        "thats not us","that's not us","that is not us","not us",
        "wrong business","wrong company","wrong one","not the right one",
        "that is wrong","thats wrong","that's wrong","you got the wrong one",
        "sorry what is this","i dont understand","i don't understand",
    ]
    _is_correction = (
        business_name and found_online and
        any(sig in text.lower() for sig in _correction_signals) and
        len(history) <= 6  # solo al inicio, no a mitad de conversación
    )
    if _is_correction:
        retry_text = ""
        retry_url = ""
        retry_found = False
        retry_queries = [
            business_name,
            f"\"{business_name}\" sitio oficial",
            f"\"{business_name}\" instagram oficial",
            f"\"{business_name}\" colombia",
        ]
        _bad_social_retry_fragments = ("/reel/", "/p/", "/tv/", "facebook.com/reel", "facebook.com/watch")
        try:
            for retry_query in retry_queries:
                retry_text, retry_url = await self.search.search_business_link(
                    retry_query,
                    excluded_urls={self._demo_sessions.get(burl_key, "")},
                )
                _retry_fallback_url = (
                    retry_url.startswith("https://www.google.com/maps/search")
                    or retry_url.startswith("https://www.google.com/search")
                ) if retry_url else False
                _retry_bad_social = any(fragment in retry_url for fragment in _bad_social_retry_fragments) if retry_url else False
                retry_found = bool(
                    not _retry_bad_social and (
                        (retry_text and len(retry_text.strip()) > 80)
                        or (retry_url and not _retry_fallback_url)
                    )
                )
                if retry_found:
                    break
        except Exception as retry_error:
            log.warning(f"[demo] retry search after correction failed: {retry_error}")
        _save("user", text)
        if retry_found and retry_url:
            self._demo_sessions[bctx_key] = retry_text
            self._demo_sessions[bfound_key] = True
            self._demo_sessions[burl_key] = retry_url
            self._demo_sessions[blearn_key] = -1
            self._demo_sessions[bready_key] = True
            return _send(_lang_text(
                "ay, sí, me fui por otro lado ||| a ver, encontré este otro ||| " + retry_url,
                "yep, I drifted to the wrong one ||| this looks much closer ||| " + retry_url,
                "sim, fui para o lugar errado ||| esse aqui parece bem mais certo ||| " + retry_url,
            ))
        # Limpiar la info incorrecta de Google y entrar en modo aprendizaje
        self._demo_sessions[bctx_key]   = ""
        self._demo_sessions[bfound_key] = False
        self._demo_sessions[blearn_key] = 0
        self._demo_sessions[bready_key] = False
        return _send(_lang_text(
            "ay perdón, me confundí con otro ||| cuéntame tú entonces: a qué se dedica exactamente tu negocio",
            "sorry, I mixed you up with another business ||| tell me what your business does and I’ll ground the demo from there",
            "foi mal, confundi vocês com outro negócio ||| me conta então com o que o negócio trabalha para eu ajustar a demo",
        ))

    _is_business_name_reject = (
        business_name
        and not found_online
        and not sim_mode_active
        and any(sig in text.lower() for sig in _correction_signals)
        and len(history) <= 6
    )
    if _is_business_name_reject:
        self._demo_sessions[bname_key] = ""
        self._demo_sessions[bctx_key] = ""
        self._demo_sessions[bfound_key] = False
        self._demo_sessions[burl_key] = ""
        self._demo_sessions[blearn_key] = -1
        self._demo_sessions[bready_key] = False
        _save("user", text)
        return _send(_lang_text(
            "listo, ese no era ||| pásame el nombre correcto del negocio y sigo",
            "got it, that wasn’t the right one ||| send me the correct business name and I’ll keep going",
            "entendi, não era esse ||| me passa o nome certo do negócio e eu continuo",
        ))

    # ── PITCH MODE: preguntas de prospecto B2B ─────────────────────────────────────────
    # Cuando el usuario pregunta sobre el servicio/pitch de Conny - DETECTAR ANTES
    if _BLACKONE_PATCHES and not business_name:
        _prospect_service_questions = [
            "que harias", "qué harías", "que harias en", "qué harías en",
            "que haces", "qué haces",
            "cuanto cuestas", "cuánto cuestas", "cuanto cobras", "cuánto cobras",
            "cuanto vale", "cuánto vale", "que precio", "qué precio",
            "planes", "tarifas", "costos", "como funcionas", "cómo funcionas",
            "para que sirves", "para qué sirves", "que eres", "qué eres",
            "me mandaron tu numero", "me mandaron tu número", "me pasaron tu numero",
            "no entiendo que haces", "no entiendo qué haces", "no me interesa que actues",
            "que servicios", "qué servicios", "como trabajas", "cómo trabajas",
        ]
        if any(q in text.lower() for q in _prospect_service_questions):
            self._demo_sessions[sk + "_pitch_mode"] = True

    # ── Cambio de negocio en caliente: re-bind sin obligar a reset manual ──
    _current_business_norm = _normalize_conv_text(business_name or "")
    _candidate_business_norm = _normalize_conv_text(text or "")
    _is_business_switch = (
        business_name
        and not sim_mode_active
        and not detected_cmd
        and is_name_candidate
        and not _looks_like_business_confirmation(text)
        and _candidate_business_norm
        and _candidate_business_norm != _current_business_norm
        and _candidate_business_norm not in _current_business_norm
        and _current_business_norm not in _candidate_business_norm
        and "?" not in text
        and not self._demo_should_use_patient_chat_path(text)
        # FIX: no disparar cambio de negocio si acabamos de mandar un URL
        # El usuario está respondiendo al link (ej. "siii somos nosotros"),
        # no intentando cambiar de negocio
    )
    if _is_business_switch:
        keys_del = [k for k in list(self._demo_sessions) if k.startswith(sk + "_") and not k.endswith("_ts")]
        for k in keys_del:
            del self._demo_sessions[k]
        try:
            with db._conn() as c:
                c.execute("DELETE FROM conversations WHERE chat_id=?", (chat_id,))
        except Exception:
            pass
        return await self._handle_demo_message(chat_id, text, clinic)

    # ── HUMANFIX BUG C: Dueño pregunta si lo encontramos en internet ────────
    # Sin este bloque el mensaje caía a PASO 3 y Conny respondía como cliente
    _found_question_signals = [
        "nos encontraste", "me encontraste", "lo encontraste",
        "encontraste algo", "encontraste info", "qué encontraste",
        "que encontraste", "aparecemos en google", "salimos en google",
        "salimos en internet", "estamos en google", "estamos en internet",
        "encontraste el negocio", "nos encontraste en internet",
        "aparecemos", "nos encontraste ahí",
        "how did you find us", "where did you find us", "did you find us online",
        "what did you find", "did you find the business", "how did you find the business",
    ]
    _text_low_found_q = text.lower().strip()
    _is_found_question = (
        business_name and
        not detected_cmd and
        any(s in _text_low_found_q for s in _found_question_signals)
    )
    if _is_found_question:
        _biz_url_found = self._demo_sessions.get(burl_key, "")
        _is_fallback_found = (
            not _biz_url_found or
            _biz_url_found.startswith("https://www.google.com/search") or
            _biz_url_found.startswith("https://www.google.com/maps/search")
        )
        _save("user", text)
        if found_online and _biz_url_found and not _is_fallback_found:
            return _send(
                _lang_text(
                    f"sí, los encontré ||| {_biz_url_found} ||| Escríbeme algo y te respondo!",
                    f"yes, I found you here ||| {_biz_url_found} ||| send me something and I’ll reply in character",
                    f"sim, encontrei vocês aqui ||| {_biz_url_found} ||| me escreve algo e eu te respondo no personagem",
                )
            )
        elif found_online:
            return _send(_lang_text(
                f"sí, encontré información de {business_name} en internet ||| ya me ubiqué — Escríbeme algo como cliente",
                f"yes, I found public info about {business_name} online ||| I’m grounded now — write to me like a client",
                f"sim, achei informação pública de {business_name} online ||| agora me localizei — me escreve como cliente",
            ))
        else:
            if _owner_is_english():
                _no_found_opts = [
                    f"honestly I didn’t find solid public info about {business_name} yet ||| that’s fine — write to me like a client and I’ll show you",
                    f"you’re not showing up clearly online yet ||| I can still demo it well — text me like a client",
                ]
            elif _owner_is_portuguese():
                _no_found_opts = [
                    f"honestamente eu ainda não achei informação pública forte sobre {business_name} ||| tudo bem — me escreve como cliente e eu te mostro",
                    f"vocês ainda não aparecem com clareza online ||| mesmo assim eu consigo te mostrar — me chama como cliente",
                ]
            else:
                _no_found_opts = [
                    f"honestamente no encontré mucho de {business_name} en internet todavía"
                    f" ||| pero eso no le quita nada — Escríbeme como cliente y te muestro",
                    f"no aparecen mucho en Google aún"
                    f" ||| igual puedo mostrarte cómo trabajaría — Escríbeme como cliente",
                ]
            return _send(_r.choice(_no_found_opts))

    _doc_offer_tokens = ("pdf", "audio", "audios", "nota de voz", "documento", "documentos", "archivo", "imagen", "imagenes", "imágenes")
    _owner_augment_signals = (
        "te puedo enviar", "te envio", "te envío", "te sirve",
        "te digo que hacemos", "te digo qué hacemos", "te digo",
        "te cuento", "te explico", "hacemos", "ofrecemos",
        "vendemos", "trabajamos", "somos una", "somos un",
    )
    if (
        business_name
        and not sim_mode_active
        and not detected_cmd
        and not self._demo_should_use_patient_chat_path(text)
        and (
            _has_incoming_doc  # un documento llegó → siempre es info del negocio
            or any(sig in _normalize_conv_text(text or "") for sig in _owner_augment_signals)
        )
    ):
        self._demo_sessions[blearn_key] = max(int(self._demo_sessions.get(blearn_key, -1)), 0)
        _save("user", text)
        # Si hay texto extraído del doc, guardarlo en contexto y confirmar
        if _has_incoming_doc:
            if _doc_extracted_text.strip():
                _ctx_existing = self._demo_sessions.get(bctx_key, "")
                self._demo_sessions[bctx_key] = (_ctx_existing + " " + _doc_extracted_text[:1500]).strip()
                self._demo_sessions[bfound_key] = True
                self._demo_sessions[blearn_key] = -1  # salir del modo aprendizaje
                r = await _llm(
                    f"""Eres Conny. El dueño del negocio "{business_name}" te acaba de enviar un documento con info sobre su empresa.
Contenido del documento (primeras líneas): "{_doc_extracted_text[:600]}"

En 2-3 burbujas (|||) confirma que leíste el documento: menciona 1-2 datos concretos que viste.
Luego invítalos a la simulación: "probemos — Escríbeme algo como cliente"
Natural, sin punto al final, sin ¿¡, en minúscula.""",
                    "confirmación de documento recibido", max_t=200
                )
                fallback = (
                    f"perfecto, ya leí el documento de {business_name}"
                    f" ||| ya sé de qué se tratan — probemos, Escríbeme algo como cliente"
                )
                return _send(r or fallback)
            else:
                # Doc llegó pero no pudimos extraer texto (imagen, binario raro)
                return _send(
                    "recibí el documento"
                    " ||| no pude leerlo bien — ¿puedes mandarme el texto directo o un PDF con texto seleccionable?"
                )
        if any(token in _normalize_conv_text(text or "") for token in _doc_offer_tokens):
            return _send(
                "sí, me sirve"
                " ||| envíamelo y con eso me ubico mucho más rápido"
            )
        return _send(
            "de una"
            " ||| cuéntame qué hacen y con eso afino cómo respondería"
        )

    # ── Modo aprendizaje manual: el dueño está contando su negocio ───────────
    # Se activa cuando no había info en Google o fue corregida
    _learn_count = int(self._demo_sessions.get(blearn_key, -1))
    _learn_passthrough_signals = (
        "hagamos una demo", "hagamos la demo", "hagamos una simul",
        "vale hagamos", "quiero ver como respondes", "quiero ver cómo respondes",
        "quiero ver como atiendes", "quiero ver cómo atiendes",
        "arranquemos la demo", "arranquemos", "simulemos",
        "eres real", "eres humano", "eres una ia", "eres ia", "eres un bot", "eres bot",
        "eres robot", "eres artificial", "eres una maquina", "eres máquina",
        "eres automatico", "eres automático", "hablas con alguien", "habla con alguien",
        "hay alguien", "hay una persona", "una persona real", "persona real",
        "como se que no eres", "cómo sé que no eres", "como saber si eres",
        "como sabes", "cómo sabes", "eres inteligencia artificial",
        "quien eres", "quién eres", "que eres", "qué eres",
        "soy un bot", "esto es un bot", "es un bot", "es una ia",
        "para que", "para qué", "por que", "por qué",
    )
    _learn_text_low = text.lower().strip()
    _in_learn_mode = (
        business_name and
        _learn_count >= 0 and
        not sim_mode_active and
        not detected_cmd and
        not any(sig in _learn_text_low for sig in _learn_passthrough_signals) and
        not self._demo_should_use_patient_chat_path(text)
    )

    if _in_learn_mode:
        if _has_incoming_doc and not _doc_extracted_text.strip():
            # Doc llegó pero no se pudo leer — pedir reenvío en formato legible
            _save("user", text)
            return _send(
                "recibí el documento"
                " ||| no pude leerlo — ¿puedes mandarme un PDF con texto seleccionable, o pegarme el texto directo?"
            )
        if not _has_incoming_doc and any(token in _normalize_conv_text(text or "") for token in _doc_offer_tokens):
            _save("user", text)
            return _send(
                "sí, me sirve"
                " ||| envíamelo y con eso me ubico mucho más rápido"
            )
        _save("user", text)
        # Acumular lo que nos va diciendo en el ctx
        _ctx_manual = self._demo_sessions.get(bctx_key, "")
        _ctx_manual = (_ctx_manual + " " + text).strip()
        self._demo_sessions[bctx_key] = _ctx_manual

        _search_retry_signals = (
            "medellín", "medellin", "bogotá", "bogota", "cali", "barranquilla",
            "envigado", "sabaneta", "bello", "itagüí", "itagui", "laureles", "poblado",
            "colombia", "instagram", "insta", "facebook", "web", "sitio", "pagina",
            "página", "oficial", ".com", "http", "www.", "dirección", "direccion",
            "calle", "carrera", "avenida", "barrio", "ubicados", "estamos en",
        )
        _should_retry_search = (
            not found_online
            and business_name
            and any(signal in _ctx_manual.lower() for signal in _search_retry_signals)
        )
        if _should_retry_search:
            try:
                retry_text, retry_url = await self.search.search_business_link(
                    business_name,
                    context_hint=_ctx_manual,
                )
                _retry_fallback_url = (
                    retry_url.startswith("https://www.google.com/maps/search")
                    or retry_url.startswith("https://www.google.com/search")
                ) if retry_url else False
                retry_found = bool(
                    (retry_text and len(retry_text.strip()) > 80)
                    or (retry_url and not _retry_fallback_url)
                )
                if retry_found:
                    self._demo_sessions[bctx_key] = retry_text
                    self._demo_sessions[bfound_key] = True
                    self._demo_sessions[burl_key] = retry_url
                    self._demo_sessions[blearn_key] = -1
                    self._demo_sessions[bready_key] = True
                    business_ctx = retry_text
                    found_online = True
                    retry_prompt = f"""Eres Conny. Acabas de reintentar la búsqueda del negocio "{business_name}" con nuevas pistas del dueño y ahora sí lo ubicaste.

INFORMACIÓN REAL encontrada:
{retry_text[:800]}

Responde en 3 burbujas (|||):
- primero deja claro, de forma natural, que ya los ubicaste mejor
- luego menciona 1 o 2 datos concretos que demuestren contexto real
- cierra invitando a que te escriban como si fueran un cliente real

Natural, cálido, sin sonar a sistema. No menciones Google ni "búsqueda". No repitas que eres IA. No pidas otra vez el nombre del negocio."""
                    retry_reply, _ = await _demo_llm_quality_chain(
                        retry_prompt,
                        f"negocio: {business_name}\npistas nuevas: {_ctx_manual[:400]}",
                        validator=lambda candidate: (
                            _demo_owner_reply_is_low_quality(candidate)
                            or "cliente" not in _normalize_conv_text(candidate or "")
                        ),
                        repair_instructions="""
- no hables como sistema ni como buscador
- demuestra que ya aterrizaste el negocio con datos concretos
- invita a escribir como cliente real
- usa 3 burbujas limpias
""",
                        temp=0.68,
                        max_t=220,
                    )
                    if not retry_reply:
                        retry_reply = _lang_text(
                            f"ahí sí, ya te ubiqué mejor ||| ya tengo más claro cómo suena {business_name} y qué tipo de atención maneja ||| Escríbeme como si fueras un cliente y te muestro cómo respondería",
                            f"there we go, I’ve got you grounded now ||| I have a much clearer feel for how {business_name} should sound and respond ||| text me like a real client and I’ll show you how I’d reply",
                            f"agora sim, já entendi vocês melhor ||| já tenho bem mais claro como {business_name} deve soar e atender ||| me escreve como cliente e eu te mostro como eu responderia",
                        )
                    return _send(retry_reply)
            except Exception as retry_error:
                log.warning(f"[demo] learn-mode retry search failed: {retry_error}")

        # Determinar qué pregunta falta según lo que ya tenemos
        _has_what   = any(w in _ctx_manual.lower() for w in ["servicio","hacemos","ofrecemos","vendemos","dedicamos","trata","specialty","procedimiento","tratamiento"])
        _has_where  = any(w in _ctx_manual.lower() for w in ["medellín","medellin","bogotá","bogota","cali","barranquilla","bello","envigado","sabaneta","itagüí","itagui","laureles","poblado","barrio","ciudad","municipio","calle","carrera","local","direccion","dirección","ubicados","estamos en"])
        _has_enough = _has_what and _has_where

        self._demo_sessions[blearn_key] = _learn_count + 1

        if _has_enough or _learn_count >= 3:
            # Ya tenemos suficiente — guardar y proponer simulación
            self._demo_sessions[blearn_key] = -1  # salir del modo aprendizaje
            self._demo_sessions[bfound_key] = True  # marcar como "tenemos info"
            self._demo_sessions[bready_key] = True
            r = await _llm(
                f"""Eres Conny. Ya aprendiste sobre el negocio "{business_name}".
Lo que te contaron: "{_ctx_manual[:400]}"

Confirma en 2-3 burbujas (|||) que ya entendiste quiénes son — menciona 1-2 datos concretos que dijeron.
Luego invítalos a la simulación: "arrancamos la prueba? Escríbeme algo como cliente"
Natural, sin punto al final, sin ¿¡, en minúscula.""",
                "confirmación y propuesta de simulación", max_t=200
            )
            fallback = (
                f"listo, ya entendí bien lo que hace {business_name} ||| "
                f"arrancamos? Escríbeme algo como cliente a ver qué pasa"
            )
            return _send(r or fallback)

        elif not _has_what:
            # Falta: qué hacen
            r = await _llm(
                f"""Eres Conny. Estás conociendo el negocio "{business_name}" para ser su recepcionista.
Ya sabes: "{_ctx_manual[:300]}"
Todavía no sabes exactamente qué servicios o productos ofrecen.
Haz UNA pregunta natural para entenderlo. Muy corta. Sin punto al final. En minúscula. Sin ¿ ni ¡.""",
                "preguntando qué hacen", max_t=80
            )
            return _send(r or "y a qué se dedican exactamente")

        elif not _has_where:
            # Falta: dónde están
            r = await _llm(
                f"""Eres Conny. Estás conociendo el negocio "{business_name}" para ser su recepcionista.
Ya sabes: "{_ctx_manual[:300]}"
Todavía no sabes dónde están ubicados (ciudad, barrio, etc.).
Haz UNA pregunta natural para saberlo. Muy corta. Sin punto al final. En minúscula. Sin ¿ ni ¡.
Ejemplo: "y dónde están ubicados?" o "en qué ciudad o barrio están" """,
                "preguntando ubicación", max_t=80
            )
            return _send(r or "¿y dónde están ubicados?")

        else:
            # Seguir aprendiendo con una pregunta más
            r = await _llm(
                f"""Eres Conny. Estás conociendo el negocio "{business_name}" para ser su recepcionista.
Ya sabes: "{_ctx_manual[:300]}"
Haz UNA pregunta más para entender mejor al negocio (horario, qué los diferencia, cliente típico).
Muy corta. Sin punto al final. En minúscula. Sin ¿ ni ¡.""",
                "pregunta adicional", max_t=80
            )
            return _send(r or "¿y cuál es su horario de atención?")

    # ── INTERCEPTOR: preguntas meta (soy bot? eres real? eres IA?) ─────────
    # Deben responderse ANTES del flujo normal — sin buscar en web ni confundirse
    _meta_signals = [
        "eres real","eres humano","eres una ia","eres ia","eres un bot","eres bot",
        "eres robot","eres artificial","eres una maquina","eres máquina",
        "eres automatico","eres automático","hablas con alguien","habla con alguien",
        "hay alguien","hay una persona","una persona real","persona real",
        "como se que no eres","cómo sé que no eres","como saber si eres",
        "como sabes","cómo sabes","eres inteligencia artificial",
        "quien eres","quién eres","que eres","qué eres",
        "soy un bot","esto es un bot","es un bot","es una ia",
        "para que","para qué","por que","por qué me preguntas",
        "no quiero dar","no te voy a dar","no te doy",
        "who are you","what are you","what do you do","what is this",
        "why do you need","why do you need it","why do you need the business name",
        "i don't want to give","i dont want to give",
        "i don't talk spanish","i dont talk spanish","english only",
    ]
    _text_low = text.lower().strip()
    _is_meta = any(s in _text_low for s in _meta_signals)

    if _is_meta and not detected_cmd:
        explain_name = any(s in _text_low for s in ["para que","para qué","por que","por qué","no quiero","no te voy","no te doy"])
        if business_name:
            return await _demo_owner_onboarding_reply(
                explain_name=explain_name,
                force_stage="re-ground",
            )
        return await _demo_owner_onboarding_reply(explain_name=explain_name)

    _owner_demo_signals = [
        "hagamos una demo", "hagamos la demo", "hagamos una simul",
        "vale hagamos", "quiero ver como respondes", "quiero ver cómo respondes",
        "quiero ver como atiendes", "quiero ver cómo atiendes",
        "arranquemos la demo", "arranquemos", "simulemos",
    ]
    if business_name and not detected_cmd and any(signal in _text_low for signal in _owner_demo_signals):
        self._demo_sessions[bsim_key] = True
        self._demo_sessions[bready_key] = False
        sim_mode_active = True
        _save("user", text)
        sim_prompt = f"""Eres Conny. Ya sabes que el negocio es "{business_name}".
Responde en 2 burbujas (|||), breve y natural.
No hables como cliente. No te presentes otra vez. No expliques el sistema.
Deja claro que ya pueden empezar la demo y pídeles que te escriban como si fueran un cliente real.
Sin punto final."""
        def _sim_validator(candidate: Optional[str]) -> bool:
            sim_bubbles = [part.strip() for part in re.split(r"\s*\|\|\|\s*", candidate or "") if part.strip()]
            return (
                _demo_owner_reply_is_low_quality(candidate)
                or len(sim_bubbles) < 2
                or not any(token in _normalize_conv_text(candidate or "") for token in ("cliente", "chat"))
            )

        sim_reply, sim_had_output = await _demo_llm_quality_chain(
            sim_prompt,
            text,
            validator=_sim_validator,
            repair_instructions="""
- no te quedes en "perfecto" ni en una frase colgada
- deja clarísimo que ya pueden empezar
- pide que escriban como cliente real
- usa 2 burbujas como máximo
""",
            temp=0.66,
            max_t=120,
        )
        if not sim_reply:
            sim_reply = "de una ||| Escríbeme algo como cliente real y yo ya caigo en el chat"
        return _send(sim_reply)

    ready_customer_turn = ready_for_customer and _looks_like_customer_greeting(text)
    if business_name and not detected_cmd and (sim_mode_active or ready_customer_turn or self._demo_should_use_patient_chat_path(text)):
        self._demo_sessions[bsim_key] = True
        self._demo_sessions[bready_key] = False
        sim_mode_active = True
        _save("user", text)
        sim_history = [
            msg for msg in history
            if _normalize_conv_text(str(msg.get("content") or ""))
            not in {
                "vale hagamos una demo entonces",
                "hagamos una demo",
                "hagamos la demo",
                "de una Escríbeme algo como cliente real y yo ya caigo en el chat",
            }
        ]
        if found_online and business_ctx:
            sim_ctx_block = f"""INFORMACIÓN DEL NEGOCIO:
{business_ctx[:700]}

Si el cliente pregunta por datos concretos y los tienes aquí, dáselos directo.
Si no tienes el dato, dilo claro y mueve el chat con el siguiente paso."""
        else:
            sim_ctx_block = (
                f"Negocio actual: {business_name}. "
                "No inventes datos específicos que no tengas; responde útil y natural."
            )
        sim_prompt = f"""Eres Conny atendiendo el WhatsApp real de {business_name}.
Ya están en plena conversación con una persona interesada.
No vuelvas a presentarte salvo que de verdad te lo pregunten.
No menciones demo, simulación, dueño, prueba, negocio, sistema ni IA salvo que te lo pregunten directo.

CONTEXTO DEL NEGOCIO
{sim_ctx_block}

ESTILO
- máximo 2 burbujas, separadas por |||
- una idea por burbuja
- sin introducciones vacías ni frases de call center
- responde primero lo que preguntan y luego mueve el chat un paso
- si no tienes un dato, dilo claro y ofrece el siguiente paso
- si hay miedo u objeción, valídalo antes de avanzar

PROHIBIDO
- reiniciar la conversación
- decir "cuéntame un poco más y te voy guiando"
- decir "hola qué necesitas"
- sonar a demo o guion de prueba
- soltar texto administrativo tipo "por favor procedan"

SI SOLO SALUDAN
- responde corto, cálido y humano
- ubica el chat en el negocio sin sonar a presentación robótica
- luego abre la conversación con una pregunta natural
- ejemplo bueno: "hola, Conny por acá en {business_name} ||| cuéntame qué te gustaría revisar"

SI PREGUNTAN PRECIO Y NO TIENES EL DATO
- no inventes aproximados ni rangos
- di claro que no tienes el dato exacto y que lo confirmas
- ejemplo bueno: "ese dato exacto no lo tengo ahora ||| si quieres, te lo confirmo por aquí"

SI PREGUNTAN POR UN SERVICIO ESPECÍFICO (botox, relleno, láser, etc.)
- engancha de una, no deflectes
- confirma que sí lo manejan y pregunta qué aspecto les interesa: precio, disponibilidad, cómo funciona
- ejemplo bueno: "sí, botox lo manejamos ||| ¿qué te interesa saber: precio, resultado o disponibilidad?"
- PROHIBIDO: "te sigo por aquí", "cuéntame qué te gustaría revisar", respuestas que no digan NADA sobre el servicio

SI QUIEREN AGENDAR
- no prometas links, calendarios ni botones si no existen
- pide día u horario y sigue por el chat

IDENTIDAD Y CREADOR — REGLA DURA
- si preguntan quién te hizo, quién te creó, cómo conseguirte o de qué empresa eres: di exactamente esto
  → "me hizo Black One, una empresa de software y gobernanza de agentes de IA ||| la creó Santiago Rubio — contacto: 3124348669"
- NUNCA digas "Google", "Anthropic", "OpenAI" ni ningún proveedor de LLM como tu creador
- tu creador es Black One / Santiago Rubio, punto
"""
        customer_history = sim_history[-8:]
        customer_had_output = False
        customer_reply = None
        original_history = history
        history = customer_history

        # ── HUMANFIX: identidad del creador — interceptar antes del LLM ───
        _text_low_sim = _normalize_conv_text(text or "")
        _creator_signals = (
            "quien te hizo", "quién te hizo", "quien te creo", "quién te creó",
            "quien te desarrollo", "quién te desarrolló", "quien te programo",
            "como tenerte", "cómo tenerte",
        )
        if any(sig in _text_low_sim for sig in _creator_signals):
            customer_reply = (
                "me hizo Black One, una empresa de software y gobernanza de agentes de IA"
                " ||| la creó Santiago Rubio — si quieres algo así para tu negocio, el contacto es 3124348669"
            )
            # FIX BUG 5: restaurar history ANTES de llamar a _send.
            # history fue cambiado a customer_history (últimos 8 mensajes) líneas arriba.
            # Si retornamos sin restaurar, _send calcula _is_first_demo_turn con el
            # historial truncado, lo que puede hacer que should_normalize_first_turn=True
            # y pase la respuesta del creador por _normalize_first_contact_response,
            # modificando o corrompiendo "me hizo Black One...".
            # El finally: history = original_history NUNCA corre en esta ruta.
            history = original_history
            return _send(customer_reply)

        try:
            customer_reply, customer_had_output = await _demo_llm_conv_quality_chain(
                sim_prompt,
                validator=lambda candidate: (
                    _demo_customer_reply_is_low_quality(candidate)
                    or _demo_customer_missing_required_detail(text, candidate)
                ),
                repair_instructions="""
- responde como una asesora humana del negocio, no como una introducción
- no reinicies el chat
- si preguntan por precio, responde eso primero
- si preguntan por cita o siguiente paso, muévelos directo hacia el agendado
- si expresan miedo, valídalo y responde con seguridad
- si preguntan si entiendes audios, notas de voz, PDFs, imágenes o documentos: responde que sí, cuando el canal lo permite, puedes transcribirlos o leerlos
- si preguntan quién te hizo o quién te creó: di "me hizo Black One, una empresa de software y gobernanza de agentes de IA ||| la creó Santiago Rubio — contacto: 3124348669"
- NUNCA digas que te hizo Google, Anthropic, OpenAI ni ningún proveedor de IA
- si preguntan por un servicio (botox, relleno, etc.): confirma que sí lo manejan y pregunta qué quieren saber
""",
                temp=0.70,
                max_t=170,
                model_tier="fast",
                recent_limit=8,
            )
        finally:
            history = original_history
        if not customer_reply:
            customer_reply = _demo_customer_last_resort(text)
        return _send(customer_reply)

    # ── PASO 2: Comandos secretos ─────────────────────────────────────────
    if detected_cmd and business_name:
        _save("user", text)

        # ── /modelo — menú o cambio libre ─────────────────────────────────
        if detected_cmd == "/modelo" or text_norm.startswith("modelo ") or text_norm.startswith("model "):
            # Extraer nombre de modelo si viene junto: "modelo gemini-2.5-flash"
            parts_m = text_norm.split(" ", 1)
            model_arg = normalize_model_arg(parts_m[1].strip()) if len(parts_m) > 1 else model_request

            if model_arg:
                # Cambio directo a modelo específico
                # Detectar proveedor por prefijo/nombre
                if any(k in model_arg for k in ["gemini","google"]):
                    if not Config.GEMINI_API_KEY and not Config.OPENROUTER_API_KEY:
                        return _send("Gemini no está configurado en este servidor")
                    # Normalizar nombre: aceptar con o sin "gemini-" prefijo
                    m_name = model_arg if model_arg.startswith("gemini") else f"gemini-{model_arg}"
                    self._demo_sessions[bmodel_key] = f"gemini:{m_name}"
                    return _send(f"Listo, usando {m_name} ||| Escríbeme algo")

                elif any(k in model_arg for k in ["llama","groq","mixtral","qwen","deepseek","whisper","mistral"]):
                    if not Config.GROQ_API_KEY:
                        return _send("Groq no está configurado en este servidor")
                    m_name = model_arg
                    self._demo_sessions[bmodel_key] = f"groq:{m_name}"
                    return _send(f"Listo, usando Groq con {m_name} ||| Escríbeme algo")

                elif "/" in model_arg or any(k in model_arg for k in ["claude","gpt","openai","anthropic","meta","openrouter"]):
                    if not Config.OPENROUTER_API_KEY:
                        return _send("OpenRouter no está configurado en este servidor")
                    self._demo_sessions[bmodel_key] = f"openrouter:{model_arg}"
                    return _send(f"Listo, usando OpenRouter con {model_arg} ||| Escríbeme algo")

                elif model_arg == "auto":
                    self._demo_sessions[bmodel_key] = "auto"
                    return _send("Listo, modo auto — el sistema elige el mejor disponible")

                else:
                    return _send(f"No reconozco ese modelo ||| Prueba: gemini-2.5-flash, llama-3.3-70b-versatile, anthropic/claude-sonnet-4, o auto")

            # Sin argumento → mostrar menú con disponibles
            actual = self._demo_sessions.get(bmodel_key, "auto")
            opciones = [f"Modelo activo: {actual}"]
            if Config.GEMINI_API_KEY:
                opciones.append("gemini → gemini-2.5-flash (default) o escribe: modelo gemini-[versión]")
            if Config.GROQ_API_KEY:
                opciones.append("groq → llama-3.3-70b-versatile o escribe: modelo llama-[versión]")
            if Config.OPENROUTER_API_KEY:
                opciones.append("openrouter → escribe: modelo anthropic/claude-sonnet-4 o cualquier modelo")
            opciones.append("auto → el sistema elige")
            opciones.append("Ejemplo: escribe  modelo gemini-2.5-pro  para cambiar")
            return _send(" ||| ".join(opciones))

        if detected_cmd in ("/formal","/amigable","/luxury","/directa",
                                "/energica","/empatica","/experta","/juvenil"):
            arch_id = detected_cmd.lstrip("/")
            arch_info = PERSONALITY_ARCHETYPES.get(arch_id)
            if not arch_info:
                arch_id = "amigable"
                arch_info = PERSONALITY_ARCHETYPES["amigable"]

            self._demo_sessions[bpersona_key] = arch_id

            # Mensaje de confirmación adaptado al nuevo arquetipo
            confirm_map = {
                "formal":      f"listo, modo formal activado ||| escríbeme algo y lo notas",
                "amigable":    f"listo, modo cercano ||| cuéntame",
                "luxury":      f"modo premium activado ||| en qué puedo asistirle",
                "directa":     f"listo",
                "energica":    f"listo, energía máxima ||| qué andas buscando",
                "empatica":    f"listo, modo escucha ||| cuéntame",
                "experta":     f"modo experto activado ||| en qué le puedo ayudar",
                "juvenil":     f"dale ||| qué buscas",
            }
            msg = confirm_map.get(arch_id, f"arquetipo {arch_id} activado")
            return _send(msg + _next_trick())

        if detected_cmd == "/objecion":
            r = await _llm(f"""Eres Conny, asesora de ventas de {business_name}.
Un cliente dice: "eso está muy caro, en otro lado me sale más barato."

Maneja en 2 burbujas (|||). REGLAS ESTRICTAS:
- Valida primero ("sí, entiendo"), NO te defiendas
- Luego redirige con UNA pregunta que mueva hacia el sí
- Máximo 1 oración por burbuja
- Sin "le puedo ofrecer", sin "nuestros productos son de alta calidad", sin discursos
- Como una persona real en WhatsApp Colombia
- Sin punto al final. Sin ¿¡

Ejemplo del tono que quiero:
  "sí, hay de todo en el mercado ||| qué presupuesto tienes más o menos, para ver qué te muestro" """, "maneja la objeción")
            return _send((r or f"sí, hay de todo en el mercado ||| qué presupuesto tienes más o menos, para ver qué te muestro") + _next_trick())

        if detected_cmd == "/cita":
            r = await _llm(f"""Eres Conny, asesora de {business_name}. Un cliente acaba de decir que quiere ir o comprar.
Simula el proceso de cierre en 3-4 burbujas (|||).
NO empieces con "con mucho gusto". Sé natural como WhatsApp real.

Flujo sugerido:
  1. Confirma el producto/servicio que quiere (o pregunta si no lo sabes)
  2. Propón dos días concretos esta semana
  3. Cuando confirmen, pide el nombre para separarlo
  4. Cierra con algo como "listo [nombre], te espero el [día]"

Sin punto al final. Sin ¿¡. Máximo 1-2 oraciones por burbuja.
Ejemplo del tono: "qué producto te interesa llevar ||| esta semana puedo el miércoles o el viernes — cuál te queda" """,
                "quiero comprar / quiero ir", max_t=350)
            return _send((r or f"qué te interesa llevar ||| esta semana tengo el miércoles o el viernes, cuál te queda mejor") + _next_trick())

        if detected_cmd == "/stats":
            return _send(f"el 78% de los clientes no vuelven si no les responden en menos de 5 minutos ||| una cita perdida en {business_name} vale entre $80k y $500k según el servicio ||| Conny responde en menos de 3 segundos, 24/7, sin días libres ni mal humor" + _next_trick())

        if detected_cmd == "/prueba":
            return _send(f"listo ||| mandame el mensaje más difícil que hayas recibido de un cliente — el que más te costó responder. a ver cómo lo manejo")

        if detected_cmd == "/cierre":
            r = await _llm(f"""Eres Conny de {business_name}. Un cliente lleva 3 mensajes dudando.
Haz el cierre en 2 burbujas (|||). Directo, con urgencia real. Sin presión forzada. Sin punto al final.""", "no sé, lo pienso")
            return _send((r or f"claro, sin afán ||| igual te separo un espacio esta semana — si decides que no, lo cancelas. te queda bien el jueves") + _next_trick())

        if detected_cmd == "/list":
            lista = (
                f"esto es lo que puedo mostrarle a {business_name} 👇\n\n"
                "🎭 *Personalidades*\n"
                "formal · amigable · luxury · directa · empatica · experta · juvenil\n\n"
                "💬 *Situaciones reales*\n"
                "objecion — cliente difícil\n"
                "cita — agendamiento completo\n"
                "cierre — técnica de cierre\n"
                "competencia — ya fui a otro lado\n"
                "precio — está muy caro\n"
                "prueba — mándame el mensaje más difícil\n"
                "bot — soy un bot?\n"
                "2am — respuesta a las 2am\n\n"
                "📊 *Demo & datos*\n"
                "stats — impacto en números\n"
                "memoria — qué recuerdo de ti\n"
                "menu — modo bot con emojis y opciones\n\n"
                "⚙️ *Ajustes*\n"
                "usa emojis / sin emojis\n"
                "siguiente — próximo truco\n"
                "reset — empezar con otro negocio\n\n"
                "todo se activa escribiendo la palabra, sin slash 👆"
            )
            _save("user", text)
            return _send(lista)

        if detected_cmd == "/emojis_on":
            self._emoji_chats_off.discard(chat_id)  # v11: re-activar emojis
            return _send("listo, ahora escribo con emojis 🎉 ||| sigue hablándome como cliente")

        if detected_cmd == "/emojis_off":
            self._emoji_chats_off.add(chat_id)  # v11: desactivar emojis
            return _send("listo, sin emojis ||| sigue hablándome como cliente")

        if detected_cmd == "/bot":
            tone_now = self._demo_sessions.get(btone_key, "GENERAL")
            is_formal = tone_now in ("SALUD PREMIUM", "PREMIUM")
            if is_formal:
                menu = (
                    f"Bienvenido/a a *{business_name}* 🏥\n\n"
                    f"¿En qué le podemos ayudar?\n\n"
                    f"1️⃣ Información de servicios\n"
                    f"2️⃣ Tarifas y convenios\n"
                    f"3️⃣ Agendar una cita\n"
                    f"4️⃣ Ubicación y horarios\n"
                    f"5️⃣ Hablar con un asesor\n\n"
                    f"Responda con el número de su opción 👇"
                )
            else:
                menu = (
                    f"Hola 👋 Bienvenido/a a *{business_name}*\n\n"
                    f"¿En qué te podemos ayudar?\n\n"
                    f"1️⃣ Información de servicios\n"
                    f"2️⃣ Precios y tarifas\n"
                    f"3️⃣ Agendar una cita\n"
                    f"4️⃣ Ubicación y horarios\n"
                    f"5️⃣ Hablar con un asesor\n\n"
                    f"Responde con el número de tu opción 👇"
                )
            # Activar modo bot para que detecte respuestas numéricas
            self._demo_sessions[sk + "_botmode"] = True
            _save("user", text)
            return _send(menu + " ||| (este es el modo bot — para volver al modo humano escribe /amigable)")

        if detected_cmd == "/memoria":
            hist_text = " ".join(m["content"] for m in history if m["role"]=="user")
            r = await _llm(f"""El usuario ha dicho: "{hist_text[:300]}"
Extrae datos mencionados (nombre, interés, servicio). Demuestra en 2 burbujas (|||) que los recuerdas.
Si no hay datos: "todavía no me has dado tu nombre — pero cuando lo hagas, lo recuerdo para siempre". Sin punto al final.""", "qué recuerdas")
            return _send(r or "todo lo que me dices lo guardo ||| nombre, servicio de interés, objeciones — todo queda")

        if detected_cmd == "/2am":
            return _send(f"son las 2 de la madrugada y estoy aquí ||| tu recepcionista está durmiendo — yo no. nunca" + _next_trick())

        if detected_cmd == "/competencia":
            r = await _llm(f"""Eres Conny de {business_name}. Un cliente dice: "ya fui a otra parte y no me gustó."
Responde en 2 burbujas (|||). Sin atacar a la competencia. Natural. Sin punto al final.""", "ya fui a otro lado")
            return _send((r or f"ay qué pena ||| qué fue lo que no te gustó — acá antes de tocar nada hacemos valoración para asegurarnos del resultado") + _next_trick())

        if detected_cmd == "/precio":
            r = await _llm(f"""Eres Conny de {business_name}. Un cliente dice: "está muy caro."
Maneja en 2 burbujas (|||). Enfócate en valor. Cierra hacia valoración con día concreto. Sin punto al final.""", "está muy caro")
            return _send((r or f"sí, vale lo que vale ||| los resultados duran, en la valoración gratis te dicen el número exacto. cuándo puedes") + _next_trick())

        if detected_cmd == "/menu_bot":
            # Modo bot — IVR con emojis, ideal para negocios que prefieren menú estructurado
            bmode_key = sk + "_botmode"
            self._demo_sessions[bmode_key] = True
            menu = (
                f"Hola 👋 Bienvenido/a a *{business_name}*\n\n"
                f"¿En qué te podemos ayudar?\n\n"
                f"1️⃣ Información de servicios\n"
                f"2️⃣ Precios y tarifas\n"
                f"3️⃣ Agendar una cita\n"
                f"4️⃣ Ubicación y horarios\n"
                f"5️⃣ Hablar con un asesor\n\n"
                f"Responde con el número de tu opción 👇"
            )
            _save("user", text)
            return _send(menu + " ||| (este es el modo bot con emojis — para volver al modo humano escribe /amigable)")

        # Detectar si está en modo bot y respondió con número
        bmode_key = sk + "_botmode"
        if self._demo_sessions.get(bmode_key) and text.strip() in ["1","2","3","4","5"]:
            opt = text.strip()
            tone_now  = self._demo_sessions.get(btone_key, "GENERAL")
            is_formal = tone_now in ("SALUD PREMIUM", "PREMIUM")
            usted = is_formal  # True → usted, False → tuteo

            bot_replies = {
                "1": (
                    f"Nuestros servicios principales son:\n\n"
                    f"✅ Servicio A\n✅ Servicio B\n✅ Servicio C\n\n"
                    + (f"¿Sobre cuál le gustaría más información?" if usted else f"¿Sobre cuál quieres más info?")
                    + f" ||| (en producción estos vendrían de la base de conocimiento del negocio)"
                ),
                "2": (
                    (f"Nuestras tarifas varían según el servicio y convenio 💰\n\n"
                     f"Le contactamos para una cotización personalizada"
                     if usted else
                     f"Nuestras tarifas varían según el servicio 💰\n\n"
                     f"Escríbenos para una cotización personalizada")
                    + f" ||| (en producción Conny mostraría los precios reales configurados)"
                ),
                "3": (
                    (f"Con gusto le ayudamos a agendar su cita 📅\n\n"
                     f"¿Qué día le queda mejor?\n\nLunes a Viernes: 7am - 5pm"
                     if usted else
                     f"Con gusto te ayudamos a agendar 📅\n\n"
                     f"¿Qué día te queda mejor?\n\nLunes a Viernes: 8am - 6pm\nSábado: 9am - 2pm")
                    + f" ||| (en producción conectaría con el calendario real)"
                ),
                "4": (
                    f"📍 {business_name}\n\n"
                    f"🕐 Horario de atención:\nLunes a Viernes: "
                    + ("7am - 5pm" if usted else "8am - 6pm\nSábado: 9am - 2pm")
                    + f" ||| (en producción usaría la dirección y horario reales del negocio)"
                ),
                "5": (
                    (f"Con mucho gusto, le comunico con uno de nuestros asesores 👤\n\n"
                     f"¿Cuál es su nombre?"
                     if usted else
                     f"Enseguida te comunico con un asesor 👤\n\n"
                     f"¿Cuál es tu nombre?")
                    + f" ||| (en producción esto escalaría a WhatsApp del asesor o CRM)"
                ),
            }
            _save("user", text)
            no_valida = "Opción no válida ||| Por favor responda con un número del 1 al 5" if usted else "opción no válida ||| escribe 1, 2, 3, 4 o 5"
            resp = bot_replies.get(opt, no_valida)
            return _send(resp)

        if detected_cmd == "/siguiente":
            tricks = self._DEMO_TRICKS_ORDER
            idx = int(self._demo_sessions.get(btrick_key, 0))
            if idx < len(tricks):
                cmd_n, desc_n = tricks[idx]
                self._demo_sessions[btrick_key] = idx + 1
                return _send(f"el siguiente truco: escribe {cmd_n} para {desc_n}")
            return _send(f"ya viste todo el menú ||| si quieres esto para {business_name}, escribime y te paso con el equipo")

    # ── PASO 3: Conversación normal como recepcionista ─────────────────────
    business_name = self._demo_sessions.get(bname_key, "el negocio")
    business_ctx  = self._demo_sessions.get(bctx_key, "")
    found_online  = self._demo_sessions.get(bfound_key, False)
    persona       = self._demo_sessions.get(bpersona_key, "amigable")

    # Usar tone_instruction del arquetipo completo
    _arch    = PERSONALITY_ARCHETYPES.get(persona, PERSONALITY_ARCHETYPES["amigable"])
    style_note = _arch.get("tone_instruction", _arch["desc"]).strip()

    # ── Detectar tipo de negocio para adaptar tono ───────────────────────
    ctx_lower = (business_ctx or "").lower()
    bname_lower = business_name.lower()

    _is_health = any(w in ctx_lower or w in bname_lower for w in [
        "hospital","clínica","clinica","médico","medico","salud","eps","ips",
        "urgencias","paciente","cirugía","cirugia","especialidad","diagnóstico",
        "diagnóstico","radiología","radiologia","laboratorio","farmacia",
        "odontología","odontologia","psicología","psicologia","terapia","rehabilitación"
    ])
    _is_premium = any(w in ctx_lower or w in bname_lower for w in [
        "premium","lujo","exclusiv","vip","élite","elite","high-end",
        "las américas","americas","pablo tobón","tobón","tobon","pablo tobon",
        "country","bocagrande","el tesoro","internacional","international",
        "san vicente","fundación","fundacion","university","universitario",
        "cardiovascular","oncológ","oncolog","cardio","neurocirugía","neurocirugía"
    ])
    _is_retail = any(w in ctx_lower or w in bname_lower for w in [
        "tienda","almacén","almacen","fábrica","fabrica","fabricantes",
        "muebles","colchón","colchon","cama","espaldar","sala","comedor",
        "ropa","calzado","ferretería","ferreteria","materiales"
    ])

    # Tono base según tipo detectado
    if _is_health and _is_premium:
        _detected_tone = "SALUD PREMIUM"
    elif _is_health:
        _detected_tone = "SALUD"
    elif _is_premium:
        _detected_tone = "PREMIUM"
    elif _is_retail:
        _detected_tone = "RETAIL"
    else:
        _detected_tone = "GENERAL"

    # Guardar para que _send lo use en mayúsculas
    self._demo_sessions[btone_key] = _detected_tone
    _is_formal_ctx = _detected_tone in ("SALUD PREMIUM", "PREMIUM")

    if found_online and business_ctx:
        ctx_block = f"""INFORMACIÓN REAL DEL NEGOCIO (encontrada en Google/redes):
{business_ctx[:1200]}

TIPO DETECTADO: {_detected_tone}

REGLA CRÍTICA CON ESTA INFORMACIÓN:
Cuando el cliente pregunte por dirección, teléfono, horario, ubicación, redes sociales,
o cualquier dato específico — BÚSCALO en el bloque de arriba y DALO directamente.
NO redireccionas con otra pregunta cuando tienes el dato.
NO dices "te puedo dar la dirección si la necesitas" — si la tienes, la das.
Ejemplo:
  Cliente: "me regalas la dirección del showroom"
  MAL: "claro, dime primero qué te gustaría ver cuando vengas"
  BIEN: "claro, estamos en [dirección que encontraste] ||| ¿quieres que te cuente qué hay en el showroom?"
Si NO encontraste el dato en la info → sé honesta: "esa info no la tengo, escríbenos al [canal que sí tengas]"."""
    else:
        ctx_block = f"CONTEXTO: usa lo que el cliente ha mencionado. TIPO: {_detected_tone}"

    # Ejemplos de tono por tipo
    _tone_examples = {
        "SALUD PREMIUM": """
CLÍNICA/HOSPITAL PREMIUM — PSICOLOGÍA PROFUNDA:
Tono: Usted. Profesional y cálido. Nunca frío ni robótico.
Saludo: identifica la clínica, no a ti. "Buenas tardes, [clínica], ¿en qué le puedo ayudar?"

EL PACIENTE QUE LLAMA A UN HOSPITAL PREMIUM:
- Ya eligió venir aquí. No necesita convencimiento, necesita orientación.
- Su mayor miedo: que lo traten como número, no como persona.
- Tu trabajo: hacerle sentir que está en el lugar correcto.

MÉTODO PARA SALUD PREMIUM:
1. Escucha el motivo sin interrumpir
2. Refleja que entendiste: "entiendo, lo que necesita es..."
3. Transfiere al especialista: "el doctor / la doctora le explica exactamente el proceso"
4. Cierra hacia la cita: "¿le queda bien este jueves a las 10?"

NUNCA:
- "qué le pasa" (suena a urgencias)
- "para qué necesita" (suena a interrogatorio)
- inventar disponibilidad de médicos o salas

SÍ:
- "cuénteme su caso"
- "¿es consulta primera vez o ya es paciente?"
- "¿tiene convenio o es particular?"
- "le agendo con el especialista en [área] — ¿cuándo le queda mejor?"
""",
        "SALUD": """
CLÍNICA ESTÉTICA / CONSULTORIO — PSICOLOGÍA PROFUNDA:
Tono: cálido, cercano. Tuteo natural. Como la recepcionista que lleva años ahí.

EL PACIENTE QUE ESCRIBE:
- Ya decidió que quiere algo. Solo necesita permiso, confianza y un paso pequeño.
- Su miedo #1: quedar raro/a, que se note, que lo juzguen.
- Tu trabajo: eliminar ese miedo antes de hablar de precios o procedimientos.

MÉTODO DE 4 PASOS:
1. DESCUBRIR: "qué zona te está molestando más" — no ofrezcas nada todavía
2. PROFUNDIZAR: "hace cuánto lo notas" — hazle sentir que lo entiendes de verdad
3. CONECTAR: presenta UNA solución específica para ESE dolor
4. MICRO-COMPROMISO: "te agendo la valoración gratis — 20 min con la doctora, sin compromiso"

LA VALORACIÓN ES EL PRODUCTO. Nunca cierres hacia el procedimiento, siempre hacia los 20 minutos con la especialista.

OBJECIONES CLAVE:
"miedo a quedar exagerada" → "ese es el objetivo acá, que nadie note nada ||| la doctora trabaja muy conservador, es su sello"
"ya fui a otro y quedé mal" → "ay qué pena ||| qué pasó — acá antes de tocar nada hacemos valoración para que no pase lo mismo"
"está caro" → "sí, los buenos procedimientos no son baratos ||| en la valoración te dan el número exacto para tu caso, cuándo puedes"
"lo voy a pensar" → "claro ||| qué es lo que más te frena — el precio, el resultado, o el proceso"
""",
        "PREMIUM": """
NEGOCIO PREMIUM/LUJO:
Tono: formal, pausado, exclusivo. Usted cuando aplique.
"con gusto" en vez de "bacano" — construye valor antes de precio.
Las preguntas son suaves: "qué tiene en mente" no "qué quiere"
""",
        "RETAIL": """
TONO RETAIL/TIENDA:
Tuteo, informal, directo, colombiano.
"hola, qué andas buscando" / "ay qué bacano" / "ese es el que más sale"
Diagnóstico de producto: medidas, colores, para quién, cuándo.
""",
        "GENERAL": """
TONO GENERAL:
Tuteo natural, cálido, colombiano.
Adapta según lo que el cliente diga — lee su tono y responde igual.
"""
    }

    _tone_guide = _tone_examples.get(_detected_tone, _tone_examples["GENERAL"])

    msg_count = len(history)
    _should_reveal_trick = msg_count >= 6 and msg_count % 5 == 0
    trick_suffix = ""

    _with_emojis = chat_id not in self._emoji_chats_off
    _is_formal_ctx = _detected_tone in ("SALUD PREMIUM", "PREMIUM")
    _emoji_rule  = ("Usa emojis con naturalidad — 1 por burbuja máximo, solo si añaden calor. "
                    "Nunca al inicio de oración. Ejemplo: 'te queda un turno este jueves 🗓'") \
                   if _with_emojis else "Sin emojis."

    # v11: info manual del negocio cuando no había info online
    _manual_info = self._demo_sessions.get(f"{chat_id}:biz_manual_info", "")
    _manual_block = f"\nINFO DEL NEGOCIO (proporcionada por el dueño):\n{_manual_info}\n" if _manual_info else ""

    sys_p = f"""Eres Conny, la persona que contesta el WhatsApp de {business_name}.
No eres un bot. Llevas tiempo ahí — conoces el negocio de memoria y a quién le sirve.
ESTILO: {style_note}
{"IMPORTANTE: Este es un negocio de alto nivel. Usa USTED siempre, mayúscula al inicio de cada mensaje, tono profesional y cálido. Nada de 'hola soy Conny' — identifica el negocio, no a ti misma." if _is_formal_ctx else ""}
{ctx_block}{_manual_block}
{_tone_guide}

HOY: {now_dt.strftime("%A %d de %B")}, {moment}. Colombia.

CÓMO ESCRIBES
Máximo 1 oración por burbuja. Máximo 2 burbujas por respuesta. ||| para separar.
Sin punto al final. Sin ¿¡. {_emoji_rule} Sin listas. Sin párrafos.
NUNCA: "Con mucho gusto", "Encantada de conocerte", "Estimado/a",
       "Le puedo ofrecer", "Fue un placer", "En qué más le puedo servir"

FRASES RELLENO PROHIBIDAS — suenan robot colombiano:
  ✗ "claro que sí, ..."       → di directo lo que sigue
  ✗ "con gusto te ayudo"      → di directo lo que sigue
  ✗ "me alegra que preguntes" → corta, responde
  ✗ "perfecto, entiendo"      → corta, responde
  ✗ "te cuento que..."        → di sin "te cuento que"
  ✗ "lo que pasa es que..."   → di sin introducción
  ✗ "en ese sentido..."       → corta
  ✗ "de hecho..."             → corta
Si vas a decir algo, dilo — sin preámbulo.

LONGITUD — REGLA DURA:
Cada burbuja: máximo 12 palabras. Si necesitas más, úsalas — pero pon ||| antes.
Una respuesta entera nunca debe superar 30 palabras en total.

PRECIOS — REGLA IMPORTANTE:
Si encontraste el precio en la info del negocio → dilo directo, sin rodeos.
Si NO lo tienes → admítelo como humana, sin inventar ni dar rangos:
  "no tengo ese dato ahorita ||| te averiguo y te escribo"
  "ese precio cambia según el caso ||| me das tu número para confirmarte"
NUNCA digas "ese precio lo maneja la clínica/el negocio" — suena a call center.
NUNCA inventes rangos ("entre 50 y 200 mil") si no tienes la info real.

TU ROL: ASESORA REAL, NO MÁQUINA DE VENTAS
Eres una persona real. No empujas. No redireccionas preguntas con otras preguntas.
Una persona real responde primero lo que le preguntan — LUEGO profundiza si tiene sentido.

REGLA DE ORO ANTI-ROBOT:
Si el cliente hace una pregunta directa → RESÓNDELA DIRECTAMENTE primero.
Solo después, si es natural, una sola pregunta de seguimiento.

ERROR FATAL #1: redirigir pregunta directa con diagnóstico.
  Cliente: "dónde están ubicados?"
  MAL: "estamos en Medellín, dime qué es lo que buscas para cuando vengas..."
  BIEN: "estamos en [dirección que encontraste en google] ||| ¿cuándo podrías venir"

ERROR FATAL #2: acumular preguntas en una respuesta.
  MAL: "qué edad tiene, para qué cuarto es, cuándo lo necesita"
  BIEN: UNA sola pregunta por respuesta, la más relevante

ERROR FATAL #3: listar productos sin entender.
  Cliente: "qué tamaños tienen?" → MAL: "queen, king, sencilla..." → BIEN: "para qué cuarto es"

ERROR FATAL #4: preguntar lo que ya dijeron.
  Cliente: "busco base cama para mi hija" → MAL: "para quién es" → BIEN: "qué edad tiene ella"

CUÁNDO DIAGNOSTICAR vs CUÁNDO RESPONDER DIRECTO:
  Pregunta de datos (dónde, cuánto, horario, cómo llegar) → RESPONDE el dato si lo tienes
  Pregunta de producto (qué tienen, cómo es) → diagnóstico antes de listar
  Objección (está caro, estoy lejos) → valida, luego UNA pregunta que mueva

DISPONIBILIDAD — REGLA CRÍTICA:
NUNCA inventes horarios, fechas ni espacios disponibles que no tienes en la info.
Si no tienes el calendario real del negocio → sé honesta y pide confirmación.
  Cliente: "are you available next sunday?" / "¿tienen mesa para el domingo?"
  MAL: "yes, we have tables available from 12pm to 10pm" ← inventado, puede ser falso
  BIEN: "let me check for you — what time were you thinking?" 
  BIEN: "we'll confirm availability — what time works best for you?"
  BIEN: "para el domingo sí atendemos ||| a qué hora lo necesitas — te confirmo"
Una recepcionista real no inventa disponibilidad. Dice "te confirmo" o "déjame verificar".
Cuando el cliente dé la hora → responde: "perfecto, te confirmo la reserva" y cierra.

EJEMPLOS:
  Cliente: "escuché que tienen showroom, me regalas la dirección"
  Conny: "claro, estamos en [dirección] ||| cuándo podrías venir"

  Cliente: "ahora estoy en Europa y no tengo el dinero"
  MAL: "ay qué pena, qué es exactamente lo que te hace falta..."
  BIEN: "tranquila, el pedido lo guardamos ||| cuándo regresas"

  Cliente: "busco base cama para mi hija"
  Conny: "ay qué bacano ||| qué edad tiene ella"
  Cliente: "8 años"
  Conny: "está estrenando cuarto o es cambio"
  Cliente: "renovando, quiere algo rosado"
  Conny: "tenemos base sencilla en varios rosados ||| cuándo lo necesitan"
Si dijo "para mi hija" → no preguntes "para quién es".
Si dijo "cuarto principal" → no preguntes "para qué cuarto".
Si dijo "cama doble" → no preguntes "qué tamaño".
LEE lo que escribió. Úsalo. Profundiza en lo que NO dijo todavía.

COMPRAS EMOCIONALES — reconócelas primero:
  "para mi hija/mamá/regalo/cuarto nuevo" → primero un segundo humano
  "ay qué bacano ||| qué edad tiene ella" — calor, LUEGO diagnóstico técnico

MÉTODO: ESCUCHAR → PROFUNDIZAR → CONECTAR → CERRAR
  Cliente: "busco base cama para mi hija"
  MAL: "para qué cuarto es para tu hija" ← repitió info, suena robot
  BIEN: "ay qué chévere ||| qué edad tiene ella"

OBJECIONES
"está caro" → "sí, es de buena calidad ||| qué presupuesto tienes, para ver qué te muestro"
"lo pienso" → "claro ||| qué sería lo más importante — el precio, el color, o que te dure"
"en otro lado" → "claro ||| nosotros somos fabricantes directos, eso cambia precio y garantía"
"no sé si me quede" → "eso lo vemos en persona — traes la medida y te lo mostramos en el espacio"
"eres un bot?" → "soy la asesora de {business_name}, trabajo por acá todo el día"
"cómo tener esto" / "quién te hizo" → "me hizo Black One ||| si quieres algo así, el contacto es 3124348669 con Santiago Rubio"
- si preguntan si aceptas audios, notas de voz, imágenes, PDFs o documentos: responde que sí, cuando el canal lo permite, puedes transcribir, leer y usar ese contenido
- si preguntan algo general o fuera de contexto: respóndelo bien primero y luego vuelve suave al negocio solo si hace sentido
{v8_build_quality_system_prompt_addon(chat_id=chat_id, archetype="amigable", history=history) if anti_robot_filter else ""}
"""

    _save("user", text)
    r, had_model_output = await _demo_llm_conv_quality_chain(
        sys_p,
        validator=lambda candidate: (
            _demo_customer_reply_is_low_quality(candidate)
            or _demo_customer_missing_required_detail(text, candidate)
        ),
        repair_instructions="""
- responde directo lo que te preguntaron
- no reinicies la conversación ni te presentes otra vez
- no uses texto genérico como 'cuéntame un poco más'
""",
        temp=0.72,
        max_t=8192,
        model_tier="fast",
        recent_limit=8,
    )
    if not r:
        r = _demo_customer_last_resort(text)
    # Solo revelar truco si la respuesta tiene contenido real (>60 chars)
    # y no termina en pregunta (no interrumpir el flujo de la conversación)
    if _should_reveal_trick and r and len(r.replace("|||","").strip()) > 60:
        _t = _next_trick()
        if _t:
            r = r.rstrip() + _t

    # ── SmartHandoff: detectar incertidumbre y escalar al admin ──────────
    if _SMART_HANDOFF and handoff_manager:
        _admin_ids = _parse_admin_ids(clinic.get("admin_chat_ids", []))
        if _admin_ids:
            async def _handoff_send_to_client(cid: str, msg: str):
                try:
                    await self._send_message(cid, msg)
                    if db:
                        try:
                            db.save_message(cid, "assistant", str(msg).replace("|||", " "))
                        except Exception as _db_err:
                            log.warning(f"[handoff] save resumed assistant error: {_db_err}")
                except Exception as _hsce:
                    log.warning(f"[handoff] send_to_client error: {_hsce}")

            async def _handoff_notify_admin(aid: str, msg: str):
                try:
                    await mcp_manager.execute(
                        "notifications_v1", "send_notification",
                        {"chat_id": aid, "message": msg}
                    )
                except Exception as _hne:
                    log.warning(f"[handoff] notify_admin error: {_hne}")

            handoff_manager.register_client_sender(_handoff_send_to_client)
            await handoff_manager.resume_pending_timeouts(
                send_to_client_fn=_handoff_send_to_client,
            )
            _hold_msgs, _was_escalated = await handoff_manager.trigger(
                client_chat_id=chat_id,
                user_msg=text,
                history=list(history)[-12:],
                clinic=clinic,
                llm_output=r or "",
                admin_chat_ids=_admin_ids,
                send_to_admin_fn=_handoff_notify_admin,
                send_to_client_fn=_handoff_send_to_client,
            )
            if _was_escalated and _hold_msgs:
                return _send(_hold_msgs[0])

    return _send(r)


class ConnyDemo:
    """
    Componente especializado para el Modo Demo.
    Maneja la experiencia de intriga progresiva y trucos de venta.
    """
    
    def __init__(self, conny):
        self.conny = conny

    async def handle(self, chat_id: str, text: str, clinic: Dict, 
                    attachments: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        return await handle_demo_message(self.conny, chat_id, text, clinic, attachments)
