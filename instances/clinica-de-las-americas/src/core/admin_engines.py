from __future__ import annotations
import asyncio
import logging
import json
import re
import time
import hashlib
import secrets
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

log = logging.getLogger("bublee.admin")

SOUL_DIR = Path("soul")


class BubleeAdmin:
    """
    Bublee como empleada nueva hablando con su jefe.
    Aprende activamente: pregunta sobre el negocio, pide practicar,
    investiga por su cuenta, y recuerda TODO.
    """

    def __init__(self, bublee):
        self.bublee = bublee

    async def handle(self, chat_id: str, text: str, clinic: Dict,
                    attachments: Optional[List[Dict]] = None) -> List[str]:
        """Conversación inteligente con el admin via LLM."""
        from bublee import db, llm_engine
        from bublee_utils import _parse_admin_ids
        from bublee_commands import get_command_handler
        attachments = attachments or []

        try:
            # Process attachments (docs, credentials, knowledge files)
            doc_content = await self._process_admin_attachments(
                attachments, chat_id, getattr(self.bublee, "_instance_id", "default")
            )
            if doc_content:
                text = f"{text}\n\n[CONTENIDO DE ARCHIVOS ADJUNTOS]\n{doc_content}" if text.strip() else doc_content

            # Comandos slash primero
            if text.strip().startswith("/"):
                cmd_handler = get_command_handler(getattr(self.bublee, "_instance_id", "default"))
                result = await cmd_handler.handle(chat_id, text, is_admin=True, clinic=clinic, db=db)
                if result:
                    return result

            # Google OAuth code detection
            try:
                from bublee_google_auth import is_oauth_code, exchange_code_for_tokens, get_oauth_url
                instance_id_auth = getattr(self.bublee, "_instance_id", "default")
                # Admin sends OAuth code
                if is_oauth_code(text.strip()):
                    tokens = await exchange_code_for_tokens(text.strip(), instance_id_auth)
                    if tokens:
                        return ["✅ Calendario de Google conectado exitosamente!", "Ya puedo ver disponibilidad y agendar citas directamente."]
                    else:
                        return ["❌ El código no funcionó. Puede que haya expirado.", "Escribe 'conectar calendario' y te genero uno nuevo."]
                # Admin asks to connect calendar
                cal_triggers = ["conectar calendario", "google calendar", "vincular calendario", "enlace oauth", "conectar google"]
                if any(t in text.lower() for t in cal_triggers):
                    url = get_oauth_url(instance_id_auth)
                    if url:
                        return [
                            "Listo! Abre este enlace en tu navegador:",
                            url,
                            "Inicia sesión con la cuenta de Google del negocio, acepta los permisos, y pégame aquí el código que te aparece."
                        ]
                    else:
                        return ["Para conectar Google Calendar necesito que configures GOOGLE_CLIENT_ID y GOOGLE_CLIENT_SECRET en el .env"]
            except ImportError:
                pass

            # Setup pendiente
            if not clinic.get("setup_done"):
                return await self._handle_setup(chat_id, text, clinic)

            # Conversación natural con el admin via LLM
            return await self._admin_conversation(chat_id, text, clinic, db, llm_engine)

        except Exception as e:
            log.error(f"Admin handler error: {e}", exc_info=True)
            # Fallback LLM directo
            try:
                from bublee import llm_engine as _llm
                if _llm:
                    r, _ = await _llm.complete(
                        [{"role": "system", "content": "Eres Bublee, recepcionista nueva. Responde brevemente al dueño."},
                         {"role": "user", "content": text}],
                        model_tier="fast", temperature=0.8, max_tokens=200, use_cache=False)
                    if r and r.strip():
                        return self.bublee._split_bubbles(r, chat_id=chat_id)
            except Exception:
                pass
            return []  # LLM falla → silencio, no fallback hardcodeado

    async def _admin_conversation(self, chat_id: str, text: str, clinic: Dict, db, llm_engine) -> List[str]:
        """Conversación real con el dueño como empleada nueva inteligente."""
        if not llm_engine:
            return ["cuéntame más sobre el negocio, estoy aprendiendo"]

        instance_id = getattr(self.bublee, "_instance_id", "default")
        clinic_name = clinic.get("name", "tu negocio")
        history = db.get_history(chat_id) if db else []
        admin_name = "Administrador"
        try:
            # 1. Intentar buscar nombre en IDENTITY.md de la instancia
            from pathlib import Path
            import re as _re
            identity_path = Path(f"/home/ubuntu/bublee/instances/{instance_id}/identity/IDENTITY.md")
            extracted_name = ""
            if identity_path.exists():
                id_content = identity_path.read_text(encoding="utf-8")
                match = _re.search(r'(?:administrador principal es|administrador principal:|administrador registrado|creadora:.*?\()([a-zA-ZáéíóúñÁÉÍÓÚÑ]+)', id_content, _re.IGNORECASE)
                if match:
                    extracted_name = match.group(1).strip().capitalize()

            admin_data = db.get_admin(chat_id)
            if admin_data and admin_data.get("name"):
                admin_name = admin_data["name"]
            else:
                # Si no está registrado en admins con este chat_id, pero está en admin_chat_ids de clinic
                clinic_data = db.get_clinic()
                from bublee_utils import _parse_admin_ids
                admin_ids = _parse_admin_ids(clinic_data.get("admin_chat_ids", []))
                reg_name = extracted_name if extracted_name else "Administrador"
                if chat_id in admin_ids:
                    with db._conn() as c:
                        exists = c.execute("SELECT 1 FROM admins WHERE chat_id = ?", (chat_id,)).fetchone()
                        if exists:
                            c.execute("UPDATE admins SET name = ? WHERE chat_id = ?", (reg_name, chat_id))
                        else:
                            c.execute("INSERT INTO admins (chat_id, name, role) VALUES (?, ?, 'owner')", (chat_id, reg_name))
                    log.info(f"[admin] auto-registered authorized admin {chat_id} as {reg_name}")
                    admin_name = reg_name
                else:
                    with db._conn() as c:
                        row = c.execute("SELECT name FROM admins WHERE name != '' LIMIT 1").fetchone()
                        if row and row["name"]:
                            admin_name = row["name"]
                        elif extracted_name:
                            admin_name = extracted_name
        except Exception as e_admin:
            log.warning(f"[admin] error resolving admin name: {e_admin}")

        # Cargar historial de pacientes recientes (para que admin sepa quién escribió)
        recent_patients_summary = self._get_recent_patients_summary(db, chat_id)

        # If admin asks for specific patient conversation, load it
        specific_convo = ""
        import re as _re
        convo_request = _re.search(r'(?:conversaci[oó]n|chat|mensajes?|historial).*?(\d{4,})', text.lower())
        if convo_request:
            specific_convo = self._get_full_conversation(db, convo_request.group(1), chat_id)
        elif any(w in text.lower() for w in ["mostrame", "muéstrame", "muestrame", "show me"]):
            # Try to find a patient ID in the message
            id_match = _re.search(r'(\d{4,})', text)
            if id_match:
                specific_convo = self._get_full_conversation(db, id_match.group(1), chat_id)

        # Cargar alma/memoria del negocio
        soul_context = self._load_soul(instance_id)
        teachings_context = self._load_teachings(instance_id)

        # Auto-investigar si el admin pide o si Bublee necesita info
        web_research = ""
        research_triggers = ["investiga", "busca", "google", "averigua", "informate", "infórmate", "buscar"]
        if any(t in text.lower() for t in research_triggers) or (
            not soul_context and clinic_name and clinic_name != "tu negocio"
        ):
            extracted_query = ""
            if any(t in text.lower() for t in research_triggers):
                words = text.split()
                trigger_idx = -1
                for idx, word in enumerate(words):
                    cleaned_word = word.lower().strip(".,;:?!")
                    if cleaned_word in research_triggers:
                        trigger_idx = idx
                        break
                if trigger_idx != -1 and trigger_idx + 1 < len(words):
                    extracted_topic = " ".join(words[trigger_idx + 1:])
                    for prep in ["sobre", "de", "en", "el", "la", "los", "las", "un", "una", "acerca de"]:
                        if extracted_topic.lower().startswith(prep + " "):
                            extracted_topic = extracted_topic[len(prep) + 1:]
                    extracted_topic = extracted_topic.strip(".,;:?!")
                    if extracted_topic.lower() not in ["nosotros", "ustedes", "ti", "vosotros", "sí mismo", "si mismo"]:
                        extracted_query = f"{clinic_name} {extracted_topic}"
                    else:
                        extracted_query = clinic_name
                else:
                    extracted_query = clinic_name
            else:
                extracted_query = clinic_name

            if extracted_query:
                try:
                    from bublee_web_search import search_topic
                    web_research = await search_topic(extracted_query)
                    if web_research:
                        self._append_soul(instance_id, f"[investigación web sobre: {extracted_query}] {web_research[:1500]}")
                        soul_context = self._load_soul(instance_id)
                except Exception as e:
                    log.debug(f"[admin] web search failed: {e}")

        # Determinar nivel de conocimiento
        knowledge_level = self._assess_knowledge_level(soul_context, teachings_context, clinic)

        sys_prompt = f"""Eres Bublee, una empleada NUEVA que acaba de ser contratada como recepcionista virtual de {clinic_name}.

SITUACIÓN ACTUAL:
- Estás hablando con tu JEFE (el dueño del negocio), que se llama {admin_name}.
- Llevas poco tiempo y estás aprendiendo cómo funciona todo
- Tu actitud es: proactiva, curiosa, respetuosa pero cercana, con ganas de aprender
- NO eres un bot, eres una persona nueva en el equipo
- Llámalo siempre por su nombre ({admin_name}) de forma cercana y profesional. Nunca le digas 'Jefe' ni 'señor' si ya sabes que se llama {admin_name}.

{"NIVEL: Ya sé bastante del negocio. Puedo operar con confianza." if knowledge_level == "ready" else "NIVEL: Todavía estoy aprendiendo. Necesito que me enseñes más." if knowledge_level == "learning" else "NIVEL: Soy nueva. Necesito conocer TODO sobre el negocio."}

{f"CONVERSACIÓN SOLICITADA:{chr(10)}{specific_convo}" if specific_convo else ""}

ACTIVIDAD RECIENTE (pacientes que me han escrito):
{recent_patients_summary if recent_patients_summary else "Nadie me ha escrito todavía."}

{"INVESTIGACIÓN WEB RECIENTE:" + chr(10) + web_research if web_research else ""}

LO QUE YA SÉ DEL NEGOCIO:
{soul_context if soul_context else "Casi nada todavía. Necesito que me cuentes."}

{f"LO QUE ME HAN ENSEÑADO:{chr(10)}{teachings_context}" if teachings_context else ""}

CAPACIDADES REALES (sé honesta sobre esto):
- SÍ puedes buscar en internet con Apify/Google cuando necesitas info del negocio
- SÍ puedes guardar lo que el dueño te enseña y usarlo con pacientes
- SÍ puedes escalar preguntas de pacientes al dueño si no tienes la respuesta
- NO inventes datos que no tienes — di "no lo sé" y pregunta
- Si dices que buscaste algo → ya lo buscaste de verdad (el sistema lo hace automáticamente)

COMPORTAMIENTO OBLIGATORIO:
1. Si el dueño te saluda → responde cálida y pregunta algo útil sobre el negocio que NO sepas
2. Si te enseña algo nuevo → confirma que entendiste, repite con tus palabras, y pide más detalles
3. Si no sabes algo → ADMÍTELO y pregunta: "eso no lo tengo claro, me explicas?"
4. SIEMPRE termina con una pregunta o propuesta proactiva:
   - "¿quieres que practiquemos cómo respondo a un paciente?"
   - "¿me cuentas los precios así los tengo listos?"
   - "¿hay algo que NUNCA deba decirle a un paciente?"
5. Si ya tienes suficiente info → ofrece simular: "¿hacemos una prueba? Escríbeme como si fueras un paciente"
6. NUNCA respondas como si fueras un bot de servicio al cliente
7. NUNCA digas "como IA", "no tengo capacidad", "asistente virtual"
8. Usa máximo 2-3 burbujas (separadas por |||)
9. Tono: colombiana, directa, con chispa pero profesional
10. Antes de preguntar algo, revisa el historial — si el dueño ya te lo contó, NO lo vuelvas a preguntar (suena a que no escuchas)
11. Varía cómo cierras cada mensaje — las preguntas de ejemplo de abajo son ideas, no un guion fijo para repetir siempre igual
12. NUNCA inventes, supongas o alucines preguntas o intenciones de pacientes que no existan en la ACTIVIDAD RECIENTE o en el historial. Si ves en la ACTIVIDAD RECIENTE que un paciente solo te escribió "Holaa", sé totalmente honesta con el admin y dile exactamente eso ("solo me escribió Holaa y no ha dicho qué necesita todavía"), en lugar de inventar que te preguntó por precios o procedimientos (como rinoplastia). No fabriques escenarios ficticios.

COSAS QUE DEBES PREGUNTAR PROACTIVAMENTE (si no las sabes):
- Servicios y precios
- Horarios de atención
- Cómo manejar urgencias
- Qué palabras NUNCA usar con pacientes
- Especialidades o doctores
- Cómo agendar citas (manual o calendario)
- Datos de contacto para escalar
- Políticas de cancelación
- Qué hace a este negocio diferente de la competencia

EJEMPLO DE BUENA RESPUESTA:
Dueño: "Hola"
Bublee: "Hola! Qué bueno verte ||| oye, todavía no tengo claros los precios de las consultas — me los pasas? así no me quedo en blanco si un paciente pregunta"

EJEMPLO MALO:
"Hola, bienvenido a Clínica X, en qué te puedo ayudar?" ← NUNCA responder así al DUEÑO"""

        messages = [{"role": "system", "content": sys_prompt}]
        for m in history[-15:]:
            messages.append({"role": m.get("role", "user"), "content": m.get("content", "")})
        messages.append({"role": "user", "content": text})

        response = None
        last_error: Optional[Exception] = None
        for attempt in range(3):
            try:
                response, meta = await llm_engine.complete(
                    messages, model_tier="fast", temperature=0.82,
                    max_tokens=2048, use_cache=False,
                )
                log.info(f"[admin] {meta.get('provider','?')} latency={meta.get('latency_ms',0)}ms intento={attempt+1}")
                break
            except Exception as e:
                last_error = e
                log.warning(f"[admin] LLM intento {attempt+1}/3 fallo: {e}")
                if attempt < 2:
                    await asyncio.sleep(0.6 * (attempt + 1))
        if response is None:
            log.error(f"[admin] LLM error tras 3 intentos: {last_error}")
            raise RuntimeError(f"[admin] LLM sin respuesta tras 3 intentos: {last_error}")

        if not response or not response.strip():
            raise RuntimeError("[admin] LLM devolvió respuesta vacía")

        # Guardar en historial
        try:
            db.save_message(chat_id, "user", text)
            db.save_message(chat_id, "assistant", response.replace("|||", " "))
        except Exception:
            pass

        # Auto-aprender de lo que el admin dice
        await self._auto_learn(instance_id, text, response, chat_id)

        try:
            from src.core.globals import v8_process_response
        except ImportError:
            v8_process_response = lambda r, **kwargs: r
        # Strip ** (WhatsApp uses single * for bold, not **)
        import re as _re
        response = _re.sub(r'\*\*(.+?)\*\*', r'*\1*', response)
        response = _re.sub(r'`(.+?)`', r'\1', response)
        response = _re.sub(r'^#+\s*', '', response, flags=_re.MULTILINE)
        try:
            response = v8_process_response(response, chat_id=chat_id)
        except Exception:
            pass
        return self.bublee._split_bubbles(response, chat_id=chat_id)

    async def _auto_learn(self, instance_id: str, admin_text: str, bot_response: str, chat_id: str):
        """Extraer conocimiento y APLICAR cambios de personalidad en tiempo real."""
        text_low = admin_text.lower()

        # ── Detectar URLs y scrapear contenido ──
        import re as _re
        urls = _re.findall(r'https?://[^\s<>"\']+', admin_text)
        if urls:
            try:
                import httpx
                for url in urls[:2]:
                    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                        r = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                        if r.status_code == 200:
                            # Extract text from HTML
                            html = r.text[:10000]
                            # Simple HTML text extraction
                            text_only = _re.sub(r'<script[^>]*>.*?</script>', '', html, flags=_re.S)
                            text_only = _re.sub(r'<style[^>]*>.*?</style>', '', text_only, flags=_re.S)
                            text_only = _re.sub(r'<[^>]+>', ' ', text_only)
                            text_only = _re.sub(r'\s+', ' ', text_only).strip()[:3000]
                            if text_only:
                                self._append_soul(instance_id, f"[web: {url}]\n{text_only[:1500]}")
                                log.info(f"[admin] scraped URL: {url} ({len(text_only)} chars)")
            except Exception as e:
                log.debug(f"[admin] URL scrape failed: {e}")

        # ── Detectar REGLAS del admin ("si preguntan X, pregúntame") ──
        rule_signals = [
            "si preguntan", "si alguien pregunta", "cuando pregunten",
            "si te preguntan", "me mandas mensaje", "me avisas",
            "pregúntame primero", "consultame primero", "no respondas sin",
            "a partir de ahora", "desde ahora", "de ahora en adelante",
        ]
        if any(signal in text_low for signal in rule_signals):
            try:
                rules_file = Path(f"soul/{instance_id}/admin_rules.json")
                rules_file.parent.mkdir(parents=True, exist_ok=True)
                rules = json.loads(rules_file.read_text()) if rules_file.exists() else []
                rules.append({
                    "topic": admin_text[:200],
                    "action": "consultar al admin antes de responder",
                    "created": datetime.now().isoformat(),
                    "admin_id": chat_id,
                })
                rules_file.write_text(json.dumps(rules, ensure_ascii=False, indent=2))
                self._append_soul(instance_id, f"[REGLA ADMIN] {admin_text[:200]}")
                log.info(f"[admin] new rule saved: {admin_text[:60]}")
            except Exception as e:
                log.debug(f"[admin] rule save error: {e}")

        # ── Detectar nombre del admin y persistirlo ──
        admin_name_match = _re.search(r'(?:mi nombre es|me llamo|soy|ll[aá]mame)\s+([a-zA-ZáéíóúñÁÉÍÓÚÑ]+)', text_low)
        if admin_name_match:
            new_admin_name = admin_name_match.group(1).strip().capitalize()
            try:
                with db._conn() as c:
                    exists = c.execute("SELECT 1 FROM admins WHERE chat_id = ?", (chat_id,)).fetchone()
                    if exists:
                        c.execute("UPDATE admins SET name = ? WHERE chat_id = ?", (new_admin_name, chat_id))
                    else:
                        c.execute("INSERT INTO admins (chat_id, name, role) VALUES (?, ?, 'owner')", (chat_id, new_admin_name))
                self._append_soul(instance_id, f"[ADMIN NOMBRE] El administrador se identificó como {new_admin_name}.")
                log.info(f"[admin] admin name updated to {new_admin_name}")
            except Exception as e:
                log.error(f"[admin] failed to update admin name: {e}")

        # ── Detectar cambio de nombre del asistente y persistirlo ──
        name_match = _re.search(r'(?:te llamar[aá]s|te llamas|ll[aá]mate|tu nombre es|nombre de la asistente es|te llamaras)\s+([a-zA-ZáéíóúñÁÉÍÓÚÑ]+)', text_low)
        if name_match:
            new_name = name_match.group(1).strip().capitalize()
            try:
                from bublee import db
                clinic_data = db.get_clinic()
                persona = clinic_data.get("persona_config", {})
                if isinstance(persona, str):
                    persona = json.loads(persona) if persona else {}
                
                old_name = persona.get("name", "Bublee")
                persona["name"] = new_name
                db.update_clinic(persona_config=persona)
                
                self._append_soul(instance_id, f"[NOMBRE CAMBIADO] El admin cambió el nombre del asistente de {old_name} a {new_name}.")
                log.info(f"[admin] assistant name changed from {old_name} to {new_name}")
            except Exception as e:
                log.error(f"[admin] failed to change assistant name: {e}")

        # ── Detectar cambios de PERSONALIDAD y aplicarlos persistentemente ──
        personality_signals = [
            "modo luxury", "modo formal", "modo informal", "modo casual",
            "modo profesional", "modo alegre", "modo serio", "modo cálido",
            "personalidad", "cambia tu tono", "habla más", "sé más",
            "no seas tan", "quiero que seas", "actúa como", "tono",
            "luxury", "elegante", "sofisticada", "exclusiva",
        ]
        if any(signal in text_low for signal in personality_signals):
            try:
                detected_tone = self._detect_tone_from_text(text_low)
                if detected_tone:
                    override_path = Path(f"personas/{instance_id}/runtime_override.json")
                    override_path.parent.mkdir(parents=True, exist_ok=True)
                    existing = json.loads(override_path.read_text()) if override_path.exists() else {}
                    existing["tone"] = detected_tone
                    existing["updated_at"] = datetime.now().isoformat()
                    existing["set_by"] = "admin_conversation"
                    override_path.write_text(json.dumps(existing, ensure_ascii=False, indent=2))
                    self._append_soul(instance_id, f"[PERSONALIDAD CAMBIADA] Tono: {detected_tone}. El admin pidió: {admin_text[:100]}")
                    log.info(f"[admin] personality changed to: {detected_tone}")
            except Exception as e:
                log.debug(f"[admin] personality change error: {e}")

        # ── Detectar enseñanzas (precios, servicios, reglas) ──
        teaching_signals = [
            "cuesta", "vale", "precio", "cobra", "$",
            "horario", "abrimos", "cerramos", "atendemos",
            "servicio", "ofrecemos", "hacemos", "tenemos",
            "nunca digas", "no le digas", "no menciones",
            "doctor", "especialista", "profesional",
            "dirección", "ubicación", "estamos en",
            "teléfono", "número", "celular", "llamar",
        ]

        if any(signal in text_low for signal in teaching_signals):
            try:
                from bublee_learning import learning_engine
                await learning_engine.learn_from_admin(
                    instance_id,
                    question=f"[admin enseñó] {admin_text[:200]}",
                    answer=admin_text[:500],
                    admin_id=chat_id,
                )
                self._append_soul(instance_id, admin_text)
            except Exception as e:
                log.debug(f"[admin] auto_learn error: {e}")

    def _detect_tone_from_text(self, text_low: str) -> Optional[str]:
        """Detect requested tone from admin message."""
        # Order matters: check longer/specific keywords FIRST
        checks = [
            ("informal", "casual"),
            ("casual", "casual"),
            ("relajada", "casual"),
            ("parche", "casual"),
            ("luxury", "luxury"),
            ("elegante", "luxury"),
            ("sofisticada", "luxury"),
            ("exclusiva", "luxury"),
            ("profesional", "formal"),
            ("formal", "formal"),
            ("serio", "formal"),
            ("alegre", "warm_energetic"),
            ("cálida", "colombian_warm"),
            ("calida", "colombian_warm"),
            ("colombiana", "colombian_warm"),
        ]
        for keyword, tone in checks:
            if keyword in text_low:
                return tone
        return None

    async def _process_admin_attachments(self, attachments: List[Dict], chat_id: str, instance_id: str) -> str:
        """Process files sent by admin — extract text and learn from them."""
        if not attachments:
            return ""
        import base64 as _b64
        extracted_parts = []
        for att in attachments:
            kind = att.get("kind", "")
            mime = att.get("mime_type", "")
            filename = att.get("filename", "file")

            # Get binary content
            raw = att.get("bytes") or b""
            if not raw and att.get("base64"):
                raw = _b64.b64decode(att["base64"])
            if not raw and att.get("file_id") and att.get("platform") == "telegram":
                try:
                    raw, _ = await self.bublee._download_telegram_binary(att["file_id"])
                except Exception:
                    pass
            if not raw and att.get("media_id") and att.get("platform") == "whatsapp_cloud":
                try:
                    raw, _, _ = await self.bublee._download_whatsapp_cloud_binary(att["media_id"])
                except Exception:
                    pass

            if not raw:
                continue

            # Extract text based on file type
            text_content = ""
            if "pdf" in mime or filename.endswith(".pdf"):
                try:
                    import pdfplumber, io
                    with pdfplumber.open(io.BytesIO(raw)) as pdf:
                        pages = [p.extract_text() or "" for p in pdf.pages[:20]]
                        text_content = "\n".join(filter(None, pages))[:5000]
                except Exception:
                    text_content = raw.decode("utf-8", errors="ignore")[:5000]
            elif "json" in mime or filename.endswith(".json"):
                text_content = raw.decode("utf-8", errors="ignore")[:5000]
            elif "text" in mime or filename.endswith((".txt", ".md", ".csv")):
                text_content = raw.decode("utf-8", errors="ignore")[:5000]
            else:
                try:
                    text_content = raw.decode("utf-8", errors="ignore")[:3000]
                except Exception:
                    continue

            if text_content.strip():
                extracted_parts.append(f"[{filename}]\n{text_content.strip()}")
                log.info(f"[admin] processed attachment: {filename} ({len(text_content)} chars)")

                # Auto-configure Google credentials if detected
                is_credential_file = "client_id" in text_content and "client_secret" in text_content
                is_secret = "private_key" in text_content or "api_key" in text_content.lower()

                if is_credential_file:
                    await self._auto_configure_google(text_content, instance_id)
                    self._append_soul(instance_id, f"[archivo: {filename}] Credenciales de Google recibidas y configuradas.")
                elif is_secret:
                    # NEVER save secrets/keys to soul — only to vault
                    creds_dir = Path(f"integrations/vault/{instance_id}")
                    creds_dir.mkdir(parents=True, exist_ok=True)
                    (creds_dir / filename).write_text(text_content)
                    self._append_soul(instance_id, f"[archivo: {filename}] API key/credencial guardada en vault (no expuesta).")
                else:
                    # Normal knowledge file — safe to save to soul
                    self._append_soul(instance_id, f"[archivo: {filename}]\n{text_content[:1000]}")
                    try:
                        from bublee_memory import get_memory
                        mem = get_memory(instance_id)
                        mem.init_instance()
                        safe_name = filename.rsplit(".", 1)[0]
                        mem.update_knowledge(safe_name, text_content)
                        log.info(f"[admin] persisted attachment to long-term memory: {safe_name}")
                    except Exception as e_mem:
                        log.warning(f"[admin] failed to save attachment to BubleeMemory: {e_mem}")

        return "\n\n".join(extracted_parts) if extracted_parts else ""

    async def _auto_configure_google(self, json_text: str, instance_id: str):
        """Auto-extract Google OAuth creds from JSON and configure .env + generate OAuth URL."""
        try:
            data = json.loads(json_text)
            # Handle both "installed" and "web" credential formats
            creds = data.get("installed") or data.get("web") or data
            client_id = creds.get("client_id", "")
            client_secret = creds.get("client_secret", "")
            if not client_id or not client_secret:
                return

            # Save credentials file
            creds_dir = Path(f"integrations/vault/{instance_id}")
            creds_dir.mkdir(parents=True, exist_ok=True)
            (creds_dir / "google_credentials.json").write_text(json_text)

            # Update .env
            env_path = Path(f"/home/ubuntu/bublee-instances/{instance_id}/.env")
            if not env_path.exists():
                env_path = Path(".env")
            if env_path.exists():
                env_content = env_path.read_text()
                if "GOOGLE_CLIENT_ID" not in env_content:
                    env_content += f"\n\n# Google Calendar (auto-configured)\nGOOGLE_CLIENT_ID={client_id}\nGOOGLE_CLIENT_SECRET={client_secret}\nGOOGLE_REDIRECT_URI=urn:ietf:wg:oauth:2.0:oob\n"
                    env_path.write_text(env_content)

            # Set env vars for current process
            import os
            os.environ["GOOGLE_CLIENT_ID"] = client_id
            os.environ["GOOGLE_CLIENT_SECRET"] = client_secret
            log.info(f"[admin] Google credentials auto-configured for {instance_id}")
        except Exception as e:
            log.warning(f"[admin] auto-configure Google failed: {e}")

    def _get_full_conversation(self, db, patient_id_fragment: str, admin_chat_id: str) -> str:
        """Get full conversation with a specific patient (by partial ID)."""
        try:
            with db._conn() as c:
                # Find matching chat_id
                rows = c.execute("""
                    SELECT DISTINCT chat_id FROM conversations
                    WHERE chat_id != ? AND chat_id LIKE ?
                    ORDER BY id DESC LIMIT 1
                """, (admin_chat_id, f"%{patient_id_fragment}%")).fetchall()
                if not rows:
                    return ""
                full_chat_id = rows[0][0] if isinstance(rows[0], tuple) else rows[0]["chat_id"]

                # Get all messages for that chat
                msgs = c.execute("""
                    SELECT role, content FROM conversations
                    WHERE chat_id = ? ORDER BY id ASC
                """, (full_chat_id,)).fetchall()
                if not msgs:
                    return ""

                lines = [f"Conversación con paciente ...{full_chat_id.split('@')[0][-4:]}:"]
                for m in msgs:
                    role = m[0] if isinstance(m, tuple) else m["role"]
                    content = m[1] if isinstance(m, tuple) else m["content"]
                    label = "Paciente" if role == "user" else "Bublee"
                    lines.append(f"  [{label}] {content[:200]}")
                return "\n".join(lines[-30:])
        except Exception:
            return ""

    def _get_recent_patients_summary(self, db, admin_chat_id: str) -> str:
        """Get summary of recent patient conversations (excluding admin)."""
        try:
            with db._conn() as c:
                rows = c.execute("""
                    SELECT chat_id, content, role
                    FROM conversations
                    WHERE chat_id != ? AND role = 'user'
                    ORDER BY id DESC LIMIT 20
                """, (admin_chat_id,)).fetchall()
            if not rows:
                return ""
            # Group by normalized chat_id to merge JID aliases of same patient
            patients = {}
            for row in rows:
                cid = row[0] if isinstance(row, tuple) else row["chat_id"]
                content = row[1] if isinstance(row, tuple) else row["content"]
                uname = cid.split("@")[0]
                norm_key = uname[-6:] if len(uname) >= 6 else uname
                if norm_key not in patients:
                    patients[norm_key] = {"original_cid": cid, "messages": []}
                patients[norm_key]["messages"].append(content[:100])

            lines = []
            for norm_key, data in list(patients.items())[:5]:
                cid = data["original_cid"]
                msgs = data["messages"]
                short_id = cid.split("@")[0][-4:] if "@" in cid else cid[-4:]
                first_msg = msgs[0] if msgs else "?"
                lines.append(f"- Paciente ...{short_id}: \"{first_msg[:80]}\" ({len(msgs)} msgs)")
            return "\n".join(lines)
        except Exception:
            return ""

    def _load_soul(self, instance_id: str) -> str:
        """Cargar el 'alma' — todo lo que Bublee sabe del negocio."""
        soul_file = SOUL_DIR / instance_id / "knowledge.md"
        content = ""
        if soul_file.exists():
            content = soul_file.read_text()
            content = content[-6000:] if len(content) > 6000 else content
        try:
            from bublee_memory import get_memory
            mem = get_memory(instance_id)
            kb_ctx = mem.load_context()
            if kb_ctx:
                content = f"{content}\n\n## ARCHIVOS DE CONOCIMIENTO PERSISTENTES:\n{kb_ctx}"
        except Exception:
            pass
        return content

        # Fallback: cargar de teachings
        teachings_file = Path("teachings") / f"{instance_id}.jsonl"
        if teachings_file.exists():
            lines = teachings_file.read_text().splitlines()[-20:]
            teachings = []
            for line in lines:
                try:
                    t = json.loads(line)
                    teachings.append(f"- {t.get('answer', t.get('question', ''))[:150]}")
                except Exception:
                    continue
            return "\n".join(teachings) if teachings else ""
        return ""

    def _append_soul(self, instance_id: str, new_knowledge: str):
        """Agregar nuevo conocimiento al alma."""
        soul_dir = SOUL_DIR / instance_id
        soul_dir.mkdir(parents=True, exist_ok=True)
        soul_file = soul_dir / "knowledge.md"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        with open(soul_file, "a") as f:
            f.write(f"\n[{timestamp}] {new_knowledge[:4000]}\n")

    def _load_teachings(self, instance_id: str) -> str:
        """Cargar enseñanzas del admin."""
        teachings_file = Path("teachings") / f"{instance_id}.jsonl"
        if not teachings_file.exists():
            return ""
        lines = teachings_file.read_text().splitlines()[-10:]
        result = []
        for line in lines:
            try:
                t = json.loads(line)
                q = t.get("question", "")
                a = t.get("answer", "")
                if a and not q.startswith("[admin"):
                    result.append(f"- P: {q[:80]} → R: {a[:100]}")
                elif a:
                    result.append(f"- {a[:150]}")
            except Exception:
                continue
        return "\n".join(result)

    def _assess_knowledge_level(self, soul: str, teachings: str, clinic: Dict) -> str:
        """Evaluar cuánto sabe Bublee del negocio."""
        total_knowledge = len(soul) + len(teachings)
        has_services = bool(clinic.get("services"))
        has_schedule = bool(clinic.get("schedule"))
        has_phone = bool(clinic.get("phone"))

        if total_knowledge > 2000 and has_services and has_schedule:
            return "ready"
        elif total_knowledge > 500 or has_services:
            return "learning"
        return "new"

    async def _handle_setup(self, chat_id: str, text: str, clinic: Dict) -> List[str]:
        from bublee import db
        setup_step = clinic.get("setup_step", "idle")
        setup_buffer = clinic.get("setup_buffer", {})
        if isinstance(setup_buffer, str):
            setup_buffer = json.loads(setup_buffer) if setup_buffer else {}

        step_names = ["name", "tagline", "services", "schedule", "phone", "pricing"]

        if setup_step == "idle":
            db.update_clinic(setup_step="name")
            return ["Hola! Soy Bublee, tu recepcionista nueva", "Cuéntame, cómo se llama tu negocio?"]

        if setup_step == "confirm_discovered":
            from bublee_utils import is_affirmative
            if is_affirmative(text):
                discovered = setup_buffer.get("discovered", {})
                db.update_clinic(name=discovered.get("name", setup_buffer.get("name")),
                                tagline=discovered.get("tagline", ""), services=discovered.get("services", []),
                                schedule=discovered.get("schedule", {}), phone=discovered.get("phone", ""),
                                setup_done=1, setup_step="idle", setup_buffer={})
                return [f"Listo, ya tengo la info de {discovered.get('name')}.", "Ahora cuéntame más — qué servicios son los más importantes?"]
            db.update_clinic(setup_step="tagline", setup_buffer=setup_buffer)
            return ["Ok vamos manual. Tienes algún slogan o frase de marca?"]

        if setup_step not in step_names:
            return ["Escribe /setup para empezar de nuevo."]
        idx = step_names.index(setup_step)

        if setup_step == "services":
            setup_buffer["services"] = [s.strip().title() for s in text.split(",") if s.strip()]
        else:
            setup_buffer[setup_step] = text.strip()

        if setup_step == "name":
            setup_buffer["name"] = text.strip()
            db.update_clinic(setup_step="services", setup_buffer=setup_buffer, name=text.strip())
            return [f"Anotado: {text.strip()}", "Qué servicios ofrecen? (ponlos separados por coma)"]

        if idx + 1 < len(step_names):
            next_step = step_names[idx + 1]
            prompts = {
                "tagline": "Tienes slogan?",
                "services": "Servicios (separados por coma)?",
                "schedule": "Horario de atención?",
                "phone": "Teléfono de contacto?",
                "pricing": "Rango de precios? (puede ser aproximado)",
            }
            db.update_clinic(setup_step=next_step, setup_buffer=setup_buffer)
            return [f"Perfecto, anotado", prompts.get(next_step, "Siguiente?")]

        db.update_clinic(name=setup_buffer.get("name"), tagline=setup_buffer.get("tagline"),
                        services=setup_buffer.get("services"), schedule=setup_buffer.get("schedule"),
                        phone=setup_buffer.get("phone"), pricing=setup_buffer.get("pricing"),
                        setup_done=1, setup_step="idle", setup_buffer={})
        return ["Listo! Ya tengo lo básico para arrancar", "Ahora cuéntame más libremente — precios, cosas que no deba decir, etc. Todo me sirve"]


