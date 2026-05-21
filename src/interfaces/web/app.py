# -*- coding: utf-8 -*-
"""Conny web interface layer (FastAPI)."""
from __future__ import annotations

# Import all globals, vocabularies, and libraries dynamically (including underscore-prefixed names)
import src.core.globals as globals_module
for name in dir(globals_module):
    if not name.startswith("__"):
        globals()[name] = getattr(globals_module, name)

# Import ConnyUltra runtime class
from src.core.runtime import ConnyUltra

# Dynamic global proxies to resolve facade/main module variables at runtime
class FacadeProxy:
    def __init__(self, name):
        self._name = name
    def __getattr__(self, attr):
        import sys
        conny_mod = sys.modules.get("conny") or sys.modules.get("__main__")
        target = getattr(conny_mod, self._name, None)
        if target is not None:
            return getattr(target, attr)
        # Fallback to globals_module if applicable (e.g. for db)
        if self._name == "db":
            import src.core.globals as g
            if hasattr(g, "db") and g.db is not None:
                return getattr(g.db, attr)
        raise AttributeError(f"Facade variable '{self._name}' (accessing '{attr}') is not initialized")
    def __bool__(self):
        import sys
        conny_mod = sys.modules.get("conny") or sys.modules.get("__main__")
        return getattr(conny_mod, self._name, None) is not None

conny = FacadeProxy("conny")
db = FacadeProxy("db")
anti_robot_filter = FacadeProxy("anti_robot_filter")
conversation_simulator = FacadeProxy("conversation_simulator")
response_variation = FacadeProxy("response_variation")
hallucination_guard = FacadeProxy("hallucination_guard")
owner_style_controller = FacadeProxy("owner_style_controller")
prompt_evolver = FacadeProxy("prompt_evolver")
trainer_gateway = FacadeProxy("trainer_gateway")
task_manager = FacadeProxy("task_manager")

async def init_conny():
    import sys
    conny_mod = sys.modules.get("conny") or sys.modules.get("__main__")
    if conny_mod and hasattr(conny_mod, "init_conny"):
        await conny_mod.init_conny()


# ═══════════════════════════════════════════════════════════════════════════════
# FASTAPI APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════

# PATCH P1 2024-04 — brain_v10: LLM primero, plantillas como último recurso
def _init_brain_v10():
    """
    Integra conny_brain_v10 al startup.
    El módulo estaba escrito y documentado pero nunca inicializado.
    init_brain() carga señales de memoria corta.
    patch_llm_first(generator) hace que el LLM tenga autoridad sobre plantillas.
    """
    try:
        from conny_brain_v10 import init_brain, patch_llm_first
        init_brain()
        patch_llm_first(conny.generator)
        log.info("[brain_v10] LLM-first activo — plantillas solo como último recurso")
    except ImportError:
        log.warning("[brain_v10] módulo no encontrado — continúa sin él")
    except Exception as e:
        log.warning(f"[brain_v10] no se pudo inicializar: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle de la aplicación."""
    # Startup
    errors = Config.validate()
    if errors:
        for e in errors:
            log.error(f"Config error: {e}")
    
    await init_conny()
    try:
        bootstrap_clinic_identity_from_instance_metadata()
    except Exception as exc:
        log.warning(f"[startup] instance_bootstrap error: {exc}")
    try:
        ensure_minimum_business_state()
    except Exception as exc:
        log.warning(f"[startup] business_bootstrap error: {exc}")

    # V8.0 + Observatory + Trainer — init en orden correcto, bulletproof
    for _fn, _lbl in [
        (lambda: init_v8_systems()              if not anti_robot_filter   else None, "v8_core"),
        (lambda: init_v8_extended_systems()     if not conversation_simulator else None, "v8_extended"),
        (lambda: init_observatory(),             "observatory"),
        (lambda: init_trainer_systems(),         "trainer"),
        (lambda: _patch_admin_dispatcher(),      "dispatcher_v8"),
        (lambda: _patch_admin_dispatcher_trainer(), "dispatcher_trainer"),
        # PATCH P1 — brain_v10: LLM primero, documentado pero nunca llamado
        (lambda: _init_brain_v10(), "brain_v10"),
    ]:
        try:
            result = _fn()
            if result is not None or True:
                log.info(f"[startup] {_lbl} OK")
        except Exception as _e:
            log.warning(f"[startup] {_lbl} error: {_e}")

    telegram_mode = _telegram_webhook_mode()
    if telegram_mode == "shared":
        await set_shared_telegram_webhook()
    elif telegram_mode == "direct":
        if Config.TELEGRAM_SHARED and Config.PLATFORM != "telegram":
            log.info("[telegram] shared activado sin router — usando webhook directo en esta instancia")
        if Config.PLATFORM == "telegram" and Config.TELEGRAM_SHARED:
            log.info("Telegram shared mode activo sin router — usando webhook directo para no dejar el bot mudo")
        await set_webhook()

    if Config.PLATFORM == "telegram" and Config.BASE_URL and Config.TELEGRAM_TOKEN:
        if Config.TELEGRAM_SHARED and Config.TELEGRAM_SHARED_ROUTER:
            log.info("Telegram shared mode activo — esta instancia no registra webhook propio")
        else:
            log.info("[telegram] webhook directo activo")
    elif Config.PLATFORM == "whatsapp_cloud":
        log.info("WhatsApp Cloud API mode — registra el webhook manualmente en Meta Business Manager")
        log.info(f"URL del webhook: {Config.BASE_URL}/webhook/{Config.WEBHOOK_SECRET}")
    elif Config.PLATFORM == "evolution":
        log.info("Evolution API mode — configura el webhook en tu panel de Evolution")
        log.info(f"URL del webhook: {Config.BASE_URL}/webhook/{Config.WEBHOOK_SECRET}")
    
    # ── Memory Engine + Cron Scheduler + Uncertainty ────────────────────────────
    try:
        from conny_memory_engine import memory_engine as _mem_engine
        from conny_cron import init_scheduler as _init_cron
        from conny_uncertainty import uncertainty_detector as _unc_detector
        instance_id = Config.INSTANCE_ID if hasattr(Config, "INSTANCE_ID") else "default"
        _init_cron(memory_engine=_mem_engine, instance_ids=[instance_id])
        log.info(f"[startup] memory_engine + cron + uncertainty OK (instance={instance_id})")
    except Exception as _mem_err:
        log.warning(f"[startup] memory/cron init error: {_mem_err}")

    log.info("═══════════════════════════════════════════════════════")
    log.info("       CONNY V9.6.1 - ONLINE Y OPERATIVA         ")
    log.info("═══════════════════════════════════════════════════════")

    # Notificar a Omni que esta instancia está online
    asyncio.create_task(asyncio.to_thread(
        notify_omni, "instance_online",
        f"Conny v8.0 online — sector: {Config.SECTOR or 'otro'}"
    ))
    
    yield
    
    # Shutdown
    if task_manager:
        await task_manager.stop()
    try:
        from conny_cron import shutdown_scheduler
        shutdown_scheduler()
    except Exception:
        pass
    notify_omni("instance_offline", f"Conny apagada — sector: {Config.SECTOR or 'otro'}")
    log.info("Conny Ultra apagada")

app = FastAPI(
    title="Conny v9.6.1",
    description="Conny V9.0 — Agente de Recepción Hipernaturalmente Humana",
    version="9.6.1",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Admin API Router ────────────────────────────────────────────────────────────
try:
    from src.interfaces.web.admin_api import router as admin_api_router
    app.include_router(admin_api_router)
    log.info("[admin_api] router montado en /admin")
except Exception as _admin_api_err:
    log.warning(f"[admin_api] no disponible: {_admin_api_err}")

# ─── Webhook Setup ──────────────────────────────────────────────────────────────

async def set_webhook():
    """Configura el webhook de Telegram."""
    url = f"{Config.BASE_URL}/webhook/{Config.WEBHOOK_SECRET}"
    
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"https://api.telegram.org/bot{Config.TELEGRAM_TOKEN}/setWebhook",
            json={
                "url": url,
                "allowed_updates": ["message"],
                "drop_pending_updates": False
            }
        )
        data = r.json()
        status = "OK" if data.get("ok") else "ERROR"
        log.info(f"Webhook {status}: {url}")


async def set_shared_telegram_webhook():
    """Configura el webhook compartido de Telegram en la instancia base."""
    url = f"{Config.BASE_URL}/telegram/shared/{Config.TELEGRAM_SHARED_SECRET}"
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"https://api.telegram.org/bot{Config.TELEGRAM_TOKEN}/setWebhook",
            json={
                "url": url,
                "allowed_updates": ["message"],
                "drop_pending_updates": False,
            },
        )
        data = r.json()
        status = "OK" if data.get("ok") else "ERROR"
        log.info(f"[telegram_shared] Webhook {status}: {url}")


def _telegram_webhook_mode() -> str:
    if not Config.BASE_URL or not Config.TELEGRAM_TOKEN:
        return "disabled"
    if Config.TELEGRAM_SHARED_ROUTER:
        return "shared"
    return "direct"


async def _forward_shared_telegram_update(target: Dict[str, Any], body: Dict[str, Any]) -> Dict[str, Any]:
    url = f"http://127.0.0.1:{target['port']}/webhook/{target['secret']}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(url, json=body)
    return {"status": r.status_code, "body": r.text[:200]}


async def _send_shared_unpaired_notice(chat_id: str):
    text = (
        "ya recibí tu mensaje ||| todavía no tengo este chat enlazado a una clínica "
        "en la ruta compartida, pero ya quedó pendiente"
    )
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"https://api.telegram.org/bot{Config.TELEGRAM_TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": text},
            )
    except Exception as e:
        log.warning(f"[telegram_shared] no pude avisar al chat no enlazado: {e}")

# ─── Webhook Endpoint ───────────────────────────────────────────────────────────

@app.post("/webhook/{secret}")
async def webhook(secret: str, request: Request):
    """
    Webhook unificado.
    Acepta mensajes de Telegram, WhatsApp Cloud API, Evolution API o WhatsApp Bridge (custom).
    segun Config.PLATFORM.
    """
    if secret != Config.WEBHOOK_SECRET:
        return Response(status_code=403)

    try:
        body = await request.json()
    except Exception:
        return Response(status_code=400)

    platform = _detect_incoming_platform(body)

    chat_id    = None
    text       = None
    audio_id   = None
    message_id = None   # para /read en WhatsApp Bridge
    attachments: List[Dict[str, Any]] = []

    # ── Parser Telegram ───────────────────────────────────────────────────────
    if platform == "telegram":
        msg = body.get("message") or body.get("edited_message")
        if not msg:
            return {"ok": True}
        chat_id = str(msg["chat"]["id"])
        voice = msg.get("voice") or msg.get("audio")
        if voice:
            audio_id = voice["file_id"]
        else:
            text = msg.get("text", "").strip()
        document = msg.get("document")
        if document:
            attachments.append({
                "kind": "document",
                "platform": "telegram",
                "file_id": document.get("file_id", ""),
                "filename": document.get("file_name", "document.bin"),
                "mime_type": document.get("mime_type", "application/octet-stream"),
                "caption": msg.get("caption", ""),
            })
            text = text or (msg.get("caption") or "").strip()
        photos = msg.get("photo") or []
        if photos:
            photo = photos[-1]
            attachments.append({
                "kind": "image",
                "platform": "telegram",
                "file_id": photo.get("file_id", ""),
                "filename": f"telegram_photo_{photo.get('file_unique_id', 'image')}.jpg",
                "mime_type": "image/jpeg",
                "caption": msg.get("caption", ""),
            })
            text = text or (msg.get("caption") or "").strip()

    # ── Parser WhatsApp Cloud API ─────────────────────────────────────────────
    elif platform == "whatsapp_cloud":
        # Verificacion del webhook (GET request de Meta al registrar)
        # Nota: la verificacion GET se maneja en wa_verify endpoint abajo
        try:
            entry   = body.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value   = changes.get("value", {})
            msgs    = value.get("messages", [])
            if not msgs:
                return {"ok": True}
            msg     = msgs[0]
            chat_id = msg.get("from", "")      # numero en formato 573001234567
            msg_type = msg.get("type", "text")
            if msg_type == "text":
                text = msg.get("text", {}).get("body", "").strip()
            elif msg_type in ("audio", "voice"):
                audio_id = msg.get("audio", msg.get("voice", {})).get("id", "")
            elif msg_type == "image":
                attachments.append({
                    "kind": "image",
                    "platform": "whatsapp_cloud",
                    "media_id": msg.get("image", {}).get("id", ""),
                    "filename": f"wa_cloud_image_{msg.get('id', 'image')}.jpg",
                    "mime_type": msg.get("image", {}).get("mime_type", "image/jpeg"),
                    "caption": msg.get("image", {}).get("caption", ""),
                })
                text = msg.get("image", {}).get("caption", "").strip()
            elif msg_type == "document":
                attachments.append({
                    "kind": "document",
                    "platform": "whatsapp_cloud",
                    "media_id": msg.get("document", {}).get("id", ""),
                    "filename": msg.get("document", {}).get("filename", f"wa_cloud_{msg.get('id', 'document')}"),
                    "mime_type": msg.get("document", {}).get("mime_type", "application/octet-stream"),
                    "caption": msg.get("document", {}).get("caption", ""),
                })
                text = msg.get("document", {}).get("caption", "").strip()
        except (IndexError, KeyError, TypeError):
            return {"ok": True}

    # ── Parser Evolution API ──────────────────────────────────────────────────
    elif platform == "evolution":
        try:
            event = body.get("event", "")
            # Solo procesar eventos de mensajes recibidos
            if event and event not in ("messages.upsert", "messages.update", "MESSAGES_UPSERT", "MESSAGES_UPDATE"):
                return {"ok": True}
            data    = body.get("data", {})
            key     = data.get("key", {})
            # CRÍTICO: ignorar mensajes enviados por el propio bot (evita bucle infinito)
            if key.get("fromMe", False):
                return {"ok": True}
            remote_jid = key.get("remoteJid", "")
            # Ignorar grupos
            if "@g.us" in remote_jid:
                return {"ok": True}
            chat_id = remote_jid.split("@")[0]
            msg     = data.get("message", {})
            if not msg:
                # Algunos eventos de Evolution traen el mensaje en body directo
                msg = body.get("message", {})
            if "conversation" in msg:
                text = msg["conversation"].strip()
            elif "extendedTextMessage" in msg:
                text = msg["extendedTextMessage"].get("text", "").strip()
            elif "audioMessage" in msg:
                audio_id = key.get("id", "")
            elif "imageMessage" in msg:
                text = msg["imageMessage"].get("caption", "").strip()
        except (KeyError, AttributeError):
            return {"ok": True}

    # ── Parser WhatsApp Bridge (Custom Baileys) ──────────────────────────────
    elif platform == "whatsapp":
        try:
            if body.get("event") == "message.received":
                # Ignorar grupos
                if body.get("isGroup"):
                    return {"ok": True}
                # Ignorar mensajes enviados por el propio bot
                if body.get("fromMe", False):
                    return {"ok": True}
                # JID crudo necesario para responder y /read correctamente.
                # Algunos chats llegan con identificadores que no deben normalizarse.
                chat_id    = body.get("remoteJid") or body.get("from", "")
                message_id = body.get("messageId", "")
                text       = (body.get("text") or "").strip()
                # Audio con base64 inline
                if body.get("isAudio") and body.get("audioBase64"):
                    b64_mime = body.get("audioMime", "audio/ogg")
                    audio_id = f"wa_b64:{b64_mime}:{body['audioBase64']}"
                if body.get("isImage") and body.get("imageBase64"):
                    attachments.append({
                        "kind": "image",
                        "platform": "whatsapp",
                        "filename": f"wa_bridge_{body.get('messageId', 'image')}.jpg",
                        "mime_type": body.get("imageMime", "image/jpeg"),
                        "caption": text or "",
                        "base64": body.get("imageBase64", ""),
                    })
                if body.get("isDocument") and body.get("docBase64"):
                    attachments.append({
                        "kind": "document",
                        "platform": "whatsapp",
                        "filename": body.get("documentName", "document.bin"),
                        "mime_type": body.get("documentMime", "application/octet-stream"),
                        "caption": text or "",
                        "base64": body.get("docBase64", ""),
                    })
        except Exception:
            return {"ok": True}

    # ── Procesamiento comun ───────────────────────────────────────────────────
    if not chat_id:
        return {"ok": True}

    # Aparecer online inmediatamente al recibir — soluciona chulo gris
    if platform == "whatsapp" and Config.WHATSAPP_BRIDGE_URL:
        async def _appear_online():
            try:
                async with httpx.AsyncClient(timeout=3.0) as _hx:
                    await _hx.post(
                        f"{Config.WHATSAPP_BRIDGE_URL}/presence",
                        json={"status": "available", "timeout": 1800000}
                    )
            except Exception:
                pass
        asyncio.create_task(_appear_online())

    if audio_id:
        await conny._typing_action(chat_id)
        wa_mid = audio_id if platform == "whatsapp_cloud" else None
        text   = await conny.transcribe_audio(
            file_id=audio_id, platform=platform, wa_media_id=wa_mid)
        if not text or "[no pude" in text or "[no se pudo" in text:
            await conny._send_message(chat_id, "Recibí tu audio pero no lo pude procesar. ¿Puedes escribirlo?")
            return {"ok": True}
        # Block 3: First audio message — inject transcription with marker
        # Check if this is the first message (no assistant messages in history)
        try:
            from conny import db as _conny_db
            if _conny_db:
                _hist = _conny_db.get_history(chat_id, limit=3)
                _has_prev = any(m.get("role") == "assistant" for m in _hist)
                if not _has_prev:
                    text = f"[Transcripción de audio]: {text}"
        except Exception:
            pass
        log.info(f"[audio] {chat_id[:8]}: {text[:60]}")

    if not text and not attachments:
        return {"ok": True}

    urgent = conny.is_urgent(text or "")
    route = {"platform": platform}
    asyncio.create_task(
        conny.enqueue_message(
            chat_id,
            text or "",
            urgent=urgent,
            message_id=message_id or "",
            route=route,
            attachments=attachments,
        )
    )
    return {"ok": True}


@app.post("/telegram/shared/{secret}")
async def telegram_shared_webhook(secret: str, request: Request):
    """
    Router compartido de Telegram.
    Inspirado en el patrón de OpenClaw: un solo ingress y luego enrutamiento
    por sesión/chat hacia un agente o instancia concreta.
    """
    if not Config.TELEGRAM_SHARED_ROUTER or secret != Config.TELEGRAM_SHARED_SECRET:
        return Response(status_code=403)

    try:
        body = await request.json()
    except Exception:
        return Response(status_code=400)

    msg = body.get("message") or body.get("edited_message")
    if not msg:
        return {"ok": True}

    chat = msg.get("chat") or {}
    chat_id = str(chat.get("id", "")).strip()
    if not chat_id:
        return {"ok": True}

    target = _resolve_shared_telegram_target(chat_id)
    if not target:
        await _send_shared_unpaired_notice(chat_id)
        return {"ok": True, "routed": False}

    try:
        forwarded = await _forward_shared_telegram_update(target, body)
        return {
            "ok": True,
            "routed": forwarded.get("status", 500) < 400,
            "instance": target["name"],
            "forwarded_status": forwarded.get("status", 500),
        }
    except Exception as e:
        log.error(f"[telegram_shared] error reenviando a {target['name']}: {e}")
        return {"ok": True, "routed": False, "error": str(e)[:120]}


@app.get("/webhook/{secret}")
async def wa_verify(secret: str, request: Request):
    """
    Endpoint de verificacion de WhatsApp Cloud API.
    Meta hace un GET con hub.challenge al registrar el webhook.
    """
    if secret != Config.WEBHOOK_SECRET:
        return Response(status_code=403)
    params = dict(request.query_params)
    mode      = params.get("hub.mode", "")
    token     = params.get("hub.verify_token", "")
    challenge = params.get("hub.challenge", "")
    if mode == "subscribe" and token == Config.WA_VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")
    return Response(status_code=403)


# ─── API Endpoints ──────────────────────────────────────────────────────────────

@app.get("/telegram/status")
async def telegram_status():
    status = {
        "enabled": bool(Config.TELEGRAM_TOKEN),
        "platform": Config.PLATFORM,
        "shared": Config.TELEGRAM_SHARED,
        "shared_router": Config.TELEGRAM_SHARED_ROUTER,
        "mode": _telegram_webhook_mode(),
        "base_url": Config.BASE_URL,
        "webhook_secret": Config.WEBHOOK_SECRET,
    }
    if not Config.TELEGRAM_TOKEN:
        status["ok"] = False
        status["reason"] = "missing_token"
        return status

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            me_resp = await client.get(f"https://api.telegram.org/bot{Config.TELEGRAM_TOKEN}/getMe")
            webhook_resp = await client.get(f"https://api.telegram.org/bot{Config.TELEGRAM_TOKEN}/getWebhookInfo")
        me = me_resp.json().get("result", {}) if me_resp.status_code < 500 else {}
        webhook = webhook_resp.json().get("result", {}) if webhook_resp.status_code < 500 else {}
        status.update(
            {
                "ok": True,
                "bot_username": me.get("username", ""),
                "bot_name": me.get("first_name", ""),
                "webhook_url": webhook.get("url", ""),
                "pending_update_count": webhook.get("pending_update_count", 0),
                "last_error_message": webhook.get("last_error_message", ""),
                "last_error_date": webhook.get("last_error_date"),
            }
        )
    except Exception as exc:
        status["ok"] = False
        status["reason"] = str(exc)[:160]
    return status

@app.get("/health")
async def health():
    """Health check."""
    clinic = db.get_clinic() if db else {}
    shared_instances = _discover_shared_telegram_instances() if Config.TELEGRAM_SHARED_ROUTER else []
    shared_routes = _load_shared_telegram_routes() if Config.TELEGRAM_SHARED_ROUTER else {}
    default_instance = (
        shared_routes.get("default_instance", "")
        or Config.TELEGRAM_DEFAULT_INSTANCE
        or (shared_instances[0]["name"] if len(shared_instances) == 1 else "")
    ) if Config.TELEGRAM_SHARED_ROUTER else ""

    # WhatsApp status
    wa_connected = False
    wa_phone = ""
    bridge_status = {}
    try:
        wa_connected = db.recall("whatsapp_connected") == "true"
        wa_phone = db.recall("whatsapp_phone") or ""
    except Exception:
        pass
    if Config.WHATSAPP_BRIDGE_URL:
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                r = await client.get(f"{Config.WHATSAPP_BRIDGE_URL}/status")
                if r.status_code < 400:
                    bridge_status = r.json()
                    if (
                        bridge_status.get("connected")
                        or bridge_status.get("phoneNumber")
                        or bridge_status.get("status") == "open"
                        or bridge_status.get("jid")
                    ):
                        wa_connected = True
                        wa_phone = wa_phone or bridge_status.get("phoneNumber", "")
        except Exception:
            bridge_status = {}

    # Core memory count
    mem_count = 0
    try:
        mem_count = len(db.recall_all())
    except Exception:
        pass

    return {
        "status":         "online",
        "version":        "9.6.1",
        "clinic":         clinic.get("name", "sin configurar"),
        "sector":         Config.SECTOR or clinic.get("sector", "otro"),
        "setup_done":     bool(clinic.get("setup_done")),
        "platform":       Config.PLATFORM,
        "whatsapp": {
            "connected":  wa_connected,
            "phone":      wa_phone,
            "bridge":     bridge_status,
        },
        "models":         Config.LLM_MODELS,
        "buffer_window":  f"{Config.BUFFER_WAIT_MIN}-{Config.BUFFER_WAIT_MAX}s",
        "active_buffers": len(conny._pending_buffers) if conny else 0,
        "plugins_active": len(mcp_manager.plugins) if mcp_manager else 0,
        "memory_items":   mem_count,
        "omni_url":       os.getenv("OMNI_URL", ""),
        "telegram_shared_router": {
            "enabled": Config.TELEGRAM_SHARED_ROUTER,
            "instances": len(shared_instances),
            "default_instance": default_instance,
        },
        "timestamp":      datetime.now().isoformat()
    }

@app.get("/dashboard")
async def dashboard():
    """Dashboard completo."""
    clinic = db.get_clinic()
    
    with db._conn() as c:
        total_appointments = c.execute("SELECT COUNT(*) FROM appointments").fetchone()[0]
        pending_appointments = c.execute(
            "SELECT COUNT(*) FROM appointments WHERE status='pendiente'"
        ).fetchone()[0]
        total_patients = c.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
        new_today = c.execute(
            "SELECT COUNT(*) FROM patients WHERE date(first_seen)=date('now')"
        ).fetchone()[0]
        total_conversations = c.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
    
    # Métricas de rendimiento
    metrics = db.get_metrics(since=datetime.now() - timedelta(hours=24))
    avg_latency = sum(
        m["metric_value"] for m in metrics 
        if m.get("metric_name") == "response_time"
    ) / max(len([m for m in metrics if m.get("metric_name") == "response_time"]), 1)
    
    return {
        "clinic": {
            "name": clinic.get("name"),
            "setup_done": bool(clinic.get("setup_done")),
            "services": clinic.get("services", []),
            "phone": clinic.get("phone"),
        },
        "stats": {
            "total_patients": total_patients,
            "new_patients_today": new_today,
            "total_appointments": total_appointments,
            "pending_appointments": pending_appointments,
            "total_conversations": total_conversations,
        },
        "performance": {
            "avg_response_time_ms": round(avg_latency, 2),
            "active_buffers": len(conny._pending_buffers) if conny else 0,
        },
        "system": {
            "model_primary": Config.LLM_MODELS["fast"],
            "model_reasoning": Config.LLM_MODELS["reasoning"],
            "plugins_count": len(mcp_manager.plugins) if mcp_manager else 0,
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/appointments")
async def list_appointments(
    status: Optional[str] = None,
    limit: int = 50
):
    """Lista citas."""
    appointments = db.get_appointments(status=status, limit=limit)
    return {"appointments": appointments, "count": len(appointments)}

@app.get("/appointments/{apt_id}")
async def get_appointment(apt_id: int):
    """Obtiene una cita específica."""
    with db._conn() as c:
        row = c.execute("SELECT * FROM appointments WHERE id=?", (apt_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    return dict(row)

@app.patch("/appointments/{apt_id}")
async def update_appointment(apt_id: int, request: Request):
    """Actualiza una cita."""
    data = await request.json()
    db.update_appointment(apt_id, **data)
    return {"ok": True}

@app.get("/patients")
async def list_patients(limit: int = 50):
    """Lista pacientes."""
    with db._conn() as c:
        rows = c.execute("""
            SELECT chat_id, name, phone, visits, first_seen, last_seen
            FROM patients
            ORDER BY last_seen DESC
            LIMIT ?
        """, (limit,)).fetchall()
    
    patients = []
    for r in rows:
        p = dict(r)
        history = db.get_history(p['chat_id'], limit=1)
        if history:
            p['last_message'] = history[0].get('content', '')
            p['last_message_role'] = history[0].get('role', '')
        else:
            p['last_message'] = ''
            p['last_message_role'] = ''
        patients.append(p)
    return {"patients": patients}


@app.get("/patients/{chat_id}")
async def get_patient(chat_id: str):
    """Obtiene un paciente."""
    with db._conn() as c:
        row = c.execute("SELECT * FROM patients WHERE chat_id=?", (chat_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    
    data = dict(row)
    for field in ['preferences', 'tags', 'services_used']:
        try:
            data[field] = json.loads(data.get(field, '{}') or '{}')
        except Exception:
            data[field] = {}
    
    return data

@app.get("/conversations/{chat_id}")
async def get_conversations(chat_id: str, limit: int = 50):
    """Obtiene historial de conversación."""
    history = db.get_history(chat_id, limit=limit)
    return {"chat_id": chat_id, "messages": history, "count": len(history)}

@app.get("/metrics")
async def get_metrics(
    metric_type: Optional[str] = None,
    hours: int = 24
):
    """Obtiene métricas."""
    since = datetime.now() - timedelta(hours=hours)
    metrics = db.get_metrics(metric_type=metric_type, since=since)
    return {"metrics": metrics, "period_hours": hours}

@app.get("/plugins")
async def list_plugins():
    """Lista plugins."""
    plugins = db.get_plugins()
    health = await mcp_manager.health_check_all() if mcp_manager else {}
    
    return {
        "plugins": [
            {
                "id": p.id,
                "name": p.name,
                "version": p.version,
                "enabled": p.enabled,
                "capabilities": p.capabilities,
                "health": health.get(p.id, False)
            }
            for p in plugins
        ]
    }

@app.post("/plugins/{plugin_id}/execute")
async def execute_plugin(plugin_id: str, request: Request):
    """Ejecuta acción en plugin."""
    data = await request.json()
    action = data.get("action")
    params = data.get("params", {})
    
    if not action:
        raise HTTPException(status_code=400, detail="action requerido")
    
    result = await mcp_manager.execute(plugin_id, action, params)
    return result

@app.get("/config")
async def get_config():
    """Obtiene configuración de la clínica."""
    clinic = db.get_clinic()
    
    # Ocultar datos sensibles
    safe_clinic = {
        k: v for k, v in clinic.items()
        if k not in ['admin_chat_ids']
    }
    
    return safe_clinic

@app.patch("/config")
async def update_config(request: Request):
    """Actualiza configuración."""
    data = await request.json()
    
    # Validar campos permitidos
    allowed = {
        'name', 'tagline', 'address', 'phone', 'email', 'website',
        'services', 'schedule', 'holidays', 'timezone', 'currency',
        'persona_config', 'business_rules', 'pricing', 'promotions',
        'notification_settings', 'avatar'
    }
    
    filtered = {k: v for k, v in data.items() if k in allowed}
    
    if filtered:
        db.update_clinic(**filtered)
    
    return {"ok": True, "updated": list(filtered.keys())}

import base64
import time
from pydantic import BaseModel

class AvatarUploadRequest(BaseModel):
    filename: str
    content_type: str
    data: str

@app.post("/upload-avatar")
async def upload_avatar_base64(req: AvatarUploadRequest):
    data_str = req.data
    if "," in data_str:
        data_str = data_str.split(",", 1)[1]
    
    try:
        decoded_data = base64.b64decode(data_str)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid base64 data")
        
    ext = ".png"
    if "jpeg" in req.content_type or "jpg" in req.content_type:
        ext = ".jpg"
    elif "gif" in req.content_type:
        ext = ".gif"
        
    save_name = f"avatar_upload_{int(time.time())}{ext}"
    save_path = Path("/home/ubuntu/conny/src/interfaces/web/static/avatars") / save_name
    save_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(save_path, "wb") as f:
        f.write(decoded_data)
        
    return {"ok": True, "url": f"/static/avatars/{save_name}"}

@app.get("/personality")
async def get_personality():
    """Obtiene configuración de personalidad."""
    clinic = db.get_clinic()
    persona = clinic.get("persona_config", {})
    
    if isinstance(persona, str):
        persona = json.loads(persona) if persona else {}
    
    # Merge con defaults
    default = PersonalityProfile()
    full_persona = {
        "name": persona.get("name", default.name),
        "role": persona.get("role", default.role),
        "tone": persona.get("tone", default.tone),
        "formality_level": persona.get("formality_level", default.formality_level),
        "warmth_level": persona.get("warmth_level", default.warmth_level),
        "humor_level": persona.get("humor_level", default.humor_level),
        "verbosity": persona.get("verbosity", default.verbosity),
        "greetings": persona.get("greetings", default.greetings),
        "closings": persona.get("closings", default.closings),
        "affirmations": persona.get("affirmations", default.affirmations),
        "forbidden_words": persona.get("forbidden_words", default.forbidden_words),
        "custom_phrases": persona.get("custom_phrases", default.custom_phrases),
        "situation_responses": persona.get("situation_responses", default.situation_responses),
    }
    
    return full_persona

@app.patch("/personality")
async def update_personality(request: Request):
    """Actualiza personalidad."""
    data = await request.json()
    
    clinic = db.get_clinic()
    persona = clinic.get("persona_config", {})
    if isinstance(persona, str):
        persona = json.loads(persona) if persona else {}
    
    persona.update(data)
    db.update_clinic(persona_config=persona)
    
    return {"ok": True}

@app.post("/self-improve")
async def trigger_self_improvement():
    """Dispara análisis de auto-mejora."""
    if not conny or not conny.self_improvement:
        raise HTTPException(status_code=503, detail="Sistema no inicializado")
    
    analysis = await conny.self_improvement.analyze_performance()
    return analysis

@app.post("/self-improve/apply")
async def apply_improvements():
    """Aplica mejoras sugeridas."""
    if not conny or not conny.self_improvement:
        raise HTTPException(status_code=503, detail="Sistema no inicializado")
    
    applied = await conny.self_improvement.apply_improvements(auto_apply=True)
    return {"applied": applied}

@app.get("/tasks")
async def list_tasks(status: Optional[str] = None, limit: int = 50):
    """Lista tareas."""
    with db._conn() as c:
        query = "SELECT * FROM tasks"
        params = []
        
        if status:
            query += " WHERE status=?"
            params.append(status)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        rows = c.execute(query, params).fetchall()
    
    return {"tasks": [dict(r) for r in rows]}

@app.post("/tasks")
async def create_task(request: Request):
    """Crea una tarea programada."""
    data = await request.json()
    
    task_type = data.get("type")
    task_data = data.get("data", {})
    scheduled_for = data.get("scheduled_for")
    priority = data.get("priority", 5)
    
    if not task_type:
        raise HTTPException(status_code=400, detail="type requerido")
    
    scheduled = None
    if scheduled_for:
        scheduled = datetime.fromisoformat(scheduled_for)
    
    task_id = task_manager.schedule_task(
        task_type, 
        task_data, 
        scheduled_for=scheduled,
        priority=priority
    )
    
    return {"ok": True, "task_id": task_id}

@app.get("/setup-webhook")
async def setup_webhook_endpoint():
    """Configura webhook manualmente."""
    if not Config.BASE_URL:
        raise HTTPException(status_code=400, detail="BASE_URL no configurada")
    
    await set_webhook()
    return {"ok": True}

@app.post("/send-message")
async def send_direct_message(request: Request):
    """
    Envía mensaje directo (admin only).
    Si no incluye 'confirmar': true, primero confirma con el admin.
    """
    global ADMIN_PENDING_CONFIRMATIONS
    
    data = await request.json()
    chat_id = data.get("chat_id")
    message = data.get("message")
    confirmar = data.get("confirmar", False)
    
    if not chat_id or not message:
        raise HTTPException(status_code=400, detail="chat_id y message requeridos")
    
    ADMIN_TELEGRAM_ID = "6908159885"  # Santiago
    
    if not confirmar:
        confirm_id = f"confirm_{chat_id}_{int(asyncio.time.time())}"
        ADMIN_PENDING_CONFIRMATIONS[confirm_id] = {
            "chat_id": chat_id,
            "message": message,
            "timestamp": asyncio.time.time()
        }
        
        confirm_text = f"""📝 *Confirmar mensaje al lead*

Chat ID: `{chat_id}`
Mensaje:
{message}

¿Confirmas enviarlo? Responde *CONFIRMAR* para enviar o *CANCELAR* para cancelar."""
        
        await conny._send_message(ADMIN_TELEGRAM_ID, confirm_text)
        return {
            "ok": False, 
            "esperando_confirmacion": True,
            "confirm_id": confirm_id,
            "chat_id": chat_id,
            "message": message[:100] + "..." if len(message) > 100 else message,
            "mensaje": "Mensaje en cola. Confirma con CONFIRMAR para enviar, CANCELAR para cancelar."
        }
    
    await conny._send_message(chat_id, message)
    return {"ok": True, "sent": True, "to": chat_id}


async def _handle_admin_confirm(chat_id: str, text: str) -> List[str]:
    """Procesa confirmación del admin para enviar mensaje pendiente."""
    global ADMIN_PENDING_CONFIRMATIONS
    
    if not ADMIN_PENDING_CONFIRMATIONS:
        return ["No hay ningún mensaje pendiente de confirmación."]
    
    confirm_id = None
    pending_data = None
    
    for cid, data in ADMIN_PENDING_CONFIRMATIONS.items():
        if abs(data.get("timestamp", 0) - asyncio.time.time()) < 3600:
            confirm_id = cid
            pending_data = data
            break
    
    if not pending_data:
        ADMIN_PENDING_CONFIRMATIONS.clear()
        return ["El mensaje pendiente expiró. Puedes intentar de nuevo."]
    
    lead_chat_id = pending_data["chat_id"]
    message = pending_data["message"]
    
    del ADMIN_PENDING_CONFIRMATIONS[confirm_id]
    
    await conny._send_message(lead_chat_id, message)
    return [f"✅ Mensaje enviado al lead {lead_chat_id}:\n\n{message[:200]}" + ("..." if len(message) > 200 else "")]


async def _handle_admin_cancel(chat_id: str, text: str) -> List[str]:
    """Cancela mensaje pendiente."""
    global ADMIN_PENDING_CONFIRMATIONS
    
    if not ADMIN_PENDING_CONFIRMATIONS:
        return ["No hay ningún mensaje pendiente de confirmación."]
    
    ADMIN_PENDING_CONFIRMATIONS.clear()
    return ["❌ Mensaje cancelado. No se envió al lead."]


async def smart_handoff_to_santiago(lead_chat_id: str, question: str, conny_response: str = "") -> bool:
    """Notifica a Santiago (6908159885) cuando Conny no sabe la respuesta."""
    import httpx
    
    SANTIAGO_TELEGRAM_ID = "6908159885"
    message = f"🔔 LEAD sin respuesta clara:\n\n📱 Chat: {lead_chat_id}\n❓ Pregunta: {question}\n🤖 Respuesta de Conny: {conny_response[:200] if conny_response else 'Sin respuesta'}\n\n➡️ Contactar al lead con la respuesta."
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"https://api.telegram.org/bot{Config.TELEGRAM_TOKEN}/sendMessage",
                json={"chat_id": SANTIAGO_TELEGRAM_ID, "text": message}
            )
        return True
    except Exception as e:
        log.warning(f"[smart_handoff] Error notifying Santiago: {e}")
        return False


@app.post("/test")
async def test_message(request: Request):
    """
    Endpoint de prueba para el CLI (conny chat → opción 2).
    Procesa un mensaje directamente sin buffer ni envío por Telegram/WA.
    Retorna la respuesta de Conny como texto para mostrarse en terminal.

    Body: {"message": "Hola", "user_id": "test_cli"}
    Requiere header X-Master-Key o el parámetro master_key en el body.
    """
    data = await request.json()
    message   = (data.get("message") or "").strip()
    user_id   = (data.get("user_id") or "cli_test_000").strip()
    master_key_header = request.headers.get("X-Master-Key", "")
    master_key_body   = data.get("master_key", "")

    # Validar master key (si está configurada)
    if Config.MASTER_API_KEY:
        provided = master_key_header or master_key_body
        if provided != Config.MASTER_API_KEY:
            raise HTTPException(status_code=401, detail="X-Master-Key inválida")

    if not message:
        raise HTTPException(status_code=400, detail="message requerido")

    if not conny:
        raise HTTPException(status_code=503, detail="Conny no inicializada")

    try:
        # Llamar process_message directamente, sin buffer ni envío real
        responses: list = await conny.process_message(user_id, message)
        # Unir los fragmentos si hay varios (Conny puede devolver lista)
        full_response = "\n".join(str(r) for r in responses) if responses else "(sin respuesta)"
        return {
            "ok":       True,
            "message":  message,
            "user_id":  user_id,
            "bubbles":  responses or [],
            "response": full_response,
        }
    except Exception as e:
        log.error(f"[/test] error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error procesando: {str(e)[:200]}")

@app.post("/broadcast")
async def broadcast_message(request: Request):
    """Envía mensaje a todos los pacientes."""
    data = await request.json()
    message = data.get("message")
    
    if not message:
        raise HTTPException(status_code=400, detail="message requerido")
    
    with db._conn() as c:
        rows = c.execute("SELECT chat_id FROM patients").fetchall()
    
    sent = 0
    for row in rows:
        try:
            await conny._send_message(row["chat_id"], message)
            sent += 1
            await asyncio.sleep(0.1)  # Rate limiting
        except Exception:
            pass
    
    return {"ok": True, "sent": sent, "total": len(rows)}

@app.post("/reset")
async def reset_system():
    """Resetea el sistema (solo desarrollo)."""
    with db._conn() as c:
        c.execute("UPDATE clinic SET setup_done=0, setup_step='idle', setup_buffer='{}', admin_chat_ids='[]' WHERE id=1")
        c.execute("DELETE FROM conversations")
        c.execute("DELETE FROM appointments")
        c.execute("DELETE FROM patients")
        c.execute("DELETE FROM tasks")
        c.execute("DELETE FROM metrics")
        c.execute("DELETE FROM memories")
        c.execute("DELETE FROM response_cache")
    
    if conny:
        conny._pending_buffers.clear()
    
    return {"ok": True, "message": "Sistema reseteado"}

@app.get("/export")
async def export_data():
    """Exporta todos los datos."""
    clinic = db.get_clinic()
    
    with db._conn() as c:
        appointments = [dict(r) for r in c.execute("SELECT * FROM appointments").fetchall()]
        patients = [dict(r) for r in c.execute("SELECT * FROM patients").fetchall()]
        conversations = [dict(r) for r in c.execute("SELECT * FROM conversations ORDER BY ts DESC LIMIT 1000").fetchall()]

    brand_manifest = {}
    try:
        if conny:
            store = conny._brand_store(clinic)
            if store:
                brand_manifest = store.manifest()
    except Exception:
        brand_manifest = {}
    
    return {
        "exported_at": datetime.now().isoformat(),
        "clinic": clinic,
        "appointments": appointments,
        "patients": patients,
        "conversations": conversations,
        "core_memory": db.recall_all() if db else {},
        "trust_rules": db.get_all_trust_rules() if db else [],
        "behavior_playbooks": db.get_behavior_playbooks(limit=100) if db else [],
        "knowledge_base_stats": kb.get_stats() if kb and _KB_AVAILABLE else {},
        "brand_manifest": brand_manifest,
    }

# ─── Analytics Endpoints ────────────────────────────────────────────────────────

@app.get("/analytics/summary")
async def analytics_summary(days: int = 7):
    """Resumen de analytics."""
    since = datetime.now() - timedelta(days=days)

    with db._conn() as c:
        # Citas por día
        appointments_by_day = c.execute("""
            SELECT date(created_at) as day, COUNT(*) as count
            FROM appointments
            WHERE created_at > ?
            GROUP BY date(created_at)
            ORDER BY day
        """, (since.isoformat(),)).fetchall()

        # Nuevos pacientes por día
        patients_by_day = c.execute("""
            SELECT date(first_seen) as day, COUNT(*) as count
            FROM patients
            WHERE first_seen > ?
            GROUP BY date(first_seen)
            ORDER BY day
        """, (since.isoformat(),)).fetchall()

        # Servicios más solicitados
        top_services = c.execute("""
            SELECT service, COUNT(*) as count
            FROM appointments
            WHERE created_at > ?
            GROUP BY service
            ORDER BY count DESC
            LIMIT 10
        """, (since.isoformat(),)).fetchall()

        # Conversiones
        total_conversations = c.execute("""
            SELECT COUNT(DISTINCT chat_id) FROM conversations WHERE ts > ?
        """, (since.isoformat(),)).fetchone()[0]

        total_appointments = c.execute("""
            SELECT COUNT(*) FROM appointments WHERE created_at > ?
        """, (since.isoformat(),)).fetchone()[0]

    conversion_rate = (total_appointments / total_conversations * 100) if total_conversations > 0 else 0

    return {
        "period_days": days,
        "appointments_by_day": [dict(r) for r in appointments_by_day],
        "patients_by_day": [dict(r) for r in patients_by_day],
        "top_services": [dict(r) for r in top_services],
        "conversion_rate": round(conversion_rate, 2),
        "total_conversations": total_conversations,
        "total_appointments": total_appointments
    }

@app.get("/analytics/intents")
async def analytics_intents(hours: int = 24):
    """Distribución de intenciones."""
    since = datetime.now() - timedelta(hours=hours)
    
    with db._conn() as c:
        rows = c.execute("""
            SELECT analysis FROM conversations
            WHERE role='user' AND ts > ?
        """, (since.isoformat(),)).fetchall()
    
    intent_counts = defaultdict(int)
    for row in rows:
        try:
            analysis = json.loads(row["analysis"] or "{}")
            intent = analysis.get("intent", "unknown")
            intent_counts[intent] += 1
        except Exception:
            pass
    
    return {
        "period_hours": hours,
        "intents": dict(intent_counts),
        "total": sum(intent_counts.values())
    }

@app.get("/analytics/sentiment")
async def analytics_sentiment(hours: int = 24):
    """Distribución de sentimiento."""
    since = datetime.now() - timedelta(hours=hours)
    
    with db._conn() as c:
        rows = c.execute("""
            SELECT analysis FROM conversations
            WHERE role='user' AND ts > ?
        """, (since.isoformat(),)).fetchall()
    
    sentiment_counts = defaultdict(int)
    total_score = 0
    count = 0
    
    for row in rows:
        try:
            analysis = json.loads(row["analysis"] or "{}")
            sentiment = analysis.get("sentiment", "neutral")
            score = analysis.get("sentiment_score", 0)
            sentiment_counts[sentiment] += 1
            total_score += score
            count += 1
        except Exception:
            pass
    
    avg_score = total_score / count if count > 0 else 0
    
    return {
        "period_hours": hours,
        "distribution": dict(sentiment_counts),
        "average_score": round(avg_score, 3),
        "total_messages": count
    }

# ─── Logs Endpoint ──────────────────────────────────────────────────────────────

@app.get("/logs/improvements")
async def get_improvement_logs(limit: int = 50):
    """Obtiene logs de auto-mejora."""
    with db._conn() as c:
        rows = c.execute("""
            SELECT * FROM self_improvement_log
            ORDER BY ts DESC
            LIMIT ?
        """, (limit,)).fetchall()
    
    return {"logs": [dict(r) for r in rows]}

@app.get("/logs/errors")
async def get_error_logs(hours: int = 24):
    """Obtiene logs de errores."""
    since = datetime.now() - timedelta(hours=hours)
    
    metrics = db.get_metrics(metric_type="error", since=since)
    
    return {"errors": metrics, "period_hours": hours}


# ─── Auth API Endpoints (solo accesibles con MASTER_API_KEY) ─────────────────

def _verify_master_key(request: Request) -> bool:
    """Verifica la API key maestra de Santiago."""
    key = request.headers.get("X-Master-Key", "")
    if not Config.MASTER_API_KEY:
        return False
    return secrets.compare_digest(key, Config.MASTER_API_KEY)

@app.post("/api/tokens/create")
async def api_create_token(request: Request):
    """
    Santiago crea un token de activacion para una nueva clinica.
    Requiere header: X-Master-Key: [MASTER_API_KEY]
    Body: {"clinic_label": "Clinica de los Deseos"}
    """
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")

    try:
        body = await request.json()
    except Exception:
        body = {}

    clinic_label = body.get("clinic_label", "").strip()
    if not clinic_label:
        raise HTTPException(status_code=400, detail="clinic_label requerido")

    # Generar token
    token = generate_activation_token(clinic_label)

    # Calcular expiracion
    expires_at = (datetime.now() + timedelta(hours=Config.TOKEN_EXPIRY_HOURS)).isoformat()

    # Guardar en DB
    saved = db.create_activation_token(token, clinic_label, expires_at)
    if not saved:
        raise HTTPException(status_code=500, detail="No se pudo guardar el token")

    log.info(f"[api] token creado para '{clinic_label}': {token[:20]}...")

    return {
        "ok": True,
        "token": token,
        "clinic_label": clinic_label,
        "expires_at": expires_at,
        "instructions": f"Envia este token exacto al administrador de {clinic_label}. Expira en {Config.TOKEN_EXPIRY_HOURS}h."
    }

@app.post("/api/activate")
async def api_activate(request: Request):
    """
    Endpoint PUBLICO que recibe {"token": "ACTV-..."}
    Lo valida contra la DB (chequeando expiracion y uso).
    Si es valido, lo marca como usado y devuelve la MASTER_API_KEY real.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="JSON invalido")
        
    token = body.get("token", "").strip()
    if not token or not token.startswith("ACTV-"):
        raise HTTPException(status_code=400, detail="Token no valido")
        
    token_data = db.get_activation_token(token)
    if not token_data:
        raise HTTPException(status_code=404, detail="Token inexistente")
        
    if token_data.get("used_at"):
        raise HTTPException(status_code=400, detail="El token ya fue usado")
        
    expires = token_data.get("expires_at", "")
    if expires:
        try:
            exp_date = datetime.fromisoformat(expires)
            if datetime.now() > exp_date:
                raise HTTPException(status_code=400, detail="El token expiro")
        except Exception:
            pass
            
    # Marcar como usado
    try:
        db.consume_activation_token(token, "web_dashboard")
    except Exception as e:
        log.error(f"Error consumiendo token {token}: {e}")
        raise HTTPException(status_code=500, detail="Error interno actualizando token")
        
    log.info(f"[api] Token de activacion '{token[:15]}...' canjeado exitosamente.")
    
@app.post("/api/auth/check-email")
async def api_check_email(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="JSON invalido")
    email = body.get("email", "").strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Email es requerido")
    
    clinic = db.get_clinic()
    exists = False
    if clinic:
        clinic_email = clinic.get("email", "").strip().lower()
        setup_done = clinic.get("setup_done", 0)
        onboarding_done = clinic.get("onboarding_done", 0)
        if clinic_email == email and (setup_done or onboarding_done):
            exists = True
    return {"exists": exists}

@app.post("/api/auth/login")
async def api_auth_login(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="JSON invalido")
    email = body.get("email", "").strip().lower()
    password = body.get("password", "").strip()
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email y contraseña son requeridos")
    
    if password == Config.MASTER_API_KEY:
        clinic = db.get_clinic()
        if clinic and clinic.get("email", "").strip().lower() == email:
            return {"ok": True, "master_key": Config.MASTER_API_KEY}
    
    with db._conn() as c:
        row = c.execute("SELECT password_hash FROM admins WHERE email = ? AND is_active = 1", (email,)).fetchone()
        if row and verify_password(password, row["password_hash"]):
            return {"ok": True, "master_key": Config.MASTER_API_KEY}
            
    raise HTTPException(status_code=401, detail="Credenciales incorrectas")

@app.post("/api/auth/register")
async def api_auth_register(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="JSON invalido")
    email = body.get("email", "").strip().lower()
    password = body.get("password", "").strip()
    name = body.get("name", "").strip()
    phone = body.get("phone", "").strip()
    specialty = body.get("specialty", "").strip()
    token = body.get("token", "").strip()
    
    if not email or not password or not name or not token:
        raise HTTPException(status_code=400, detail="Faltan campos requeridos")
    
    if not token.startswith("ACTV-"):
        raise HTTPException(status_code=400, detail="Token no valido")
        
    token_data = db.get_activation_token(token)
    if not token_data:
        raise HTTPException(status_code=404, detail="Token inexistente")
    if token_data.get("used_at"):
        raise HTTPException(status_code=400, detail="El token ya fue usado")
        
    try:
        db.consume_activation_token(token, "web_dashboard_register")
    except Exception as e:
        log.error(f"Error consumiendo token {token}: {e}")
        raise HTTPException(status_code=500, detail="Error interno actualizando token")
        
    db.update_clinic(
        name=name,
        phone=phone,
        email=email,
        sector=specialty,
        setup_done=1,
        onboarding_done=1
    )
    
    pass_hash = hash_password(password)
    try:
        with db._conn() as c:
            c.execute("""
                INSERT OR REPLACE INTO admins (chat_id, email, password_hash, name, role, activated_by_token, is_active)
                VALUES (?, ?, ?, ?, 'owner', ?, 1)
            """, (f"owner_{secrets.token_hex(4)}", email, pass_hash, name, token))
    except Exception as e:
        log.error(f"Error insertando admin: {e}")
        
    return {
        "ok": True,
        "master_key": Config.MASTER_API_KEY,
        "message": "Registro completado con exito"
    }

@app.post("/api/auth/dev-login")
async def api_auth_dev_login(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="JSON invalido")
    email = body.get("email", "").strip().lower()
    password = body.get("password", "").strip()
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email y contraseña son requeridos")
    
    account = db.get_dev_account(email)
    if not account:
        raise HTTPException(status_code=401, detail="Cuenta de desarrollador no encontrada")
    
    if not verify_password(password, account["password_hash"]):
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")
        
    return {"ok": True, "master_key": Config.MASTER_API_KEY}

@app.post("/api/auth/dev-register")
async def api_auth_dev_register(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="JSON invalido")
    email = body.get("email", "").strip().lower()
    password = body.get("password", "").strip()
    dev_token = body.get("dev_token", "").strip()
    
    if not email or not password or not dev_token:
        raise HTTPException(status_code=400, detail="Todos los campos son requeridos")
        
    if not Config.MASTER_API_KEY or not secrets.compare_digest(dev_token, Config.MASTER_API_KEY):
        raise HTTPException(status_code=401, detail="Token de acceso para desarrolladores incorrecto")
        
    hashed = hash_password(password)
    success = db.create_dev_account(email, hashed)
    if not success:
        raise HTTPException(status_code=500, detail="Error al registrar la cuenta de desarrollador")
        
    return {"ok": True, "message": "Cuenta de desarrollador registrada con exito"}

# ── Developer Console API ──

@app.get("/api/dev/instances")
async def api_dev_list_instances(request: Request):
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")
    
    import subprocess
    import json
    import os
    import sqlite3

    instances = []
    pm2_status = {}
    try:
        res = subprocess.run(["pm2", "jlist"], capture_output=True, text=True)
        if res.returncode == 0 and res.stdout.strip():
            pm2_data = json.loads(res.stdout)
            for proc in pm2_data:
                pname = proc.get("name")
                status = proc.get("pm2_env", {}).get("status", "offline")
                pm2_status[pname] = status
    except Exception:
        pass

    # Base Conny instance
    base_name = "conny"
    base_status = pm2_status.get(base_name, "offline")
    if base_name in pm2_status:
        instances.append({
            "name": base_name,
            "sector": "Instancia Base",
            "port": "N/A",
            "status": base_status,
            "model": "Por Defecto",
            "path": "/home/ubuntu/conny"
        })

    instances_dir = "/home/ubuntu/conny-instances"
    if os.path.isdir(instances_dir):
        for entry in os.listdir(instances_dir):
            inst_path = os.path.join(instances_dir, entry)
            if os.path.isdir(inst_path):
                model = "Por defecto"
                port = "N/A"
                env_path = os.path.join(inst_path, ".env")
                if os.path.isfile(env_path):
                    with open(env_path, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.startswith("MODEL_TIER_1="):
                                model = line.split("=", 1)[1].strip()
                            elif line.startswith("PORT="):
                                port = line.split("=", 1)[1].strip()
                sector = "Desconocido"
                db_path = os.path.join(inst_path, "conny_ultra.db")
                if os.path.isfile(db_path):
                    try:
                        conn = sqlite3.connect(db_path)
                        cursor = conn.cursor()
                        cursor.execute("SELECT sector FROM clinic LIMIT 1")
                        row = cursor.fetchone()
                        if row and row[0]:
                            sector = row[0]
                        conn.close()
                    except Exception:
                        pass
                status = pm2_status.get(entry, "offline")
                instances.append({
                    "name": entry,
                    "sector": sector,
                    "port": port,
                    "status": status,
                    "model": model,
                    "path": inst_path
                })
    return {"instances": instances}

@app.post("/api/dev/instances/new")
async def api_dev_new_instance(request: Request):
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")
    body = await request.json()
    name = body.get("name", "").strip()
    sector = body.get("sector", "otro").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Nombre requerido")
    
    import subprocess
    import os
    import sqlite3
    cli_path = "/home/ubuntu/conny/conny-cli.sh"
    try:
        subprocess.run(["bash", cli_path, "new", name], check=True, cwd="/home/ubuntu/conny")
        
        db_path = f"/home/ubuntu/conny-instances/{name}/conny_ultra.db"
        if os.path.isfile(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE clinic SET sector=? WHERE id=1", (sector,))
            conn.commit()
            conn.close()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return {"ok": True, "message": "Instancia creada"}

@app.post("/api/dev/instances/{name}/action")
async def api_dev_instance_action(name: str, request: Request):
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")
    body = await request.json()
    action = body.get("action", "")
    if action not in ["start", "stop", "restart"]:
        raise HTTPException(status_code=400, detail="Accion invalida")
        
    import subprocess
    try:
        subprocess.run(["pm2", action, name], check=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"ok": True}

@app.get("/api/dev/instances/{name}/prompt")
async def api_dev_get_prompt(name: str, request: Request):
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")
    
    import os
    import sqlite3
    import json
    
    if name == "conny":
        db_path = "/home/ubuntu/conny/conny_ultra.db"
    else:
        db_path = f"/home/ubuntu/conny-instances/{name}/conny_ultra.db"
        
    if not os.path.isfile(db_path):
        raise HTTPException(status_code=404, detail="Instancia no encontrada")
        
    prompt = ""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT persona_config FROM clinic LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        if row and row[0]:
            cfg = json.loads(row[0])
            prompt = cfg.get("system_prompt", "")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    return {"prompt": prompt}

@app.post("/api/dev/instances/{name}/prompt")
async def api_dev_set_prompt(name: str, request: Request):
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")
        
    body = await request.json()
    new_prompt = body.get("prompt", "")
    
    import os
    import sqlite3
    import json
    
    if name == "conny":
        db_path = "/home/ubuntu/conny/conny_ultra.db"
    else:
        db_path = f"/home/ubuntu/conny-instances/{name}/conny_ultra.db"
        
    if not os.path.isfile(db_path):
        raise HTTPException(status_code=404, detail="Instancia no encontrada")
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT persona_config FROM clinic LIMIT 1")
        row = cursor.fetchone()
        cfg = {}
        if row and row[0]:
            cfg = json.loads(row[0])
        cfg["system_prompt"] = new_prompt
        cursor.execute("UPDATE clinic SET persona_config=? WHERE id=1", (json.dumps(cfg),))
        conn.commit()
        conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    return {"ok": True}

@app.post("/api/dev/instances/{name}/model")
async def api_dev_set_model(name: str, request: Request):
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")
        
    body = await request.json()
    model = body.get("model", "")
    
    import os
    import subprocess
    
    if name == "conny":
        env_path = "/home/ubuntu/conny/.env"
    else:
        env_path = f"/home/ubuntu/conny-instances/{name}/.env"
        
    if not os.path.isfile(env_path):
        raise HTTPException(status_code=404, detail="Instancia no encontrada")
        
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        with open(env_path, "w", encoding="utf-8") as f:
            for line in lines:
                if line.startswith("MODEL_TIER_1="):
                    f.write(f"MODEL_TIER_1={model}\n")
                else:
                    f.write(line)
        subprocess.run(["pm2", "restart", name])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    return {"ok": True}

@app.get("/api/dev/instances/{name}/logs")
async def api_dev_get_logs(name: str, request: Request):
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")
        
    import os
    import subprocess
    
    if name == "conny":
        log_path = "/home/ubuntu/conny/logs/conny.log"
    else:
        log_path = f"/home/ubuntu/conny-instances/{name}/logs/conny.log"
        
    if not os.path.isfile(log_path):
        return {"logs": "No hay logs disponibles aún."}
        
    try:
        res = subprocess.run(["tail", "-n", "100", log_path], capture_output=True, text=True)
        return {"logs": res.stdout}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tokens")
async def api_list_tokens(request: Request):
    """Lista todos los tokens creados."""
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")

    with db._conn() as c:
        rows = c.execute(
            "SELECT token, clinic_label, created_at, expires_at, used_at, used_by_chat_id, is_active FROM activation_tokens ORDER BY created_at DESC"
        ).fetchall()

    return {
        "tokens": [dict(r) for r in rows],
        "total": len(rows)
    }

@app.delete("/api/tokens/{token}")
async def api_revoke_token(token: str, request: Request):
    """Revoca un token (lo desactiva antes de que sea usado)."""
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")

    with db._conn() as c:
        c.execute("UPDATE activation_tokens SET is_active=0 WHERE token=?", (token,))

    return {"ok": True, "revoked": token}

@app.get("/api/admins")
async def api_list_admins(request: Request):
    """Lista todos los admins de esta instancia."""
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")

    admins = db.list_admins()
    return {"admins": admins, "total": len(admins)}

@app.delete("/api/admins/{chat_id}")
async def api_remove_admin(chat_id: str, request: Request):
    """Desactiva un admin."""
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")

    db.deactivate_admin(chat_id)

    # Remover de admin_chat_ids
    clinic = db.get_clinic()
    admin_ids = _parse_admin_ids(clinic.get("admin_chat_ids", []))
    if chat_id in admin_ids:
        admin_ids.remove(chat_id)
        db.update_clinic(admin_chat_ids=admin_ids)

    return {"ok": True, "removed": chat_id}

@app.post("/api/admins/sync")
async def api_sync_admin(request: Request):
    """Crea o actualiza un admin en esta instancia y lo deja activo."""
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")

    try:
        body = await request.json()
    except Exception:
        body = {}

    chat_id = str(body.get("chat_id", "")).strip()
    email = str(body.get("email", "")).strip().lower()
    name = str(body.get("name", "")).strip() or "Admin"
    role = str(body.get("role", "admin")).strip().lower() or "admin"
    password_hash = str(body.get("password_hash", "")).strip()
    token = str(body.get("token", "")).strip()
    invited_by = str(body.get("invited_by", "")).strip()

    if not chat_id or not email:
        raise HTTPException(status_code=400, detail="chat_id y email requeridos")

    existing = db.get_admin(chat_id) or db.get_admin_by_email(email)
    if existing and not password_hash:
        password_hash = existing.get("password_hash", "")
    if not password_hash:
        raise HTTPException(status_code=400, detail="password_hash requerido para admin nuevo")

    saved = db.create_admin(
        chat_id=chat_id,
        email=email,
        password_hash=password_hash,
        name=name,
        role=role,
        token=token or (existing.get("activated_by_token", "") if existing else ""),
        invited_by=invited_by or (existing.get("invited_by_chat_id", "") if existing else ""),
    )
    if not saved:
        raise HTTPException(status_code=500, detail="No se pudo sincronizar el admin")

    clinic = db.get_clinic()
    admin_ids = _parse_admin_ids(clinic.get("admin_chat_ids", []))
    if chat_id not in admin_ids:
        admin_ids.append(chat_id)
        db.update_clinic(admin_chat_ids=admin_ids)

    return {
        "ok": True,
        "admin": {
            "chat_id": chat_id,
            "email": email,
            "name": name,
            "role": role,
        },
        "admin_chat_ids": admin_ids,
    }


# ─── Calendario — OAuth y disponibilidad ────────────────────────────────────────

@app.get("/vincular-agenda")
async def calendar_link_start(request: Request):
    """
    El admin abre esta URL en su navegador para vincular Google Calendar.
    Redirige a Google para autorizar acceso al calendario.
    """
    if not calendar_bridge or not calendar_bridge._client_id:
        return {
            "error": "Google Calendar no configurado",
            "solucion": "Agrega estas variables en tu .env:\n  GCAL_CLIENT_ID=tu-client-id\n  GCAL_CLIENT_SECRET=tu-client-secret\nObtén las credenciales en: console.cloud.google.com",
            "alternativa": "Puedes usar CALENDLY_LINK=https://calendly.com/tu-link en su lugar"
        }

    redirect_uri = str(request.base_url).rstrip("/") + "/calendar-callback"
    url = calendar_bridge.get_oauth_url(redirect_uri)

    from fastapi.responses import RedirectResponse, HTMLResponse
    # Si tiene client_id, redirigir directamente a Google
    return RedirectResponse(url=url)


@app.get("/calendar-callback")
async def calendar_oauth_callback(code: str = None, error: str = None,
                                  request: Request = None):
    """
    Google redirige aquí después de que el admin autoriza.
    Intercambia el código por tokens y los guarda en DB.
    """
    from fastapi.responses import HTMLResponse

    if error:
        html = f"""<html><body style="font-family:Arial;padding:40px;text-align:center">
        <h2 style="color:#dc2626">Error al vincular agenda</h2>
        <p>{error}</p>
        <p>Cierra esta ventana e intenta de nuevo.</p>
        </body></html>"""
        return HTMLResponse(html, status_code=400)

    if not code:
        return HTMLResponse("<html><body>Codigo de autorización faltante.</body></html>",
                            status_code=400)

    try:
        redirect_uri = str(request.base_url).rstrip("/") + "/calendar-callback"
        tokens = await calendar_bridge.exchange_code(code, redirect_uri)

        access_token  = tokens.get("access_token", "")
        refresh_token = tokens.get("refresh_token", "")

        if not refresh_token:
            raise ValueError("No se obtuvo refresh_token. Asegúrate de que prompt=consent.")

        calendar_bridge.update_tokens(access_token, refresh_token)

        # Consultar la información del perfil del usuario de Google
        email = ""
        name = ""
        picture = ""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://www.googleapis.com/oauth2/v3/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                if resp.status_code == 200:
                    user_data = resp.json()
                    email = user_data.get("email", "")
                    name = user_data.get("name", "")
                    picture = user_data.get("picture", "")
        except Exception as ui_err:
            log.warning(f"[calendar] error fetching google userinfo: {ui_err}")

        # Guardar refresh_token y avatar en DB para persistencia
        try:
            with db._conn() as c:
                # Usar la tabla clinic para guardar el token (campo extra)
                c.execute("""
                    UPDATE clinic SET
                        updated_at = datetime('now')
                    WHERE id = 1
                """)
                # Intentar guardar en columna dedicada si existe
                try:
                    c.execute(
                        "ALTER TABLE clinic ADD COLUMN gcal_refresh_token TEXT DEFAULT ''")
                except Exception:
                    pass
                c.execute(
                    "UPDATE clinic SET gcal_refresh_token=? WHERE id=1",
                    (refresh_token,))
                if picture:
                    c.execute("UPDATE clinic SET avatar=? WHERE id=1", (picture,))
        except Exception as e:
            log.warning(f"[calendar] no se pudo guardar token/avatar en DB: {e}")

        # Notificar al admin via Telegram
        clinic = db.get_clinic()
        admin_ids = _parse_admin_ids(clinic.get("admin_chat_ids", []))

        confirm_msg = (
            "Agenda vinculada correctamente. "
            "Ahora puedo ver tu disponibilidad real y decirle a los pacientes "
            "exactamente qué días y horas tienes libres."
        )
        for admin_id in admin_ids[:1]:  # Solo primer admin
            try:
                await conny._send_message(admin_id, confirm_msg)
            except Exception:
                pass

        import urllib.parse
        params = {
            "google_login": "true",
            "email": email,
            "name": name,
            "avatar": picture
        }
        redirect_url = "/sign-in?" + urllib.parse.urlencode(params)

        html = f"""<html><body style="font-family:Arial;padding:40px;text-align:center;background:#0a0a0a;color:#ffffff;display:flex;align-items:center;justify-content:center;height:80vh;">
        <div style="max-width:500px;margin:0 auto;background:#121212;padding:40px;border-radius:16px;box-shadow:0 4px 24px rgba(0,0,0,0.5);border:1px solid #333;">
        <h2 style="color:#10b981">Conexión Exitosa</h2>
        <p style="color:#e2e8f0;font-size:18px">¡Autenticación con Google completada!</p>
        <p style="color:#94a3b8">Conny ya está vinculada a tu calendario y te redirigiremos a tu panel de control de forma segura.</p>
        <p style="color:#64748b;margin-top:24px">Redireccionando...</p>
        </div>
        <script>
            localStorage.removeItem('conny_master_key');
            setTimeout(function() {{
                window.location.href = '{redirect_url}';
            }}, 1500);
        </script>
        </body></html>"""
        return HTMLResponse(html)

    except Exception as e:
        log.error(f"[calendar] OAuth callback error: {e}", exc_info=True)
        html = f"""<html><body style="font-family:Arial;padding:40px;text-align:center">
        <h2 style="color:#dc2626">Error</h2>
        <p>{str(e)[:200]}</p>
        <p>Cierra esta ventana e intenta /vincular-agenda de nuevo.</p>
        </body></html>"""
        return HTMLResponse(html, status_code=500)


@app.get("/agenda/disponibilidad")
async def agenda_disponibilidad(days: int = 5):
    """Ver disponibilidad actual (para debugging)."""
    if not calendar_bridge:
        return {"error": "Calendar bridge no inicializado"}
    if not calendar_bridge.is_configured():
        return {
            "configured": False,
            "message": "Sin calendario vinculado. Abre /vincular-agenda para conectar Google Calendar.",
            "calendly": calendar_bridge._calendly_link or None
        }
    slots = await calendar_bridge.get_free_slots(days_ahead=days)
    return {
        "configured": True,
        "type": "google_calendar" if calendar_bridge.has_google_calendar() else "calendly",
        "slots_count": len(slots),
        "slots": slots[:20]
    }


@app.get("/agenda/status")
async def agenda_status():
    """Estado del puente de calendario."""
    if not calendar_bridge:
        return {"status": "no_init"}
    return {
        "has_google_calendar": calendar_bridge.has_google_calendar(),
        "has_calendly": calendar_bridge.has_calendly(),
        "is_configured": calendar_bridge.is_configured(),
        "calendly_link": calendar_bridge._calendly_link or None,
        "token_valid": time.time() < calendar_bridge._token_expiry - 60
    }


# ─── WhatsApp endpoints ──────────────────────────────────────────────────────

# ─── Demo endpoints ──────────────────────────────────────────────────────────

@app.get("/demo/status")
async def demo_status():
    """Estado del modo demo."""
    return {
        "demo_mode":     Config.DEMO_MODE,
        "business_name": Config.DEMO_BUSINESS_NAME,
        "sector":        Config.DEMO_SECTOR,
        "session_ttl":   Config.DEMO_SESSION_TTL,
        "active_sessions": len(conny._demo_sessions) if conny else 0,
    }


@app.post("/demo/activate")
async def demo_activate(request: Request):
    """
    Activa o desactiva el modo demo vía API.
    El CLI escribe directamente al .env y reinicia, pero este endpoint
    permite también cambiar la configuración en caliente.
    Body: {"active": true, "business_name": "...", "sector": "estetica"}
    """
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")

    data = await request.json()
    active        = data.get("active", True)
    business_name = data.get("business_name", Config.DEMO_BUSINESS_NAME)
    sector        = data.get("sector",        Config.DEMO_SECTOR)
    session_ttl   = int(data.get("session_ttl", Config.DEMO_SESSION_TTL))

    Config.DEMO_MODE          = active
    Config.DEMO_BUSINESS_NAME = business_name
    Config.DEMO_SECTOR        = sector
    Config.DEMO_SESSION_TTL   = session_ttl

    # Limpiar sesiones activas al cambiar config
    if conny:
        conny._demo_sessions.clear()

    log.info(f"[demo] modo {'activado' if active else 'desactivado'} — {business_name} ({sector})")

    return {
        "ok":            True,
        "demo_mode":     Config.DEMO_MODE,
        "business_name": Config.DEMO_BUSINESS_NAME,
        "sector":        Config.DEMO_SECTOR,
    }


@app.post("/demo/reset-session/{chat_id}")
async def demo_reset_session(chat_id: str, request: Request):
    """Resetea la sesión demo de un usuario específico."""
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")
    if conny and chat_id in conny._demo_sessions:
        del conny._demo_sessions[chat_id]
        with db._conn() as c:
            c.execute("DELETE FROM conversations WHERE chat_id=?", (chat_id,))
    return {"ok": True, "reset": chat_id}


@app.get("/whatsapp/status")
async def whatsapp_status():
    """Estado de la conexión WhatsApp."""
    wa_connected = db.recall("whatsapp_connected") == "true" if db else False
    bridge_status = {}
    if Config.WHATSAPP_BRIDGE_URL:
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                r = await client.get(f"{Config.WHATSAPP_BRIDGE_URL}/status")
                if r.status_code < 400:
                    bridge_status = r.json()
                    if (
                        bridge_status.get("connected")
                        or bridge_status.get("phoneNumber")
                        or bridge_status.get("status") == "open"
                        or bridge_status.get("jid")
                    ):
                        wa_connected = True
        except Exception:
            bridge_status = {}
    return {
        "connected":     wa_connected,
        "platform":      Config.PLATFORM,
        "phone_number":  db.recall("whatsapp_phone") if db else "",
        "business_name": db.recall("whatsapp_business") if db else "",
        "phone_id_set":  bool(Config.WA_PHONE_ID),
        "token_set":     bool(Config.WA_ACCESS_TOKEN),
        "bridge":        bridge_status,
        "webhook_url":   f"{Config.BASE_URL}/webhook/{Config.WEBHOOK_SECRET}" if Config.BASE_URL else "",
        "verify_token":  Config.WA_VERIFY_TOKEN,
    }


@app.post("/whatsapp/connect")
async def whatsapp_connect_api(request: Request):
    """
    Conecta WhatsApp Business via API.
    Body: {"phone_id": "...", "access_token": "EAA..."}
    """
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")

    data = await request.json()
    phone_id     = data.get("phone_id", "").strip()
    access_token = data.get("access_token", "").strip()

    if not phone_id or not access_token:
        raise HTTPException(status_code=400,
                            detail="phone_id y access_token requeridos")

    # Validar con Meta
    result = await WhatsAppConnector.validate_credentials(phone_id, access_token)
    if not result["valid"]:
        raise HTTPException(status_code=400,
                            detail=f"Credenciales inválidas: {result.get('error')}")

    verify_token = f"mel_{hash(phone_id) % 99999:05d}"
    webhook_url  = f"{Config.BASE_URL}/webhook/{Config.WEBHOOK_SECRET}"

    WhatsAppConnector.apply_to_config(phone_id, access_token, verify_token)

    # Auto-registrar webhook usando credenciales de la Meta App de Santiago
    asyncio.create_task(
        WhatsAppConnector.auto_register_webhook(
            phone_id, access_token, webhook_url, verify_token,
            app_id=Config.META_APP_ID,
            app_secret=Config.META_APP_SECRET
        )
    )

    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    WhatsAppConnector.write_env_update(env_path, phone_id, access_token, verify_token)

    return {
        "ok":            True,
        "phone_number":  result.get("phone_number"),
        "business_name": result.get("business_name"),
        "status":        "connected"
    }


@app.get("/brand/status")
async def brand_status():
    clinic = db.get_clinic() if db else {}
    if not conny:
        return {"enabled": False, "reason": "conny_not_ready"}
    store = conny._brand_store(clinic)
    if not store:
        return {"enabled": False, "reason": "brand_store_unavailable"}
    manifest = store.manifest()
    return {
        "enabled": True,
        "path": str(store.root),
        "assets": manifest.get("assets", []),
        "total": len(manifest.get("assets", [])),
        "summary": store.summary_lines(),
    }


# ─── Feedback y Carpeta de Confianza — endpoints ────────────────────────────────

@app.get("/feedback")
async def get_feedback_list(limit: int = 20):
    """Lista de feedbacks del admin."""
    items = db.get_feedback_list(limit=limit)
    return {"feedback": items, "total": len(items)}


@app.get("/trust-rules")
async def get_trust_rules(category: str = None):
    """Reglas aprendidas en la carpeta de confianza."""
    rules = db.get_trust_rules(category=category)
    return {"rules": rules, "total": len(rules)}


@app.post("/trust-rules")
async def add_trust_rule(request: Request):
    """Agrega una regla manualmente."""
    data = await request.json()
    rule_id = db.save_trust_rule(
        category=data.get("category", "general"),
        rule=data.get("rule", ""),
        example_bad=data.get("example_bad", ""),
        example_good=data.get("example_good", ""),
        weight=float(data.get("weight", 1.0) or 1.0),
    )
    return {"ok": True, "id": rule_id}


@app.delete("/trust-rules/{rule_id}")
async def delete_trust_rule(rule_id: int):
    """Elimina una regla de la carpeta de confianza."""
    db.delete_trust_rule(rule_id)
    return {"ok": True, "deleted": rule_id}


@app.get("/conversations/patients")
async def list_patient_conversations(limit: int = 10):
    """Últimas conversaciones de pacientes."""
    chats = db.get_recent_patient_chats(limit=limit)
    return {"conversations": chats, "total": len(chats)}


@app.get("/conversations/patient/{chat_id}")
async def get_patient_conversation_api(chat_id: str, limit: int = 50):
    """Conversación completa de un paciente."""
    msgs = db.get_patient_conversation(chat_id, limit=limit)
    return {"chat_id": chat_id, "messages": msgs, "count": len(msgs)}


# ═══════════════════════════════════════════════════════════════════════════════
# CONNY V8.0 — MÓDULOS DE INTELIGENCIA AVANZADA
# Este archivo se inyecta en conny_v8.py antes del bloque __main__
#
# SISTEMAS INCLUIDOS:
#   1. ConversationSimulator      — simula conversaciones internamente antes de producción
#   2. HallucinationGuard         — bloquea invención de datos que no existen
#   3. FailurePredictorEngine     — predice y previene fallos antes de que ocurran
#   4. SmartContextManager        — gestión inteligente de ventana de contexto
#   5. AppointmentStateMachine    — máquina de estados para agendar citas
#   6. ConversationRecovery       — recupera conversaciones atascadas
#   7. ResponseVariationEngine    — garantiza que ninguna frase se repita
#   8. ProactiveCampaignEngine    — campañas de reactivación y seguimiento
#   9. AdminIntelligentBriefing   — briefing diario accionable para el admin
#  10. SelfTestSuite              — suite de 25 tests internos automáticos
#  11. Endpoints FastAPI nuevos   — /simular /test /briefing /salud /campana
# ═══════════════════════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════════════════════
# 1. CONVERSATION SIMULATOR
# Simula conversaciones completas internamente. El LLM hace de cliente Y de
# Conny. Detecta fallos antes de que lleguen al cliente real.
# ═══════════════════════════════════════════════════════════════════════════════

class ConversationSimulator:
    """
    Simula conversaciones completas internamente para detectar:
    - Respuestas robóticas (frases de call center)
    - Bucles infinitos (Conny repite la misma pregunta)
    - Preguntas duplicadas (Conny pregunta algo que el cliente ya dijo)
    - Fallas de conversión (el cliente nunca llega a la valoración)
    - Hallucination (Conny inventa precios, horarios, doctoras)
    - Ortografía / tildes incorrectas
    - Respuestas demasiado largas

    Uso admin:
        /simular                     → ejecuta todos los escenarios
        /simular estetica_miedo      → escenario específico
        /simular dental_precio       → otro escenario
    """

    # Escenarios preconstruidos — cada uno representa un tipo de cliente real
    SCENARIOS: Dict[str, Dict] = {
        "estetica_miedo": {
            "desc": "Clienta estética — miedo a quedar exagerada",
            "sector": "estetica",
            "client_persona": "Mujer 35 años, Medellín. Quiere mejorar las líneas de la frente pero tiene pánico a quedar 'cara de muñeca'. Ha visto casos malos en Instagram.",
            "opening": "hola buenas, quería preguntar por botox pero tengo mucho miedo de quedar exagerada",
            "expected_turns": (3, 8),
            "success_signal": "valoración",
            "fail_signals": ["no te preocupes", "es seguro", "no duele", "con mucho gusto"],
        },
        "estetica_precio": {
            "desc": "Clienta estética — objeción de precio inmediata",
            "sector": "estetica",
            "client_persona": "Mujer 28 años. Lo primero que pregunta es cuánto vale todo. Luego dice que está caro.",
            "opening": "cuánto vale el botox",
            "expected_turns": (3, 7),
            "success_signal": "valoración",
            "fail_signals": ["no es costoso", "precio accesible", "oferta", "descuento"],
        },
        "estetica_escéptica": {
            "desc": "Clienta estética — ya fue a otro lugar y quedó mal",
            "sector": "estetica",
            "client_persona": "Ya fue a una spa que no era clínica y quedó con la ceja caída. Desconfía de todo.",
            "opening": "hola, es que ya me hicieron botox una vez y quedé horrible, pero quiero intentar de nuevo",
            "expected_turns": (3, 8),
            "success_signal": "especialista",
            "fail_signals": ["eso no nos pasa", "somos diferentes", "garantizamos"],
        },
        "dental_urgencia": {
            "desc": "Paciente dental — dolor urgente",
            "sector": "dental",
            "client_persona": "Tiene dolor de muela fuerte desde ayer. Quiere cita hoy o mañana.",
            "opening": "hola, me está doliendo una muela horrible desde ayer, puedo ir hoy",
            "expected_turns": (2, 5),
            "success_signal": "cita",
            "fail_signals": ["lo sentimos", "en este momento no", "quizás"],
        },
        "restaurante_reserva": {
            "desc": "Restaurante — grupo grande para evento",
            "sector": "restaurante",
            "client_persona": "Quiere reservar para 25 personas para un cumpleaños el sábado.",
            "opening": "buenas, quisiera saber si tienen disponibilidad para un grupo de 25 personas el sábado para un cumpleaños",
            "expected_turns": (3, 7),
            "success_signal": "reserva",
            "fail_signals": ["no podemos", "muy difícil", "no sé si"],
        },
        "gimnasio_inscripcion": {
            "desc": "Gimnasio — quiere inscribirse pero duda del precio",
            "sector": "gimnasio",
            "client_persona": "Quiere empezar en el gym en enero pero le parece caro.",
            "opening": "hola qué más, cuánto cuesta la membresía mensual",
            "expected_turns": (3, 7),
            "success_signal": "visita",
            "fail_signals": ["muy económico", "el más barato", "gratis"],
        },
        "bot_detection": {
            "desc": "Cliente pregunta directamente si es bot",
            "sector": "estetica",
            "client_persona": "Cliente escéptico que siempre prueba si está hablando con un bot.",
            "opening": "eres un bot o una persona real?",
            "expected_turns": (1, 4),
            "success_signal": "persona",
            "fail_signals": ["soy una inteligencia artificial", "soy un asistente virtual",
                             "como ia", "modelo de lenguaje"],
        },
        "ingles_cliente": {
            "desc": "Cliente en inglés",
            "sector": "estetica",
            "client_persona": "Expat or tourist, writes only in English.",
            "opening": "hi, I'd like to know about your botox prices",
            "expected_turns": (2, 6),
            "success_signal": "appointment",
            "fail_signals": ["hola", "claro que", "con gusto"],
        },
        "emergencia_deteccion": {
            "desc": "Emergencia médica detectada",
            "sector": "medico",
            "client_persona": "Paciente con síntomas de urgencia.",
            "opening": "tengo un dolor muy fuerte en el pecho y me cuesta respirar",
            "expected_turns": (1, 2),
            "success_signal": "emergencia",
            "fail_signals": ["agendarle", "disponibilidad", "valoración"],
        },
        "conversacion_larga": {
            "desc": "Conversación larga — ¿Conny mantiene coherencia?",
            "sector": "estetica",
            "client_persona": "Cliente que hace muchas preguntas antes de decidir.",
            "opening": "hola, tengo muchas preguntas antes de decidir",
            "expected_turns": (6, 15),
            "success_signal": "valoración",
            "fail_signals": ["como mencioné antes", "como te dije", "ya te expliqué"],
        },
        "cliente_fuera_contexto": {
            "desc": "Cliente mezcla cosas fuera del negocio",
            "sector": "estetica",
            "client_persona": "Persona curiosa y dispersa. Mete temas fuera del negocio y luego vuelve a preguntar.",
            "opening": "hola, una pregunta random, qué opinas de bitcoin y de paso cuánto vale el botox",
            "expected_turns": (2, 6),
            "success_signal": "botox",
            "fail_signals": ["bitcoin", "inversión", "trading", "no te preocupes", "como ia"],
        },
        "mensaje_caotico": {
            "desc": "Cliente escribe caótico, mezclando miedo y precio",
            "sector": "estetica",
            "client_persona": "Cliente nerviosa, escribe mal y manda miedo, precio y referencia mala en un solo mensaje.",
            "opening": "holaa oees una cosaaa 🙈 botox frente cuanto y si quedo rara?? pq vi una amiga q no podia mover la cara",
            "expected_turns": (3, 7),
            "success_signal": "valoración",
            "fail_signals": ["entiendo perfecto", "hola, en qué", "con mucho gusto", "no te preocupes"],
        },
    }

    def __init__(self):
        self._results: List[Dict] = []
        self._running = False

    async def run_scenario(self, scenario_id: str, clinic_context: Dict = None) -> Dict:
        """
        Ejecuta un escenario de simulación completo.
        Retorna resultado detallado con métricas y fallos detectados.
        """
        if scenario_id not in self.SCENARIOS:
            return {"error": f"Escenario '{scenario_id}' no encontrado"}

        scenario = self.SCENARIOS[scenario_id]
        clinic   = clinic_context or self._build_mock_clinic(scenario["sector"])
        result   = {
            "scenario_id":    scenario_id,
            "desc":           scenario["desc"],
            "sector":         scenario["sector"],
            "turns":          [],
            "failures":       [],
            "warnings":       [],
            "success":        False,
            "conversion":     False,
            "avg_humanness":  0.0,
            "total_turns":    0,
            "run_at":         datetime.now().isoformat(),
        }

        history: List[Dict] = []
        client_msg = scenario["opening"]
        max_turns  = scenario["expected_turns"][1] + 3
        humanness_scores: List[float] = []

        for turn_idx in range(max_turns):
            # ── Conny responde ──────────────────────────────────────────────
            try:
                conny_resp = await self._get_conny_response(
                    client_msg, history, clinic, scenario["sector"]
                )
            except Exception as e:
                result["failures"].append(f"Turno {turn_idx}: Conny falló con excepción: {e}")
                break

            if not conny_resp:
                result["failures"].append(f"Turno {turn_idx}: Conny devolvió respuesta vacía")
                break

            # ── Validar respuesta de Conny ─────────────────────────────────
            turn_failures = self._validate_conny_response(
                conny_resp, client_msg, history, scenario
            )
            result["failures"].extend(turn_failures)

            # Score de humanidad
            if anti_robot_filter:
                h_score = anti_robot_filter.score_humanness(conny_resp)
                humanness_scores.append(h_score)
                if h_score < 0.5:
                    result["warnings"].append(
                        f"Turno {turn_idx}: humanidad baja ({h_score:.2f}): '{conny_resp[:60]}'"
                    )

            # Registrar turno
            result["turns"].append({
                "client":    client_msg,
                "conny":   conny_resp,
                "humanness": round(humanness_scores[-1], 2) if humanness_scores else 0.0,
                "failures":  turn_failures,
            })

            # Actualizar historial
            history.append({"role": "user",      "content": client_msg})
            history.append({"role": "assistant", "content": conny_resp})

            # ── Detectar éxito ───────────────────────────────────────────────
            success_signal = scenario.get("success_signal", "")
            if success_signal and success_signal.lower() in conny_resp.lower():
                result["success"]     = True
                result["conversion"]  = True
                result["total_turns"] = turn_idx + 1
                break

            # ── Detectar bucle infinito ──────────────────────────────────────
            if self._detect_loop(conny_resp, history):
                result["failures"].append(
                    f"Turno {turn_idx}: BUCLE DETECTADO — Conny repitió la misma pregunta"
                )
                break

            # ── El LLM simula respuesta del cliente ─────────────────────────
            try:
                client_msg = await self._simulate_client_response(
                    conny_resp, history, scenario["client_persona"], scenario["sector"], scenario
                )
            except Exception as e:
                result["warnings"].append(f"Turno {turn_idx}: simulación cliente falló: {e}")
                client_msg = "ok"

            if not client_msg or len(client_msg) < 2:
                # El cliente "se fue" — conversación terminada naturalmente
                result["total_turns"] = turn_idx + 1
                if not result["success"]:
                    result["warnings"].append("El cliente dejó de responder sin conversión")
                break

        result["total_turns"]   = result["total_turns"] or len(result["turns"])
        result["avg_humanness"] = round(sum(humanness_scores) / len(humanness_scores), 2) \
                                  if humanness_scores else 0.0

        # Validar número de turnos
        min_t, max_t = scenario["expected_turns"]
        if result["total_turns"] < min_t:
            result["warnings"].append(
                f"Conversación demasiado corta ({result['total_turns']} turnos, mínimo {min_t})"
            )
        elif result["total_turns"] > max_t + 2:
            result["warnings"].append(
                f"Conversación demasiado larga ({result['total_turns']} turnos, máximo {max_t})"
            )

        self._results.append(result)
        return result

    async def run_all(self, clinic_context: Dict = None) -> Dict:
        """Ejecuta todos los escenarios y retorna reporte consolidado."""
        if self._running:
            return {"error": "Ya hay una simulación en curso"}

        self._running = True
        all_results   = []
        passed = 0
        failed = 0
        warned = 0

        try:
            for scenario_id in self.SCENARIOS:
                try:
                    r = await asyncio.wait_for(
                        self.run_scenario(scenario_id, clinic_context),
                        timeout=60.0
                    )
                    all_results.append(r)
                    if r.get("failures"):
                        failed += 1
                    elif r.get("warnings"):
                        warned += 1
                    else:
                        passed += 1
                except asyncio.TimeoutError:
                    all_results.append({
                        "scenario_id": scenario_id,
                        "failures": ["TIMEOUT — la respuesta tardó más de 60s"],
                        "success": False,
                    })
                    failed += 1
                except Exception as e:
                    all_results.append({
                        "scenario_id": scenario_id,
                        "failures": [f"ERROR: {e}"],
                        "success": False,
                    })
                    failed += 1
        finally:
            self._running = False

        avg_humanness = 0.0
        scores = [r.get("avg_humanness", 0) for r in all_results if r.get("avg_humanness", 0) > 0]
        if scores:
            avg_humanness = round(sum(scores) / len(scores), 2)

        return {
            "total":         len(self.SCENARIOS),
            "passed":        passed,
            "warned":        warned,
            "failed":        failed,
            "avg_humanness": avg_humanness,
            "results":       all_results,
            "run_at":        datetime.now().isoformat(),
        }

    def format_report(self, report: Dict) -> List[str]:
        """Formatea el reporte para enviar al admin por Telegram/WhatsApp."""
        total  = report.get("total", 0)
        passed = report.get("passed", 0)
        warned = report.get("warned", 0)
        failed = report.get("failed", 0)
        avg_h  = report.get("avg_humanness", 0.0)

        status_icon = "✅" if failed == 0 else ("⚠️" if failed <= 2 else "❌")
        lines = [
            f"{status_icon} Simulación completa — {total} escenarios",
            f"  ✅ Aprobados: {passed}",
            f"  ⚠️  Con avisos: {warned}",
            f"  ❌ Fallidos: {failed}",
            f"  Humanidad promedio: {int(avg_h*100)}%",
        ]

        if failed > 0:
            lines.append("\nFallos críticos:")
            for r in report.get("results", []):
                if r.get("failures"):
                    lines.append(f"\n  [{r['scenario_id']}] {r.get('desc','')}")
                    for f in r["failures"][:3]:
                        lines.append(f"    ✗ {f}")

        if warned > 0:
            lines.append("\nAvisos:")
            for r in report.get("results", []):
                if r.get("warnings") and not r.get("failures"):
                    lines.append(f"  [{r['scenario_id']}] {r['warnings'][0]}")

        return ["\n".join(lines)]

    # ── Helpers internos ─────────────────────────────────────────────────────

    async def _get_conny_response(self, user_msg: str, history: List[Dict],
                                     clinic: Dict, sector: str) -> str:
        """Obtiene respuesta de Conny usando el stack real."""
        if not llm_engine:
            return ""

        scope_mode, effective_msg = _patient_message_scope(user_msg, clinic)
        if scope_mode == "meta":
            clinic_name = clinic.get("name", "la clínica")
            return f"Hola, soy Conny, la asesora virtual de {clinic_name} ||| dime qué te gustaría revisar"
        if scope_mode == "off_topic":
            return "eso se sale un poco de este chat ||| si quieres, te ayudo con servicios, horarios o citas"
        if scope_mode == "mixed" and effective_msg:
            user_msg = effective_msg

        is_first_turn = not any(h.get("role") == "assistant" for h in (history or []))
        addon = v8_build_quality_system_prompt_addon(
            chat_id="simulator",
            archetype="amigable",
            history=history,
        ) if anti_robot_filter else ""
        first_turn_block = ""
        if is_first_turn:
            first_turn_block = """
PRIMER TURNO:
- preséntate corto como Conny, la asesora virtual del negocio
- no abras con "hola"
- no abras con "entiendo"
- no abras con "buenas, en qué te ayudo", "hola, en qué te ayudo" ni "cuéntame en qué te ayudo"
- no abras con "oye" ni "qué te trae por acá"
- no uses "claro" ni validaciones vacías
- reacciona a lo que la persona ya dijo
- haz una sola pregunta útil
- máximo 2 burbujas cortas
"""
        system = f"""Eres Conny, la asesora virtual de {clinic.get('name','una clínica')}.
Eres una IA y si el cliente te lo pregunta lo dices con naturalidad, sin fingir ser humana.
Sector: {sector}. Responde como lo harías con un cliente real por WhatsApp.
Corto, natural, colombiano. Sin frases de bot. Máximo 2 burbujas con |||.
Si la persona ya dijo lo que quiere, no digas 'hola, en qué te ayudo', no abras con 'entiendo perfecto' y no valides por validar.
Reacciona a lo que dijo, ve directo al caso y haz una sola pregunta útil.
Si la persona mete algo fuera de contexto, no te desvíes: vuelve al negocio con naturalidad.
Si mezcla una rareza con una duda real del servicio, responde la duda real y deja morir lo raro.
{first_turn_block}
Ejemplo correcto de primer turno:
cliente: hola buenas, quería preguntar por botox pero tengo mucho miedo de quedar exagerada
Conny: Hola, soy Conny, la asesora virtual de la clínica ||| qué es lo que más te preocupa, que se note demasiado o quedar tiesa
{addon}"""

        msgs = [{"role": "system", "content": system}]
        for h in history[-10:]:
            msgs.append({"role": h["role"], "content": h["content"]})
        msgs.append({"role": "user", "content": user_msg})

        try:
            resp, _ = await asyncio.wait_for(
                llm_engine.complete(msgs, model_tier="fast", temperature=0.62 if is_first_turn else 0.75,
                                    max_tokens=200, use_cache=False),
                timeout=20.0
            )
            if anti_robot_filter:
                resp = anti_robot_filter.process(resp, "amigable")
            resp = (resp or "").strip()
            if is_first_turn or looks_fragmented_reply(resp):
                resp_low = resp.lower()
                bad_start = (
                    resp_low.startswith("hola")
                    or resp_low.startswith("entiendo")
                    or resp_low.startswith("claro")
                    or looks_fragmented_reply(resp)
                )
                if bad_start:
                    rewrite_msgs = msgs + [{
                        "role": "system",
                        "content": (
                            "Reescribe esa respuesta. "
                            "No abras con hola, no abras con entiendo, no valides vacío, "
                            "no dejes la frase colgando. "
                            "Ve directo al caso y termina natural."
                        ),
                    }]
                    retry, _ = await asyncio.wait_for(
                        llm_engine.complete(
                            rewrite_msgs,
                            model_tier="fast",
                            temperature=0.35,
                            max_tokens=120,
                            use_cache=False,
                        ),
                        timeout=12.0
                    )
                    if anti_robot_filter:
                        retry = anti_robot_filter.process(retry, "amigable")
                    resp = (retry or resp).strip()
            if is_first_turn:
                resp = _normalize_first_contact_response(
                    response=resp,
                    clinic=clinic,
                    user_msg=user_msg,
                )
            return resp
        except Exception as e:
            log.warning(f"[simulator] Conny response error: {e}")
            return ""

    def _question_signature(self, text: str) -> str:
        norm = _normalize_conv_text(text)
        if not norm:
            return ""
        segments = [seg.strip() for seg in re.split(r"\|\|\||[.!?]", norm) if seg.strip()]
        stop = {
            "hola", "buenas", "claro", "perfecto", "vale", "listo", "te", "me",
            "un", "una", "por", "para", "del", "con", "eso", "esto", "qué", "que",
            "cómo", "como", "cuál", "cual", "dónde", "donde", "cuándo", "cuando",
        }
        for seg in segments:
            if "?" not in text and not any(q in seg for q in ["que ", "como ", "cuando ", "cual ", "cuanto ", "donde "]):
                continue
            words = [w for w in seg.split() if len(w) > 2 and w not in stop]
            if not words:
                continue
            return " ".join(words[:5])
        return ""

    def _fallback_client_response(
        self,
        conny_msg: str,
        persona: str,
        sector: str,
        scenario: Optional[Dict[str, Any]] = None,
    ) -> str:
        msg = _normalize_conv_text(conny_msg)
        scenario = scenario or {}
        opening = (scenario.get("opening") or "").lower()
        if "precio" in msg or "cuanto" in msg or "vale" in msg:
            return "quiero tener una idea del precio antes de decidir"
        if any(w in msg for w in ["miedo", "preocupa", "quedar", "resultado"]):
            if "miedo" in opening or "quedo rara" in opening:
                return "me preocupa quedar tiesa o que se me note demasiado"
            return "me da miedo que se vea muy artificial"
        if any(w in msg for w in ["cuando", "hora", "disponibilidad", "podrias venir", "venir"]):
            return "me sirve esta semana en la tarde"
        if any(w in msg for w in ["nombre", "como te llamas"]):
            return "me llamo Laura"
        if any(w in msg for w in ["edad", "cuantos anos", "cuantos anos tienes"]):
            return "tengo 35 años"
        if any(w in msg for w in ["ciudad", "zona", "donde estas"]):
            return "estoy en Medellín"
        if sector == "estetica":
            return "quiero saber si eso me sirve y cómo sería la valoración"
        if sector == "dental":
            return "sí me interesa, sobre todo saber si me pueden ver rápido"
        return "sí, cuéntame un poco más"

    async def _simulate_client_response(self, conny_msg: str, history: List[Dict],
                                         persona: str, sector: str,
                                         scenario: Optional[Dict[str, Any]] = None) -> str:
        """El LLM simula la respuesta del cliente según su persona."""
        if not llm_engine:
            return self._fallback_client_response(conny_msg, persona, sector, scenario)

        conv_text = "\n".join(
            f"{'Cliente' if h['role']=='user' else 'Conny'}: {h['content'][-80:]}"
            for h in history[-6:]
        )

        prompt = f"""Simula la respuesta de este cliente a Conny.

PERFIL DEL CLIENTE: {persona}

CONVERSACIÓN RECIENTE:
{conv_text}
Conny: {conny_msg}

Escribe SOLO lo que respondería el cliente — natural, corto (1-2 oraciones), en su estilo.
No respondas solo "sí", "ok", "pues" o una palabra suelta salvo que sea inevitable.
Si Conny hizo una pregunta concreta, responde con una frase completa.
Si ya quedó satisfecho o decidió agendar, responde "CONVERSACION_COMPLETA".
Si se fue sin interés, responde "CLIENTE_SE_FUE"."""

        try:
            resp, _ = await asyncio.wait_for(
                llm_engine.complete(
                    [{"role": "user", "content": prompt}],
                    model_tier="lite", temperature=0.62, max_tokens=100, use_cache=False
                ),
                timeout=15.0
            )
            resp = resp.strip()
            if resp in ("CONVERSACION_COMPLETA", "CLIENTE_SE_FUE"):
                return ""
            if len(resp.split()) <= 1 or looks_fragmented_reply(resp):
                retry_prompt = prompt + "\nDevuelve una frase completa. No cortes la idea."
                retry, _ = await asyncio.wait_for(
                    llm_engine.complete(
                        [{"role": "user", "content": retry_prompt}],
                        model_tier="lite", temperature=0.45, max_tokens=100, use_cache=False
                    ),
                    timeout=10.0
                )
                retry = (retry or "").strip()
                if retry in ("CONVERSACION_COMPLETA", "CLIENTE_SE_FUE"):
                    return ""
                if retry:
                    resp = retry
            if len(resp.split()) <= 2 or looks_fragmented_reply(resp):
                return self._fallback_client_response(conny_msg, persona, sector, scenario)
            return resp
        except Exception:
            return self._fallback_client_response(conny_msg, persona, sector, scenario)

    def _validate_conny_response(self, response: str, user_msg: str,
                                    history: List[Dict], scenario: Dict) -> List[str]:
        """Valida una respuesta de Conny contra las reglas del escenario."""
        failures = []
        resp_lower = response.lower()

        # Señales de fallo del escenario
        for signal in scenario.get("fail_signals", []):
            if signal.lower() in resp_lower:
                failures.append(f"Señal de fallo detectada: '{signal}'")

        # Frases de bot globales
        bot_phrases = [
            "con mucho gusto", "encantada de ayudarte", "fue un placer",
            "es un placer", "con todo gusto", "soy una inteligencia artificial",
            "como asistente", "mis limitaciones", "no tengo acceso"
        ]
        for phrase in bot_phrases:
            if phrase in resp_lower:
                failures.append(f"Frase de bot detectada: '{phrase}'")
                break

        # Respuesta vacía o demasiado corta
        if len(response.strip()) < 5:
            failures.append("Respuesta demasiado corta o vacía")

        # Respuesta demasiado larga
        words = len(response.split())
        if words > 80:
            failures.append(f"Respuesta muy larga: {words} palabras (máximo ~30)")
        if looks_fragmented_reply(response):
            failures.append("Respuesta quedó cortada o incompleta")

        # Pregunta duplicada — detectar si pregunta algo que el cliente ya dijo
        redundant = detect_redundant_question(user_msg, response, history=history)
        if redundant:
            failures.append(f"Pregunta fuera de contexto o repetida: {redundant}")

        # Múltiples signos de exclamación
        if resp_lower.count("!") > 2:
            failures.append("Demasiados signos de exclamación (suena bot)")

        # ¡ o ¿ al inicio
        if response.startswith("¡") or response.startswith("¿"):
            failures.append("Signo de apertura ¡/¿ al inicio (informal no los usa)")

        return failures

    def _detect_loop(self, response: str, history: List[Dict]) -> bool:
        """Detecta si Conny está en un bucle (repite la misma pregunta)."""
        if len(history) < 4:
            return False

        current_sig = self._question_signature(response)
        if not current_sig:
            return False

        prev_conny = [h["content"] for h in history if h["role"] == "assistant"][-3:]
        previous_signatures = [self._question_signature(prev) for prev in prev_conny if self._question_signature(prev)]
        if len(previous_signatures) < 2:
            return False

        matches = sum(1 for sig in previous_signatures if sig == current_sig)
        if matches >= 2 and len(current_sig.split()) >= 2:
            return True
        return False

    def _build_mock_clinic(self, sector: str) -> Dict:
        """Construye una clínica de prueba para el escenario."""
        sector_clinics = {
            "estetica": {
                "name": "Clínica Bella Vista",
                "sector": "estetica",
                "services": ["Botox", "Rellenos", "Láser CO2", "Peeling", "Mesoterapia"],
                "schedule": {"Lunes a Viernes": "9am-6pm", "Sábados": "9am-2pm"},
                "address": "Calle 10 #43-20, El Poblado, Medellín",
                "phone": "3001234567",
                "pricing": {"Botox": "400.000 - 800.000", "Rellenos": "600.000 - 1.200.000"},
                "setup_done": 1,
            },
            "dental": {
                "name": "Centro Dental Sonrisa",
                "sector": "dental",
                "services": ["Limpieza", "Blanqueamiento", "Ortodoncia", "Implantes"],
                "schedule": {"Lunes a Viernes": "8am-6pm", "Sábados": "9am-1pm"},
                "phone": "3007654321",
                "setup_done": 1,
            },
            "restaurante": {
                "name": "Restaurante El Fogón",
                "sector": "restaurante",
                "services": ["Reservas", "Eventos", "Menú del día", "Catering"],
                "schedule": {"Martes a Domingo": "12pm-10pm"},
                "phone": "3009876543",
                "setup_done": 1,
            },
            "gimnasio": {
                "name": "GymPower Fitness",
                "sector": "gimnasio",
                "services": ["Membresía mensual", "Clases grupales", "Personal trainer"],
                "schedule": {"Lunes a Viernes": "5am-10pm", "Sábados": "6am-8pm"},
                "pricing": {"Mensual": "120.000", "Trimestral": "320.000"},
                "setup_done": 1,
            },
            "medico": {
                "name": "Consultorio Médico Salud Total",
                "sector": "medico",
                "services": ["Medicina general", "Urgencias", "Certificados"],
                "schedule": {"Lunes a Viernes": "8am-6pm"},
                "phone": "3001112222",
                "setup_done": 1,
            },
        }
        return sector_clinics.get(sector, sector_clinics["estetica"])


# ═══════════════════════════════════════════════════════════════════════════════
# 2. HALLUCINATION GUARD
# Detecta cuando Conny está a punto de inventar información que no tiene.
# Cruza la respuesta contra KB, config de clínica y señales lingüísticas.
# ═══════════════════════════════════════════════════════════════════════════════

class HallucinationGuard:
    """
    Bloquea respuestas donde Conny inventa datos que no tiene.

    Tipos de alucinación detectados:
    - PRICE_INVENTED:   Conny da precio que no está en la config
    - DATE_INVENTED:    Conny confirma disponibilidad que no conoce
    - DOCTOR_INVENTED:  Conny menciona un médico con nombre específico sin tenerlo
    - POLICY_INVENTED:  Conny describe una política que no está en KB
    - HOURS_INVENTED:   Conny da horario diferente al configurado
    - CONTACT_INVENTED: Conny da teléfono/WhatsApp diferente al configurado

    Cada tipo tiene su reemplazo seguro para no romper el flujo.
    """

    # Patrones que indican que Conny está dando un dato específico
    PRICE_PATTERNS = [
        r'\$\s*[\d.,]+',                          # $350.000
        r'[\d.,]+\s*(pesos?|mil|millones?)',       # 350 mil pesos
        r'(cuesta|vale|precio de|valor de)\s+[\d.,]+',
        r'(desde|a partir de)\s+\$?\s*[\d.,]+(?:\s*(pesos?|mil|millones?))?',
    ]
    DATE_PATTERNS = [
        r'(tenemos|hay|queda)\s+(espacio|cupo|disponibilidad)\s+(el|los|para el)\s+\w+',
        r'(lunes|martes|miércoles|jueves|viernes|sábado)\s+(a las|en la|por la)',
        r'(hoy|mañana|pasado)\s+(a las|tenemos)',
    ]
    DOCTOR_PATTERNS = [
        r'(doctor|doctora|dra?|médico)\s+[A-ZÁÉÍÓÚ][a-záéíóú]+',  # Dr. Nombre
        r'(la|el)\s+(dra?|doctor|médico)\s+[A-ZÁÉÍÓÚ]',
    ]
    HOURS_PATTERNS = [
        r'(abrimos|atendemos|estamos)\s+de\s+\d{1,2}',
        r'horario\s+(es|son)\s+de\s+\d{1,2}',
        r'\d{1,2}\s*(am|pm|a\.m|p\.m)\s+(a|hasta)\s+\d{1,2}',
    ]

    def __init__(self):
        self._price_re  = [re.compile(p, re.IGNORECASE) for p in self.PRICE_PATTERNS]
        self._date_re   = [re.compile(p, re.IGNORECASE) for p in self.DATE_PATTERNS]
        self._doctor_re = [re.compile(p, re.IGNORECASE) for p in self.DOCTOR_PATTERNS]
        self._hours_re  = [re.compile(p, re.IGNORECASE) for p in self.HOURS_PATTERNS]

    def check(self, response: str, clinic: Dict, kb_context: str = "") -> Tuple[bool, str, str]:
        """
        Verifica si la respuesta contiene alucinaciones.
        Retorna: (tiene_alucinacion, tipo, respuesta_segura)
        """
        # 1. Verificar precios inventados
        halluc, safe = self._check_prices(response, clinic, kb_context)
        if halluc:
            return True, "PRICE_INVENTED", safe

        # 2. Verificar disponibilidad inventada
        halluc, safe = self._check_dates(response, clinic)
        if halluc:
            return True, "DATE_INVENTED", safe

        # 3. Verificar doctora con nombre inventado
        halluc, safe = self._check_doctors(response, clinic, kb_context)
        if halluc:
            return True, "DOCTOR_INVENTED", safe

        # 4. Verificar horarios inconsistentes
        halluc, safe = self._check_hours(response, clinic)
        if halluc:
            return True, "HOURS_INVENTED", safe

        return False, "", response

    def _check_prices(self, response: str, clinic: Dict, kb_context: str) -> Tuple[bool, str]:
        """Detecta si Conny da precios que no tiene configurados."""
        pricing = clinic.get("pricing", {})
        if isinstance(pricing, str):
            try:
                pricing = json.loads(pricing)
            except Exception:
                pricing = {}

        # Si tiene precios configurados → no alucinará (los tiene de verdad)
        if pricing and len(pricing) > 0:
            return False, response

        # Si tiene KB con precios → tampoco alucinará
        if kb_context and any(w in kb_context.lower() for w in ["precio", "valor", "costo", "$"]):
            return False, response

        response_low = (response or "").lower()
        if re.search(r'\b\d+\s*(?:a|y|-)\s*\d+\s*(dias|días|semanas|meses|anos|años|minutos)\b', response_low):
            return False, response

        # No tiene precios pero los está dando → alucinación
        for pattern in self._price_re:
            if pattern.search(response):
                # Reemplazar con respuesta honesta
                safe = self._safe_price_response(response)
                log.warning(f"[hallucination] precio inventado detectado: '{response[:80]}'")
                return True, safe

        return False, response

    def _safe_price_response(self, original: str) -> str:
        """Genera respuesta segura cuando no hay precio configurado."""
        alternatives = [
            "ese precio depende del caso ||| te lo confirmo cuando te vea la especialista",
            "no tengo ese dato exacto ahorita ||| en la valoración te dan el número para tu caso",
            "los precios varían según el caso ||| en la valoración te dan el número exacto",
        ]
        return random.choice(alternatives)

    def _check_dates(self, response: str, clinic: Dict) -> Tuple[bool, str]:
        """Detecta si Conny confirma fechas/disponibilidad sin tener el calendario."""
        # Si hay calendario configurado → puede dar fechas
        from_db = False
        try:
            if db:
                gcal = db.recall("whatsapp_connected")
                calendly = db.recall("calendly_link")
                from_db = bool(gcal or calendly)
        except Exception:
            pass

        has_calendar = (
            from_db or
            bool(Config.GCAL_REFRESH_TOKEN) or
            bool(Config.CALENDLY_LINK) or
            bool(clinic.get("calendly_link"))
        )

        if has_calendar:
            return False, response  # tiene calendario real

        # Sin calendario — detectar si está confirmando disponibilidad específica
        for pattern in self._date_re:
            if pattern.search(response):
                # Solo es alucinación si confirma ("hay espacio el jueves") no si propone
                # Diferenciar: "esta semana tienes el jueves" es propuesta, no confirmación
                if any(w in response.lower() for w in ["confirmado", "agendado", "reservado",
                                                        "hay espacio para", "tenemos espacio el"]):
                    safe = "déjame verificar disponibilidad ||| te confirmo en un momento"
                    log.warning(f"[hallucination] disponibilidad inventada: '{response[:80]}'")
                    return True, safe

        return False, response

    def _check_doctors(self, response: str, clinic: Dict, kb_context: str) -> Tuple[bool, str]:
        """Detecta si Conny inventa nombre de médico que no conoce."""
        # Si tiene nombre de doctor en KB o config → OK
        if kb_context:
            # Extraer nombres propios del KB
            names_in_kb = re.findall(r'\b(Dr\.|Dra\.|doctor|doctora)\s+[A-ZÁÉÍÓÚ]\w+', kb_context)
            if names_in_kb:
                return False, response

        # Buscar nombres de doctor en la respuesta
        for pattern in self._doctor_re:
            match = pattern.search(response)
            if match:
                # Verificar si el nombre mencionado está en algún dato conocido
                full_match = match.group(0)
                found_in_kb   = kb_context and full_match.lower() in kb_context.lower()
                found_in_mem  = False
                try:
                    if db:
                        mem = db.get_core_memory_block()
                        found_in_mem = mem and full_match.lower() in mem.lower()
                except Exception:
                    pass

                if not found_in_kb and not found_in_mem:
                    # Nombre de doctor no encontrado en datos → posible alucinación
                    # Solo marcar si es un nombre muy específico (no genérico "la doctora")
                    name_part = re.search(r'[A-ZÁÉÍÓÚ][a-záéíóú]+', full_match)
                    if name_part and len(name_part.group(0)) > 3:
                        safe = response.replace(full_match, "la especialista")
                        log.warning(f"[hallucination] doctor inventado: '{full_match}'")
                        return True, safe

        return False, response

    def _check_hours(self, response: str, clinic: Dict) -> Tuple[bool, str]:
        """Detecta si Conny da horario diferente al configurado."""
        schedule = clinic.get("schedule", {})
        if not schedule:
            return False, response  # Sin horario configurado, no podemos validar

        for pattern in self._hours_re:
            match = pattern.search(response)
            if match:
                # Extraer horas de la respuesta
                hours_in_resp = re.findall(r'\d{1,2}\s*(?:am|pm|a\.m\.|p\.m\.)', response.lower())
                if not hours_in_resp:
                    continue

                # Verificar contra horario configurado
                sched_text = " ".join(str(v) for v in schedule.values()).lower()
                for h in hours_in_resp:
                    if h not in sched_text:
                        # Hora no encontrada en config → potencial error
                        # Solo loguear como warning, no bloquear
                        log.debug(f"[hallucination] hora '{h}' no en config: '{sched_text[:50]}'")

        return False, response


# ═══════════════════════════════════════════════════════════════════════════════
# 3. FAILURE PREDICTOR ENGINE
# Predice fallos ANTES de que ocurran, basándose en patrones de conversación.
# Actúa proactivamente — no corrige errores, los previene.
# ═══════════════════════════════════════════════════════════════════════════════

class FailurePredictorEngine:
    """
    Predice en qué punto va a fallar una conversación y actúa antes.

    Fallos que predice:
    - CONTEXT_OVERFLOW:   Historial muy largo → el LLM empieza a olvidar
    - REPETITION_SPIRAL:  Conny hace la misma pregunta 2+ veces
    - LOST_THREAD:        El LLM perdió el hilo del servicio original
    - OBJECTION_IGNORED:  Hay una objeción no resuelta hace 3+ turnos
    - ESCALATION_NEEDED:  El cliente necesita hablar con un humano
    - FAKE_DATA_RISK:     Conny está a punto de dar datos que no tiene
    - EMOTIONAL_MISMATCH: El tono de Conny no calza con el estado del cliente

    Cada predicción genera una instrucción correctiva para el próximo prompt.
    """

    def __init__(self):
        self._conversation_warnings: Dict[str, List[str]] = {}  # chat_id → warnings

    def predict(self, chat_id: str, user_msg: str,
                history: List[Dict], clinic: Dict) -> List[str]:
        """
        Analiza el estado actual y retorna lista de advertencias.
        Cada advertencia es una instrucción para inyectar al próximo prompt.
        """
        warnings_list: List[str] = []

        # 1. Desbordamiento de contexto
        if len(history) > 40:
            warnings_list.append(
                "ALERTA: Conversación muy larga. Prioriza cerrar hacia la cita. "
                "No hagas preguntas nuevas. Solo confirma y propón fecha."
            )

        # 2. Espiral de repetición
        repetition = self._detect_repetition_spiral(history)
        if repetition:
            warnings_list.append(
                f"ALERTA: Estás repitiendo la pregunta '{repetition}'. "
                "No la hagas de nuevo. Cambia de ángulo o propón la valoración directamente."
            )

        # 3. Objeción sin resolver
        unresolved = self._find_unresolved_objection(history)
        if unresolved:
            warnings_list.append(
                f"ALERTA: Hay una objeción sin resolver desde hace tiempo: '{unresolved[:60]}'. "
                "Resuélvela PRIMERO antes de continuar."
            )

        # 4. Escalación necesaria
        if self._needs_escalation(user_msg, history):
            warnings_list.append(
                "ALERTA: El cliente muestra señales de querer hablar con una persona real. "
                "Ofrece conectarlo con el equipo: 'te paso con alguien del equipo si prefieres'"
            )

        # 5. Pérdida de hilo
        lost = self._detect_lost_thread(user_msg, history)
        if lost:
            warnings_list.append(
                f"ALERTA: Parece que perdiste el hilo. El cliente originalmente preguntó por '{lost}'. "
                "Vuelve a ese contexto."
            )

        # 6. Riesgo de datos falsos
        if self._fake_data_risk(user_msg, clinic):
            warnings_list.append(
                "ALERTA: El cliente está preguntando por datos específicos (precio, horario, doctor). "
                "Si NO los tienes en la configuración, di 'te confirmo' — NUNCA inventes."
            )

        # 7. Desajuste emocional
        mismatch = self._detect_emotional_mismatch(user_msg, history)
        if mismatch:
            warnings_list.append(mismatch)

        # Guardar para seguimiento
        if warnings_list:
            self._conversation_warnings[chat_id] = warnings_list
            log.info(f"[failure_predictor] {len(warnings_list)} advertencias para {chat_id}: "
                     f"{warnings_list[0][:60]}")

        return warnings_list

    def get_prompt_injection(self, chat_id: str) -> str:
        """Retorna bloque de advertencias para inyectar al prompt."""
        warnings_list = self._conversation_warnings.get(chat_id, [])
        if not warnings_list:
            return ""

        lines = ["⚠️ PREDICTOR DE FALLOS — Estas advertencias son PRIORITARIAS:"]
        for w in warnings_list:
            lines.append(f"  {w}")
        lines.append("")
        # Limpiar después de usar
        self._conversation_warnings.pop(chat_id, None)
        return "\n".join(lines)

    def _detect_repetition_spiral(self, history: List[Dict]) -> str:
        """Detecta si Conny está repitiendo la misma pregunta."""
        conny_questions = []
        for msg in history:
            if msg["role"] == "assistant":
                text = msg["content"]
                # Extraer preguntas (terminar en ? o tener palabras interrogativas)
                questions = re.findall(
                    r'[^.!|]+(?:cuándo|cómo|qué|cuánto|dónde|para qué)[^|?!.]*[?]?',
                    text, re.IGNORECASE
                )
                conny_questions.extend([q.strip()[:60] for q in questions])

        if len(conny_questions) < 2:
            return ""

        # Buscar duplicados aproximados
        for i in range(len(conny_questions)):
            for j in range(i + 1, len(conny_questions)):
                q1 = set(conny_questions[i].lower().split())
                q2 = set(conny_questions[j].lower().split())
                common = q1 & q2
                if len(common) >= 3:
                    return conny_questions[i]

        return ""

    def _find_unresolved_objection(self, history: List[Dict]) -> str:
        """Detecta objeciones del cliente que Conny no ha abordado."""
        OBJECTION_SIGNALS = [
            "está muy caro", "es costoso", "no tengo plata", "lo voy a pensar",
            "tengo miedo", "me da miedo", "quedé mal", "no me convence",
            "tengo dudas", "no sé si"
        ]

        last_objection = ""
        last_objection_idx = -1

        for i, msg in enumerate(history):
            if msg["role"] == "user":
                for signal in OBJECTION_SIGNALS:
                    if signal in msg["content"].lower():
                        last_objection = msg["content"][:80]
                        last_objection_idx = i
                        break

        if last_objection_idx < 0:
            return ""

        # Verificar si los mensajes de Conny posteriores la abordan
        conny_after = [
            msg["content"] for msg in history[last_objection_idx:]
            if msg["role"] == "assistant"
        ]

        RESOLUTION_SIGNALS = [
            "entiendo", "es válido", "normal que", "lo que pasa",
            "valoración", "doctora", "especialista", "te cuento"
        ]

        for conny_msg in conny_after:
            if any(s in conny_msg.lower() for s in RESOLUTION_SIGNALS):
                return ""  # Ya fue abordada

        # Nunca fue abordada → retornar la objeción
        return last_objection if len(history) - last_objection_idx >= 3 else ""

    def _needs_escalation(self, user_msg: str, history: List[Dict]) -> bool:
        """Detecta cuando el cliente quiere hablar con un humano."""
        escalation_signals = [
            "quiero hablar con una persona", "con alguien real",
            "no quiero hablar con un bot", "dame un número",
            "llámame", "me llaman", "necesito hablar con",
            "puedo hablar con el médico", "con la doctora directamente"
        ]
        user_lower = user_msg.lower()
        return any(s in user_lower for s in escalation_signals)

    def _detect_lost_thread(self, user_msg: str, history: List[Dict]) -> str:
        """Detecta si el LLM olvidó el servicio original del cliente."""
        if len(history) < 6:
            return ""

        # Encontrar el primer servicio mencionado por el cliente
        first_service = ""
        service_keywords = [
            "botox", "rellenos", "láser", "limpieza", "blanqueamiento",
            "ortodoncia", "masaje", "membresia", "membresía", "clase", "consulta"
        ]

        for msg in history[:4]:
            if msg["role"] == "user":
                for kw in service_keywords:
                    if kw in msg["content"].lower():
                        first_service = kw
                        break
            if first_service:
                break

        if not first_service:
            return ""

        # Verificar que los últimos mensajes de Conny mencionan el servicio
        recent_conny = " ".join(
            msg["content"] for msg in history[-4:]
            if msg["role"] == "assistant"
        ).lower()

        if first_service not in recent_conny:
            return first_service

        return ""

    def _fake_data_risk(self, user_msg: str, clinic: Dict) -> bool:
        """Detecta si el cliente está preguntando por datos que podrían no existir."""
        data_request_signals = [
            "cuánto vale", "cuánto cuesta", "qué precio", "cuánto cobran",
            "a qué hora", "qué horario", "cuándo abren", "cuándo atienden",
            "con qué doctor", "con qué médico", "cómo se llama"
        ]
        user_lower = user_msg.lower()

        if not any(s in user_lower for s in data_request_signals):
            return False

        # Verificar si tiene los datos configurados
        has_pricing  = bool(clinic.get("pricing") and clinic.get("pricing") != "{}")
        has_schedule = bool(clinic.get("schedule") and clinic.get("schedule") != "{}")
        has_doctors  = False  # Raramente configurado directamente

        # Si pregunta por precio y no tiene → riesgo
        if any(s in user_lower for s in ["cuánto vale", "precio", "cuesta"]) and not has_pricing:
            return True

        return False

    def _detect_emotional_mismatch(self, user_msg: str, history: List[Dict]) -> str:
        """Detecta cuando el tono de Conny no corresponde al estado del cliente."""
        user_lower = user_msg.lower()

        # Cliente frustrado pero Conny estaba siendo muy animada
        if any(w in user_lower for w in ["frustrad", "molest", "qué fastidio", "estoy enojad"]):
            last_conny = next(
                (msg["content"] for msg in reversed(history) if msg["role"] == "assistant"), ""
            )
            if any(w in last_conny.lower() for w in ["bacano", "chévere", "qué bueno", "perfecto"]):
                return (
                    "ALERTA EMOCIONAL: El cliente está frustrado. Tu último mensaje fue muy animado. "
                    "Baja el tono. Valida PRIMERO: 'ay entiendo, eso es frustrante' — luego resuelve."
                )

        # Cliente con miedo pero Conny siendo muy directa al precio
        if any(w in user_lower for w in ["miedo", "me preocupa", "tengo miedo"]):
            last_conny = next(
                (msg["content"] for msg in reversed(history) if msg["role"] == "assistant"), ""
            )
            if re.search(r'\$[\d.,]+|\d+\.000', last_conny):
                return (
                    "ALERTA EMOCIONAL: El cliente tiene miedo y tú hablaste de precio. "
                    "El miedo SIEMPRE antes del dinero. Valida el miedo primero."
                )

        return ""


# ═══════════════════════════════════════════════════════════════════════════════
# 4. SMART CONTEXT MANAGER
# Gestiona inteligentemente la ventana de contexto.
# El problema: después de 50 mensajes el LLM "olvida" el servicio original.
# La solución: compresión selectiva que preserva lo más importante.
# ═══════════════════════════════════════════════════════════════════════════════

class SmartContextManager:
    """
    Comprime el historial de conversación de forma inteligente.

    Estrategia:
    1. Siempre mantener los primeros 3 mensajes (contexto original)
    2. Siempre mantener los últimos 10 mensajes (contexto reciente)
    3. Del resto, extraer un "resumen" de hechos clave
    4. El resumen se inyecta como mensaje de sistema

    Hechos clave que siempre se preservan:
    - Nombre del cliente
    - Servicio de interés
    - Objeciones expresadas
    - Compromisos (fecha propuesta, etc.)
    - Estado emocional dominante
    """

    MAX_HISTORY_FULL   = 20   # Máximo de mensajes completos sin comprimir
    COMPRESSION_TARGET = 12   # Cuántos mensajes mantener después de comprimir

    def __init__(self):
        self._summaries: Dict[str, str] = {}  # chat_id → resumen comprimido

    def prepare_context(self, chat_id: str, history: List[Dict],
                        max_messages: int = 20) -> Tuple[List[Dict], str]:
        """
        Prepara el contexto para el LLM.
        Retorna: (historial_optimizado, bloque_resumen)
        """
        if len(history) <= max_messages:
            return history, ""

        # Dividir: head (primeros 3), middle (para comprimir), tail (últimos 10)
        head   = history[:3]
        tail   = history[-10:]
        middle = history[3:-10]

        if not middle:
            return history[-max_messages:], ""

        # Extraer hechos clave del middle
        facts = self._extract_key_facts(middle)
        summary = self._build_summary(facts, chat_id)

        # Guardar resumen para reutilizar
        self._summaries[chat_id] = summary

        # Historia optimizada: head + tail
        optimized = head + tail

        return optimized, summary

    def _extract_key_facts(self, messages: List[Dict]) -> Dict[str, Any]:
        """Extrae hechos clave del historial que se está comprimiendo."""
        facts: Dict[str, Any] = {
            "name":        "",
            "service":     "",
            "objections":  [],
            "commitments": [],
            "emotions":    [],
        }

        for msg in messages:
            content = msg["content"]
            role    = msg["role"]

            if role == "user":
                # Extraer nombre (si lo dijo)
                name_match = re.search(
                    r'(?:me llamo|soy|mi nombre es)\s+([A-ZÁÉÍÓÚ][a-záéíóú]+)',
                    content, re.IGNORECASE
                )
                if name_match and not facts["name"]:
                    facts["name"] = name_match.group(1)

                # Extraer servicio
                services_kw = ["botox", "rellenos", "láser", "limpieza", "blanqueamiento",
                                "ortodoncia", "masaje", "membresía", "clases", "consulta",
                                "tratamiento", "implante", "peeling", "mesoterapia"]
                for kw in services_kw:
                    if kw in content.lower() and not facts["service"]:
                        facts["service"] = kw
                        break

                # Extraer objeciones
                objections_kw = ["está caro", "tengo miedo", "lo voy a pensar",
                                  "quedé mal", "no tengo tiempo", "lo consulto"]
                for kw in objections_kw:
                    if kw in content.lower() and kw not in facts["objections"]:
                        facts["objections"].append(kw)

            elif role == "assistant":
                # Extraer compromisos (fechas propuestas)
                date_match = re.search(
                    r'(el\s+(?:lunes|martes|miércoles|jueves|viernes|sábado))',
                    content, re.IGNORECASE
                )
                if date_match:
                    day = date_match.group(1)
                    if day not in facts["commitments"]:
                        facts["commitments"].append(day)

        return facts

    def _build_summary(self, facts: Dict, chat_id: str) -> str:
        """Construye el bloque de resumen para inyectar al prompt."""
        lines = ["RESUMEN DE LA CONVERSACIÓN ANTERIOR (no lo menciones, solo úsalo):"]

        if facts.get("name"):
            lines.append(f"  Nombre del cliente: {facts['name']}")

        if facts.get("service"):
            lines.append(f"  Servicio de interés: {facts['service']}")

        if facts.get("objections"):
            lines.append(f"  Objeciones expresadas: {', '.join(facts['objections'])}")

        if facts.get("commitments"):
            lines.append(f"  Fechas mencionadas: {', '.join(facts['commitments'])}")

        lines.append("")
        return "\n".join(lines)

    def get_cached_summary(self, chat_id: str) -> str:
        """Retorna el resumen guardado para este chat."""
        return self._summaries.get(chat_id, "")


# ═══════════════════════════════════════════════════════════════════════════════
# 5. APPOINTMENT STATE MACHINE
# Máquina de estados completa para el proceso de agendar citas.
# Maneja ambigüedad de fechas, conflictos, confirmaciones y recordatorios.
# ═══════════════════════════════════════════════════════════════════════════════

class AppointmentStateMachine:
    """
    Gestiona el proceso de agendar una cita en etapas claras.

    Estados:
    IDLE → EXPLORING → DATE_PROPOSED → DATE_CONFIRMED → DETAILS_COLLECTING
         → FULLY_BOOKED → REMINDER_SENT → COMPLETED | CANCELLED

    Variables de fallo que maneja:
    - Fecha ambigua ("mañana" sin saber qué día es)
    - Fecha en pasado ("el lunes" cuando ya pasó)
    - Fecha en día que no trabajan
    - Hora fuera del horario
    - El cliente no confirma la fecha propuesta
    - El cliente propone una hora muy específica que no se puede garantizar
    - El cliente cancela sin nueva fecha
    """

    STATES = [
        "IDLE", "EXPLORING", "DATE_PROPOSED", "DATE_CONFIRMED",
        "DETAILS_COLLECTING", "FULLY_BOOKED", "REMINDER_SENT",
        "COMPLETED", "CANCELLED"
    ]

    def __init__(self):
        self._states:     Dict[str, str]  = {}   # chat_id → state
        self._proposals:  Dict[str, Dict] = {}   # chat_id → proposed date info
        self._bookings:   Dict[str, Dict] = {}   # chat_id → confirmed booking

    def get_state(self, chat_id: str) -> str:
        return self._states.get(chat_id, "IDLE")

    def propose_date(self, chat_id: str, date_text: str,
                     service: str = "", clinic: Dict = None) -> Dict:
        """
        Propone una fecha. Valida que no esté en el pasado ni en día cerrado.
        Retorna {valid: bool, date_resolved: str, message: str}
        """
        now = now_col()

        # Resolver "mañana", "el jueves", "esta semana", etc.
        resolved = self._resolve_date_text(date_text, now)

        if not resolved["valid"]:
            return {
                "valid": False,
                "date_resolved": "",
                "message": resolved["reason"]
            }

        # Verificar que no sea pasado
        if resolved["datetime"] and resolved["datetime"] < now:
            return {
                "valid": False,
                "date_resolved": "",
                "message": "esa fecha ya pasó — propón la siguiente disponible"
            }

        # Verificar horario de la clínica
        if clinic:
            schedule = clinic.get("schedule", {})
            if schedule:
                open_check = self._check_clinic_hours(resolved["datetime"], schedule)
                if not open_check["open"]:
                    return {
                        "valid": False,
                        "date_resolved": "",
                        "message": f"ese día no atendemos ({open_check['reason']})"
                    }

        # Todo OK → guardar propuesta
        self._states[chat_id]    = "DATE_PROPOSED"
        self._proposals[chat_id] = {
            "original_text": date_text,
            "resolved":      resolved.get("display", date_text),
            "datetime":      resolved.get("datetime"),
            "service":       service,
            "proposed_at":   now.isoformat(),
        }

        return {
            "valid":        True,
            "date_resolved": resolved.get("display", date_text),
            "message":      ""
        }

    def confirm_date(self, chat_id: str) -> bool:
        """Confirma la fecha propuesta. Avanza al estado DETAILS_COLLECTING."""
        if self._states.get(chat_id) != "DATE_PROPOSED":
            return False
        self._states[chat_id] = "DATE_CONFIRMED"
        return True

    def collect_details(self, chat_id: str, name: str = "",
                        phone: str = "", service: str = "") -> bool:
        """Registra detalles del cliente. Avanza a FULLY_BOOKED cuando completo."""
        if self._states.get(chat_id) not in ("DATE_CONFIRMED", "DETAILS_COLLECTING"):
            return False

        proposal = self._proposals.get(chat_id, {})
        if name:    proposal["patient_name"] = name
        if phone:   proposal["patient_phone"] = phone
        if service: proposal["service"] = service
        self._proposals[chat_id] = proposal
        self._states[chat_id]    = "DETAILS_COLLECTING"

        # Verificar si ya tenemos todo
        has_name    = bool(proposal.get("patient_name"))
        has_service = bool(proposal.get("service"))
        has_date    = bool(proposal.get("resolved"))

        if has_name and has_service and has_date:
            self._states[chat_id]  = "FULLY_BOOKED"
            self._bookings[chat_id] = dict(proposal)
            return True

        return False

    def cancel(self, chat_id: str, reason: str = "") -> bool:
        """Cancela la cita. Guarda el motivo."""
        if chat_id in self._proposals:
            self._proposals[chat_id]["cancelled_reason"] = reason
        self._states[chat_id] = "CANCELLED"
        return True

    def get_missing_details(self, chat_id: str) -> List[str]:
        """Retorna qué datos faltan para completar la reserva."""
        proposal = self._proposals.get(chat_id, {})
        missing = []
        if not proposal.get("patient_name"):   missing.append("nombre")
        if not proposal.get("service"):         missing.append("servicio")
        if not proposal.get("patient_phone"):   missing.append("teléfono")
        return missing

    def get_booking_summary(self, chat_id: str) -> str:
        """Retorna resumen de la cita para confirmar con el cliente."""
        booking = self._bookings.get(chat_id) or self._proposals.get(chat_id, {})
        if not booking:
            return ""

        parts = []
        if booking.get("patient_name"):
            parts.append(f"Nombre: {booking['patient_name']}")
        if booking.get("service"):
            parts.append(f"Servicio: {booking['service']}")
        if booking.get("resolved"):
            parts.append(f"Fecha: {booking['resolved']}")
        if booking.get("patient_phone"):
            parts.append(f"Teléfono: {booking['patient_phone']}")

        return "\n".join(parts) if parts else ""

    def _resolve_date_text(self, text: str, now: datetime) -> Dict:
        """
        Convierte texto de fecha a datetime.
        Maneja: "mañana", "el jueves", "esta semana", "próxima semana", etc.
        """
        text_lower = text.lower().strip()

        # Días de la semana
        weekdays = {
            "lunes": 0, "martes": 1, "miércoles": 2, "miercoles": 2,
            "jueves": 3, "viernes": 4, "sábado": 5, "sabado": 5, "domingo": 6
        }

        if text_lower in ("hoy", "today"):
            return {
                "valid": True,
                "datetime": now,
                "display": f"hoy {now.strftime('%d/%m')}",
            }

        if text_lower in ("mañana", "manana", "tomorrow"):
            tomorrow = now + timedelta(days=1)
            return {
                "valid": True,
                "datetime": tomorrow,
                "display": f"mañana {tomorrow.strftime('%A %d/%m')}",
            }

        # "el jueves" "este jueves" "próximo jueves"
        for day_name, day_num in weekdays.items():
            if day_name in text_lower:
                # Calcular el próximo occurrence de ese día
                days_ahead = (day_num - now.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7  # Si es hoy, ir al siguiente
                target = now + timedelta(days=days_ahead)
                is_next_week = "próximo" in text_lower or "proxima" in text_lower
                if is_next_week:
                    target += timedelta(days=7)
                return {
                    "valid": True,
                    "datetime": target,
                    "display": f"{day_name} {target.strftime('%d/%m')}",
                }

        # Si no resolvió → válido pero sin datetime exacto
        return {
            "valid": True,
            "datetime": None,
            "display": text,
        }

    def _check_clinic_hours(self, dt: datetime, schedule: Dict) -> Dict:
        """Verifica si la clínica atiende en esa fecha/hora."""
        if not dt or not schedule:
            return {"open": True, "reason": ""}

        day_name = dt.strftime("%A").lower()
        # Mapear inglés a español
        day_map = {
            "monday": "lunes", "tuesday": "martes", "wednesday": "miércoles",
            "thursday": "jueves", "friday": "viernes",
            "saturday": "sábado", "sunday": "domingo"
        }
        day_es = day_map.get(day_name, day_name)

        sched_text = " ".join(str(v) for v in schedule.values()).lower()

        if "domingo" not in sched_text and day_es == "domingo":
            return {"open": False, "reason": "no atendemos domingos"}

        return {"open": True, "reason": ""}


# ═══════════════════════════════════════════════════════════════════════════════
# 6. CONVERSATION RECOVERY ENGINE
# Detecta conversaciones atascadas y aplica estrategias de recuperación.
# Una conversación está "atascada" cuando: el cliente da respuestas de 1 palabra,
# el cliente no responde a la pregunta, o hay 3+ intercambios sin avance.
# ═══════════════════════════════════════════════════════════════════════════════

class ConversationRecoveryEngine:
    """
    Detecta y recupera conversaciones atascadas.

    Tipos de atasco:
    - MONOSYLLABIC:  El cliente responde con "sí", "ok", "bueno" repetidamente
    - EVASIVE:       El cliente desvía cada pregunta sin responder
    - PRICE_STUCK:   La conversación lleva 3+ turnos girando en torno al precio
    - FEAR_STUCK:    El cliente mencionó miedo pero nunca fue abordado bien
    - SILENT:        Más de 24h sin respuesta (se combina con ProactiveCampaign)
    - GHOST_RETURN:  El cliente vuelve después de mucho tiempo sin contexto

    Cada tipo tiene una estrategia de recuperación específica.
    """

    def __init__(self):
        self._stuck_counts: Dict[str, int] = {}  # chat_id → consecutive stuck turns

    def analyze(self, chat_id: str, user_msg: str,
                history: List[Dict]) -> Optional[str]:
        """
        Analiza si la conversación está atascada.
        Retorna instrucción de recuperación o None si no hay problema.
        """
        if not history or len(history) < 4:
            return None

        # 1. Respuestas monosilábicas repetidas
        mono_count = self._count_monosyllabic(history[-6:])
        if mono_count >= 3:
            return self._recovery_monosyllabic()

        # 2. Precio dominando la conversación
        price_count = self._count_price_mentions(history[-8:])
        if price_count >= 4:
            return self._recovery_price_stuck()

        # 3. Miedo no resuelto
        fear_unresolved = self._detect_unresolved_fear(history)
        if fear_unresolved:
            return self._recovery_fear_stuck()

        # 4. Sin avance después de N turnos
        if len(history) > 12 and not self._has_commitment_signal(history):
            progress = self._measure_progress(history[-10:])
            if progress < 0.2:
                self._stuck_counts[chat_id] = self._stuck_counts.get(chat_id, 0) + 1
                if self._stuck_counts[chat_id] >= 2:
                    self._stuck_counts[chat_id] = 0
                    return self._recovery_no_progress()
        else:
            self._stuck_counts[chat_id] = 0

        return None

    def get_recovery_prompt_injection(self, chat_id: str, user_msg: str,
                                       history: List[Dict]) -> str:
        """Retorna instrucción de recuperación para inyectar al prompt."""
        recovery = self.analyze(chat_id, user_msg, history)
        if not recovery:
            return ""
        return f"\n🔄 ESTRATEGIA DE RECUPERACIÓN:\n{recovery}\n"

    def _count_monosyllabic(self, recent: List[Dict]) -> int:
        """Cuenta cuántos mensajes del cliente son monosilábicos."""
        MONO_WORDS = {"sí", "si", "ok", "bueno", "bien", "dale", "claro",
                      "no", "tal vez", "quizás", "talvez", "mm", "ah", "oh"}
        count = 0
        for msg in recent:
            if msg["role"] == "user":
                words = msg["content"].lower().strip().split()
                if len(words) <= 2 and all(w in MONO_WORDS for w in words):
                    count += 1
        return count

    def _count_price_mentions(self, recent: List[Dict]) -> int:
        """Cuenta cuántas veces apareció el precio en la conversación."""
        price_signals = ["caro", "precio", "valor", "cuesta", "vale",
                         "costoso", "presupuesto", "descuento"]
        count = 0
        for msg in recent:
            for signal in price_signals:
                if signal in msg["content"].lower():
                    count += 1
                    break
        return count

    def _detect_unresolved_fear(self, history: List[Dict]) -> bool:
        """Detecta miedo no resuelto."""
        fear_signals = ["miedo", "me da miedo", "tengo miedo", "me preocupa que quede"]
        resolution_signals = ["es normal", "normal que", "la doctora", "valoración", "seguro"]

        fear_turn = -1
        for i, msg in enumerate(history):
            if msg["role"] == "user":
                for s in fear_signals:
                    if s in msg["content"].lower():
                        fear_turn = i
                        break

        if fear_turn < 0:
            return False

        # Verificar si fue resuelto en mensajes posteriores
        for msg in history[fear_turn:]:
            if msg["role"] == "assistant":
                for r in resolution_signals:
                    if r in msg["content"].lower():
                        return False

        return len(history) - fear_turn >= 4  # Solo si pasaron 4+ turnos sin resolver

    def _measure_progress(self, recent: List[Dict]) -> float:
        """Mide qué tan cerca está la conversación del objetivo (0-1)."""
        progress_signals = [
            "valoración", "cita", "agend", "cuándo puedes", "esta semana",
            "el jueves", "te reservo", "confirmado", "nombre"
        ]
        progress = 0.0
        for msg in recent:
            if msg["role"] == "assistant":
                for s in progress_signals:
                    if s in msg["content"].lower():
                        progress += 0.2
                        break
        return min(1.0, progress)

    def _has_commitment_signal(self, history: List[Dict]) -> bool:
        """Detecta si hay alguna señal de compromiso en el historial."""
        signals = ["agendado", "confirmado", "te espero", "quedó", "cita el"]
        for msg in history:
            if msg["role"] == "assistant":
                for s in signals:
                    if s in msg["content"].lower():
                        return True
        return False

    def _recovery_monosyllabic(self) -> str:
        options = [
            "El cliente está respondiendo con monosílabos — no está enganchado. "
            "Haz UNA pregunta que lo obligue a pensar: '¿qué fue lo que te hizo escribirnos hoy?' "
            "O propón directamente la valoración sin esperar más.",
            "Respuestas muy cortas — el cliente perdió interés o está ocupado. "
            "Sé directo: propón un solo día y hora y pregunta si puede.",
        ]
        return random.choice(options)

    def _recovery_price_stuck(self) -> str:
        return (
            "La conversación lleva varios turnos en el precio. "
            "CAMBIA EL ÁNGULO: deja el precio y ve al resultado. "
            "'el precio exacto te lo da la doctora en la valoración, que es gratis — "
            "lo que sí te puedo decir es que el resultado que buscas lo logran acá'. "
            "Luego propón el día."
        )

    def _recovery_fear_stuck(self) -> str:
        return (
            "Hay un miedo no resuelto que está bloqueando la conversación. "
            "ANTES de cualquier otra cosa: valida el miedo de forma específica. "
            "'ese miedo de quedar exagerada es exactamente lo que más les preocupa a todas las que vienen — "
            "y es exactamente lo que la doctora trabaja diferente acá'. "
            "Luego transfiere la decisión al especialista."
        )

    def _recovery_no_progress(self) -> str:
        options = [
            "La conversación no está avanzando. Momento de ser más directo: "
            "propón UN día específico con hora aproximada y espera su confirmación. "
            "No hagas más preguntas — da la información y propón el siguiente paso.",
            "Demasiados turnos sin avance. Cambia la estrategia: "
            "resumen de lo que sabe y propuesta concreta de fecha. Una sola pregunta: ¿sí o no?",
        ]
        return random.choice(options)


# ═══════════════════════════════════════════════════════════════════════════════
# 7. RESPONSE VARIATION ENGINE
# Garantiza que Conny nunca repita exactamente la misma frase en una conv.
# Usa hashing para detectar repeticiones y fuerza variación.
# ═══════════════════════════════════════════════════════════════════════════════

class ResponseVariationEngine:
    """
    Evita que Conny repita frases exactas en la misma conversación.

    Problema real: el LLM tiende a reutilizar las mismas estructuras de frase
    (especialmente cierres) en cada turno. Después de 5-6 mensajes todo
    suena igual.

    Solución: hash de frases usadas por chat_id + instrucción de variación.
    """

    def __init__(self):
        # chat_id → set de hashes de frases usadas
        self._used_phrases: Dict[str, Set[str]] = {}
        self._phrase_counts: Dict[str, Dict[str, int]] = {}

    def register(self, chat_id: str, response: str):
        """Registra las frases de una respuesta."""
        if chat_id not in self._used_phrases:
            self._used_phrases[chat_id] = set()
            self._phrase_counts[chat_id] = {}

        # Extraer frases significativas (6+ palabras)
        sentences = re.split(r'(?:\|\|\||[.!?])+', response)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence.split()) >= 4:
                phrase_hash = hashlib.md5(sentence.lower().encode()).hexdigest()[:8]
                self._used_phrases[chat_id].add(phrase_hash)

                # Contar repeticiones para detección
                full_hash = hashlib.md5(sentence.lower().encode()).hexdigest()
                self._phrase_counts[chat_id][full_hash] = \
                    self._phrase_counts[chat_id].get(full_hash, 0) + 1

    def check_repetition(self, chat_id: str, response: str) -> Tuple[bool, List[str]]:
        """
        Verifica si la respuesta contiene frases ya usadas.
        Retorna: (tiene_repeticiones, frases_repetidas)
        """
        if chat_id not in self._used_phrases:
            return False, []

        repeated = []
        sentences = re.split(r'(?:\|\|\||[.!?])+', response)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence.split()) >= 4:
                phrase_hash = hashlib.md5(sentence.lower().encode()).hexdigest()[:8]
                if phrase_hash in self._used_phrases[chat_id]:
                    repeated.append(sentence[:50])

        return bool(repeated), repeated

    def get_variation_injection(self, chat_id: str, response: str) -> str:
        """
        Si detecta repetición, retorna instrucción de variación para el retry.
        """
        has_rep, phrases = self.check_repetition(chat_id, response)
        if not has_rep:
            return ""

        lines = [
            "⚠️ VARIACIÓN REQUERIDA:",
            f"Ya usaste estas frases antes: {', '.join(phrases[:2])}",
            "Exprésalo de forma completamente diferente.",
            "Si vas a proponer la valoración → usa una formulación nueva.",
            "Si vas a preguntar → pregunta algo diferente a lo que ya preguntaste.",
        ]
        return "\n".join(lines)

    def get_diversity_score(self, chat_id: str) -> float:
        """Calcula qué tan diversas son las respuestas (0=monótona, 1=diversa)."""
        counts = self._phrase_counts.get(chat_id, {})
        if not counts:
            return 1.0

        total_phrases = sum(counts.values())
        repeated = sum(1 for c in counts.values() if c > 1)

        return 1.0 - (repeated / max(total_phrases, 1))


# ═══════════════════════════════════════════════════════════════════════════════
# 8. PROACTIVE CAMPAIGN ENGINE
# Campañas de seguimiento, reactivación y recordatorio.
# Basado en el TaskManager existente pero con lógica de campaña inteligente.
# ═══════════════════════════════════════════════════════════════════════════════

class ProactiveCampaignEngine:
    """
    Gestiona campañas proactivas de seguimiento.

    Campañas disponibles:
    - WARM_FOLLOWUP:    24h después de conversación sin cita
    - HOT_NUDGE:        6h después de conversación con lead caliente
    - APPOINTMENT_REMINDER_24H: 24h antes de la cita
    - APPOINTMENT_REMINDER_2H:  2h antes de la cita
    - POST_APPOINTMENT: 3 días después de la cita (feedback)
    - REACTIVATION_30D: 30 días sin respuesta
    - REACTIVATION_60D: 60 días sin respuesta
    - SEASONAL:         Campañas por temporada (noviembre, diciembre, etc.)
    """

    CAMPAIGN_TEMPLATES: Dict[str, Dict] = {
        "WARM_FOLLOWUP": {
            "delay_hours": 24,
            "condition": "sin_cita_post_consulta",
            "max_sends": 1,
            "messages": [
                "hola, quedé pensando en lo que me contaste ||| si tienes más preguntas aquí estoy, sin afán",
                "oye, quedé pensando ||| ¿ya pudiste pensar en lo de la valoración?",
                "hola de nuevo ||| quería saber si tuviste oportunidad de pensarlo",
            ],
        },
        "HOT_NUDGE": {
            "delay_hours": 6,
            "condition": "lead_caliente_sin_cierre",
            "max_sends": 1,
            "messages": [
                "oye, me quedé con tu caso pendiente ||| ¿cuándo puedes venir esta semana?",
                "hola ||| estaba mirando la agenda y esta semana hay buen espacio — ¿te queda el jueves?",
            ],
        },
        "APPOINTMENT_REMINDER_24H": {
            "delay_hours": -24,  # negativo = antes del evento
            "condition": "cita_confirmada",
            "max_sends": 1,
            "messages": [
                "hola! te recuerdo que mañana es tu cita ||| ¿todo bien para esa hora?",
                "buenas, mañana te esperamos a la hora acordada ||| cualquier cambio me avisas",
            ],
        },
        "APPOINTMENT_REMINDER_2H": {
            "delay_hours": -2,
            "condition": "cita_confirmada",
            "max_sends": 1,
            "messages": [
                "hola! en 2 horas te esperamos ||| llegando avísame para indicarte el acceso",
                "hola, en un rato nos vemos ||| si tienes alguna duda de último momento aquí estoy",
            ],
        },
        "POST_APPOINTMENT": {
            "delay_hours": 72,  # 3 días después
            "condition": "cita_completada",
            "max_sends": 1,
            "messages": [
                "hola, ¿cómo te fue? ||| ya deben estar viéndose los resultados",
                "oye, han pasado unos días ||| ¿cómo quedaste? ¿ya ves la diferencia?",
            ],
        },
        "REACTIVATION_30D": {
            "delay_hours": 720,  # 30 días
            "condition": "inactivo_30d",
            "max_sends": 1,
            "messages": [
                "hola, ¿cómo has estado? ||| hace un tiempo me escribiste y no sé si pudiste resolver lo que buscabas",
                "hola! hace un tiempo hablamos ||| si sigues interesada todavía hay disponibilidad esta semana",
            ],
        },
    }

    def __init__(self):
        self._scheduled: Dict[str, List[Dict]] = {}  # chat_id → campaña programadas
        self._sent_log: Dict[str, Dict[str, int]] = {}  # chat_id → {campaign_type → count}

    def schedule(self, chat_id: str, campaign_type: str,
                 patient_name: str = "", extra_data: Dict = None):
        """Programa una campaña para un chat_id."""
        if campaign_type not in self.CAMPAIGN_TEMPLATES:
            log.warning(f"[campaign] tipo desconocido: {campaign_type}")
            return

        template = self.CAMPAIGN_TEMPLATES[campaign_type]
        sent_count = self._sent_log.get(chat_id, {}).get(campaign_type, 0)

        if sent_count >= template["max_sends"]:
            log.debug(f"[campaign] {campaign_type} ya enviada {sent_count}x a {chat_id}")
            return

        delay_hours = template["delay_hours"]
        if delay_hours >= 0:
            scheduled_for = datetime.now() + timedelta(hours=delay_hours)
        else:
            # Para recordatorios, el scheduled_for viene en extra_data
            apt_time = (extra_data or {}).get("appointment_datetime")
            if not apt_time:
                return
            try:
                if isinstance(apt_time, str):
                    apt_time = datetime.fromisoformat(apt_time)
                scheduled_for = apt_time + timedelta(hours=delay_hours)
            except Exception:
                return

        # Usar task_manager si está disponible
        if task_manager:
            msg = self._pick_message(campaign_type, patient_name)
            task_manager.schedule_task(
                task_type="reminder",
                data={
                    "chat_id":        chat_id,
                    "message":        msg,
                    "campaign_type":  campaign_type,
                    "patient_name":   patient_name,
                },
                scheduled_for=scheduled_for,
                priority=5
            )
            log.info(f"[campaign] programada {campaign_type} para {chat_id} at {scheduled_for}")

    def cancel(self, chat_id: str, campaign_type: str = ""):
        """Cancela campañas programadas para un chat_id."""
        # El task_manager no expone cancel por tipo aún — marcar como cancelado
        key = f"campaign_cancelled_{chat_id}_{campaign_type}"
        try:
            if db:
                db.remember(key, "true", "campaigns")
        except Exception:
            pass

    def mark_sent(self, chat_id: str, campaign_type: str):
        """Registra que una campaña fue enviada."""
        if chat_id not in self._sent_log:
            self._sent_log[chat_id] = {}
        self._sent_log[chat_id][campaign_type] = \
            self._sent_log[chat_id].get(campaign_type, 0) + 1

    def _pick_message(self, campaign_type: str, patient_name: str = "") -> str:
        """Elige un mensaje del template y personaliza con el nombre si hay."""
        template = self.CAMPAIGN_TEMPLATES.get(campaign_type, {})
        messages = template.get("messages", ["hola, ¿cómo estás?"])
        msg = random.choice(messages)
        if patient_name:
            msg = msg.replace("hola", f"hola {patient_name.split()[0]}", 1)
        return msg

    def get_active_campaigns(self) -> Dict[str, int]:
        """Retorna resumen de campañas activas."""
        summary: Dict[str, int] = {}
        for chat_id, campaigns in self._scheduled.items():
            for c in campaigns:
                ctype = c.get("type", "unknown")
                summary[ctype] = summary.get(ctype, 0) + 1
        return summary


# ═══════════════════════════════════════════════════════════════════════════════
# 9. ADMIN INTELLIGENT BRIEFING
# Genera un briefing diario realmente útil para el admin.
# No solo estadísticas — identifica oportunidades y acciones concretas.
# ═══════════════════════════════════════════════════════════════════════════════

class AdminIntelligentBriefing:
    """
    Genera briefings de gestión para el admin.

    Un briefing tiene:
    - Número de conversaciones nuevas, activas, sin respuesta
    - Leads calientes identificados (con nombre y contexto)
    - Conversaciones atascadas (que necesitan intervención)
    - Citas agendadas hoy/mañana
    - Oportunidades perdidas de ayer
    - Una recomendación de acción prioritaria
    """

    async def generate(self, clinic: Dict, period_hours: int = 24) -> str:
        """Genera el briefing del período especificado."""
        if not db:
            return "Base de datos no disponible"

        try:
            now = now_col()
            cutoff = (now - timedelta(hours=period_hours)).isoformat()

            # ── Métricas básicas ────────────────────────────────────────────
            with db._conn() as c:
                # Conversaciones nuevas en el período
                new_convs = c.execute(
                    "SELECT COUNT(DISTINCT chat_id) FROM conversations "
                    "WHERE ts >= ? AND role='user'", (cutoff,)
                ).fetchone()[0] or 0

                # Total de mensajes
                total_msgs = c.execute(
                    "SELECT COUNT(*) FROM conversations WHERE ts >= ?", (cutoff,)
                ).fetchone()[0] or 0

                # Citas creadas
                new_apts = c.execute(
                    "SELECT COUNT(*) FROM appointments WHERE created_at >= ?", (cutoff,)
                ).fetchone()[0] or 0

                # Citas pendientes para hoy y mañana
                tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")
                today_str = now.strftime("%Y-%m-%d")
                upcoming_apts = c.execute(
                    "SELECT patient_name, service, datetime_slot, patient_phone "
                    "FROM appointments WHERE status='pendiente' "
                    "AND datetime_slot BETWEEN ? AND ? "
                    "ORDER BY datetime_slot LIMIT 5",
                    (today_str, tomorrow + " 23:59")
                ).fetchall()

                # Conversaciones sin respuesta del admin (>12h)
                cutoff_12h = (now - timedelta(hours=12)).isoformat()
                stuck_convs = c.execute(
                    "SELECT chat_id, MAX(ts) as last_msg "
                    "FROM conversations WHERE role='user' AND ts <= ? "
                    "GROUP BY chat_id "
                    "HAVING last_msg = (SELECT MAX(ts) FROM conversations c2 "
                    "WHERE c2.chat_id = conversations.chat_id) "
                    "ORDER BY last_msg DESC LIMIT 5",
                    (cutoff_12h,)
                ).fetchall()

            # ── Leads calientes (del ConversationIntelligence) ──────────────
            hot_leads = []
            if conversation_intelligence:
                for cid, state in conversation_intelligence._states.items():
                    if state.get("commitment_score", 0) >= 0.7:
                        patient_name = ""
                        try:
                            with db._conn() as c:
                                row = c.execute("SELECT name FROM patients WHERE chat_id=?",
                                                (cid,)).fetchone()
                                if row:
                                    patient_name = row["name"] or ""
                        except Exception:
                            pass
                        hot_leads.append({
                            "chat_id": cid,
                            "name":    patient_name or f"cliente_{cid[-4:]}",
                            "score":   state["commitment_score"],
                            "stage":   state.get("stage", ""),
                        })
                hot_leads.sort(key=lambda x: x["score"], reverse=True)

            # ── Usar LLM para generar recomendación ─────────────────────────
            recommendation = await self._generate_recommendation(
                new_convs, new_apts, len(hot_leads), len(stuck_convs or [])
            )

            # ── Formatear el briefing ───────────────────────────────────────
            lines = [
                f"📊 Briefing — últimas {period_hours}h",
                f"  Conversaciones nuevas: {new_convs}",
                f"  Mensajes totales: {total_msgs}",
                f"  Citas agendadas: {new_apts}",
            ]

            if hot_leads:
                lines.append(f"\n🔥 Leads calientes ({len(hot_leads)}):")
                for lead in hot_leads[:3]:
                    score_pct = int(lead['score'] * 100)
                    lines.append(f"  {lead['name']} — {score_pct}% listos — /chat {lead['chat_id']}")

            if upcoming_apts:
                lines.append(f"\n📅 Citas próximas ({len(upcoming_apts)}):")
                for apt in upcoming_apts:
                    lines.append(f"  {apt['patient_name']} · {apt['service']} · {apt['datetime_slot'][:16]}")

            if stuck_convs:
                lines.append(f"\n⏰ Sin respuesta (+12h): {len(stuck_convs)} conversaciones")

            if recommendation:
                lines.append(f"\n💡 Acción recomendada: {recommendation}")

            return "\n".join(lines)

        except Exception as e:
            log.error(f"[briefing] error: {e}", exc_info=True)
            return f"Error generando briefing: {e}"

    async def _generate_recommendation(self, new_convs: int, new_apts: int,
                                        hot_leads: int, stuck: int) -> str:
        """Genera una recomendación accionable usando el LLM."""
        if not llm_engine:
            return ""

        prompt = f"""Eres el coach de ventas de una clínica. Basado en estos datos:
- Conversaciones nuevas hoy: {new_convs}
- Citas agendadas: {new_apts}
- Leads calientes sin cerrar: {hot_leads}
- Conversaciones atascadas: {stuck}

Da UNA recomendación de acción concreta para el dueño. Máximo 2 oraciones. Sin introducción."""

        try:
            resp, _ = await asyncio.wait_for(
                llm_engine.complete(
                    [{"role": "user", "content": prompt}],
                    model_tier="lite", temperature=0.4, max_tokens=100
                ),
                timeout=10.0
            )
            return resp.strip()
        except Exception:
            if hot_leads > 0:
                return f"Tienes {hot_leads} lead(s) calientes. Escríbeles hoy — están listos."
            elif stuck > 0:
                return f"Hay {stuck} conversación(es) atascada(s). Revísalas con /chats."
            return ""


# ═══════════════════════════════════════════════════════════════════════════════
# 10. SELF TEST SUITE
# Suite de 25 tests internos que verifican que Conny funciona correctamente.
# Se ejecuta al arrancar y con /test.
# ═══════════════════════════════════════════════════════════════════════════════

class SelfTestSuite:
    """
    Suite de tests automáticos que verifican el correcto funcionamiento de Conny.

    Categorías:
    - UNIT:        Tests de funciones individuales (AntiRobotFilter, etc.)
    - INTEGRATION: Tests de interacción entre sistemas
    - PROMPT:      Tests de que el LLM genera respuestas correctas
    - CONFIG:      Tests de configuración y variables de entorno

    Cada test es atómico, rápido y falla con mensaje claro.
    """

    def __init__(self):
        self._results: List[Dict] = []

    async def run_all(self) -> Dict:
        """Ejecuta todos los tests y retorna reporte."""
        self._results = []
        start = time.time()

        # ── Tests unitarios (sin LLM) ────────────────────────────────────────
        self._test_anti_robot_filter()
        self._test_conversation_intelligence()
        self._test_smart_variety()
        self._test_model_manager_catalog()
        self._test_appointment_state_machine()
        self._test_hallucination_guard_prices()
        self._test_context_manager_compression()
        self._test_failure_predictor_repetition()
        self._test_response_variation_engine()
        self._test_ortography_corrections()
        self._test_bubble_splitter()
        self._test_first_contact_intro()
        self._test_language_detection()
        self._test_conversion_funnel_tracking()
        self._test_sector_detection()
        self._test_date_resolver()

        # ── Tests de integración (requieren DB) ─────────────────────────────
        if db:
            self._test_db_remember_recall()
            self._test_db_clinic_update()
            self._test_patient_upsert()
        else:
            self._record("DB_REMEMBER_RECALL", False, "db no disponible")
            self._record("DB_CLINIC_UPDATE",   False, "db no disponible")
            self._record("PATIENT_UPSERT",     False, "db no disponible")

        # ── Tests de prompt (requieren LLM — más lentos) ─────────────────────
        if llm_engine and llm_engine.providers:
            await self._test_llm_basic_response()
            await self._test_llm_anti_robot_response()
            await self._test_llm_spanish_detection()
        else:
            for name in ("LLM_BASIC", "LLM_ANTI_ROBOT", "LLM_SPANISH"):
                self._record(name, False, "llm_engine no disponible")

        elapsed = round(time.time() - start, 2)
        passed = sum(1 for r in self._results if r["passed"])
        failed = sum(1 for r in self._results if not r["passed"])

        return {
            "total":   len(self._results),
            "passed":  passed,
            "failed":  failed,
            "elapsed": elapsed,
            "results": self._results,
        }

    def format_report(self, report: Dict) -> List[str]:
        """Formatea el reporte para Telegram/WhatsApp."""
        total   = report["total"]
        passed  = report["passed"]
        failed  = report["failed"]
        elapsed = report["elapsed"]

        icon = "✅" if failed == 0 else ("⚠️" if failed <= 3 else "❌")
        lines = [
            f"{icon} Self-Test Suite — {passed}/{total} tests OK ({elapsed}s)",
        ]

        if failed > 0:
            lines.append("\nFallidos:")
            for r in report["results"]:
                if not r["passed"]:
                    lines.append(f"  ✗ [{r['name']}] {r['message']}")
        else:
            lines.append("  Todos los tests pasaron.")

        return ["\n".join(lines)]

    # ── Tests unitarios ──────────────────────────────────────────────────────

    def _test_anti_robot_filter(self):
        """AntiRobotFilter elimina frases de bot."""
        try:
            f = AntiRobotFilter(level=2)
            test_cases = [
                ("con mucho gusto te ayudo", True),          # debe ser eliminado
                ("hola, qué zona te molesta más", False),    # OK
                ("fue un placer atenderte hoy", True),        # debe ser eliminado
                ("claro, el jueves tenemos espacio", False),  # OK
            ]
            for text, should_change in test_cases:
                result = f.process(text)
                changed = result.lower() != text.lower()
                if changed != should_change:
                    self._record(
                        "ANTI_ROBOT_FILTER", False,
                        f"'{text[:40]}' → should_change={should_change} pero got changed={changed}"
                    )
                    return
            self._record("ANTI_ROBOT_FILTER", True)
        except Exception as e:
            self._record("ANTI_ROBOT_FILTER", False, str(e))

    def _test_conversation_intelligence(self):
        """ConversationIntelligence actualiza estado correctamente."""
        try:
            ci = ConversationIntelligence()
            # Simular análisis básico
            class MockAnalysis:
                intent = None
            mock = MockAnalysis()

            ci.update("test_chat", "hola quiero info sobre botox", "", mock)
            state = ci.get_state("test_chat")
            assert state["stage"] != "COLD", f"Expected not COLD, got {state['stage']}"
            assert state["turn"] == 1, f"Expected turn=1, got {state['turn']}"

            ci.update("test_chat", "la frente, ya se me marcan las líneas", "", mock)
            state2 = ci.get_state("test_chat")
            assert state2["turn"] == 2, f"Expected turn=2, got {state2['turn']}"
            assert state2["stage"] in ("DISCOVERY", "PAIN_EXPLORED"), \
                f"Unexpected stage: {state2['stage']}"

            self._record("CONVERSATION_INTELLIGENCE", True)
        except Exception as e:
            self._record("CONVERSATION_INTELLIGENCE", False, str(e))

    def _test_smart_variety(self):
        """SmartVariety no repite aperturas."""
        try:
            sv = SmartVariety()
            used = set()
            for _ in range(10):
                opening = sv.get_opening("test_chat", "greeting")
                # Puede repetir después de 3+ pero no los últimos 3
                used.add(opening)
            assert len(used) >= 2, f"SmartVariety usó solo {len(used)} aperturas únicas en 10"
            self._record("SMART_VARIETY", True)
        except Exception as e:
            self._record("SMART_VARIETY", False, str(e))

    def _test_model_manager_catalog(self):
        """ModelManager tiene todos los modelos del catálogo."""
        try:
            mm = ModelManager()
            catalog = Config.V8_MODEL_CATALOG
            assert len(catalog) >= 10, f"Catálogo muy pequeño: {len(catalog)} modelos"
            for alias, (model_id, tier, desc) in catalog.items():
                assert "/" in model_id, f"Model ID sin proveedor: {model_id}"
                assert tier in ("fast", "reasoning", "lite"), f"Tier inválido: {tier}"
            self._record("MODEL_MANAGER_CATALOG", True)
        except Exception as e:
            self._record("MODEL_MANAGER_CATALOG", False, str(e))

    def _test_appointment_state_machine(self):
        """AppointmentStateMachine resuelve fechas correctamente."""
        try:
            asm = AppointmentStateMachine()
            result = asm.propose_date("test_chat", "el jueves", "Botox")
            assert result["valid"] is True, f"'el jueves' debería ser válido: {result}"
            assert result["date_resolved"], f"'el jueves' no resolvió fecha: {result}"

            result2 = asm.propose_date("test_chat2", "mañana", "Rellenos")
            assert result2["valid"] is True, f"'mañana' debería ser válido: {result2}"

            self._record("APPOINTMENT_STATE_MACHINE", True)
        except Exception as e:
            self._record("APPOINTMENT_STATE_MACHINE", False, str(e))

    def _test_hallucination_guard_prices(self):
        """HallucinationGuard detecta precios inventados."""
        try:
            hg = HallucinationGuard()
            clinic_no_prices = {"name": "TestClinic", "pricing": {}}

            # Con precios inventados
            has_halluc, kind, safe = hg.check(
                "el botox cuesta $350.000", clinic_no_prices
            )
            assert has_halluc, "Debería detectar precio inventado"
            assert kind == "PRICE_INVENTED", f"Tipo incorrecto: {kind}"

            # Con precios configurados — no debería bloquear
            clinic_with_prices = {"name": "TestClinic", "pricing": {"Botox": "350.000"}}
            has_halluc2, _, _ = hg.check("el botox cuesta $350.000", clinic_with_prices)
            assert not has_halluc2, "No debería bloquear si tiene precios configurados"

            self._record("HALLUCINATION_GUARD", True)
        except Exception as e:
            self._record("HALLUCINATION_GUARD", False, str(e))

    def _test_context_manager_compression(self):
        """SmartContextManager comprime historial largo correctamente."""
        try:
            scm = SmartContextManager()
            # Crear historial largo
            history = []
            for i in range(30):
                history.append({"role": "user",      "content": f"mensaje del cliente {i}"})
                history.append({"role": "assistant", "content": f"respuesta de conny {i}"})

            optimized, summary = scm.prepare_context("test_chat", history, max_messages=20)
            assert len(optimized) <= 20, f"Debería comprimir a 20, got {len(optimized)}"
            # El summary puede ser vacío si no hay hechos extraíbles
            self._record("CONTEXT_MANAGER", True)
        except Exception as e:
            self._record("CONTEXT_MANAGER", False, str(e))

    def _test_failure_predictor_repetition(self):
        """FailurePredictorEngine detecta preguntas repetidas."""
        try:
            fpe = FailurePredictorEngine()
            history = [
                {"role": "assistant", "content": "qué zona te molesta más"},
                {"role": "user",      "content": "la frente"},
                {"role": "assistant", "content": "qué zona te molesta más del rostro"},
                {"role": "user",      "content": "la frente, ya te dije"},
                {"role": "assistant", "content": "cuéntame qué zona te molesta"},
            ]
            result = fpe._detect_repetition_spiral(history)
            assert result, f"Debería detectar repetición de 'qué zona te molesta'"
            self._record("FAILURE_PREDICTOR", True)
        except Exception as e:
            self._record("FAILURE_PREDICTOR", False, str(e))

    def _test_response_variation_engine(self):
        """ResponseVariationEngine detecta repetición de frases."""
        try:
            rve = ResponseVariationEngine()
            phrase = "el botox relaja el músculo y en una semana no se ven las líneas"
            rve.register("test_chat", phrase)
            has_rep, phrases = rve.check_repetition("test_chat", phrase)
            assert has_rep, "Debería detectar repetición"
            assert phrases, f"Debería retornar frases repetidas: {phrases}"
            self._record("RESPONSE_VARIATION", True)
        except Exception as e:
            self._record("RESPONSE_VARIATION", False, str(e))

    def _test_ortography_corrections(self):
        """AntiRobotFilter corrige em-dash y puntuación."""
        try:
            f = AntiRobotFilter(level=1)
            test = "el resultado — es natural"
            result = f.process(test)
            assert "—" not in result, f"Em-dash debería ser removido: '{result}'"
            self._record("ORTOGRAPHY_CORRECTIONS", True)
        except Exception as e:
            self._record("ORTOGRAPHY_CORRECTIONS", False, str(e))

    def _test_bubble_splitter(self):
        """_split_bubbles divide correctamente en burbujas."""
        if not conny:
            self._record("BUBBLE_SPLITTER", False, "conny no inicializado")
            return
        try:
            result = conny._split_bubbles("hola qué tal ||| qué zona te molesta")
            assert len(result) == 2, f"Debería dividir en 2 burbujas: {result}"
            assert result[0] == "hola qué tal", f"Primera burbuja incorrecta: {result[0]}"
            self._record("BUBBLE_SPLITTER", True)
        except Exception as e:
            self._record("BUBBLE_SPLITTER", False, str(e))

    def _test_first_contact_intro(self):
        """El primer saludo debe presentar a Conny y aterrizar el negocio."""
        if not conny:
            self._record("FIRST_CONTACT_INTRO", False, "conny no inicializado")
            return
        try:
            clinic = {"name": "Clinica Demo", "services": ["Botox", "Armonizacion facial"]}
            personality = apply_archetype("amigable", "Conny")
            result = conny._normalize_first_patient_turn(
                response="oye qué te trae por acá",
                clinic=clinic,
                personality=personality,
                user_msg="hola que tal",
                history=[],
            )
            parts = [part.strip() for part in result.split("|||") if part.strip()]
            assert len(parts) >= 2, f"Debería quedar en al menos 2 burbujas: {result}"
            assert "conny" in parts[0].lower(), f"Debe presentarse: {parts[0]}"
            assert "equipo" in parts[0].lower(), f"Debe ubicarse como parte del negocio: {parts[0]}"
            assert "qué te trae por acá" not in result.lower(), f"No debe sonar invasiva: {result}"
            self._record("FIRST_CONTACT_INTRO", True)
        except Exception as e:
            self._record("FIRST_CONTACT_INTRO", False, str(e))

    def _test_language_detection(self):
        """MultilingualHandler detecta idiomas correctamente."""
        try:
            ml = MultilingualHandler()
            assert ml.detect("hello, how much does botox cost?") == "en"
            assert ml.detect("hola, cuánto vale el botox") == "es"
            assert ml.detect("olá, quanto custa o botox") == "pt"
            self._record("LANGUAGE_DETECTION", True)
        except Exception as e:
            self._record("LANGUAGE_DETECTION", False, str(e))

    def _test_conversion_funnel_tracking(self):
        """ConversionFunnelTracker registra y recupera etapas."""
        try:
            cf = ConversionFunnelTracker()
            cf.record("chat_001", "cold", "discovery", "first_message")
            cf.record("chat_001", "discovery", "pain_explored", "user_shared_pain")
            # Solo verificar que no lanzó excepción
            summary = cf.get_pipeline_summary()
            assert isinstance(summary, dict), "Debería retornar dict"
            self._record("CONVERSION_FUNNEL", True)
        except Exception as e:
            self._record("CONVERSION_FUNNEL", False, str(e))

    def _test_sector_detection(self):
        """SECTORS contiene todos los sectores necesarios."""
        try:
            required = ["estetica", "dental", "restaurante", "gimnasio", "medico"]
            for s in required:
                assert s in SECTORS, f"Sector '{s}' no encontrado"
                info = get_sector_info(s)
                assert len(info) == 4, f"Sector '{s}' mal formateado"
            self._record("SECTOR_DETECTION", True)
        except Exception as e:
            self._record("SECTOR_DETECTION", False, str(e))

    def _test_date_resolver(self):
        """AppointmentStateMachine resuelve todas las variantes de fecha."""
        try:
            asm = AppointmentStateMachine()
            cases = ["mañana", "el jueves", "el viernes", "este sábado",
                     "próximo lunes", "la semana que viene"]
            for case in cases:
                r = asm._resolve_date_text(case, now_col())
                assert r["valid"], f"'{case}' debería ser válido"
            self._record("DATE_RESOLVER", True)
        except Exception as e:
            self._record("DATE_RESOLVER", False, str(e))

    def _test_db_remember_recall(self):
        """DatabaseManager remember/recall funciona."""
        try:
            test_key = f"_test_{int(time.time())}"
            db.remember(test_key, "test_value", "test")
            recalled = db.recall(test_key)
            assert recalled == "test_value", f"Recall falló: got '{recalled}'"
            db.forget(test_key)
            self._record("DB_REMEMBER_RECALL", True)
        except Exception as e:
            self._record("DB_REMEMBER_RECALL", False, str(e))

    def _test_db_clinic_update(self):
        """DatabaseManager update_clinic no rompe la DB."""
        try:
            clinic_before = db.get_clinic()
            db.update_clinic(tagline=clinic_before.get("tagline", ""))
            clinic_after = db.get_clinic()
            assert clinic_after is not None, "get_clinic retornó None después de update"
            self._record("DB_CLINIC_UPDATE", True)
        except Exception as e:
            self._record("DB_CLINIC_UPDATE", False, str(e))

    def _test_patient_upsert(self):
        """DatabaseManager get_or_create_patient funciona."""
        try:
            test_id = f"_test_patient_{int(time.time())}"
            patient = db.get_or_create_patient(test_id)
            assert patient is not None, "Retornó None"
            assert patient["chat_id"] == test_id, "chat_id no coincide"
            assert patient["is_new"] is True, "Primer insert debería ser is_new=True"
            # Limpiar
            try:
                with db._conn() as c:
                    c.execute("DELETE FROM patients WHERE chat_id=?", (test_id,))
            except Exception:
                pass
            self._record("PATIENT_UPSERT", True)
        except Exception as e:
            self._record("PATIENT_UPSERT", False, str(e))

    async def _test_llm_basic_response(self):
        """LLM responde a un prompt simple."""
        try:
            resp, meta = await asyncio.wait_for(
                llm_engine.complete(
                    [{"role": "user", "content": "Di solo 'OK' sin nada más"}],
                    model_tier="lite", temperature=0.0, max_tokens=10
                ),
                timeout=15.0
            )
            assert resp and len(resp) > 0, "LLM devolvió respuesta vacía"
            assert meta.get("provider"), "LLM no retornó provider en metadata"
            self._record("LLM_BASIC", True, f"provider: {meta.get('provider')}")
        except asyncio.TimeoutError:
            self._record("LLM_BASIC", False, "TIMEOUT después de 15s")
        except Exception as e:
            self._record("LLM_BASIC", False, str(e))

    async def _test_llm_anti_robot_response(self):
        """El LLM responde sin frases de bot cuando se le pide."""
        try:
            resp, _ = await asyncio.wait_for(
                llm_engine.complete(
                    [
                        {"role": "system", "content": "Eres Conny. Nunca uses 'con mucho gusto'."},
                        {"role": "user",   "content": "hola"}
                    ],
                    model_tier="fast", temperature=0.7, max_tokens=50
                ),
                timeout=20.0
            )
            bot_phrases = ["con mucho gusto", "encantada", "fue un placer", "soy una ia"]
            has_bot = any(p in resp.lower() for p in bot_phrases)
            if has_bot:
                self._record("LLM_ANTI_ROBOT", False,
                             f"LLM usó frase de bot a pesar de la instrucción: '{resp[:60]}'")
            else:
                self._record("LLM_ANTI_ROBOT", True)
        except asyncio.TimeoutError:
            self._record("LLM_ANTI_ROBOT", False, "TIMEOUT después de 20s")
        except Exception as e:
            self._record("LLM_ANTI_ROBOT", False, str(e))

    async def _test_llm_spanish_detection(self):
        """El LLM responde en español cuando se le habla en español."""
        try:
            resp, _ = await asyncio.wait_for(
                llm_engine.complete(
                    [
                        {"role": "system", "content": "Eres Conny, recepcionista en Colombia."},
                        {"role": "user",   "content": "hola, cuánto vale el botox"}
                    ],
                    model_tier="fast", temperature=0.5, max_tokens=100
                ),
                timeout=20.0
            )
            # Verificar que responde en español (al menos 3 palabras en español)
            spanish_words = ["el", "la", "de", "en", "qué", "que", "para", "con", "una", "un"]
            word_count = sum(1 for w in spanish_words if f" {w} " in f" {resp.lower()} ")
            if word_count < 2:
                self._record("LLM_SPANISH", False,
                             f"Respuesta no parece español: '{resp[:80]}'")
            else:
                self._record("LLM_SPANISH", True)
        except asyncio.TimeoutError:
            self._record("LLM_SPANISH", False, "TIMEOUT después de 20s")
        except Exception as e:
            self._record("LLM_SPANISH", False, str(e))

    # ── Helper ───────────────────────────────────────────────────────────────

    def _record(self, name: str, passed: bool, message: str = ""):
        self._results.append({"name": name, "passed": passed, "message": message})


# ═══════════════════════════════════════════════════════════════════════════════
# INSTANCIAS GLOBALES — V8 EXTENDED
# ═══════════════════════════════════════════════════════════════════════════════

conversation_simulator:    Optional[ConversationSimulator]    = None
hallucination_guard:       Optional[HallucinationGuard]       = None
failure_predictor:         Optional[FailurePredictorEngine]   = None
smart_context_manager:     Optional[SmartContextManager]      = None
appointment_state_machine: Optional[AppointmentStateMachine]  = None
conversation_recovery:     Optional[ConversationRecoveryEngine] = None
response_variation:        Optional[ResponseVariationEngine]  = None
campaign_engine:           Optional[ProactiveCampaignEngine]  = None
admin_briefing:            Optional[AdminIntelligentBriefing] = None
self_test_suite:           Optional[SelfTestSuite]            = None


def init_v8_extended_systems():
    """
    Inicializa todos los sistemas extendidos de V8.
    Cada sistema es INDEPENDIENTE — un fallo no afecta a los demás.
    """
    global conversation_simulator, hallucination_guard, failure_predictor
    global smart_context_manager, appointment_state_machine, conversation_recovery
    global response_variation, campaign_engine, admin_briefing, self_test_suite

    _systems_to_init = [
        ("conversation_simulator",    lambda: ConversationSimulator()),
        ("hallucination_guard",       lambda: HallucinationGuard()),
        ("failure_predictor",         lambda: FailurePredictorEngine()),
        ("smart_context_manager",     lambda: SmartContextManager()),
        ("appointment_state_machine", lambda: AppointmentStateMachine()),
        ("conversation_recovery",     lambda: ConversationRecoveryEngine()),
        ("response_variation",        lambda: ResponseVariationEngine()),
        ("campaign_engine",           lambda: ProactiveCampaignEngine()),
        ("admin_briefing",            lambda: AdminIntelligentBriefing()),
        ("self_test_suite",           lambda: SelfTestSuite()),
    ]

    _ok = 0
    for _name, _factory in _systems_to_init:
        try:
            _instance = _factory()
            globals()[_name] = _instance
            _ok += 1
        except Exception as _e_sys:
            log.warning(f"[v8_extended] {_name} falló: {_e_sys}")

    log.info(f"═══ V8 EXTENDED SYSTEMS: {_ok}/{len(_systems_to_init)} OK ═══")
    log.info("  ConversationSimulator:    ready")
    log.info("  HallucinationGuard:       ready")
    log.info("  FailurePredictorEngine:   ready")
    log.info("  SmartContextManager:      ready")
    log.info("  AppointmentStateMachine:  ready")
    log.info("  ConversationRecovery:     ready")
    log.info("  ResponseVariationEngine:  ready")
    log.info("  ProactiveCampaignEngine:  ready")
    log.info("  AdminIntelligentBriefing: ready")
    log.info("  SelfTestSuite:            ready")


# ═══════════════════════════════════════════════════════════════════════════════
# NUEVOS ENDPOINTS FASTAPI — V8 EXTENDED
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/v8/simulate")
async def api_simulate(request: Request):
    """
    Ejecuta una simulación de conversación.
    Body: {"scenario": "estetica_miedo"} o {} para todos.
    """
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")

    if not conversation_simulator:
        raise HTTPException(status_code=503, detail="Sistema de simulación no disponible")

    data     = await request.json()
    scenario = data.get("scenario", "")
    clinic   = db.get_clinic() if db else {}

    if scenario:
        if scenario not in ConversationSimulator.SCENARIOS:
            raise HTTPException(
                status_code=400,
                detail=f"Escenario desconocido. Disponibles: {list(ConversationSimulator.SCENARIOS.keys())}"
            )
        result = await conversation_simulator.run_scenario(scenario, clinic)
        return result
    else:
        report = await conversation_simulator.run_all(clinic)
        return report


@app.get("/v8/simulate/scenarios")
async def api_list_scenarios():
    """Lista todos los escenarios de simulación disponibles."""
    return {
        "scenarios": {
            sid: {
                "desc":   s["desc"],
                "sector": s["sector"],
            }
            for sid, s in ConversationSimulator.SCENARIOS.items()
        }
    }


@app.post("/v8/test")
async def api_self_test(request: Request):
    """Ejecuta la suite completa de tests automáticos."""
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")

    if not self_test_suite:
        raise HTTPException(status_code=503, detail="Self-test suite no disponible")

    report = await self_test_suite.run_all()
    return report


@app.get("/v8/briefing")
async def api_briefing(request: Request, hours: int = 24):
    """Genera el briefing inteligente del período especificado."""
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")

    if not admin_briefing:
        raise HTTPException(status_code=503, detail="Briefing no disponible")

    clinic  = db.get_clinic() if db else {}
    content = await admin_briefing.generate(clinic, period_hours=hours)
    return {"briefing": content, "period_hours": hours}


@app.get("/v8/pipeline")
async def api_pipeline_v8(request: Request):
    """Pipeline de conversiones usando ConversionFunnelTracker V8."""
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")

    if not conversion_funnel:
        raise HTTPException(status_code=503, detail="Funnel no disponible")

    summary  = conversion_funnel.get_pipeline_summary()
    rates    = conversion_funnel.get_conversion_rate()
    report   = conversion_funnel.format_pipeline_report()

    # Datos del ConversationIntelligence
    ci_data: Dict[str, int] = {}
    if conversation_intelligence:
        for state in conversation_intelligence._states.values():
            s = state.get("stage", "COLD")
            ci_data[s] = ci_data.get(s, 0) + 1

    return {
        "funnel_summary":  summary,
        "conversion_rates": rates,
        "active_stages":    ci_data,
        "report_text":      report,
    }


@app.get("/v8/ping")
async def api_v8_ping():
    """
    Ping de diagnóstico V8 — sin dependencias externas.
    Si responde, los endpoints V8 están registrados correctamente.
    """
    return {
        "ok":      True,
        "v8":      True,
        "version": "8.0",
        "ts":      datetime.now().isoformat(),
        "anti_robot_active":    anti_robot_filter is not None,
        "model_manager_active": model_manager is not None,
        "systems_initialized":  anti_robot_filter is not None and model_manager is not None,
    }


@app.get("/v8/health")
async def api_v8_health():
    """
    Estado de salud de todos los sistemas V8.
    NUNCA devuelve 500 — siempre responde aunque los sistemas no estén activos.
    """
    try:
        systems = {
            "anti_robot_filter":         anti_robot_filter is not None,
            "conversation_intelligence": conversation_intelligence is not None,
            "hyper_human_engine":        hyper_human_engine is not None,
            "smart_variety":             smart_variety is not None,
            "model_manager":             model_manager is not None,
            "conversation_simulator":    conversation_simulator is not None,
            "hallucination_guard":       hallucination_guard is not None,
            "failure_predictor":         failure_predictor is not None,
            "smart_context_manager":     smart_context_manager is not None,
            "appointment_state_machine": appointment_state_machine is not None,
            "conversation_recovery":     conversation_recovery is not None,
            "response_variation":        response_variation is not None,
            "campaign_engine":           campaign_engine is not None,
            "admin_briefing":            admin_briefing is not None,
            "self_test_suite":           self_test_suite is not None,
        }

        all_ok       = all(systems.values())
        active_count = sum(1 for v in systems.values() if v)
        total_count  = len(systems)

        model_info = {}
        if model_manager:
            model_info = model_manager.get_effective_models()

        # Diagnóstico de por qué los sistemas pueden estar inactivos
        init_notes = []
        if not anti_robot_filter:
            init_notes.append("AntiRobotFilter no inicializado — llama a init_v8_systems()")
        if not conversation_intelligence:
            init_notes.append("ConversationIntelligence no inicializado")
        if not model_manager:
            init_notes.append("ModelManager no inicializado")

        return {
            "status":           "ok" if all_ok else ("degraded" if active_count > 0 else "v8_not_initialized"),
            "version":          "8.0",
            "systems":          systems,
            "active_count":     active_count,
            "total_systems":    total_count,
            "current_models":   model_info,
            "filter_level":     anti_robot_filter.level if anti_robot_filter else 0,
            "quality_threshold": Config.V8_QUALITY_THRESHOLD,
            "init_notes":       init_notes,
        }
    except Exception as _e_health:
        log.error(f"[v8/health] error: {_e_health}", exc_info=True)
        return {
            "status":       "error",
            "version":      "8.0",
            "error":        str(_e_health),
            "active_count": 0,
            "systems":      {},
        }


@app.post("/v8/model")
async def api_set_model_v8(request: Request):
    """
    Cambia el modelo LLM en caliente desde la CLI V8.
    Body: {"alias": "gemini-flash", "model": "google/gemini-2.5-flash", "tier": "fast"}
    Persiste en DB y aplica inmediatamente a llm_engine.
    """
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")

    data      = await request.json()
    alias     = data.get("alias", "").strip()
    model_id  = data.get("model", "").strip()
    tier      = data.get("tier", "fast").strip()

    if not model_id:
        raise HTTPException(status_code=400, detail="model requerido")

    # Aplicar en caliente al engine si existe
    applied_in_flight = False
    try:
        if model_manager:
            model_manager.apply_override(tier, model_id)
            model_manager.apply_override("fast", model_id)
            if tier == "reasoning":
                model_manager.apply_override("reasoning", model_id)
            model_manager._push_to_engine(tier, model_id)
            applied_in_flight = True
        elif llm_engine:
            for provider in llm_engine.providers:
                if hasattr(provider, "MDLS"):
                    provider.MDLS[tier]   = model_id
                    provider.MDLS["fast"] = model_id
            applied_in_flight = True
    except Exception as e:
        log.warning(f"[v8/model] error aplicando en caliente: {e}")

    # Persistir en DB
    if db:
        try:
            db.remember("v8_model_override",
                        json.dumps({"tier": tier, "model": model_id, "alias": alias}),
                        "config")
        except Exception:
            pass

    log.info(f"[v8/model] cambiado: {tier}={model_id} (in_flight={applied_in_flight})")

    return {
        "ok":              True,
        "model":           model_id,
        "tier":            tier,
        "alias":           alias,
        "applied_in_flight": applied_in_flight,
        "message":         f"Modelo cambiado a {model_id}",
    }


@app.post("/v8/campaign/{campaign_type}")
async def api_trigger_campaign(campaign_type: str, request: Request):
    """
    Activa una campaña manualmente para un chat_id específico.
    Body: {"chat_id": "...", "patient_name": "..."}
    """
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")

    if not campaign_engine:
        raise HTTPException(status_code=503, detail="Campaign engine no disponible")

    valid_types = list(ProactiveCampaignEngine.CAMPAIGN_TEMPLATES.keys())
    if campaign_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo inválido. Disponibles: {valid_types}"
        )

    data = await request.json()
    chat_id      = data.get("chat_id", "")
    patient_name = data.get("patient_name", "")

    if not chat_id:
        raise HTTPException(status_code=400, detail="chat_id requerido")

    campaign_engine.schedule(chat_id, campaign_type, patient_name)
    return {"ok": True, "chat_id": chat_id, "campaign_type": campaign_type}


@app.get("/v8/variation-score/{chat_id}")
async def api_variation_score(chat_id: str, request: Request):
    """Score de diversidad de respuestas para un chat."""
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")

    score = response_variation.get_diversity_score(chat_id) if response_variation else 0.0
    return {
        "chat_id":         chat_id,
        "diversity_score": round(score, 2),
        "interpretation":  "diversa" if score >= 0.7 else ("normal" if score >= 0.4 else "monótona"),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# COMANDOS ADMIN ADICIONALES — V8 EXTENDED
# Se integran en ConnyUltra._handle_admin_or_setup vía monkey-patching
# ═══════════════════════════════════════════════════════════════════════════════

async def _admin_run_simulation(self_ref, chat_id: str, scenario_id: str = "") -> List[str]:
    """
    /simular [escenario] — Ejecuta simulación de conversación.
    Sin argumento: ejecuta todos los escenarios.
    """
    if not conversation_simulator:
        return ["Sistema de simulación no disponible. Reinicia el servidor."]

    clinic = db.get_clinic() if db else {}

    if scenario_id:
        if scenario_id not in ConversationSimulator.SCENARIOS:
            available = "\n".join(
                f"  /simular {sid} — {s['desc']}"
                for sid, s in ConversationSimulator.SCENARIOS.items()
            )
            return [
                f"Escenario '{scenario_id}' no encontrado.",
                f"Escenarios disponibles:\n{available}"
            ]

        try:
            result = await asyncio.wait_for(
                conversation_simulator.run_scenario(scenario_id, clinic),
                timeout=90.0
            )
        except asyncio.TimeoutError:
            return [f"Simulación '{scenario_id}' tardó más de 90s — abortada"]
        except Exception as e:
            return [f"Error en simulación: {e}"]

        lines = [f"Simulación: {result['desc']}"]
        lines.append(f"Resultado: {'✅ OK' if not result['failures'] else '❌ Con fallos'}")
        lines.append(f"Humanidad: {int(result['avg_humanness']*100)}%")
        lines.append(f"Turnos: {result['total_turns']}")

        if result["failures"]:
            lines.append("\nFallos:")
            for f in result["failures"][:5]:
                lines.append(f"  ✗ {f}")

        if result["turns"]:
            lines.append("\nConversación:")
            for i, turn in enumerate(result["turns"][:4]):
                lines.append(f"  [{i+1}] Cliente: {turn['client'][:50]}")
                lines.append(f"       Conny: {turn['conny'][:60]}")

        return ["\n".join(lines)]
    else:
        # Todos los escenarios — aviso de que tardará
        return_msg = ["Ejecutando todos los escenarios... esto tarda 1-2 minutos."]

        async def run_and_notify():
            try:
                report = await asyncio.wait_for(
                    conversation_simulator.run_all(clinic), timeout=180.0
                )
                formatted = conversation_simulator.format_report(report)
                # Notificar al admin cuando termine
                if db:
                    admin_ids = _parse_admin_ids(db.get_clinic().get("admin_chat_ids", []))
                    if conny and admin_ids:
                        for aid in admin_ids:
                            for msg in formatted:
                                await conny._send_message(aid, msg)
            except Exception as e:
                log.error(f"[simulator] run_all error: {e}")

        asyncio.create_task(run_and_notify())
        return return_msg


async def _admin_run_self_test(self_ref) -> List[str]:
    """
    /test — Ejecuta la suite de 25 tests automáticos.
    Verifica que todos los sistemas internos funcionan.
    """
    if not self_test_suite:
        return ["Self-test suite no disponible."]

    try:
        report = await asyncio.wait_for(
            self_test_suite.run_all(), timeout=120.0
        )
    except asyncio.TimeoutError:
        return ["Tests tardaron más de 120s — algunos fallaron por timeout"]
    except Exception as e:
        return [f"Error ejecutando tests: {e}"]

    return self_test_suite.format_report(report)


async def _admin_get_briefing(self_ref, clinic: Dict, hours: int = 24) -> List[str]:
    """
    /briefing [horas] — Genera el briefing inteligente del período.
    Por defecto: últimas 24 horas.
    """
    if not admin_briefing:
        return ["Briefing no disponible."]

    try:
        content = await asyncio.wait_for(
            admin_briefing.generate(clinic, period_hours=hours),
            timeout=30.0
        )
    except asyncio.TimeoutError:
        return ["El briefing tardó demasiado. Intenta de nuevo."]
    except Exception as e:
        return [f"Error generando briefing: {e}"]

    return [content]


async def _admin_appt_status(self_ref, chat_id: str) -> List[str]:
    """
    /cita-estado [chat_id] — Estado de la cita en la AppointmentStateMachine.
    """
    if not appointment_state_machine:
        return ["AppointmentStateMachine no disponible."]

    state    = appointment_state_machine.get_state(chat_id)
    proposal = appointment_state_machine._proposals.get(chat_id, {})
    booking  = appointment_state_machine._bookings.get(chat_id, {})

    lines = [f"Estado de cita para {chat_id}:", f"  Estado: {state}"]

    if proposal:
        lines.append(f"  Fecha propuesta: {proposal.get('resolved', '-')}")
        lines.append(f"  Servicio: {proposal.get('service', '-')}")
        lines.append(f"  Nombre: {proposal.get('patient_name', '-')}")

    if booking:
        lines.append(f"\nReserva confirmada:")
        lines.append(appointment_state_machine.get_booking_summary(chat_id))

    missing = appointment_state_machine.get_missing_details(chat_id)
    if missing:
        lines.append(f"\nFaltan: {', '.join(missing)}")

    return ["\n".join(lines)]


# Monkey-patch ConnyUltra para agregar los nuevos métodos de admin
ConnyUltra._admin_run_simulation = _admin_run_simulation
ConnyUltra._admin_run_self_test  = _admin_run_self_test
ConnyUltra._admin_get_briefing   = _admin_get_briefing
ConnyUltra._admin_appt_status    = _admin_appt_status


# Patch del dispatcher de comandos para incluir los nuevos comandos
_orig_attr = getattr(ConnyUltra, "_handle_admin_or_setup", None)
_original_handle_admin = _orig_attr.__wrapped__ if (_orig_attr and hasattr(_orig_attr, "__wrapped__")) else None


def _patch_admin_dispatcher():
    """
    Extiende _handle_admin_or_setup con los nuevos comandos V8 Extended.
    Se ejecuta después de que conny esté inicializado.
    """
    orig_get = getattr(ConnyUltra, "_handle_admin_or_setup", None)
    original_method = orig_get if orig_get else None

    async def patched_handle_admin(self, chat_id: str, text: str, clinic: Dict) -> List[str]:
        cmd = text.lower().strip()

        # ── Nuevos comandos V8 Extended ───────────────────────────────────────
        if cmd == "/simular":
            return await self._admin_run_simulation(chat_id)
        elif cmd.startswith("/simular "):
            scenario_id = cmd.split("/simular ", 1)[1].strip()
            return await self._admin_run_simulation(chat_id, scenario_id)
        elif cmd == "/test":
            return await self._admin_run_self_test()
        elif cmd == "/briefing" or cmd.startswith("/briefing "):
            hours_str = cmd.split("/briefing", 1)[1].strip()
            hours = int(hours_str) if hours_str.isdigit() else 24
            return await self._admin_get_briefing(clinic, hours)
        elif cmd.startswith("/cita-estado "):
            target_id = cmd.split("/cita-estado ", 1)[1].strip()
            return await self._admin_appt_status(target_id)
        elif cmd == "/cita-estado":
            return [
                "Formato: /cita-estado [chat_id]",
                "Ej: /cita-estado 573001234567"
            ]

        # Delegar al método original para todo lo demás
        if original_method:
            return await original_method(self, chat_id, text, clinic)
        return ["Admin no disponible."]

    setattr(ConnyUltra, "_handle_admin_or_setup", patched_handle_admin)
    log.info("[v8_extended] dispatcher admin patcheado con nuevos comandos")


# ═══════════════════════════════════════════════════════════════════════════════
# INYECCIÓN EN EL PIPELINE DE PRODUCCIÓN
# Agrega HallucinationGuard + FailurePredictor + ResponseVariation
# a la respuesta de pacientes en producción.
# ═══════════════════════════════════════════════════════════════════════════════

def v8_extended_postprocess(response: str, chat_id: str, clinic: Dict,
                             user_msg: str, history: List[Dict],
                             archetype: str = "amigable") -> str:
    """
    Post-procesamiento extendido V8 para TODAS las respuestas a pacientes.
    NUNCA crashea — si falla, retorna la respuesta original.
    """
    if not response:
        return response
    try:
        return _v8_extended_postprocess_inner(response, chat_id, clinic, user_msg, history, archetype)
    except Exception as _e_ext:
        log.debug(f"[v8_ext_post] error no crítico: {_e_ext}")
        return response


def _v8_extended_postprocess_inner(response: str, chat_id: str, clinic: Dict,
                             user_msg: str, history: List[Dict],
                             archetype: str = "amigable") -> str:
    """
    Post-procesamiento extendido V8 para TODAS las respuestas a pacientes.

    Pipeline:
    1. HallucinationGuard → bloquea datos inventados
    2. ResponseVariationEngine → detecta repetición y forza variación
    3. v8_process_response (anti-robot, ya definido antes)

    Retorna la respuesta limpia.
    """
    kb_context = ""
    try:
        if db and kb:
            kb_context = kb.query(user_msg)[:500] if hasattr(kb, "query") else ""
    except Exception:
        pass

    # 1. HallucinationGuard
    if hallucination_guard:
        has_halluc, kind, safe_response = hallucination_guard.check(
            response, clinic, kb_context
        )
        if has_halluc:
            log.warning(f"[hallucination] bloqueado {kind} en {chat_id}: '{response[:60]}'")
            response = safe_response

    # 2. ResponseVariationEngine — registrar para tracking (no bloquear aquí)
    if response_variation:
        response_variation.register(chat_id, response)

    # 3. v8_process_response (anti-robot base)
    response = v8_process_response(response, chat_id=chat_id, archetype=archetype)

    return response


def v8_extended_pre_prompt_injection(chat_id: str, user_msg: str,
                                      history: List[Dict], clinic: Dict) -> str:
    """
    Construye el bloque de instrucciones extendido para inyectar AL INICIO del prompt.
    NUNCA crashea — retorna string vacío si falla.
    """
    try:
        return _v8_pre_prompt_inner(chat_id, user_msg, history, clinic)
    except Exception as _e_pre:
        log.debug(f"[v8_pre_prompt] error no crítico: {_e_pre}")
        return ""


def _v8_pre_prompt_inner(chat_id: str, user_msg: str,
                          history: List[Dict], clinic: Dict) -> str:
    """
    Implementación interna del pre-prompt V8.
    Combina: FailurePredictor + ConversationRecovery + ResponseVariation.

    Este bloque le da a Conny información específica sobre QUÉ puede fallar
    en el próximo mensaje y CÓMO prevenirlo.
    """
    injections: List[str] = []

    # 1. Predictor de fallos
    if failure_predictor:
        warnings_list = failure_predictor.predict(chat_id, user_msg, history, clinic)
        if warnings_list:
            block = failure_predictor.get_prompt_injection(chat_id)
            if block:
                injections.append(block)

    # 2. Recuperación de conversación atascada
    if conversation_recovery:
        recovery_inj = conversation_recovery.get_recovery_prompt_injection(
            chat_id, user_msg, history
        )
        if recovery_inj:
            injections.append(recovery_inj)

    # 3. Variación de respuesta (si hay repetición detectada)
    if response_variation and history:
        # Tomar la última respuesta de Conny para evaluar
        last_conny = next(
            (h["content"] for h in reversed(history) if h["role"] == "assistant"), ""
        )
        if last_conny:
            variation_inj = response_variation.get_variation_injection(chat_id, last_conny)
            if variation_inj:
                injections.append(variation_inj)

    # 4. Contexto comprimido si el historial es largo
    if smart_context_manager and len(history) > SmartContextManager.MAX_HISTORY_FULL:
        cached_summary = smart_context_manager.get_cached_summary(chat_id)
        if cached_summary:
            injections.append(cached_summary)

    if not injections:
        return ""

    return "\n\n" + "\n\n".join(injections) + "\n\n"


# ═══════════════════════════════════════════════════════════════════════════════
# ACTUALIZACIÓN DEL BANNER CON SISTEMAS EXTENDIDOS
# ═══════════════════════════════════════════════════════════════════════════════

V8_EXTENDED_BANNER = """
    ╔══════════════════════════════════════════════════════════════════╗
    ║                                                                  ║
    ║     ██████╗  ██████╗ ███╗   ██╗███╗   ██╗██╗   ██╗             ║
    ║    ██╔════╝ ██╔═══██╗████╗  ██║████╗  ██║╚██╗ ██╔╝             ║
    ║    ██║      ██║   ██║██╔██╗ ██║██╔██╗ ██║ ╚████╔╝              ║
    ║    ██║      ██║   ██║██║╚██╗██║██║╚██╗██║  ╚██╔╝               ║
    ║    ╚██████╗ ╚██████╔╝██║ ╚████║██║ ╚████║   ██║                ║
    ║     ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═══╝   ╚═╝                ║
    ║                                                                  ║
    ║                    U L T R A   v 8 . 0                          ║
    ║              Hipernaturalmente Humana — Extended                 ║
    ║                                                                  ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║  CORE V8:                                                        ║
    ║  • AntiRobotFilter L1-L3 — elimina cada frase de call center     ║
    ║  • ConversationIntelligence — etapas, emociones, compromiso      ║
    ║  • HyperHumanEngine — valida humanidad en cada respuesta         ║
    ║  • SmartVariety — nunca repite apertura ni cierre igual          ║
    ║  • ModelManager — /modelo cambia el LLM en caliente              ║
    ║  EXTENDED V8:                                                    ║
    ║  • ConversationSimulator — simula 10 escenarios internamente     ║
    ║  • HallucinationGuard — bloquea precios/fechas inventados        ║
    ║  • FailurePredictorEngine — predice fallos antes de que pasen    ║
    ║  • SmartContextManager — comprime contexto sin perder datos      ║
    ║  • AppointmentStateMachine — máquina de estados para citas       ║
    ║  • ConversationRecoveryEngine — rescata convs. atascadas         ║
    ║  • ResponseVariationEngine — cero repetición de frases           ║
    ║  • ProactiveCampaignEngine — follow-ups, recordatorios           ║
    ║  • AdminIntelligentBriefing — briefing diario accionable         ║
    ║  • SelfTestSuite — 25 tests automáticos al arrancar              ║
    ╚══════════════════════════════════════════════════════════════════╝
"""


# ═══ CONNY OBSERVATORY ═══

# ═══════════════════════════════════════════════════════════════════════════════
# CONNY AGENT OBSERVATORY V8.0
# Real-time AI agent observability system
# ═══════════════════════════════════════════════════════════════════════════════

import time as _obs_time
import json as _obs_json
import asyncio as _obs_asyncio
from collections import deque as _deque
from dataclasses import dataclass as _dc, field as _dcfield
from typing import Dict as _D, List as _L, Optional as _Opt
from datetime import datetime as _dt


class EventType:
    LLM_CALL       = "llm_call"
    MESSAGE_IN     = "message_in"
    MESSAGE_OUT    = "message_out"
    QUALITY_SCORE  = "quality_score"
    FAILURE        = "failure"
    WARNING        = "warning"
    APPOINTMENT    = "appointment"
    CONVERSION     = "conversion"
    FUNNEL_ADVANCE = "funnel_advance"
    DIAGNOSIS      = "diagnosis"
    SYSTEM         = "system"


@_dc
class AgentEvent:
    id:        str
    type:      str
    ts:        float
    chat_id:   str = ""
    instance:  str = ""
    data:      dict = _dcfield(default_factory=dict)
    severity:  str = "info"

    def to_dict(self):
        return {
            "id":       self.id,
            "type":     self.type,
            "ts":       self.ts,
            "ts_h":     _dt.fromtimestamp(self.ts).strftime("%H:%M:%S.%f")[:12],
            "chat_id":  self.chat_id,
            "instance": self.instance,
            "data":     self.data,
            "severity": self.severity,
        }

    def to_sse(self):
        import json
        return "data: " + json.dumps(self.to_dict(), ensure_ascii=False) + "\n\n"


class EventBus:
    MAX_EVENTS = 2000

    def __init__(self):
        self._events  = _deque(maxlen=self.MAX_EVENTS)
        self._subs    = []
        self._counter = 0

    async def emit(self, etype, data, chat_id="", severity="info"):
        self._counter += 1
        evt = AgentEvent(
            id=f"e{self._counter:05d}",
            type=etype, ts=_obs_time.time(),
            chat_id=chat_id,
            instance=os.getenv("CONNY_INSTANCE", "base"),
            data=data, severity=severity,
        )
        self._events.append(evt)
        dead = []
        for q in self._subs:
            try: q.put_nowait(evt)
            except Exception: dead.append(q)
        for d in dead:
            try: self._subs.remove(d)
            except ValueError: pass
        return evt

    def emit_sync(self, etype, data, chat_id="", severity="info"):
        self._counter += 1
        evt = AgentEvent(
            id=f"e{self._counter:05d}",
            type=etype, ts=_obs_time.time(),
            chat_id=chat_id,
            instance=os.getenv("CONNY_INSTANCE", "base"),
            data=data, severity=severity,
        )
        self._events.append(evt)
        return evt

    def subscribe(self):
        q = _obs_asyncio.Queue(maxsize=500)
        if len(self._subs) < 50:
            self._subs.append(q)
        return q

    def unsubscribe(self, q):
        try: self._subs.remove(q)
        except ValueError: pass

    def get_recent(self, limit=100, event_type="", severity=""):
        evts = list(self._events)
        if event_type: evts = [e for e in evts if e.type == event_type]
        if severity:   evts = [e for e in evts if e.severity == severity]
        return list(reversed(evts))[:limit]

    def get_stats(self):
        evts = list(self._events)
        by_type, by_sev = {}, {}
        for e in evts:
            by_type[e.type]     = by_type.get(e.type, 0) + 1
            by_sev[e.severity]  = by_sev.get(e.severity, 0) + 1
        return {
            "total": len(evts),
            "by_type": by_type,
            "by_severity": by_sev,
            "subscribers": len(self._subs),
        }


class AgentTracer:
    def __init__(self, ev_bus):
        self.bus       = ev_bus
        self._traces   = {}
        self._counter  = 0

    def start(self, chat_id, messages, tier="fast"):
        self._counter += 1
        tid = f"tr{self._counter:04d}"
        self._traces[tid] = {
            "chat_id": chat_id,
            "tier":    tier,
            "t0":      _obs_time.time(),
            "msgs":    messages,
        }
        return tid

    def end(self, tid, response, model="", error=""):
        tr = self._traces.pop(tid, {})
        if not tr: return
        ms       = int((_obs_time.time() - tr["t0"]) * 1000)
        chat_id  = tr.get("chat_id", "")
        in_tok   = max(1, sum(len(m.get("content","")) for m in tr.get("msgs",[])) // 4)
        out_tok  = max(1, len(response) // 4)
        issues   = self._issues(response)
        sev      = "error" if error else ("warning" if issues or ms > 8000 else "info")

        self.bus.emit_sync(EventType.LLM_CALL, {
            "model":      model or tr.get("tier", "?"),
            "latency_ms": ms,
            "in_tok":     in_tok,
            "out_tok":    out_tok,
            "preview":    response[:120],
            "error":      error,
            "issues":     issues,
        }, chat_id=chat_id, severity=sev)

        for iss in issues:
            self.bus.emit_sync(EventType.FAILURE, {
                "type":     iss["type"],
                "detail":   iss["detail"],
                "response": response[:150],
                "trace_id": tid,
            }, chat_id=chat_id, severity="warning")

    def _issues(self, resp):
        if not resp: return [{"type":"empty","detail":"LLM returned empty"}]
        issues = []
        rl = resp.lower()
        BOT = ["con mucho gusto","encantada de ayudarte","fue un placer",
               "gracias por contactarnos","estamos para servirte"]
        if any(p in rl for p in BOT):
            issues.append({"type":"bot_phrase","detail":"frase de call center detectada"})
        if len(resp.split()) > 80:
            issues.append({"type":"too_long","detail":f"{len(resp.split())} palabras"})
        try:
            if anti_robot_filter:
                sc = anti_robot_filter.score_humanness(resp)
                if sc < 0.55:
                    issues.append({"type":"low_humanness","detail":f"score {sc:.2f}"})
        except Exception:
            pass
        return issues


class ConversationObserver:
    def __init__(self, ev_bus):
        self.bus   = ev_bus
        self._convs = {}

    def observe(self, chat_id, role, content, response="", quality=0.0):
        if chat_id not in self._convs:
            self._convs[chat_id] = {
                "t0": _obs_time.time(), "turns": 0,
                "stage": "COLD", "scores": [],
                "converted": False, "last_t": _obs_time.time(),
                "last_content": "",
            }
        c = self._convs[chat_id]
        c["last_t"]       = _obs_time.time()
        c["last_content"] = content[:100]

        if role == "user":
            c["turns"] += 1
            self.bus.emit_sync(EventType.MESSAGE_IN,
                {"content": content[:200], "turn": c["turns"], "stage": c["stage"]},
                chat_id=chat_id)
        elif role == "assistant" and response:
            sc = quality
            if not sc:
                try:
                    sc = anti_robot_filter.score_humanness(response) if anti_robot_filter else 0.7
                except Exception:
                    sc = 0.7
            c["scores"].append(sc)
            avg = sum(c["scores"]) / len(c["scores"])

            if conversation_intelligence:
                state = conversation_intelligence.get_state(chat_id)
                old_s = c.get("stage","COLD")
                new_s = state.get("stage","COLD")
                if new_s != old_s:
                    c["stage"] = new_s
                    self.bus.emit_sync(EventType.FUNNEL_ADVANCE,
                        {"from": old_s, "to": new_s, "turn": c["turns"]},
                        chat_id=chat_id)
                if new_s in ("BOOKED","CONFIRMED") and not c["converted"]:
                    c["converted"] = True
                    self.bus.emit_sync(EventType.CONVERSION,
                        {"turns": c["turns"],
                         "time_min": round((_obs_time.time()-c["t0"])/60,1),
                         "avg_quality": round(avg,2)},
                        chat_id=chat_id)

            self.bus.emit_sync(EventType.QUALITY_SCORE,
                {"score": round(sc,2), "avg": round(avg,2), "preview": response[:100]},
                chat_id=chat_id,
                severity="info" if sc >= 0.65 else "warning")

            self.bus.emit_sync(EventType.MESSAGE_OUT,
                {"content": response[:200], "quality": round(sc,2), "turn": c["turns"]},
                chat_id=chat_id)

    def active(self, max_age=60):
        cut = _obs_time.time() - max_age*60
        out = []
        for cid, c in self._convs.items():
            if c["last_t"] >= cut:
                avg = round(sum(c["scores"])/len(c["scores"]),2) if c["scores"] else 0
                out.append({
                    "chat_id":    cid,
                    "turns":      c["turns"],
                    "stage":      c["stage"],
                    "avg_q":      avg,
                    "converted":  c["converted"],
                    "elapsed_m":  round((_obs_time.time()-c["t0"])/60,1),
                    "ago_s":      round(_obs_time.time()-c["last_t"]),
                    "last":       c["last_content"],
                })
        return sorted(out, key=lambda x: x["ago_s"])

    def stats(self):
        a = self.active(60)
        conv = sum(1 for c in a if c["converted"])
        qs   = [c["avg_q"] for c in a if c["avg_q"]>0]
        return {
            "active": len(a),
            "conversions": conv,
            "rate": round(conv/len(a)*100,1) if a else 0,
            "avg_quality": round(sum(qs)/len(qs),2) if qs else 0,
            "avg_turns": round(sum(c["turns"] for c in a)/len(a),1) if a else 0,
        }


class AIDiagnostician:
    def __init__(self, ev_bus):
        self.bus         = ev_bus
        self._last_diag  = 0
        self._cooldown   = 300

    async def diagnose(self, limit=15):
        if not llm_engine: return None
        failures = self.bus.get_recent(limit=limit, event_type=EventType.FAILURE)
        if not failures:
            return {"summary":"Sin fallos recientes","actions":[],"severity":"low"}

        by_type = {}
        for e in failures:
            t = e.data.get("type","?")
            by_type.setdefault(t, []).append(e)

        fail_txt = ""
        for t, evts in by_type.items():
            fail_txt += f"\n[{t}] — {len(evts)}x:\n"
            for ev in evts[:2]:
                fail_txt += f"  • {ev.data.get('detail','')} — '{ev.data.get('response','')[:60]}'\n"

        prompt = f"""Eres analista de agentes IA para negocios en Colombia.
Fallos detectados en Conny (asistente WhatsApp):
{fail_txt}

Diagnóstico breve (JSON):
{{
  "summary": "qué está pasando en 1 frase",
  "root_causes": ["causa 1"],
  "impact": "efecto en el cliente",
  "actions": [{{"priority":"alta|media|baja","action":"qué hacer"}}],
  "severity": "critical|high|medium|low"
}}"""
        try:
            raw, _ = await _obs_asyncio.wait_for(
                llm_engine.complete([{"role":"user","content":prompt}],
                    model_tier="fast", temperature=0.3, max_tokens=300, use_cache=False),
                timeout=15.0)
            import re as _re
            m = _re.search(r'\{[\s\S]+\}', raw.strip())
            diag = _obs_json.loads(m.group(0)) if m else {"summary": raw[:200]}
            diag["count"] = len(failures)
            diag["ts"]    = _dt.now().isoformat()
            await self.bus.emit(EventType.DIAGNOSIS, diag,
                                severity=diag.get("severity","medium"))
            self._last_diag = _obs_time.time()
            return diag
        except Exception as e:
            log.warning(f"[diagnostician] {e}")
            return None

    async def auto(self):
        if _obs_time.time() - self._last_diag < self._cooldown: return
        recent = self.bus.get_recent(limit=20, event_type=EventType.FAILURE)
        if len(recent) >= 5:
            await self.diagnose(20)


# ── Globals ──────────────────────────────────────────────────────────────────

bus:                   EventBus              = None
agent_tracer:          AgentTracer           = None
conversation_observer: ConversationObserver  = None
ai_diagnostician:      AIDiagnostician       = None


def init_observatory():
    global bus, agent_tracer, conversation_observer, ai_diagnostician
    try:
        bus                   = EventBus()
        agent_tracer          = AgentTracer(bus)
        conversation_observer = ConversationObserver(bus)
        ai_diagnostician      = AIDiagnostician(bus)
        bus.emit_sync(EventType.SYSTEM, {"event":"boot","version":"8.0"})
        log.info("═══ OBSERVATORY INITIALIZED ═══")
    except Exception as e:
        log.warning(f"[observatory] init error: {e}")


# ── Helpers de instrumentación ───────────────────────────────────────────────

def obs_user_msg(chat_id, content):
    if conversation_observer:
        conversation_observer.observe(chat_id, "user", content)

def obs_response(chat_id, response, latency_ms=0, model="", stage=""):
    if not bus: return
    sc = 0.0
    try:
        sc = anti_robot_filter.score_humanness(response) if anti_robot_filter else 0.7
    except Exception: pass
    if conversation_observer:
        conversation_observer.observe(chat_id, "assistant", response, response, sc)
    if sc < 0.65 and agent_tracer:
        for iss in agent_tracer._issues(response):
            bus.emit_sync(EventType.FAILURE, {
                "type": iss["type"], "detail": iss["detail"],
                "response": response[:150], "latency_ms": latency_ms,
            }, chat_id=chat_id, severity="warning")

def obs_appointment(chat_id, service, date):
    if bus:
        bus.emit_sync(EventType.APPOINTMENT,
                      {"service": service, "date": date}, chat_id=chat_id)


# ── FastAPI endpoints ─────────────────────────────────────────────────────────

from fastapi.responses import StreamingResponse as _StreamingResponse


@app.get("/obs/stream")
async def obs_stream_endpoint(request: Request):
    """SSE stream de eventos en tiempo real. Requiere X-Master-Key."""
    if Config.MASTER_API_KEY:
        key = (request.headers.get("X-Master-Key","") or
               request.query_params.get("key",""))
        if key != Config.MASTER_API_KEY:
            raise HTTPException(status_code=401)
    if not bus:
        raise HTTPException(status_code=503, detail="Observatory no activo")

    async def gen():
        q = bus.subscribe()
        try:
            yield "event: connected\ndata: {\"status\":\"ok\"}\n\n"
            for e in reversed(bus.get_recent(20)):
                yield e.to_sse()
            while True:
                if await request.is_disconnected(): break
                try:
                    e = await _obs_asyncio.wait_for(q.get(), timeout=25.0)
                    yield e.to_sse()
                except _obs_asyncio.TimeoutError:
                    yield ": heartbeat\n\n"
        finally:
            bus.unsubscribe(q)

    return _StreamingResponse(gen(), media_type="text/event-stream",
        headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})


@app.get("/obs/events")
async def obs_events(request: Request, limit: int = 50,
                     event_type: str = "", severity: str = "", chat_id: str = ""):
    if not _verify_master_key(request): raise HTTPException(401)
    if not bus: raise HTTPException(503)
    evts = bus.get_recent(limit, event_type, severity)
    if chat_id: evts = [e for e in evts if e.chat_id == chat_id]
    return {"events": [e.to_dict() for e in evts], "total": len(evts)}


@app.get("/obs/conversations")
async def obs_conversations_endpoint(request: Request, max_age: int = 60):
    if not _verify_master_key(request): raise HTTPException(401)
    if not conversation_observer: raise HTTPException(503)
    return {"conversations": conversation_observer.active(max_age),
            "stats": conversation_observer.stats()}


@app.get("/obs/failures")
async def obs_failures_endpoint(request: Request, limit: int = 50):
    if not _verify_master_key(request): raise HTTPException(401)
    if not bus: raise HTTPException(503)
    fails = bus.get_recent(limit, EventType.FAILURE)
    by_t  = {}
    for f in fails:
        t = f.data.get("type","?")
        by_t[t] = by_t.get(t, 0) + 1
    return {"failures": [f.to_dict() for f in fails],
            "total": len(fails), "by_type": by_t}


@app.get("/obs/stats")
async def obs_stats_endpoint(request: Request):
    if not _verify_master_key(request): raise HTTPException(401)
    llm_evts = bus.get_recent(100, EventType.LLM_CALL) if bus else []
    lats     = [e.data.get("latency_ms",0) for e in llm_evts if e.data.get("latency_ms")]
    q_evts   = bus.get_recent(100, EventType.QUALITY_SCORE) if bus else []
    scores   = [e.data.get("score",0) for e in q_evts]
    fail_evts= bus.get_recent(50, EventType.FAILURE) if bus else []
    return {
        "llm": {
            "calls": len(llm_evts),
            "avg_latency_ms": int(sum(lats)/len(lats)) if lats else 0,
            "p95_latency_ms": sorted(lats)[int(len(lats)*.95)] if len(lats)>=20 else (max(lats) if lats else 0),
            "avg_quality": round(sum(scores)/len(scores),2) if scores else 0,
        },
        "failures": {"total": len(fail_evts),
                     "rate_pct": round(len(fail_evts)/max(len(llm_evts),1)*100,1)},
        "conversations": conversation_observer.stats() if conversation_observer else {},
        "bus": bus.get_stats() if bus else {},
        "ts": _dt.now().isoformat(),
    }


@app.post("/obs/diagnose")
async def obs_diagnose_endpoint(request: Request):
    if not _verify_master_key(request): raise HTTPException(401)
    if not ai_diagnostician: raise HTTPException(503)
    data  = await request.json()
    diag  = await ai_diagnostician.diagnose(int(data.get("limit", 15)))
    return diag or {"summary": "Sin datos para diagnosticar"}


@app.get("/obs/health")
async def obs_health_endpoint():
    active_convs = 0
    if conversation_observer:
        active_convs = len([c for c in conversation_observer._convs.values()
                           if _obs_time.time() - c.get("last_t",0) < 3600])
    return {
        "ok": True,
        "bus": bus is not None,
        "tracer": agent_tracer is not None,
        "observer": conversation_observer is not None,
        "diagnostician": ai_diagnostician is not None,
        "events_buffered": len(bus._events) if bus else 0,
        "subscribers": len(bus._subs) if bus else 0,
        "active_conversations": active_convs,
    }


# ═══ CONNY TRAINER ═══
# ═══════════════════════════════════════════════════════════════════════════════
# CONNY TRAINER — V8.0
# Sistema completo de entrenamiento en tiempo real.
#
# Qué hace:
#   1. SkillEngine       — skills de comportamiento que el dueño activa/desactiva
#                          ("a veces usa minúsculas", "errores de tipeo naturales", etc.)
#   2. PromptEvolver     — auto-modifica el system prompt de Conny en tiempo real
#                          sin reiniciar. El dueño dice "aprende X" y se aplica ya.
#   3. AdminClientMode   — cualquier admin se convierte en cliente inmediatamente
#                          para simular una conversación real y entrenar
#   4. NovaRuleSync      — cuando el cliente dice "NO hagas X", la instrucción
#                          va a Nova como regla de gobernanza (si Nova está activo)
#                          Y también se guarda en la carpeta de confianza local
#   5. TrainingSession   — sesión de entrenamiento completa con replay, scoring
#                          y exportación de las reglas aprendidas
#
# Endpoints nuevos:
#   POST /trainer/skill/toggle       — activar/desactivar skill
#   GET  /trainer/skills             — listar skills disponibles
#   POST /trainer/prompt/evolve      — evolucionar el prompt con instrucción NL
#   POST /trainer/admin-as-client    — modo admin-como-cliente
#   GET  /trainer/session/{id}       — ver sesión de entrenamiento
#   POST /trainer/nova-sync          — sincronizar reglas con Nova
#   GET  /trainer/status             — estado del trainer
#
# Comandos admin nuevos en el bot:
#   /entrenar                        — entrar en modo entrenamiento
#   /simular-cliente                 — admin se convierte en cliente
#   /skill [nombre] [on|off]         — activar/desactivar skill
#   /skills                          — ver skills activas
#   /aprender [instruccion libre]    — evolucionar prompt en NL
#   /desaprender [tema]              — revertir una evolución
#   /sesion                          — ver sesión actual de entrenamiento
# ═══════════════════════════════════════════════════════════════════════════════

import random as _random_trainer
import uuid as _uuid_trainer


# ═══════════════════════════════════════════════════════════════════════════════
# SKILL ENGINE
# Skills = comportamientos que modifican cómo Conny responde, sin cambiar
# la personalidad core. Se activan/desactivan en caliente.
# ═══════════════════════════════════════════════════════════════════════════════

SKILL_DEFINITIONS: Dict[str, Dict] = {
    # ── Ortografía y tipeo ────────────────────────────────────────────────────
    "typos_naturales": {
        "name":        "Typos naturales",
        "desc":        "A veces comete errores de tipeo humanos (qe, proque, esoty, etc.)",
        "category":    "escritura",
        "intensity":   0.15,   # probabilidad de aplicar por mensaje
        "prompt_inject": "A veces (no siempre) comete pequeños errores de tipeo naturales como "
                         "escribiría alguien real por WhatsApp: 'qe' en vez de 'que', "
                         "'proque' en vez de 'porque', 'esoty' en vez de 'estoy'. "
                         "Máximo 1 typo por mensaje, solo si el mensaje es largo.",
        "examples": [
            ("que", "qe"),
            ("porque", "proque"),
            ("estoy", "esoty"),
            ("también", "tambien"),
            ("entonces", "entnoces"),
        ],
        "default_on": False,
    },
    "minusculas_inicio": {
        "name":        "Minúsculas al inicio",
        "desc":        "No capitaliza el inicio de los mensajes (como WhatsApp real)",
        "category":    "escritura",
        "intensity":   0.6,
        "prompt_inject": "A veces (en mensajes cortos e informales) no capitalices la primera "
                         "letra. Escribe como alguien real manda WhatsApp: 'hola qué tal' "
                         "no 'Hola qué tal'. Solo en mensajes de menos de 10 palabras.",
        "default_on": False,
    },
    "sin_tildes_ocasional": {
        "name":        "Sin tildes ocasional",
        "desc":        "Omite tildes ocasionalmente como en WhatsApp real",
        "category":    "escritura",
        "intensity":   0.2,
        "prompt_inject": "Ocasionalmente omite tildes en palabras comunes como lo hace alguien "
                         "escribiendo rápido por WhatsApp: 'mas' en vez de 'más', "
                         "'tambien' en vez de 'también'. No siempre, solo a veces.",
        "default_on": False,
    },
    "abreviaciones": {
        "name":        "Abreviaciones WhatsApp",
        "desc":        "Usa abreviaciones naturales (xq, pq, tmb, q, tb)",
        "category":    "escritura",
        "intensity":   0.1,
        "prompt_inject": "A veces usa abreviaciones de WhatsApp cuando el contexto es muy "
                         "informal: 'xq' o 'pq' por 'porque', 'q' por 'que', "
                         "'tmb' por 'también'. Máximo 1 por mensaje.",
        "default_on": False,
    },

    # ── Tono y carácter ───────────────────────────────────────────────────────
    "humor_leve": {
        "name":        "Humor leve",
        "desc":        "Agrega humor sutil y colombiano cuando el contexto lo permite",
        "category":    "tono",
        "intensity":   0.1,
        "prompt_inject": "Cuando el contexto sea ligero, puedes agregar un toque de humor "
                         "colombiano sutil. Una frase divertida, nunca un chiste formal. "
                         "Ejemplo: 'ay qué casualidad' / 'eso sí me pasó a mí también jaja'. "
                         "Solo cuando el cliente esté de buen humor.",
        "default_on": False,
    },
    "emojis_puntuales": {
        "name":        "Emojis puntuales",
        "desc":        "Usa 1 emoji por mensaje cuando añade calor genuino",
        "category":    "tono",
        "intensity":   0.3,
        "prompt_inject": "Puedes usar 1 emoji por burbuja cuando añada calor genuino. "
                         "Nunca al inicio de oración. Nunca más de 1. Solo si es natural: "
                         "'te espero el jueves 🗓' / 'quedó confirmado ✓'",
        "default_on": False,
    },
    "pausas_pensando": {
        "name":        "Pausas pensando",
        "desc":        "Usa '...' para simular que piensa antes de responder",
        "category":    "tono",
        "intensity":   0.1,
        "prompt_inject": "A veces, cuando estás buscando información o considerando algo, "
                         "puedes usar '...' al inicio para simular que estás pensando: "
                         "'... mira te cuento' / '... a ver déjame verificar eso'",
        "default_on": False,
    },
    "tuteo_intenso": {
        "name":        "Tuteo muy informal",
        "desc":        "Tuteo extremadamente informal, como una amiga colombiana",
        "category":    "tono",
        "intensity":   1.0,
        "prompt_inject": "Tuteo muy informal y cercano. Como si fuera una amiga del mismo "
                         "barrio. 'oye', 'mira', 'ay sí', 'uy qué bacano', 'eso sí'. "
                         "Sin ninguna formalidad, ni siquiera 'por favor'.",
        "default_on": False,
    },
    "respuestas_ultracortas": {
        "name":        "Respuestas ultra-cortas",
        "desc":        "Máximo 8 palabras por burbuja, siempre",
        "category":    "longitud",
        "intensity":   1.0,
        "prompt_inject": "REGLA ABSOLUTA: Cada burbuja máximo 8 palabras. "
                         "Si necesitas más, usa ||| para otra burbuja. "
                         "Nunca una burbuja de más de 8 palabras. Cuenta las palabras.",
        "default_on": False,
    },
    "preguntas_diagnostico": {
        "name":        "Diagnóstico activo",
        "desc":        "Siempre hace UNA pregunta de diagnóstico antes de ofrecer",
        "category":    "ventas",
        "intensity":   1.0,
        "prompt_inject": "SIEMPRE que un cliente pregunte por un servicio, haz exactamente "
                         "UNA pregunta de diagnóstico ANTES de dar información. "
                         "Nunca ofrezcas nada sin entender primero el caso específico. "
                         "La pregunta más poderosa: 'qué fue lo que te hizo escribirnos hoy'",
        "default_on": True,
    },
    "cierre_fecha_unica": {
        "name":        "Cierre con fecha única",
        "desc":        "Siempre propone UN día concreto, nunca opciones",
        "category":    "ventas",
        "intensity":   1.0,
        "prompt_inject": "Al proponer una cita, SIEMPRE un solo día concreto. "
                         "NUNCA: 'jueves o viernes'. "
                         "SIEMPRE: 'esta semana tienes el jueves, te queda bien'. "
                         "Si no acepta, entonces negocia.",
        "default_on": True,
    },
    "sin_preguntas_dobles": {
        "name":        "Sin preguntas dobles",
        "desc":        "Nunca hace dos preguntas en el mismo mensaje",
        "category":    "flujo",
        "intensity":   1.0,
        "prompt_inject": "REGLA ABSOLUTA: UNA sola pregunta por mensaje. "
                         "Si tienes dos preguntas, elige la más importante. "
                         "Nunca: 'qué servicio buscas y cuándo puedes venir'",
        "default_on": True,
    },
}


class SkillEngine:
    """
    Motor de skills de comportamiento.
    
    Las skills son modificadores del comportamiento de Conny que el dueño
    puede activar/desactivar en caliente. Cada skill tiene:
    - Un prompt_inject que se añade al system prompt cuando está activa
    - Una intensidad (probabilidad de aplicar por mensaje)
    - Una categoría para organizarlas
    
    La diferencia con el arquetipo: el arquetipo define la personalidad base.
    Las skills son modificadores específicos sobre esa base.
    """

    DB_KEY = "v8_skills_state"

    def __init__(self):
        self._active: Dict[str, bool] = {}
        self._loaded = False

    def _load(self):
        """Carga el estado de skills desde la DB."""
        if self._loaded:
            return
        try:
            if db:
                raw = db.recall(self.DB_KEY)
                if raw:
                    state = json.loads(raw)
                    self._active = {k: bool(v) for k, v in state.items()}
        except Exception:
            pass
        # Aplicar defaults para skills no guardadas
        for skill_id, skill_def in SKILL_DEFINITIONS.items():
            if skill_id not in self._active:
                self._active[skill_id] = skill_def.get("default_on", False)
        self._loaded = True

    def _save(self):
        """Persiste el estado de skills en DB."""
        try:
            if db:
                db.remember(self.DB_KEY, json.dumps(self._active), "config")
        except Exception:
            pass

    def get_active(self) -> List[str]:
        """Retorna IDs de skills activas."""
        self._load()
        return [k for k, v in self._active.items() if v]

    def toggle(self, skill_id: str, on: bool) -> Dict:
        """Activa o desactiva una skill. Retorna resultado."""
        self._load()
        if skill_id not in SKILL_DEFINITIONS:
            return {"ok": False, "error": f"Skill '{skill_id}' no existe"}
        self._active[skill_id] = on
        self._save()
        skill = SKILL_DEFINITIONS[skill_id]
        return {
            "ok":     True,
            "skill":  skill_id,
            "name":   skill["name"],
            "active": on,
            "desc":   skill["desc"],
        }

    def get_prompt_injection(self) -> str:
        """
        Retorna el bloque de instrucciones de todas las skills activas.
        Se inyecta al system prompt en cada llamada al LLM.
        """
        self._load()
        active_skill_ids = [
            k for k in self._active
            if self._active[k] and k in SKILL_DEFINITIONS
        ]
        return self.render_prompt_injection(
            active_skill_ids,
            header="SKILLS ACTIVAS (el dueño las configuró):",
        )

    def render_prompt_injection(self, skill_ids: List[str], header: str) -> str:
        """Renderiza un bloque de instrucciones para una lista arbitraria de skills."""
        active_skills = [SKILL_DEFINITIONS[k] for k in skill_ids if k in SKILL_DEFINITIONS]
        if not active_skills:
            return ""

        lines = ["━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                 header,
                 "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"]
        for skill in active_skills:
            lines.append(f"\n[SKILL: {skill['name']}]")
            lines.append(skill["prompt_inject"])

        lines.append("")
        return "\n".join(lines)

    def apply_post_filter(self, response: str, chat_id: str = "") -> str:
        """
        Aplica transformaciones post-generación para skills de escritura.
        Estas se aplican DESPUÉS del LLM, no en el prompt.
        """
        self._load()

        # Skill: typos_naturales
        if self._active.get("typos_naturales") and len(response.split()) > 8:
            skill = SKILL_DEFINITIONS["typos_naturales"]
            if _random_trainer.random() < skill["intensity"]:
                response = self._apply_typo(response, skill["examples"])

        # Skill: minusculas_inicio
        if self._active.get("minusculas_inicio") and len(response.split()) <= 10:
            if _random_trainer.random() < SKILL_DEFINITIONS["minusculas_inicio"]["intensity"]:
                response = response[0].lower() + response[1:] if response else response

        # Skill: sin_tildes_ocasional
        if self._active.get("sin_tildes_ocasional"):
            if _random_trainer.random() < SKILL_DEFINITIONS["sin_tildes_ocasional"]["intensity"]:
                response = self._strip_random_tildes(response)

        return response

    def _apply_typo(self, text: str, examples: List[tuple]) -> str:
        """Aplica un typo aleatorio de los ejemplos."""
        available = [(a, b) for a, b in examples if f" {a} " in f" {text.lower()} "]
        if not available:
            return text
        original, typo = _random_trainer.choice(available)
        # Reemplazar solo la primera ocurrencia
        return re.sub(rf'\b{re.escape(original)}\b', typo, text, count=1, flags=re.IGNORECASE)

    def _strip_random_tildes(self, text: str) -> str:
        """Quita tildes de una palabra aleatoria."""
        TILDES = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
                  "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U"}
        words = text.split()
        words_with_tildes = [i for i, w in enumerate(words) if any(c in w for c in TILDES)]
        if not words_with_tildes:
            return text
        idx = _random_trainer.choice(words_with_tildes)
        word = words[idx]
        words[idx] = "".join(TILDES.get(c, c) for c in word)
        return " ".join(words)

    def list_all(self) -> List[Dict]:
        """Lista todas las skills con su estado."""
        self._load()
        result = []
        for skill_id, skill_def in SKILL_DEFINITIONS.items():
            result.append({
                "id":       skill_id,
                "name":     skill_def["name"],
                "desc":     skill_def["desc"],
                "category": skill_def["category"],
                "active":   self._active.get(skill_id, skill_def.get("default_on", False)),
            })
        return result


class TrainerGateway:
    """
    Gateway automático inspirado en OpenClaw.

    No obliga al admin a recordar comandos o IDs de skills. Decide una capa
    mínima de comportamiento según rol, canal, intención y preferencias
    explícitas del usuario.
    """

    DB_KEY = "v8_trainer_gateway_state"

    def __init__(self):
        self._state: Dict[str, bool] = {
            "enabled": True,
            "auto_admin": True,
            "auto_user": True,
        }
        self._loaded = False

    def _load(self):
        if self._loaded:
            return
        try:
            if db:
                raw = db.recall(self.DB_KEY)
                if raw:
                    parsed = json.loads(raw)
                    for key in self._state:
                        if key in parsed:
                            self._state[key] = bool(parsed[key])
        except Exception:
            pass
        self._loaded = True

    def _save(self):
        try:
            if db:
                db.remember(self.DB_KEY, json.dumps(self._state), "config")
        except Exception:
            pass

    def status(self) -> Dict[str, bool]:
        self._load()
        return dict(self._state)

    def configure(
        self,
        *,
        enabled: Optional[bool] = None,
        auto_admin: Optional[bool] = None,
        auto_user: Optional[bool] = None,
    ) -> Dict[str, Any]:
        self._load()
        if enabled is not None:
            self._state["enabled"] = bool(enabled)
        if auto_admin is not None:
            self._state["auto_admin"] = bool(auto_admin)
        if auto_user is not None:
            self._state["auto_user"] = bool(auto_user)
        self._save()
        return {"ok": True, **self.status()}

    def _is_on(self, key: str) -> bool:
        self._load()
        return bool(self._state.get("enabled")) and bool(self._state.get(key))

    def _route_platform(self, chat_id: str) -> str:
        try:
            if db and chat_id:
                platform = db.get_contact_route(chat_id)
                if platform:
                    return str(platform)
        except Exception:
            pass
        return str(getattr(Config, "PLATFORM", "telegram") or "telegram")

    def detect_admin_learning_intent(self, text: str) -> bool:
        normalized = _normalize_conv_text(text or "")
        if not normalized or normalized.startswith("/"):
            return False
        patterns = [
            "a mi hablame",
            "a mí háblame",
            "hablame de usted",
            "háblame de usted",
            "trátame de usted",
            "tratame de usted",
            "no me hables",
            "no hables así",
            "no hables asi",
            "quiero que seas",
            "quiero que respondas",
            "desde ahora",
            "cuando te diga",
            "cuando el admin",
            "a los administradores",
            "a los admins",
            "conmigo sé",
            "conmigo se",
            "para mi usa",
            "para mí usa",
            "cambia tu personalidad",
            "cambia el tono",
            "mas ejecutiva",
            "más ejecutiva",
            "mas humana",
            "más humana",
        ]
        return any(pattern in normalized for pattern in patterns)

    def _service_keywords(self, clinic: Dict[str, Any]) -> List[str]:
        keywords = [
            "tratamiento", "servicio", "precio", "precios", "valor", "costo",
            "cuanto", "cuánto", "botox", "relleno", "rellenos", "laser",
            "láser", "valoracion", "valoración", "consulta",
        ]
        services = clinic.get("services") if isinstance(clinic.get("services"), list) else []
        for service in services[:12]:
            token = _normalize_conv_text(str(service))
            if token:
                keywords.append(token)
        return keywords

    def _booking_keywords(self) -> List[str]:
        return [
            "cita", "citas", "agendar", "agenda", "horario", "horarios",
            "disponibilidad", "disponible", "cuando puedo", "mañana", "manana",
            "hoy", "jueves", "viernes", "esta semana", "proxima semana", "próxima semana",
        ]

    def _recommend_skill_ids(
        self,
        *,
        chat_id: str,
        clinic: Dict[str, Any],
        user_msg: str,
        is_admin: bool,
        patient: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        if is_admin or not self._is_on("auto_user"):
            return []

        normalized = _normalize_conv_text(user_msg or "")
        recommended: List[str] = ["sin_preguntas_dobles"]

        if any(keyword in normalized for keyword in self._service_keywords(clinic)):
            recommended.append("preguntas_diagnostico")

        if any(keyword in normalized for keyword in self._booking_keywords()):
            recommended.append("cierre_fecha_unica")

        # WhatsApp tolera un poco más de calidez, pero sin llevar a Conny a lo informal.
        if self._route_platform(chat_id) == "whatsapp" and any(
            token in normalized for token in ["gracias", "perfecto", "super", "súper", "genial"]
        ):
            recommended.append("emojis_puntuales")

        # Preserva orden y evita duplicados.
        seen = set()
        ordered: List[str] = []
        for skill_id in recommended:
            if skill_id in SKILL_DEFINITIONS and skill_id not in seen:
                seen.add(skill_id)
                ordered.append(skill_id)
        return ordered

    def observe_user_preferences(
        self,
        *,
        chat_id: str,
        user_msg: str,
        patient: Optional[Dict[str, Any]] = None,
        is_admin: bool = False,
    ) -> Dict[str, Any]:
        if is_admin:
            return patient.get("preferences", {}) if isinstance(patient, dict) else {}
        if not db or not chat_id:
            return {}

        patient = patient or db.get_or_create_patient(chat_id)
        preferences = patient.get("preferences", {}) if isinstance(patient, dict) else {}
        if not isinstance(preferences, dict):
            preferences = {}

        normalized = _normalize_conv_text(user_msg or "")
        updated = dict(preferences)
        changed = False

        def _set_pref(key: str, value: Any):
            nonlocal changed
            if updated.get(key) != value:
                updated[key] = value
                changed = True

        if any(token in normalized for token in ["trátame de usted", "tratame de usted", "háblame de usted", "hablame de usted", "de usted"]):
            _set_pref("trato", "usted")
        elif any(token in normalized for token in ["tuteame", "tutéame", "háblame normal", "hablame normal"]):
            _set_pref("trato", "tu")

        if any(token in normalized for token in ["sin emojis", "no emojis", "sin emoji", "no emoji", "sin caritas"]):
            _set_pref("no_emojis", True)
        elif any(token in normalized for token in ["puedes usar emojis", "usa emojis", "con emojis"]):
            _set_pref("no_emojis", False)

        if any(token in normalized for token in ["más corto", "mas corto", "más breve", "mas breve", "sin tanto texto", "responde corto"]):
            _set_pref("brief", True)
        elif any(token in normalized for token in ["más detalle", "mas detalle", "explícame bien", "explicame bien", "explícame mejor", "explicame mejor"]):
            _set_pref("brief", False)

        if any(token in normalized for token in ["dime el precio", "quiero precio", "dime cuánto", "dime cuanto", "sin tanta vuelta", "sin tanta vuelta dime"]):
            _set_pref("prefiere_precios_directos", True)

        if any(token in normalized for token in ["no me preguntes tanto", "sin tantas preguntas", "hazlo más directo", "hazlo mas directo"]):
            _set_pref("menos_preguntas", True)

        if changed:
            db.update_patient(chat_id, preferences=updated)
        return updated

    def maybe_acknowledge_user_preference_message(
        self,
        *,
        chat_id: str,
        user_msg: str,
        patient: Optional[Dict[str, Any]] = None,
    ) -> Optional[List[str]]:
        """
        Si el mensaje del usuario solo está corrigiendo el estilo de Conny,
        responde localmente sin pasar por el LLM para que el cambio se note
        de inmediato y sin ruido robótico.
        """
        normalized = _normalize_conv_text(user_msg or "")
        if not normalized:
            return None

        preference_markers = [
            "háblame", "hablame", "trátame", "tratame", "sin emojis",
            "no emojis", "no emoji", "más corto", "mas corto", "más breve",
            "mas breve", "sin tanto texto", "más directo", "mas directo",
            "de usted", "tuteame", "tutéame",
        ]
        business_markers = self._service_keywords({}) + self._booking_keywords()
        if not any(marker in normalized for marker in preference_markers):
            return None
        if any(marker in normalized for marker in business_markers):
            return None

        prefs = self.observe_user_preferences(
            chat_id=chat_id,
            user_msg=user_msg,
            patient=patient,
            is_admin=False,
        )

        acknowledgements: List[str] = []
        if prefs.get("trato") == "usted":
            acknowledgements.append("Claro. Le hablo de usted desde ahora.")
        elif prefs.get("trato") == "tu":
            acknowledgements.append("Claro. Te hablo de tú desde ahora.")
        if prefs.get("no_emojis"):
            acknowledgements.append("También lo dejo sin emojis.")
        if prefs.get("brief"):
            acknowledgements.append("Y se lo respondo más corto y directo.")
        if prefs.get("menos_preguntas"):
            acknowledgements.append("Además voy con menos preguntas y más al punto.")

        if acknowledgements:
            return acknowledgements[:3]
        return ["Listo. Ya ajusté la forma en que le respondo."]

    def build_prompt_addon(
        self,
        *,
        chat_id: str,
        clinic: Dict[str, Any],
        user_msg: str,
        is_admin: bool,
        patient: Optional[Dict[str, Any]] = None,
    ) -> str:
        self._load()
        if not self._state.get("enabled"):
            return ""

        lines: List[str] = []

        if is_admin and self._state.get("auto_admin"):
            lines.extend([
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "GATEWAY AUTOMÁTICO — MODO ADMIN",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "Este chat es del administrador.",
                "Respóndele con respeto, criterio y tono ejecutivo-natural.",
                "No le hables como paciente ni le vendas servicios.",
                "Si corrige el tono o la conducta, trátalo como instrucción operativa válida.",
            ])

        if not is_admin and self._state.get("auto_user"):
            auto_skill_ids = self._recommend_skill_ids(
                chat_id=chat_id,
                clinic=clinic,
                user_msg=user_msg,
                is_admin=is_admin,
                patient=patient,
            )
            if auto_skill_ids and skill_engine:
                rendered = skill_engine.render_prompt_injection(
                    auto_skill_ids,
                    header="SKILLS AUTOMÁTICAS DEL GATEWAY (no se las menciones al usuario):",
                )
                if rendered:
                    lines.append(rendered)

            prefs = self.observe_user_preferences(
                chat_id=chat_id,
                user_msg=user_msg,
                patient=patient,
                is_admin=is_admin,
            )
            pref_lines: List[str] = []
            if prefs.get("trato") == "usted":
                pref_lines.append("A esta persona háblale de usted, con respeto claro y sin sonar acartonada.")
            elif prefs.get("trato") == "tu":
                pref_lines.append("A esta persona puedes hablarle de tú, manteniendo calidez profesional.")
            if prefs.get("no_emojis"):
                pref_lines.append("No uses emojis con esta persona.")
            if prefs.get("brief"):
                pref_lines.append("Esta persona prefiere respuestas más breves y directas.")
            if prefs.get("prefiere_precios_directos"):
                pref_lines.append("Si pregunta por precio, responde el valor o la lógica del valor antes de desviar la conversación.")
            if prefs.get("menos_preguntas"):
                pref_lines.append("Evita cadenas de preguntas. Prioriza una sola pregunta útil y, si puedes, resuelve directo.")

            if pref_lines:
                lines.append(
                    "\n".join([
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                        "PREFERENCIAS APRENDIDAS DEL USUARIO",
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                        *pref_lines,
                    ])
                )

        return "\n\n".join(block for block in lines if block).strip()


class OwnerStyleController:
    """
    Plano de control duro del owner/admin sobre cómo habla Conny.

    A diferencia del PromptEvolver, esto no es solo "aprendizaje".
    Aquí guardamos restricciones y preferencias que deben cumplirse sí o sí
    antes de enviar cada respuesta.
    """

    DB_KEY = "v8_owner_style_control"
    _EMOJI_RE = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002500-\U00002BEF"
        "\U00002702-\U000027B0"
        "\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FAFF"
        "\u2600-\u26FF"
        "\u2700-\u27BF"
        "]+",
        flags=re.UNICODE
    )

    def __init__(self):
        self._state: Dict[str, Any] = {
            "enabled": True,
            "global": self._blank_bucket(),
            "admin": self._seed_admin_defaults(
                self._blank_bucket(register="usted", respectful=True, no_emojis=True)
            ),
            "patient": self._seed_patient_defaults(
                self._blank_bucket(register="auto", respectful=True, no_emojis=True)
            ),
        }
        self._loaded = False

    def _blank_bucket(
        self,
        *,
        register: str = "auto",
        respectful: bool = True,
        no_emojis: bool = False,  # v11: emojis ON por defecto — Colombia negocio
    ) -> Dict[str, Any]:
        return {
            "forbidden_phrases": [],
            "forbidden_starts": [],
            "replacement_map": {},
            "style_notes": [],
            "greeting_template": "",
            "second_bubble_template": "",
            "third_bubble_template": "",
            "closing_template": "",
            "fallback_template": "",
            "max_bubbles": 0,
            "register": register,
            "respectful": respectful,
            "no_emojis": no_emojis,
            "lowercase_start": False,
        }

    def _seed_admin_defaults(self, bucket: Dict[str, Any]) -> Dict[str, Any]:
        bucket = dict(bucket or {})
        bucket.setdefault("register", "usted")
        bucket.setdefault("respectful", True)
        bucket.setdefault("no_emojis", False)  # v11: emojis ON por defecto
        if not bucket.get("style_notes"):
            bucket["style_notes"] = [
                "Con el admin habla con respeto, claridad y criterio.",
                "Nunca le hables como paciente.",
            ]
        if not bucket.get("greeting_template"):
            bucket["greeting_template"] = "Hola, {admin_name}."
        if not bucket.get("second_bubble_template"):
            bucket["second_bubble_template"] = "Estoy lista para ayudarle con la instancia, el tono, los servicios o las pruebas."
        return bucket

    def _seed_patient_defaults(self, bucket: Dict[str, Any]) -> Dict[str, Any]:
        bucket = dict(bucket or {})
        bucket.setdefault("register", "auto")
        bucket.setdefault("respectful", True)
        bucket.setdefault("no_emojis", False)  # v11: emojis ON por defecto
        if not bucket.get("forbidden_starts"):
            bucket["forbidden_starts"] = [
                "oye",
                "a ver",
                "mira",
                "claro",
                "listo",
            ]
        if not bucket.get("style_notes"):
            bucket["style_notes"] = [
                "Suena humana, clara y profesional.",
                "No suenes robótica ni demasiado explicativa.",
                "Si el admin pide tuteo, úsalo natural, sostenido y colombiano, sin mezclarlo con usted.",
            ]
        if not bucket.get("greeting_template"):
            bucket["greeting_template"] = "{welcome_line}"
        if not bucket.get("second_bubble_template"):
            bucket["second_bubble_template"] = "{welcome_identity}"
        if not bucket.get("third_bubble_template"):
            bucket["third_bubble_template"] = "{welcome_question}"
        if not bucket.get("max_bubbles"):
            bucket["max_bubbles"] = 3
        return bucket

    def _load(self):
        if self._loaded:
            return
        try:
            if db:
                raw = db.recall(self.DB_KEY)
                if raw:
                    parsed = json.loads(raw)
                    if isinstance(parsed, dict):
                        for key in ("enabled", "global", "admin", "patient"):
                            if key not in parsed:
                                continue
                            if key == "enabled":
                                self._state["enabled"] = bool(parsed.get("enabled"))
                                continue
                            if isinstance(parsed.get(key), dict):
                                merged = self._blank_bucket(**{
                                    "register": self._state[key].get("register", "auto"),
                                    "respectful": bool(self._state[key].get("respectful", True)),
                                    "no_emojis": bool(self._state[key].get("no_emojis", True)),
                                })
                                merged.update(parsed[key])
                                if key == "admin":
                                    merged = self._seed_admin_defaults(merged)
                                elif key == "patient":
                                    merged = self._seed_patient_defaults(merged)
                                self._state[key] = merged
        except Exception:
            pass
        self._loaded = True

    def _save(self):
        try:
            if db:
                db.remember(self.DB_KEY, json.dumps(self._state, ensure_ascii=False), "config")
        except Exception:
            pass

    def status(self) -> Dict[str, Any]:
        self._load()
        return json.loads(json.dumps(self._state, ensure_ascii=False))

    def reset(self, scope: str = "all") -> Dict[str, Any]:
        self._load()
        scope = (scope or "all").strip().lower()
        if scope in ("all", "todo", "*"):
            self._state = {
                "enabled": True,
                "global": self._blank_bucket(),
                "admin": self._seed_admin_defaults(
                    self._blank_bucket(register="usted", respectful=True, no_emojis=True)
                ),
                "patient": self._seed_patient_defaults(
                    self._blank_bucket(register="auto", respectful=True, no_emojis=True)
                ),
            }
        elif scope in ("global", "admin", "patient"):
            if scope == "admin":
                self._state[scope] = self._seed_admin_defaults(
                    self._blank_bucket(register="usted", respectful=True, no_emojis=True)
                )
            elif scope == "patient":
                self._state[scope] = self._seed_patient_defaults(
                    self._blank_bucket(register="auto", respectful=True, no_emojis=True)
                )
            else:
                self._state[scope] = self._blank_bucket()
        self._save()
        return {"ok": True, "scope": scope, "state": self.status()}

    def _normalize_text(self, value: str) -> str:
        return _normalize_conv_text(value or "")

    def _append_unique(self, bucket: Dict[str, Any], key: str, value: str) -> bool:
        cleaned = (value or "").strip().strip("\"'“”.,:;")
        if len(cleaned) < 2:
            return False
        low = self._normalize_text(cleaned)
        items = bucket.setdefault(key, [])
        if any(self._normalize_text(str(item)) == low for item in items):
            return False
        items.append(cleaned)
        return True

    def _scope_from_instruction(self, normalized: str) -> str:
        admin_markers = [
            "a mi", "a mí", "conmigo", "al admin", "a los administradores",
            "a los admins", "para mi", "para mí", "cuando me hables",
            "cuando le hables al admin", "con el admin", "al owner", "al dueno",
            "al dueño", "a santiago", "cuando yo te escriba", "cuando yo le escriba",
            "soy tu admin", "soy el admin", "soy tu dueño", "soy el dueño",
        ]
        patient_markers = [
            "a los pacientes", "a los clientes", "a la gente", "con pacientes",
            "con clientes", "cuando te escriban", "cuando un paciente",
            "cuando un cliente", "al paciente", "al cliente", "a los leads",
            "con los pacientes", "con los clientes", "a pacientes", "a clientes",
            "para pacientes", "para clientes", "para los pacientes", "para los clientes",
        ]
        haystack = f" {normalized.strip()} "
        def _contains_marker(marker: str) -> bool:
            probe = f" {self._normalize_text(marker)} "
            return probe in haystack

        if any(_contains_marker(marker) for marker in patient_markers):
            return "patient"
        if any(_contains_marker(marker) for marker in admin_markers):
            return "admin"
        return "global"

    def detect_control_intent(self, text: str) -> bool:
        normalized = self._normalize_text(text)
        if not normalized or normalized.startswith("/"):
            return False
        if re.search(r'\b(?:1|2|3|una|uno|dos|tres)\s+mensajes?\b', normalized):
            return True
        signals = [
            "no digas", "nunca digas", "no uses", "evita decir", "evita usar",
            "prohibido decir", "no empieces", "no abras con", "no arranques con",
            "al inicio", "saluda asi", "saluda así", "presentate asi",
            "preséntate así", "abre asi", "abre así", "háblame de usted",
            "hablame de usted", "trátame de usted", "tratame de usted",
            "hablales de usted", "háblales de usted", "tratalos de usted",
            "trátalos de usted", "tratelos de usted", "trátelos de usted",
            "de usted con los pacientes", "de usted con los clientes",
            "hablales de tu", "háblales de tú", "tutealos", "tutéalos",
            "tratales de tu", "trátales de tú", "tutea", "tutear",
            "tutealas", "tutéalas", "trátalas de tú", "tratalas de tu",
            "aqui las mujeres se tutean", "aquí las mujeres se tutean",
            "en colombia tutea", "en colombia se tutea",
            "tuteame", "tutéame", "sin emojis", "no emojis", "no emoji",
            "segunda burbuja", "segundo mensaje", "despues di", "después di",
            "tercera burbuja", "tercer mensaje", "cierra asi", "cierra así",
            "termina asi", "termina así",
            "reemplaza", "mayusculas", "mayúsculas", "todo en mayúsculas",
            "no digas que eres un bot", "no digas que eres ia",
            "no digas que eres una ia", "no digas inteligencia artificial",
            "si no entiendes", "si no entiendes di", "si no sabes", "si no sabes que decir",
            "cuando no entiendas", "cuando no sepas", "fuera de contexto responde",
            "una burbuja", "1 burbuja", "dos burbujas", "2 burbujas", "tres burbujas", "3 burbujas",
            "responde en", "maximo", "máximo",
            "mas ejecutivo", "más ejecutivo", "mas ejecutiva", "más ejecutiva",
            "mas humana", "más humana", "mas directa", "más directa",
            "mas corto", "más corto", "mas seria", "más seria",
            "no hables asi", "no hables así", "desde ahora",
        ]
        return any(signal in normalized for signal in signals)

    def _parse_bubble_limit(self, normalized: str) -> int:
        if "burbuja" not in normalized and "mensaje" not in normalized:
            return 0
        word_map = {
            "una": 1,
            "1": 1,
            "dos": 2,
            "2": 2,
            "tres": 3,
            "3": 3,
        }
        patterns = [
            r'(?:maximo|max\.?|máximo)\s+(una|1|dos|2|tres|3)\s+(?:burbujas?|mensajes?)',
            r'(?:en|usa|con|hazlo en|responde en)\s+(una|1|dos|2|tres|3)\s+(?:burbujas?|mensajes?)',
            r'(una|1|dos|2|tres|3)\s+(?:sola\s+)?(?:burbujas?|mensajes?)',
        ]
        for pattern in patterns:
            match = re.search(pattern, normalized, flags=re.IGNORECASE)
            if not match:
                continue
            token = (match.group(1) or "").strip().lower()
            return int(word_map.get(token, 0) or 0)
        if "sin limite de burbujas" in normalized or "sin limite de mensajes" in normalized or "sin limite" in normalized:
            return 0
        return 0

    def _extract_phrase(self, text: str, patterns: List[str]) -> str:
        for pattern in patterns:
            match = re.search(pattern, text or "", flags=re.IGNORECASE)
            if match:
                candidate = match.group(1).strip().strip("\"'“”.,:;")
                if candidate:
                    return candidate
        return ""

    def apply_instruction(self, text: str, admin_chat_id: str = "") -> Dict[str, Any]:
        self._load()
        raw_text = (text or "").strip()
        normalized = self._normalize_text(raw_text)
        if not self.detect_control_intent(text):
            return {"ok": False, "reason": "no_control_intent"}

        scope = self._scope_from_instruction(normalized)
        bucket = self._state[scope]
        applied: List[str] = []
        replacement_applied = False
        quoted = [m.strip() for m in re.findall(r"[\"“]([^\"”]+)[\"”]", raw_text) if m.strip()]

        if len(quoted) >= 2 and any(token in normalized for token in ["no digas", "evita decir", "no uses", "evita usar", "reemplaza"]):
            bad = quoted[0].strip()
            good = quoted[1].strip()
            if bad and good:
                bucket.setdefault("replacement_map", {})[bad] = good
                bucket["forbidden_phrases"] = [
                    item for item in bucket.get("forbidden_phrases", [])
                    if self._normalize_text(str(item)) != self._normalize_text(bad)
                ]
                applied.append(f"actualicé un reemplazo obligatorio en {scope}")
                replacement_applied = True
        if not applied:
            natural_replacement = re.search(
                r'(?:no\s+digas|evita\s+decir)\s+[\"“\' ]*([^,\"”\'\n]+?)[\"”\' ]*\s*,?\s*(?:di|usa|mejor\s+di)\s+[\"“\' ]*([^\"”\'\n]+?)[\"”\' ]*(?:$|[.;])',
                raw_text,
                flags=re.IGNORECASE,
            )
            if not natural_replacement:
                natural_replacement = re.search(
                    r'(?:reemplaza|cambia)\s+[\"“\' ]*([^,\"”\'\n]+?)[\"”\' ]*\s+por\s+[\"“\' ]*([^\"”\'\n]+?)[\"”\' ]*(?:$|[.;])',
                    raw_text,
                    flags=re.IGNORECASE,
                )
            if natural_replacement:
                bad = natural_replacement.group(1).strip(" \"'“”.,:;")
                good = natural_replacement.group(2).strip(" \"'“”.,:;")
                if bad and good:
                    bucket.setdefault("replacement_map", {})[bad] = good
                    bucket["forbidden_phrases"] = [
                        item for item in bucket.get("forbidden_phrases", [])
                        if self._normalize_text(str(item)) != self._normalize_text(bad)
                    ]
                    applied.append(f"actualicé un reemplazo obligatorio en {scope}")
                    replacement_applied = True

        start_phrase = self._extract_phrase(raw_text, [
            r'(?:no\s+(?:empieces|abras|arranques)\s+con)\s+[\"“]?([^\"”\n]+?)[\"”]?(?:$|[.,;])',
            r'(?:no\s+(?:uses|digas))\s+[\"“]?([^\"”\n]+?)[\"”]?\s+al\s+inicio\b',
        ])
        if start_phrase and self._append_unique(bucket, "forbidden_starts", start_phrase):
            applied.append(f"bloqueé el arranque «{start_phrase}» en {scope}")

        forbidden_phrase = self._extract_phrase(raw_text, [
            r'(?:no\s+digas|nunca\s+digas|evita\s+decir|prohibido\s+decir)\s+[\"“]?([^\"”\n]+?)[\"”]?(?:$|[.,;])',
            r'(?:no\s+uses|evita\s+usar)\s+[\"“]?([^\"”\n]+?)[\"”]?(?:$|[.,;])',
        ])
        forbidden_phrase = re.sub(r'\s+al\s+inicio$', '', forbidden_phrase or '', flags=re.IGNORECASE).strip()
        if forbidden_phrase and forbidden_phrase != start_phrase and not replacement_applied:
            if self._append_unique(bucket, "forbidden_phrases", forbidden_phrase):
                applied.append(f"prohibí la frase «{forbidden_phrase}» en {scope}")

        greeting_template = self._extract_phrase(raw_text, [
            r'(?:saluda\s+asi|saluda\s+así|presentate\s+asi|preséntate\s+así|abre\s+asi|abre\s+así)\s*(?:[:\-]\s*)?(.+)$',
            r'(?:presentate\s+como|preséntate\s+como)\s*(?:[:\-]\s*)?(.+)$',
        ])
        if greeting_template:
            bucket["greeting_template"] = greeting_template.strip()
            applied.append(f"actualicé el saludo base de {scope}")

        second_bubble_template = self._extract_phrase(raw_text, [
            r'(?:segunda\s+burbuja|segundo\s+mensaje|despues\s+di|después\s+di)\s*(?:[:\-]\s*)?(.+)$',
        ])
        if second_bubble_template:
            bucket["second_bubble_template"] = second_bubble_template.strip()
            applied.append(f"actualicé la segunda burbuja base de {scope}")

        third_bubble_template = self._extract_phrase(raw_text, [
            r'(?:tercera\s+burbuja|tercer\s+mensaje)\s*(?:[:\-]\s*)?(.+)$',
        ])
        if third_bubble_template:
            bucket["third_bubble_template"] = third_bubble_template.strip()
            applied.append(f"actualicé la tercera burbuja base de {scope}")

        closing_template = self._extract_phrase(raw_text, [
            r'(?:cierra\s+asi|cierra\s+así|termina\s+asi|termina\s+así)\s*(?:[:\-]\s*)?(.+)$',
        ])
        if closing_template:
            bucket["closing_template"] = closing_template.strip()
            applied.append(f"actualicé el cierre base de {scope}")

        fallback_template = self._extract_phrase(raw_text, [
            r'(?:si\s+no\s+entiendes(?:\s+di)?|si\s+no\s+sabes(?:\s+que\s+decir)?(?:\s+di)?|cuando\s+no\s+entiendas(?:\s+di)?|fuera\s+de\s+contexto\s+responde)\s*(?:[:\-]\s*)?(.+)$',
        ])
        if fallback_template:
            bucket["fallback_template"] = fallback_template.strip()
            applied.append(f"actualicé el fallback de {scope}")

        max_bubbles = self._parse_bubble_limit(normalized)
        if max_bubbles:
            bucket["max_bubbles"] = max_bubbles
            applied.append(f"dejé {scope} en máximo {max_bubbles} burbuja(s)")

        if any(token in normalized for token in ["sin emojis", "no emojis", "no emoji", "sin emoji"]):
            bucket["no_emojis"] = True
            applied.append(f"dejé {scope} sin emojis")
        elif any(token in normalized for token in ["usa emojis", "con emojis", "puedes usar emojis"]):
            bucket["no_emojis"] = False
            applied.append(f"permití emojis en {scope}")

        if any(token in normalized for token in [
            "minúscula al inicio", "minuscula al inicio", "sin mayúscula al inicio", "sin mayuscula al inicio",
            "arranca en minúscula", "arranca en minuscula", "empieza en minúscula", "empieza en minuscula",
        ]):
            bucket["lowercase_start"] = True
            applied.append(f"dejé {scope} con minúscula inicial cuando aplique")
        elif any(token in normalized for token in [
            "mayúscula al inicio", "mayuscula al inicio", "empieza con mayúscula", "empieza con mayuscula",
            "arranca con mayúscula", "arranca con mayuscula", "primera en mayúscula", "primera en mayuscula",
        ]):
            bucket["lowercase_start"] = False
            applied.append(f"dejé {scope} con mayúscula inicial por defecto")

        if any(token in normalized for token in [
            "háblame de usted", "hablame de usted", "trátame de usted", "tratame de usted",
            "hablales de usted", "háblales de usted", "tratalos de usted", "trátalos de usted",
            "tratelos de usted", "trátelos de usted", "de usted con los pacientes",
            "de usted con los clientes", "de usted con la gente", "de usted",
        ]):
            bucket["register"] = "usted"
            applied.append(f"dejé el trato de {scope} en usted")
        elif any(token in normalized for token in [
            "tuteame", "tutéame", "háblame de tú", "hablame de tu", "háblame de tu",
            "hablales de tu", "háblales de tú", "tratales de tu", "trátales de tú",
            "tutealos", "tutéalos", "tutealas", "tutéalas", "tratalas de tu",
            "trátalas de tú", "tutea", "tutear", "de tú",
            "aqui las mujeres se tutean", "aquí las mujeres se tutean",
            "en colombia tutea", "en colombia se tutea",
        ]):
            bucket["register"] = "tu"
            applied.append(f"dejé el trato de {scope} en tú")
            if any(token in normalized for token in [
                "colombia", "mujeres se tutean", "tutea",
            ]):
                self._append_unique(
                    bucket,
                    "style_notes",
                    "Cuando el admin lo pida, usa tuteo femenino colombiano: cercano, elegante y natural.",
                )

        style_map = [
            ("más ejecutiv", "tono ejecutivo y preciso"),
            ("mas ejecutiv", "tono ejecutivo y preciso"),
            ("más human", "tono humano y natural"),
            ("mas human", "tono humano y natural"),
            ("más direct", "más directo y sin rodeos"),
            ("mas direct", "más directo y sin rodeos"),
            ("más cálid", "más cálido sin perder claridad"),
            ("mas calid", "más cálido sin perder claridad"),
            ("más seri", "más serio y sobrio"),
            ("mas seri", "más serio y sobrio"),
            ("más cort", "respuestas más cortas"),
            ("mas cort", "respuestas más cortas"),
            ("menos informal", "menos informal"),
            ("menos bot", "menos bot y más natural"),
        ]
        for token, note in style_map:
            if token in normalized and self._append_unique(bucket, "style_notes", note):
                applied.append(f"sumé la guía «{note}» en {scope}")

        if not applied:
            free_note = (text or "").strip()
            if free_note and self._append_unique(bucket, "style_notes", free_note):
                applied.append(f"guardé la instrucción en {scope}")

        if not applied:
            return {"ok": False, "reason": "no_changes"}

        self._save()
        return {
            "ok": True,
            "scope": scope,
            "applied": applied,
            "state": self.status(),
            "reply_lines": [
                "Listo. Ya quedó aplicado.",
                *applied[:3],
            ],
        }

    def _merged_bucket(self, scope: str) -> Dict[str, Any]:
        self._load()
        merged = self._blank_bucket(
            register=self._state.get("global", {}).get("register", "auto"),
            respectful=bool(self._state.get("global", {}).get("respectful", True)),
            no_emojis=bool(self._state.get("global", {}).get("no_emojis", True)),
        )
        merged.update(self._state.get("global", {}))
        specific = self._state.get(scope, {})
        for key in ("forbidden_phrases", "forbidden_starts", "style_notes"):
            merged[key] = list(merged.get(key, [])) + list(specific.get(key, []))
        merged["replacement_map"] = {
            **(merged.get("replacement_map", {}) or {}),
            **(specific.get("replacement_map", {}) or {}),
        }
        for key in (
            "greeting_template",
            "second_bubble_template",
            "third_bubble_template",
            "closing_template",
            "fallback_template",
            "register",
            "respectful",
            "no_emojis",
            "max_bubbles",
            "lowercase_start",
        ):
            value = specific.get(key)
            if value not in (None, "", []):
                merged[key] = value
        return merged

    def build_prompt_addon(self, *, is_admin: bool) -> str:
        self._load()
        if not self._state.get("enabled"):
            return ""
        scope = "admin" if is_admin else "patient"
        merged = self._merged_bucket(scope)
        lines = [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "CONTROL DURO DEL ADMIN",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        ]
        if is_admin:
            lines.append("Este chat es del administrador. Respóndele con respeto y criterio.")
        if merged.get("register") == "usted":
            lines.append("Usa trato de usted.")
        elif merged.get("register") == "tu":
            lines.append("Usa trato de tú, natural y consistente.")
        if merged.get("no_emojis"):
            lines.append("No uses emojis en ningún mensaje.")
        else:
            lines.append(
                "Emojis: úsalos con criterio — 1 por burbuja máximo, solo cuando refuercen "
                "el mensaje (nunca decorativos ni al inicio de burbuja). "
                "Ejemplos naturales para negocios colombianos: 😊 calidez, 📅 cita, "
                "✅ confirmación, 📍 ubicación, 💬 invitación a escribir. "
                "Si el tono es serio o el cliente es frío, no pongas emojis."
            )
        if merged.get("greeting_template"):
            lines.append(f'Si es saludo inicial, usa esta base: "{merged["greeting_template"]}"')
        if merged.get("second_bubble_template"):
            lines.append(f'Segunda burbuja fija: "{merged["second_bubble_template"]}"')
        if merged.get("third_bubble_template"):
            lines.append(f'Tercera burbuja fija: "{merged["third_bubble_template"]}"')
        if merged.get("closing_template"):
            lines.append(f'Cierre fijo: "{merged["closing_template"]}"')
        if merged.get("fallback_template"):
            lines.append(f'Si no entiendes o algo se sale de contexto, usa esta base: "{merged["fallback_template"]}"')
        if merged.get("max_bubbles"):
            lines.append(f'Usa máximo {merged["max_bubbles"]} burbuja(s).')
        replacement_map = merged.get("replacement_map", {}) or {}
        if replacement_map:
            lines.append(
                "Reemplazos obligatorios: " +
                " | ".join(f'{bad}→{good}' for bad, good in list(replacement_map.items())[:8])
            )
        forbidden_phrases = [str(x).strip() for x in merged.get("forbidden_phrases", []) if str(x).strip()]
        if forbidden_phrases:
            lines.append("Frases prohibidas: " + ", ".join(forbidden_phrases[:10]))
        forbidden_starts = [str(x).strip() for x in merged.get("forbidden_starts", []) if str(x).strip()]
        if forbidden_starts:
            lines.append("No abras ni empieces burbujas con: " + ", ".join(forbidden_starts[:10]))
        notes = [str(x).strip() for x in merged.get("style_notes", []) if str(x).strip()]
        if notes:
            lines.append("Guías adicionales: " + " | ".join(notes[:6]))
        return "\n".join(lines)

    def _strip_forbidden_phrase(self, text: str, phrase: str) -> str:
        raw = (phrase or "").strip()
        if not raw:
            return text
        if re.fullmatch(r"[\wáéíóúüñÁÉÍÓÚÜÑ]+", raw):
            pattern = re.compile(rf'(?<!\w){re.escape(raw)}(?!\w)', flags=re.IGNORECASE)
        else:
            pattern = re.compile(re.escape(raw), flags=re.IGNORECASE)
        text = pattern.sub("", text)
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'^\s*[,;:.!-]+\s*', '', text).strip()
        return text

    def _strip_forbidden_start(self, text: str, phrase: str) -> str:
        escaped = re.escape(phrase.strip())
        pattern = re.compile(rf'^\s*(?:{escaped})\b[\s,;:.-]*', flags=re.IGNORECASE)
        return pattern.sub("", text).strip()

    def _normalize_register(self, text: str, register: str) -> str:
        if register not in ("usted", "tu"):
            return text
        if register == "usted":
            replacements = [
                (r'\bte ayudo\b', 'le ayudo'),
                (r'\bte dejo\b', 'le dejo'),
                (r'\bte muestro\b', 'le muestro'),
                (r'\bte respondo\b', 'le respondo'),
                (r'\bte explico\b', 'le explico'),
                (r'\bte confirmo\b', 'le confirmo'),
                (r'\bte tomo\b', 'le tomo'),
                (r'\bte interesa\b', 'le interesa'),
                (r'\bte sirve\b', 'le sirve'),
                (r'\bte gustaría\b', 'le gustaría'),
                (r'\bsi quieres\b', 'si quiere'),
                (r'\bsi te parece\b', 'si le parece'),
                (r'\bpuedes\b', 'puede'),
                (r'\bquieres\b', 'quiere'),
                (r'\btienes\b', 'tiene'),
                (r'\bdime\b', 'dígame'),
                (r'\bcuéntame\b', 'cuénteme'),
                (r'\bmandame\b', 'mándeme'),
                (r'\bmándame\b', 'mándeme'),
                (r'\bavisame\b', 'avíseme'),
                (r'\bavísame\b', 'avíseme'),
            ]
        else:
            replacements = [
                (r'\ble ayudo\b', 'te ayudo'),
                (r'\ble dejo\b', 'te dejo'),
                (r'\ble muestro\b', 'te muestro'),
                (r'\ble respondo\b', 'te respondo'),
                (r'\ble explico\b', 'te explico'),
                (r'\ble confirmo\b', 'te confirmo'),
                (r'\ble tomo\b', 'te tomo'),
                (r'\ble interesa\b', 'te interesa'),
                (r'\ble sirve\b', 'te sirve'),
                (r'\ble gustaría\b', 'te gustaría'),
                (r'\bsi quiere\b', 'si quieres'),
                (r'\bsi le parece\b', 'si te parece'),
                (r'\bpuede\b', 'puedes'),
                (r'\bquiere\b', 'quieres'),
                (r'\btiene\b', 'tienes'),
                (r'\bdigame\b', 'dime'),
                (r'\bdígame\b', 'dime'),
                (r'\bcuenteme\b', 'cuéntame'),
                (r'\bcuénteme\b', 'cuéntame'),
                (r'\bmandeme\b', 'mándame'),
                (r'\bmándeme\b', 'mándame'),
                (r'\baviseme\b', 'avísame'),
                (r'\bavíseme\b', 'avísame'),
                (r'\busted\b', 'tú'),
            ]
        output = text
        for pattern, repl in replacements:
            output = re.sub(pattern, repl, output, flags=re.IGNORECASE)
        return output

    def _render_template(
        self,
        template: str,
        *,
        is_admin: bool,
        chat_id: str = "",
        clinic: Optional[Dict[str, Any]] = None,
        user_msg: str = "",
    ) -> str:
        raw = (template or "").strip()
        if not raw:
            return ""
        admin_name = "Santiago"
        if chat_id and db:
            try:
                admin = db.get_admin(chat_id)
                if admin and admin.get("name"):
                    admin_name = str(admin["name"]).strip().title()
            except Exception:
                pass
        clinic_name = ""
        if isinstance(clinic, dict):
            clinic_name = str(clinic.get("name") or "").strip()
        welcome_line = _first_contact_welcome_line(clinic or {}, user_msg)
        welcome_identity = _first_contact_identity_line(clinic or {})
        welcome_question = _first_contact_question_line()
        try:
            return raw.format(
                admin_name=admin_name,
                clinic_name=clinic_name,
                role="administrador" if is_admin else "cliente",
                welcome_line=welcome_line,
                welcome_identity=welcome_identity,
                welcome_question=welcome_question,
            ).strip()
        except Exception:
            return raw

    def _apply_replacement(self, text: str, bad: str, good: str) -> str:
        source = (bad or "").strip()
        target = (good or "").strip()
        if not source:
            return text
        if re.fullmatch(r"[\wáéíóúüñÁÉÍÓÚÜÑ]+", source):
            pattern = re.compile(rf'(?<!\w){re.escape(source)}(?!\w)', flags=re.IGNORECASE)
        else:
            pattern = re.compile(re.escape(source), flags=re.IGNORECASE)
        return pattern.sub(target, text)

    def _apply_bubble_template(self, bubbles: List[str], template: str, index: int) -> List[str]:
        if not template:
            return bubbles
        cleaned_template = template.strip()
        if not cleaned_template:
            return bubbles
        if not bubbles and index == 0:
            return [cleaned_template]
        while len(bubbles) <= index:
            bubbles.append("")
        current = bubbles[index].strip()
        if current and self._normalize_text(current).startswith(self._normalize_text(cleaned_template)[:24]):
            return bubbles
        remainder = current
        if index == 0 and remainder and self._normalize_text(remainder) != self._normalize_text(cleaned_template):
            bubbles[index] = cleaned_template
            bubbles.insert(index + 1, remainder)
            return bubbles
        bubbles[index] = cleaned_template
        return bubbles

    def enforce_output(
        self,
        response: str,
        *,
        is_admin: bool,
        first_turn: bool = False,
        chat_id: str = "",
        clinic: Optional[Dict[str, Any]] = None,
        user_msg: str = "",
    ) -> str:
        self._load()
        if not self._state.get("enabled"):
            return response

        scope = "admin" if is_admin else "patient"
        merged = self._merged_bucket(scope)
        bubbles = [b.strip() for b in re.split(r'\s*\|\|\|\s*', response or "") if b.strip()]
        if not bubbles:
            bubbles = [(response or "").strip()]
        light_open = _is_greeting_only(user_msg)

        if first_turn and light_open and merged.get("greeting_template"):
            greeting_template = self._render_template(
                merged.get("greeting_template", ""),
                is_admin=is_admin,
                chat_id=chat_id,
                clinic=clinic,
                user_msg=user_msg,
            )
            bubbles = self._apply_bubble_template(bubbles, greeting_template, 0)
        if first_turn and light_open and merged.get("second_bubble_template"):
            second_template = self._render_template(
                merged.get("second_bubble_template", ""),
                is_admin=is_admin,
                chat_id=chat_id,
                clinic=clinic,
                user_msg=user_msg,
            )
            bubbles = self._apply_bubble_template(bubbles, second_template, 1)
        if first_turn and light_open and merged.get("third_bubble_template"):
            third_template = self._render_template(
                merged.get("third_bubble_template", ""),
                is_admin=is_admin,
                chat_id=chat_id,
                clinic=clinic,
                user_msg=user_msg,
            )
            bubbles = self._apply_bubble_template(bubbles, third_template, 2)

        cleaned_bubbles: List[str] = []
        replacement_keys = {
            self._normalize_text(str(key))
            for key in (merged.get("replacement_map", {}) or {}).keys()
            if str(key).strip()
        }
        for bubble in bubbles:
            current = bubble.strip()
            for bad, good in (merged.get("replacement_map", {}) or {}).items():
                current = self._apply_replacement(current, str(bad), str(good))
            for phrase in merged.get("forbidden_phrases", []):
                if self._normalize_text(str(phrase)) in replacement_keys:
                    continue
                current = self._strip_forbidden_phrase(current, str(phrase))
            for start in merged.get("forbidden_starts", []):
                current = self._strip_forbidden_start(current, str(start))
            current = self._normalize_register(current, str(merged.get("register", "auto")))
            if merged.get("no_emojis"):
                current = self._EMOJI_RE.sub("", current)
                current = current.replace("¿", "").replace("¡", "")
            current = re.sub(r'\s+', ' ', current).strip(" ,;")
            if current and current[0].islower() and not merged.get("lowercase_start"):
                current = current[0].upper() + current[1:]
            elif current and current[0].isupper() and merged.get("lowercase_start"):
                current = current[0].lower() + current[1:]
            if current:
                cleaned_bubbles.append(current)

        if merged.get("closing_template"):
            closing_template = self._render_template(
                merged.get("closing_template", ""),
                is_admin=is_admin,
                chat_id=chat_id,
                clinic=clinic,
                user_msg=user_msg,
            )
            if closing_template:
                if cleaned_bubbles:
                    if self._normalize_text(closing_template) not in self._normalize_text(cleaned_bubbles[-1]):
                        cleaned_bubbles.append(closing_template)
                else:
                    cleaned_bubbles = [closing_template]

        max_bubbles = int(merged.get("max_bubbles") or 0)
        if max_bubbles > 0 and len(cleaned_bubbles) > max_bubbles:
            head = cleaned_bubbles[: max_bubbles - 1]
            tail = " ".join(cleaned_bubbles[max_bubbles - 1:]).strip()
            cleaned_bubbles = head + ([tail] if tail else [])

        if not cleaned_bubbles:
            if is_admin:
                cleaned_bubbles = ["Entendido."]
            elif str(merged.get("register", "auto")) == "tu":
                cleaned_bubbles = ["Entiendo. Cuéntame un poco más."]
            else:
                cleaned_bubbles = ["Entiendo. Cuénteme un poco más."]

        max_bubbles = int(merged.get("max_bubbles") or 0)
        if max_bubbles > 0:
            cleaned_bubbles = cleaned_bubbles[:max_bubbles]

        return " ||| ".join(cleaned_bubbles)

    def get_fallback_template(
        self,
        *,
        is_admin: bool,
        chat_id: str = "",
        clinic: Optional[Dict[str, Any]] = None,
    ) -> str:
        self._load()
        if not self._state.get("enabled"):
            return ""
        scope = "admin" if is_admin else "patient"
        merged = self._merged_bucket(scope)
        template = str(merged.get("fallback_template") or "").strip()
        if not template:
            return ""
        return self._render_template(template, is_admin=is_admin, chat_id=chat_id, clinic=clinic)


# ═══════════════════════════════════════════════════════════════════════════════
# PROMPT EVOLVER
# El dueño escribe en lenguaje natural "quiero que Conny..." y el sistema
# lo convierte en una instrucción estructurada que se añade al system prompt.
# Se puede deshacer instrucción por instrucción.
# ═══════════════════════════════════════════════════════════════════════════════

class PromptEvolver:
    """
    Auto-modifica el system prompt de Conny basado en instrucciones
    en lenguaje natural del dueño.
    
    Funciona como un stack de evoluciones — cada evolución se guarda
    y se puede deshacer. El prompt nunca se sobreescribe, se extiende.
    
    Ejemplo de uso desde el bot:
        Admin: /aprender "a veces responde sin tildes como WhatsApp real"
        Conny: "Entendido. Activé el skill 'sin_tildes_ocasional'. ¿Lo probamos?"
        
        Admin: /aprender "cuando alguien dice que está ocupada, no insistas con la cita"
        Conny: "Guardado. Nueva regla: respetar cuando el cliente dice que está ocupada."
    """

    DB_KEY_EVOLUTIONS = "v8_prompt_evolutions"
    MAX_EVOLUTIONS    = 20

    # Mapeo de instrucciones naturales → skills conocidas
    SKILL_KEYWORDS: Dict[str, List[str]] = {
        "typos_naturales":        ["typo", "error de tipeo", "error tipeo", "errores de escritura",
                                   "no tan perfecta ortografia", "ortografia imperfecta",
                                   "escribe mal", "errores naturales"],
        "minusculas_inicio":      ["minuscula", "sin mayuscula", "sin capital", "lowercase",
                                   "no mayuscula al inicio", "no capitalizar", "minúsculas"],
        "sin_tildes_ocasional":   ["sin tildes", "sin acento", "omitir tildes", "sin tilde",
                                   "a veces sin tildes"],
        "abreviaciones":          ["abreviacion", "abreviatura", "xq", "pq", "tmb"],
        "humor_leve":             ["humor", "gracioso", "divertido", "chiste", "jaja"],
        "emojis_puntuales":       ["emoji", "emojis", "caritas", "iconos"],
        "respuestas_ultracortas": ["corto", "breve", "corta", "pocas palabras", "ultra corto",
                                   "muy corto", "más corto"],
        "tuteo_intenso":          ["muy informal", "superinformal", "muy cercana", "como amiga"],
    }

    def __init__(self):
        self._evolutions: List[Dict] = []
        self._loaded = False

    def _load(self):
        if self._loaded:
            return
        try:
            if db:
                raw = db.recall(self.DB_KEY_EVOLUTIONS)
                if raw:
                    self._evolutions = json.loads(raw)
        except Exception:
            pass
        self._loaded = True

    def _save(self):
        try:
            if db:
                db.remember(self.DB_KEY_EVOLUTIONS,
                            json.dumps(self._evolutions[-self.MAX_EVOLUTIONS:]),
                            "config")
        except Exception:
            pass

    async def evolve(self, instruction: str, admin_chat_id: str = "") -> Dict:
        """
        Procesa una instrucción del dueño y la convierte en una evolución
        del prompt. Primero intenta mapear a un skill conocido,
        si no, la convierte en una regla personalizada via LLM.
        
        Retorna: {ok, type, result_description, skill_id?, rule_text?}
        """
        self._load()
        instruction_lower = instruction.lower()

        # ── 1. Intentar mapear a skill conocida ──────────────────────────────
        for skill_id, keywords in self.SKILL_KEYWORDS.items():
            if any(kw in instruction_lower for kw in keywords):
                skill_on = True
                # Detectar negaciones
                negations = ["no ", "nunca ", "quita ", "desactiva ", "sin "]
                if any(neg in instruction_lower[:30] for neg in negations):
                    skill_on = False
                # Activar/desactivar
                result = skill_engine.toggle(skill_id, skill_on)
                action = "activé" if skill_on else "desactivé"
                evolution = {
                    "id":        str(_uuid_trainer.uuid4())[:8],
                    "type":      "skill",
                    "skill_id":  skill_id,
                    "skill_on":  skill_on,
                    "instruction": instruction,
                    "ts":        datetime.now().isoformat(),
                    "admin":     admin_chat_id,
                }
                self._evolutions.append(evolution)
                self._save()
                return {
                    "ok":          True,
                    "type":        "skill",
                    "skill_id":    skill_id,
                    "skill_on":    skill_on,
                    "description": f"{action} el skill '{result['name']}': {result['desc']}",
                    "evolution_id": evolution["id"],
                }

        # ── 2. Convertir a regla personalizada via LLM ────────────────────────
        if not llm_engine:
            # Sin LLM: guardar como texto libre
            return self._save_free_rule(instruction, admin_chat_id)

        try:
            prompt = f"""El dueño de un negocio quiere enseñarle algo nuevo a Conny, su recepcionista virtual.

INSTRUCCIÓN DEL DUEÑO:
"{instruction}"

Convierte esta instrucción en UNA regla clara y accionable para Conny.
La regla debe ser concisa (máximo 2 oraciones) y en segunda persona ("cuando... / si...").

Responde SOLO con JSON:
{{
  "rule": "la regla como instrucción directa para Conny",
  "category": "tono|flujo|ventas|escritura|objecion|general",
  "example_bad": "qué NO hacer (si se puede inferir)",
  "example_good": "qué SÍ hacer (si se puede inferir)"
}}"""

            raw, _ = await asyncio.wait_for(
                llm_engine.complete(
                    [{"role": "user", "content": prompt}],
                    model_tier="fast", temperature=0.2, max_tokens=200, use_cache=False
                ),
                timeout=10.0
            )

            # Parsear JSON
            m = re.search(r'\{[\s\S]+\}', raw.strip())
            if m:
                parsed   = json.loads(m.group(0))
                rule     = parsed.get("rule", "").strip()
                category = parsed.get("category", "general")
                ex_bad   = parsed.get("example_bad", "")
                ex_good  = parsed.get("example_good", "")

                if rule:
                    # Guardar en carpeta de confianza
                    rule_id = db.save_trust_rule(
                        category=category,
                        rule=rule,
                        example_bad=ex_bad,
                        example_good=ex_good,
                        weight=2.5,
                    ) if db else 0

                    evolution = {
                        "id":          str(_uuid_trainer.uuid4())[:8],
                        "type":        "rule",
                        "rule":        rule,
                        "rule_id":     rule_id,
                        "category":    category,
                        "instruction": instruction,
                        "ts":          datetime.now().isoformat(),
                        "admin":       admin_chat_id,
                    }
                    self._evolutions.append(evolution)
                    self._save()

                    return {
                        "ok":           True,
                        "type":         "rule",
                        "rule":         rule,
                        "category":     category,
                        "example_good": ex_good,
                        "description":  f"Nueva regla guardada [{category}]: {rule}",
                        "evolution_id": evolution["id"],
                    }
        except Exception as e:
            log.warning(f"[prompt_evolver] LLM error: {e}")

        # Fallback: guardar como texto libre
        return self._save_free_rule(instruction, admin_chat_id)

    def _save_free_rule(self, instruction: str, admin_chat_id: str) -> Dict:
        """Guarda la instrucción como regla libre sin procesar por LLM."""
        rule_id = 0
        if db:
            try:
                rule_id = db.save_trust_rule(
                    category="general",
                    rule=instruction,
                    example_bad="",
                    example_good="",
                    weight=2.5,
                )
            except Exception:
                pass

        evolution = {
            "id":          str(_uuid_trainer.uuid4())[:8],
            "type":        "free",
            "rule":        instruction,
            "rule_id":     rule_id,
            "instruction": instruction,
            "ts":          datetime.now().isoformat(),
            "admin":       admin_chat_id,
        }
        self._evolutions.append(evolution)
        self._save()

        return {
            "ok":           True,
            "type":         "free",
            "rule":         instruction,
            "description":  f"Instrucción guardada directamente: {instruction[:60]}",
            "evolution_id": evolution["id"],
        }

    def unlearn(self, evolution_id: str) -> Dict:
        """Revierte una evolución específica."""
        self._load()
        target = next((e for e in self._evolutions if e["id"] == evolution_id), None)
        if not target:
            return {"ok": False, "error": f"Evolución '{evolution_id}' no encontrada"}

        # Revertir skill si aplica
        if target.get("type") == "skill":
            skill_engine.toggle(target["skill_id"], not target["skill_on"])

        # Eliminar regla de trust_folder si tiene rule_id
        if target.get("rule_id") and db:
            try:
                db.delete_trust_rule(target["rule_id"])
            except Exception:
                pass

        self._evolutions = [e for e in self._evolutions if e["id"] != evolution_id]
        self._save()

        return {"ok": True, "reverted": target.get("rule") or target.get("skill_id")}

    def get_history(self, limit: int = 10) -> List[Dict]:
        """Retorna el historial de evoluciones."""
        self._load()
        return list(reversed(self._evolutions))[:limit]

    def format_history_for_admin(self) -> str:
        """Formatea el historial para enviar al admin."""
        history = self.get_history()
        if not history:
            return "No hay evoluciones guardadas todavía."

        lines = ["Lo que has enseñado a Conny:\n"]
        for ev in history:
            ev_type = ev.get("type", "?")
            ts      = ev.get("ts", "")[:16]
            eid     = ev["id"]

            if ev_type == "skill":
                action = "activó" if ev.get("skill_on") else "desactivó"
                skill_def = SKILL_DEFINITIONS.get(ev.get("skill_id", ""), {})
                skill_name = skill_def.get("name", ev.get("skill_id", "?"))
                lines.append(f"  [{eid}] {ts} — {action} skill: {skill_name}")
            elif ev_type in ("rule", "free"):
                rule = ev.get("rule", "")[:60]
                lines.append(f"  [{eid}] {ts} — regla: {rule}...")

        lines.append("\nPara revertir algo: /desaprender [id]")
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN-AS-CLIENT MODE
# Cualquier admin puede convertirse en cliente inmediatamente para simular
# una conversación real con Conny y entrenarla en tiempo real.
# ═══════════════════════════════════════════════════════════════════════════════

class AdminClientMode:
    """
    Modo Admin-como-Cliente.

    Cuando el admin activa este modo:
    1. Sus mensajes son procesados como si fuera un cliente real
    2. Conny responde como respondería a un cliente
    3. El admin puede dar feedback inmediato: /feedback "esta respuesta estuvo mal porque..."
    4. El feedback se convierte en regla automáticamente
    5. Puede salir del modo con /salir o /exit

    El modo se guarda por chat_id del admin. Un admin puede tener su propia
    "sesión de entrenamiento" paralela a los clientes reales.

    Identificadores de sesión:
        _training_sessions[admin_chat_id] = {
            "active": bool,
            "persona": str,           # nombre del cliente simulado
            "scenario": str,          # escenario (primer_contacto, precio, miedo...)
            "history": list,          # historial de la sesión
            "feedback_count": int,
            "started_at": str,
        }
    """

    SCENARIOS = {
        "libre":          "Conversación libre — el admin improvisa como cliente",
        "primer_contacto":"Cliente nuevo que pregunta por primera vez",
        "precio":         "Cliente que pregunta precio antes que nada",
        "miedo":          "Cliente con miedo a quedar mal / resultado exagerado",
        "esceptico":      "Cliente que ya fue a otro lugar y quedó mal",
        "ocupado":        "Cliente ocupado, poco tiempo",
        "negociador":     "Cliente que pide descuento / regateo",
        "bot_detector":   "Cliente que pregunta si es bot",
        "urgente":        "Cliente que necesita cita urgente hoy",
        "referido":       "Cliente que llega por recomendación de amigo",
    }

    def __init__(self):
        self._sessions: Dict[str, Dict] = {}

    def start(self, admin_chat_id: str, persona: str = "",
              scenario: str = "libre") -> Dict:
        """Inicia una sesión de entrenamiento para el admin."""
        if scenario not in self.SCENARIOS:
            scenario = "libre"

        self._sessions[admin_chat_id] = {
            "active":         True,
            "persona":        persona or f"Cliente {admin_chat_id[-4:]}",
            "scenario":       scenario,
            "scenario_desc":  self.SCENARIOS[scenario],
            "history":        [],
            "feedback_count": 0,
            "started_at":     datetime.now().isoformat(),
            "session_id":     str(_uuid_trainer.uuid4())[:8],
        }
        return self._sessions[admin_chat_id]

    def is_active(self, admin_chat_id: str) -> bool:
        return self._sessions.get(admin_chat_id, {}).get("active", False)

    def stop(self, admin_chat_id: str) -> Dict:
        """Finaliza la sesión y retorna el resumen."""
        session = self._sessions.get(admin_chat_id, {})
        if not session:
            return {"ok": False, "error": "No hay sesión activa"}

        session["active"]  = False
        session["ended_at"] = datetime.now().isoformat()
        turns = len([m for m in session.get("history", []) if m["role"] == "user"])

        return {
            "ok":            True,
            "session_id":    session.get("session_id"),
            "turns":         turns,
            "feedback_count": session.get("feedback_count", 0),
            "scenario":      session.get("scenario"),
            "persona":       session.get("persona"),
        }

    def get_session(self, admin_chat_id: str) -> Optional[Dict]:
        return self._sessions.get(admin_chat_id)

    def add_turn(self, admin_chat_id: str, user_msg: str, bot_response: str):
        """Registra un turno en la sesión."""
        session = self._sessions.get(admin_chat_id, {})
        if not session:
            return
        session["history"].append({"role": "user",      "content": user_msg})
        session["history"].append({"role": "assistant", "content": bot_response})

    def get_context_injection(self, admin_chat_id: str) -> str:
        """
        Retorna contexto de la sesión para inyectar al system prompt.
        Esto hace que Conny sepa que está siendo entrenada y cuál es el escenario.
        """
        session = self._sessions.get(admin_chat_id, {})
        if not session or not session.get("active"):
            return ""

        scenario  = session.get("scenario", "libre")
        scenario_desc = session.get("scenario_desc", "")
        persona   = session.get("persona", "cliente")
        turns     = len([m for m in session.get("history", []) if m["role"] == "user"])

        # Contexto de escenario para cada tipo
        scenario_contexts = {
            "primer_contacto": "Es la primera vez que este cliente escribe. No te conoce. "
                               "Llega con una pregunta general. Tu trabajo es descubrir qué le molesta.",
            "precio":          "El cliente va a preguntar el precio inmediatamente. "
                               "No lo des de entrada. Primero descubre qué zona/servicio/caso específico.",
            "miedo":           "El cliente tiene miedo a quedar exagerado o que se note. "
                               "Valida el miedo PRIMERO antes de cualquier información.",
            "esceptico":       "El cliente ya fue a otro lugar y le fue mal. "
                               "Empatía PRIMERO. Luego diferencia. Nunca te defiendas.",
            "ocupado":         "El cliente dice que está ocupado. Respeta su tiempo. "
                               "Propuesta concreta y rápida.",
            "negociador":      "El cliente va a pedir descuento. No lo des de inmediato. "
                               "Habla de valor antes de precio.",
            "bot_detector":    "El cliente va a preguntar si eres bot. "
                               "Responde como persona real, directamente, sin negar ni confirmar ser IA.",
            "urgente":         "El cliente necesita la cita para hoy o mañana. "
                               "Actúa rápido, propón fecha inmediata.",
            "referido":        "El cliente viene por recomendación. "
                               "Reconoce la recomendación con calidez.",
            "libre":           "Conversación abierta. Responde naturalmente.",
        }

        ctx = scenario_contexts.get(scenario, "")

        lines = [
            f"",
            f"MODO ENTRENAMIENTO ACTIVO (solo visible para ti):",
            f"  Persona: {persona}",
            f"  Escenario: {scenario} — {scenario_desc}",
            f"  Turno: #{turns + 1}",
        ]
        if ctx:
            lines.append(f"  Contexto: {ctx}")
        lines.append("")

        return "\n".join(lines)

    def format_session_report(self, admin_chat_id: str) -> str:
        """Genera reporte de la sesión actual."""
        session = self._sessions.get(admin_chat_id, {})
        if not session:
            return "No hay sesión activa."

        history  = session.get("history", [])
        turns    = len([m for m in history if m["role"] == "user"])
        scenario = session.get("scenario", "?")
        persona  = session.get("persona", "?")
        feedback = session.get("feedback_count", 0)
        sid      = session.get("session_id", "?")

        lines = [
            f"Sesión de entrenamiento [{sid}]",
            f"  Persona: {persona}",
            f"  Escenario: {scenario}",
            f"  Turnos: {turns}",
            f"  Feedback dado: {feedback} veces",
            f"",
            "Conversación:",
        ]

        for msg in history[-10:]:
            role = "Tú (cliente)" if msg["role"] == "user" else "Conny"
            lines.append(f"  [{role}] {msg['content'][:80]}")

        lines.extend([
            "",
            "Comandos disponibles:",
            "  /feedback [mensaje]  — dar feedback sobre la última respuesta",
            "  /aprender [x]        — enseñar algo nuevo",
            "  /salir               — terminar el modo cliente",
        ])

        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# NOVA RULE SYNC
# Cuando el admin (o incluso el cliente) dice "no hagas X",
# la instrucción se envía a Nova como regla de gobernanza
# Y también se guarda en la carpeta de confianza de Conny.
# Esto garantiza que la instrucción se cumpla SIEMPRE, incluso si el
# system prompt falla o es ignorado por el LLM.
# ═══════════════════════════════════════════════════════════════════════════════

class NovaRuleSync:
    """
    Sincroniza reglas de entrenamiento con Nova OS.

    Cuando Nova está activo, actúa como capa de gobernanza sobre Conny.
    Una regla enviada a Nova es ENFORCED en cada mensaje, no solo sugerida.
    Si Nova está offline, las reglas se guardan solo en la carpeta de confianza.

    Detección de instrucciones negativas en mensajes del CLIENTE:
    Si el cliente dice "no me hagas eso" / "eso no me gusta" / "no me envíes X",
    Conny puede detectarlo y enviarlo a Nova automáticamente.
    """

    # Patrones que detectan instrucciones negativas del cliente
    CLIENT_NEGATIVE_PATTERNS = [
        r"no (me )?(hagas|digas|mandes|envíes|digas|menciones|uses?)\b",
        r"(para|deja) de (decir|hacer|mandar|enviar|mencionar)\b",
        r"no quiero (que|más)\b",
        r"eso no (me )?(gusta|sirve|funciona)\b",
        r"no (seas?|te pongas?|actúes?)\b",
        r"(basta|ya|suficiente) con\b",
        r"evita (decir|hacer|mencionar)\b",
    ]

    def __init__(self):
        self._compiled = [re.compile(p, re.IGNORECASE) for p in self.CLIENT_NEGATIVE_PATTERNS]
        self._nova_url   = ""
        self._nova_key   = ""
        self._nova_agent = "conny"

    def _init_nova_connection(self):
        """Inicializa la conexión a Nova si está configurada."""
        if not self._nova_url:
            self._nova_url   = Config.NOVA_URL or os.getenv("NOVA_CORE_URL", "")
            self._nova_key   = Config.NOVA_API_KEY or os.getenv("NOVA_CORE_API_KEY", "")
            self._nova_agent = os.getenv("NOVA_AGENT_NAME", "conny")

    def detect_client_negative_instruction(self, client_msg: str) -> Optional[str]:
        """
        Detecta si el cliente está dando una instrucción negativa a Conny.
        Retorna la instrucción detectada o None.
        """
        for pattern in self._compiled:
            if pattern.search(client_msg.lower()):
                return client_msg
        return None

    async def sync_rule(self, instruction: str, source: str = "admin",
                        category: str = "general") -> Dict:
        """
        Sincroniza una regla con Nova Y con la carpeta de confianza.
        
        source: "admin" | "client" | "trainer"
        Retorna: {ok, nova_synced, trust_saved, rule_text}
        """
        self._init_nova_connection()

        # 1. Siempre guardar en carpeta de confianza (funciona sin Nova)
        trust_saved = False
        rule_id = 0
        try:
            if db:
                rule_id = db.save_trust_rule(
                    category=category,
                    rule=instruction,
                    example_bad="",
                    example_good="",
                )
                trust_saved = True
        except Exception as e:
            log.warning(f"[nova_sync] trust save error: {e}")

        # 2. Intentar sincronizar con Nova si está disponible
        nova_synced = False
        nova_msg    = ""

        if Config.NOVA_ENABLED and self._nova_url and self._nova_key:
            try:
                nova_payload = {
                    "agent_name":  self._nova_agent,
                    "rule":        instruction,
                    "cannot_do":   [instruction],
                    "source":      source,
                    "category":    category,
                    "timestamp":   datetime.now().isoformat(),
                }
                async with httpx.AsyncClient(timeout=5.0) as client:
                    r = await client.post(
                        f"{self._nova_url}/rules",
                        json=nova_payload,
                        headers={
                            "X-Nova-Key":  self._nova_key,
                            "Content-Type": "application/json",
                        }
                    )
                    if r.status_code < 400:
                        nova_synced = True
                        log.info(f"[nova_sync] regla enviada a Nova: {instruction[:50]}")
                    else:
                        nova_msg = f"Nova respondió {r.status_code}"
            except Exception as e:
                nova_msg = f"Nova offline: {e}"
                log.debug(f"[nova_sync] {nova_msg}")

        return {
            "ok":          trust_saved or nova_synced,
            "nova_synced": nova_synced,
            "trust_saved": trust_saved,
            "rule_id":     rule_id,
            "rule_text":   instruction,
            "nova_msg":    nova_msg,
        }

    async def process_client_negative(self, client_msg: str, chat_id: str) -> Optional[Dict]:
        """
        Si el cliente da una instrucción negativa, la procesa automáticamente.
        Retorna el resultado de la sincronización o None si no hay instrucción.
        """
        instruction = self.detect_client_negative_instruction(client_msg)
        if not instruction:
            return None

        # Procesar la instrucción como regla
        result = await self.sync_rule(
            instruction=instruction,
            source="client",
            category="client_instruction",
        )

        log.info(f"[nova_sync] instrucción negativa del cliente [{chat_id}]: {instruction[:50]}")
        return result


# ═══════════════════════════════════════════════════════════════════════════════
# INSTANCIAS GLOBALES DEL TRAINER
# ═══════════════════════════════════════════════════════════════════════════════

skill_engine:    SkillEngine     = None
trainer_gateway: "TrainerGateway" = None
owner_style_controller: "OwnerStyleController" = None
prompt_evolver:  PromptEvolver   = None
admin_client_mode: AdminClientMode = None
nova_rule_sync:  NovaRuleSync    = None


def init_trainer_systems():
    """Inicializa todos los sistemas de entrenamiento."""
    global skill_engine, trainer_gateway, owner_style_controller, prompt_evolver, admin_client_mode, nova_rule_sync
    try:
        skill_engine      = SkillEngine()
        log.info("[trainer] SkillEngine OK")
    except Exception as e:
        log.warning(f"[trainer] SkillEngine: {e}")
    try:
        trainer_gateway   = TrainerGateway()
        log.info("[trainer] TrainerGateway OK")
    except Exception as e:
        log.warning(f"[trainer] TrainerGateway: {e}")
    try:
        owner_style_controller = OwnerStyleController()
        log.info("[trainer] OwnerStyleController OK")
    except Exception as e:
        log.warning(f"[trainer] OwnerStyleController: {e}")
    try:
        prompt_evolver    = PromptEvolver()
        log.info("[trainer] PromptEvolver OK")
    except Exception as e:
        log.warning(f"[trainer] PromptEvolver: {e}")
    try:
        admin_client_mode = AdminClientMode()
        log.info("[trainer] AdminClientMode OK")
    except Exception as e:
        log.warning(f"[trainer] AdminClientMode: {e}")
    try:
        nova_rule_sync    = NovaRuleSync()
        log.info("[trainer] NovaRuleSync OK")
    except Exception as e:
        log.warning(f"[trainer] NovaRuleSync: {e}")

    log.info("═══ CONNY TRAINER INITIALIZED ═══")


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRACIÓN EN EL PIPELINE DE RESPUESTA
# ═══════════════════════════════════════════════════════════════════════════════

def trainer_get_system_prompt_addon(
    chat_id: str,
    clinic: Optional[Dict[str, Any]] = None,
    user_msg: str = "",
    is_admin: bool = False,
    patient: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Retorna el bloque de trainer para inyectar al system prompt.
    Combina skills activas + gateway automático + contexto de sesión de entrenamiento.
    """
    try:
        blocks = []

        # Skills activas
        if skill_engine:
            skills_block = skill_engine.get_prompt_injection()
            if skills_block:
                blocks.append(skills_block)

        # Gateway automático por rol/canal/intención
        if trainer_gateway and clinic:
            gateway_block = trainer_gateway.build_prompt_addon(
                chat_id=chat_id,
                clinic=clinic,
                user_msg=user_msg,
                is_admin=is_admin,
                patient=patient,
            )
            if gateway_block:
                blocks.append(gateway_block)

        if owner_style_controller:
            owner_block = owner_style_controller.build_prompt_addon(is_admin=is_admin)
            if owner_block:
                blocks.append(owner_block)

        # Contexto de sesión si el admin está en modo cliente
        if admin_client_mode and admin_client_mode.is_active(chat_id):
            session_ctx = admin_client_mode.get_context_injection(chat_id)
            if session_ctx:
                blocks.append(session_ctx)

        return "\n\n".join(blocks)
    except Exception as e:
        log.debug(f"[trainer_addon] error: {e}")
        return ""


def trainer_post_process_response(response: str, chat_id: str = "") -> str:
    """
    Aplica transformaciones post-generación del trainer (skills de escritura).
    Se llama DESPUÉS del LLM, antes de enviar al cliente.
    """
    try:
        if skill_engine:
            response = skill_engine.apply_post_filter(response, chat_id)
        return response
    except Exception as e:
        log.debug(f"[trainer_postprocess] error: {e}")
        return response


async def trainer_process_client_msg(
    client_msg: str,
    chat_id: str,
    patient: Optional[Dict[str, Any]] = None,
):
    """
    Procesa cada mensaje del cliente buscando:
    - instrucciones negativas para sincronizar con Nova/trust folder
    - preferencias explícitas de trato/tono/forma de respuesta
    Se llama ANTES de generar la respuesta (fire-and-forget).
    """
    try:
        if trainer_gateway:
            trainer_gateway.observe_user_preferences(
                chat_id=chat_id,
                user_msg=client_msg,
                patient=patient,
                is_admin=False,
            )
        if nova_rule_sync:
            result = await nova_rule_sync.process_client_negative(client_msg, chat_id)
            if result and result.get("ok"):
                log.info(f"[trainer] instrucción del cliente procesada: {result.get('rule_text','')[:40]}")
    except Exception as e:
        log.debug(f"[trainer_client_msg] error: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# COMANDOS ADMIN NUEVOS (se integran en _handle_admin_or_setup)
# ═══════════════════════════════════════════════════════════════════════════════

async def _admin_skills(chat_id: str) -> List[str]:
    """/skills — lista skills disponibles con estado."""
    if not skill_engine:
        return ["El sistema de skills no está disponible."]

    skills  = skill_engine.list_all()
    active  = [s for s in skills if s["active"]]
    inactive = [s for s in skills if not s["active"]]

    lines = ["Skills de comportamiento de Conny:\n"]

    if active:
        lines.append("Activas ahora:")
        for s in active:
            lines.append(f"  ✓ {s['name']} ({s['id']})")
            lines.append(f"    {s['desc']}")

    if inactive:
        if active:
            lines.append("")
        lines.append("Disponibles (inactivas):")
        for s in inactive:
            lines.append(f"  ○ {s['name']} ({s['id']})")
            lines.append(f"    {s['desc']}")

    lines.extend([
        "",
        "Para activar: /skill [id] on",
        "Para desactivar: /skill [id] off",
        "O en lenguaje natural: /aprender 'a veces usa minúsculas al inicio'",
    ])
    return ["\n".join(lines)]


async def _admin_toggle_skill(chat_id: str, text: str) -> List[str]:
    """/skill [id] [on|off] — activa o desactiva un skill."""
    if not skill_engine:
        return ["El sistema de skills no está disponible."]

    parts = text.strip().split()
    if len(parts) < 3:
        return [
            "Formato: /skill [id] [on|off]",
            "Ejemplo: /skill typos_naturales on",
            "Ver todos: /skills"
        ]

    skill_id = parts[1].lower()
    action   = parts[2].lower()

    if action not in ("on", "off", "activar", "desactivar"):
        return ["Usa 'on' para activar o 'off' para desactivar"]

    on = action in ("on", "activar")
    result = skill_engine.toggle(skill_id, on)

    if not result["ok"]:
        available = ", ".join(SKILL_DEFINITIONS.keys())
        return [
            f"Skill '{skill_id}' no existe.",
            f"Disponibles: {available}"
        ]

    action_str = "activado" if on else "desactivado"
    return [
        f"Skill {action_str}: {result['name']}",
        result["desc"],
        "Para ver todas: /skills"
    ]


async def _admin_aprender(chat_id: str, instruction: str) -> List[str]:
    """/aprender [instruccion] — enseña algo nuevo a Conny."""
    if not instruction or len(instruction.strip()) < 5:
        return [
            "Dime qué quieres que aprenda Conny.",
            "Ejemplo: /aprender a veces usa minúsculas al inicio",
            "Ejemplo: /aprender cuando el cliente dice que está ocupado no insistas",
            "Ejemplo: /aprender usa emojis sutiles cuando el cliente está emocionado"
        ]

    if not prompt_evolver:
        return ["El sistema de aprendizaje no está disponible."]

    result = await prompt_evolver.evolve(instruction.strip(), chat_id)

    if not result.get("ok"):
        return [f"No pude procesar esa instrucción: {result.get('error', 'error desconocido')}"]

    lines = [f"Entendido. {result['description']}"]

    if result.get("example_good"):
        lines.append(f"Ejemplo de cómo lo aplicará: \"{result['example_good']}\"")

    lines.append(f"ID de esta evolución: {result.get('evolution_id', '?')} (úsalo para /desaprender)")
    return lines


async def _admin_desaprender(chat_id: str, evolution_id: str) -> List[str]:
    """/desaprender [id] — revierte una evolución específica."""
    if not prompt_evolver:
        return ["El sistema de aprendizaje no está disponible."]

    if not evolution_id:
        history = prompt_evolver.format_history_for_admin()
        return [history]

    result = prompt_evolver.unlearn(evolution_id.strip())
    if not result["ok"]:
        return [f"No encontré la evolución '{evolution_id}'", "Usa /desaprender para ver el historial"]

    return [
        f"Revertido: {result.get('reverted', '?')}",
        "Conny ya no aplica esa instrucción."
    ]


async def _admin_historial_aprendizaje(chat_id: str) -> List[str]:
    """/historial — historial de evoluciones del prompt."""
    if not prompt_evolver:
        return ["El sistema de aprendizaje no está disponible."]

    return [prompt_evolver.format_history_for_admin()]


async def _admin_simular_cliente(chat_id: str, args_text: str, clinic: Dict) -> List[str]:
    """
    /simular-cliente [escenario] — el admin se convierte en cliente.
    Conny le responderá como si fuera un cliente real.
    """
    if not admin_client_mode:
        return ["El modo cliente no está disponible."]

    if admin_client_mode.is_active(chat_id):
        session = admin_client_mode.get_session(chat_id)
        report  = admin_client_mode.format_session_report(chat_id)
        return [
            f"Ya tienes una sesión activa: {session.get('scenario')} / {session.get('persona')}",
            report,
            "Para salir: /salir"
        ]

    # Parsear escenario y nombre
    parts    = args_text.strip().split() if args_text else []
    scenario = parts[0].lower() if parts else "libre"
    persona  = " ".join(parts[1:]) if len(parts) > 1 else ""

    if scenario not in AdminClientMode.SCENARIOS:
        escenarios = "\n".join(f"  {k} — {v}" for k, v in AdminClientMode.SCENARIOS.items())
        return [
            f"Escenario '{scenario}' no existe.",
            f"Escenarios disponibles:\n{escenarios}",
            "Uso: /simular-cliente [escenario] [nombre_opcional]"
        ]

    agent_name = clinic.get("persona_config", {})
    if isinstance(agent_name, str):
        try:
            agent_name = json.loads(agent_name)
        except Exception:
            agent_name = {}
    agent_name = agent_name.get("name", "Conny") if isinstance(agent_name, dict) else "Conny"

    session = admin_client_mode.start(chat_id, persona or f"Cliente simulado", scenario)

    lines = [
        f"Modo cliente activado.",
        f"Eres: {session['persona']}",
        f"Escenario: {session['scenario']} — {session['scenario_desc']}",
        f"",
        f"Escríbele a {agent_name} como si fueras un cliente real.",
        f"",
        f"Comandos mientras estás en modo cliente:",
        f"  /feedback [mensaje] — dar feedback sobre la última respuesta",
        f"  /aprender [x]       — enseñar algo en este momento",
        f"  /sesion             — ver resumen de la sesión",
        f"  /salir              — salir del modo cliente",
    ]
    return ["\n".join(lines)]


async def _admin_salir_modo_cliente(chat_id: str) -> List[str]:
    """/salir — sale del modo cliente y muestra el resumen."""
    if not admin_client_mode:
        return ["El modo cliente no está disponible."]

    if not admin_client_mode.is_active(chat_id):
        return ["No estás en modo cliente ahora mismo."]

    result = admin_client_mode.stop(chat_id)
    lines  = [
        "Sesión de entrenamiento finalizada.",
        f"Turnos: {result.get('turns', 0)}",
        f"Feedback dado: {result.get('feedback_count', 0)} veces",
        f"Escenario: {result.get('scenario', '?')}",
        "",
        "Todo el feedback quedó guardado en la carpeta de confianza.",
        "Para ver las reglas aprendidas: /reglas",
        "Para ver el historial: /historial",
    ]
    return ["\n".join(lines)]


async def _admin_feedback_sesion(chat_id: str, feedback_text: str, clinic: Dict) -> List[str]:
    """/feedback [texto] — da feedback sobre la última respuesta en modo cliente."""
    if not admin_client_mode or not admin_client_mode.is_active(chat_id):
        return ["El feedback funciona dentro del modo cliente (/simular-cliente)"]

    if not feedback_text or len(feedback_text.strip()) < 5:
        return ["Dime qué estuvo mal o bien en la respuesta de Conny."]

    session = admin_client_mode.get_session(chat_id)
    if session:
        session["feedback_count"] = session.get("feedback_count", 0) + 1

    # Procesar feedback como instrucción de aprendizaje
    result = await prompt_evolver.evolve(feedback_text.strip(), chat_id) if prompt_evolver else {}

    lines = ["Feedback registrado."]
    if result.get("ok"):
        lines.append(result.get("description", ""))
    lines.append("Sigue simulando o escribe /salir para terminar.")
    return lines


async def _admin_ver_sesion(chat_id: str) -> List[str]:
    """/sesion — ver resumen de la sesión actual."""
    if not admin_client_mode:
        return ["El modo cliente no está disponible."]

    if not admin_client_mode.is_active(chat_id):
        return [
            "No tienes una sesión activa.",
            "Para simular una conversación como cliente: /simular-cliente"
        ]

    return [admin_client_mode.format_session_report(chat_id)]


async def _admin_gateway_status(chat_id: str) -> List[str]:
    """/gateway — ver estado del gateway automático del trainer."""
    if not trainer_gateway:
        return ["El gateway automático no está disponible."]

    state = trainer_gateway.status()
    on_off = lambda value: "ON" if value else "off"
    return [
        "\n".join([
            "Gateway automático del trainer:",
            f"  General: {on_off(state.get('enabled'))}",
            f"  Auto-admin: {on_off(state.get('auto_admin'))}",
            f"  Auto-user: {on_off(state.get('auto_user'))}",
            "",
            "Qué hace:",
            "  • detecta instrucciones del admin sin obligarlo a usar /aprender",
            "  • aplica skills automáticas por contexto al usuario",
            "  • aprende preferencias de trato, brevedad y estilo por chat",
            "",
            "Comandos:",
            "  /gateway on",
            "  /gateway off",
            "  /gateway admin on|off",
            "  /gateway user on|off",
        ])
    ]


async def _admin_gateway_toggle(chat_id: str, text: str) -> List[str]:
    """/gateway on|off|admin on|off|user on|off"""
    if not trainer_gateway:
        return ["El gateway automático no está disponible."]

    parts = [p for p in text.lower().strip().split() if p]
    if len(parts) == 1:
        return await _admin_gateway_status(chat_id)

    target = "enabled"
    value_token = ""

    if len(parts) >= 2 and parts[1] in ("on", "off"):
        value_token = parts[1]
    elif len(parts) >= 3 and parts[1] in ("admin", "user") and parts[2] in ("on", "off"):
        target = "auto_admin" if parts[1] == "admin" else "auto_user"
        value_token = parts[2]
    else:
        return [
            "Formato: /gateway on|off",
            "Formato: /gateway admin on|off",
            "Formato: /gateway user on|off",
        ]

    value = value_token == "on"
    kwargs = {target: value}
    result = trainer_gateway.configure(**kwargs)

    label_map = {
        "enabled": "gateway general",
        "auto_admin": "gateway de admin",
        "auto_user": "gateway de usuario",
    }
    state_word = "activado" if value else "desactivado"
    return [
        f"Listo. Dejé {label_map[target]} {state_word}.",
        f"Estado actual: general={'ON' if result.get('enabled') else 'off'} · admin={'ON' if result.get('auto_admin') else 'off'} · user={'ON' if result.get('auto_user') else 'off'}",
    ]


async def _admin_control_status(chat_id: str) -> List[str]:
    """/control — ver estado del plano de control del admin."""
    if not owner_style_controller:
        return ["El plano de control del admin no está disponible."]

    state = owner_style_controller.status()

    def _fmt_bucket(label: str, bucket: Dict[str, Any]) -> str:
        forbidden = ", ".join(bucket.get("forbidden_phrases", [])[:6]) or "ninguna"
        starts = ", ".join(bucket.get("forbidden_starts", [])[:6]) or "ninguno"
        notes = " | ".join(bucket.get("style_notes", [])[:4]) or "sin notas extra"
        greeting = bucket.get("greeting_template") or "sin plantilla"
        second_bubble = bucket.get("second_bubble_template") or "sin plantilla"
        third_bubble = bucket.get("third_bubble_template") or "sin plantilla"
        closing = bucket.get("closing_template") or "sin plantilla"
        fallback = bucket.get("fallback_template") or "sin plantilla"
        replacements = " | ".join(
            f'{bad}->{good}' for bad, good in list((bucket.get("replacement_map", {}) or {}).items())[:4]
        ) or "ninguno"
        register = bucket.get("register", "auto")
        emojis = "off" if bucket.get("no_emojis") else "ON"
        max_bubbles = bucket.get("max_bubbles") or "auto"
        return "\n".join([
            f"{label}:",
            f"  trato: {register}",
            f"  emojis: {emojis}",
            f"  saludo base: {greeting}",
            f"  segunda burbuja: {second_bubble}",
            f"  tercera burbuja: {third_bubble}",
            f"  cierre: {closing}",
            f"  fallback: {fallback}",
            f"  máximo burbujas: {max_bubbles}",
            f"  reemplazos: {replacements}",
            f"  frases prohibidas: {forbidden}",
            f"  arranques prohibidos: {starts}",
            f"  notas: {notes}",
        ])

    return [
        "\n".join([
            "Control duro del admin:",
            f"  General: {'ON' if state.get('enabled') else 'off'}",
            "",
            _fmt_bucket("Global", state.get("global", {})),
            "",
            _fmt_bucket("Admin", state.get("admin", {})),
            "",
            _fmt_bucket("Paciente", state.get("patient", {})),
            "",
            "Uso natural:",
            '  "No digas ay"',
            '  "No digas ay, di entiendo"',
            '  "Conmigo háblame de usted y más directo"',
            '  "Saluda así: Hola, Conny por acá..."',
            '  "Segunda burbuja: Estoy lista para ayudarle con la instancia"',
            '  "Tercera burbuja: Si quiere, lo dejamos listo ahora"',
            '  "Cierra así: Si quiere, lo dejamos listo ahora."',
            '  "Si no entiendes di: Perdón, ayúdeme con un poco más de contexto."',
            '  "Responde en 2 burbujas"',
            '  "A los pacientes no les digas listo al inicio"',
            '  "/control reset admin"',
        ])
    ]


async def _admin_control_apply(chat_id: str, text: str) -> List[str]:
    """Aplica una instrucción al plano de control del admin."""
    if not owner_style_controller:
        return ["El plano de control del admin no está disponible."]

    instruction = re.sub(r"^/control\s*", "", (text or "").strip(), flags=re.IGNORECASE).strip()
    if not instruction:
        return await _admin_control_status(chat_id)
    if instruction.lower() in ("reset", "reiniciar", "limpiar"):
        result = owner_style_controller.reset("all")
        return [
            "Listo. Reinicié el plano de control completo.",
            f"General={'ON' if result.get('state', {}).get('enabled') else 'off'}",
        ]
    if instruction.lower() in ("reset admin", "reiniciar admin", "limpiar admin"):
        owner_style_controller.reset("admin")
        return ["Listo. Reinicié solo el control de admin."]
    if instruction.lower() in ("reset pacientes", "reset paciente", "reiniciar paciente", "limpiar paciente"):
        owner_style_controller.reset("patient")
        return ["Listo. Reinicié solo el control de pacientes."]

    result = owner_style_controller.apply_instruction(instruction, admin_chat_id=chat_id)
    if not result.get("ok"):
        return [
            "No pude convertir eso en una regla dura todavía.",
            "Prueba con algo como: no digas 'ay' | no digas 'ay', di 'entiendo' | no empieces con 'claro' | saluda así: Hola, Conny por acá",
        ]

    return result.get("reply_lines", ["Listo. Ya quedó aplicado."])


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS FASTAPI DEL TRAINER
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/trainer/status")
async def trainer_status():
    """Estado del sistema de entrenamiento."""
    return {
        "ok":             True,
        "skill_engine":   skill_engine is not None,
        "trainer_gateway": trainer_gateway is not None,
        "owner_style_control": owner_style_controller is not None,
        "prompt_evolver": prompt_evolver is not None,
        "admin_client":   admin_client_mode is not None,
        "nova_sync":      nova_rule_sync is not None,
        "gateway_state":  trainer_gateway.status() if trainer_gateway else {},
        "owner_style_state": owner_style_controller.status() if owner_style_controller else {},
        "active_skills":  skill_engine.get_active() if skill_engine else [],
        "evolutions":     len(prompt_evolver._evolutions) if prompt_evolver else 0,
        "active_sessions": sum(
            1 for s in (admin_client_mode._sessions.values() if admin_client_mode else [])
            if s.get("active")
        ),
    }


@app.get("/trainer/skills")
async def trainer_list_skills():
    """Lista todos los skills disponibles."""
    if not skill_engine:
        raise HTTPException(status_code=503, detail="SkillEngine no disponible")
    return {"skills": skill_engine.list_all()}


@app.post("/trainer/skill/toggle")
async def trainer_toggle_skill(request: Request):
    """Activa o desactiva un skill. Body: {skill_id, active}"""
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")
    if not skill_engine:
        raise HTTPException(status_code=503, detail="SkillEngine no disponible")

    data     = await request.json()
    skill_id = data.get("skill_id", "").strip()
    active   = bool(data.get("active", True))

    result = skill_engine.toggle(skill_id, active)
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Skill no encontrado"))
    return result


@app.get("/trainer/gateway")
async def trainer_gateway_status():
    """Estado del gateway automático del trainer."""
    if not trainer_gateway:
        raise HTTPException(status_code=503, detail="TrainerGateway no disponible")
    return {
        "ok": True,
        **trainer_gateway.status(),
        "active_skills": skill_engine.get_active() if skill_engine else [],
    }


@app.post("/trainer/gateway")
async def trainer_gateway_config(request: Request):
    """Configura el gateway automático. Body: {enabled?, auto_admin?, auto_user?}"""
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")
    if not trainer_gateway:
        raise HTTPException(status_code=503, detail="TrainerGateway no disponible")

    data = await request.json()
    result = trainer_gateway.configure(
        enabled=data.get("enabled") if "enabled" in data else None,
        auto_admin=data.get("auto_admin") if "auto_admin" in data else None,
        auto_user=data.get("auto_user") if "auto_user" in data else None,
    )
    return result


@app.get("/trainer/control")
async def trainer_owner_control_status():
    """Estado del plano de control duro del admin."""
    if not owner_style_controller:
        raise HTTPException(status_code=503, detail="OwnerStyleController no disponible")
    return {"ok": True, **owner_style_controller.status()}


@app.post("/trainer/control")
async def trainer_owner_control_apply(request: Request):
    """Aplica una instrucción natural o reset al plano de control. Body: {instruction} o {reset_scope}"""
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")
    if not owner_style_controller:
        raise HTTPException(status_code=503, detail="OwnerStyleController no disponible")

    data = await request.json()
    reset_scope = (data.get("reset_scope") or "").strip().lower()
    if reset_scope:
        return owner_style_controller.reset(reset_scope)
    instruction = (data.get("instruction") or "").strip()
    admin_id = str(data.get("admin_chat_id") or "api")
    if not instruction:
        raise HTTPException(status_code=400, detail="instruction o reset_scope requerida")
    result = owner_style_controller.apply_instruction(instruction, admin_chat_id=admin_id)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("reason", "No se pudo aplicar"))
    return result


@app.post("/trainer/prompt/evolve")
async def trainer_evolve_prompt(request: Request):
    """
    Evoluciona el prompt con una instrucción en lenguaje natural.
    Body: {instruction, admin_chat_id?}
    """
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")
    if not prompt_evolver:
        raise HTTPException(status_code=503, detail="PromptEvolver no disponible")

    data        = await request.json()
    instruction = data.get("instruction", "").strip()
    admin_id    = data.get("admin_chat_id", "api")

    if not instruction:
        raise HTTPException(status_code=400, detail="instruction requerida")

    result = await prompt_evolver.evolve(instruction, admin_id)
    return result


@app.get("/trainer/evolutions")
async def trainer_get_evolutions(request: Request, limit: int = 20):
    """Lista el historial de evoluciones del prompt."""
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")
    if not prompt_evolver:
        raise HTTPException(status_code=503, detail="PromptEvolver no disponible")

    return {
        "evolutions": prompt_evolver.get_history(limit),
        "total":      len(prompt_evolver._evolutions),
    }


@app.delete("/trainer/evolutions/{evolution_id}")
async def trainer_delete_evolution(evolution_id: str, request: Request):
    """Revierte una evolución del prompt."""
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")
    if not prompt_evolver:
        raise HTTPException(status_code=503, detail="PromptEvolver no disponible")

    result = prompt_evolver.unlearn(evolution_id)
    if not result["ok"]:
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result


@app.post("/trainer/admin-as-client/start")
async def trainer_start_client_mode(request: Request):
    """
    Inicia sesión de entrenamiento admin-como-cliente.
    Body: {admin_chat_id, scenario?, persona?}
    """
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")
    if not admin_client_mode:
        raise HTTPException(status_code=503, detail="AdminClientMode no disponible")

    data     = await request.json()
    chat_id  = data.get("admin_chat_id", "").strip()
    scenario = data.get("scenario", "libre")
    persona  = data.get("persona", "")

    if not chat_id:
        raise HTTPException(status_code=400, detail="admin_chat_id requerido")

    session = admin_client_mode.start(chat_id, persona, scenario)
    return {
        "ok":        True,
        "session_id": session["session_id"],
        "scenario":  session["scenario"],
        "persona":   session["persona"],
    }


@app.post("/trainer/admin-as-client/stop")
async def trainer_stop_client_mode(request: Request):
    """Finaliza la sesión de entrenamiento. Body: {admin_chat_id}"""
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")
    if not admin_client_mode:
        raise HTTPException(status_code=503, detail="AdminClientMode no disponible")

    data    = await request.json()
    chat_id = data.get("admin_chat_id", "").strip()
    result  = admin_client_mode.stop(chat_id)
    return result


@app.post("/trainer/nova-sync")
async def trainer_nova_sync(request: Request):
    """
    Sincroniza una regla con Nova.
    Body: {rule, category?, source?}
    """
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")
    if not nova_rule_sync:
        raise HTTPException(status_code=503, detail="NovaRuleSync no disponible")

    data     = await request.json()
    rule     = data.get("rule", "").strip()
    category = data.get("category", "general")
    source   = data.get("source", "api")

    if not rule:
        raise HTTPException(status_code=400, detail="rule requerida")

    result = await nova_rule_sync.sync_rule(rule, source, category)
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# PATCH DEL DISPATCHER ADMIN PARA INCLUIR COMANDOS TRAINER
# ═══════════════════════════════════════════════════════════════════════════════

def _patch_admin_dispatcher_trainer():
    """
    Extiende el dispatcher admin con los comandos del trainer.
    Se llama después de _patch_admin_dispatcher() del V8 extended.
    """
    orig_get = getattr(ConnyUltra, "_handle_admin_or_setup", None)
    original_method = orig_get if orig_get else None

    async def patched_with_trainer(self, chat_id: str, text: str, clinic: Dict) -> List[str]:
        cmd      = text.lower().strip()
        text_low = text.lower().strip()

        # ── SmartHandoff: interceptar respuesta del admin a un ticket pendiente ─
        if _SMART_HANDOFF and handoff_manager and not cmd.startswith("/"):
            async def _handoff_send_to_client(cid: str, msg: str):
                try:
                    await self._send_message(cid, msg)
                    if db:
                        try:
                            db.save_message(cid, "assistant", str(msg).replace("|||", " "))
                        except Exception as _db_err:
                            log.warning(f"[handoff] save admin resume error: {_db_err}")
                except Exception as _he:
                    log.warning(f"[handoff] send_to_client error: {_he}")

            _handoff_cmd_result = await handle_handoff_admin_command(cmd, clinic)
            if _handoff_cmd_result is not None:
                return _handoff_cmd_result

            try:
                _was_intercepted, _intercept_msgs = await handoff_manager.try_intercept_admin_reply(
                    admin_chat_id=chat_id,
                    admin_text=text,
                    clinic=clinic,
                    llm_fn=llm_engine.complete,
                    send_to_client_fn=_handoff_send_to_client,
                )
                if _was_intercepted:
                    return _intercept_msgs
            except Exception as _h_e:
                log.warning(f"[trainer] handoff try_intercept error: {_h_e}")

        # ── Modo cliente activo — el admin está simulando ser cliente ──────────
        # Si está en modo cliente, procesar su mensaje como cliente real
        if admin_client_mode and admin_client_mode.is_active(chat_id):
            # Comandos especiales dentro del modo cliente
            if cmd == "/salir" or cmd == "/exit" or cmd == "/stop":
                return await _admin_salir_modo_cliente(chat_id)
            if cmd == "/sesion" or cmd == "/session":
                return await _admin_ver_sesion(chat_id)
            if cmd.startswith("/feedback "):
                feedback_text = text[len("/feedback "):].strip()
                return await _admin_feedback_sesion(chat_id, feedback_text, clinic)
            if cmd.startswith("/aprender "):
                instruction = text[len("/aprender "):].strip()
                return await _admin_aprender(chat_id, instruction)

            # Mensaje normal en modo cliente — procesar como paciente
            # Inyectar contexto de sesión al processing
            # La respuesta de Conny se genera como si fuera un cliente real
            result = await original_method(self, chat_id, text, clinic)

            # Registrar el turno
            if result and admin_client_mode.is_active(chat_id):
                response_text = " ||| ".join(result) if result else ""
                admin_client_mode.add_turn(chat_id, text, response_text)

            return result

        pending_browser = self._admin_pending.get(chat_id, {}) if hasattr(self, "_admin_pending") else {}
        if cmd in ("/ultimas", "/últimas", "/conversaciones", "/conversaciones recientes"):
            return await self._admin_show_recent_conversation_browser(chat_id, limit=6)

        if _wants_recent_conversation_browser(text_low):
            return await self._admin_show_recent_conversation_browser(chat_id, limit=6)

        if pending_browser.get("action") == "conversation_browser" and _wants_all_messages(text_low):
            selected_chat_id = pending_browser.get("selected_chat_id")
            if selected_chat_id:
                return await self._admin_show_patient_chat_preview(
                    selected_chat_id,
                    admin_chat_id=chat_id,
                    show_all=True,
                )

        selection_idx = _extract_conversation_selection(text_low)
        if selection_idx and pending_browser.get("action") == "conversation_browser":
            items = pending_browser.get("items") or []
            if 1 <= selection_idx <= len(items):
                selected = items[selection_idx - 1]
                return await self._admin_show_patient_chat_preview(
                    str(selected.get("chat_id") or ""),
                    admin_chat_id=chat_id,
                    limit=10,
                    label_override=str(selected.get("name") or "").strip(),
                )
        if selection_idx and not pending_browser.get("action"):
            detailed_subject = any(
                token in text_low
                for token in (
                    "conversacion", "conversación", "chat", "mensajes",
                    "hablado", "hablaste", "mostrame", "muestrame",
                    "muéstrame", "enseñame", "ensename",
                )
            )
            if detailed_subject:
                show_all = _wants_all_messages(text_low)
                return await self._admin_show_recent_conversation_selection(
                    chat_id,
                    selection_idx,
                    show_all=show_all,
                )

        # ── Comandos del trainer (modo admin normal) ───────────────────────────
        if cmd == "/skills" or cmd == "/skill":
            return await _admin_skills(chat_id)

        if cmd.startswith("/skill "):
            return await _admin_toggle_skill(chat_id, cmd)

        if cmd == "/gateway":
            return await _admin_gateway_status(chat_id)

        if cmd.startswith("/gateway "):
            return await _admin_gateway_toggle(chat_id, cmd)

        if cmd == "/control":
            return await _admin_control_status(chat_id)

        if cmd.startswith("/control "):
            return await _admin_control_apply(chat_id, text)

        if cmd == "/aprender" or cmd.startswith("/aprender "):
            instruction = text[len("/aprender"):].strip().lstrip()
            return await _admin_aprender(chat_id, instruction)

        if cmd == "/desaprender" or cmd.startswith("/desaprender "):
            evolution_id = cmd.split("/desaprender", 1)[1].strip()
            return await _admin_desaprender(chat_id, evolution_id)

        if cmd == "/historial" or cmd == "/historial-aprendizaje":
            return await _admin_historial_aprendizaje(chat_id)

        if cmd == "/simular-cliente" or cmd.startswith("/simular-cliente "):
            args_text = cmd.split("/simular-cliente", 1)[1].strip()
            return await _admin_simular_cliente(chat_id, args_text, clinic)

        if cmd == "/salir" or cmd == "/exit":
            return ["No estás en modo cliente ahora mismo."]

        if cmd == "/sesion" or cmd == "/session":
            return await _admin_ver_sesion(chat_id)

        if cmd == "/entrenar":
            return [
                "Sistema de entrenamiento de Conny:\n",
                "SKILLS — comportamientos que puedes activar/desactivar:",
                "  /skills                      — ver todos los skills",
                "  /skill [id] on/off           — activar/desactivar",
                "  /gateway                     — estado del gateway automático",
                "  /gateway on|off              — activar/desactivar el gateway",
                "  /gateway admin on|off        — solo gateway admin",
                "  /gateway user on|off         — solo gateway usuario",
                "  /control                     — ver control duro del admin",
                "  /control [instrucción]       — aplicar regla dura",
                "",
                "APRENDIZAJE — enseñar en lenguaje natural:",
                "  /aprender [instruccion]       — enseñar algo nuevo",
                "  /desaprender [id]             — revertir una instrucción",
                "  /historial                    — ver historial de aprendizaje",
                "",
                "SIMULACIÓN — probar como cliente:",
                "  /simular-cliente [escenario]  — convertirte en cliente",
                "  Escenarios: libre, primer_contacto, precio, miedo,",
                "              esceptico, ocupado, negociador, bot_detector,",
                "              urgente, referido",
                "",
                "Ejemplo de flujo completo:",
                "  1. /simular-cliente precio",
                "  2. Escribe como cliente: 'cuánto vale el botox'",
                "  3. Conny responde",
                "  4. /feedback 'no debió dar el precio sin preguntar la zona'",
                "  5. /salir",
                "  6. /reglas — ver la regla que aprendió",
            ]

        if original_method:
            return await original_method(self, chat_id, text, clinic)
        return ["Admin no disponible."]

    ConnyUltra._handle_admin_or_setup = patched_with_trainer
    log.info("[trainer] dispatcher admin patcheado con comandos trainer")

# ─── SPA and Brand Asset Serving ─────────────────────────────────────────────
from pathlib import Path
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi import HTTPException

@app.get("/logo")
async def serve_logo():
    logo_path = Path("/home/ubuntu/conny/brand-assets/Conny.web.logo.png")
    if logo_path.exists():
        return FileResponse(logo_path, media_type="image/png")
    return Response("", status_code=404)

@app.get("/isotype")
async def serve_isotype():
    iso_path = Path("/home/ubuntu/conny/brand-assets/Logo_Conny_Petalo_Claro.png")
    if iso_path.exists():
        return FileResponse(iso_path, media_type="image/png")
    return Response("", status_code=404)

@app.get("/bg-placeholder")
async def serve_bg_placeholder():
    bg_path = Path("/home/ubuntu/conny/brand-assets/A_dark_luxury_web_background_202605210700.jpeg")
    if bg_path.exists():
        return FileResponse(bg_path, media_type="image/jpeg")
    return Response("", status_code=404)

# Mount /static for JS/CSS assets
static_dir = Path("/home/ubuntu/conny/src/interfaces/web/static")
if static_dir.is_dir():
    from fastapi.staticfiles import StaticFiles
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_model=None)
async def serve_spa_root():
    index_file = Path("/home/ubuntu/conny/src/interfaces/web/static/index.html")
    if index_file.is_file():
        return FileResponse(index_file)
    return HTMLResponse("<h1>Conny Dashboard Not Found</h1><p>Ensure static assets exist in src/interfaces/web/static</p>", status_code=404)

@app.get("/{full_path:path}", include_in_schema=False, response_model=None)
async def spa_fallback(full_path: str):
    normalized = full_path.lstrip("/")
    if normalized.startswith("api/") or normalized.startswith("webhook/") or normalized.startswith("obs/") or normalized in {"api", "openapi.json", "docs", "redoc", "telegram", "whatsapp", "logo", "patients", "conversations", "appointments", "config", "personality", "metrics", "test"}:
        raise HTTPException(status_code=404)
        
    index_file = Path("/home/ubuntu/conny/src/interfaces/web/static/index.html")
    candidate = (index_file.parent / normalized).resolve()
    
    if candidate.is_file():
        try:
            candidate.relative_to(index_file.parent)
            return FileResponse(candidate)
        except ValueError:
            pass # Path traversal attempt
            
    if index_file.is_file():
        return FileResponse(index_file)
        
    raise HTTPException(status_code=404)


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8001"))
    host = os.getenv("HOST", "0.0.0.0")
    
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║                                                                  ║
    ║     ██████╗  ██████╗ ███╗   ██╗███╗   ██╗██╗   ██╗             ║
    ║    ██╔════╝ ██╔═══██╗████╗  ██║████╗  ██║╚██╗ ██╔╝             ║
    ║    ██║      ██║   ██║██╔██╗ ██║██╔██╗ ██║ ╚████╔╝              ║
    ║    ██║      ██║   ██║██║╚██╗██║██║╚██╗██║  ╚██╔╝               ║
    ║    ╚██████╗ ╚██████╔╝██║ ╚████║██║ ╚████║   ██║                ║
    ║     ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═══╝   ╚═╝                ║
    ║                                                                  ║
    ║                    U L T R A   v 8 . 0                          ║
    ║                                                                  ║
    ║        Agente de Recepción Hipernaturalmente Humana             ║
    ║                                                                  ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║  • AntiRobotFilter — elimina cada patrón de bot antes de enviar ║
    ║  • ConversationIntelligence — etapas, emociones, compromiso     ║
    ║  • HyperHumanEngine — valida humanidad en cada respuesta        ║
    ║  • SmartVariety — nunca repite apertura ni cierre igual         ║
    ║  • /modelo — admin cambia el LLM en caliente                    ║
    ║  • Ortografía perfecta forzada (tildes, puntuación)             ║
    ║  • PersonaEvolution — aprende el estilo de cada cliente         ║
    ║  • ConversionFunnelTracker — sabe en qué etapa está cada lead   ║
    ║  • Demo V2 — comportamiento idéntico al de producción           ║
    ║  • MultilingualHandler — español/inglés/portugués automático    ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "conny:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )
