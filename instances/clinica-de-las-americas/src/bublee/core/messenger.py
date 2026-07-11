"""Message sending, buffering, typing simulation, and audio transcription."""
from __future__ import annotations
# TODO: These methods were part of BubleeUltra class.
# They reference self._pending_buffers, self._demo_sessions, Config, httpx, etc.
# To fully decouple: inject dependencies via constructor or pass as params.

def _calc_smart_wait(self, chat_id: str, text: str) -> float:
    """
    Calcula tiempo de espera inteligente. No es random fijo.
    Analiza el contexto real para decidir cuanto esperar.

    Logica:
      - Setup flow (respondiendo preguntas directas) (3-8s)
      - Mensaje muy corto (si/no/ok/dato puntual)    (3-10s)
      - Respuesta corta (1 dato, una oracion)        (5-15s)
      - Mensaje normal (1-2 oraciones)               (9-22s)
      - Mensaje largo (parrafo, varias preguntas)    (16-40s)
      - Si Bublee acaba de preguntar algo (-40%) del tiempo base
    
    Maximo absoluto: 55s
    """
    text = text.strip()
    chars = len(text)
    
    # ── Leer contexto de la BD ─────────────────────────────────────────────
    try:
        clinic = db.get_clinic()
        is_setup = not clinic.get("setup_done")
        history = db.get_history(chat_id, limit=3)
        
        # Demo mode: siempre rápido para no perder al prospecto
        if Config.DEMO_MODE:
            if chars <= 12:
                return round(random.uniform(2.0, 4.5), 1)
            elif chars <= 60:
                return round(random.uniform(3.0, 7.0), 1)
            else:
                return round(random.uniform(5.0, 10.0), 1)

        # Setup: siempre rapido — el usuario responde preguntas directas cortas
        if is_setup:
            if chars < 60:
                return round(random.uniform(3.0, 7.0), 1)
            return round(random.uniform(5.0, 11.0), 1)
        
        if not history and _is_greeting_only(text):
            return float(Config.GREETING_ONLY_IDLE_SECONDS)

        # Ver si Bublee acaba de hacer una pregunta al usuario
        last_bot = next(
            (m for m in reversed(history) if m["role"] == "assistant"), None
        )
        bot_asked = False
        if last_bot:
            bot_content = last_bot.get("content", "").lower()
            # Pregunta directa: tiene "?" o palabras tipicas de solicitud de dato
            bot_asked = "?" in bot_content or any(
                w in bot_content for w in [
                    "cual", "como", "cuando", "tienes", "nombre", "telefono",
                    "servicio", "fecha", "hora", "confirmas", "dime"
                ]
            )
    except Exception:
        is_setup = False
        bot_asked = False
        history = []
    
    # ── Rango base segun longitud del texto ───────────────────────────────
    # Muy corto: "si", "no", "ok", "dale", numero, nombre
    if chars <= 12:
        lo, hi = 3.0, 9.0
    # Corto: dato simple, respuesta directa
    elif chars <= 40:
        lo, hi = 5.0, 14.0
    # Oracion normal
    elif chars <= 100:
        lo, hi = 9.0, 22.0
    # Parrafo
    elif chars <= 220:
        lo, hi = 16.0, 35.0
    # Mensaje largo con varias preguntas/contexto
    else:
        lo, hi = 22.0, 50.0
    
    # Si Bublee pregunto algo y el usuario responde -> ir mas rapido
    if bot_asked:
        lo = max(3.0, lo * 0.55)
        hi = max(8.0, hi * 0.60)
    
    # Nunca superar 55s
    hi = min(hi, 55.0)
    
    return round(random.uniform(lo, hi), 1)