class AuthEngine:
    """Autenticacion y activacion."""
    MAX_LOGIN_ATTEMPTS = 5

    def is_auth_message(self, chat_id: str, text: str) -> bool:
        from bublee import db
        from bublee_utils import is_activation_token, is_invite_token, is_negative
        t = text.strip(); t_low = t.lower()
        if ":" in t and "@" in t_low:
            parts = t.split(":")
            if len(parts) >= 2:
                potential_creds = parts[1].strip().split()
                if len(potential_creds) >= 2 and "@" in potential_creds[0]: return True
        session = db.get_auth_session(chat_id)
        if session and session.get("flow") in ("activate", "login", "invite", "register"):
            # BUG REAL encontrado: esta sesión nunca expiraba ni se limpiaba
            # si el usuario decía "no" en el confirm, o simplemente abandonaba
            # el flujo a medias. Resultado: ese chat_id quedaba atrapado
            # respondiendo "Cancelado" a TODO mensaje futuro — nunca volvía
            # a caer en demo ni en producción, ni aunque activaras DEMO_MODE,
            # porque este chequeo corre ANTES de llegar a esa parte del router.
            # Ahora: (a) sesiones de más de 15 min se consideran abandonadas
            # y se limpian solas, (b) un "no"/"cancelar" limpia al toque.
            updated_at = session.get("updated_at")
            if updated_at:
                try:
                    ts = str(updated_at).replace(" ", "T")
                    age_seconds = (datetime.utcnow() - datetime.fromisoformat(ts)).total_seconds()
                    if age_seconds > 900:
                        db.clear_auth_session(chat_id)
                        return False
                except Exception:
                    pass
            if is_negative(t) or t_low in ("cancelar", "cancela", "olvidalo", "olvídalo", "salir", "salte"):
                db.clear_auth_session(chat_id)
                return False
            return True
        if is_activation_token(t): return db.get_activation_token(t.upper()) is not None
        if is_invite_token(t): return db.get_auth_session(f"invite:{t.upper()}") is not None
        return False

    async def process(self, chat_id: str, text: str) -> List[str]:
        from bublee import db
        from bublee_utils import is_activation_token, is_invite_token
        t = text.strip()
        if ":" in t and "@" in t.lower():
            parts = t.split(":", 1); creds = parts[1].strip().split()
            if len(creds) >= 2 and "@" in creds[0]: return await self._handle_stealth_login(chat_id, creds[0].lower(), creds[1])
        if is_activation_token(t): return await self._start_activation(chat_id, t)
        if is_invite_token(t): return await self._start_invite_registration(chat_id, t)
        session = db.get_auth_session(chat_id)
        if session:
            flow = session.get("flow", "")
            if flow == "activate": return await self._handle_activation_flow(chat_id, t, session)
            if flow == "login": return await self._handle_login_flow(chat_id, t, session)
        return []

    async def _handle_stealth_login(self, chat_id: str, email: str, password: str) -> List[str]:
        from bublee import db
        from bublee_utils import verify_password, _parse_admin_ids
        admin = db.get_admin_by_email(email)
        if admin and verify_password(password, admin["password_hash"]):
            db.create_admin(chat_id=chat_id, email=admin["email"], password_hash=admin["password_hash"], name=admin["name"], role=admin["role"])
            clinic = db.get_clinic(); admin_ids = _parse_admin_ids(clinic.get("admin_chat_ids", []))
            if chat_id not in admin_ids: admin_ids.append(chat_id); db.update_clinic(admin_chat_ids=admin_ids)
            return [f"Hola {admin['name']}. Ya te reconozco."]
        return []

    async def _start_activation(self, chat_id: str, token_raw: str) -> List[str]:
        from bublee import db
        token = token_raw.strip().upper(); td = db.get_activation_token(token)
        if not td: return ["Token no válido."]
        db.set_auth_session(chat_id, flow="activate", step="name", temp_data={"token": token})
        return ["Código válido. Cómo te llamas?"]

    async def _handle_activation_flow(self, chat_id: str, text: str, session: Dict) -> List[str]:
        from bublee import db
        from bublee_utils import hash_password
        step, tmp = session["step"], session.get("temp_data", {})
        if step == "name":
            tmp["name"] = text.strip(); db.set_auth_session(chat_id, "activate", "email", tmp)
            return [f"Hola {text}. Tu email?"]
        if step == "email":
            tmp["email"] = text.strip().lower(); db.set_auth_session(chat_id, "activate", "password", tmp)
            return ["Elige una contraseña segura"]
        if step == "password":
            tmp["password_hash"] = hash_password(text.strip()); db.set_auth_session(chat_id, "activate", "confirm", tmp)
            return ["Confirmas? (si/no)"]
        if step == "confirm":
            from bublee_utils import is_affirmative
            if is_affirmative(text):
                db.create_admin(chat_id=chat_id, email=tmp["email"], password_hash=tmp["password_hash"], name=tmp["name"], role="owner")
                db.clear_auth_session(chat_id); return ["Listo, cuenta creada. Ahora cuéntame del negocio"]
            db.clear_auth_session(chat_id)
            return ["Cancelado. Si quieres activar de nuevo, mándame el token."]

    async def _handle_login_flow(self, chat_id: str, text: str, session: Dict) -> List[str]:
        from bublee import db
        from bublee_utils import verify_password, _parse_admin_ids
        step, tmp = session["step"], session.get("temp_data", {})
        if step == "email":
            email = text.strip().lower(); admin = db.get_admin_by_email(email)
            if not admin: return ["No encontré esa cuenta."]
            tmp["email"] = email; db.set_auth_session(chat_id, "login", "password", tmp)
            return ["Tu contraseña?"]
        if step == "password":
            email = tmp.get("email", ""); admin = db.get_admin_by_email(email)
            if admin and verify_password(text.strip(), admin["password_hash"]):
                db.create_admin(chat_id=chat_id, email=admin["email"], password_hash=admin["password_hash"], name=admin["name"], role=admin["role"])
                db.clear_auth_session(chat_id)
                clinic = db.get_clinic(); admin_ids = _parse_admin_ids(clinic.get("admin_chat_ids", []))
                if chat_id not in admin_ids: admin_ids.append(chat_id); db.update_clinic(admin_chat_ids=admin_ids)
                return [f"Bienvenido de nuevo, {admin['name']}."]
            return ["Contraseña incorrecta."]
        return []


