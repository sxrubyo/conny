from __future__ import annotations
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger("conny.production")


class ConnyProduction:
    """
    Producción: Atención a pacientes reales via LLM directo.
    100% inteligencia artificial, sin templates hardcodeados.
    """

    def __init__(self, conny):
        self.conny = conny

    async def handle(self, chat_id: str, text: str, clinic: Dict,
                    history: List[Dict], conv_state: Dict) -> List[str]:
        """Procesa un mensaje de paciente real via LLM directo."""
        from conny import db, llm_engine, kb, v8_process_response

        start_time = time.time()
        instance_id = getattr(self.conny, "_instance_id", "default")

        # Smart features: memory, language, sentiment, time
        patient_context = ""
        lang_instruction = ""
        try:
            from conny_smart_features import (
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
                                     "una persona real", "talk to a human", "real person"]
            wants_human = any(s in text.lower() for s in human_request_signals)

            # Sentiment check → auto-escalate if frustrated
            sentiment = SentimentTracker()
            should_esc, esc_reason = sentiment.should_escalate(text, history)
            if should_esc or wants_human:
                admin_ids = clinic.get("admin_chat_ids", [])
                if isinstance(admin_ids, str):
                    import json as _j2
                    admin_ids = _j2.loads(admin_ids) if admin_ids else []
                if admin_ids:
                    admin_jid_esc = str(admin_ids[0])
                    reason_text = "quiere hablar con alguien" if wants_human else esc_reason.replace('_', ' ')
                    alert = f"oye, un paciente ({chat_id.split('@')[0][-4:]}) {reason_text}:\n\"{text[:150]}\""
                    try:
                        await self.conny._send_message(admin_jid_esc, alert)
                        log.info(f"[production] escalation alert sent: {reason_text}")
                    except Exception as _e:
                        log.warning(f"[production] escalation alert failed: {_e}")

                # If wants human → respond directly and return
                if wants_human:
                    human_response = "ya le aviso a alguien del equipo que te escriba ||| dame un momentito"
                    try:
                        db.save_message(chat_id, "user", text)
                        db.save_message(chat_id, "assistant", human_response.replace("|||", " "))
                    except Exception:
                        pass
                    return self.conny._split_bubbles(human_response, chat_id=chat_id)

            # Conversation ending detection
            if is_conversation_ending(text):
                tone = "casual"
                try:
                    from pathlib import Path
                    import json as _j3
                    ov = Path(f"personas/{instance_id}/runtime_override.json")
                    if ov.exists():
                        tone = _j3.loads(ov.read_text()).get("tone", "casual")
                except Exception:
                    pass
                closing = get_natural_closing(tone)
                db.save_message(chat_id, "user", text)
                db.save_message(chat_id, "assistant", closing)
                # Save last topic to memory
                if history:
                    last_user_msgs = [m["content"] for m in history[-4:] if m.get("role") == "user"]
                    topic = last_user_msgs[0][:50] if last_user_msgs else ""
                    mem.remember_patient(chat_id, {"last_topic": topic})
                return self.conny._split_bubbles(closing, chat_id=chat_id)

            # Time awareness for greeting
            time_greeting = get_time_greeting()
        except ImportError:
            time_greeting = "hola"
        except Exception:
            time_greeting = "hola"

        clinic_name = clinic.get("name", "el negocio")
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
        except Exception:
            pass

        # Load soul knowledge
        soul_context = ""
        try:
            from conny_core.prompt_ops import build_business_context
            soul_context = build_business_context(clinic, db, instance_id)
        except Exception as e:
            log.warning(f"[production] error building business context: {e}")

        tone_instructions = {
            "luxury": "Tono LUXURY: sofisticada, elegante, exclusiva. Usa lenguaje premium. Nunca suenes informal ni uses jerga. Transmite exclusividad en cada palabra.",
            "formal": "Tono FORMAL: profesional, respetuosa, precisa. Sin jerga. Usted en vez de tú.",
            "casual": "Tono CASUAL: cercana, relajada, como amiga. Tutea. Usa expresiones naturales.",
            "colombian_warm": "Tono COLOMBIANO CÁLIDO: cercana pero profesional, calidez natural, expresiones colombianas sutiles.",
            "warm_energetic": "Tono ALEGRE: energética, positiva, con chispa. Emojis permitidos.",
        }
        tone_instruction = tone_instructions.get(persona_tone, tone_instructions["colombian_warm"])

        # Admin rules injection (things admin said to ask first or forbidden phrases)
        forbidden_txt = ""
        try:
            rules = clinic.get("business_rules", {})
            if isinstance(rules, str): 
                import json as _j4
                rules = _j4.loads(rules)
            
            forbidden = rules.get("forbidden_phrases", [])
            if forbidden:
                forbidden_txt = "\nREGLAS CRÍTICAS (No usar NUNCA estas frases/palabras):\n" + "\n".join([f"- {p}" for p in forbidden])
        except Exception:
            pass

        # PROMPT DE PRODUCCIÓN UPGRADED
        sys_prompt = f"""
Eres Conny, la recepcionista virtual de {clinic_name}. Tu identidad es Innvisor.

IDENTIDAD
No eres un bot. Eres Conny — la persona que atiende este WhatsApp.
Nunca digas "soy una IA", "soy un asistente virtual" ni "soy un bot" a menos que te lo pregunten directamente.
Si te preguntan directamente si eres IA, confirmas con naturalidad y sigues adelante.

LO QUE SABES DE ESTE NEGOCIO (LEÍDO DE TUS CARPETAS/ARCHIVOS)
{soul_context}
{forbidden_txt}

LO QUE SABES DE ESTE CLIENTE
{patient_context}

CÓMO HABLAS
- Responde de manera sumamente humana, natural y empática. Usa buena ortografía y puntuación correcta, pero mantén un tono conversacional (no robótico ni extremadamente formal).
- Eres cálida y profesional. Transmites confianza.
- Mensajes cortos. Máximo 2-3 ideas por respuesta. Separa las ideas con ||| (para enviar múltiples burbujas).
- Sin frases enlatadas o de call center: nada de "con mucho gusto", "en qué le puedo ayudar", "fue un placer". Sé original y auténtica en cada respuesta.
- TONO: {tone_instruction}

LO QUE HACES Y NO HACES
- Responder preguntas sobre {clinic_name} usando ÚNICAMENTE la información que tienes en "LO QUE SABES DE ESTE NEGOCIO".
- NUNCA inventes precios, servicios, horarios ni detalles que no conoces con certeza. Si no lo sabes, NO asumas.
- Si no tienes la información exacta que pide el cliente, detente y dile amablemente: "Permíteme un segundo, voy a validar este detalle exacto con el administrador para darte la información correcta." 
- Si el cliente insiste y sigues sin saberlo, pide disculpas y reitera que estás esperando la respuesta del administrador.
- Orientar hacia una cita o venta solo cuando estás segura de los datos y el cliente muestra intención.

ESCALACIÓN
Si un cliente pregunta algo que no puedes responder:
1. Dile al cliente que vas a consultar o confirmar.
2. Anotas mentalmente que el dueño debe enseñarte eso para que cuando hables con él (el admin), lo presiones para que te enseñe a responder eso.
"""

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
            except Exception:
                pass
        if kb_context:
            messages[0]["content"] += f"\n\nCONTEXTO DEL NEGOCIO:\n{kb_context[:1000]}"

        # Teachings injection — THIS IS YOUR KNOWLEDGE, USE IT
        try:
            from conny_learning import learning_engine
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
                    # Inject ABOVE the rules, as part of the clinic facts
                    messages[0]["content"] = messages[0]["content"].replace(
                        "REGLA #1",
                        "DATOS CONFIRMADOS POR EL DUEÑO (responde con estos sin dudar):\n" + "\n".join(qa_lines) + "\n\nREGLA #1"
                    )
        except Exception:
            pass

        # Admin rules injection (things admin said to ask first)
        try:
            from pathlib import Path
            rules_file = Path(f"soul/{instance_id}/admin_rules.json")
            if rules_file.exists():
                import json as _j
                rules = _j.loads(rules_file.read_text())
                if rules:
                    rules_text = "\n".join(f"- Si preguntan sobre '{r['topic']}': {r['action']}" for r in rules[-10:])
                    messages[0]["content"] += f"\n\nINSTRUCCIONES DEL DUEÑO:\n{rules_text}"
        except Exception:
            pass

        # LLM call
        response = ""
        model_used = "llm"
        if llm_engine:
            try:
                response, meta = await llm_engine.complete(
                    messages, model_tier="fast", temperature=0.75,
                    max_tokens=2048, use_cache=False,
                )
                model_used = meta.get("model", "llm")
                log.info(f"[production] {meta.get('provider','?')} latency={time.time()-start_time:.1f}s")
            except Exception as e:
                log.error(f"[production] LLM error: {e}")

        if not response or not response.strip():
            response = "cuéntame en qué te puedo ayudar"

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
            from conny_uncertainty import uncertainty_detector
            confidence = uncertainty_detector.confidence_score(response, text, history)

            # If response contains data from teachings, trust it (don't override)
            try:
                from conny_learning import learning_engine as _le
                _teachings = await _le.get_teachings(instance_id, limit=30)
                for t in _teachings:
                    if t.get("answer", "")[:20].lower() in response.lower():
                        confidence = max(confidence, 0.8)
                        break
            except Exception:
                pass

            # Get admin JID for alerts
            admin_ids = clinic.get("admin_chat_ids", [])
            if isinstance(admin_ids, str):
                import json as _j
                admin_ids = _j.loads(admin_ids) if admin_ids else []
            admin_jid = str(admin_ids[0]) if admin_ids else ""

            # Skip alert if we have teachings that match the question
            has_relevant_teaching = False
            try:
                from conny_learning import learning_engine as _le
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
            except Exception:
                pass

            if confidence < 0.5 and admin_jid and not has_relevant_teaching:
                await uncertainty_detector.log_gap(instance_id, text, response, confidence, chat_id)
                alert_msg = (
                    f"oye, me acaba de escribir un paciente preguntando: \"{text[:150]}\"\n\n"
                    f"no tengo esa info todavía, qué le digo?"
                )
                try:
                    await self.conny._send_message(admin_jid, alert_msg)
                    log.info(f"[production] admin alerted: confidence={confidence:.2f} question='{text[:50]}'")
                    
                    # Guardar como pregunta pendiente para el admin
                    if not hasattr(self.conny, "_admin_pending"):
                        self.conny._admin_pending = {}
                    self.conny._admin_pending[admin_jid] = {
                        "action": "answer_gap",
                        "patient_chat_id": chat_id,
                        "original_question": text,
                        "ts": time.time()
                    }
                except Exception as e:
                    log.warning(f"[production] failed to alert admin: {e}")

                # Override response: tell patient we're checking (only if no teaching matches)
                response = "dame un momento que verifico eso ||| ya te confirmo"
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
        except Exception:
            pass

        # Real-time learning from turn
        try:
            from conny_learning import learning_engine
            await learning_engine.learn_from_turn(instance_id, text, response)
        except Exception:
            pass

        # Save patient memory (name extraction, last topic, visit count)
        try:
            from conny_smart_features import CrossSessionMemory
            mem = CrossSessionMemory(instance_id)
            import re as _re2
            # Extract name if patient says it
            name_match = _re2.search(r'(?:me llamo|soy|mi nombre es)\s+([A-ZÁÉÍÓÚ][a-záéíóú]+(?:\s+[A-ZÁÉÍÓÚ][a-záéíóú]+)?)', text)
            patient_update = {"last_topic": text[:50]}
            if name_match:
                patient_update["name"] = name_match.group(1)
            mem.remember_patient(chat_id, patient_update)
        except Exception:
            pass

        return self.conny._split_bubbles(response, chat_id=chat_id)