async def enqueue_message(
    self,
    chat_id: str,
    text: str,
    urgent: bool = False,
    message_id: str = "",
    route: Optional[Dict[str, Any]] = None,
    attachments: Optional[List[Dict[str, Any]]] = None,
):
    """Encola mensaje con buffer inteligente basado en contexto real."""
    attachments = attachments or []

    # ── Commands: process inline (no buffer needed for slash commands)
    if text.strip().startswith("/"):
        try:
            from bublee_commands import get_command_handler
            instance_id = getattr(self, "_instance_id", "default")
            clinic = db.get_clinic()
            admin_ids = _parse_admin_ids(clinic.get("admin_chat_ids", []))
            is_admin = (chat_id in admin_ids or db.get_admin(chat_id) is not None)
            cmd_handler = get_command_handler(instance_id)
            result = await cmd_handler.handle(chat_id, text.strip(), is_admin=is_admin, clinic=clinic, db=db)
            if result:
                await self._send_bubbles(chat_id, result, message_id="", route=route)
                return
        except Exception as e:
            log.warning(f"[command] error: {e}")
        # If command not recognized, let it pass to process_message as normal text
        pass

    # ── MODO SIMULACIÓN ──────────────────────────────────────────────────
    if self.simulator and self.simulator.is_simulating(chat_id):
        bubbles = await self.simulator.handle_step(chat_id, text)
        if bubbles:
            await self._send_bubbles(chat_id, bubbles, message_id=message_id, route=route)
        return

    route = self._resolve_route(chat_id, route)
    platform = _route_platform(route)
    key = _buffer_key(chat_id, route)
    is_wa = platform == "whatsapp" and bool(Config.WHATSAPP_BRIDGE_URL)

    # ── Fire /read con delay natural — tarea completamente independiente ──────
    # Separada del buffer para que nunca interfiera con el flush.
    # read_delay simula el tiempo que tarda una persona en leer antes de marcar azul.
    if is_wa and message_id:
        chars = len(text.strip())
        is_demo = Config.DEMO_MODE
        if   chars <= 8:   rd_lo, rd_hi = 0.8, 2.0
        elif chars <= 30:  rd_lo, rd_hi = 1.2, 3.5
        elif chars <= 80:  rd_lo, rd_hi = 2.5, 6.0
        elif chars <= 200: rd_lo, rd_hi = 4.0, 10.0
        else:              rd_lo, rd_hi = 6.0, 15.0
        if is_demo:
            rd_lo *= 0.35; rd_hi *= 0.35
        read_delay = round(random.uniform(rd_lo, rd_hi), 1)

        async def _fire_read(mid: str, delay: float):
            await asyncio.sleep(delay)
            try:
                async with httpx.AsyncClient(timeout=4.0) as hx:
                    await hx.post(
                        f"{Config.WHATSAPP_BRIDGE_URL}/read",
                        json={"to": chat_id, "messageId": mid}
                    )
            except Exception:
                pass

        asyncio.create_task(_fire_read(message_id, read_delay))

    if urgent:
        log.info(f"Urgente [{chat_id[:8]}]: bypass buffer")
        if key in self._pending_buffers:
            task = self._pending_buffers[key].get("task")
            if task and not task.done():
                task.cancel()
            prev_entry = self._pending_buffers.pop(key, {})
            prev = " ".join(prev_entry.get("messages", []))
            attachments = prev_entry.get("attachments", []) + attachments
            combined = (prev + " " + text).strip() if prev else text
        else:
            combined = text
        bubbles = await self.process_message(chat_id, combined, attachments=attachments, route=route)
        await self._send_bubbles(chat_id, bubbles, message_id="", route=route)  # read ya disparado arriba
        return

    # Buffer normal — lógica original intacta
    if key in self._pending_buffers:
        task = self._pending_buffers[key].get("task")
        if task and not task.done():
            task.cancel()
        if text:
            self._pending_buffers[key]["messages"].append(text)
        self._pending_buffers[key]["attachments"].extend(attachments)
    else:
        self._pending_buffers[key] = {
            "chat_id": chat_id,
            "messages": [text] if text else [],
            "attachments": list(attachments),
            "task": None,
            "message_id": message_id,
            "route": route,
        }

    wait_seed = text or " ".join(att.get("filename", "") for att in attachments) or "archivo"
    wait = self._calc_smart_wait(chat_id, wait_seed)

    async def delayed():
        await asyncio.sleep(wait)
        await self._flush_buffer(key)

    task = asyncio.create_task(delayed())
    self._pending_buffers[key]["task"] = task

    n = len(self._pending_buffers[key]["messages"])
    log.info(f"buffer [{platform}:{chat_id[:8]}] msg #{n}, flush en {wait:.1f}s")