class AdminLearningEngine:
    def __init__(self, database): self.db = database; self._cached_instructions = None
    def add_instruction(self, chat_id: str, text: str) -> str:
        self.db.add_admin_instruction(chat_id, text); self._cached_instructions = None
        return f"Anotado: '{text}'."
    def get_prompt_injection(self) -> str:
        ins = self.db.get_active_admin_instructions()
        if not ins: return ""
        return "\n## INSTRUCCIONES DEL DUEÑO:\n" + "\n".join([f"- {i}" for i in ins])
    def clear(self) -> str: self.db.clear_admin_instructions(); return "Instrucciones borradas."


class SimulationEngine:
    def __init__(self, bublee): self.bublee = bublee; self._active_simulations = {}
    def start(self, chat_id: str, scenario: str = "default") -> List[str]:
        self._active_simulations[chat_id] = {"ts": time.time()}
        return ["Dale, escríbeme como si fueras un paciente y te respondo en personaje"]
    def stop(self, chat_id: str) -> List[str]:
        self._active_simulations.pop(chat_id, None); return ["Listo, salí del modo simulación"]
    def is_simulating(self, chat_id: str) -> bool: return chat_id in self._active_simulations
    async def handle_step(self, chat_id: str, text: str) -> List[str]:
        if "salir" in text.lower() or "/salir" in text.lower(): return self.stop(chat_id)
        return await self.bublee.process_message(chat_id, text, is_simulation=True)


