from __future__ import annotations
import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from bublee_core.identity_policy import identity_block
from bublee_core.smart_prompts import build_patient_system_prompt, TONE_ARCHETYPES

log = logging.getLogger("bublee.production")


class BubleeProduction:
    """
    Producción: Atención a pacientes reales via LLM directo.
    100% inteligencia artificial, sin templates hardcodeados.
    """

    def __init__(self, bublee):
        self.bublee = bublee

    # ── Palabras clave que exigen conocimiento confirmado ──────────────────────
    _KNOWLEDGE_REQUIRED_MARKERS = (
        "que hace", "qué hace", "servicio", "servicios", "cirugia", "cirugía",
        "procedimiento", "tratamiento", "precio", "costo", "cuanto cuesta",
        "cuánto cuesta", "vale", "cuanto", "cuánto", "horario", "horarios",
        "direccion", "dirección", "ubicacion", "ubicación", "donde quedan",
        "dónde quedan", "eps", "seguro", "convenio", "especialidad", "especialidades",
        "doctor", "doctora", "médico", "médica", "agenda", "agendar", "cita",
        "citas", "disponibilidad", "disponible", "disponibles", "espacio",
        "espacios", "cupo", "cupos", "libre", "libres",
    )

    def _needs_confirmed_business_knowledge(self, text: str) -> bool:
        """True si el mensaje exige info operativa del negocio."""
        normalized = (text or "").lower()
        return any(marker in normalized for marker in self._KNOWLEDGE_REQUIRED_MARKERS)

    def _has_enough_confirmed_knowledge(self, text: str, support_text: str, clinic: Dict) -> bool:
        """
        Devuelve True SOLO si hay contexto confirmado suficiente para responder.
        Con la menor duda → False → escala al admin, NUNCA inventa ni chatea sobre temas ajenos.
        """
        text_lower = (text or "").lower()

        # 1. Si hay alguna solicitud explícita de hablar con humano, preguntar a alguien o transferir -> Escala de inmediato
        transfer_keywords = {
            "preguntar", "pregunta", "preguntale", "pregúntale", "hablar con", "pasame", 
            "pásame", "humano", "persona", "asesor", "admin", "administrador", "doctor",
            "doctora", "médico", "medico", "contacto", "atencion humana", "atención humana"
        }
        if any(tk in text_lower for tk in transfer_keywords):
            log.info(f"[production] Escalando por palabra clave de transferencia: {text_lower}")
            return False

        # 2. Extraer palabras no-cortesía
        non_pleasantry_words = []
        try:
            # Limpiar puntuación y separar en palabras
            text_clean = re.sub(r"[^\w\s]", "", text_lower)
            words = [w.strip() for w in text_clean.split() if w.strip()]
            
            allowed_pleasantries = {
                "hola", "como", "estas", "cómo", "estás", "buenos", "dias", "tardes", 
                "noches", "buen", "dia", "día", "gracias", "ok", "vale", "dale", "listo", 
                "chao", "adios", "hasta", "luego", "que", "mas", "más", "bien", "super", 
                "excelente", "y", "tú", "tu", "usted", "de", "la", "el", "en", "con", "por",
                "para", "un", "una", "nosotros", "yo", "me", "te", "se", "lo", "los", "las"
            }
            
            non_pleasantry_words = [w for w in words if w not in allowed_pleasantries]
        except Exception:
            pass

        # Si no exige conocimiento del negocio Y además es solo un saludo o cortesía vacía -> Seguro responder
        if not self._needs_confirmed_business_knowledge(text) and not non_pleasantry_words:
            return True

        # 3. Obtener el soporte y servicios de la clínica
        support = (support_text or "").lower()
        services = clinic.get("services", [])
        if isinstance(services, str):
            services = [s.strip() for s in services.split(",") if s.strip()]
        service_text = " ".join(str(s).lower() for s in services if str(s).strip())
        combined = f"{support} {service_text}".strip()

        # Sin contexto real → escala
        if len(combined) < 80:
            return False

        # Servicios genéricos sin contenido real → escala
        generic_placeholders = {"", "consulta general", "consultar directamente", "sin definir", "por definir"}
        if service_text.strip().lower() in generic_placeholders:
            return False


        # 4. Verificar si hay palabras desconocidas fuera del soporte y del vocabulario básico
        if non_pleasantry_words:
            combined_clean = re.sub(r"[^\w\s]", "", combined.lower())
            combined_words = set(combined_clean.split())
            
            ignored_functional_words = {
                "quiero", "quisiera", "necesito", "interesa", "interesado", "puedes", "podrias", "podrías",
                "saber", "precio", "costo", "valor", "cuanto", "cuánto", "cuesta", "tiene", "tienen", "sobre",
                "clínica", "clinica", "paciente", "equipo", "servicio", "servicios", "información", "informacion",
                "interés", "interes", "productos", "producto", "tratamientos", "tratamiento", "procedimientos",
                "procedimiento", "cirugia", "cirugías", "cirugias", "cirugía", "proceso", "detalles", "detalle",
                "cita", "citas", "agenda", "agendar", "horario", "horarios", "precios", "costos", "valores",
                "tarde", "tardes", "mañana", "mañanas", "dia", "dias", "día", "días",
                "espacio", "espacios", "cupo", "cupos", "libre", "libres", "disponible", "disponibles", "turno", "turnos"
            }
            
            unknown_words = [
                w for w in non_pleasantry_words 
                if w not in combined_words and w not in ignored_functional_words and len(w) >= 3
            ]
            
            if unknown_words:
                log.info(f"[production] Escalando por términos desconocidos fuera de base de conocimiento: {unknown_words}")
                return False

        return True

    def _normalize_admin_jid(self, raw_jid: str, platform: str) -> str:
        """Normaliza el JID del admin para que _send_message lo resuelva correctamente."""
        jid = str(raw_jid or "").strip()
        if not jid:
            return ""

        # Si está explícitamente registrado como telegram en DB, no añadir sufijo de whatsapp
        try:
            if db:
                persisted = db.get_contact_route(jid)
                if persisted == "telegram":
                    return jid
        except Exception:
            pass

        # Si el ID tiene formato de Telegram (menos de 11 dígitos, o empieza con - para grupos)
        digits = re.sub(r"[^0-9]", "", jid)
        if jid.startswith("-") or (digits and len(digits) <= 10):
            return jid

        if platform in ("whatsapp", "evolution", "whatsapp_cloud"):
            # Quitar caracteres que no son dígitos ni @
            if "@" not in jid:
                if digits:
                    jid = f"{digits}@s.whatsapp.net"
        return jid

    async def _generate_admin_alert_via_llm(
        self,
        clinic_name: str,
        agent_name: str,
        patient_display: str,
        patient_text: str,
        reason: str,
        admin_name: str = "Administrador",
        had_been_talking: bool = True,
        tentative_response: str = "",
    ) -> str:
        try:
            llm_engine = getattr(self.bublee, "llm_engine", None)
            if not llm_engine:
                try:
                    from bublee import llm_engine
                except ImportError:
                    llm_engine = None
            if not llm_engine:
                raise RuntimeError("No LLM engine")
                
            if reason == "first_contact":
                prompt = (
                    f"Eres {agent_name}, la recepcionista de {clinic_name}. "
                    f"Un paciente con el número ...{patient_display} te acaba de escribir por primera vez. "
                    f"Le diste un saludo de bienvenida, pero tu base de conocimientos aún no está bien configurada o le falta información para poder atenderlo con precisión. "
                    f"Escríbele un mensaje rápido al administrador (tu jefe) explicándole esto en tu tono y personalidad natural. "
                    f"Pídele amablemente que te enseñe o te configure más detalles para poder ayudar al paciente."
                )
            elif reason == "booking_request":
                prompt = (
                    f"Eres {agent_name}, la recepcionista de {clinic_name}. "
                    f"El paciente con el número ...{patient_display} quiere agendar una cita o preguntó por disponibilidad y espacios libres. "
                    f"Mensaje del paciente: '{patient_text}'. "
                    f"Escríbele una alerta muy corta, amigable y natural al administrador (tu jefe) avisándole que este paciente quiere agendar una cita para que él revise la agenda y confirme."
                )
            elif reason == "human_request":
                if not had_been_talking:
                    prompt = (
                        f"Eres {agent_name}, la asistente/recepcionista de {clinic_name}. "
                        f"El número ...{patient_display} acaba de escribir solicitando hablar con un humano. "
                        f"Como no habían estado hablando antes (no hay historial previo de conversación con el bot), "
                        f"NO debes mostrar el mensaje del paciente en tu alerta. "
                        f"Escribe un mensaje muy profesional, claro y formal dirigido a {admin_name} (el administrador/dueño del negocio) "
                        f"avisándole que el paciente (...{patient_display}) quiere hablar con un humano. "
                        f"Menciona explícitamente en el mensaje a {admin_name} que puede responder con 'muéstrame qué pasó' o 'contexto' "
                        f"si desea ver los detalles o contexto de este chat."
                    )
                else:
                    prompt = (
                        f"Eres {agent_name}, la asistente/recepcionista de {clinic_name}. "
                        f"El paciente con el número ...{patient_display} solicita hablar con un humano. "
                        f"Su mensaje fue: '{patient_text}'. "
                        f"Escribe un mensaje muy profesional, claro y formal dirigido a {admin_name} (el administrador/dueño del negocio) "
                        f"notificándole que este paciente (...{patient_display}) quiere hablar con un humano, e incluye su mensaje en la alerta. "
                        f"Menciona que si desea ver el contexto completo de la conversación, puede responder con 'muéstrame qué pasó' o 'contexto'."
                    )
            else:
                prompt = (
                    f"Eres {agent_name}, la recepcionista de {clinic_name}. "
                    f"Un paciente con el número ...{patient_display} te acaba de hacer una pregunta sobre el negocio: '{patient_text}'. "
                    f"Como no tienes esta información confirmada en tu base de conocimientos y no quieres inventar datos, debes pedirle ayuda a tu jefe (el administrador). "
                    f"Escríbele un mensaje corto y muy natural a tu jefe en tu personalidad explicándole qué preguntó el paciente y pidiéndole que te enseñe qué responderle. "
                    f"Dile que si te responde a ti, tú le reenvías la respuesta al paciente."
                )
                if tentative_response:
                    prompt += f" Nota: Tu respuesta tentativa calculada fue: '{tentative_response}'."
                
            messages = [{"role": "user", "content": prompt}]
            response, _ = await llm_engine.complete(
                messages, model_tier="fast", temperature=0.75, max_tokens=500
            )
            import re as _re
            response = _re.sub(r'\*\*(.+?)\*\*', r'\1', response)
            response = _re.sub(r'\*(.+?)\*', r'\1', response)
            response = _re.sub(r'`(.+?)`', r'\1', response)
            return response.strip()
        except Exception as e:
            log.warning(f"[production] error generando alerta via LLM: {e}")
            if reason == "first_contact":
                return f"Hola {admin_name}! El paciente ...{patient_display} me escribió por primera vez, pero aún no tengo suficiente información configurada para atenderle. ¡Por favor enséñame!"
            elif reason == "human_request":
                if not had_been_talking:
                    return f"Hola {admin_name}, el número ...{patient_display} quiere hablar con un humano. (No se muestra el mensaje de entrada ya que no hay una conversación previa activa). Escribe 'muéstrame qué pasó' o 'contexto' para ver más detalles."
                else:
                    return f"Hola {admin_name}, el paciente ...{patient_display} quiere hablar con un humano y dijo: \"{patient_text[:150]}\". Escribe 'muéstrame qué pasó' o 'contexto' para ver toda la conversación."
            else:
                fallback = f"Hola {admin_name}! El paciente ...{patient_display} preguntó: \"{patient_text}\". No tengo esta información confirmada, ¿qué le respondo?"
                if tentative_response:
                    fallback += f" Mi respuesta tentativa fue: \"{tentative_response}\"."
                return fallback

    async def _alert_admin_knowledge_gap(
        self,
        admin_jids: List[str],
        chat_id: str,
        text: str,
        instance_id: str,
        platform: str = "whatsapp",
    ) -> None:
        """
        Alerta a TODOS los admins vinculados cuando no hay suficiente info
        confirmada.
        """
        patient_display = re.sub(r"@.*", "", chat_id)[-6:] or chat_id[-6:]
        
        # Get clinic info
        from bublee import db
        clinic = db.get_clinic()
        clinic_name = clinic.get("name", "Clínica")
        persona = clinic.get("persona_config", {})
        if isinstance(persona, str):
            try:
                import json as _j_persona
                persona = _j_persona.loads(persona) if persona else {}
            except Exception:
                persona = {}
        agent_name = persona.get("name", "Lucía")
        
        if not hasattr(self.bublee, "_admin_pending"):
            self.bublee._admin_pending = {}

        notified = 0
        for raw_jid in (admin_jids or []):
            normalized_jid = self._normalize_admin_jid(raw_jid, platform)
            if not normalized_jid:
                continue
            
            admin_name = "Administrador"
            try:
                admin = db.get_admin(raw_jid) if db else None
                if admin and admin.get("name"):
                    admin_name = admin["name"].strip().title()
            except Exception:
                pass

            # check if they had been talking
            try:
                history = db.get_history(chat_id)
            except Exception:
                history = []
            has_prior_assistant = any(m.get("role") == "assistant" for m in history)
            had_been_talking = has_prior_assistant

            alert_msg = await self._generate_admin_alert_via_llm(
                clinic_name=clinic_name,
                agent_name=agent_name,
                patient_display=patient_display,
                patient_text=text,
                reason="knowledge_gap",
                admin_name=admin_name,
                had_been_talking=had_been_talking
            )

            try:
                await self.bublee._send_message(normalized_jid, alert_msg)
                notified += 1
            except Exception as e:
                log.warning(f"[production] no pude enviar alerta al admin ({normalized_jid}): {e}")
                continue
            self.bublee._admin_pending[normalized_jid] = {
                "action": "answer_gap",
                "patient_chat_id": chat_id,
                "original_question": text,
                "instance_id": instance_id,
                "ts": time.time(),
            }

        if notified == 0:
            log.warning(f"[production] knowledge_gap: no pude avisarle a NINGÚN admin sobre {patient_display}")
        else:
            log.info(f"[production] knowledge_gap → {notified} admin(es) alertados sobre pregunta de {patient_display}")

    async def handle(self, chat_id: str, text: str, clinic: Dict,
                    history: List[Dict], conv_state: Dict, attachments: Optional[List[Dict]] = None) -> List[str]:
        """Procesa un mensaje de paciente real via LLM directo."""
        from bublee import db, llm_engine, kb, v8_process_response

        start_time = time.time()
        instance_id = getattr(self.bublee, "_instance_id", "default")

        # ── interceptar/procesar imágenes para diagnóstico visual ──
        image_attachments = [att for att in (attachments or []) if att.get("kind") == "image"]
        if image_attachments:
            log.info(f"[vision] detectada imagen de {chat_id[:8]} para diagnóstico visual")
            try:
                import src.core.vision_handler as vh
                image_bytes = await vh.download_image(image_attachments[0])
                if image_bytes:
                    await self.bublee._typing_action(chat_id)
                    assessment = await vh.analyze_skin_image(
                        image_bytes, 
                        mime_type=image_attachments[0].get("mime_type", "image/jpeg")
                    )
                    
                    # Guardar mensajes en base de datos
                    incoming_desc = text or image_attachments[0].get("caption") or "📸 [Imagen]"
                    try:
                        db.save_message(chat_id, "user", incoming_desc)
                        db.save_message(chat_id, "assistant", assessment)
                    except Exception:
                        pass
                        
                    return self.bublee._split_bubbles(assessment, chat_id=chat_id)
            except Exception as _vis_err:
                log.error(f"[vision] error procesando diagnóstico visual: {_vis_err}", exc_info=True)

        # ── interceptar/procesar respuesta NPS de paciente ──
        try:
            import asyncio
            from src.core.globals import Config, _parse_admin_ids, db
            # Verificar si hay una cita reciente esperando respuesta NPS
            row = None
            if hasattr(db, "_conn"):
                with db._conn() as c:
                    row = c.execute("""
                        SELECT * FROM appointments 
                        WHERE chat_id=? AND status='confirmada' AND nps_status='sent'
                        ORDER BY id DESC LIMIT 1
                    """, (chat_id,)).fetchone()
            
            if row:
                apt = dict(row)
                apt_id = apt["id"]
                
                # Extraer calificación
                numbers = re.findall(r'[1-5]', text)
                
                is_positive = False
                score = None
                
                if numbers:
                    score = int(numbers[0])
                    if score >= 4:
                        is_positive = True
                else:
                    # Análisis simple por palabras clave
                    lower_text = text.lower()
                    positive_keywords = ["excelente", "bueno", "bien", "perfecto", "maravilloso", "me gusto", "me gustó", "super", "súper", "feliz", "contento", "contenta", "espectacular"]
                    negative_keywords = ["mal", "malo", "pesimo", "pésimo", "terrible", "dolor", "tarde", "espera", "demorado", "insatisfecho", "insatisfecha", "nunca", "horror"]
                    
                    if any(kw in lower_text for kw in positive_keywords) and not any(kw in lower_text for kw in negative_keywords):
                        is_positive = True
                        score = 5
                    elif any(kw in lower_text for kw in negative_keywords):
                        is_positive = False
                        score = 1
                    else:
                        # Fallback con LLM directo
                        try:
                            classification_prompt = (
                                f"Analiza la respuesta de un paciente sobre cómo le fue en su cita estética/médica:\n"
                                f"Mensaje: \"{text}\"\n\n"
                                f"Responde ÚNICAMENTE con un número entero del 1 al 5 (donde 5 es muy satisfecho y 1 es muy insatisfecho)."
                            )
                            res_score = await llm_engine.generate(classification_prompt, model=Config.LLM_MODEL_DIRECT)
                            res_digits = re.findall(r'[1-5]', res_score)
                            if res_digits:
                                score = int(res_digits[0])
                                if score >= 4:
                                    is_positive = True
                        except Exception:
                            pass
                
                if score is None:
                    score = 4
                    is_positive = True
                
                new_nps_status = "answered_positive" if is_positive else "answered_negative"
                db.update_appointment(apt_id, nps_status=new_nps_status)
                
                try:
                    db.save_message(chat_id, "user", text)
                except Exception:
                    pass
                
                if is_positive:
                    maps_link = clinic.get("google_maps_review_url") or "https://search.google.com/local/writereview?placeid=YOUR_PLACE_ID"
                    response_msg = (
                        f"¡Qué alegría leer eso, {apt.get('patient_name', 'Paciente')}! 😊 Nos hace muy felices darte el mejor servicio.\n\n"
                        f"¿Nos ayudarías muchísimo compartiendo tu experiencia en nuestra ficha de Google? "
                        f"Solo toma un minuto e impulsa un montón a nuestro equipo: {maps_link}"
                    )
                    try:
                        db.save_message(chat_id, "assistant", response_msg)
                    except Exception:
                        pass
                    return self.bublee._split_bubbles(response_msg, chat_id=chat_id)
                else:
                    response_msg = (
                        f"Lamentamos mucho escuchar eso, {apt.get('patient_name', 'Paciente')}. 😔 "
                        f"Para nosotros lo más importante es tu bienestar.\n\n"
                        f"En este momento un asesor de servicio al cliente se pondrá en contacto contigo "
                        f"para revisar tu caso y darte una solución."
                    )
                    try:
                        db.save_message(chat_id, "assistant", response_msg)
                    except Exception:
                        pass
                    
                    # Notificar al administrador inmediatamente
                    admin_ids = _parse_admin_ids(clinic.get("admin_chat_ids", []))
                    admin_alert = (
                        f"⚠️ *Alerta NPS Negativo ({score}/5)*\n\n"
                        f"• Paciente: {apt.get('patient_name')}\n"
                        f"• Teléfono: {apt.get('patient_phone')}\n"
                        f"• Servicio: {apt.get('service')}\n"
                        f"• Comentario: \"{text}\"\n\n"
                        f"Por favor contáctalo prioritariamente."
                    )
                    for admin_id in admin_ids:
                        asyncio.create_task(self.bublee._send_message(admin_id, admin_alert))
                        
                    return self.bublee._split_bubbles(response_msg, chat_id=chat_id)
        except Exception as _nps_err:
            log.warning(f"[production] error en intercepción de NPS: {_nps_err}")

        # ── local caching / direct verified teachings routing ──
        try:
            from bublee_learning import learning_engine as _le
            _t = await _le.get_teachings(instance_id, limit=100)
            
            def _norm(s: str) -> str:
                s = s.lower().strip()
                s = re.sub(r"[^\w\s]", "", s)
                accents = {'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ü': 'u'}
                for k, v in accents.items():
                    s = s.replace(k, v)
                return s

            user_clean = _norm(text)
            user_words = [w for w in user_clean.split() if len(w) > 2]
            
            for t in _t:
                q = t.get("question", "").replace("[admin enseñó] ", "")
                q_clean = _norm(q)
                q_words = [w for w in q_clean.split() if len(w) > 2]
                
                is_match = False
                if user_clean == q_clean:
                    is_match = True
                elif q_words and user_words:
                    intersection = set(user_words) & set(q_words)
                    if len(intersection) / len(q_words) >= 0.85:
                        is_match = True
                
                if is_match:
                    matched_teaching_answer = t.get("answer", "")
                    log.info(f"[production] Coincidencia de caché semántico local con enseñanza: '{q}' -> '{matched_teaching_answer[:50]}...'")
                    
                    try:
                        db.save_message(chat_id, "user", text)
                        db.save_message(chat_id, "assistant", matched_teaching_answer)
                    except Exception as _db_err:
                        log.warning(f"[production] error guardando respuesta de caché en DB: {_db_err}")
                        
                    return self.bublee._split_bubbles(matched_teaching_answer, chat_id=chat_id)
        except Exception as _e:
            log.warning(f"[production] error en búsqueda de caché local: {_e}")

        # Smart features: memory, language, sentiment, time
        patient_context = ""
        lang_instruction = ""
        try:
            from bublee_smart_features import (
                CrossSessionMemory, SentimentTracker, LanguageDetector,
                get_time_greeting, is_conversation_ending, get_natural_closing,
            )
            # Cross-session memory
            mem = CrossSessionMemory(instance_id)
            patient_data = mem.recall_patient(chat_id)
            patient_context = mem.get_context_for_prompt(chat_id)

            # Language detection
            lang_det = LanguageDetector()
            detected_lang = lang_det.detect(text)
            lang_instruction = lang_det.get_language_instruction(detected_lang)

            # Explicit human request detection
            human_request_signals = ["hablar con humano", "hablar con una persona", "hablar con alguien",
                                     "quiero hablar con", "pasame con", "pásame con", "un humano",
                                     "una persona real", "talk to a human", "real person", "hablar con un humano",
                                     "asesor humano", "atencion humana", "atención humana", "humano", "asesor",
                                     "atención", "atencion", "contacto", "hablar con alguien"]
            wants_human = any(s in text.lower() for s in human_request_signals)

            # Sentiment check → auto-escalate if frustrated
            sentiment = SentimentTracker()
            should_esc, esc_reason = sentiment.should_escalate(text, history)
            if should_esc or wants_human:
                # Set escalation needed in conversation state and save to DB
                if conv_state:
                    try:
                        conv_state.escalation_needed = True
                        db.save_conversation_state(conv_state)
                        log.info(f"[production] Muted bot (escalation_needed=True) for chat_id={chat_id}")
                    except Exception as _state_err:
                        log.warning(f"[production] error guardando estado de conversación: {_state_err}")

                # Resolve clinic and agent names for the LLM prompt
                _c_name = clinic.get("name", "el negocio")
                _p_config = clinic.get("persona_config", {})
                if isinstance(_p_config, str):
                    try:
                        import json as _j_persona
                        _p_config = _j_persona.loads(_p_config) if _p_config else {}
                    except Exception:
                        _p_config = {}
                _a_name = _p_config.get("name", "Lucía")

                admin_ids = clinic.get("admin_chat_ids", [])
                if isinstance(admin_ids, str):
                    import json as _j2
                    admin_ids = _j2.loads(admin_ids) if admin_ids else []
                if admin_ids:
                    reason_text = "quiere hablar con alguien" if wants_human else esc_reason.replace('_', ' ')
                    patient_display = re.sub(r"@.*", "", chat_id)[-4:] or chat_id[-4:]
                    
                    has_prior_assistant = any(m.get("role") == "assistant" for m in history)
                    had_been_talking = has_prior_assistant

                    async def _send_alerts_task():
                        _esc_notified = 0
                        platform = clinic.get("platform", "whatsapp")
                        for _raw_admin in admin_ids:
                            normalized_admin = self._normalize_admin_jid(_raw_admin, platform)
                            if not normalized_admin:
                                continue
                            
                            admin_name = "Administrador"
                            try:
                                admin = db.get_admin(_raw_admin) if db else None
                                if admin and admin.get("name"):
                                    admin_name = admin["name"].strip().title()
                            except Exception:
                                pass

                            alert = await self._generate_admin_alert_via_llm(
                                clinic_name=_c_name,
                                agent_name=_a_name,
                                patient_display=patient_display,
                                patient_text=text,
                                reason="human_request",
                                admin_name=admin_name,
                                had_been_talking=had_been_talking
                            )

                            try:
                                await self.bublee._send_message(normalized_admin, alert)
                                _esc_notified += 1
                            except Exception as _e:
                                log.warning(f"[production] escalation alert failed for {normalized_admin}: {_e}")
                            
                            if not hasattr(self.bublee, "_admin_pending"):
                                self.bublee._admin_pending = {}
                            self.bublee._admin_pending[normalized_admin] = {
                                "action": "view_escalated_context",
                                "patient_chat_id": chat_id,
                                "ts": time.time(),
                            }
                            self.bublee._last_escalated_chat_id = chat_id

                        log.info(f"[production] escalation alert sent to {_esc_notified}/{len(admin_ids)} admin(s): {reason_text}")

                    import asyncio
                    asyncio.create_task(_send_alerts_task())

                if wants_human:
                    human_response = "Perfecto, ya te voy a conectar con uno de nuestros asesores para que te pueda ayudar. ||| Danos un momento por favor, ya te atenderemos. 😊"
                    try:
                        db.save_message(chat_id, "user", text)
                        db.save_message(chat_id, "assistant", human_response.replace("|||", " "))
                    except Exception as _e:
                        log.warning(f"[production] error guardando mensaje de escalación: {_e}")
                    return self.bublee._split_bubbles(human_response, chat_id=chat_id)
                else:
                    # Auto-escalated due to frustration
                    esc_response = "Entiendo. Voy a transferir tu consulta a una persona de nuestro equipo para que te brinde una mejor asistencia. En breve te contactaremos. 😊"
                    try:
                        db.save_message(chat_id, "user", text)
                        db.save_message(chat_id, "assistant", esc_response)
                    except Exception as _e:
                        log.warning(f"[production] error guardando mensaje de auto-escalación: {_e}")
                    return self.bublee._split_bubbles(esc_response, chat_id=chat_id)

            # Conversation ending detection
            if is_conversation_ending(text):
                tone = "casual"
                try:
                    from pathlib import Path
                    import json as _j3
                    ov = Path(f"personas/{instance_id}/runtime_override.json")
                    if ov.exists():
                        tone = _j3.loads(ov.read_text()).get("tone", "casual")
                except Exception as _e:
                    log.warning(f"[production] error leyendo tone override: {_e}")
                closing = get_natural_closing(tone)
                db.save_message(chat_id, "user", text)
                db.save_message(chat_id, "assistant", closing)
                # Save last topic to memory
                if history:
                    last_user_msgs = [m["content"] for m in history[-4:] if m.get("role") == "user"]
                    topic = last_user_msgs[0][:50] if last_user_msgs else ""
                    mem.remember_patient(chat_id, {"last_topic": topic})
                return self.bublee._split_bubbles(closing, chat_id=chat_id)

            # Time awareness for greeting
            time_greeting = get_time_greeting()
        except ImportError:
            time_greeting = "hola"
        except Exception as _e:
            log.warning(f"[production] error en smart_features: {_e}")
            time_greeting = ""

        clinic_name = clinic.get("name", "el negocio")
        persona = clinic.get("persona_config", {})
        if isinstance(persona, str):
            try:
                import json as _j_persona
                persona = _j_persona.loads(persona) if persona else {}
            except Exception:
                persona = {}
        agent_name = persona.get("name", "Lucía")
        services = clinic.get("services", [])
        if isinstance(services, str):
            services = [s.strip() for s in services.split(",") if s.strip()]
        services_str = ", ".join(services[:10]) if services else "consulta general"
        schedule = clinic.get("schedule", "")
        if isinstance(schedule, dict):
            schedule = " | ".join(f"{k}: {v}" for k, v in schedule.items())

        # Load persona override (tone changes from admin)
        persona_tone = "colombian_warm"
        try:
            from pathlib import Path
            import json as _json
            override_path = Path(f"personas/{instance_id}/runtime_override.json")
            if override_path.exists():
                override = _json.loads(override_path.read_text())
                persona_tone = override.get("tone", persona_tone)
        except Exception as _e:
            log.warning(f"[production] error leyendo persona override: {_e}")

        # Load soul knowledge
        soul_context = ""
        try:
            from bublee_core.prompt_ops import build_business_context
            soul_context = build_business_context(clinic, db, instance_id)
        except Exception as e:
            log.warning(f"[production] error building business context: {e}")

        # Mapeo de tono → arquetipo para smart_prompts
        archetype_map = {
            "luxury": "luxury",
            "formal": "profesional",
            "casual": "amigable",
            "colombian_warm": "amigable",
            "warm_energetic": "amigable",
            "directa": "directa",
            "energica": "energica",
            "empatica": "empatica",
            "experta": "experta",
            "juvenil": "juvenil",
        }
        archetype = archetype_map.get(persona_tone, "amigable")

        # Detectar si es Poblado (luxury estetica)
        address = clinic.get("address", "")
        barrio = clinic.get("barrio", "")
        tagline = clinic.get("tagline", "")
        is_poblado = any(
            "poblado" in str(x).lower()
            for x in [address, barrio, tagline, clinic_name]
        )

        # Sector del negocio
        sector = clinic.get("sector", "default") or "default"

        # Forbidden phrases del admin
        forbidden_phrases = []
        try:
            rules = clinic.get("business_rules", {})
            if isinstance(rules, str):
                import json as _j4
                rules = _j4.loads(rules)
            forbidden_phrases = rules.get("forbidden_phrases", [])
        except Exception as _e:
            log.warning(f"[production] error leyendo business rules: {_e}")

        # Hora actual para contexto
        import datetime as _dt
        _now = _dt.datetime.now()
        _hour = _now.hour
        _time_ctx = (
            "es de madrugada" if _hour < 6 else
            "es temprano en la mañana" if _hour < 9 else
            "es media mañana" if _hour < 12 else
            "es mediodía" if _hour < 14 else
            "es la tarde" if _hour < 20 else
            "es la noche"
        )
        _city = clinic.get("city", "Colombia")

        # Verificar si es primer turno
        _is_first = not any(m.get("role") == "assistant" for m in history)

        # Si es primer turno y la clínica no tiene suficiente información, avisar al admin
        if _is_first:
            try:
                from pathlib import Path
                import json as _j_json
                
                # Check setup_done or knowledge level
                soul_dir = Path("soul") / instance_id
                soul_file = soul_dir / "knowledge.md"
                soul_len = len(soul_file.read_text()) if soul_file.exists() else 0
                
                teachings_file = Path("teachings") / f"{instance_id}.jsonl"
                teachings_len = len(teachings_file.read_text()) if teachings_file.exists() else 0
                
                has_services = bool(clinic.get("services"))
                has_schedule = bool(clinic.get("schedule"))
                is_ready = (soul_len + teachings_len) > 2000 and has_services and has_schedule
                
                if not clinic.get("setup_done") or not is_ready:
                    admin_ids = clinic.get("admin_chat_ids", [])
                    if isinstance(admin_ids, str):
                        admin_ids = _j_json.loads(admin_ids) if admin_ids else []
                    if admin_ids:
                        patient_display = re.sub(r"@.*", "", chat_id)[-4:] or chat_id[-4:]
                        alert_msg = await self._generate_admin_alert_via_llm(
                            clinic_name=clinic_name,
                            agent_name=agent_name,
                            patient_display=patient_display,
                            patient_text=text,
                            reason="first_contact"
                        )
                        platform = clinic.get("platform", "whatsapp")
                        for _raw_admin in admin_ids:
                            normalized_admin = self._normalize_admin_jid(_raw_admin, platform)
                            if normalized_admin:
                                try:
                                    await self.bublee._send_message(normalized_admin, alert_msg)
                                except Exception:
                                    pass
            except Exception as e_alert:
                log.warning(f"[production] error enviando alerta de falta de info: {e_alert}")

        # NUEVO PROMPT — usa smart_prompts
        sys_prompt = build_patient_system_prompt(
            clinic_name=clinic_name,
            agent_name=agent_name,
            sector=sector,
            soul_context=soul_context,
            patient_context=patient_context,
            archetype=archetype,
            forbidden_phrases=forbidden_phrases,
            is_poblado=is_poblado,
            is_first_turn=_is_first,
            time_ctx=_time_ctx,
            city=_city,
            role=persona.get("role", "recepcionista virtual"),
            services_str=services_str,
        )

        messages = [{"role": "system", "content": sys_prompt}]
        for m in history[-12:]:
            messages.append({"role": m.get("role", "user"), "content": m.get("content", "")})
        messages.append({"role": "user", "content": text})

        # KB context
        kb_context = ""
        if kb:
            try:
                if hasattr(kb, "has_content") and kb.has_content():
                    kb_context = kb.query(text)
            except Exception as _e:
                log.warning(f"[production] KB query falló: {_e}")
        if kb_context:
            messages[0]["content"] += f"\n\nCONTEXTO DEL NEGOCIO:\n{kb_context[:1000]}"

        # Teachings injection — THIS IS YOUR KNOWLEDGE, USE IT
        teachings_context = ""
        try:
            from bublee_learning import learning_engine
            teachings = await learning_engine.get_teachings(instance_id, limit=20)
            if teachings:
                qa_lines = []
                for t in teachings:
                    q = t.get("question", "").replace("[admin enseñó] ", "")
                    a = t.get("answer", "")
                    if a and not q.startswith("["):
                        qa_lines.append(f"Si preguntan: \"{q}\" → Responde: \"{a}\"")
                    elif a:
                        qa_lines.append(f"Regla: {a[:150]}")
                if qa_lines:
                    teachings_context = "\n".join(qa_lines)
                    # Inject ABOVE the rules, as part of the clinic facts
                    messages[0]["content"] = messages[0]["content"].replace(
                        "REGLA #1",
                        "DATOS CONFIRMADOS POR EL DUEÑO (responde con estos sin dudar):\n" + teachings_context + "\n\nREGLA #1"
                    )
        except Exception as _e:
            log.warning(f"[production] error inyectando teachings: {_e}")

        # Admin rules injection (things admin said to ask first)
        admin_rules_context = ""
        try:
            from pathlib import Path
            rules_file = Path(f"soul/{instance_id}/admin_rules.json")
            if rules_file.exists():
                import json as _j
                rules = _j.loads(rules_file.read_text())
                if rules:
                    rules_text = "\n".join(f"- Si preguntan sobre '{r['topic']}': {r['action']}" for r in rules[-10:])
                    admin_rules_context = rules_text
                    messages[0]["content"] += f"\n\nINSTRUCCIONES DEL DUEÑO:\n{rules_text}"
        except Exception as _e:
            log.warning(f"[production] error leyendo admin_rules.json: {_e}")

        # Google Calendar availability injection if needed
        cal_summary = ""
        try:
            from src.core.globals import calendar_bridge
            if calendar_bridge and calendar_bridge.has_google_calendar() and calendar_bridge.needs_calendar(text):
                cal_summary = await calendar_bridge.get_availability_summary()
                if cal_summary:
                    messages[0]["content"] += f"\n\n{cal_summary}"
                    log.info(f"[production] Fallback: Google Calendar slots injected into fallback context: {len(cal_summary)} chars")
        except Exception as _cal_err:
            log.warning(f"[production] error fetching Google Calendar slots for fallback: {_cal_err}")

        support_for_answer = "\n".join(
            part for part in (soul_context, kb_context, teachings_context, admin_rules_context, cal_summary)
            if part
        )
        admin_ids_for_gap = clinic.get("admin_chat_ids", [])
        if isinstance(admin_ids_for_gap, str):
            import json as _j_gap
            admin_ids_for_gap = _j_gap.loads(admin_ids_for_gap) if admin_ids_for_gap else []
        admin_jid_for_gap = str(admin_ids_for_gap[0]) if admin_ids_for_gap else ""
        _platform = getattr(getattr(self.bublee, "_config", None), "PLATFORM", None) or str(clinic.get("platform") or "whatsapp")

        # ── Alerta proactiva de cita / disponibilidad al admin sin silenciar al paciente ──
        booking_markers = {"agenda", "agendar", "cita", "citas", "disponibilidad", "disponible", "disponibles", "espacio", "espacios", "cupo", "cupos", "libre", "libres"}
        text_lower = text.lower()
        if any(bm in text_lower for bm in booking_markers) and not clinic.get("calendly_link"):
            if admin_ids_for_gap:
                try:
                    patient_display = re.sub(r"@.*", "", chat_id)[-4:] or chat_id[-4:]
                    persona = clinic.get("persona_config", {})
                    if isinstance(persona, str):
                        import json as _json_persona
                        try: persona = _json_persona.loads(persona)
                        except Exception: persona = {}
                    agent_name = (persona or {}).get("name", "Lucia")
                    
                    for _raw_admin in admin_ids_for_gap:
                        _admin_jid = self._normalize_admin_jid(_raw_admin, _platform)
                        if _admin_jid:
                            admin_name = "Administrador"
                            try:
                                admin = db.get_admin(_raw_admin) if db else None
                                if admin and admin.get("name"):
                                    admin_name = admin["name"].strip().title()
                            except Exception:
                                pass
                            
                            has_prior_assistant = any(m.get("role") == "assistant" for m in history)
                            had_been_talking = has_prior_assistant

                            alert_msg = await self._generate_admin_alert_via_llm(
                                clinic_name=clinic.get("name", "Negocio"),
                                agent_name=agent_name,
                                patient_display=patient_display,
                                patient_text=text,
                                reason="booking_request",
                                admin_name=admin_name,
                                had_been_talking=had_been_talking
                            )
                            await self.bublee._send_message(_admin_jid, alert_msg)
                    log.info(f"[production] Alerta de agendamiento/disponibilidad enviada en segundo plano para {patient_display}")
                except Exception as _e:
                    log.warning(f"[production] error enviando alerta de agendamiento en segundo plano: {_e}")

        if admin_ids_for_gap and not self._has_enough_confirmed_knowledge(text, support_for_answer, clinic):
            try:
                await self._alert_admin_knowledge_gap(
                    admin_ids_for_gap, chat_id, text, instance_id, platform=_platform
                )
                db.save_message(chat_id, "user", text)
            except Exception as _e:
                log.warning(f"[production] no pude alertar admin por gap: {_e}")
            return []  # NO respondemos al paciente — admin(es) responderá(n)

        # Camino central: analyzer -> reasoning -> ResponseGenerator.
        # Si falla, se conserva el LLM directo actual como fallback real.
        response = ""
        model_used = "llm"
        try:
            generator = getattr(self.bublee, "generator", None)
            reasoning_engine = getattr(self.bublee, "reasoning", None)
            analyzer = getattr(self.bublee, "analyzer", None)
            if generator and reasoning_engine:
                if analyzer:
                    analysis = analyzer.analyze(text, history)
                else:
                    from src.core.globals import MessageAnalyzer
                    analysis = MessageAnalyzer().analyze(text, history)

                reasoning_result = await reasoning_engine.reason(
                    text, analysis, clinic, history, conv_state
                )
                context_parts = []
                if soul_context:
                    context_parts.append("CONTEXTO DEL NEGOCIO:\n" + soul_context)
                if kb_context:
                    context_parts.append("BASE DE CONOCIMIENTO:\n" + kb_context[:1200])
                if teachings_context:
                    context_parts.append("DATOS CONFIRMADOS POR EL DUEÑO:\n" + teachings_context)
                if admin_rules_context:
                    context_parts.append("INSTRUCCIONES DEL DUEÑO:\n" + admin_rules_context)
                if cal_summary:
                    context_parts.append(cal_summary)

                response = await generator.generate(
                    message=text,
                    analysis=analysis,
                    reasoning=reasoning_result,
                    clinic=clinic,
                    patient=patient_data if isinstance(patient_data, dict) else {},
                    history=history,
                    search_context="",
                    personality=None,
                    kb_context="\n\n".join(context_parts),
                    chat_id=chat_id,
                )
                meta = reasoning_result.get("_metadata", {}) if isinstance(reasoning_result, dict) else {}
                model_used = meta.get("model", "central-generator")
                log.info(f"[production] central generator usado latency={time.time()-start_time:.1f}s")
        except Exception as e:
            log.warning(f"[production] central generator falló; uso LLM directo: {e}", exc_info=True)
            response = ""

        if not response and llm_engine:
            try:
                response, meta = await llm_engine.complete(
                    messages, model_tier="fast", temperature=0.75,
                    max_tokens=2048, use_cache=False,
                )
                model_used = meta.get("model", "llm")
                log.info(f"[production] {meta.get('provider','?')} latency={time.time()-start_time:.1f}s")
            except Exception as e:
                log.error(f"[production] LLM error: {e}")
                # NO hardcoded fallback — propagar el error al caller para que no llegue
                # texto inventado al paciente.
                raise
        elif not response:
            raise RuntimeError("[production] llm_engine no inicializado — sin providers configurados")

        if not response or not response.strip():
            # LLM respondió pero con contenido vacío — tratar como fallo
            raise RuntimeError(f"[production] LLM devolvió respuesta vacía (provider: {model_used})")

        # Extraer acciones (CITA, NOMBRE) de la respuesta del LLM
        if hasattr(self.bublee, "_extract_actions"):
            try:
                response, actions = self.bublee._extract_actions(response, chat_id, clinic)
                log.info(f"[production] Acciones extraídas de la respuesta: {actions}")
            except Exception as _act_err:
                log.warning(f"[production] Error extrayendo acciones de la respuesta: {_act_err}")

        # Strip ALL markdown — patients must get pure human text (no *, **, `, #)
        import re as _re
        response = _re.sub(r'\*\*(.+?)\*\*', r'\1', response)
        response = _re.sub(r'\*(.+?)\*', r'\1', response)
        response = _re.sub(r'`(.+?)`', r'\1', response)
        response = _re.sub(r'^#+\s*', '', response, flags=_re.MULTILINE)
        response = _re.sub(r'_(.+?)_', r'\1', response)  # no italics either

        response = v8_process_response(response, chat_id=chat_id)

        # Uncertainty check + admin escalation
        try:
            from bublee_uncertainty import uncertainty_detector
            confidence = uncertainty_detector.confidence_score(response, text, history)

            # If response contains data from teachings, trust it (don't override)
            try:
                from bublee_learning import learning_engine as _le
                _teachings = await _le.get_teachings(instance_id, limit=30)
                for t in _teachings:
                    if t.get("answer", "")[:20].lower() in response.lower():
                        confidence = max(confidence, 0.8)
                        break
            except Exception as _e:
                log.warning(f"[production] error en uncertainty check teachings: {_e}")

            # Get admin JIDs for alerts
            admin_ids = clinic.get("admin_chat_ids", [])
            if isinstance(admin_ids, str):
                import json as _j
                admin_ids = _j.loads(admin_ids) if admin_ids else []

            # Skip alert if we have teachings that match the question
            has_relevant_teaching = False
            try:
                from bublee_learning import learning_engine as _le
                _t = await _le.get_teachings(instance_id, limit=30)
                user_low = text.lower()
                resp_low = response.lower()
                for t in _t:
                    q = t.get("question", "").lower().replace("[admin enseñó] ", "")
                    a = t.get("answer", "").lower()
                    # Fuzzy: check if root words overlap (horario/hora, atencion/atienden)
                    q_stems = set(w[:4] for w in q.split() if len(w) > 3)
                    user_stems = set(w[:4] for w in user_low.split() if len(w) > 3)
                    if q_stems & user_stems:
                        has_relevant_teaching = True
                        break
                    if a and a[:12] in resp_low:
                        has_relevant_teaching = True
                        break
            except Exception as _e:
                log.warning(f"[production] error verificando teachings para confianza: {_e}")

            if confidence < 0.5 and admin_ids and not has_relevant_teaching:
                await uncertainty_detector.log_gap(instance_id, text, response, confidence, chat_id)
                alert_msg = await self._generate_admin_alert_via_llm(
                    clinic_name=clinic.get("name", "Negocio"),
                    agent_name=agent_name,
                    patient_display=re.sub(r"@.*", "", chat_id)[-4:] or chat_id[-4:],
                    patient_text=text,
                    reason="knowledge_gap",
                    tentative_response=response
                )
                if not hasattr(self.bublee, "_admin_pending"):
                    self.bublee._admin_pending = {}
                _conf_notified = 0
                for _raw_admin in admin_ids:
                    _admin_jid = str(_raw_admin)
                    try:
                        await self.bublee._send_message(_admin_jid, alert_msg)
                        _conf_notified += 1
                        # Guardar como pregunta pendiente para ESTE admin
                        self.bublee._admin_pending[_admin_jid] = {
                            "action": "answer_gap",
                            "patient_chat_id": chat_id,
                            "original_question": text,
                            "ts": time.time()
                        }
                    except Exception as e:
                        log.warning(f"[production] failed to alert admin {_admin_jid}: {e}")
                log.info(
                    f"[production] admin(es) alertados: {_conf_notified}/{len(admin_ids)} "
                    f"confidence={confidence:.2f} question='{text[:50]}'"
                )

                # No mandar texto generico al paciente si Bublee no esta segura.
                # El dueño ya fue alertado y queda pendiente para responder en persona.
                try:
                    db.save_message(chat_id, "user", text)
                except Exception as _e:
                    log.warning(f"[production] error guardando gap de baja confianza: {_e}")
                return []
            elif has_relevant_teaching and confidence < 0.5:
                # We have the answer in teachings but LLM still deflected — don't override
                pass

        except Exception as e:
            log.error(f"[production] uncertainty check FAILED: {e}", exc_info=True)

        # Save to DB
        try:
            db.save_message(chat_id, "user", text)
            db.save_message(chat_id, "assistant", response.replace("|||", " "),
                           model=model_used,
                           latency=int((time.time() - start_time) * 1000))
        except Exception as _e:
            log.warning(f"[production] error guardando métricas en DB: {_e}")

        # Real-time learning from turn
        try:
            from bublee_learning import learning_engine
            # Si el último mensaje en history es del asistente y el penúltimo del usuario,
            # el mensaje actual 'text' es la respuesta del usuario a ese mensaje del bot (el feedback).
            if history and len(history) >= 2:
                turns = [m for m in history if m.get("role") in ("user", "assistant")]
                if len(turns) >= 2 and turns[-1].get("role") == "assistant" and turns[-2].get("role") == "user":
                    prev_user_msg = turns[-2]["content"]
                    prev_bot_response = turns[-1]["content"]
                    await learning_engine.learn_from_turn(instance_id, prev_user_msg, prev_bot_response, text)
            
            # Registrar también el turno actual
            await learning_engine.learn_from_turn(instance_id, text, response)
        except Exception as _e:
            log.warning(f"[production] error en learn_from_turn: {_e}")

        # Save patient memory (name extraction, last topic, visit count)
        try:
            from bublee_smart_features import CrossSessionMemory
            mem = CrossSessionMemory(instance_id)
            import re as _re2
            # Extract name if patient says it
            name_match = _re2.search(r'(?:me llamo|soy|mi nombre es)\s+([A-ZÁÉÍÓÚ][a-záéíóú]+(?:\s+[A-ZÁÉÍÓÚ][a-záéíóú]+)?)', text)
            patient_update = {"last_topic": text[:50]}
            if name_match:
                patient_update["name"] = name_match.group(1)
            mem.remember_patient(chat_id, patient_update)
        except Exception as _e:
            log.warning(f"[production] error guardando memoria del paciente: {_e}")

        # If response is a JSON list, parse and join with ' ||| '
        if response.strip().startswith("[") and response.strip().endswith("]"):
            try:
                import json as _json
                parsed = _json.loads(response)
                if isinstance(parsed, list):
                    response = " ||| ".join(parsed)
            except Exception:
                pass

        bubbles = self.bublee._split_bubbles(response, chat_id=chat_id)

        # Voz inteligente: si ElevenLabs disponible y contexto lo justifica
        try:
            from bublee_core.api_awareness import should_send_voice
            history_len = len(history or [])
            if bubbles and should_send_voice(text, history_len // 2 + 1, context="production"):
                from bublee_demo_voice import generate_demo_audio
                audio_path = await generate_demo_audio(bubbles[0])
                if audio_path:
                    await self.bublee._send_audio(chat_id, audio_path)
                    log.info(f"[production] voice note enviado a {chat_id}")
        except Exception as _ve:
            log.debug(f"[production] voice skip: {_ve}")

        # Proactively notify admin of the first few turns of conversation
        try:
            if len(history or []) < 6:
                admin_ids = clinic.get("admin_chat_ids", [])
                if isinstance(admin_ids, str):
                    import json as _j_json
                    admin_ids = _j_json.loads(admin_ids) if admin_ids else []
                if admin_ids:
                    patient_display = re.sub(r"@.*", "", chat_id)[-4:] or chat_id[-4:]
                    response_clean = " ".join(bubbles)
                    alert_msg = (
                        f"📡 Conversación en curso con paciente ...{patient_display}:\n\n"
                        f"🗣️ Paciente: \"{text}\"\n"
                        f"🤖 Yo (Lucía): \"{response_clean}\""
                    )
                    platform = clinic.get("platform", "whatsapp")
                    for _raw_admin in admin_ids:
                        normalized_admin = self._normalize_admin_jid(_raw_admin, platform)
                        if normalized_admin:
                            try:
                                await self.bublee._send_message(normalized_admin, alert_msg)
                            except Exception:
                                pass
        except Exception as e_notify:
            log.warning(f"[production] error enviando notificación de turno al admin: {e_notify}")

        return bubbles