async def _flush_buffer(self, key: str):
    """Vacía el buffer y procesa mensajes."""
    entry = self._pending_buffers.pop(key, None)
    if not entry:
        return

    chat_id = entry.get("chat_id", "")
    route = entry.get("route") or self._resolve_route(chat_id)
    combined   = " ".join(entry.get("messages", []))
    message_id = entry.get("message_id", "")
    attachments = entry.get("attachments", [])
    log.info(f"flush [{key}] {len(entry.get('messages', []))} msgs")

    try:
        bubbles = await self.process_message(chat_id, combined, attachments=attachments, route=route)
        if bubbles:
            await self._send_bubbles(chat_id, bubbles, message_id=message_id, route=route)
    except Exception as e:
        log.error(f"Flush error for {chat_id}: {e}", exc_info=True)
        # ponytail: mensaje amigable al usuario cuando el LLM falla
        await self._send_message(chat_id, "Lo siento, tuve un error técnico inesperado. ¿Podrías repetir?", route=route)

async def _send_bubbles(
    self,
    chat_id: str,
    bubbles: List[str],
    message_id: str = "",
    route: Optional[Dict[str, Any]] = None,
):
    """Envía burbujas con typing proporcional y pausas naturales."""
    route = self._resolve_route(chat_id, route)
    platform = _route_platform(route)
    is_wa = platform in ("whatsapp", "evolution")

    # Demo voice: send first bubble as audio for wow factor
    if Config.DEMO_MODE and is_wa and bubbles and os.getenv("ELEVENLABS_API_KEY"):
        try:
            from bublee_demo_voice import generate_demo_audio, should_send_voice_in_demo
            history_len = len(db.get_history(chat_id)) if db else 0
            if should_send_voice_in_demo(bubbles[0], history_len // 2, False):
                audio_path = await generate_demo_audio(bubbles[0])
                if audio_path:
                    await self._send_audio(chat_id, audio_path, route=route)
                    os.unlink(audio_path)
                    # Still send text after audio for accessibility
                    await asyncio.sleep(1.0)
        except Exception as e:
            log.debug(f"[demo_voice] skipped: {e}")

    for i, bubble in enumerate(bubbles):
        if not bubble.strip():
            continue

        # Typing proporcional al bubble + read receipt en primera burbuja
        mid = message_id if i == 0 else ""
        await self._typing_action(chat_id, text=bubble, message_id=mid, route=route)

        # Duración del typing que se fijó en el bridge (misma fórmula que _typing_action)
        # para que pause >= typing_duration y nunca lleguemos a /send antes de que expire
        chars = len(bubble)
        typing_duration_s = max(1.5, min(chars * 0.05, 8.0))  # same as max(1500,min(chars*50,8000))/1000
        typing_time = chars / 38  # velocidad de escritura humana ~38 chars/s

        pause = max(
            typing_duration_s + 0.15,   # siempre > duración del timer — margen 150ms
            Config.BUBBLE_PAUSE_MIN,
            min(typing_time + random.uniform(0.1, 0.5), Config.BUBBLE_PAUSE_MAX + 0.8)
        )

        await asyncio.sleep(pause)
        await self._send_message(chat_id, bubble, route=route)

        if i < len(bubbles) - 1:
            # Pausa inter-burbuja más humana — evita que WA trate las ráfagas como spam
            inter_pause = random.uniform(1.4, 2.8) if is_wa else random.uniform(0.8, 1.8)
            await asyncio.sleep(inter_pause)

    # No forzamos offline después de responder.
    # El bridge mantiene presencia humana y expira solo tras el timeout configurado.

async def _typing_action(
    self,
    chat_id: str,
    text: str = "",
    message_id: str = "",
    route: Optional[Dict[str, Any]] = None,
):
    """
    Indica 'escribiendo...' proporcional al texto que va a enviar.
    En WhatsApp Bridge también marca como leído si hay message_id.
    """
    try:
        route = self._resolve_route(chat_id, route)
        platform = _route_platform(route)
        # Duración proporcional: ~50ms por char, entre 1.5s y 8s
        chars    = len(text) if text else 60
        duration = max(1500, min(int(chars * 50), 8000))

        if platform == "telegram":
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    f"https://api.telegram.org/bot{Config.TELEGRAM_TOKEN}/sendChatAction",
                    json={"chat_id": chat_id, "action": "typing"}
                )

        elif platform == "whatsapp_cloud":
            pass  # no soportado en API v17+

        elif platform == "evolution":
            if Config.EVOLUTION_URL and Config.EVOLUTION_API_KEY:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    await client.post(
                        f"{Config.EVOLUTION_URL}/chat/sendPresence/{Config.EVOLUTION_INSTANCE}",
                        headers={"apikey": Config.EVOLUTION_API_KEY},
                        json={"number": chat_id, "presence": "composing", "delay": duration}
                    )

        elif platform == "whatsapp":
            if Config.WHATSAPP_BRIDGE_URL:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    # Aparecer online PRIMERO — sin esto WhatsApp no muestra "escribiendo"
                    # y el mensaje llega con un solo chulo gris
                    try:
                        await client.post(
                            f"{Config.WHATSAPP_BRIDGE_URL}/presence",
                            json={"status": "available", "timeout": 1800000},
                            timeout=3.0
                        )
                    except Exception:
                        pass
                    # Typing proporcional al mensaje
                    await client.post(
                        f"{Config.WHATSAPP_BRIDGE_URL}/typing",
                        json={"to": chat_id, "duration": duration}
                    )
    except Exception:
        pass