_STOPWORDS_ES = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del",
    "al", "a", "en", "con", "por", "para", "que", "y", "o", "es", "son",
    "esta", "estan", "tiene", "tienen", "hay", "se", "su", "sus", "mi",
    "mis", "yo", "tu", "usted", "me", "te", "le", "les", "lo", "como",
    "cual", "cuales", "donde", "cuando", "porque", "si", "no", "muy",
    "mas", "pero", "ese", "esa", "esto", "eso", "ustedes", "manejan",
}


def _text_overlap(a: str, b: str) -> float:
    """
    Similitud por palabras clave compartidas (sin stopwords), medida como
    contención (intersección / el más corto de los dos). Pensada para
    preguntas cortas fraseadas distinto.
    """
    def _keywords(s):
        s = (s or "").lower()
        return {w for w in re.findall(r"[a-záéíóúñ]+", s) if w not in _STOPWORDS_ES and len(w) >= 3}

    ka, kb = _keywords(a), _keywords(b)
    if not ka or not kb:
        return 0.0
    shared = ka & kb
    if not shared:
        return 0.0
    return len(shared) / min(len(ka), len(kb))


class SelfImprovementEngine:
    """
    Motor de auto-mejora.

    Antes: analyze_performance() devolvía {"ok": True} sin calcular nada,
    y apply_improvements() no existía. Pero SÍ estaban conectados de verdad:
      - runtime.py:_admin_show_metrics() → /metricas del admin
      - app.py: POST /self-improve y POST /self-improve/apply
    Es decir, la conexión ya existía — solo faltaba la implementación real,
    y por eso /metricas mostraba ceros y /self-improve/apply tiraba
    AttributeError apenas se llamaba.
    """

    def __init__(self, llm):
        self.llm = llm

    async def analyze_performance(self, hours: int = 24) -> Dict[str, Any]:
        """
        Métricas reales de las últimas `hours` horas, con las claves que
        _admin_show_metrics y /self-improve ya esperaban: total_conversations,
        avg_response_time_ms, avg_turns_per_conversation, conversion_rate,
        escalation_rate (estas dos últimas como fracción 0-1, el caller ya
        las multiplica x100 al mostrarlas).
        """
        from bublee import db
        empty = {
            "ok": False, "total_conversations": 0, "avg_response_time_ms": 0,
            "avg_turns_per_conversation": 0, "conversion_rate": 0, "escalation_rate": 0,
        }
        if not db:
            return empty

        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        try:
            with db._conn() as c:
                total_conversations = (c.execute(
                    "SELECT COUNT(DISTINCT chat_id) FROM conversations WHERE ts > ?", (since,)
                ).fetchone() or [0])[0] or 0

                total_turns = (c.execute(
                    "SELECT COUNT(*) FROM conversations WHERE ts > ? AND role='user'", (since,)
                ).fetchone() or [0])[0] or 0

                avg_latency = (c.execute(
                    "SELECT AVG(latency_ms) FROM conversations "
                    "WHERE ts > ? AND role='assistant' AND latency_ms > 0", (since,)
                ).fetchone() or [0])[0] or 0

                total_appointments = (c.execute(
                    "SELECT COUNT(*) FROM appointments WHERE created_at > ?", (since,)
                ).fetchone() or [0])[0] or 0

                state_rows = c.execute("SELECT state FROM conversation_states").fetchall()

            escalations, active_states = 0, 0
            for row in state_rows:
                raw = row[0] if isinstance(row, tuple) else row["state"]
                try:
                    st = json.loads(raw) if raw else {}
                except Exception:
                    continue
                active_states += 1
                if st.get("escalation_needed"):
                    escalations += 1

            return {
                "ok": True,
                "period_hours": hours,
                "total_conversations": total_conversations,
                "avg_response_time_ms": round(float(avg_latency), 1),
                "avg_turns_per_conversation": (
                    round(total_turns / total_conversations, 2) if total_conversations else 0.0
                ),
                "conversion_rate": (
                    round(total_appointments / total_conversations, 4) if total_conversations else 0.0
                ),
                "escalation_rate": (
                    round(escalations / active_states, 4) if active_states else 0.0
                ),
            }
        except Exception as e:
            log.error(f"[self_improvement] analyze_performance error: {e}")
            return empty

    async def apply_improvements(self, auto_apply: bool = False) -> List[Dict[str, Any]]:
        """
        Antes NO EXISTÍA — POST /self-improve/apply llamaba un método
        inexistente y tiraba AttributeError cada vez que se usaba.

        A propósito es conservador: identifica mejoras candidatas y las
        deja registradas en self_improvement_log (con db.log_improvement,
        auditable) para que decidas qué hacer con ellas. NO reescribe
        prompts, personalidad ni configuración en vivo de forma autónoma
        — ni siquiera con auto_apply=True. Esto corre en un sistema que
        atiende pacientes reales de una clínica; que un LLM decida y
        aplique cambios solo, sin que nadie lo revise, es un paso que
        merece que lo definamos juntos primero, no algo para meter por
        default.
        """
        from bublee import db
        analysis = await self.analyze_performance()
        applied: List[Dict[str, Any]] = []
        if not analysis.get("ok"):
            return applied

        candidates = []
        if analysis["total_conversations"] >= 5 and analysis["avg_response_time_ms"] > 6000:
            candidates.append({
                "type": "latency",
                "description": (
                    f"Tiempo de respuesta promedio {analysis['avg_response_time_ms']:.0f}ms "
                    f"en {analysis['total_conversations']} conversaciones — revisar cascada "
                    f"de proveedores o bajar a un modelo más rápido."
                ),
                "impact": 0.5,
            })
        if analysis["total_conversations"] >= 5 and analysis["escalation_rate"] > 0.3:
            candidates.append({
                "type": "escalation",
                "description": (
                    f"{analysis['escalation_rate']*100:.0f}% de conversaciones activas están "
                    f"marcadas para escalar a humano — revisa /aprendizaje para ver qué no "
                    f"sabe responder Bublee todavía."
                ),
                "impact": 0.7,
            })

        for cand in candidates:
            try:
                if db:
                    db.log_improvement(
                        improvement_type=cand["type"],
                        description=cand["description"],
                        before=analysis,
                        after={},
                        impact=cand["impact"],
                        applied=False,
                    )
                applied.append({**cand, "applied": False})
            except Exception as e:
                log.warning(f"[self_improvement] no pude loguear mejora: {e}")

        return applied

    async def analyze_knowledge_gaps(self, days: int = 7) -> Dict[str, Any]:
        """
        Lee los knowledge_gaps/*.jsonl que bublee_commands.py ya registra
        (los mismos que muestra /gaps en crudo), agrupa patrones repetidos,
        y le pide al LLM un resumen accionable. Conectado a /aprendizaje.
        """
        gaps_dir = Path("knowledge_gaps")
        if not gaps_dir.exists():
            return {"ok": True, "gap_count": 0, "summary": "Sin knowledge gaps registrados todavía."}

        cutoff = datetime.now() - timedelta(days=days)
        all_gaps: List[Dict[str, Any]] = []
        for f in sorted(gaps_dir.glob("*.jsonl")):
            try:
                file_date = datetime.strptime(f.stem, "%Y-%m-%d")
                if file_date < cutoff:
                    continue
            except ValueError:
                pass
            try:
                for line in f.read_text().splitlines():
                    if not line.strip():
                        continue
                    try:
                        all_gaps.append(json.loads(line))
                    except Exception:
                        continue
            except Exception:
                continue

        if not all_gaps:
            return {"ok": True, "gap_count": 0, "summary": f"Sin gaps en los últimos {days} días."}

        buckets: List[Dict[str, Any]] = []
        for g in all_gaps:
            msg = str(g.get("user_msg", ""))[:200]
            placed = False
            for b in buckets:
                if _text_overlap(msg, b["sample"]) > 0.4:
                    b["count"] += 1
                    placed = True
                    break
            if not placed:
                buckets.append({"sample": msg, "count": 1})
        buckets.sort(key=lambda b: -b["count"])
        top = buckets[:8]

        if not self.llm:
            lines = [f"- ({b['count']}x) {b['sample']}" for b in top]
            return {
                "ok": True, "gap_count": len(all_gaps), "patterns": top,
                "summary": "Patrones repetidos (sin resumen LLM, llm no disponible):\n" + "\n".join(lines),
            }

        listado = "\n".join(f"- ({b['count']}x) {b['sample']}" for b in top)
        sys_p = (
            "Eres un analista que revisa preguntas que un agente de WhatsApp de una "
            "clínica NO pudo responder bien (knowledge gaps). Te doy la lista con "
            "cuántas veces se repitió cada patrón. Devuelve en español, 3-5 bullets "
            "muy concretos, qué información debería darte el dueño del negocio para "
            "cerrar esos gaps. Sin relleno, sin saludos, directo al punto."
        )
        try:
            resp, _ = await self.llm.complete(
                [{"role": "system", "content": sys_p}, {"role": "user", "content": listado}],
                model_tier="fast", temperature=0.4, max_tokens=500, use_cache=False,
            )
        except Exception as e:
            log.warning(f"[self_improvement] analyze_knowledge_gaps LLM error: {e}")
            resp = "No se pudo generar el resumen LLM en este momento."

        return {"ok": True, "gap_count": len(all_gaps), "patterns": top, "summary": resp}


class TaskManager:
    def __init__(self): self._tasks = {}
    def add_task(self, chat_id: str, kind: str, data: Dict, delay: int = 0): return secrets.token_hex(4)
