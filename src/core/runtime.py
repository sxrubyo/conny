# -*- coding: utf-8 -*-
"""Bublee runtime execution layer."""
from __future__ import annotations

# Import all globals, vocabularies, and libraries dynamically (including underscore-prefixed names)
import src.core.globals as globals_module
for name in dir(globals_module):
    if not name.startswith("__"):
        globals()[name] = getattr(globals_module, name)


class BubleeUltra:
    """Orquestador principal de Bublee Ultra V7.0."""

    def __init__(self):
        self.db = db
        self.analyzer = analyzer
        self.search = WebSearchEngine()
        self.reasoning: ReasoningEngine = None
        self.generator: ResponseGenerator = None
        self.self_improvement = None
        self.admin_learning: AdminLearningEngine = None
        self.simulator: SimulationEngine = None
        # ── Atributos base (antes de managers que los usan) ──────────────────────
        self._demo_sessions: Dict[str, float] = {}
        self._emoji_chats_off: set = set()
        self._chat_routes: Dict[str, Dict[str, Any]] = {}

        # ── Demo: trucos progresivos y comandos del modo demo ─────────────────
        self._DEMO_TRICKS_ORDER = [
            ("/objecion",  "ver cómo manejo objeciones en vivo"),
            ("/cita",      "ver cómo agendo una cita completa"),
            ("/luxury",    "activar personalidad premium"),
            ("/empatica",  "cambiar a modo empático y de escucha"),
            ("/stats",     "ver el impacto en números reales"),
            ("/prueba",    "lanzarme el mensaje más difícil que tengas"),
            ("/cierre",    "ver cómo cierro una venta"),
            ("/directa",   "activar modo al grano sin rodeos"),
            ("/menu",      "ver modo bot con emojis y menú numerado"),
            ("/2am",       "verme responder a las 2 de la madrugada"),
        ]

        # Gestores de áreas separadas (v9)
        self.demo_mgr = BubleeDemo(self)
        self.admin_mgr = BubleeAdmin(self)
        self.production_mgr = BubleeProduction(self)
        self._conversation_engine = None

        # V7.0 — orquestador de agentes especializados
        self._orchestrator = None   # se inicializa en initialize() cuando llm_engine existe

        self._pending_buffers: Dict[str, Dict] = {}
        self._admin_pending: Dict[str, Dict] = {}
        self._last_reviewed_chat: Optional[str] = None
        self._availability_pending_patient: Optional[str] = None

        if _SESSION_MANAGER_AVAILABLE:
            self._session_mgr = SessionManager(self._demo_sessions, self._emoji_chats_off)
        if _AUDIO_HANDLER_AVAILABLE:
            self._audio_handler = AudioHandler()
        if _GENERATOR_MANAGER_AVAILABLE:
            self._generator_mgr = GeneratorManager(llm_engine, None)

    def _remember_route(self, chat_id: str, route: Optional[Dict[str, Any]] = None):
        if not route:
            return
        clean = {
            "platform": route.get("platform") or Config.PLATFORM,
            "seen_at": time.time(),
        }
        self._chat_routes[str(chat_id)] = clean
        try:
            if db:
                db.remember_contact_route(chat_id, clean["platform"])
        except Exception:
            pass

    def _resolve_route(self, chat_id: str, route: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if route:
            self._remember_route(chat_id, route)
            return route
        remembered = self._chat_routes.get(str(chat_id))
        if remembered:
            return remembered
        try:
            if db:
                persisted = db.get_contact_route(chat_id)
                if persisted:
                    route = {"platform": persisted}
                    self._chat_routes[str(chat_id)] = route
                    return route
        except Exception:
            pass
        return {"platform": Config.PLATFORM}

    def _brand_store(self, clinic: Dict[str, Any]) -> Optional["BrandAssetStore"]:
        if not _BRAND_ASSETS_AVAILABLE:
            return None
        clinic_name = clinic.get("name") or clinic.get("tagline") or Config.SECTOR or "bublee"
        brand_key = clinic_name
        try:
            remembered_slug = (db.recall("instance_slug") or "").strip() if db else ""
            meta = _load_instance_metadata()
            meta_slug = str(meta.get("name") or "").strip() if isinstance(meta, dict) else ""
            brand_key = remembered_slug or meta_slug or clinic_name
        except Exception:
            brand_key = clinic_name
        try:
            return BrandAssetStore(Config.BRAND_ASSETS_BASE_DIR, brand_key)
        except Exception as e:
            log.warning(f"[brand] no pude abrir el vault: {e}")
            return None
    
    async def initialize(self):
        """Inicializa todos los componentes."""
        init_database()
        init_llm()
        init_auth()
        # admin_learning/simulator/reasoning/generator se instancian más abajo,
        # después de restaurar credenciales de WhatsApp y business_bootstrap
        # (antes se creaban también acá, se descartaban sin usar, y se volvían
        # a crear más abajo — duplicado innecesario).
        init_calendar()
        await init_mcp()
        try:
            await init_task_manager()
        except NameError:
            log.warning("[startup] init_task_manager no disponible — saltando")
        except Exception as _tm_err:
            log.warning(f"[startup] init_task_manager error: {_tm_err}")

        # Nova governance bridge
        if _NOVA_AVAILABLE and Config.NOVA_ENABLED:
            nova_guard = init_nova()
            # Verificar si Nova está activo
            client = get_client()
            if client:
                nova_alive = await client.health_check()
                if nova_alive:
                    log.info("[nova] conectado y activo")
                    # Auto-crear agente si no hay token configurado
                    if not Config.NOVA_TOKEN:
                        clinic = db.get_clinic()
                        token_id = await setup_bublee_agent(
                            client, clinic.get("name", "Clinica"),
                            "Bublee"
                        )
                        if token_id:
                            log.info(f"[nova] agente creado automáticamente: {token_id[:16]}...")
                else:
                    log.warning("[nova] server no disponible — modo degradado")

        # Restaurar credenciales WhatsApp desde DB (si fueron configuradas antes)
        try:
            clinic = db.get_clinic()
            wa_phone_id    = clinic.get("wa_phone_id", "")
            wa_access_token = clinic.get("wa_access_token", "")
            wa_verify_token = clinic.get("wa_verify_token", "")
            if wa_phone_id and wa_access_token:
                WhatsAppConnector.apply_to_config(
                    wa_phone_id, wa_access_token, wa_verify_token
                )
                log.info(f"[wa] credenciales restauradas desde DB: {wa_phone_id[:8]}...")
        except Exception as e:
            log.warning(f"[wa] no se pudieron restaurar credenciales: {e}")

        try:
            ensure_minimum_business_state()
        except Exception as exc:
            log.warning(f"[business_bootstrap] error: {exc}")

        # NOTA: antes estas 4 líneas se ejecutaban DOS VECES seguidas dentro
        # de este mismo initialize() — se creaban admin_learning/simulator/
        # reasoning/generator, se descartaban sin usar, y se volvían a crear
        # unas líneas más abajo. Se dejó solo la segunda tanda (que además
        # agrega self_improvement) para no instanciar objetos al pedo.
        self.admin_learning   = AdminLearningEngine(db)
        self.simulator        = SimulationEngine(self)
        self.reasoning        = ReasoningEngine(llm_engine)
        self.generator        = ResponseGenerator(llm_engine, learning_engine=self.admin_learning)
        self.self_improvement = None
        try:
            self.self_improvement = SelfImprovementEngine(llm_engine)
        except (NameError, AttributeError):
            log.warning("[startup] SelfImprovementEngine no disponible")

        if Config.BUBLEE_CORE_ENABLED and _BUBLEE_CORE_AVAILABLE:
            try:
                self._conversation_registry = PersonaRegistry(Config.BUBLEE_CORE_PERSONAS_DIR)
                self._conversation_engine = ConversationEngine(self._conversation_registry)
                log.info("[bublee_core] conversation core OK")
            except Exception as _mcore_err:
                self._conversation_registry = None
                self._conversation_engine = None
                log.warning(f"[bublee_core] no se pudo activar el core nuevo: {_mcore_err}")
        else:
            self._conversation_registry = None
            self._conversation_engine = None
            log.info("[bublee_core] desactivado o no disponible")

        # V8.0 — inicializar sistemas de humanidad real
        # CRÍTICO: envuelto en try/except para que un fallo en V8
        # NUNCA crashee el bot principal
        try:
            init_v8_systems()
            log.info("[v8] core OK")
        except Exception as _ev8:
            log.warning(f"[v8] init_v8_systems falló — V8 degradado: {_ev8}")
        try:
            init_v8_extended_systems()
            log.info("[v8] extended OK")
        except Exception as _ev8ext:
            log.warning(f"[v8] init_v8_extended falló: {_ev8ext}")
        # _patch_admin_dispatcher se llama SOLO en lifespan

        # V7.0 — activable por flag para rollout seguro
        v7_enabled = os.getenv("BUBLEE_V7_ENABLED", "false").lower() in ("1", "true", "yes", "on")
        if v7_enabled:
            try:
                from src.core.orchestrator import BubleeOrchestrator
                self._orchestrator = BubleeOrchestrator(llm_engine, db)
                log.info("[v7] orquestador activado por BUBLEE_V7_ENABLED")
            except Exception as _v7_init:
                self._orchestrator = None
                log.warning(f"[v7] no se pudo activar el orquestador, fallback a generator: {_v7_init}")
        else:
            self._orchestrator = None
            log.info("[v7] orquestador desactivado — usando generator clásico")

        # Programar auto-mejora periódica
        task_manager.schedule_task(
            "self_improve",
            {},
            scheduled_for=datetime.now() + timedelta(hours=1)
        )

        log.info("═══ BUBLEE V9.6.1 INICIALIZADA ═══")
        asyncio.create_task(self._schedule_daily_report())
    
    async def _schedule_daily_report(self):
        """Programa el reporte diario a las 8am."""
        while True:
            try:
                now = now_col()
                # Calcular segundos hasta las 8am del día siguiente
                next_8am = now.replace(hour=8, minute=0, second=0, microsecond=0)
                if now.hour >= 8:
                    next_8am = next_8am + timedelta(days=1)
                wait_seconds = (next_8am - now).total_seconds()
                await asyncio.sleep(wait_seconds)

                # Programar el reporte
                if task_manager:
                    task_manager.schedule_task(
                        task_type="report",
                        data={"type": "daily"},
                        scheduled_for=datetime.now(),
                        priority=5
                    )
                log.info("[daily_report] programado")
            except Exception as e:
                log.error(f"[daily_report] {e}")
                await asyncio.sleep(3600)

    async def _notify_hot_lead(self, clinic: Dict, message: str):
        """Notifica al admin cuando un lead tiene closing_score >= 75%."""
        try:
            admin_ids = _parse_admin_ids(clinic.get("admin_chat_ids", []))
            for admin_id in admin_ids[:2]:
                await self._send_message(admin_id, message)
        except Exception as e:
            log.warning(f"[hot_lead] {e}")

    def _build_conversation_core_clinic(self, clinic: Dict[str, Any], channel: str = "") -> Dict[str, Any]:
        core_clinic = dict(clinic or {})
        sector = _normalize_conv_text(str(core_clinic.get("sector") or Config.SECTOR or ""))
        channel_norm = _normalize_conv_text(channel or core_clinic.get("channel") or Config.PLATFORM or "")
        if sector == "estetica" and not core_clinic.get("persona_key"):
            core_clinic["persona_key"] = "estetica_whatsapp"
        if channel_norm:
            core_clinic["channel"] = channel_norm
        return core_clinic

    def _try_conversation_core(
        self,
        *,
        clinic: Dict[str, Any],
        user_msg: str,
        history: Optional[List[Dict[str, Any]]] = None,
        is_admin: bool = False,
        channel: str = "",
    ) -> Optional[List[str]]:
        if not Config.BUBLEE_CORE_ENABLED or not self._conversation_engine:
            return None
        try:
            core_clinic = self._build_conversation_core_clinic(clinic, channel)
            result = self._conversation_engine.handle(
                clinic=core_clinic,
                user_msg=user_msg,
                history=history or [],
                is_admin=is_admin,
                channel=channel,
            )
            if result.handled and result.bubbles:
                return [bubble.strip() for bubble in result.bubbles if str(bubble).strip()]
        except Exception as exc:
            log.warning(f"[bublee_core] fallo en handle(): {exc}")
        return None

    def _llm_runtime_available(self) -> bool:
        """Indica si Bublee tiene un runtime LLM utilizable para priorizarlo sobre fallbacks."""
        try:
            if llm_engine:
                return True
        except Exception:
            pass
        try:
            generator = getattr(self, "generator", None)
            if generator and getattr(generator, "llm", None):
                return True
        except Exception:
            pass
        provider_keys = (
            getattr(Config, "GEMINI_API_KEY", ""),
            getattr(Config, "GEMINI_API_KEY_2", ""),
            getattr(Config, "GEMINI_API_KEY_3", ""),
            getattr(Config, "OPENROUTER_API_KEY", ""),
            getattr(Config, "GROQ_API_KEY", ""),
        )
        return any(bool(key) for key in provider_keys)

    def _handle_patient_meta_question(
        self,
        clinic: Dict,
        chat_id: str = "",
        user_msg: str = "",
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> List[str]:
        clinic_name = clinic.get("name", "la clínica")
        services = clinic.get("services", [])
        channel = ""
        if chat_id:
            try:
                channel = str(self._resolve_route(chat_id).get("platform") or "")
            except Exception:
                channel = ""
        core_bubbles = self._try_conversation_core(
            clinic=clinic,
            user_msg=user_msg or "",
            history=history or [],
            is_admin=False,
            channel=channel,
        )
        if core_bubbles:
            return core_bubbles
        normalized_user = _normalize_conv_text(user_msg or "")
        prior_identity = any(
            any(marker in _normalize_conv_text(str(msg.get("content") or "")) for marker in (
                "recepcionista virtual",
                "asesora virtual",
                "soy bublee",
                "trabaja por tu negocio",
                "trabajo por este canal",
            ))
            for msg in (history or [])
            if msg.get("role") == "assistant"
        )
        if prior_identity:
            if any(marker in normalized_user for marker in ("eres una ia", "eres ia", "eres una persona", "persona real", "eres un bot", "eres bot")):
                return [
                    f"Sigo siendo Bublee, la asesora virtual de {clinic_name}",
                    "Soy una IA hecha para orientar, responder y ayudarte a avanzar sin que todo dependa de una persona pegada al chat",
                ]
            if any(marker in normalized_user for marker in ("quién eres", "quien eres", "qué eres", "que eres")):
                return [
                    f"Soy Bublee, la asesora virtual de {clinic_name}",
                    "Soy una IA pensada para atender bien, sostener la conversación y ayudarte con información, disponibilidad y siguiente paso",
                ]
        try:
            personality = self.generator._get_default_personality(clinic)
        except Exception:
            personality = None
        if personality:
            return self.generator._build_identity_probe_bubbles(clinic, personality, user_msg or "")
        if owner_style_controller:
            fallback = owner_style_controller.get_fallback_template(
                is_admin=False,
                chat_id=chat_id,
                clinic=clinic,
            )
            if fallback:
                return [part.strip() for part in fallback.split("|||") if part.strip()]
        services_text = ", ".join(services[:2]) if services else "citas e información"
        return [
            f"Soy Bublee, la asesora virtual de {clinic_name}",
            f"Soy una IA pensada para ayudarte con {services_text}, horarios y orientación inicial",
            "Si quieres probarme, escríbeme el nombre de tu negocio y te muestro cómo trabajaría contigo",
        ]

    def _build_demo_patient_clinic(self, clinic: Dict[str, Any]) -> Dict[str, Any]:
        demo_clinic = dict(clinic or {})
        clinic_name = str(demo_clinic.get("name") or "").strip()
        sector = str(demo_clinic.get("sector") or "").strip().lower()
        env_sector = str(Config.SECTOR or Config.DEMO_SECTOR or "").strip().lower()
        configured_demo_name = str(Config.DEMO_BUSINESS_NAME or "").strip()
        normalized_demo_name = _normalize_conv_text(configured_demo_name)
        if normalized_demo_name in {"clinica demo", "clínica demo", "demo", "nova"}:
            configured_demo_name = ""

        # FIX: En modo demo para leads nuevos (sin negocio conocido), NO mostrar nombre de negocio
        # Solo usar DEMO_BUSINESS_NAME si es un negocio real configurado, no "demo" genérico
        if Config.DEMO_MODE and configured_demo_name and normalized_demo_name not in {"clinica demo", "clínica demo", "demo", "nova"}:
            demo_clinic["name"] = configured_demo_name
        elif clinic_name.lower() == "nova":
            demo_clinic["name"] = "la clínica"
        elif not clinic_name.strip():
            # En demo mode para leads nuevos, usar "tu clínica" en vez de nombre específico
            demo_clinic["name"] = "la clínica"

        if not sector or sector == "otro":
            demo_clinic["sector"] = env_sector or "estetica"

        if not demo_clinic.get("platform"):
            demo_clinic["platform"] = str(Config.PLATFORM or "").strip().lower()
        return demo_clinic

    def _demo_should_use_patient_chat_path(self, user_msg: str) -> bool:
        normalized = _normalize_conv_text(user_msg or "")
        if not normalized:
            return False

        token_set = set(re.findall(r"[a-z0-9áéíóúüñ]+", normalized))

        def _has_marker(marker: str) -> bool:
            marker_norm = _normalize_conv_text(marker or "")
            if not marker_norm:
                return False
            if " " in marker_norm:
                return marker_norm in normalized
            return marker_norm in token_set

        owner_exceptions = (
            "config", "demo", "prueba", "probar", "entrenar", "enseñar",
            "cómo funcionas", "como funcionas", "qué haces", "que haces",
            "quiero una demo", "quiero demo", "hagamos una demo", "simulacion",
            "simulación", "modo demo", "tengo un negocio", "tengo una empresa",
            "what is this", "what do you do", "who are you", "english only",
            "i don't talk spanish", "i dont talk spanish", "i don't understand", "i dont understand",
            "me mandaron", "me enviaron", "me pasaron", "me recomendaron",
            "no se que es", "no sé qué es", "que es esto", "qué es esto",
            "como funciona esto", "cómo funciona esto", "para que sirve", "para qué sirve",
            "me dijeron que", "alguien me dijo", "me lo recomendaron",
        )
        if any(_has_marker(exc) for exc in owner_exceptions):
            return False

        if any(_has_marker(marker) for marker in ("5 x 4", "5x4", "capital de francia", "capital de")):
            return False
        if any(
            _has_marker(marker)
            for marker in (
                "cuanto es",
                "cuánto es",
                "quien te hizo",
                "quién te hizo",
                "para que",
                "para qué",
                "aceptas audios",
                "aceptas pdf",
            )
        ):
            return False

        # Keywords de cliente/lead (mensaje de alguien preguntando como cliente)
        client_intent_markers = (
            # Servicios
            "botox", "relleno", "rellenos", "laser", "láser", "facial",
            "tratamiento", "tratamientos", "procedimiento", "procedimientos",
            "cita", "agenda", "agendar", "disponibilidad", "valoracion", "valoración",
            "consulta", "sesion", "sesión", "toxina", "hifu", "prp", "hidrafacial",
            # Precios
            "precio", "costo", "cuánto", "cuanto", "tarifa",
            # Ubicación/horario
            "horario", "hora", "abierta", "abierto", "cerrado", "ubicación", "dirección",
            # Agendamiento
            "reservar", "reserva", "mañana", "hoy", "viernes", "lunes", "sábado",
            "tarde", "noche", "pronto", "primavera", "urgencia", "emergencia",
            # generic lead
            "quiero", "necesito", "busco", "me interesa", "información",
            "saber", "acerca", "sobre", "qué tienen", "que tienen", "servicios",
        )
        if any(_has_marker(token) for token in client_intent_markers):
            return True

        if any(_has_marker(marker) for marker in ("cuanto es", "cuánto es", "cuanto cuestas", "cuánto cuestas", "cuanto vale", "cuánto vale", "que es", "qué es")):
            if not any(_has_marker(token) for token in client_intent_markers):
                return False

        owner_demo_markers = (
            "hola",
            "hola buenas",
            "buenas",
            "buenas tardes",
            "buenos dias",
            "buenos días",
            "buenas noches",
            "hey",
            "holi",
            "quien eres",
            "quién eres",
            "que eres",
            "qué eres",
            "que haces",
            "qué haces",
            "como funcionas",
            "cómo funcionas",
            "como trabajas",
            "cómo trabajas",
            "para que",
            "para qué",
            "por que",
            "por qué",
            "quien te hizo",
            "quién te hizo",
            "como te hicieron",
            "cómo te hicieron",
            "aceptas audios",
            # Prospect B2B markers (solo para pregunta de precio, NO para cambiar el flujo de demo)
            "cuanto cuestas",
            "cuánto cuestas",
            "cuanto cobras",
            "cuánto cobras",
            "cuanto vale",
            "cuánto vale",
            "me mandaron",
            "me pasaron",
            "aceptas audio",
            "aceptas pdf",
            "lees pdf",
            "lees archivos",
            "me mandaron tu numero",
            "me mandaron tu número",
            "me pasaron tu numero",
            "me pasaron tu número",
            "quiero probarte",
            "me gustaria probarte",
            "me gustaría probarte",
            "quiero una demo",
            "quiero demo",
            "tengo un negocio",
            "tengo una empresa",
            "me lo recomendaron",
            "me dijeron que te escribiera",
            "me dejaron probarte",
            "me pasaron este numero",
            "me pasaron este número",
            "para mi negocio",
            "para mi empresa",
            "what is this",
            "what do you do",
            "who are you",
            "english only",
            "i don't talk spanish",
            "i dont talk spanish",
            "i don't understand",
            "i dont understand",
        )
        if any(_has_marker(marker) for marker in owner_demo_markers):
            return False

        patient_like_markers = (
            "botox",
            "relleno",
            "rellenos",
            "laser",
            "láser",
            "cita",
            "agenda",
            "agendar",
            "disponibilidad",
            "precio",
            "cuanto",
            "cuánto",
            "valor",
            "tratamiento",
            "procedimiento",
            "consulta",
            "quiero informacion",
            "quiero información",
            "quiero una cita",
            "me quiero valorar",
            "valoracion",
            "valoración",
            "me interesa el botox",
            "me interesa botox",
            "me interesa el tratamiento",
            "me interesa el procedimiento",
            "quiero info sobre",
            "quiero saber del tratamiento",
            "quiero reservar",
            "quiero una reserva",
            "quiero apartar",
            "me duele",
            "me preocupa",
            "me mandaron por botox",
        )
        return any(_has_marker(marker) for marker in patient_like_markers)

    def _handle_patient_off_topic(self, clinic: Dict, chat_id: str = "", user_msg: str = "") -> List[str]:
        """Maneja mensajes fuera de tema con respuestas variadas según el tipo de off-topic."""
        if owner_style_controller:
            fallback = owner_style_controller.get_fallback_template(
                is_admin=False,
                chat_id=chat_id,
                clinic=clinic,
            )
            if fallback:
                return [part.strip() for part in fallback.split("|||") if part.strip()]

        services = clinic.get("services", [])
        focus = ", ".join(services[:2]) if services else "servicios, horarios o citas"
        normalized = (user_msg or "").lower()

        # Respuestas diferenciadas según el tipo de off-topic
        if any(t in normalized for t in ["película", "pelicula", "movie", "cine", "serie", "netflix"]):
            return [
                "eso ya se sale de lo que manejo por acá",
                f"si quieres, te ayudo con {focus} o agendamos una cita"
            ]

        if any(t in normalized for t in ["clima", "tiempo", "lluvia", "calor", "frío", "frio"]):
            return [
                "el clima no lo manejo desde este chat",
                f"pero si necesitas {focus} o información de citas, ahí sí te ayudo"
            ]

        if any(t in normalized for t in ["comida", "restaurante", "almuerzo", "cena", "desayuno"]):
            return [
                "eso de comida no lo manejo por aquí",
                f"te puedo ayudar con {focus} si quieres"
            ]

        if any(t in normalized for t in ["música", "musica", "canción", "cancion", "artista", "banda"]):
            return [
                "la música no es algo que maneje desde acá",
                f"pero para {focus} o citas, ahí sí te oriento"
            ]

        if any(t in normalized for t in ["bitcoin", "crypto", "cripto", "trading", "crypto"]):
            return [
                "eso de criptos no lo manejo por este canal",
                f"si quieres información de {focus}, ahí te ayudo"
            ]

        if any(t in normalized for t in ["fútbol", "futbol", "messi", "deporte", "partido"]):
            return [
                "el deporte no es algo que maneje desde aquí",
                f"pero si es por {focus} o citas, te ayudo con gusto"
            ]

        # Fallback genérico con variación
        variants = [
            ["eso se sale un poco de lo que manejo por acá", f"si quieres, te ayudo con {focus} o con una cita"],
            ["eso no lo manejo desde este chat", f"pero para {focus} o información de citas, ahí sí te ayudo"],
            ["eso ya es por fuera de lo que hago acá", f"si necesitas {focus}, te ayudo sin problema"],
        ]
        import hashlib
        idx = int(hashlib.md5(normalized.encode()).hexdigest()[:2], 16) % len(variants)
        return variants[idx]

    async def _download_telegram_binary(self, file_id: str) -> Tuple[bytes, str]:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.get(
                f"https://api.telegram.org/bot{Config.TELEGRAM_TOKEN}/getFile",
                params={"file_id": file_id},
            )
            data = r.json()
            file_path = data.get("result", {}).get("file_path", "")
            if not file_path:
                raise RuntimeError("Telegram no devolvió file_path")
            dl = await client.get(
                f"https://api.telegram.org/file/bot{Config.TELEGRAM_TOKEN}/{file_path}"
            )
            dl.raise_for_status()
            return dl.content, Path(file_path).name or "telegram_asset.bin"

    async def _download_whatsapp_cloud_binary(self, media_id: str) -> Tuple[bytes, str, str]:
        async with httpx.AsyncClient(timeout=20.0) as client:
            meta = await client.get(
                f"https://graph.facebook.com/v20.0/{media_id}",
                headers={"Authorization": f"Bearer {Config.WA_ACCESS_TOKEN}"},
            )
            meta.raise_for_status()
            payload = meta.json() if meta.content else {}
            media_url = payload.get("url", "")
            if not media_url:
                raise RuntimeError("WhatsApp Cloud no devolvió URL del media")
            dl = await client.get(
                media_url,
                headers={"Authorization": f"Bearer {Config.WA_ACCESS_TOKEN}"},
            )
            dl.raise_for_status()
            filename = payload.get("id", media_id)
            mime_type = payload.get("mime_type", "application/octet-stream")
            return dl.content, filename, mime_type

    async def _admin_ingest_assets(
        self,
        chat_id: str,
        text: str,
        attachments: List[Dict[str, Any]],
        clinic: Dict[str, Any],
    ) -> Optional[List[str]]:
        if not attachments:
            return None

        store = self._brand_store(clinic)
        if not store:
            return ["No pude abrir el vault de marca en esta instalación."]

        saved_items: List[Dict[str, Any]] = []
        extracted_blocks: List[str] = []

        for item in attachments:
            kind = item.get("kind", "asset")
            platform = item.get("platform", Config.PLATFORM)
            caption = (item.get("caption") or "").strip()
            filename = item.get("filename") or ("logo.png" if kind == "image" else "document.bin")
            mime_type = item.get("mime_type", "")
            raw_bytes = item.get("bytes")

            try:
                if platform == "telegram" and item.get("file_id"):
                    raw_bytes, downloaded_name = await self._download_telegram_binary(item["file_id"])
                    if not item.get("filename"):
                        filename = downloaded_name
                elif platform == "whatsapp_cloud" and item.get("media_id"):
                    raw_bytes, downloaded_name, downloaded_mime = await self._download_whatsapp_cloud_binary(item["media_id"])
                    if not item.get("filename"):
                        filename = downloaded_name
                    if not mime_type:
                        mime_type = downloaded_mime
                elif item.get("base64"):
                    import base64 as _b64
                    raw_bytes = _b64.b64decode(item["base64"])
                elif isinstance(raw_bytes, str):
                    raw_bytes = raw_bytes.encode("utf-8")
            except Exception as e:
                log.warning(f"[brand] fallo descargando adjunto {filename}: {e}")
                continue

            if not raw_bytes:
                continue

            lower_name = f"{filename} {caption}".lower()
            if any(tag in lower_name for tag in ["logo", "isotipo", "brand", "identidad", "manual", "paleta", "colores"]):
                category = "brand"
            elif kind == "image":
                category = "visual"
            else:
                category = "knowledge"

            saved = store.save_binary_asset(
                filename=filename,
                data=raw_bytes,
                mime_type=mime_type,
                source=f"{platform}_attachment",
                category=category,
                caption=caption,
            )
            if saved.manifest_entry:
                saved_items.append(saved.manifest_entry)
            if saved.extracted_text and len(saved.extracted_text.strip()) > 20:
                extracted_blocks.append(saved.extracted_text.strip())
            if category == "brand" and any(tag in lower_name for tag in ["logo", "isotipo"]):
                db.remember("brand_logo_asset", saved.saved_path, "identity")

        extra_note = (text or "").strip()
        if extra_note:
            note_saved = store.save_text_note(
                "admin_brand_note",
                extra_note,
                source="admin_chat",
                category="knowledge",
            )
            if note_saved.manifest_entry:
                saved_items.append(note_saved.manifest_entry)
            if len(extra_note) > 40:
                extracted_blocks.append(extra_note)

        if not saved_items and not extracted_blocks:
            return ["Recibí el adjunto, pero no pude guardarlo bien. Intenta de nuevo."]

        if kb and extracted_blocks:
            try:
                kb.append("\n\n".join(block for block in extracted_blocks if block.strip()))
            except Exception as e:
                log.warning(f"[brand] no pude anexar al KB: {e}")

        manifest = store.manifest()
        db.remember("brand_assets_path", str(store.root), "identity")
        db.remember("brand_assets_count", str(len(manifest.get("assets", []))), "identity")
        db.remember("brand_identity_summary", store.latest_identity_summary(), "identity")
        db.remember("brand_last_upload_at", datetime.now().isoformat(), "identity")

        latest = saved_items[-4:]
        latest_lines = "\n".join(
            f"• {item.get('filename', 'asset')} [{item.get('category', 'asset')}]"
            for item in latest
        )
        return [
            "Listo. Ya guardé esos activos en el vault permanente de la marca.",
            f"Ruta: {store.root}\nArchivos recientes:\n{latest_lines}",
            "Desde ahora los conservo por instancia y los uso como contexto oficial. Si el adjunto tenía texto, ya quedó anexado al conocimiento activo.",
        ]

    async def _admin_brand_status(self, clinic: Dict[str, Any]) -> List[str]:
        store = self._brand_store(clinic)
        if not store:
            return ["El vault de marca no está disponible en esta instalación."]
        summary = "\n".join(store.summary_lines())
        return [
            "Vault de marca activo.",
            summary,
            "Puedes mandarme logos, manuales, identidad de marca, PDFs, DOCX, TXT, MD o JSON. Lo guardo por instancia y no lo olvido.",
        ]


    async def _process_patient_message(self, chat_id: str, text: str, clinic: dict, history: list, conv_state: dict, is_audio: bool = False, attachments: list = None) -> list:
        if self.production_mgr:
            return await self.production_mgr.handle(chat_id, text, clinic, history, conv_state, attachments=attachments)
        return []
    async def process_message(self, chat_id: str, text: str,
                             is_audio: bool = False,
                             attachments: Optional[List[Dict[str, Any]]] = None,
                             route: Optional[Dict[str, Any]] = None,
                             is_simulation: bool = False) -> List[str]:
        """Procesa un mensaje delegando a los gestores especializados."""
        start_time = time.time()
        attachments = attachments or []
        self._remember_route(chat_id, route)
        
        try:
            clinic = db.get_clinic()
            admin_ids = _parse_admin_ids(clinic.get("admin_chat_ids", []))
            is_admin = (chat_id in admin_ids or db.get_admin(chat_id) is not None)
            
            # En modo simulación, tratamos al admin como un paciente real
            effective_is_admin = is_admin and not is_simulation

            # 1. Auth check (ignorar en simulación)
            if not is_simulation and auth_engine and auth_engine.is_auth_message(chat_id, text):
                result = await auth_engine.process(chat_id, text)
                if result: return result

            # 1.5. Slash commands (works in all modes)
            if text.strip().startswith("/"):
                try:
                    from bublee_commands import get_command_handler
                    _cmd_h = get_command_handler(getattr(self, "_instance_id", "default"))
                    _cmd_result = await _cmd_h.handle(chat_id, text.strip(), is_admin=False, clinic=clinic, db=db)
                    if _cmd_result:
                        return _cmd_result
                except Exception:
                    pass

            # --- CLASIFICACIÓN Y RUTEO ---
            if Config.DEMO_MODE:
                log.info(f"[Router] Ruteando mensaje de {chat_id} a Modo Demo (DEMO_MODE=True)")
                return await self._handle_demo_message(chat_id, text, clinic, attachments)
            
            # Modo producción: localizar admin e identificar si es nueva instancia o ya configurada
            is_setup_done = bool(clinic.get("setup_done"))
            log.info(f"[Router] Modo Producción Activo. Instancia: {'Configurada' if is_setup_done else 'Nueva Instancia (Falta Setup)'}")
            
            if effective_is_admin:
                log.info(f"[Router] Admin detectado ({chat_id}). Ruteando a Panel Admin.")
                return await self._handle_admin_message(chat_id, text, clinic, is_audio=is_audio, attachments=attachments)
            
            if not is_setup_done:
                log.warning(
                    f"[Router] Remitente {chat_id} no es admin y la instancia no está configurada aún. "
                    "Bloqueando setup hasta token de activación."
                )
                return ["Ingresa tu Token de Activación para comenzar."]

            # Ruteo normal para paciente en producción
            log.info(f"[Router] Remitente {chat_id} clasificado como Paciente. Ruteando a flujo de producción.")
            conv_state = db.get_conversation_state(chat_id)
            if conv_state and conv_state.escalation_needed and not effective_is_admin:
                # Si el paciente está pidiendo explícitamente hablar con un humano, no lo silenciamos
                # para que el production monitor le responda con el mensaje de transferencia y alerte al admin.
                human_signals = ["hablar con humano", "hablar con una persona", "hablar con alguien",
                                 "quiero hablar con", "pasame con", "pásame con", "un humano",
                                 "una persona real", "talk to a human", "real person", "hablar con un humano",
                                 "asesor humano", "atencion humana", "atención humana", "humano", "asesor",
                                 "atención", "atencion", "contacto", "hablar con alguien"]
                wants_human = any(s in text.lower() for s in human_signals)
                if not wants_human:
                    log.info(f"[mute] Bot is muted for chat_id={chat_id} (escalation_needed=True)")
                    return []
                
            history = db.get_history(chat_id)
            return await self._process_patient_message(chat_id, text, clinic, history, conv_state, is_audio=is_audio, attachments=attachments)

        except Exception as e:
            log.error(f"Error processing message from {chat_id}: {e}", exc_info=True)
            db.record_metric("error", "message_processing", 1, {"error": str(e)})

            # Recuperación inteligente: intentar respuesta LLM directa como fallback
            # (2 intentos — antes era 1 solo, y con cascada de varias keys/proveedores
            # vale la pena un segundo intento antes de escalar a un humano)
            for attempt in range(2):
                try:
                    if llm_engine and text and text.strip():
                        clinic_fb = db.get_clinic()
                        biz_name = clinic_fb.get("name", "") if clinic_fb else ""
                        fallback_sys = f"Eres Bublee, recepcionista virtual{' de ' + biz_name if biz_name else ''}. Responde de forma breve, cálida y natural. Si no tienes contexto suficiente, pide al usuario que te cuente más."
                        fallback_r, _ = await llm_engine.complete(
                            [{"role": "system", "content": fallback_sys}, {"role": "user", "content": text}],
                            model_tier="fast", temperature=0.8, max_tokens=200, use_cache=False,
                        )
                        if fallback_r and fallback_r.strip():
                            return self._split_bubbles(fallback_r, chat_id=chat_id)
                except Exception as e2:
                    log.warning(f"[recovery] intento {attempt+1}/2 de LLM directo falló: {e2}")

            # ── Último recurso: acá antes había una lista de frases hardcodeadas
            # ("perdona, me perdí un momento", etc). Eso es exactamente lo que no
            # se quiere: un texto genérico y repetido al cliente que delata que
            # el bot se rompió. Ahora, si de verdad no hay ninguna respuesta real
            # de IA disponible: al paciente NO se le manda nada (lista vacía —
            # _flush_buffer ya chequea `if bubbles:` antes de enviar), y se avisa
            # de inmediato al dueño vinculado para que entre en persona.
            try:
                from bublee_utils import notify_owner_of_ai_failure, _parse_admin_ids as _parse_admin_ids_fb1
                clinic_fb = db.get_clinic()
                admin_ids = _parse_admin_ids_fb1((clinic_fb or {}).get("admin_chat_ids", []))
                context_label = "prospecto (demo)" if Config.DEMO_MODE else "paciente"
                await notify_owner_of_ai_failure(
                    self._send_message, admin_ids, chat_id, text, context=context_label,
                )
            except Exception as e3:
                log.error(f"[ai_failure] no pude avisarle al dueño sobre {chat_id}: {e3}")

            return []
    async def _handle_demo_message(self, chat_id: str, text: str,
                                    clinic: Dict,
                                    attachments: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        from src.interfaces.web.demo_handler import handle_demo_message
        print("DEBUG RESOLVED FILENAME:", handle_demo_message.__code__.co_filename)
        return await handle_demo_message(self, chat_id, text, clinic, attachments)

    async def _handle_admin_message(self, chat_id: str, text: str, clinic: Dict,
                                   is_audio: bool = False,
                                   attachments: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        # 1. Ingest assets if there are attachments
        if attachments:
            assets_res = await self._admin_ingest_assets(chat_id, text, attachments, clinic)
            if assets_res:
                return assets_res
        
        # 2. Delegate to _handle_admin_or_setup
        return await self._handle_admin_or_setup(chat_id, text, clinic)



    async def _handle_admin_or_setup(self, chat_id: str, text: str,
                                     clinic: Dict) -> List[str]:
        """Maneja modo admin o setup. Nunca lanza excepcion al exterior."""
        from bublee_utils import _parse_admin_ids
        try:
            # Setup inicial — SOLO si el chat_id ya fue autenticado como admin
            # Protege contra pacientes que lleguen antes de que el admin configure
            if not clinic.get("setup_done"):
                admin_ids = _parse_admin_ids(clinic.get("admin_chat_ids", []))

                # ¿Este chat_id fue autenticado via token de activacion?
                is_authenticated_admin = (
                    chat_id in admin_ids or
                    db.get_admin(chat_id) is not None
                )

                if is_authenticated_admin:
                    return await self._handle_setup(chat_id, text, clinic)
                else:
                    # Paciente sin token — pedir activación por LLM o hardcoded
                    try:
                        _tok_llm = getattr(getattr(self, "generator", None), "llm", None)
                        if _tok_llm:
                            r, _ = await _tok_llm.complete(
                                [{"role": "system", "content": "Eres Bublee. El sistema no está activado aún. Respondé de forma breve y amable que para usar el servicio necesita un token de activación. Decí exactamente: 'Ingresa tu Token de Activación para comenzar.' No des más información."},
                                 {"role": "user", "content": text}],
                                model_tier="fast", temperature=0.3, max_tokens=100,
                            )
                            if r and r.strip():
                                return [r.strip()]
                    except Exception:
                        pass
                    return ["Ingresa tu Token de Activación para comenzar."]

            # Comandos slash
            cmd = text.lower().strip()

            natural_model_arg = extract_model_request_from_text(cmd)
            if natural_model_arg:
                return await self._admin_set_model(natural_model_arg, clinic)

            if cmd == "/citas":
                return await self._admin_show_appointments()
            elif cmd == "/config":
                return await self._admin_show_config(clinic)
            elif cmd == "/metricas":
                return await self._admin_show_metrics()
            elif cmd == "/setup":
                return await self._restart_setup(chat_id)
            elif cmd == "/plugins":
                return await self._admin_show_plugins()
            elif cmd == "/personalidad":
                return await self._admin_show_personality(clinic)
            elif cmd == "/control":
                return await _admin_control_status(chat_id)
            elif cmd.startswith("/control "):
                return await _admin_control_apply(chat_id, text)
            elif cmd == "/addadmin":
                if auth_engine:
                    return await auth_engine.create_invite(chat_id)
                return ["Sistema de invitaciones no disponible."]
            elif cmd == "/admins":
                return await self._admin_show_admins()
            elif cmd == "/login":
                db.set_auth_session(chat_id, flow="login", step="email", temp_data={})
                return ["Tu correo electronico de admin?"]
            elif cmd == "/logout":
                if auth_engine:
                    return auth_engine._logout(chat_id)
                return ["Sesion cerrada."]
            elif cmd == "/kb":
                return await self._admin_kb_status()
            elif cmd == "/simular":
                if self.simulator:
                    return self.simulator.start(chat_id)
                return ["El motor de simulación no está disponible."]
            elif cmd == "/kb borrar":
                return await self._admin_kb_clear()
            elif cmd == "/brand":
                return await self._admin_brand_status(clinic)
            # Handler de confirmación de mensajes pendientes
            text_lower = text.lower().strip()
            if text_lower in ("confirmar", "confirmar sí", "confirmar si", "si", "sí", "ok", "si, confirmar"):
                return await self._handle_admin_confirm(chat_id, text)
            elif text_lower in ("cancelar", "no", "cancela"):
                return await self._handle_admin_cancel(chat_id, text)
            
            elif cmd == "/sector":
                return await self._admin_show_sector()
            elif cmd.startswith("/sector "):
                new_sector = cmd.split("/sector ", 1)[1].strip().lower()
                return await self._admin_set_sector(new_sector)

            # ── Calendario ────────────────────────────────────────────────
            elif cmd == "/agenda":
                return await self._admin_agenda_status()
            elif cmd.startswith("/calendly "):
                link = cmd.split("/calendly ", 1)[1].strip()
                if link.startswith("http"):
                    # Guardar en Config y en DB
                    Config.CALENDLY_LINK = link
                    if calendar_bridge:
                        calendar_bridge._calendly_link = link
                    db.update_clinic(calendly_link=link)
                    return [
                        f"Calendly guardado.",
                        f"Cuando un paciente pregunte por horarios, le comparto ese link directamente."
                    ]
                return ["Formato: /calendly https://calendly.com/tu-link"]

            # ── WhatsApp ──────────────────────────────────────────────────
            elif cmd == "/whatsapp":
                return await self._admin_whatsapp_guide(clinic)

            # ── Nova governance ───────────────────────────────────────────
            elif cmd == "/nova":
                return await self._admin_nova_status()
            elif cmd == "/nova ledger":
                return await self._admin_nova_ledger()
            elif cmd.startswith("/nova regla "):
                rule_text = cmd.split("/nova regla ", 1)[1].strip()
                return await self._admin_nova_add_rule(rule_text, clinic)

            # ── V6.0 — Nuevos comandos ────────────────────────────────────
            elif cmd == "/pipeline":
                return await self._admin_pipeline()
            elif cmd == "/perdidos":
                return await self._admin_lost_analysis()
            elif cmd == "/coach":
                return await self._admin_sales_coach()
            elif cmd == "/estilo":
                return await self._admin_clone_style(chat_id)
            elif cmd == "/reactivar":
                return await self._admin_reactivate_dormant()
            elif cmd == "/seguimiento":
                return await self._admin_configure_followup(clinic)
            elif cmd == "/preconsulta":
                return await self._admin_preconsult_config(clinic)
            elif cmd.startswith("/broadcast "):
                msg_text = cmd.split("/broadcast ", 1)[1].strip()
                return await self._admin_broadcast(msg_text)
            elif cmd == "/instagram":
                return await self._admin_instagram_guide()
            elif cmd == "/pagos":
                return await self._admin_payments_guide()
            elif cmd == "/reporte":
                return await self._admin_trigger_report()

            # ── V8.0 — Modelo en caliente ─────────────────────────────────
            elif cmd == "/modelo":
                return await self._admin_show_model(clinic)
            elif cmd.startswith("/modelo "):
                arg = cmd.split("/modelo ", 1)[1].strip()
                return await self._admin_set_model(arg, clinic)
            elif cmd == "/v8":
                return await self._admin_v8_status()
            elif cmd == "/v8 reset":
                # Desbloquear todos los providers manualmente
                if llm_engine:
                    for p in llm_engine.providers:
                        llm_engine._failures[p.name] = 0
                        llm_engine._blocked_until[p.name] = 0
                    return ["todos los providers LLM desbloqueados", "usa /v8 para ver el estado"]
                return ["LLMEngine no disponible"]
            elif cmd == "/filtro":
                return await self._admin_show_filter_status()
            elif cmd.startswith("/filtro "):
                level_str = cmd.split("/filtro ", 1)[1].strip()
                return await self._admin_set_filter_level(level_str)

            # ── Conversaciones y feedback ──────────────────────────────────
            elif cmd == "/chats":
                return await self._admin_show_chats()
            elif cmd.startswith("/chat "):
                # /chat 1234567890  → ver conversación de ese chat_id
                patient_id = cmd.split("/chat ", 1)[1].strip()
                return await self._admin_show_patient_chat(patient_id)
            elif cmd == "/reglas":
                return await self._admin_show_trust_rules()
            elif cmd.startswith("/borrar regla "):
                rule_id_str = cmd.split("/borrar regla ", 1)[1].strip()
                if rule_id_str.isdigit():
                    db.delete_trust_rule(int(rule_id_str))
                    return ["Regla eliminada."]
                return ["Formato: /borrar regla [número]"]

            # ── Activacion y tokens ───────────────────────────────────────
            elif cmd == "/token" or cmd.startswith("/token "):
                label = cmd.split("/token", 1)[1].strip() if " " in cmd else ""
                if not label:
                    label = clinic.get("name") or "Mi Negocio"
                new_token = generate_activation_token(label)
                expires_at = (datetime.now() + timedelta(hours=Config.TOKEN_EXPIRY_HOURS)).isoformat()
                saved = db.create_activation_token(new_token, label, expires_at)
                if saved:
                    return [
                        f"Token generado para: {label}",
                        f"{new_token}",
                        f"Expira en {Config.TOKEN_EXPIRY_HOURS}h. Enviaselo al administrador."
                    ]
                return ["No pude generar el token. Intenta de nuevo."]

            elif cmd == "/activar":
                clinic_name = clinic.get("name") or ""
                if not clinic_name:
                    db.update_clinic(setup_step="idle")
                    return ["Para activar primero dime el nombre de tu negocio."]
                db.update_clinic(setup_done=1)
                admin_ids = _parse_admin_ids(clinic.get("admin_chat_ids", []))
                if chat_id not in admin_ids:
                    admin_ids.append(chat_id)
                    db.update_clinic(admin_chat_ids=json.dumps(admin_ids))
                return [
                    f"Instancia activada.",
                    f"Negocio: {clinic_name}",
                    "Ya puedo atender pacientes. Escribe /config para ver la configuracion."
                ]

            elif cmd == "/bridge":
                # Estado del WhatsApp bridge
                if not Config.WHATSAPP_BRIDGE_URL:
                    return ["WHATSAPP_BRIDGE_URL no configurada."]
                try:
                    async with httpx.AsyncClient(timeout=5.0) as hx:
                        r = await hx.get(f"{Config.WHATSAPP_BRIDGE_URL}/status")
                        data = r.json()
                    status = data.get("status", "?")
                    phone = data.get("phoneNumber", "no vinculado")
                    return [
                        f"Bridge WhatsApp: {status}",
                        f"Numero: {phone}",
                        f"Puerto: {Config.WHATSAPP_BRIDGE_URL}"
                    ]
                except Exception as e:
                    return [f"Bridge no responde: {e}"]

            elif cmd.startswith("/"):
                return [
                    "Comandos disponibles:\n\n"
                    "Atención:\n"
                    "/citas — citas pendientes\n"
                    "/chats — conversaciones de pacientes\n"
                    "/chat [id] — conversación completa\n"
                    "/reglas — reglas aprendidas\n"
                    "/broadcast [msg] — mensaje masivo\n\n"
                    "Configuración:\n"
                    "/config — configuración completa\n"
                    "/sector — ver/cambiar sector\n"
                    "/brand — vault de marca y documentos\n"
                    "/personalidad — ajustar personalidad\n"
                    "/control — control duro de frases, saludo y trato\n"
                    "/gateway — gateway automático de skills/reglas\n"
                    "/whatsapp — conectar WhatsApp\n"
                    "/bridge — estado del bridge WhatsApp\n"
                    "/agenda — calendario\n"
                    "/nova — gobernanza\n"
                    "/metricas — métricas\n\n"
                    "V8.0 — Modelo & Calidad:\n"
                    "/modelo — ver modelo activo y cambiarlo\n"
                    "/modelo [alias] — cambiar modelo (ej: claude-sonnet, gemini-flash)\n"
                    "/modelo reset — volver al modelo del .env\n"
                    "/v8 — estado de los sistemas V8\n"
                    "/filtro [1|2|3] — nivel del filtro anti-robot\n\n"
                    "Activación:\n"
                    "/activar — activar esta instancia\n"
                    "/token [nombre] — generar código de activación\n\n"
                    "Inteligencia:\n"
                    "/pipeline — leads por temperatura\n"
                    "/perdidos — análisis de abandono\n"
                    "/coach — feedback de ventas\n"
                    "/reactivar — reactivar inactivos\n"
                    "/reporte — reporte inmediato\n\n"
                    "O escribe en lenguaje natural."
                ]

            # ── Feedback sobre conversación revisada ──────────────────────
            feedback_result = await self._process_admin_feedback(chat_id, text, clinic)
            if feedback_result is not None:
                return feedback_result

            # ── Flujo activo de configuración WhatsApp ─────────────────────
            wa_result = await self._handle_whatsapp_setup_flow(chat_id, text, clinic)
            if wa_result is not None:
                return wa_result

            # Lenguaje natural
            return await self._admin_natural_command(chat_id, text, clinic)

        except Exception as e:
            log.error(f"Admin handler error: {e}", exc_info=True)
            return ["algo salió mal, intenta de nuevo"]
    
    async def _handle_setup(self, chat_id: str, text: str, clinic: Dict) -> List[str]:
        """
        Setup inteligente con autodiscovery.
        Cuando el admin escribe el nombre, buscamos la clinica en Google
        y pre-llenamos todo. Si se encuentra, solo confirman. Si no, 5 pasos rapidos.
        """

        setup_step   = clinic.get("setup_step", "idle")
        setup_buffer = clinic.get("setup_buffer", {})
        if isinstance(setup_buffer, str):
            setup_buffer = json.loads(setup_buffer) if setup_buffer else {}

        step_names = ["name", "tagline", "services", "schedule", "phone", "pricing"]

        # ── Inicio ─────────────────────────────────────────────────────────────
        if setup_step == "idle":
            admin_name_greeting = ""
            try:
                rec = db.get_admin(chat_id) if db else None
                if rec and rec.get("name") and rec["name"] not in ("", "Admin"):
                    admin_name_greeting = f" Hola, {rec['name']}."
            except Exception:
                pass
            db.update_clinic(setup_step="name")
            return [
                f"¡Hola!{admin_name_greeting} Vamos a dejarme lista para tu negocio.",
                "¿Cómo se llama tu clínica o negocio?"
            ]

        # ── Confirmar datos descubiertos en web ─────────────────────────────────
        if setup_step == "confirm_discovered":
            text_low = text.lower().strip()
            if text_low in ["si", "sip", "sep", "dale", "correcto", "ok", "yes", "listo", "claro"]:
                # Aplicar todo lo descubierto
                discovered = setup_buffer.get("discovered", {})
                db.update_clinic(
                    name=discovered.get("name", setup_buffer.get("name", "Mi Clinica")),
                    tagline=discovered.get("tagline", ""),
                    services=discovered.get("services", []),
                    schedule=discovered.get("schedule", {}),
                    phone=discovered.get("phone", ""),
                    address=discovered.get("address", ""),
                    setup_done=1,
                    setup_step="idle",
                    setup_buffer={}
                )
                name = discovered.get("name", "tu clinica")
                svcs = ", ".join(discovered.get("services", [])) or "sin definir"
                return [
                    f"Listo. Quede configurada para {name}.",
                    f"Servicios: {svcs}.\n\nDesde ahora me encargo de tus pacientes.\nComandos: /citas | /config | /metricas | /personalidad"
                ]
            else:
                # No confirmo, ir a setup manual desde donde quedamos
                db.update_clinic(setup_step="tagline", setup_buffer=setup_buffer)
                return [
                    "Sin problema, vamos a completar esto manualmente.",
                    "Tienes un slogan o descripcion corta? Si no, escribe 'no'."
                ]

        if setup_step not in step_names:
            db.update_clinic(setup_step="idle", setup_buffer={})
            return ["Algo salio mal. Escribe /setup para comenzar de nuevo."]

        idx = step_names.index(setup_step)

        # ── Procesar respuesta ─────────────────────────────────────────────────
        if setup_step == "services":
            raw_svcs = [s.strip() for s in text.split(",") if s.strip()]
            # Validar: si parece una URL, un comando, o una sola frase larga -> rechazar
            is_garbage = (
                len(raw_svcs) == 1 and (
                    len(raw_svcs[0]) > 50 or
                    any(kw in raw_svcs[0].lower() for kw in [
                        "google", "busca", "http", "www", ".com", "facebook",
                        "instagram", "busqueda", "encuentra"
                    ])
                )
            )
            if is_garbage:
                return [
                    "Eso no parece una lista de servicios.",
                    "Escribelos separados por coma:\nEj: Botox, Rellenos, Limpieza facial, Laser CO2, Radiofrecuencia"
                ]
            setup_buffer["services"] = [s.title() for s in raw_svcs]
        elif setup_step == "tagline":
            setup_buffer["tagline"] = "" if text.lower().strip() in ["no", "n", "-", "ninguno"] else text.strip()
        elif setup_step == "schedule":
            setup_buffer["schedule"] = {"General": text.strip()}
        elif setup_step == "pricing":
            # Parsear precios libres: "Botox: 350.000, Rellenos: 500.000" o texto libre
            pricing_dict = {}
            text_low_p = text.lower().strip()
            if text_low_p not in ["no", "n", "-", "ninguno", "despues", "luego"]:
                for line in re.split(r'[,\n;]+', text):
                    line = line.strip()
                    if ':' in line:
                        parts = line.split(':', 1)
                        svc = parts[0].strip()
                        price = parts[1].strip()
                        if svc and price:
                            pricing_dict[svc] = price
                    elif '-' in line:
                        parts = line.split('-', 1)
                        svc = parts[0].strip()
                        price = parts[1].strip()
                        if svc and price:
                            pricing_dict[svc] = price
            setup_buffer["pricing"] = pricing_dict
        else:
            setup_buffer[setup_step] = text.strip()

        # ── Si acaba de darnos el nombre, buscar en Google ─────────────────────
        if setup_step == "name":
            clinic_name = text.strip()
            discovered  = await self._discover_clinic_from_web(clinic_name)

            if discovered and discovered.get("confidence", 0) >= 0.5:
                # Guardamos todo en buffer
                setup_buffer["discovered"] = discovered
                setup_buffer["name"] = clinic_name

                svcs  = ", ".join(discovered.get("services", [])) or "no encontre servicios"
                phone = discovered.get("phone", "")
                sched = discovered.get("schedule_text", "")
                addr  = discovered.get("address", "")

                summary_parts = [f"Servicios: {svcs}"]
                if sched:
                    summary_parts.append(f"Horario: {sched}")
                if phone:
                    summary_parts.append(f"Tel: {phone}")
                if addr:
                    summary_parts.append(f"Direccion: {addr}")
                summary = ". ".join(summary_parts)

                db.update_clinic(
                    setup_step="confirm_discovered",
                    setup_buffer=setup_buffer
                )
                return [
                    f"Encontre info de {clinic_name} en internet.",
                    f"{summary}.\n\nConfirmas estos datos? (si / no)"
                ]
            else:
                # No encontre nada, seguir con setup normal
                db.update_clinic(
                    setup_step=step_names[1],
                    setup_buffer=setup_buffer
                )
                return self._setup_next_bubbles("name", text.strip(), "tagline", setup_buffer)

        # ── Siguiente paso normal ──────────────────────────────────────────────
        if idx + 1 < len(step_names):
            next_step = step_names[idx + 1]
            db.update_clinic(setup_step=next_step, setup_buffer=setup_buffer)
            return self._setup_next_bubbles(setup_step, text.strip(), next_step, setup_buffer)

        # ── Finalizar setup ───────────────────────────────────────────────────
        db.update_clinic(
            name=setup_buffer.get("name", "Mi Clinica"),
            tagline=setup_buffer.get("tagline", ""),
            services=setup_buffer.get("services", []),
            schedule=setup_buffer.get("schedule", {}),
            phone=setup_buffer.get("phone", ""),
            pricing=setup_buffer.get("pricing", {}),
            setup_done=1,
            setup_step="idle",
            setup_buffer={}
        )
        name = setup_buffer.get("name", "tu clinica")
        svcs = ", ".join(setup_buffer.get("services", [])) or "sin definir"
        pricing_count = len(setup_buffer.get("pricing", {}))
        pricing_note  = f" con {pricing_count} precios cargados" if pricing_count else ""

        # Guardar identidad en memoria permanente
        db.remember("clinic_name",     name,                               "identity")
        db.remember("clinic_services", ", ".join(setup_buffer.get("services", [])), "clinic")
        db.remember("clinic_phone",    setup_buffer.get("phone", ""),     "clinic")
        db.remember("platform",        Config.PLATFORM,                    "identity")
        db.remember("setup_completed", "true",                             "identity")

        # Notificar a Omni que esta instancia quedó configurada
        asyncio.create_task(asyncio.to_thread(
            notify_omni, "setup_completado",
            f"Nueva instancia configurada: {name} (sector: {Config.SECTOR})", name
        ))

        # Guía de siguiente paso — WhatsApp si aún no está conectado
        whatsapp_connected = db.recall("whatsapp_connected") == "true"

        if whatsapp_connected:
            next_step = (
                "\n\nYa tienes WhatsApp conectado. Listo para recibir pacientes."
            )
        else:
            next_step = (
                "\n\nSiguiente paso — conectar WhatsApp:\n"
                "Pégame aquí tu Phone Number ID y Access Token de Meta Business.\n"
                "Formato:\n"
                "  WA_PHONE_ID: 123456789012345\n"
                "  WA_TOKEN: EAAxxxxx...\n\n"
                "Si aun no los tienes, escribe /whatsapp y te explico cómo obtenerlos."
            )

        kb_invite = (
            "\n\nTambién puedes enviarme un documento con toda la info de tu clinica "
            "(precios detallados, protocolos, FAQs) y lo aprendo todo de una vez."
        ) if _KB_AVAILABLE else ""

        return [
            f"¡Listo! Soy {name}.{pricing_note}",
            f"Servicios: {svcs}.{next_step}{kb_invite}",
            "Estoy aquí cuando llegue tu primer paciente. Cuéntame más sobre cómo te gusta que les hable y yo aprendo.",
        ]

    async def _discover_clinic_from_web(self, clinic_name: str, city: str = "Medellin") -> Dict:
        """
        Busca la clinica en Google y extrae info estructurada via LLM.
        V9 Upgrade: Timeout robusto y protección contra cuelgues.
        """
        try:
            # ── Paso 1: Búsqueda Web con Timeout ──────────────────────────────
            search_query = f"{clinic_name} {city} servicios precios horario telefono"
            log.info(f"[autodiscovery] buscando: {search_query}")

            try:
                # Timeout de 15s para la búsqueda
                snippets = await asyncio.wait_for(
                    self.search.search(search_query, context=""),
                    timeout=15.0
                )
            except asyncio.TimeoutError:
                log.warning(f"[autodiscovery] búsqueda expiró para {clinic_name}")
                return {}
            except Exception as se:
                log.warning(f"[autodiscovery] error en búsqueda: {se}")
                return {}

            if not snippets:
                log.info(f"[autodiscovery] no se encontro info de {clinic_name}")
                return {}

            # Usar LLM para extraer datos estructurados
            extraction_prompt = f"""Extrae informacion estructurada de esta clinica estetica a partir de los snippets de busqueda.

NOMBRE DE LA CLINICA: {clinic_name}
CIUDAD: {city}

SNIPPETS DE BUSQUEDA:
{snippets[:1200]}

Extrae y retorna SOLO un JSON valido con esta estructura exacta:
{{
  "name": "nombre oficial de la clinica",
  "tagline": "descripcion corta o slogan si hay",
  "services": ["servicio 1", "servicio 2", ...],
  "schedule": {{"Lunes a Viernes": "9am-6pm", "Sabados": "9am-2pm"}},
  "schedule_text": "texto resumido del horario",
  "phone": "telefono si aparece",
  "address": "direccion si aparece",
  "confidence": 0.0
}}

confidence: 0.0 si no encontraste nada relevante, 0.5 si encontraste algo, 0.9 si encontraste bastante.
Si un campo no aplica o no se encontro, usa "" o []. Solo JSON, sin texto extra."""

            try:
                # Timeout de 20s para el LLM
                response, _ = await asyncio.wait_for(
                    llm_engine.complete(
                        [{"role": "user", "content": extraction_prompt}],
                        model_tier="fast",
                        temperature=0.1,
                        max_tokens=600,
                        use_cache=False
                    ),
                    timeout=20.0
                )
            except asyncio.TimeoutError:
                log.warning(f"[autodiscovery] LLM expiró para {clinic_name}")
                return {}

            # Limpiar y parsear
            clean = response.strip()
            clean = re.sub(r'^```json\s*', '', clean)
            clean = re.sub(r'\s*```$', '', clean)

            data = json.loads(clean)
            log.info(f"[autodiscovery] encontrado con confidence={data.get('confidence', 0)}: {data.get('name', '')}")
            return data

        except Exception as e:
            log.warning(f"[autodiscovery] error critico: {e}")
            return {}

    def _setup_next_bubbles(self, completed_step: str, value: str,
                            next_step: str, buffer: Dict) -> List[str]:
        """Genera transicion natural entre pasos. Acuse breve + pregunta."""
        ack = self._setup_ack(completed_step, value, buffer)

        questions = {
            "tagline":  "Tienes un slogan o descripcion corta? Si no, escribe 'no'.",
            "services": "Que servicios ofreces?\nEscribelos separados por coma. Ej: Botox, Rellenos, Limpieza facial",
            "schedule": "Cual es el horario de atencion?\nEj: Lunes a viernes 9am-6pm, Sabados 9am-2pm",
            "phone":    "Y el telefono de la clinica?",
            "pricing":  "Tienes precios para tus servicios? (opcionales, ayudan a informar mejor al paciente)\n\nFormato: Servicio: precio\nEj: Botox: 350.000, Rellenos: 500.000\n\nSi no, escribe 'no'.",
        }

        question = questions.get(next_step, "")

        if ack and question:
            return [ack, question]
        if question:
            return [question]
        return [ack] if ack else ["Siguiente."]

    def _setup_ack(self, step: str, value: str, buffer: Dict) -> str:
        """Acuse corto y natural. Maximo 1 oracion."""
        if step == "name":
            clean = value.strip().title() if value else "Listo"
            return f"{clean}, perfecto."
        elif step == "tagline":
            low = value.lower().strip()
            if not value or low in ["no", "n", "-", "ninguno", "ninguna"]:
                return "Sin slogan, bien."
            return "Guardado."
        elif step == "services":
            n = len(buffer.get("services", []))
            s = "servicio" if n == 1 else "servicios"
            return f"{n} {s} registrados."
        elif step == "schedule":
            return "Horario guardado."
        elif step == "phone":
            return "Telefono guardado."
        elif step == "pricing":
            low = value.lower().strip()
            if not value or low in ["no", "n", "-", "ninguno"]:
                return "Sin precios por ahora, bien."
            return "Precios guardados."
        return ""




    async def _handle_emergency(self, chat_id: str, text: str,
                                analysis: MessageAnalysis, clinic: Dict) -> List[str]:
        """Maneja emergencias."""
        
        # Notificar a admins
        admin_ids = _parse_admin_ids(clinic.get("admin_chat_ids", []))
        
        for admin_id in admin_ids:
            await mcp_manager.execute(
                "notifications_v1",
                "send_notification",
                {
                    "chat_id": admin_id,
                    "message": f"⚠️ EMERGENCIA detectada:\n\n{text[:200]}\n\nChat: {chat_id}"
                }
            )
        
        phone = clinic.get("phone", "")
        
        return [
            "Entiendo que es urgente.",
            f"Te recomiendo llamar directamente al teléfono: {phone}" if phone else "Por favor contacta a la clínica directamente.",
            "Un profesional te atenderá de inmediato."
        ]
    
    def _extract_actions(self, response: str, chat_id: str, 
                        clinic: Dict) -> Tuple[str, List[Dict]]:
        """Extrae y procesa acciones del response."""
        actions = []
        clean = response
        
        # Extraer nombre del paciente
        if "NOMBRE:" in clean:
            parts = clean.split("NOMBRE:", 1)
            clean = parts[0].strip()
            try:
                raw = parts[1].strip().split("\n")[0]
                data = json.loads(raw)
                if data.get("name"):
                    db.update_patient(chat_id, name=data["name"])
                    actions.append({"type": "name_extracted", "name": data["name"]})
            except Exception:
                pass
        
        # Extraer cita
        if "CITA:" in clean:
            parts = clean.split("CITA:", 1)
            clean = parts[0].strip()
            try:
                raw = parts[1].strip().split("\n")[0]
                data = json.loads(raw)
                apt_id = db.save_appointment(chat_id, data)
                actions.append({"type": "appointment_created", "id": apt_id, "data": data})
                
                # Notificar admin
                admin_ids = _parse_admin_ids(clinic.get("admin_chat_ids", []))
                
                for admin_id in admin_ids:
                    asyncio.create_task(self._notify_admin_appointment(admin_id, data))
                
                # Procesar Pasarela de Pagos (Stripe / Bold)
                from src.core.globals import payment_bridge, calendar_bridge
                deposit = payment_bridge.get_deposit_amount(data.get("service", ""))
                
                if deposit > 0:
                    db.update_appointment(apt_id, status="pendiente_pago")
                    
                    async def _process_payment_flow():
                        try:
                            pay_url = await payment_bridge.create_payment_link(
                                appointment_id=apt_id,
                                service=data.get("service", ""),
                                amount=deposit,
                                chat_id=chat_id
                            )
                            if pay_url:
                                db.update_appointment(apt_id, notes=f"{data.get('notes', '')}\n[Link de Pago]: {pay_url}".strip())
                                # Enviar link de pago al paciente
                                formatted_msg = (
                                    f"Para confirmar tu cita de {data.get('service', '')}, "
                                    f"por favor realiza el pago del abono de {deposit:,} COP ingresando a este enlace: {pay_url}"
                                )
                                await self._send_message(chat_id, formatted_msg)
                        except Exception as _pay_err:
                            log.error(f"[payments] Error procesando flujo de pago: {_pay_err}")
                            
                    asyncio.create_task(_process_payment_flow())

                # Sincronizar con Google Calendar si está configurado
                if calendar_bridge and calendar_bridge.has_google_calendar():
                    async def _sync_to_gcal():
                        try:
                            p_name = data.get("patient_name") or "Paciente"
                            p_phone = data.get("patient_phone") or chat_id.split("@")[0]
                            svc = data.get("service") or "Servicio"
                            dt_slot = data.get("datetime_slot")
                            
                            notes_field = data.get("notes", "")
                            if deposit > 0:
                                notes_field = f"[PENDIENTE DE PAGO - Abono: {deposit:,} COP]\n{notes_field}".strip()
                                
                            if dt_slot:
                                evt_id = await calendar_bridge.create_event(
                                    patient_name=p_name,
                                    phone=p_phone,
                                    service=svc,
                                    date_time=dt_slot,
                                    notes=notes_field
                                )
                                if evt_id:
                                    db.update_appointment(apt_id, google_event_id=evt_id)
                                    log.info(f"[calendar] Cita {apt_id} vinculada exitosamente con evento Google {evt_id}")
                        except Exception as _sync_err:
                            log.warning(f"[calendar] Error sincronizando cita con Google Calendar: {_sync_err}")
                    asyncio.create_task(_sync_to_gcal())

                # Programar recordatorio
                if data.get("datetime_slot"):
                    try:
                        apt_time = datetime.fromisoformat(data["datetime_slot"])
                        reminder_time = apt_time - timedelta(hours=24)
                        if reminder_time > datetime.now():
                            task_manager.schedule_task(
                                "reminder",
                                {
                                    "chat_id": chat_id,
                                    "message": f"Recordatorio: Mañana tienes cita para {data.get('service', 'tu servicio')} a las {apt_time.strftime('%H:%M')}.",
                                    "appointment_id": apt_id
                                },
                                scheduled_for=reminder_time
                            )
                    except Exception:
                        pass
            except Exception as e:
                log.warning(f"Appointment extraction error: {e}")
        
        return clean, actions
    
    async def _notify_admin_appointment(self, admin_id: str, data: Dict):
        """Notifica al admin de nueva cita."""
        nombre = data.get("patient_name", "Paciente")
        msg = (
            f"*Nueva cita agendada*\n\n"
            f"Paciente: {nombre}\n"
            f"Servicio: {data.get('service', '-')}\n"
            f"Fecha/hora: {data.get('datetime_slot', '-')}\n"
            f"Teléfono: {data.get('patient_phone', '-')}"
        )
        
        await mcp_manager.execute(
            "notifications_v1",
            "send_notification",
            {"chat_id": admin_id, "message": msg}
        )
    
    def _split_bubbles(self, text: str, chat_id: str = "",
                       archetype: str = "amigable") -> List[str]:
        """
        Divide respuesta en burbujas separadas.
        Respeta separador explicito |||.
        Para textos sin separador, aplica logica de longitud.
        V8: aplica AntiRobotFilter a cada burbuja antes de retornar.
        Siempre limpia ¿ y ¡ de cada burbuja.
        v12: el umbral de corte varía un poco en vez de ser siempre 140 fijo
        — con umbral fijo, muchos mensajes seguidos se sienten cortados
        siempre en el mismo patrón (mecánico). Además, una oración muy larga
        sin punto interno ahora se puede partir por un conector fuerte
        (", pero", ", así que"...) en vez de quedar como un bloque único.
        """
        import random as _rnd

        def clean(s: str) -> str:
            s = s.replace('¿', '').replace('¡', '').strip()
            # Triple exclamación → suena bot
            import re as _re2
            s = _re2.sub(r'!{2,}', '!', s)
            # Delimitadores rotos sobrantes ("||" huérfanos) → limpiar
            s = _re2.sub(r'\s*\|{1,2}\s*$', '', s)
            s = _re2.sub(r'\s+\|{1,2}\s+', ' ', s)
            # Punto + exclamación (contradicción tipográfica)
            s = s.replace('.!', '.').replace('!.', '.')
            # V8: aplicar AntiRobotFilter
            if anti_robot_filter:
                s = anti_robot_filter.process(s, archetype)
            return s
        
        # Por separador explícito (el LLM lo agrega cuando quiere 2 mensajes)
        if "|||" in text:
            parts = [clean(p) for p in text.split("|||") if p.strip()]
            # v11: descartar burbujas que solo tienen puntuación o son conector solo
            parts = [p for p in parts if p and re.search(r'\w', p) and len(p.strip()) > 2]
            return parts[:12]  # V6: permite presentaciones largas
        
        # Mensaje corto -> una sola burbuja
        if len(text) <= 130:
            c = clean(text)
            # v11: descartar si es solo puntuación (ej: resultado de una frase eliminada)
            return [c] if c and re.search(r'\w', c) else []
        
        # Partir por oraciones completas
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÜÑA-Za-z¿])', text)
        # v11: descartar fragmentos de solo puntuación
        sentences = [clean(s) for s in sentences if s.strip() and re.search(r'\w', s)]
        
        if len(sentences) <= 1:
            return [clean(text)]

        # v12: umbral variable (no siempre el mismo corte exacto)
        _bucket_limit = _rnd.randint(100, 155)

        # Agrupar oraciones en burbujas de ~100-155 chars max
        bubbles, bucket = [], ""
        for s in sentences:
            if not s:
                continue
            # v12: oración muy larga sin punto interno -> intenta partir por
            # un conector fuerte antes de meterla entera en una sola burbuja
            candidates = [s]
            if len(s) > 170:
                sub_parts = re.split(r',\s+(?=pero\b|así que\b|aunque\b|y eso\b|entonces\b|osea\b)', s)
                if len(sub_parts) > 1:
                    candidates = sub_parts
            for c_part in candidates:
                c_part = c_part.strip()
                if not c_part:
                    continue
                if len(bucket) + len(c_part) < _bucket_limit or not bucket:
                    bucket = (bucket + " " + c_part).strip() if bucket else c_part
                else:
                    bubbles.append(bucket)
                    bucket = c_part
        if bucket:
            bubbles.append(bucket)
        
        return bubbles[:4]
    
    # ─── Admin Commands ─────────────────────────────────────────────────────────
    
    async def _admin_show_appointments(self) -> List[str]:
        """Muestra citas."""
        appointments = db.get_appointments(status="pendiente", limit=15)
        
        if not appointments:
            return ["Sin citas pendientes."]
        
        lines = ["*Citas pendientes:*\n"]
        for apt in appointments:
            lines.append(
                f"• *{apt['patient_name']}* | {apt['service']} | "
                f"{apt['datetime_slot']} | {apt['status']}"
            )
        
        return ["\n".join(lines)]
    
    async def _admin_show_config(self, clinic: Dict) -> List[str]:
        """Muestra configuracion actual con hints de como editar."""
        services = clinic.get("services", [])
        schedule = clinic.get("schedule", {})
        pricing  = clinic.get("pricing", {})
        if isinstance(pricing, str):
            try:
                pricing = json.loads(pricing) if pricing else {}
            except Exception:
                pricing = {}

        persona = clinic.get("persona_config", {})
        if isinstance(persona, str):
            try:
                persona = json.loads(persona) if persona else {}
            except Exception:
                persona = {}

        agent_name = persona.get("name", "Bublee")
        formality  = int(persona.get("formality_level", 0.6) * 100)
        warmth     = int(persona.get("warmth_level", 0.7) * 100)

        svcs_str  = "\n  ".join(services) if services else "ninguno (di 'cambia los servicios')"
        sched_str = "; ".join(f"{k}: {v}" for k, v in schedule.items()) if schedule else "no configurado"

        price_block = ""
        if pricing:
            price_lines = "\n  ".join(f"{k}: {v}" for k, v in pricing.items())
            price_block = f"Precios:\n  {price_lines}\n"
        else:
            price_block = "Precios: no configurados\n"

        kb_line = ""
        if kb and _KB_AVAILABLE and kb.has_content():
            stats = kb.get_stats()
            kb_line = f"KB: {stats['chunks']} secciones · {stats['words']} palabras\n"
        else:
            kb_line = "KB: sin documento cargado\n"

        brand_line = ""
        try:
            store = self._brand_store(clinic)
            if store:
                manifest = store.manifest()
                brand_line = f"Brand Vault: {len(manifest.get('assets', []))} activos · {store.root}\n"
        except Exception:
            brand_line = ""

        return [
            f"CLINICA:\n"
            f"  Nombre: {clinic.get('name', '-')}\n"
            f"  Slogan: {clinic.get('tagline', '-') or '-'}\n"
            f"  Direccion: {clinic.get('address', '-') or '-'}\n"
            f"  Telefono: {clinic.get('phone', '-') or '-'}\n"
            f"  Horario: {sched_str}\n\n"
            f"SERVICIOS:\n  {svcs_str}\n\n"
            f"{price_block}\n"
            f"ASISTENTE:\n"
            f"  Nombre: {agent_name}\n"
            f"  Calidez: {warmth}% · Formalidad: {formality}%\n\n"
            f"{kb_line}"
            f"{brand_line}",
            "Para editar, dime:\n"
            "• 'cambia los servicios'\n"
            "• 'el telefono es 3001234567'\n"
            "• 'la direccion es Calle 10 #43'\n"
            "• 'el botox cuesta 350.000'\n"
            "• 'mas calidez' / 'llamate Sofia'\n"
            "• Enviar documento completo -> carga el KB\n"
            "• Enviar logo/manual/identidad -> queda en el Brand Vault"
        ]
    
    async def _admin_show_metrics(self) -> List[str]:
        """Muestra métricas."""
        analysis = await self.self_improvement.analyze_performance()
        
        return [
            f"*Métricas (últimas 24h):*\n\n"
            f"Conversaciones: {analysis.get('total_conversations', 0)}\n"
            f"Tiempo respuesta: {analysis.get('avg_response_time_ms', 0):.0f}ms\n"
            f"Turnos promedio: {analysis.get('avg_turns_per_conversation', 0):.1f}\n"
            f"Tasa conversión: {analysis.get('conversion_rate', 0)*100:.1f}%\n"
            f"Escalaciones: {analysis.get('escalation_rate', 0)*100:.1f}%"
        ]
    
    async def _admin_show_plugins(self) -> List[str]:
        """Muestra plugins."""
        plugins = db.get_plugins()
        
        if not plugins:
            return ["Sin plugins instalados."]
        
        lines = ["*Plugins instalados:*\n"]
        for p in plugins:
            status = "✓" if p.enabled else "✗"
            lines.append(f"{status} *{p.name}* v{p.version}")
            lines.append(f"   Capacidades: {', '.join(p.capabilities)}")
        
        return ["\n".join(lines)]
    
    async def _admin_show_personality(self, clinic: Dict) -> List[str]:
        """Muestra la personalidad actual con arquetipos disponibles."""
        persona = clinic.get("persona_config", {})
        if isinstance(persona, str):
            try:
                persona = json.loads(persona) if persona else {}
            except Exception:
                persona = {}

        name        = persona.get("name", "Bublee")
        archetype   = persona.get("archetype", "amigable")
        arch_info   = PERSONALITY_ARCHETYPES.get(archetype, PERSONALITY_ARCHETYPES["amigable"])

        arch_list = "\n".join(
            f"  {k} — {v['desc']}"
            for k, v in PERSONALITY_ARCHETYPES.items()
        )

        return [
            f"personalidad activa: {archetype}\n{arch_info['desc']}",
            f"arquetipos disponibles:\n{arch_list}",
            "para cambiar escribe por ejemplo:\n"
            "  'activa empatica'\n"
            "  'cambia a luxury y llamate Sofia'\n"
            "  'modo experta'\n"
            "  'mas calidez' / 'menos formal'\n"
            "  'agrega palabra prohibida: oferta'"
        ]
    
    async def _admin_show_admins(self) -> List[str]:
        """Muestra el equipo de admins de esta instancia."""
        admins = db.list_admins()
        if not admins:
            return ["No hay administradores registrados."]

        lines = ["Equipo de administradores:\n"]
        for a in admins:
            role_label = "Owner" if a["role"] == "owner" else "Admin"
            name  = a.get("name", "Sin nombre")
            email = a.get("email", "")
            lines.append(f"  {role_label}: {name} ({email})")

        lines.append("\nPara agregar un nuevo admin: /addadmin")
        return ["\n".join(lines)]

    # ─── Conversaciones y Feedback ──────────────────────────────────────────────

    async def _admin_show_chats(self) -> List[str]:
        """
        /chats — muestra los últimos pacientes con quienes ha hablado Bublee.
        El admin puede elegir uno para ver la conversación completa.
        """
        chats = db.get_recent_patient_chats(limit=10)
        if not chats:
            return ["Bublee no ha tenido conversaciones con pacientes todavía."]

        lines = ["Últimas conversaciones:\n"]
        for i, c in enumerate(chats, 1):
            name = c.get("name") or "Desconocido"
            last_msg = (c.get("last_user_msg") or "")[:50]
            count = c.get("message_count", 0)
            last_ts = (c.get("last_message") or "")[:16]
            cid = c["chat_id"]
            lines.append(
                f"{i}. {name} ({cid})\n"
                f"   {count} mensajes · {last_ts}\n"
                f"   Último: \"{last_msg}\""
            )

        lines.append(
            "\nPara ver una conversación completa:\n"
            "/chat [id del paciente]\n"
            "Ej: /chat 1234567890\n\n"
            "Para dar feedback sobre una conversación:\n"
            "Escríbeme después de ver la conversación."
        )
        return ["\n".join(lines)]

    async def _admin_show_recent_conversation_browser(self, admin_chat_id: str, limit: int = 6) -> List[str]:
        """
        Vista resumida para admins no técnicos.
        Muestra las últimas conversaciones y deja contexto para abrir una por número.
        """
        raw_chats = db.get_recent_patient_chats(limit=max(limit * 5, 20))
        chats = [
            chat for chat in raw_chats
            if not self._is_synthetic_chat_id(str(chat.get("chat_id") or "").strip())
        ][:limit]
        if not chats:
            return ["Bublee no ha tenido conversaciones con pacientes todavía."]

        self._admin_pending[admin_chat_id] = {
            "action": "conversation_browser",
            "items": chats,
            "selected_chat_id": None,
        }

        lines = [f"Últimas {len(chats)} conversaciones:\n"]
        for idx, chat in enumerate(chats, 1):
            name = (chat.get("name") or "Sin nombre").strip()
            chat_id = str(chat.get("chat_id") or "").strip()
            count = int(chat.get("message_count") or 0)
            last_msg = (chat.get("last_user_msg") or "").strip()
            if len(last_msg) > 60:
                last_msg = last_msg[:57].rstrip() + "..."
            last_ts = str(chat.get("last_message") or "").replace("T", " ")[:16]
            lines.append(
                f"{idx}. {name} ({chat_id})\n"
                f"   {count} mensajes · {last_ts}\n"
                f"   Último: {last_msg or 'sin texto'}"
            )

        lines.extend(
            [
                "",
                "Dime por ejemplo:",
                "  ver 1",
                "  muéstrame la primera",
                "  quiero ver todos los mensajes del primero",
            ]
        )
        return ["\n".join(lines)]

    async def _admin_show_patient_chat_preview(
        self,
        patient_chat_id: str,
        *,
        admin_chat_id: str = "",
        limit: int = 10,
        show_all: bool = False,
        label_override: str = "",
    ) -> List[str]:
        """
        Muestra un preview corto por defecto y la conversación completa si el admin lo pide.
        """
        fetch_limit = 500 if show_all else limit
        msgs = db.get_patient_conversation(patient_chat_id, limit=fetch_limit)
        if not msgs:
            return [f"No encontré conversación para el ID: {patient_chat_id}"]

        patient_name = ""
        try:
            conn_factory = getattr(db, "_conn", None)
            if callable(conn_factory):
                with conn_factory() as c:
                    row = c.execute(
                        "SELECT name FROM patients WHERE chat_id=?",
                        (patient_chat_id,),
                    ).fetchone()
                    if row:
                        patient_name = (row["name"] or "").strip()
        except Exception:
            patient_name = ""

        if admin_chat_id:
            pending = dict(self._admin_pending.get(admin_chat_id, {}))
            pending["action"] = "conversation_browser"
            pending["selected_chat_id"] = patient_chat_id
            self._admin_pending[admin_chat_id] = pending

        self._last_reviewed_chat = patient_chat_id

        label = patient_name or (label_override or "").strip() or patient_chat_id
        visible = msgs if show_all else msgs[-limit:]
        header = (
            f"Conversación completa con {label}"
            if show_all
            else f"Últimos {len(visible)} mensajes con {label}"
        )

        lines = [header, "─" * 40]
        for msg in visible:
            role_label = "Paciente" if msg.get("role") == "user" else "Bublee"
            ts = str(msg.get("ts") or "").replace("T", " ")[:16]
            content = str(msg.get("content") or "").strip()
            lines.append(f"[{ts}] {role_label}: {content}")

        lines.extend(
            [
                "",
                "Si quieres más, dime:",
                "  ver todo",
                "  enséñame todos los mensajes",
            ]
        )
        return ["\n".join(lines)]

    async def _admin_show_patient_chat(self, patient_chat_id: str) -> List[str]:
        """
        /chat [id] — muestra la conversación completa de un paciente.
        Después de verla, el admin puede dar feedback naturalmente.
        """
        msgs = db.get_patient_conversation(patient_chat_id, limit=40)
        if not msgs:
            return [f"No encontré conversación para el ID: {patient_chat_id}"]

        # Guardar contexto activo para feedback
        self._admin_pending[patient_chat_id + "_review"] = {
            "action": "reviewing_chat",
            "patient_chat_id": patient_chat_id,
        }
        # Guardar en el pending del admin también para detectar feedback
        # (keyed by admin chat_id, set later when feedback is detected)

        patient = None
        try:
            with db._conn() as c:
                row = c.execute("SELECT name FROM patients WHERE chat_id=?",
                                (patient_chat_id,)).fetchone()
                if row:
                    patient = row["name"]
        except Exception:
            pass

        name_str = f"con {patient}" if patient else f"ID: {patient_chat_id}"
        header = f"Conversación {name_str}:\n{'─'*40}"

        lines = [header]
        for m in msgs:
            role_label = "Paciente" if m["role"] == "user" else "Bublee"
            ts = (m.get("ts") or "")[:16]
            content = m["content"][:200]
            lines.append(f"\n[{ts}] {role_label}:\n{content}")

        lines.append(
            f"\n{'─'*40}\n"
            "Opciones:\n\n"
            "PUENTE — enviar mensaje directo a este cliente:\n"
            "  envíale: tu mensaje aquí\n"
            "  mándale: confirmada la cita para el martes\n"
            "  dile: ya tenemos disponibilidad esta semana\n\n"
            "FEEDBACK — enseñarme a mejorar:\n"
            "  \"Cuando dijo que era caro, debió ofrecer el plan de pagos\"\n"
            "  \"Muy bien manejada la objeción del precio\"\n\n"
            "El puente lo envío como si fuera yo — el cliente no nota diferencia."
        )

        # Store which chat the admin was just reviewing
        # (we'll use the admin's own chat_id as key — set when we know it)
        self._last_reviewed_chat = patient_chat_id

        return ["\n".join(lines)]

    async def _admin_show_trust_rules(self) -> List[str]:
        """
        /reglas — muestra lo que Bublee ha aprendido del feedback del admin.
        """
        rules = db.get_trust_rules()
        if not rules:
            return [
                "Todavía no has dado feedback.",
                "Cuando veas una conversación con /chats y me digas cómo mejorarla, lo aprendo y lo guardo acá."
            ]

        # Agrupar por categoría
        by_cat: Dict[str, list] = {}
        for r in rules:
            cat = r.get("category", "general")
            by_cat.setdefault(cat, []).append(r)

        cat_labels = {
            "objection":    "Manejo de objeciones",
            "tone":         "Tono y forma de hablar",
            "closing":      "Cierre y agendamiento",
            "product":      "Información de tratamientos",
            "flow":         "Flujo de conversación",
            "general":      "General",
        }

        lines = ["Lo que he aprendido de ti:\n"]
        for cat, cat_rules in by_cat.items():
            label = cat_labels.get(cat, cat.title())
            lines.append(f"\n{label}:")
            for r in cat_rules:
                lines.append(f"  #{r['id']} {r['rule']}")
                if r.get("example_good"):
                    lines.append(f"     Ej: \"{r['example_good']}\"")

        lines.append(
            "\n\nPara eliminar una regla:\n"
            "/borrar regla [número]\n"
            "Ej: /borrar regla 3"
        )
        return ["\n".join(lines)]

    async def _process_admin_feedback(self, chat_id: str, text: str,
                                      clinic: Dict) -> Optional[List[str]]:
        """
        Detecta si el admin está:
        A) Dando feedback sobre una conversación revisada
        B) Respondiendo a la pregunta de disponibilidad que Bublee le hizo
        C) Usando el puente — enviando un mensaje directo a un paciente activo
        """
        text_low = text.lower().strip()

        # ── C. PUENTE — admin envía mensaje directo a un paciente ────────────────
        # Patrones detectados:
        #   "envíale: hola, ¿cómo estás?"
        #   "mándale este mensaje: ya podemos atenderte"
        #   "dile a este cliente: confirmada la cita"
        #   "escríbele: te esperamos el martes"
        BRIDGE_PATTERNS = [
            "envíale:", "enviale:", "envíale ", "envialessto",
            "mándale:", "mandale:", "mándale este mensaje:",
            "dile:", "dile a este cliente:", "dile que:",
            "escríbele:", "escribele:", "escríbele este:",
            "envía:", "envia:", "manda:", "pásale:", "pasale:",
            "respóndele:", "respondele:", "contéstale:", "contestale:",
        ]
        reviewed = getattr(self, '_last_reviewed_chat', None)

        _bridge_prefix = next(
            (p for p in BRIDGE_PATTERNS if text_low.startswith(p.lower())),
            None
        )
        # También detectar patrón "envíale [mensaje]" sin dos puntos
        if not _bridge_prefix:
            for p in ["envíale ", "enviále ", "mándale ", "mandale ", "dile ", "escríbele "]:
                if text_low.startswith(p):
                    _bridge_prefix = p
                    break

        if _bridge_prefix and reviewed:
            # Extraer el mensaje que va al paciente
            raw_bridge_msg = text[len(_bridge_prefix):].strip().strip('"').strip("'").strip()

            if raw_bridge_msg:
                try:
                    # Obtener nombre del paciente para el log
                    patient_name = ""
                    try:
                        with db._conn() as c:
                            row = c.execute("SELECT name FROM patients WHERE chat_id=?",
                                            (reviewed,)).fetchone()
                            if row:
                                patient_name = row["name"] or ""
                    except Exception:
                        pass

                    # Enviar el mensaje como si fuera Bublee (no el admin)
                    await self._send_message(reviewed, raw_bridge_msg)

                    # Guardarlo en el historial como si Bublee lo hubiera dicho
                    db.save_message(reviewed, "assistant", raw_bridge_msg)

                    name_str = patient_name or f"cliente {reviewed[-6:]}"
                    log.info(f"[bridge] admin→{reviewed}: {raw_bridge_msg[:60]}")
                    return [
                        f"Listo, le mandé eso a {name_str}",
                        "Mensaje enviado: " + raw_bridge_msg[:120] + ("..." if len(raw_bridge_msg) > 120 else ""),
                        "Quedó guardado en el historial como si lo hubiera dicho Bublee"
                    ]

                except Exception as e:
                    log.error(f"[bridge] error: {e}")
                    return [f"No pude enviar el mensaje: {e}"]
            else:
                return [
                    "No entendí el mensaje a enviar",
                    "Formato: envíale: tu mensaje aquí"
                ]

        elif _bridge_prefix and not reviewed:
            return [
                "Primero abre una conversación con /chat [id]",
                "Así sé a qué cliente enviarle el mensaje"
            ]

        # ── B. Respuesta de disponibilidad del admin ──────────────────────────
        # Bublee le preguntó al admin su disponibilidad; él responde
        AVAILABILITY_RESPONSE_SIGNALS = [
            "lunes", "martes", "miercoles", "miércoles", "jueves", "viernes",
            "sabado", "sábado", "esta semana", "proxima", "próxima",
            "manana", "mañana", "hoy", "pm", "am", "9am", "10am", "11am",
            "disponible", "libre", "puedo", "tengo espacio",
        ]
        is_availability_response = sum(
            1 for s in AVAILABILITY_RESPONSE_SIGNALS if s in text_low
        ) >= 2 and len(text) > 10

        if is_availability_response:
            # Verificar si hay un paciente esperando respuesta de disponibilidad
            pending_patient = getattr(self, '_availability_pending_patient', None)
            if pending_patient:
                # Retransmitir la disponibilidad al paciente
                patient_name = ""
                try:
                    with db._conn() as c:
                        row = c.execute("SELECT name FROM patients WHERE chat_id=?",
                                        (pending_patient,)).fetchone()
                        if row:
                            patient_name = row["name"] or ""
                except Exception:
                    pass

                patient_greeting = f"Hola{f' {patient_name}' if patient_name else ''}! "
                patient_msg = f"{patient_greeting}Ya me confirmaron. {text}"

                try:
                    await self._send_message(pending_patient, patient_msg)
                    self._availability_pending_patient = None
                    return [
                        f"Listo, le acabo de confirmar la disponibilidad al paciente."
                    ]
                except Exception as e:
                    log.warning(f"[calendar] error retransmitiendo: {e}")

        # ── A. Instrucción directa del admin (sin conversación activa) ──────────
        # El admin puede decir "no le digas X", "siempre di Y", "cuando pregunten
        # por precio diles que..." en cualquier momento y se guarda como regla.
        text_low = text.lower().strip()

        DIRECT_RULE_SIGNALS = [
            "no le digas", "no digas", "nunca digas", "nunca le digas",
            "siempre di", "siempre dile", "siempre que", "cuando pregunten",
            "cuando el cliente", "cuando la cliente", "cuando alguien",
            "en vez de decir", "en lugar de", "mejor di", "mejor dile",
            "desde ahora", "de ahora en adelante", "para los clientes",
            "a los pacientes", "no menciones", "evita decir", "evita mencionar",
            "quiero que digas", "quiero que le digas", "diles que",
            "respóndeles", "respondeles", "si te preguntan por",
        ]
        is_direct_rule = any(s in text_low for s in DIRECT_RULE_SIGNALS) and len(text) > 15

        if is_direct_rule and not reviewed:
            # Regla directa — guardar sin contexto de conversación
            try:
                extraction_prompt = f"""El dueño de un negocio está dando una instrucción directa a su asistente virtual Bublee sobre cómo debe comportarse con los clientes.

INSTRUCCIÓN DEL DUEÑO:
"{text}"

Extrae una regla clara y accionable de esta instrucción.
Responde SOLO con JSON válido, sin texto adicional:
{{
  "rule": "la regla en lenguaje claro y directo, como una instrucción para Bublee",
  "example_bad": "cómo NO responder (si se puede inferir del contexto)",
  "example_good": "cómo SÍ responder (si se puede inferir del contexto)",
  "category": "tone|product|closing|objection|flow|general",
  "feedback_type": "instruction",
  "save_as_playbook": true,
  "trigger_text": "cuándo aplica esta instrucción, en lenguaje simple",
  "response_example": "ejemplo exacto de respuesta o secuencia de burbujas usando ||| si aplica",
  "bubble_count": 1
}}

Categorías:
- tone: cómo hablar, palabras a usar o evitar
- product: info sobre servicios o precios
- closing: cómo y cuándo cerrar hacia la cita
- objection: manejo de objeciones
- flow: orden de la conversación
- general: todo lo demás

Usa save_as_playbook=true SOLO si el dueño está enseñando un patrón reusable tipo:
- "si te saludan..."
- "cuando pregunten por..."
- "al inicio responde..."
- "primero di X y luego Y"

Si el dueño dio una forma concreta de responder, trigger_text y response_example son obligatorios.
Si menciona dos mensajes, response_example debe usar ||| entre burbujas."""

                raw, _ = await asyncio.wait_for(
                    llm_engine.complete(
                        [{"role": "user", "content": extraction_prompt}],
                        model_tier="fast", temperature=0.1, max_tokens=250, use_cache=False
                    ),
                    timeout=10.0
                )

                import re as _re
                m = _re.search(r'\{[\s\S]+\}', raw.strip())
                if m:
                    parsed       = json.loads(m.group(0))
                    rule         = parsed.get("rule", "")
                    example_bad  = parsed.get("example_bad", "")
                    example_good = parsed.get("example_good", "")
                    category     = parsed.get("category", "general")
                    save_as_playbook = bool(parsed.get("save_as_playbook"))
                    trigger_text = (parsed.get("trigger_text", "") or "").strip()
                    response_example = (parsed.get("response_example", "") or "").strip()
                    bubble_count = int(parsed.get("bubble_count", 1) or 1)

                    if rule:
                        rule_id = db.save_trust_rule(
                            category=category, rule=rule,
                            example_bad=example_bad, example_good=example_good,
                            weight=2.5,
                        )
                        playbook_id = 0
                        if db and save_as_playbook and trigger_text and response_example:
                            playbook_id = db.save_behavior_playbook(
                                trigger_text=trigger_text,
                                response_example=response_example,
                                category=category,
                                instruction=rule,
                                bubble_count=bubble_count,
                                weight=3.0,
                            )
                        cat_labels = {
                            "objection":"Objeciones","tone":"Tono","closing":"Cierre",
                            "product":"Servicios","flow":"Flujo","general":"General"
                        }
                        ejemplo_line = (f'\nEjemplo correcto: "{example_good}"' if example_good else "")
                        playbook_line = (
                            f'\nPlaybook #{playbook_id}: si pasa "{trigger_text}", responde parecido a "{response_example}"'
                            if playbook_id else ""
                        )
                        return [
                            "Entendido, lo guardo ahora mismo",
                            f'Carpeta de confianza #{rule_id} [{cat_labels.get(category,"General")}]:\n"{rule}"' + ejemplo_line,
                            "Aplico esto en todas las conversaciones desde ya. Ver todas las reglas: /reglas" + playbook_line
                        ]
            except Exception as e:
                log.warning(f"[trust_rule] Error procesando instrucción directa: {e}")
            return None

        # ── B. Feedback sobre conversación revisada ───────────────────────────
        if not reviewed:
            return None

        # Detectar si el texto es feedback (no un comando ni saludo)
        FEEDBACK_SIGNALS = [
            "debió", "deberia", "debería", "tendría", "tenia que", "faltó",
            "falto", "muy bien", "estuvo bien", "estuvo mal", "mal manejado",
            "bien manejado", "mejor si", "en vez de", "en lugar de",
            "cuando el paciente", "cuando la paciente", "hubiera",
            "le faltó", "pudo haber", "hay que", "siempre que",
            "nunca", "siempre", "próxima vez", "la próxima",
        ]
        is_feedback = any(s in text_low for s in FEEDBACK_SIGNALS)

        if not is_feedback and len(text) < 40:
            return None
        if not is_feedback and not any(
            kw in text_low for kw in ["precio", "cita", "objecion", "respuesta",
                                       "bublee", "paciente", "cliente", "cerrar",
                                       "agendar", "tono", "dijo", "respondio", "respondió"]
        ):
            return None

        # Obtener el contexto de la conversación revisada
        context_msgs = db.get_patient_conversation(reviewed, limit=20)
        context_str = "\n".join(
            f"{m['role']}: {m['content'][:100]}"
            for m in context_msgs[-10:]
        )

        # Usar LLM para extraer la regla aprendida
        try:
            extraction_prompt = f"""El dueño de una clínica estética está dando feedback sobre cómo su asistente virtual Bublee manejó una conversación.

CONVERSACIÓN REVISADA (fragmento):
{context_str}

FEEDBACK DEL DUEÑO:
"{text}"

Extrae la regla de comunicación aprendida y devuelve SOLO este JSON:
{{
  "category": "objection|tone|closing|product|flow|general",
  "rule": "regla clara en una oración, tercera persona",
  "example_bad": "ejemplo de lo que NO hacer (opcional, máx 60 chars)",
  "example_good": "ejemplo de lo que SÍ hacer (opcional, máx 60 chars)",
  "feedback_type": "correction|praise|instruction"
}}

Ejemplos de categorías:
- objection: manejo de "es caro", "lo pienso", "no sé si sirva"
- tone: cómo hablar, qué palabras usar o evitar
- closing: cómo y cuándo agendar la valoración
- product: información sobre tratamientos específicos
- flow: orden de la conversación, cuándo preguntar qué
- general: todo lo demás"""

            raw, _ = await asyncio.wait_for(
                llm_engine.complete(
                    [{"role": "user", "content": extraction_prompt}],
                    model_tier="fast",
                    temperature=0.2,
                    max_tokens=300,
                    use_cache=False
                ),
                timeout=10.0
            )

            raw = raw.strip()
            json_str = None
            import re as _re
            m = _re.search(r'\{[\s\S]+\}', raw)
            if m:
                json_str = m.group(0)

            if not json_str:
                raise ValueError("No JSON found")

            parsed = json.loads(json_str)
            category     = parsed.get("category", "general")
            rule         = parsed.get("rule", "")
            example_bad  = parsed.get("example_bad", "")
            example_good = parsed.get("example_good", "")
            fb_type      = parsed.get("feedback_type", "instruction")

            if not rule:
                raise ValueError("Empty rule")

            # Guardar en trust_folder
            trust_weight = 2.0 if fb_type == "praise" else 3.0
            rule_id = db.save_trust_rule(
                category=category,
                rule=rule,
                example_bad=example_bad,
                example_good=example_good,
                weight=trust_weight,
            )

            # Guardar el feedback también
            db.save_feedback(
                patient_chat_id=reviewed,
                feedback_text=text,
                feedback_type=fb_type,
                context=context_str,
                admin_chat_id=chat_id
            )

            # Limpiar la conversación bajo revisión
            self._last_reviewed_chat = None

            cat_labels = {
                "objection": "Objeciones", "tone": "Tono", "closing": "Cierre",
                "product": "Tratamientos", "flow": "Flujo", "general": "General"
            }
            cat_label = cat_labels.get(category, "General")

            if fb_type == "praise":
                return [
                    f"Gracias, guardado como referencia de lo que funciona bien.",
                    f"Carpeta de confianza #{rule_id} [{cat_label}]:\n\"{rule}\""
                ]
            else:
                return [
                    f"Entendido. Lo aprendo ahora mismo.",
                    f"Carpeta de confianza #{rule_id} [{cat_label}]:\n\"{rule}\""
                    + (f"\nEjemplo: \"{example_good}\"" if example_good else ""),
                    "Desde ahora aplico esto en cada conversación. Para ver todo lo aprendido: /reglas"
                ]

        except Exception as e:
            log.warning(f"[feedback] Error extrayendo regla: {e}")
            # Guardar el feedback en crudo aunque no se extrajo la regla
            try:
                db.save_feedback(
                    patient_chat_id=reviewed,
                    feedback_text=text,
                    feedback_type="instruction",
                    context="",
                    admin_chat_id=chat_id
                )
                self._last_reviewed_chat = None
            except Exception:
                pass
            return [
                "Guardé tu feedback, aunque no pude procesarlo automáticamente.",
                "Puedes ver todo el feedback con /reglas y editarlo desde ahí."
            ]

    async def _restart_setup(self, chat_id: str) -> List[str]:
        """Reinicia el setup."""
        db.update_clinic(
            setup_done=0,
            setup_step="idle",
            setup_buffer={}
        )
        return await self._handle_setup(chat_id, "", db.get_clinic())
    

    # ══════════════════════════════════════════════════════════════════════════
    # V6.0 — COMANDOS NUEVOS
    # ══════════════════════════════════════════════════════════════════════════

    async def _admin_pipeline(self) -> List[str]:
        """
        /pipeline — Muestra todos los leads clasificados por temperatura.
        Usa closing_score almacenado en la última conversación.
        """
        try:
            with db._conn() as c:
                patients = c.execute("""
                    SELECT p.chat_id, p.name, p.visits,
                           (SELECT content FROM conversations
                            WHERE chat_id=p.chat_id AND role='user'
                            ORDER BY created_at DESC LIMIT 1) as last_msg,
                           (SELECT created_at FROM conversations
                            WHERE chat_id=p.chat_id
                            ORDER BY created_at DESC LIMIT 1) as last_seen
                    FROM patients p
                    ORDER BY p.visits DESC LIMIT 50
                """).fetchall()

            boiling, hot, warm, cold = [], [], [], []

            for pt in patients:
                chat_id  = pt["chat_id"]
                name     = pt["name"] or "Desconocido"
                last_msg = (pt["last_msg"] or "")[:60]
                last_seen = (pt["last_seen"] or "")[:16]

                # Calcular closing_score del último mensaje
                if last_msg:
                    analysis = MessageAnalyzer().analyze(last_msg)
                    temp = analysis.lead_temperature
                    score = analysis.closing_score
                else:
                    temp, score = "cold", 0.0

                entry = f"{name} — {last_msg!r:.60} ({last_seen[:10]})"
                if   temp == "boiling": boiling.append(entry)
                elif temp == "hot":     hot.append(entry)
                elif temp == "warm":    warm.append(entry)
                else:                   cold.append(entry)

            lines = ["Pipeline de leads\n"]
            if boiling:
                lines.append(f"Listos para cerrar ({len(boiling)}):")
                lines += [f"  {e}" for e in boiling[:5]]
            if hot:
                lines.append(f"\nCalientes ({len(hot)}):")
                lines += [f"  {e}" for e in hot[:5]]
            if warm:
                lines.append(f"\nTibios ({len(warm)}):")
                lines += [f"  {e}" for e in warm[:5]]
            if cold:
                lines.append(f"\nFríos ({len(cold)}): {len(cold)} contactos")

            if not (boiling or hot or warm or cold):
                return ["No hay conversaciones registradas todavía"]

            return ["\n".join(lines)]

        except Exception as e:
            log.error(f"[pipeline] {e}")
            return [f"Error generando pipeline: {e}"]

    async def _admin_lost_analysis(self) -> List[str]:
        """
        /perdidos — Analiza por qué se pierden los clientes.
        Identifica el patrón exacto donde se cortan las conversaciones.
        """
        try:
            with db._conn() as c:
                # Conversaciones que terminaron sin cita
                convs = c.execute("""
                    SELECT chat_id,
                           GROUP_CONCAT(content || '|||' || role, '~~~') as thread
                    FROM conversations
                    WHERE created_at >= datetime('now', '-30 days')
                    GROUP BY chat_id
                    HAVING COUNT(*) >= 2
                """).fetchall()

            if not convs:
                return ["No hay suficientes conversaciones para analizar todavía"]

            # Analizar con LLM los patrones de pérdida
            sample = []
            for c in convs[:15]:
                msgs = [m.split("|||") for m in c["thread"].split("~~~") if "|||" in m]
                if len(msgs) >= 2:
                    last_user = next((m[0] for m in reversed(msgs) if len(m) > 1 and m[1] == "user"), "")
                    if last_user:
                        sample.append(last_user[:80])

            if not sample:
                return ["No hay suficientes conversaciones para analizar"]

            prompt = f"""Analiza estos últimos mensajes de clientes que dejaron de responder:

{chr(10).join(f"- {s}" for s in sample[:10])}

Identifica:
1. El patrón más común donde se pierden (qué dijeron justo antes de irse)
2. El porcentaje aproximado de cada patrón
3. Qué debería haber respondido Bublee diferente

Responde en máximo 5 líneas, directo, sin introducciones."""

            try:
                r, _ = await asyncio.wait_for(
                    llm_engine.complete(
                        [{"role": "user", "content": prompt}],
                        model_tier="fast", temperature=0.3, max_tokens=300
                    ), timeout=15.0
                )
            except Exception:
                r = "No pude analizar los patrones en este momento"

            return [
                f"Análisis de los últimos 30 días ({len(convs)} conversaciones):",
                r
            ]

        except Exception as e:
            return [f"Error: {e}"]

    async def _admin_sales_coach(self) -> List[str]:
        """
        /coach — Analiza las últimas conversaciones y da feedback de ventas.
        Funciona como entrenador: qué funcionó, qué no, qué mejorar.
        """
        try:
            with db._conn() as c:
                recent = c.execute("""
                    SELECT chat_id,
                           COUNT(*) as turns,
                           MAX(created_at) as last_ts
                    FROM conversations
                    WHERE created_at >= datetime('now', '-7 days')
                    GROUP BY chat_id
                    HAVING turns >= 4
                    ORDER BY last_ts DESC LIMIT 5
                """).fetchall()

            if not recent:
                return ["No hay conversaciones largas esta semana para analizar"]

            # Tomar la conversación más reciente y sustancial
            best = recent[0]
            msgs = db.get_patient_conversation(best["chat_id"], limit=20)
            thread = "\n".join(f"{m['role'].upper()}: {m['content'][:120]}" for m in msgs)

            prompt = f"""Eres un coach de ventas experto en WhatsApp para negocios en Colombia.
Analiza esta conversación de Bublee con un cliente:

{thread[:2000]}

Dame:
1. Una cosa que Bublee hizo MUY bien (con el mensaje exacto que lo demuestra)
2. Una cosa que pudo hacer mejor (con cómo debió responder)
3. Una técnica de venta que debería usar más en este tipo de conversación

Máximo 6 líneas. Directo. Sin introducciones."""

            try:
                r, _ = await asyncio.wait_for(
                    llm_engine.complete(
                        [{"role": "user", "content": prompt}],
                        model_tier="fast", temperature=0.4, max_tokens=350
                    ), timeout=15.0
                )
            except Exception:
                r = "No pude analizar la conversación en este momento"

            return ["Coach de ventas — última semana:", r]

        except Exception as e:
            return [f"Error: {e}"]

    async def _admin_clone_style(self, admin_chat_id: str) -> List[str]:
        """
        /estilo — Lee los mensajes del admin y clona su forma de escribir.
        Guarda el estilo como trust_rule de máxima prioridad.
        """
        try:
            msgs = db.get_history(admin_chat_id, limit=50)
            admin_msgs = [m["content"] for m in msgs if m["role"] == "user" and len(m["content"]) > 10]

            if len(admin_msgs) < 5:
                return [
                    "Necesito más mensajes tuyos para clonar tu estilo",
                    "Escríbeme unos 10 mensajes como si hablaras con un cliente y vuelve a intentar"
                ]

            sample = "\n".join(f"- {m[:80]}" for m in admin_msgs[:15])

            prompt = f"""Analiza estos mensajes de un empresario colombiano:

{sample}

Extrae su estilo de escritura: tono, vocabulario, longitud de mensajes, 
muletillas propias, cómo saluda, cómo cierra, qué palabras usa siempre.
Luego escribe UNA instrucción concisa (máximo 4 líneas) para que Bublee 
escriba EXACTAMENTE como él. Primera persona, directo."""

            try:
                r, _ = await asyncio.wait_for(
                    llm_engine.complete(
                        [{"role": "user", "content": prompt}],
                        model_tier="fast", temperature=0.3, max_tokens=200
                    ), timeout=15.0
                )
                rule = r.strip()
            except Exception:
                return ["No pude analizar tu estilo en este momento, intenta de nuevo"]

            # Guardar como trust_rule de máxima prioridad
            rule_id = db.save_trust_rule(
                category="tone",
                rule=f"ESTILO CLONADO DEL DUEÑO: {rule}",
                example_bad="",
                example_good=""
            )
            # Subir el peso al máximo
            with db._conn() as c:
                c.execute("UPDATE trust_folder SET weight=3.0 WHERE id=?", (rule_id,))

            return [
                "Analicé tus mensajes y cloné tu estilo",
                f"Regla guardada como #tone con prioridad máxima:",
                rule,
                "Desde ahora Bublee escribe como tú. Usa /reglas para verla o editarla"
            ]

        except Exception as e:
            return [f"Error: {e}"]

    async def _admin_reactivate_dormant(self) -> List[str]:
        """
        /reactivar — Encuentra clientes inactivos 60+ días y los reactiva.
        Programa follow-ups automáticos para cada uno.
        """
        try:
            with db._conn() as c:
                dormant = c.execute("""
                    SELECT p.chat_id, p.name,
                           MAX(c.created_at) as last_contact,
                           (SELECT content FROM conversations
                            WHERE chat_id=p.chat_id AND role='user'
                            ORDER BY created_at DESC LIMIT 1) as last_msg
                    FROM patients p
                    JOIN conversations c ON c.chat_id = p.chat_id
                    GROUP BY p.chat_id
                    HAVING last_contact < datetime('now', '-60 days')
                    ORDER BY last_contact DESC LIMIT 20
                """).fetchall()

            if not dormant:
                return ["No hay clientes inactivos por más de 60 días"]

            scheduled = 0
            for i, pt in enumerate(dormant[:10]):
                # Programar con delay escalonado para no spam
                run_at = datetime.now() + timedelta(hours=i * 2 + 1)
                task_manager.schedule_task(
                    task_type="follow_up",
                    data={
                        "chat_id":      pt["chat_id"],
                        "reason":       "reactivation",
                        "last_message": (pt["last_msg"] or "")[:200],
                        "patient_name": pt["name"] or "",
                    },
                    scheduled_for=run_at,
                    priority=4
                )
                scheduled += 1

            names = ", ".join(pt["name"] or pt["chat_id"][:8] for pt in dormant[:5])
            return [
                f"Encontré {len(dormant)} clientes inactivos",
                f"Programé reactivación para {scheduled} — comenzando en 1 hora",
                f"Primeros: {names}{'...' if len(dormant) > 5 else ''}",
                "Escríbeme /pipeline en 24h para ver cómo respondieron"
            ]

        except Exception as e:
            return [f"Error: {e}"]

    async def _admin_configure_followup(self, clinic: Dict) -> List[str]:
        """
        /seguimiento — Configura los follow-ups automáticos.
        Muestra estado actual y permite activar/desactivar.
        """
        try:
            with db._conn() as c:
                pending = c.execute(
                    "SELECT COUNT(*) FROM tasks WHERE type='follow_up' AND status='pending'"
                ).fetchone()[0]
                completed = c.execute(
                    "SELECT COUNT(*) FROM tasks WHERE type='follow_up' AND status='completed' "
                    "AND created_at >= datetime('now', '-7 days')"
                ).fetchone()[0]

            return [
                "Seguimiento automático",
                f"Pendientes: {pending} | Enviados esta semana: {completed}",
                "Tipos activos:",
                "  • Lead frío (48h sin respuesta) — activo",
                "  • Conversación abandonada — activo",
                "  • Recordatorio de cita — activo",
                "  • Reactivación (60+ días) — manual con /reactivar",
                "Para cambiar la configuración escríbeme algo como:\n'desactiva el follow-up de 48 horas'"
            ]
        except Exception as e:
            return [f"Error: {e}"]

    async def _admin_preconsult_config(self, clinic: Dict) -> List[str]:
        """
        /preconsulta — Configura el formulario de pre-consulta automático.
        Antes de la cita, Bublee recopila síntomas, fotos, historial.
        """
        sector = clinic.get("sector", "otro")
        templates = {
            "estetica": [
                "zona de interés", "tratamientos anteriores", "alergias conocidas",
                "foto del área (opcional)", "qué resultado esperas"
            ],
            "medico": [
                "motivo de consulta", "síntomas principales", "hace cuánto",
                "medicamentos actuales", "alergias", "última vez que consultó"
            ],
            "dental": [
                "motivo de consulta", "dolor (sí/no y dónde)", "últimas radiografías",
                "sensibilidad al frío o calor", "tratamientos previos"
            ],
        }
        fields = templates.get(sector, ["motivo de consulta", "síntomas", "historial relevante"])

        # Guardar como configuración
        db.update_clinic(preconsult_fields=fields)

        return [
            "Pre-consulta automática configurada",
            f"Sector detectado: {sector}",
            "Bublee recopilará esto antes de cada cita:",
            "  " + "\n  ".join(f"• {f}" for f in fields),
            "El médico llega con el caso pre-estudiado",
            "Para personalizar: 'agrega el campo [nombre] a la pre-consulta'"
        ]

    async def _admin_broadcast(self, message: str) -> List[str]:
        """
        /broadcast [mensaje] — Envía un mensaje a todos los pacientes activos.
        Límite de 50 pacientes, con delay para no quedar bloqueado.
        """
        if not message or len(message) < 5:
            return ["Formato: /broadcast tu mensaje aquí"]

        try:
            with db._conn() as c:
                patients = c.execute("""
                    SELECT DISTINCT chat_id FROM patients
                    WHERE chat_id IS NOT NULL
                    ORDER BY created_at DESC LIMIT 50
                """).fetchall()

            if not patients:
                return ["No hay pacientes registrados"]

            # Programar envíos escalonados (1 cada 3 segundos)
            scheduled = 0
            for i, pt in enumerate(patients):
                run_at = datetime.now() + timedelta(seconds=i * 3)
                task_manager.schedule_task(
                    task_type="reminder",
                    data={"chat_id": pt["chat_id"], "message": message},
                    scheduled_for=run_at,
                    priority=3
                )
                scheduled += 1

            return [
                f"Broadcast programado para {scheduled} contactos",
                f"Mensaje: {message[:100]}{'...' if len(message) > 100 else ''}",
                "Se enviará escalonado en los próximos minutos para evitar bloqueos",
                "Usa con cuidado — demasiados mensajes masivos pueden generar baneo en WhatsApp"
            ]

        except Exception as e:
            return [f"Error: {e}"]

    async def _admin_instagram_guide(self) -> List[str]:
        """
        /instagram — Guía para conectar Instagram DMs a Bublee.
        Actualmente requiere configuración manual vía Meta API.
        """
        return [
            "Conectar Instagram DMs a Bublee",
            "Estado actual: en configuración (requiere Meta Business verificado)",
            "Lo que necesitas:",
            "  1. Cuenta de Instagram Business o Creator",
            "  2. Meta Business Suite verificado",
            "  3. App de Meta aprobada con permiso instagram_manage_messages",
            "  4. Webhook configurado en: https://nexusys.duckdns.org/instagram/webhook",
            "Cuando lo tengas listo escríbeme:",
            "  'el instagram access token es [TOKEN]'",
            "  'el instagram page id es [ID]'",
            "Y Bublee empezará a responder los DMs igual que WhatsApp"
        ]

    async def _admin_payments_guide(self) -> List[str]:
        """
        /pagos — Configura pagos desde el chat (Wompi, MercadoPago, Stripe).
        Cuando el cliente confirma, Bublee manda el link de pago directo.
        """
        clinic = db.get_clinic()
        payment_cfg = clinic.get("payment_config") or {}
        if isinstance(payment_cfg, str):
            import json as _j
            try: payment_cfg = _j.loads(payment_cfg)
            except Exception: payment_cfg = {}

        active = payment_cfg.get("provider", "")
        status = f"Activo: {active}" if active else "Sin configurar"

        return [
            f"Pagos desde el chat — {status}",
            "Providers disponibles:",
            "  • Wompi (Colombia) — recomendado",
            "  • MercadoPago — latinoamérica",
            "  • Stripe — internacional",
            "Para activar escríbeme:",
            "  'configura pagos con Wompi, mi clave pública es [KEY]'",
            "  'configura pagos con MercadoPago, token [TOKEN]'",
            "Cuando un cliente confirme, Bublee manda el link de pago automáticamente"
        ]

    async def _admin_trigger_report(self) -> List[str]:
        """
        /reporte — Genera y envía el reporte ahora mismo (sin esperar las 8am).
        """
        try:
            clinic    = db.get_clinic()
            biz_name  = clinic.get("name", "el negocio")
            admin_ids = _parse_admin_ids(clinic.get("admin_chat_ids", []))

            # Programar para ahora mismo
            task_manager.schedule_task(
                task_type="report",
                data={"type": "daily"},
                scheduled_for=datetime.now(),
                priority=8
            )

            # También generar preview rápido
            with db._conn() as c:
                convs_hoy = c.execute(
                    "SELECT COUNT(DISTINCT chat_id) FROM conversations "
                    "WHERE created_at >= datetime('now', '-1 days')"
                ).fetchone()[0] or 0
                apts_hoy = c.execute(
                    "SELECT COUNT(*) FROM appointments "
                    "WHERE created_at >= datetime('now', '-1 days')"
                ).fetchone()[0] or 0

            return [
                f"Reporte generado y enviando",
                f"Hoy: {convs_hoy} conversaciones, {apts_hoy} citas",
                "El reporte completo llega en un momento por aquí mismo"
            ]
        except Exception as e:
            return [f"Error: {e}"]

    # ═══════════════════════════════════════════════════════════════════════════
    # V8.0 — COMANDOS DE MODELO Y SISTEMAS
    # ═══════════════════════════════════════════════════════════════════════════

    async def _admin_show_model(self, clinic: Dict) -> List[str]:
        """
        /modelo — Muestra el modelo activo y el catálogo de opciones.
        El admin puede cambiar el modelo en caliente sin reiniciar.
        """
        if not model_manager:
            return ["El gestor de modelos no está disponible (reinicia el servidor)."]

        current_display = model_manager.get_current_model_display()
        catalog_display = model_manager.get_catalog_display()

        return [
            f"V8.0 — Gestión de modelos\n\n{current_display}",
            catalog_display,
        ]

    async def _admin_set_model(self, arg: str, clinic: Dict) -> List[str]:
        """
        /modelo [alias|id_completo|reset]
        Cambia el modelo en caliente. Persiste en DB.
        """
        if not model_manager:
            return ["El gestor de modelos no está disponible."]

        success, message = model_manager.set_model_from_command(arg)

        if success:
            # Mostrar el estado actualizado
            current = model_manager.get_current_model_display()
            return [
                f"Listo. {message}",
                current,
                "El cambio es inmediato. Sobrevive reinicios.",
                "Para volver al .env: /modelo reset"
            ]
        else:
            return [
                message,
                model_manager.get_catalog_display()
            ]

    async def _admin_v8_status(self) -> List[str]:
        """
        /v8 — Estado completo de sistemas V8 + salud real de providers LLM.
        """
        lines = ["V8.1 — Estado de sistemas\n"]

        # ── Salud de providers LLM ─────────────────────────────────────────────
        if llm_engine:
            health = llm_engine.get_health()
            lines.append("Providers LLM (cascada):")
            for p in llm_engine.providers:
                h = health.get(p.name, {})
                if h.get("blocked"):
                    secs = h.get("unblocks_in", 0)
                    status = f"⛔ BLOQUEADO ({secs}s restantes)"
                elif h.get("failures", 0) > 0:
                    status = f"⚠️ OK con {h['failures']} fallo(s) reciente(s)"
                else:
                    status = "✅ OK"
                # Modelo que está usando
                mdl = getattr(p, "MDLS", {}).get("fast", "?")
                lines.append(f"  {p.name}: {status} | modelo fast: {mdl}")
        else:
            lines.append("LLMEngine: ⛔ NO INICIADO — sin respuestas de IA")

        # ── Modelo activo ──────────────────────────────────────────────────────
        if model_manager:
            effective = model_manager.get_effective_models()
            lines.append(f"\nModelo activo:")
            lines.append(f"  fast: {effective.get('fast', 'default del .env')}")
            lines.append(f"  reasoning: {effective.get('reasoning', 'default del .env')}")
        else:
            lines.append("\nModelManager: NO INICIADO")

        # ── AntiRobotFilter ────────────────────────────────────────────────────
        if anti_robot_filter:
            lines.append(f"\nAntiRobotFilter: ✅ nivel {anti_robot_filter.level}/3")
        else:
            lines.append("\nAntiRobotFilter: ⚠️ NO INICIADO")

        # ── ConversationIntelligence ───────────────────────────────────────────
        if conversation_intelligence:
            active_convs = len(conversation_intelligence._states)
            stage_counts: Dict[str, int] = {}
            for state in conversation_intelligence._states.values():
                s = state.get("stage", "COLD")
                stage_counts[s] = stage_counts.get(s, 0) + 1
            lines.append(f"\nConversationIntelligence: {active_convs} chats activos")
            for stage, count in sorted(stage_counts.items()):
                lines.append(f"  {stage}: {count}")
        else:
            lines.append("\nConversationIntelligence: ⚠️ NO INICIADO")

        # ── Pipeline ───────────────────────────────────────────────────────────
        if conversion_funnel:
            summary = conversion_funnel.get_pipeline_summary()
            total  = sum(summary.values())
            booked = summary.get("booked", 0) + summary.get("confirmed", 0)
            rate   = round(booked / total * 100, 1) if total > 0 else 0
            lines.append(f"\nPipeline: {total} leads · {rate}% conversión")

        # ── Fallos recientes LLM (últimas 2h) ─────────────────────────────────
        try:
            if db:
                # Métricas de fallo guardadas por _register_failure
                recent_fails = db.get_metrics("llm_failure", limit=10)
                if recent_fails:
                    lines.append("\nÚltimos fallos LLM:")
                    for mf in recent_fails[:5]:
                        lines.append(f"  {mf.get('category','?')}: {mf.get('details',{}).get('error','?')[:60]}")
        except Exception:
            pass

        lines.append(f"\nTimeout provider: 10s | Blacklist TTL: {llm_engine._blacklist_ttl if llm_engine else '?'}s")
        lines.append("Para desbloquear un provider manualmente: /v8 reset")

        return ["\n".join(lines)]

    async def _admin_show_filter_status(self) -> List[str]:
        """
        /filtro — Muestra el estado del AntiRobotFilter y explica los niveles.
        """
        level = anti_robot_filter.level if anti_robot_filter else 2
        levels_desc = {
            1: "Suave — solo frases de call center obvias",
            2: "Normal (recomendado) — frases + patrones de bot",
            3: "Estricto — también cierres formales y aperturas repetitivas",
        }
        lines = [
            f"AntiRobotFilter — Nivel actual: {level}",
            f"  {levels_desc.get(level, 'desconocido')}",
            "",
            "Niveles disponibles:",
        ]
        for lvl, desc in levels_desc.items():
            mark = " ← activo" if lvl == level else ""
            lines.append(f"  /filtro {lvl} — {desc}{mark}")

        lines.append("\nFrases actualmente bloqueadas:")
        if anti_robot_filter:
            sample = list(anti_robot_filter.FORBIDDEN_EXACT)[:8]
            for phrase in sample:
                lines.append(f"  • '{phrase}'")
            lines.append(f"  ... y {len(anti_robot_filter.FORBIDDEN_EXACT) - 8} más")

        return ["\n".join(lines)]

    async def _admin_set_filter_level(self, level_str: str) -> List[str]:
        """
        /filtro [1|2|3] — Cambia el nivel del AntiRobotFilter.
        """
        global anti_robot_filter, hyper_human_engine

        if not level_str.isdigit() or int(level_str) not in (1, 2, 3):
            return ["Niveles válidos: 1 (suave), 2 (normal), 3 (estricto)"]

        level = int(level_str)
        Config.V8_FILTER_LEVEL = level
        anti_robot_filter = AntiRobotFilter(level=level)
        if hyper_human_engine:
            hyper_human_engine.filter = anti_robot_filter

        if db:
            db.remember("v8_filter_level", str(level), "config")

        level_names = {1: "suave", 2: "normal", 3: "estricto"}
        return [
            f"Filtro anti-robot cambiado a nivel {level} ({level_names[level]})",
            "El cambio aplica desde el próximo mensaje."
        ]

    async def _admin_pipeline_v8(self) -> List[str]:
        """
        /pipeline — Pipeline de leads usando ConversionFunnelTracker V8.
        Más detallado que el /pipeline de V6.
        """
        if not conversion_funnel:
            # Fallback al pipeline V6
            return await self._admin_pipeline()

        report = conversion_funnel.format_pipeline_report()
        rates  = conversion_funnel.get_conversion_rate()

        # Identificar el cuello de botella
        bottleneck = ""
        min_rate = 1.0
        for stage, rate in rates.items():
            if 0 < rate < min_rate:
                min_rate = rate
                bottleneck = stage

        lines = [report]
        if bottleneck:
            stage_tips = {
                "discovery":     "Bublee no está logrando explorar el dolor real. Revisar /coach.",
                "pain_explored": "El puente dolor→solución no está funcionando. Revisar arquetipos.",
                "solution_match":"Los clientes no están aceptando la valoración. Revisar el cierre.",
                "objection_active": "Las objeciones están ganando. Revisar respuestas de /reglas.",
                "micro_commitment": "El cliente está listo pero no agenda. Revisar la propuesta de fecha.",
            }
            tip = stage_tips.get(bottleneck, "Revisar conversaciones en /chats.")
            lines.append(f"\nCuello de botella detectado: {bottleneck}")
            lines.append(f"Sugerencia: {tip}")

        return lines

    async def _admin_natural_command(self, chat_id: str, text: str,
                                     clinic: Dict) -> List[str]:
        """
        Cerebro conversacional del modo admin.
        V9 Upgrade: Aprendizaje natural + Simulaciones interactivas.
        """
        text_low = text.lower().strip()

        # ── INTERCEPCIÓN DE CONTEXTO DE ESCALACIÓN ───────────────────────────
        # "muéstrame qué pasó", "muestrame que paso", "contexto", "ver contexto", "qué pasó", "que paso"
        import re as _re
        clean_text = _re.sub(r"[¿?¡!\.,]", "", text_low).strip()
        CONTEXT_SIGNALS = {
            "muestrame que paso", "muéstrame qué pasó", "que paso", "qué pasó",
            "contexto", "ver contexto", "contexto de la conversacion", "contexto de la conversación",
            "ver conversacion", "ver conversación", "contexto de la charla", "mostrar charla", "mostrar chat"
        }
        if clean_text in CONTEXT_SIGNALS:
            patient_chat_id = None
            pending = self._admin_pending.get(chat_id)
            if pending and isinstance(pending, dict):
                patient_chat_id = pending.get("patient_chat_id")
            
            if not patient_chat_id:
                patient_chat_id = getattr(self, "_last_escalated_chat_id", None)
            
            if not patient_chat_id:
                try:
                    with db._conn() as c:
                        row = c.execute("""
                            SELECT chat_id FROM conversation_states
                            WHERE json_extract(state, '$.escalation_needed') = 1 
                               OR json_extract(state, '$.escalation_needed') = 'true'
                            ORDER BY updated_at DESC LIMIT 1
                        """).fetchone()
                        if row:
                            patient_chat_id = row["chat_id"]
                except Exception as _db_err:
                    log.warning(f"[admin_context] error buscando ultimo escalado en DB: {_db_err}")
            
            if patient_chat_id:
                log.info(f"[admin_context] Admin {chat_id} solicitó contexto. Mostrando chat de {patient_chat_id}")
                return await self._admin_show_patient_chat(patient_chat_id)
            else:
                return ["No tengo registro de ningún paciente que haya solicitado hablar con un humano recientemente."]

        persona = clinic.get("persona_config", {})
        if isinstance(persona, str):
            try:
                persona = json.loads(persona) if persona else {}
            except Exception:
                persona = {}
        agent_name = persona.get("name", "Bublee")

        # ── COMANDOS DE APRENDIZAJE NATURAL ──────────────────────────────────
        # Detecta frases como "no digas X", "usa emojis", "dile Y"
        LEARNING_SIGNALS = [
            "no digas", "no le digas", "deja de decir", "quita la frase",
            "usa emojis", "ponle emojis", "responde con", "dile que",
            "siempre di", "nunca digas", "aprende esto", "guarda esto",
            "cambia la forma", "ahora dile", "cuando pregunten por",
            "la respuesta correcta es", "háblale de", "menciona que"
        ]

        # ── INTERCEPCIÓN DE ACCIONES DE SISTEMA (Demo, Restart, etc) ──────────
        if "modo demo" in text_low or "activa demo" in text_low or "demo on" in text_low or "demo off" in text_low:
            is_on = any(w in text_low for w in ["activa", "poner", "on", "encender"])
            action = "on" if is_on else "off"
            db_val = "true" if is_on else "false"
            
            msg = f"entendido, voy a poner el modo demo en {action} y reiniciar el sistema ||| dame unos segundos"
            try:
                # 1. Cambiar flag en DB
                with db._conn() as c:
                    c.execute("INSERT OR REPLACE INTO system_config (key, value, updated_at) VALUES ('demo_mode', ?, datetime('now'))", (db_val,))
                
                # 2. Actualizar .env
                import subprocess
                env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".env")
                if os.path.exists(env_path):
                    cmd_sed = f"sed -i 's/^DEMO_MODE=.*/DEMO_MODE={db_val}/g' {env_path}"
                    subprocess.run(cmd_sed, shell=True)
                
                # 3. Ejecutar reinicio
                subprocess.Popen("pm2 restart bublee", shell=True, start_new_session=True)
                return [msg]
            except Exception as e:
                log.error(f"[system] error activando demo: {e}")
                return [f"intenté activar el modo demo pero hubo un error técnico: {e}"]

        if any(s in text_low for s in LEARNING_SIGNALS):
            if self.admin_learning:
                reply = self.admin_learning.add_instruction(chat_id, text)
                return [reply]

        if "limpia las instrucciones" in text_low or "borra lo aprendido" in text_low:
            if self.admin_learning:
                return [self.admin_learning.clear()]

        # ── MODO SIMULACIÓN ──────────────────────────────────────────────────
        SIM_SIGNALS = [
            "simula", "simulaci", "como cliente", "hazte cliente",
            "actúa como cliente", "modo cliente", "hagamos una prueba",
            "ponte a prueba", "pruébame", "quiero ver cómo respondes",
            "simulemos", "haz como si fueras un paciente"
        ]
        if any(s in text_low for s in SIM_SIGNALS):
            if self.simulator:
                return self.simulator.start(chat_id)

        # ── SEGURIDAD: Bloquear intento de login inseguro ────────────────────
        # Si un usuario que NO es admin intenta enviar algo que parece login por nombre
        if ":" in text and ("password" in text_low or "contraseña" in text_low):
            is_admin = db.get_admin(chat_id) is not None
            if not is_admin:
                log.warning(f"[security] Intento de login inseguro bloqueado desde {chat_id}")
                return ["Por seguridad, no compartas contraseñas por este medio. Usa /login para iniciar sesión de forma segura."]

        # ── Reportes de Conversaciones ───────────────────────────────────────
        REPORT_SIGNALS = [
            "que han dicho", "qué han dicho", "quien ha escrito", "quién ha escrito",
            "ultimos pacientes", "últimos pacientes", "conversaciones", "chats",
            "qué me han enviado", "que me han enviado", "mensajes recientes"
        ]
        if any(s in text_low for s in REPORT_SIGNALS):
            return await self._admin_show_recent_conversation_browser(chat_id)

        # ── Ver un chat específico ───────────────────────────────────────────
        if "ver a " in text_low or "ver el chat de" in text_low:
            # Extraer número o nombre si es posible (implementación simplificada)
            return await self._admin_show_chats()

        # ── Auto-detección de credenciales WhatsApp ─────────────────────────
        wa_creds = _detect_wa_credentials(text)
        if wa_creds:
            return await self._admin_connect_whatsapp(
                chat_id, wa_creds["phone_id"], wa_creds["token"], clinic
            )

        # ── Detección de reglas Nova en lenguaje natural ──────────────────────
        # "no permitas que...", "bloquea...", "nunca envíes...", "prohíbe..."
        NOVA_RULE_SIGNALS = [
            r"no\s+(permitas?|dejes?|quiero que)\s+que\s+bublee",
            r"(bloquea?|prohibe?|prohíbe?)\s+que",
            r"nunca\s+(envíes?|mandes?|digas?|menciones?)",
            r"no\s+(envíes?|mandes?|digas?|menciones?)\s+.{5,}",
            r"impide?\s+que\s+bublee",
            r"asegúrate de que bublee nunca",
        ]
        if _NOVA_AVAILABLE and Config.NOVA_ENABLED:
            if any(re.search(p, text_low) for p in NOVA_RULE_SIGNALS):
                return await self._admin_nova_add_rule(text, clinic)

        # ── Simulación en lenguaje natural — "hagamos una simulación", "cómo le hablarías" ──
        # (Lógica delegada al SimulationEngine en la parte superior del método)
        pass

        # ── KB automático: texto largo con info de la clínica ─────────────────
        if len(text) > 300 and kb is not None and _KB_AVAILABLE:
            kb_indicators = [
                "precio", "servicio", "tratamiento", "protocolo",
                "contraindicacion", "incluye", "sesion", "duracion",
                "costo", "valor", "procedimiento", "candidat",
                "beneficio", "resultado", "recuperacion"
            ]
            if sum(1 for kw in kb_indicators if kw in text_low) >= 3:
                return await self._admin_kb_upload(text)

        # ── Control duro del owner/admin ─────────────────────────────────────
        if owner_style_controller and owner_style_controller.detect_control_intent(text):
            result = owner_style_controller.apply_instruction(text, admin_chat_id=chat_id)
            if result.get("ok"):
                if prompt_evolver and trainer_gateway and trainer_gateway.detect_admin_learning_intent(text):
                    try:
                        await prompt_evolver.evolve(text.strip(), chat_id)
                    except Exception:
                        pass
                reply_lines = result.get("reply_lines", ["Listo. Ya quedó aplicado."])
                reply_text = self._apply_admin_output_pipeline(" ||| ".join(reply_lines), chat_id, clinic, user_msg=text)
                return self._split_bubbles(reply_text)

        # ── Gateway automático del trainer para admins ───────────────────────
        if trainer_gateway and prompt_evolver and trainer_gateway.detect_admin_learning_intent(text):
            learned = await prompt_evolver.evolve(text.strip(), chat_id)
            if learned.get("ok"):
                lines = [f"Entendido. {learned.get('description', 'Ya ajusté ese comportamiento.')}"]
                if learned.get("example_good"):
                    lines.append(f"Ejemplo: \"{learned['example_good']}\"")
                lines.append("Si quieres, lo seguimos afinando sobre la marcha.")
                reply_text = self._apply_admin_output_pipeline(" ||| ".join(lines), chat_id, clinic, user_msg=text)
                return self._split_bubbles(reply_text)

        # Natural inbox queries are now handled dynamically by the LLM using chats_summary context.
        pass

        selection_idx = _extract_conversation_selection(text_low)
        if selection_idx:
            show_all = _wants_all_messages(text_low)
            direct_selection = any(
                token in text_low
                for token in (
                    "conversacion", "conversación", "chat", "mensajes",
                    "hablado", "hablaste", "mostrame", "muestrame",
                    "muéstrame", "enseñame", "ensename",
                )
            )
            if direct_selection:
                reply = await self._admin_show_recent_conversation_selection(
                    chat_id,
                    selection_idx,
                    show_all=show_all,
                )
                reply_text = self._apply_admin_output_pipeline(" ||| ".join(reply), chat_id, clinic, user_msg=text)
                db.save_message(chat_id, "user", text)
                db.save_message(chat_id, "assistant", reply_text if reply else "")
                return self._split_bubbles(reply_text)

        tone_complaints = [
            "hablas raro", "no me gusta cómo hablas", "no me gusta como hablas",
            "estás rara", "estas rara", "eso suena robot", "suenas robot",
            "muy bot", "muy fría", "muy fria", "muy seca",
        ]
        if any(w in text_low for w in tone_complaints):
            reply_text = self._apply_admin_output_pipeline(" ||| ".join([
                "pásame la frase exacta o dime el tono que quieres",
                "te saco una versión más cálida, más directa o más premium"
            ]), chat_id, clinic, user_msg=text)
            return self._split_bubbles(reply_text)

        # ── Búsqueda web real cuando el admin pide investigar ────────────────
        SEARCH_SIGNALS = [
            "busca en google", "busca en internet", "busca en la web",
            "investiga", "googlea", "buscar", "búscame", "busque",
            "averigua", "infórmate", "informate", "investigue",
            "haz una busqueda", "haz una búsqueda", "investigación",
        ]
        web_results = None
        if any(s in text_low for s in SEARCH_SIGNALS):
            search_query = clinic.get("name", "")
            for prefix in ["busca en google", "busca en internet", "busca en la web",
                           "busca", "investiga", "averigua", "infórmate sobre",
                           "informate sobre", "investigue"]:
                if prefix in text_low:
                    after = text_low.split(prefix, 1)[1].strip().strip(",.!?¿¡")
                    if after and len(after) > 2:
                        search_query = after
                        break
            if not search_query or len(search_query) < 3:
                search_query = f"{clinic.get('name', '')} {clinic.get('tagline', '')}".strip()
            if not search_query:
                search_query = "clinica medellin"
            try:
                results = await asyncio.wait_for(
                    self.search.search(search_query),
                    timeout=15.0
                )
                if results and len(results) > 10:
                    web_results = f"Resultados de búsqueda web sobre \"{search_query}\":\n{results[:2500] if len(results) > 2500 else results}"
            except Exception as e:
                log.error(f"[admin_search] error: {e}")
                web_results = None

        # ── Historial de admin (últimos 8 mensajes) ───────────────────────────
        admin_history = db.get_history(chat_id, limit=8)

        # ── Llamar al LLM conversacional ──────────────────────────────────────
        error_msg = None
        error_msg = None
        try:
            result = await asyncio.wait_for(
                self._admin_llm_brain(chat_id, text, admin_history, clinic, agent_name, web_results=web_results),
                timeout=12.0
            )
        except Exception as e:
            import traceback
            log.error(f"[admin_brain] error: {e}", exc_info=True)
            error_msg = f"LLM Exception: {str(e)}"
            result = None

        if result is None:
            return [error_msg if error_msg else "LLM Error: Sin respuesta del cerebro."]

        # ── Aplicar acción validada ───────────────────────────────────────────
        reply_text = result.get("reply", "")
        action     = result.get("action", "none")
        data       = result.get("data", {})

        await self._admin_apply_action(action, data, clinic, chat_id)

        # ── Guardar en historial ──────────────────────────────────────────────
        reply_text = self._apply_admin_output_pipeline(reply_text, chat_id, clinic, user_msg=text)
        db.save_message(chat_id, "user", text)
        if reply_text:
            db.save_message(chat_id, "assistant", reply_text)

        return self._split_bubbles(reply_text) if reply_text else [
            "dime qué más necesitas"
        ]

    def _admin_get_recent_chats_summary(self, owner_chat_id: str, clinic: Dict) -> str:
        try:
            from bublee_utils import _parse_admin_ids
            admin_ids = set(_parse_admin_ids(clinic.get("admin_chat_ids", [])))
            if owner_chat_id:
                admin_ids.add(str(owner_chat_id))
            
            with db._conn() as c:
                rows = c.execute("""
                    SELECT chat_id, MAX(ts) AS last_ts, COUNT(*) AS total
                    FROM conversations
                    WHERE role='user'
                    GROUP BY chat_id
                    ORDER BY last_ts DESC
                    LIMIT 5
                """).fetchall()
        except Exception:
            rows = []

        real_rows = []
        for row in rows:
            chat = str(row["chat_id"])
            if chat in admin_ids or self._is_synthetic_chat_id(chat):
                continue
            real_rows.append(row)

        if not real_rows:
            return "No hay chats reales con pacientes registrados todavía."

        lines = [f"Total de chats reales: {len(real_rows)}"]
        for idx, row in enumerate(real_rows, 1):
            chat = str(row["chat_id"])
            display = chat
            try:
                patient = db.get_patient(chat)
                name = (patient or {}).get("name", "").strip() if isinstance(patient, dict) else ""
                if name:
                    display = name
                elif "@s.whatsapp.net" in chat:
                    display = "chat de WhatsApp sin nombre"
                elif chat.isdigit():
                    display = "chat sin nombre"
            except Exception:
                pass
            
            # Obtener el último mensaje
            last_msg = ""
            try:
                with db._conn() as c:
                    last_row = c.execute("SELECT content FROM conversations WHERE chat_id=? AND role='user' ORDER BY ts DESC LIMIT 1", (chat,)).fetchone()
                    if last_row:
                        last_msg = last_row["content"][:60]
            except Exception:
                pass
            
            lines.append(f"  {idx}. {display} ({chat[-6:] or chat}): \"{last_msg}\"")
        return "\n".join(lines)

    def _admin_get_appointments_summary(self) -> str:
        try:
            appointments = db.get_appointments(limit=5)
        except Exception:
            appointments = []
        if not appointments:
            return "No hay citas programadas recientemente."
        
        lines = []
        for apt in appointments:
            dt = apt.get("datetime_slot", "")
            patient_id = apt.get("chat_id", "")
            status = apt.get("status", "pendiente")
            service = apt.get("service_type", "consulta")
            patient_name = "Sin nombre"
            try:
                p = db.get_patient(patient_id)
                if p and p.get("name"):
                    patient_name = p["name"]
            except Exception:
                pass
            lines.append(f"  - {dt} | Paciente: {patient_name} ({service}) | Estado: {status}")
        return "\n".join(lines)

    async def _admin_llm_brain(self, chat_id: str, text: str, history: List[Dict],
                               clinic: Dict, agent_name: str,
                               web_results: Optional[str] = None) -> Optional[Dict]:
        """
        Admin brain. Le damos identidad y contexto — el LLM piensa solo.
        Sin ejemplos. Sin lookup tables. Temperatura alta. IA real.
        """
        chats_summary = self._admin_get_recent_chats_summary(chat_id, clinic)
        apts_summary = self._admin_get_appointments_summary()

        # Si es la primera vez que hablan (historial vacío), Bublee se presenta
        is_first_turn = len(history) == 0
        setup_done = bool(clinic.get("setup_done"))

        # Detectar si el admin ya tiene perfil en DB
        admin_rec = db.get_admin(chat_id) if db else None
        admin_name_from_db = ""
        admin_name = "Admin"
        if admin_rec and admin_rec.get("name") and admin_rec["name"] not in ("", "Admin"):
            admin_name_from_db = admin_rec["name"]
            admin_name = admin_name_from_db

        # Intro para primer mensaje — Bublee se presenta naturalmente
        first_time_greeting = ""
        if is_first_turn and setup_done:
            clinic_name = clinic.get("name", "tu negocio") or "tu negocio"
            sector_name = SECTORS.get(clinic.get("sector", ""), SECTORS["otro"]).name if clinic.get("sector") else "negocio"
            if admin_name_from_db:
                first_time_greeting = f"""Estás empezando una conversación con {admin_name_from_db}.
Este es el primer mensaje que le envías. Preséntate con calidez, natural, como lo haría una empleada nueva que está conociendo a su jefe.
Di quién eres (tu nombre es {agent_name}), para qué estás (la recepcionista virtual de {clinic_name}), y pregunta en una línea cómo quieres que funcione.
Sé breve, cálida y directa. No des lista de funciones. No suenes a tutorial."""
            else:
                first_time_greeting = f"""Estás empezando una conversación con el dueño de {clinic_name}.
Este es el primer mensaje que le envías. Preséntate con calidez, natural, como lo haría una empleada nueva que está conociendo a su jefe.
Di quién eres (tu nombre es {agent_name}), para qué estás (la recepcionista virtual de {clinic_name}), y pregunta en una línea cómo quiere que funcione.
Si el negocio tiene {sector_name}, adapta el tono al sector. Sé breve, cálida y directa."""

        # Detectar si el admin está preguntando quién es Bublee
        text_low = text.lower().strip() if text else ""
        is_who_are_you = any(kw in text_low for kw in [
            "quién eres", "quien eres", "who are you", "como te llamas",
            "cómo te llamas", "de qué trata", "de que trata", "qué haces",
            "qué eres", "que eres", "para qué estás", "para que estás"
        ])

        services = clinic.get("services", [])
        pricing  = clinic.get("pricing", {})
        if isinstance(pricing, str):
            try: pricing = json.loads(pricing) if pricing else {}
            except Exception: pricing = {}

        _pc = clinic.get("persona_config", {})
        if isinstance(_pc, str):
            try: _pc = json.loads(_pc) if _pc else {}
            except Exception: _pc = {}

        warmth    = int(_pc.get("warmth_level", 0.7) * 100)
        formality = int(_pc.get("formality_level", 0.6) * 100)

        history_txt = ""
        for h in history[-8:]:
            who = admin_name if h["role"] == "user" else agent_name
            history_txt += f"{who}: {h['content'][:250]}\n"

        # Skills activas
        skills_txt = ""
        try:
            if skill_engine:
                active = skill_engine.get_active()
                if active:
                    skills_txt = f"\nSkills activas ahora: {', '.join(active)}"
        except Exception:
            pass

        # Diagnóstico reciente
        diag_txt = ""
        try:
            if bus:
                fails = bus.get_recent(5, "failure")
                if fails:
                    diag_txt = f"\nFallos recientes detectados: {len(fails)} (últimos: {', '.join(set(f.data.get('type','?') for f in fails[:3]))})"
        except Exception:
            pass

        # Últimas respuestas que ya dio — para no repetirlas
        last_replies = [h["content"][:80] for h in history[-4:] if h["role"] == "assistant"]
        last_replies_txt = "\n".join(f'  - "{r}"' for r in last_replies) if last_replies else "  (ninguna aún)"
        owner_control_txt = ""
        try:
            if owner_style_controller:
                owner_control_txt = owner_style_controller.build_prompt_addon(is_admin=True)
        except Exception:
            owner_control_txt = ""

        # Estos son los ejemplos de cómo {agent_name} habla CON EL DUEÑO
        # No reglas — identidad. El modelo sabe cómo reaccionar siendo esta persona.
        _admin_examples = f"""
{agent_name}: tienes {len(services)} servicios configurados{" y teléfono" if clinic.get("phone") else ", falta el teléfono"}
{admin_name}: cómo estás
{agent_name}: Hola, {admin_name}. Todo bien por aquí.
{agent_name}: Estoy atenta. Si quieres, revisamos lo que haga falta.
{admin_name}: hola
{agent_name}: Hola, {admin_name}. Estoy lista. ¿Qué quieres revisar primero?
{admin_name}: muéstrame cómo le hablarías a un cliente
{agent_name}: Claro. Dime el escenario y te muestro la apertura exacta.
{admin_name}: cámbiame los servicios a botox y rellenos
{agent_name}: Listo. Ya te lo dejo ajustado.
{admin_name}: quiero más calidez
{agent_name}: Entendido. Le subo calidez sin perder seriedad y lo probamos.
{admin_name}: no te entiendo cuando respondes hola
{agent_name}: Gracias por decirlo. Te propongo una versión más clara y la corregimos si hace falta.
"""

        system_prompt = f"""Eres {agent_name}.
Trabajas como la recepcionista ejecutiva de {clinic.get("name", "este negocio")}.
Ahora mismo hablas con tu administrador, {admin_name}.

ESTADO DE ENTRENAMIENTO:
Si el negocio es nuevo o no tienes información sobre servicios/precios:
1. Confirma honestamente: "Como soy nueva en {clinic.get("name", "el negocio")}, todavía no tengo información sobre eso".
2. Sé proactiva: Invita al admin a enseñarte los detalles para que puedas atender bien a los pacientes.

INFORMACIÓN EN VIVO DEL NEGOCIO Y CONFIGURACIÓN:
- Clínica: {clinic.get("name", "Sin configurar")}
- Servicios: {", ".join(services) if services else "NINGUNO (necesito que me los enseñes)"}
- Teléfono: {clinic.get("phone") or "No configurado"}{skills_txt}{diag_txt}

CHATS RECIENTES CON PACIENTES:
{chats_summary}

CITAS PROGRAMADAS RECIENTEMENTE:
{apts_summary}

REGLAS DE COMUNICACIÓN CON EL ADMIN:
- TONO: Cálido pero estrictamente profesional y ejecutivo. Cero informalidad de calle. NUNCA uses "vos".
- SIN MULETILLAS: No digas jamás "en qué puedo ayudarte" ni frases pasivas de asistente.
- PROACTIVIDAD: Tu objetivo es que el admin te entrene. Si detectas que falta info, pídela.
- CIERRE OBLIGATORIO: Todos tus mensajes DEBEN terminar con una pregunta concreta que invite al admin a realizar una acción o enseñarte algo.
- IDENTIDAD: Eres la asistente virtual de {clinic.get("name", "este negocio")}.

INSTRUCCIONES DE SISTEMA:
- Responde siempre de forma profesional e inteligente.
- Si el admin pide "activar modo demo", confirma y ejecuta.
- NUNCA digas que estás buscando en Google, internet, o investigando. Si no tienes la información, pídele al admin que te la dé.
"""

        messages = [
            {"role": "system", "content": system_prompt},
        ]
        if web_results:
            messages.append({"role": "system", "content": f"Información encontrada en internet (útil para responder al admin si pregunta por estos temas):\n{web_results}\n\nUsa esta información si es relevante para lo que el admin te está pidiendo. Si no es relevante, ignórala."})
        if first_time_greeting:
            messages.append({"role": "system", "content": first_time_greeting})
        if is_who_are_you and not first_time_greeting:
            messages.append({"role": "system", "content": f"Te están preguntando quién eres o qué haces. Responde como {agent_name}. Natural, cálida, una frase. No des lista de funciones."})
            
        # Append history!
        for h in history[-8:]:
            messages.append({"role": h["role"], "content": h["content"][:500]})
            
        messages.append({"role": "user",   "content": text})

        raw, _ = await llm_engine.complete(
            messages,
            model_tier="fast",
            temperature=0.72,
            max_tokens=600,
            use_cache=False
        )

        raw = raw.strip()
        # Extraer JSON del response
        json_str = None
        m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw, re.DOTALL)
        if m:
            json_str = m.group(1)
        elif raw.lstrip().startswith('{'):
            json_str = raw
        else:
            mx = re.search(r'(\{[\s\S]+\})', raw)
            if mx:
                json_str = mx.group(1)

        if not json_str:
            # LLM devolvió texto plano en vez de JSON — usarlo como reply
            clean = re.sub(r'```[\w]*\n?|```', '', raw).strip()
            return {"reply": clean or "cuéntame", "intent": "other",
                    "action": "none", "data": {}}

        parsed = json.loads(json_str)
        return parsed

    async def _admin_apply_action(self, action: str, data: Dict,
                                  clinic: Dict, chat_id: str) -> Optional[bool]:
        """
        Aplica la acción al DB con validación.
        Retorna True si se aplicó, False si fue rechazada, None si action=none.
        """
        if not action or action in ("none", "other", "show_config", "show_help"):
            return None

        # Simulación — triggear modo cliente desde el LLM brain
        if action == "simulate":
            scenario = data.get("scenario", "libre")
            try:
                sim_result = await _admin_simular_cliente(chat_id, scenario, clinic)
                # Guardar en historial la entrada al modo cliente
                db.save_message(chat_id, "assistant", sim_result[0] if sim_result else "")
                return True
            except Exception as e:
                log.warning(f"[admin] simulate error: {e}")
            return False

        if action == "set_admin_name":
            name = (data.get("name") or "").strip().title()
            if name and 2 <= len(name) <= 30:
                try:
                    with db._conn() as c:
                        c.execute("UPDATE admins SET name=? WHERE chat_id=?",
                                  (name, str(chat_id)))
                    log.info(f"[admin] nombre actualizado: {name}")
                    return True
                except Exception as e:
                    log.warning(f"[admin] set_admin_name error: {e}")
            return False

        if action == "update_services":
            raw_svcs = data.get("services", [])
            # Validar: cada item debe ser un nombre de tratamiento real
            valid_svcs = self._validate_services(raw_svcs)
            if valid_svcs:
                db.update_clinic(services=valid_svcs)
                return True
            return False

        if action == "update_phone":
            phone = re.sub(r'[\s\-\(\)]', '', str(data.get("phone", "")))
            if re.match(r'^[\+\d]{7,15}$', phone):
                db.update_clinic(phone=phone)
                return True
            return False

        if action == "update_address":
            addr = str(data.get("address", "")).strip()
            if addr and len(addr) > 4:
                db.update_clinic(address=addr)
                return True
            return False

        if action == "update_schedule":
            sched = data.get("schedule")
            if isinstance(sched, dict) and sched:
                db.update_clinic(schedule=sched)
                return True
            elif isinstance(sched, str) and len(sched) > 3:
                db.update_clinic(schedule={"General": sched})
                return True
            return False

        if action == "update_pricing":
            pricing_raw = data.get("pricing", {})
            if isinstance(pricing_raw, dict) and pricing_raw:
                # Merge con precios existentes
                existing = clinic.get("pricing", {})
                if isinstance(existing, str):
                    try:
                        existing = json.loads(existing) if existing else {}
                    except Exception:
                        existing = {}
                existing.update(pricing_raw)
                db.update_clinic(pricing=existing)
                return True
            return False

        if action == "update_persona":
            persona_changes = {}
            # Arquetipo completo — reemplaza toda la personalidad
            if "archetype" in data:
                arch_id = str(data["archetype"]).lower().strip()
                if arch_id in PERSONALITY_ARCHETYPES:
                    persona_changes["archetype"] = arch_id
                    # Aplicar todos los valores del arquetipo
                    a = PERSONALITY_ARCHETYPES[arch_id]
                    persona_changes["formality_level"] = a["formality"]
                    persona_changes["warmth_level"]    = a["warmth"]
                    persona_changes["humor_level"]     = a["humor"]
                    persona_changes["verbosity"]       = a["verbosity"]
                    persona_changes["tone"]            = a["desc"]
                    persona_changes["tone_instruction"] = a["tone_instruction"]
            # Ajustes manuales por encima del arquetipo
            if "warmth_level" in data:
                v = float(data["warmth_level"])
                persona_changes["warmth_level"] = max(0.0, min(1.0, v))
            if "formality_level" in data:
                v = float(data["formality_level"])
                persona_changes["formality_level"] = max(0.0, min(1.0, v))
            if "name" in data:
                n = str(data["name"]).strip().title()
                if 2 <= len(n) <= 20:
                    persona_changes["name"] = n
            if "tone" in data:
                persona_changes["tone"] = str(data["tone"])[:100]
            if persona_changes:
                full = self._apply_persona_merge({"persona_config": persona_changes}, clinic)
                db.update_clinic(**full)
                return True
            return False

        if action == "update_clinic_name":
            name = str(data.get("name", "")).strip()
            if name and len(name) > 1:
                db.update_clinic(name=name)
                return True
            return False

        if action == "update_tagline":
            tag = str(data.get("tagline", "")).strip()
            if tag:
                db.update_clinic(tagline=tag)
                return True
            return False

        return None

    def _validate_services(self, raw: list) -> List[str]:
        """
        Valida que una lista de strings sean nombres de servicios reales.
        Filtra frases, oraciones, textos personales y garbage.
        """
        if not raw or not isinstance(raw, list):
            return []

        # Palabras que indican que NO es un servicio
        NOT_SERVICE_SIGNALS = {
            "puedes", "puede", "podrias", "llama", "llamame", "soy", "mi",
            "busca", "google", "facebook", "instagram", "http", "www",
            "necesito", "quiero", "tengo", "favor", "gracias", "por"
        }
        # Categorías de servicios estéticos válidas
        AESTHETIC_HINTS = {
            "botox", "relleno", "laser", "peeling", "facial", "corporal",
            "limpieza", "hilo", "dermapen", "radiofrecuencia", "lipolisis",
            "cavitacion", "mesoterapia", "presoterapia", "depilacion",
            "microblading", "micropigmentacion", "prp", "hifu", "toxina",
            "bichectomia", "rinoplastia", "ojeras", "vitamina", "hydrafacial",
            "masaje", "drenaje", "plasma", "nutricion", "acne", "manchas",
            "cicatriz", "poro", "colágeno", "colageno", "elastina",
        }

        valid = []
        for item in raw:
            item = str(item).strip()
            if not item or len(item) < 2:
                continue
            if len(item) > 60:
                continue  # demasiado largo para ser un nombre de servicio
            item_low = item.lower()
            # Rechazar si contiene señales de NO servicio
            if any(sig in item_low for sig in NOT_SERVICE_SIGNALS):
                log.info(f"[validate_services] rechazado: '{item}'")
                continue
            # Rechazar si parece una oración (tiene verbo conjugado al inicio)
            words = item_low.split()
            if len(words) > 6:
                continue
            valid.append(item.title())

        return valid

    def _admin_local_fallback(self, text: str, text_low: str, clinic: dict, agent_name: str, chat_id: str = "") -> list[str]:
        return ["Error del sistema LLM: fallback local deshabilitado por arquitectura estricta."]

    def _is_synthetic_chat_id(self, chat_id: str) -> bool:
        value = (chat_id or "").strip().lower()
        if not value:
            return True
        synthetic_prefixes = (
            "qa_", "test_", "cli_", "api", "debug_", "tmp_", "sim_",
            "admin_test_", "qa-", "test-", "prod_", "audit_", "probe_",
            "admin_probe_", "prod_audit_", "owner-demo-", "wa_style_probe_",
            "tone_probe_", "prompt_probe_", "style_probe_", "owner-debug",
        )
        if value.startswith(synthetic_prefixes):
            return True
        synthetic_tokens = ("probe", "debug", "synthetic")
        if any(token in value for token in synthetic_tokens):
            return True
        if "@" not in value and not value.isdigit():
            if any(ch.isalpha() for ch in value) and ("_" in value or "-" in value):
                return True
        if value in {"status@broadcast"} or value.endswith("@newsletter"):
            return True
        return False

    async def _admin_show_recent_conversation_selection(
        self,
        admin_chat_id: str,
        selection_idx: int,
        *,
        show_all: bool = False,
    ) -> List[str]:
        chats = db.get_recent_patient_chats(limit=max(selection_idx + 8, 20))
        chats = [
            chat for chat in chats
            if not self._is_synthetic_chat_id(str(chat.get("chat_id") or "").strip())
        ]
        if not chats:
            return ["Bublee no ha tenido conversaciones reales todavía."]
        if selection_idx < 1 or selection_idx > len(chats):
            return [f"No encontré una conversación {selection_idx} en la lista reciente."]
        selected_chat_id = str(chats[selection_idx - 1].get("chat_id") or "").strip()
        selected_label = str(chats[selection_idx - 1].get("name") or "").strip()
        if not selected_chat_id:
            return ["No pude abrir esa conversación."]
        return await self._admin_show_patient_chat_preview(
            selected_chat_id,
            admin_chat_id=admin_chat_id,
            limit=10,
            show_all=show_all,
            label_override=selected_label,
        )

    def _admin_recent_chat_snapshot(self, owner_chat_id: str, clinic: Dict) -> List[str]:
        admin_name = "Santiago"
        try:
            admin = db.get_admin(owner_chat_id) if db and owner_chat_id else None
            if admin and admin.get("name"):
                admin_name = admin["name"].strip().title()
        except Exception:
            pass

        if not db:
            return [f"Aún no tengo ese dato, {admin_name}.", "Si quieres, reviso el canal o te muestro cuando entren conversaciones reales."]

        admin_ids = set(_parse_admin_ids(clinic.get("admin_chat_ids", [])))
        if owner_chat_id:
            admin_ids.add(str(owner_chat_id))

        try:
            with db._conn() as c:
                rows = c.execute("""
                    SELECT chat_id, MAX(ts) AS last_ts, COUNT(*) AS total
                    FROM conversations
                    WHERE role='user'
                    GROUP BY chat_id
                    ORDER BY last_ts DESC
                    LIMIT 20
                """).fetchall()
        except Exception:
            rows = []

        real_rows = []
        for row in rows:
            chat = str(row["chat_id"])
            if chat in admin_ids or self._is_synthetic_chat_id(chat):
                continue
            real_rows.append(row)

        if not real_rows:
            return [
                f"Aún no tengo ese dato, {admin_name}.",
                "Todavía no veo conversaciones reales de pacientes registradas en esta instancia."
            ]

        latest = real_rows[:5]
        labels: List[str] = []
        for row in latest:
            chat = str(row["chat_id"])
            display = chat
            try:
                patient = db.get_patient(chat)
                name = (patient or {}).get("name", "").strip() if isinstance(patient, dict) else ""
                if name:
                    display = name
                elif "@s.whatsapp.net" in chat:
                    display = "un chat de WhatsApp sin nombre guardado"
                elif chat.isdigit():
                    display = "un chat sin nombre guardado"
            except Exception:
                pass
            display_norm = (display or "").strip().lower()
            if not display or display == chat or display_norm == chat.lower():
                if "@s.whatsapp.net" in chat:
                    display = "un chat de WhatsApp sin nombre guardado"
                elif chat.isdigit():
                    display = "un chat sin nombre guardado"
            labels.append(display)

        total = len(real_rows)
        if total == 1:
            return [
                f"Me ha escrito 1 chat real en esta instancia.",
                f"El último que veo es {labels[0]}."
            ]
        joined = ", ".join(labels[:4])
        return [
            f"Veo {total} chats reales en esta instancia.",
            f"Los más recientes son: {joined}."
        ]

    def _apply_admin_output_pipeline(self, reply_text: str, chat_id: str, clinic: Dict, user_msg: str = "") -> str:
        """Aplica el plano de control del admin sobre las respuestas internas."""
        current = (reply_text or "").strip()
        if not current:
            return ""

        current = re.sub(r'\s*—\s*', ' ', current)
        current = re.sub(r'\s+', ' ', current).strip()
        current = re.sub(r'\s*\|\|\|\s*', ' ||| ', current)

        first_turn = True
        try:
            history = db.get_history(chat_id, limit=8) if db else []
            first_turn = not any((m.get("role") == "assistant") for m in (history or []))
        except Exception:
            pass

        if owner_style_controller:
            current = owner_style_controller.enforce_output(
                current,
                is_admin=True,
                first_turn=first_turn,
                chat_id=chat_id,
                clinic=clinic,
                user_msg=user_msg,
            )

        bubbles = [part.strip() for part in re.split(r'\s*\|\|\|\s*', current or "") if part.strip()]
        normalized: List[str] = []
        for bubble in bubbles:
            if bubble and bubble[0].islower():
                bubble = bubble[0].upper() + bubble[1:]
            normalized.append(bubble)
        current = " ||| ".join(normalized) if normalized else current

        return current or "Entendido."

    async def _admin_connect_whatsapp(self, chat_id: str,
                                      phone_id: str, access_token: str,
                                      clinic: Dict) -> List[str]:
        """
        Conecta WhatsApp completamente automático.
        El admin solo pega las credenciales — Bublee hace todo el resto.
        No muestra ningún paso técnico al cliente.
        """
        persona = clinic.get("persona_config", {})
        if isinstance(persona, str):
            try: persona = json.loads(persona)
            except Exception: persona = {}
        agent_name = persona.get("name", "Bublee")
        clinic_name = clinic.get("name", "la clínica")

        # ── 1. Validar credenciales ───────────────────────────────────────────
        result = await WhatsAppConnector.validate_credentials(phone_id, access_token)

        if not result["valid"]:
            # Error amigable — sin jerga técnica
            err = result.get("error", "")
            if "token" in err.lower() or "auth" in err.lower():
                user_msg = "El Access Token no es válido o expiró."
            elif "phone" in err.lower() or "id" in err.lower():
                user_msg = "El Phone Number ID no es correcto."
            else:
                user_msg = "No pude conectarme. Verifica que copiaste bien los dos datos."
            return [
                user_msg,
                "Necesito exactamente estos dos datos de tu Meta Business:\n"
                "  WA_PHONE_ID: (el número de 15 dígitos)\n"
                "  WA_TOKEN: EAAxxxx... (el token de acceso)"
            ]

        phone_number  = result.get("phone_number", "")
        business_name = result.get("business_name", "")
        verify_token  = f"mel_{hash(phone_id) % 99999:05d}"
        webhook_url   = f"{Config.BASE_URL}/webhook/{Config.WEBHOOK_SECRET}"

        # ── 2. Registrar webhook automáticamente (silencioso) ─────────────────
        asyncio.create_task(
            WhatsAppConnector.auto_register_webhook(
                phone_id, access_token, webhook_url, verify_token,
                app_id=Config.META_APP_ID,
                app_secret=Config.META_APP_SECRET
            )
        )

        # ── 3. Aplicar config en memoria y .env ───────────────────────────────
        WhatsAppConnector.apply_to_config(phone_id, access_token, verify_token)
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        WhatsAppConnector.write_env_update(env_path, phone_id, access_token, verify_token)

        # Guardar número en memoria permanente
        db.remember("whatsapp_phone",    phone_number,  "identity")
        db.remember("whatsapp_business", business_name, "identity")

        # ── 4. Enviar mensaje de prueba al admin por WhatsApp ─────────────────
        admin_phone = clinic.get("phone", "") or ""
        test_sent = False
        if admin_phone:
            test_sent = await WhatsAppConnector.send_test_message(
                phone_id, access_token,
                to_phone=admin_phone,
                clinic_name=clinic_name,
                agent_name=agent_name
            )

        # ── 5. Respuesta limpia — cero jerga técnica ──────────────────────────
        display_name = business_name or clinic_name
        response = [
            f"Listo. Ya estoy en WhatsApp como {display_name}.",
        ]

        if test_sent:
            response.append(
                f"Te acabo de enviar un mensaje de prueba al {phone_number} "
                f"para confirmar que funciona. Tus pacientes ya pueden escribirme."
            )
        else:
            response.append(
                f"Número activo: {phone_number}. "
                f"Tus pacientes ya pueden escribirme por WhatsApp."
            )

        return response

    async def _admin_kb_upload(self, text: str, replace: bool = False) -> List[str]:
        """Procesa y guarda el texto como base de conocimiento de la clínica."""
        if not kb or not _KB_AVAILABLE:
            return ["La base de conocimiento no esta disponible en esta instalacion."]
        try:
            stats = kb.ingest(text) if replace else kb.append(text)
            if stats.get("ok"):
                return [
                    "Base de conocimiento actualizada correctamente.",
                    f"{stats['chunks']} secciones indexadas · {stats['words']} palabras.",
                    "Ahora consulto esta info PRIMERO cuando un paciente pregunte sobre servicios, precios o procedimientos. Para ver estado: /kb. Si quieres reemplazar todo, primero usa /kb borrar."
                ]
            return ["No pude procesar ese texto. Intentalo en partes mas pequenas."]
        except Exception as e:
            log.error(f"KB upload error: {e}", exc_info=True)
            return ["Hubo un error guardando la informacion. Intenta de nuevo."]

    async def _admin_kb_status(self) -> List[str]:
        """Muestra el estado actual de la base de conocimiento."""
        if not kb or not _KB_AVAILABLE:
            return ["La base de conocimiento no esta disponible en esta instalacion."]
        if not kb.has_content():
            return [
                "No hay base de conocimiento cargada todavia.",
                "Envíame un documento con toda la info de tu clínica: servicios, precios, protocolos, contraindicaciones, FAQs.\n\nLo proceso automáticamente y lo uso para responder a tus pacientes."
            ]
        stats = kb.get_stats()
        upd = (stats.get("updated_at") or "")[:10]
        return [
            "Base de conocimiento activa.",
            f"Secciones: {stats['chunks']}\nPalabras: {stats['words']}\nActualizada: {upd}",
            "Puedes seguir anexando texto o documentos. Para borrar todo: /kb borrar"
        ]

    async def _admin_kb_clear(self) -> List[str]:
        """Borra la base de conocimiento."""
        if not kb or not _KB_AVAILABLE:
            return ["La base de conocimiento no esta disponible."]
        kb.clear()
        return ["Base de conocimiento borrada. Puedes cargar una nueva cuando quieras."]

    async def _admin_show_sector(self) -> List[str]:
        """Muestra el sector actual y los disponibles."""
        current = Config.SECTOR or "otro"
        emoji, name, services, _ = get_sector_info(current)
        lines = [
            f"Sector actual: {emoji} {name}",
            f"Servicios típicos: {services}\n\n"
            "Sectores disponibles:\n" +
            "\n".join(
                f"  /sector {sid} — {info[0]} {info[1]}"
                for sid, info in SECTORS.items()
                if sid != "otro"
            )
        ]
        return lines

    async def _admin_set_sector(self, sector_id: str) -> List[str]:
        """Cambia el sector del negocio."""
        if sector_id not in SECTORS:
            available = ", ".join(SECTORS.keys())
            return [f"Sector '{sector_id}' no reconocido. Disponibles: {available}"]
        emoji, name, services, _ = get_sector_info(sector_id)
        # Guardar en .env y DB
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        try:
            content = open(env_path).read() if os.path.exists(env_path) else ""
            if re.search(r'^SECTOR=', content, re.MULTILINE):
                content = re.sub(r'^SECTOR=.*$', f'SECTOR={sector_id}', content, flags=re.MULTILINE)
            else:
                content += f'\nSECTOR={sector_id}'
            open(env_path, 'w').write(content)
        except Exception:
            pass
        Config.SECTOR = sector_id
        db.remember("sector", sector_id, "identity")
        db.update_clinic(sector=sector_id)
        return [
            f"Sector cambiado a {emoji} {name}.",
            f"Bublee ahora conoce el vocabulario y los servicios típicos de {name}. "
            f"Servicios sugeridos: {services}."
        ]

    # ─── Nova Governance ────────────────────────────────────────────────────────

    async def _admin_nova_status(self) -> List[str]:
        """Muestra el estado de Nova y las reglas activas."""
        if not _NOVA_AVAILABLE:
            return [
                "Nova no está instalado.",
                "Nova es el motor de gobernanza que controla qué puede y qué no puede hacer Bublee.",
                "Cópialo en la carpeta de Bublee y activa NOVA_ENABLED=true en el .env."
            ]

        if not Config.NOVA_ENABLED:
            return [
                "Nova está instalado pero desactivado.",
                "Para activarlo: agrega NOVA_ENABLED=true en tu .env y reinicia.",
                "Una vez activo, puedes crear reglas con:\n/nova regla [descripción en lenguaje natural]"
            ]

        client = get_client()
        if not client:
            return ["Nova no está inicializado. Reinicia Bublee."]

        alive = await client.health_check()
        if not alive:
            return [
                f"Nova no está respondiendo en {Config.NOVA_URL}.",
                "Verifica que el servidor de Nova esté corriendo:\n  python3 nova.py server\n\nO cambia NOVA_URL en el .env."
            ]

        token_status = "configurado" if Config.NOVA_TOKEN else "sin configurar (usa /nova crear)"
        return [
            f"Nova activo en {Config.NOVA_URL}.",
            f"Token del agente: {token_status}\n\n"
            f"Comandos:\n"
            f"/nova ledger — ver últimas decisiones\n"
            f"/nova regla [texto] — agregar regla en lenguaje natural\n\n"
            f"Ej: /nova regla No le mandes precios a clientes que escriben por primera vez"
        ]

    async def _admin_nova_ledger(self) -> List[str]:
        """Muestra el ledger de decisiones recientes de Nova."""
        if not _NOVA_AVAILABLE or not Config.NOVA_ENABLED:
            return ["Nova no está activo. Usa /nova para ver el estado."]

        client = get_client()
        if not client:
            return ["Nova no está disponible."]

        summary = await get_ledger_summary(client, limit=10)
        return [summary]

    async def _admin_nova_add_rule(self, instruction: str, clinic: Dict) -> List[str]:
        """
        Agrega una nueva regla a Nova en lenguaje natural.
        Ej: "No le mandes precios a clientes nuevos"
        """
        if not _NOVA_AVAILABLE or not Config.NOVA_ENABLED:
            return [
                "Nova no está activo.",
                "Activa NOVA_ENABLED=true en el .env para usar reglas de gobernanza."
            ]

        if not instruction:
            return ["Dime la regla. Ej: /nova regla No menciones descuentos sin mi autorización"]

        # Convertir instrucción natural a reglas Nova via LLM
        try:
            rules = await nl_to_nova_rules(
                instruction=instruction,
                llm_complete_fn=llm_engine.complete,
                existing_rules={}
            )
        except Exception as e:
            return [f"No pude procesar la regla: {e}"]

        cannot_do = rules.get("cannot_do", [])
        can_do    = rules.get("can_do", [])
        expl      = rules.get("explanation", instruction)

        if not cannot_do and not can_do:
            return [
                "No pude extraer una regla clara de eso.",
                "Sé más específico. Ej:\n"
                "/nova regla No le envíes información de precios a pacientes que escriben por primera vez"
            ]

        # Crear/actualizar agente en Nova
        client = get_client()
        if client:
            alive = await client.health_check()
            if alive:
                # Obtener reglas existentes del agente y agregar las nuevas
                clinic_name = clinic.get("name", "Clinica")
                agent_name  = clinic.get("persona_config", {})
                if isinstance(agent_name, str):
                    try: agent_name = json.loads(agent_name)
                    except Exception: agent_name = {}
                agent_name = agent_name.get("name", "Bublee")

                # Base rules + new ones
                base_cannot = [
                    "provide specific medical diagnosis",
                    "prescribe medications or dosages",
                    "share another patient's personal information",
                    "guarantee specific treatment results",
                ]
                base_can = [
                    "answer questions about clinic services",
                    "book free consultations",
                    "provide clinic hours and location",
                ]

                result = await client.create_agent_rule(
                    agent_name=f"{agent_name} - {clinic_name}",
                    can_do=base_can + can_do,
                    cannot_do=base_cannot + cannot_do,
                    authorized_by="admin"
                )

                if "error" not in result:
                    token_id = result.get("token_id", "")
                    # Guardar token en memoria permanente
                    if token_id:
                        db.remember("nova_token", token_id, "identity")
                        # Actualizar Config en memoria
                        import nova_bridge as _nb
                        _nb.NOVA_TOKEN = token_id
                        if _nb.get_client():
                            _nb.get_client().token_id = token_id

                    # Construir respuesta legible
                    blocked_lines = "\n".join(f"  ✗ {r}" for r in cannot_do)
                    allowed_lines = "\n".join(f"  ✓ {r}" for r in can_do) if can_do else ""

                    reply = [
                        f"Regla creada. {expl}",
                        f"Nova ahora bloquea:\n{blocked_lines}"
                        + (f"\n\nNova permite:\n{allowed_lines}" if allowed_lines else ""),
                    ]
                    if token_id:
                        reply.append(f"Ledger activo — cada decisión queda registrada permanentemente.")
                    return reply

        # Nova no disponible — guardar regla localmente en trust_folder como fallback
        for rule in cannot_do:
            db.save_trust_rule(
                category="nova_policy",
                rule=f"[Nova pendiente] {rule}",
                example_bad="",
                example_good=""
            )

        return [
            f"Regla guardada localmente (Nova no está activo).",
            f"{expl}\n\nCuando actives Nova, se aplicará automáticamente."
        ]

    async def _admin_whatsapp_guide(self, clinic: Dict) -> List[str]:
        """
        Inicia el flujo conversacional de configuración de WhatsApp.
        Pregunta si tiene número existente o quiere uno nuevo.
        """
        wa_connected = db.recall("whatsapp_connected") == "true"
        wa_phone = db.recall("whatsapp_phone") or ""

        if wa_connected and wa_phone:
            return [
                f"Ya tienes WhatsApp conectado: {wa_phone}",
                "Quieres conectarme con otro número? Si es así dime y te guío."
            ]

        # Iniciar flujo — guardar estado en setup_buffer
        clinic_data = db.get_clinic()
        buf = clinic_data.get("setup_buffer", {})
        if isinstance(buf, str):
            try: buf = json.loads(buf) if buf else {}
            except Exception: buf = {}

        buf["wa_flow"] = "asking_type"
        db.update_clinic(setup_buffer=buf)

        return [
            "Para conectarme a WhatsApp tengo dos opciones:",
            "1. Ya tienes un número de WhatsApp Business y quieres usarlo\n"
            "2. Quieres un número nuevo\n\n"
            "Cuál es tu caso?"
        ]

    async def _handle_whatsapp_setup_flow(self, chat_id: str, text: str,
                                           clinic: Dict) -> Optional[List[str]]:
        """
        Maneja el flujo conversacional de configuración de WhatsApp.
        Se activa cuando hay un wa_flow activo en setup_buffer.
        Retorna burbujas si está manejando el flujo, None si no aplica.
        """
        buf = clinic.get("setup_buffer", {})
        if isinstance(buf, str):
            try: buf = json.loads(buf) if buf else {}
            except Exception: buf = {}

        wa_flow = buf.get("wa_flow", "")
        if not wa_flow:
            return None

        text_low = text.lower().strip()

        # ── Paso 1: preguntamos tipo (nuevo o existente) ──────────────────────
        if wa_flow == "asking_type":
            is_existing = any(w in text_low for w in [
                "1", "tengo", "tengo uno", "existente", "ya tengo",
                "tengo numero", "tengo el", "mio", "mío", "si tengo"
            ])
            is_new = any(w in text_low for w in [
                "2", "nuevo", "quiero uno", "no tengo", "necesito",
                "sin numero", "quiero nuevo"
            ])

            if is_new:
                # Flujo nuevo número — escalar a Omni/Santiago
                buf["wa_flow"] = "new_number_requested"
                db.update_clinic(setup_buffer=buf)

                # Notificar a Santiago via Bublee Omni
                asyncio.create_task(
                    self._notify_omni(
                        event="new_whatsapp_number_requested",
                        clinic_name=clinic.get("name", ""),
                        chat_id=chat_id,
                        details=f"El admin de {clinic.get('name','')} necesita un número nuevo de WhatsApp."
                    )
                )
                return [
                    "Perfecto. Para conseguirte un número nuevo de WhatsApp Business "
                    "necesito coordinarlo.",
                    "Ya le avisé a nuestro equipo. Te contactarán en menos de 24 horas "
                    "para activar tu número. Mientras tanto puedo seguir funcionando por "
                    "Telegram."
                ]

            elif is_existing:
                buf["wa_flow"] = "guide_step_1"
                db.update_clinic(setup_buffer=buf)
                return await self._wa_guide_step(1, clinic)

            else:
                return [
                    "No entendí bien. Tienes ya un número de WhatsApp Business (1) "
                    "o quieres uno nuevo (2)?"
                ]

        # ── Pasos del guía para número existente ──────────────────────────────
        if wa_flow.startswith("guide_step_"):
            step = int(wa_flow.split("_")[-1])

            # Detectar si pegaron credenciales en cualquier paso
            wa_creds = _detect_wa_credentials(text)
            if wa_creds:
                buf["wa_flow"] = ""
                db.update_clinic(setup_buffer=buf)
                return await self._admin_connect_whatsapp(
                    chat_id, wa_creds["phone_id"], wa_creds["token"], clinic
                )

            # Confirmar que van avanzando
            CONTINUE_SIGNALS = [
                "listo", "ok", "ya", "hecho", "sí", "si", "dale",
                "siguiente", "continua", "next", "ya lo hice", "ya está"
            ]
            if any(s in text_low for s in CONTINUE_SIGNALS) or len(text_low) < 25:
                next_step = step + 1
                if next_step > 6:
                    # Ya deberían tener las credenciales
                    buf["wa_flow"] = "waiting_credentials"
                    db.update_clinic(setup_buffer=buf)
                    return [
                        "Ahora pégame los dos datos que copiaste:",
                        "WA_PHONE_ID: (el número largo de 15 dígitos)\n"
                        "WA_TOKEN: EAAxxxxx... (el token de acceso)"
                    ]
                buf["wa_flow"] = f"guide_step_{next_step}"
                db.update_clinic(setup_buffer=buf)
                return await self._wa_guide_step(next_step, clinic)

            # Pregunta o confusión — buscar en web para ayudar
            if len(text) > 20:
                search_hint = await self._wa_search_help(text)
                return [search_hint or "Cuéntame qué ves en tu pantalla y te ayudo."]

            return await self._wa_guide_step(step, clinic)

        if wa_flow == "waiting_credentials":
            wa_creds = _detect_wa_credentials(text)
            if wa_creds:
                buf["wa_flow"] = ""
                db.update_clinic(setup_buffer=buf)
                return await self._admin_connect_whatsapp(
                    chat_id, wa_creds["phone_id"], wa_creds["token"], clinic
                )
            return [
                "Aún no veo las credenciales. Necesito los dos datos:",
                "WA_PHONE_ID: [número de 15 dígitos]\n"
                "WA_TOKEN: EAAxxxxx..."
            ]

        return None

    async def _wa_guide_step(self, step: int, clinic: Dict) -> List[str]:
        """
        Guía paso a paso para conectar WhatsApp Business.
        Lenguaje 100% humano — sin jerga técnica.
        """
        clinic_name = clinic.get("name", "tu clínica")

        steps = {
            1: [
                "Primero abre este link en tu computador (no en el celular):",
                "developers.facebook.com/apps\n\n"
                "Si no tienes cuenta, créala con el mismo correo de tu Facebook Business. "
                "Cuando estés adentro, dime 'listo'."
            ],
            2: [
                "Haz clic en 'Crear app' (botón verde arriba a la derecha).",
                "Te va a preguntar el tipo de app. Selecciona 'Business' y sigue. "
                "Ponle el nombre que quieras, por ejemplo 'WhatsApp Clínica'. "
                "Cuando termines de crearla, dime 'listo'."
            ],
            3: [
                "Dentro de tu nueva app, busca el producto 'WhatsApp' en la lista "
                "y haz clic en 'Configurar'.",
                "Te va a pedir que conectes una cuenta de WhatsApp Business. "
                "Si no tienes una, te la crea Meta automáticamente. Acepta. "
                "Cuando lo hayas hecho, dime 'listo'."
            ],
            4: [
                "Ahora estás en el panel de WhatsApp. Busca la sección "
                "'Configuración de la API' o 'API Setup'.",
                "Ahí verás un número de prueba de Meta. Más abajo hay un campo "
                "que dice 'Número de teléfono' — ahí agrega tu número de "
                f"{clinic_name}. Cuando lo hayas agregado, dime 'listo'."
            ],
            5: [
                "En esa misma pantalla vas a ver dos datos importantes.",
                "Cópialos y guárdalos en un bloc de notas:\n\n"
                "1. Phone Number ID — un número largo de 15 dígitos\n"
                "2. Token de acceso — empieza con 'EAA...'\n\n"
                "Para el token, busca la opción de generar un token permanente "
                "(no temporal). Cuando los tengas, dime 'listo'."
            ],
            6: [
                "Perfecto, ya casi.",
                "Pégame aquí los dos datos que copiaste así:\n\n"
                "WA_PHONE_ID: [el número de 15 dígitos]\n"
                "WA_TOKEN: EAAxxxxx...\n\n"
                "Yo me encargo del resto."
            ]
        }

        return steps.get(step, steps[6])

    async def _wa_search_help(self, question: str) -> str:
        """
        Busca en web para responder una duda específica del flujo de WhatsApp.
        """
        try:
            query = f"Meta WhatsApp Business API setup {question[:60]} 2024"
            result = await self.search.search(query)
            if result:
                # Simplificar el resultado para el admin
                try:
                    prompt = (
                        f"El admin de una clínica está configurando WhatsApp Business API "
                        f"y tiene esta duda: '{question}'\n\n"
                        f"Esto encontré en internet:\n{result[:600]}\n\n"
                        f"Explícale en máximo 2 oraciones, en lenguaje simple, sin jerga técnica."
                    )
                    answer, _ = await asyncio.wait_for(
                        llm_engine.complete(
                            [{"role": "user", "content": prompt}],
                            model_tier="fast", temperature=0.3, max_tokens=150,
                            use_cache=False
                        ),
                        timeout=8.0
                    )
                    return answer.strip()
                except Exception:
                    return result[:200]
        except Exception:
            pass
        return ""

    async def _notify_omni(self, event: str, clinic_name: str,
                           chat_id: str, details: str):
        """
        Envía una notificación a Bublee Omni (instancia de Santiago).
        Usa httpx async si está disponible, cae a la función sync como fallback.
        """
        omni_url = os.getenv("OMNI_URL", "")
        omni_key = os.getenv("OMNI_KEY", "")
        if not omni_url or not omni_key:
            # Fallback: notificar directo al chat de Santiago
            santiago_chat = os.getenv("SANTIAGO_CHAT_ID", "")
            if santiago_chat:
                msg = f"Evento [{event}] en {clinic_name}: {details}"
                try:
                    await self._send_message(santiago_chat, msg)
                except Exception:
                    pass
            return
        try:
            async with httpx.AsyncClient(timeout=5.0) as c:
                await c.post(f"{omni_url}/omni/event",
                    headers={"X-Omni-Key": omni_key, "Content-Type": "application/json"},
                    json={
                        "event":      event,
                        "clinic":     clinic_name,
                        "chat_id":    chat_id,
                        "details":    details,
                        "severity":   "info" if event not in ("queja_paciente", "error_procesamiento") else "warning",
                        "timestamp":  datetime.now().isoformat()
                    })
        except Exception as e:
            log.debug(f"[omni] notify silenced: {e}")

    async def _admin_agenda_status(self) -> List[str]:
        """Muestra el estado del puente de calendario."""
        if not calendar_bridge:
            return ["El modulo de calendario no esta disponible."]

        if calendar_bridge.has_google_calendar():
            slots = await calendar_bridge.get_free_slots(days_ahead=3)
            if slots:
                # Agrupar por dia
                by_day: Dict[str, list] = {}
                for s in slots:
                    by_day.setdefault(s["day_label"], []).append(s["time"])

                lines = ["Agenda vinculada. Disponibilidad proximos 3 dias:\n"]
                for day, times in list(by_day.items())[:3]:
                    times_str = ", ".join(times[:4])
                    lines.append(f"  {day}: {times_str}")
                lines.append(
                    "\nBublee consulta esto en tiempo real cuando un paciente "
                    "pregunta por horarios."
                )
                return ["\n".join(lines)]
            return [
                "Google Calendar vinculado pero sin slots disponibles en los proximos 3 dias.",
                "Revisa tu agenda en Google Calendar."
            ]

        elif calendar_bridge.has_calendly():
            return [
                f"Calendly configurado: {calendar_bridge._calendly_link}",
                "Cuando un paciente pregunte por horarios, Bublee comparte ese link. "
                "Para vincular Google Calendar directamente: abre "
                f"{Config.BASE_URL}/vincular-agenda en tu navegador."
            ]

        else:
            base = Config.BASE_URL or "https://tu-servidor.com"
            return [
                "Sin agenda vinculada todavia.",
                f"Opciones:\n\n"
                f"1. Google Calendar (recomendado — disponibilidad en tiempo real):\n"
                f"   Abre este link en tu navegador:\n"
                f"   {base}/vincular-agenda\n\n"
                f"2. Calendly (mas simple):\n"
                f"   /calendly https://calendly.com/tu-link\n\n"
                f"Sin agenda, cuando un paciente pregunte por horarios "
                f"te escribo directamente para que me digas tu disponibilidad."
            ]

    def _try_local_persona_change(self, text_low: str, persona: Dict,
                                  clinic: Dict) -> Optional[List[str]]:
        """
        Detecta cambios de personalidad simples SIN necesitar el LLM.
        Retorna lista de burbujas si se pudo resolver localmente, None si no.
        """
        changes = {}
        msgs = []

        # Calidez
        if re.search(r'(mas|m[aá]s|m[aá]ximo|sube|aumenta|100|alta?)\s*(calidez|c[aá]lid[ao]|cariñ|warm)', text_low):
            val = 1.0 if "100" in text_low or "maximo" in text_low or "máximo" in text_low else 0.9
            changes.setdefault("persona_config", {})["warmth_level"] = val
            msgs.append(f"Calidez: {int(val*100)}%")
        elif re.search(r'(menos|baja|reduce|minimal?)\s*(calidez|cariñ)', text_low):
            changes.setdefault("persona_config", {})["warmth_level"] = 0.4
            msgs.append("Calidez: 40%")

        # Formalidad
        if re.search(r'(mas|m[aá]s|muy|sube)\s*(formal|profesional)', text_low):
            val = 0.9 if "muy" in text_low else 0.8
            changes.setdefault("persona_config", {})["formality_level"] = val
            msgs.append(f"Formalidad: {int(val*100)}%")
        elif re.search(r'(menos|baja|poco|informal|relajad)', text_low):
            changes.setdefault("persona_config", {})["formality_level"] = 0.25
            msgs.append("Formalidad: 25%")

        # Cambio de nombre del agente
        m = re.search(r'(?:cambia|llama(?:la|se)?|nombre)[^\w]+(a|como)\s+([A-Z][a-z]+)', text_low, re.IGNORECASE)
        if not m:
            m = re.search(r'(?:se llame|se llama|nombre es|nombre a)\s+([A-Z][a-z]+)', text_low, re.IGNORECASE)
            if m:
                nuevo_nombre = m.group(1).strip().title()
                changes.setdefault("persona_config", {})["name"] = nuevo_nombre
                msgs.append(f"Nombre cambiado a {nuevo_nombre}")
        elif m:
            nuevo_nombre = m.group(2).strip().title()
            changes.setdefault("persona_config", {})["name"] = nuevo_nombre
            msgs.append(f"Nombre cambiado a {nuevo_nombre}")

        if not changes:
            return None  # No se pudo resolver localmente

        # Aplicar cambios
        changes = self._apply_persona_merge(changes, clinic)
        db.update_clinic(**changes)

        persona_new = changes.get("persona_config", {})
        agent_name = persona_new.get("name", persona.get("name", "Bublee"))
        summary = ". ".join(msgs)
        return [
            f"Listo. {summary}.",
            f"{agent_name} ya tiene la nueva configuracion."
        ]

    def _apply_persona_merge(self, changes: Dict, clinic: Dict) -> Dict:
        """Merge inteligente de persona_config con el existente."""
        if "persona_config" not in changes:
            return changes

        existing = clinic.get("persona_config", {})
        if isinstance(existing, str):
            try:
                existing = json.loads(existing) if existing else {}
            except Exception:
                existing = {}

        new_persona = dict(existing)
        new_persona.update(changes["persona_config"])
        changes["persona_config"] = new_persona
        return changes

    def _changes_summary(self, changes: Dict, clinic: Dict) -> str:
        """Genera confirmacion legible de los cambios aplicados."""
        parts = []

        for key, value in changes.items():
            if key == "persona_config":
                for pkey, pval in value.items():
                    if pkey == "name":
                        parts.append(f"Nombre cambiado a {pval}")
                    elif pkey == "formality_level":
                        pct = int(float(pval) * 100)
                        parts.append(f"Formalidad: {pct}%")
                    elif pkey == "warmth_level":
                        pct = int(float(pval) * 100)
                        parts.append(f"Calidez: {pct}%")
                    elif pkey == "tone":
                        parts.append(f"Tono: {pval}")
                    elif pkey == "forbidden_words":
                        parts.append(f"Palabras prohibidas: {', '.join(pval)}")
                    else:
                        parts.append(f"{pkey}: {pval}")
            elif key == "services":
                parts.append(f"Servicios actualizados ({len(value)} en total)")
            elif key == "phone":
                parts.append(f"Telefono: {value}")
            elif key == "name":
                parts.append(f"Nombre clinica: {value}")
            elif key == "schedule":
                parts.append("Horario actualizado")
            elif key == "address":
                parts.append(f"Direccion: {value}")
            else:
                parts.append(f"{key} actualizado")

        if parts:
            return "Listo. " + ". ".join(parts) + "."
        return "Cambios aplicados."

    
    # ─── Buffer Management ──────────────────────────────────────────────────────
    
    # ─── Busqueda Inteligente ────────────────────────────────────────────────────

    async def _smart_search(self, text: str, analysis: "MessageAnalysis",
                            clinic: Dict) -> str:
        """
        Construye la query de busqueda segun intencion y entidades extraidas.
        Busca diferente segun lo que el paciente este preguntando.
        """
        clinic_name = clinic.get("name", "")
        services    = clinic.get("services", [])
        intent      = analysis.intent
        entities    = analysis.entities
        keywords    = analysis.keywords

        # ── Precio de servicio especifico ─────────────────────────────────────
        if intent.name in ("PRICE_INQUIRY", "SERVICE_INFO"):
            # Si menciona servicios conocidos, incluirlos en la query
            mentioned_services = [
                s for s in services
                if any(kw in s.lower() for kw in keywords[:5])
            ]
            service_term = mentioned_services[0] if mentioned_services else " ".join(keywords[:2])
            query = f"{service_term} precio costo Medellin clinica estetica"

        # ── Pregunta sobre horario o ubicacion ────────────────────────────────
        elif intent.name in ("HOURS_INQUIRY", "LOCATION_INQUIRY"):
            query = f"{clinic_name} {intent.name.lower().replace('_inquiry', '')} Medellin"

        # ── Pregunta general con keywords claros ──────────────────────────────
        elif keywords:
            query = f"{' '.join(keywords[:3])} clinica estetica Colombia"

        # ── Fallback: buscar el texto completo ────────────────────────────────
        else:
            query = f"{text[:80]} clinica estetica Medellin"

        log.info(f"[search] intent={intent.name} query={query!r}")
        return await self.search.search(query, context=clinic_name)

    # ─── Buffer Inteligente ──────────────────────────────────────────────────────
    
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
            # Este es el catch-all MÁS externo — algo falló fuera del try de
            # process_message. Antes se mandaba un mensaje genérico al
            # paciente ("tuve un error técnico inesperado"). Mismo criterio
            # que en process_message: nada al paciente, aviso inmediato al dueño.
            try:
                from bublee_utils import notify_owner_of_ai_failure, _parse_admin_ids as _parse_admin_ids_fb2
                clinic_fb = db.get_clinic()
                admin_ids = _parse_admin_ids_fb2((clinic_fb or {}).get("admin_chat_ids", []))
                context_label = "prospecto (demo)" if Config.DEMO_MODE else "paciente"
                await notify_owner_of_ai_failure(
                    self._send_message, admin_ids, chat_id, combined, context=context_label,
                )
            except Exception as e2:
                log.error(f"[ai_failure] no pude avisarle al dueño sobre {chat_id} (flush error): {e2}")
    
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
        _is_demo_active = False
        if db:
            try:
                _is_demo_active = db.recall(f"beta_demo_{chat_id}") == "true"
            except Exception:
                pass
        
        _is_voice_off = self._demo_sessions.get(f"demo_{chat_id}_voice_off", False)

        _has_eleven_key = bool(os.getenv("ELEVENLABS_API_KEY") or os.getenv("ELEVENLABS_API_KEY_2"))
        if not _has_eleven_key:
            try:
                from bublee_demo_voice import API_KEYS
                _has_eleven_key = any(API_KEYS)
            except Exception:
                pass

        if (Config.DEMO_MODE or _is_demo_active) and not _is_voice_off and is_wa and bubbles and _has_eleven_key:
            try:
                from bublee_demo_voice import generate_demo_audio, should_send_voice_in_demo
                history_len = len(db.get_history(chat_id)) if db else 0
                
                # Check if the user explicitly requested voice/audio in their last message
                _user_requested_voice = False
                if db:
                    _hist = db.get_history(chat_id, limit=1)
                    if _hist and _hist[0].get("role") == "user":
                        _ut = _hist[0].get("content", "").lower()
                        if any(w in _ut for w in ["audio", "voz", "escuchar", "hablar"]):
                            _user_requested_voice = True
                
                if _user_requested_voice or should_send_voice_in_demo(bubbles[0], history_len // 2, False):
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