def sanitize_outgoing(self, text: Optional[str]) -> Optional[str]:
    """
    Sanitiza TODO mensaje saliente antes de enviarlo.
    Previene JSON bleed, debug messages y respuestas vacías.
    """
    if not text:
        return None
    t = text.strip()
    if not t:
        return None
    if t.startswith('{') or t.startswith('['):
        log.error(f"[sanitize] JSON bleed blocked: {t[:80]}")
        return None
    if '|||' in t:
        t = t.split('|||')[0].strip()
    internal_phrases = [
        "todavía no tengo este chat enlazado",
        "ya recibí tu mensaje",
        "no tengo este chat",
        "[error",
        "[internal",
        "{",
    ]
    if any(phrase in t.lower() for phrase in internal_phrases):
        log.error(f"[sanitize] internal debug message blocked: {t[:80]}")
        return None
    return t if t else None


async def _send_audio(self, chat_id: str, audio_path: str, route: Optional[Dict[str, Any]] = None):
    """Send audio file as voice note via WhatsApp bridge."""
    route = self._resolve_route(chat_id, route)
    try:
        import base64
        with open(audio_path, "rb") as f:
            audio_b64 = base64.b64encode(f.read()).decode()
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(
                f"{Config.WHATSAPP_BRIDGE_URL}/send-audio",
                json={"to": chat_id, "audio": audio_b64, "ptt": True},
            )
            if r.status_code in (200, 201, 202):
                log.info(f"[voice] audio sent to {chat_id[:10]}...")
            else:
                log.warning(f"[voice] send failed: {r.status_code}")
    except Exception as e:
        log.debug(f"[voice] send_audio error: {e}")

async def _send_message(self, chat_id: str, text: str, route: Optional[Dict[str, Any]] = None):
    """
    Envia mensaje al paciente/admin segun la plataforma configurada.
    Plataformas soportadas: telegram | whatsapp_cloud | evolution | whatsapp
    """
    text = self.sanitize_outgoing(text)
    if not text:
        return
    if chat_id in self._emoji_chats_off:
        text = self._strip_emojis(text)
    text = text.replace('\u00bf', '').replace('\u00a1', '').strip()  # ¿ ¡
    if not text:
        return

    route = self._resolve_route(chat_id, route)
    platform = _route_platform(route)

    try:
        if platform == "telegram":
            async with httpx.AsyncClient(timeout=15.0) as client:
                await client.post(
                    f"https://api.telegram.org/bot{Config.TELEGRAM_TOKEN}/sendMessage",
                    json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
                )

        elif platform == "whatsapp_cloud":
            # Meta WhatsApp Cloud API — gratuita hasta 1000 conversaciones/mes
            if not Config.WA_ACCESS_TOKEN or not Config.WA_PHONE_ID:
                log.error("[wa_cloud] WA_ACCESS_TOKEN o WA_PHONE_ID no configurados")
                return
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.post(
                    f"https://graph.facebook.com/v19.0/{Config.WA_PHONE_ID}/messages",
                    headers={
                        "Authorization": f"Bearer {Config.WA_ACCESS_TOKEN}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "messaging_product": "whatsapp",
                        "recipient_type": "individual",
                        "to": chat_id,          # numero internacional sin +: 573001234567
                        "type": "text",
                        "text": {"body": text, "preview_url": False}
                    }
                )
                if r.status_code >= 400:
                    log.error(f"[wa_cloud] send error {r.status_code}: {r.text[:200]}")

        elif platform == "evolution":
            # Evolution API — auto-hospedada, conecta WhatsApp Web
            if not Config.EVOLUTION_URL or not Config.EVOLUTION_API_KEY:
                log.error("[evolution] EVOLUTION_URL o EVOLUTION_API_KEY no configurados")
                return
            # Delay proporcional al texto — simula tipeo humano y evita que
            # WhatsApp solo entregue 1 chulo (el delay 0 activa el rate-limit)
            _chars = len(text)
            _human_delay = min(max(int(_chars * 40), 800), 4000)  # 40ms/char, 800ms–4s
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.post(
                    f"{Config.EVOLUTION_URL}/message/sendText/{Config.EVOLUTION_INSTANCE}",
                    headers={
                        "apikey": Config.EVOLUTION_API_KEY,
                        "Content-Type": "application/json",
                    },
                    json={
                        "number": chat_id,     # 573001234567 o 573001234567@s.whatsapp.net
                        "text": text,
                        "delay": _human_delay
                    }
                )

        elif platform == "whatsapp":
            # Custom WhatsApp Bridge (Baileys)
            if not Config.WHATSAPP_BRIDGE_URL:
                log.error("[wa_bridge] WHATSAPP_BRIDGE_URL no configurado")
                return
            # Retry 1 vez: si el bridge está ocupado o hay un hipo de red
            _last_err = None
            for _attempt in range(2):
                try:
                    async with httpx.AsyncClient(timeout=20.0) as client:
                        r = await client.post(
                            f"{Config.WHATSAPP_BRIDGE_URL}/send",
                            json={"to": chat_id, "message": text}
                        )
                    if r.status_code < 400:
                        log.info(f"[wa_bridge] enviado OK ({r.status_code}) intento={_attempt+1}")
                        break
                    else:
                        _last_err = f"HTTP {r.status_code}: {r.text[:200]}"
                        log.error(f"[wa_bridge] send error intento={_attempt+1} — {_last_err}")
                        if _attempt == 0:
                            await asyncio.sleep(2.0)  # esperar antes del retry
                except Exception as _e:
                    _last_err = str(_e)
                    log.error(f"[wa_bridge] send exception intento={_attempt+1}: {_last_err}")
                    if _attempt == 0:
                        await asyncio.sleep(2.0)
            else:
                log.error(f"[wa_bridge] FALLÓ después de 2 intentos: {_last_err}")

        else:
            log.error(f"Plataforma desconocida: {platform!r}")

    except Exception as e:
        log.error(f"[{platform}] send_message error: {e}")


def _strip_emojis(self, text: str) -> str:
    """Elimina todos los emojis."""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002500-\U00002BEF"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FA6F"
        "\U0001FA70-\U0001FAFF"
        "\u2600-\u26FF"
        "\u2700-\u27BF"
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub("", text).strip()

async def transcribe_audio(self, file_id: str, platform: str = "telegram",
                           wa_media_id: str = None) -> str:
    """Delega transcripción a AudioHandler si está disponible."""
    if _AUDIO_HANDLER_AVAILABLE and hasattr(self, "_audio_handler"):
        return await self._audio_handler.transcribe_audio(file_id, platform, wa_media_id)
    return "[no pude escuchar, puedes escribirlo?]"

def is_urgent(self, text: str) -> bool:
    """Detecta si el mensaje es urgente."""
    analysis = self.analyzer.analyze(text)
    return analysis.urgency in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH]

def _analysis_to_dict(self, analysis: MessageAnalysis) -> Dict:
    """Convierte MessageAnalysis a dict JSON-serializable (enums -> strings)."""
    try:
        return {
            "intent": analysis.intent.name,
            "intent_confidence": analysis.intent_confidence,
            "secondary_intents": [(i.name, s) for i, s in (analysis.secondary_intents or [])],
            "sentiment": analysis.sentiment.name,
            "sentiment_score": analysis.sentiment_score,
            "urgency": analysis.urgency.name,
            "emotional_state": analysis.emotional_state,
            "is_question": analysis.is_question,
            "requires_action": analysis.requires_action,
            "requires_search": analysis.requires_search,
            "entities": analysis.entities,
            "keywords": analysis.keywords,
            "language":       analysis.language,
            "closing_score":  getattr(analysis, "closing_score", 0.0),
            "lead_temperature": getattr(analysis, "lead_temperature", "cold"),
        }
    except Exception:
        return {}

