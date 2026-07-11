from __future__ import annotations

import asyncio
import importlib.util
import sqlite3
import sys
import tempfile
import types
import uuid
from pathlib import Path


MODULE_PATH = Path("/home/ubuntu/bublee/instances/clinica-de-las-americas/bublee.py")


def load_bublee_module():
    module_name = f"bublee_instance_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_first_turn_short_messages_do_not_use_seeded_templates():
    module = load_bublee_module()
    generator = module.ResponseGenerator(llm=None)

    assert generator._should_use_seeded_first_turn("Hola buenas tardes", []) is False
    assert generator._should_use_seeded_first_turn("Botox precio", []) is False


def test_demo_business_override_payload_extracts_business_name_and_context():
    module = load_bublee_module()

    payload = module._extract_demo_business_override_payload(
        "Ya dejé Nova como negocio activo. Nova es una plataforma de gobernanza de intención para agentes de IA en bancos."
    )

    assert payload is not None
    assert payload["business_name"] == "Nova"
    assert "plataforma de gobernanza" in payload["raw_context"].lower()
    assert "negocio activo" not in payload["raw_context"].lower()


def test_demo_business_onboarding_state_tracks_answers_and_missing_gaps():
    module = load_bublee_module()

    state = module._new_demo_business_onboarding_state(
        "Nova",
        "Nova es una plataforma de gobernanza de intención para agentes de IA en bancos.",
    )
    state = module._capture_demo_business_onboarding_answers(
        state,
        "Le vendemos primero a bancos medianos y fintechs que ya tienen agentes internos en pruebas.",
    )
    state = module._capture_demo_business_onboarding_answers(
        state,
        "El ticket promedio arranca en 20 mil dólares al año.",
    )

    assert state["answers"]["problem"]
    assert state["answers"]["icp"]
    assert state["answers"]["ticket"]
    assert module._next_demo_business_onboarding_gap(state) == "objection"

    summary = module._render_demo_business_onboarding_summary(state).lower()
    assert "nova" in summary
    assert "cliente objetivo" in summary
    assert "ticket" in summary


def test_antirobot_does_not_mutilate_valid_response_into_fragment():
    module = load_bublee_module()
    anti = module.AntiRobotFilter(level=2)

    original = "gracias por escribirnos, el precio"
    processed = anti.process(original, archetype="amigable")

    assert processed == original


def test_looks_fragmented_reply_flags_short_dangling_fragments():
    module = load_bublee_module()

    assert module.looks_fragmented_reply("el precio") is True
    assert module.looks_fragmented_reply("busques lo mejor para") is True
    assert module.looks_fragmented_reply("cuál es el ticket") is True
    assert module.looks_fragmented_reply("cómo gestionan") is True
    assert module.looks_fragmented_reply("hola! Dime, de qué") is True
    assert module.looks_fragmented_reply("hola") is False


def test_activate_brain_v10_patch_marks_generator_llm_first():
    module = load_bublee_module()

    class FakeGenerator:
        async def generate(self, *args, **kwargs):
            return "respuesta"

        def _normalize_first_patient_turn(self, response, **kwargs):
            return response

    generator = FakeGenerator()

    assert module._activate_brain_v10_patch(generator) is True
    assert getattr(generator, "_brain_v10_llm_first", False) is True


def test_brain_v10_flags_stock_reentry_templates_as_code():
    module = load_bublee_module()
    brain = module._load_brain_v10_module()
    validator = brain.LLMResponseValidator()

    assert validator.is_template_response(
        "Gracias por contactarnos. Es un placer atenderte. Estoy aquí para ayudarte."
    ) is True


def test_patient_control_state_strips_fixed_templates():
    module = load_bublee_module()
    raw_state = {
        "enabled": True,
        "global": {
            "forbidden_phrases": [],
            "forbidden_starts": ["claro"],
            "replacement_map": {"ay": "entiendo"},
            "style_notes": [],
            "greeting_template": "",
            "second_bubble_template": "",
            "third_bubble_template": "",
            "closing_template": "",
            "fallback_template": "",
            "max_bubbles": 2,
            "register": "auto",
            "respectful": True,
            "no_emojis": True,
        },
        "patient": {
            "forbidden_phrases": [],
            "forbidden_starts": ["oye", "claro", "listo"],
            "replacement_map": {},
            "style_notes": [
                "Suena humana, clara y profesional.",
                "No suenes robótica ni demasiado explicativa.",
            ],
            "greeting_template": "Hola, soy Bublee, del equipo de {clinic_name}.",
            "second_bubble_template": "Te ayudo con información, valoración y disponibilidad.",
            "third_bubble_template": "",
            "closing_template": "",
            "fallback_template": "Perdón, no te entendí bien.",
            "max_bubbles": 2,
            "register": "tu",
            "respectful": True,
            "no_emojis": True,
        },
    }

    cleaned = module.sanitize_owner_style_control_state(raw_state)

    assert cleaned["patient"]["greeting_template"] == ""
    assert cleaned["patient"]["second_bubble_template"] == ""
    assert cleaned["patient"]["fallback_template"] == ""
    assert cleaned["patient"]["max_bubbles"] == 2
    assert cleaned["patient"]["register"] == "tu"


def test_admin_control_state_strips_stock_templates_and_noisy_notes():
    module = load_bublee_module()
    raw_state = {
        "enabled": True,
        "global": module.OwnerStyleController()._blank_bucket(),
        "admin": {
            "forbidden_phrases": [],
            "forbidden_starts": ["oye", "a ver", "mira"],
            "replacement_map": {},
            "style_notes": [
                "Con el admin habla con respeto, claridad y criterio.",
                'Conmigo no empieces con "oye',
                "No hables asi, soy tu admin",
            ],
            "greeting_template": "Hola, {admin_name}.",
            "second_bubble_template": "Estoy lista para ayudarle con la instancia, el tono, los servicios o las pruebas.",
            "third_bubble_template": "Si quieres, te ayudo a dejarlo encaminado ahora mismo",
            "closing_template": "",
            "fallback_template": "No me quedó claro todavía. Dígame exactamente qué ajuste quiere y lo hago.",
            "max_bubbles": 2,
            "register": "usted",
            "respectful": True,
            "no_emojis": True,
        },
        "patient": module.OwnerStyleController()._blank_bucket(register="tu"),
    }

    cleaned = module.sanitize_owner_style_control_state(raw_state)

    assert cleaned["admin"]["greeting_template"] == ""
    assert cleaned["admin"]["second_bubble_template"] == ""
    assert cleaned["admin"]["third_bubble_template"] == ""
    assert cleaned["admin"]["fallback_template"] == ""
    assert cleaned["admin"]["style_notes"] == [
        "Con el admin habla con respeto, claridad y criterio.",
    ]


def test_patient_prompt_filters_admin_only_trust_rules():
    module = load_bublee_module()
    rules = [
        {"rule": "No hables así, soy tu admin"},
        {"rule": "a los administradores háblales con respeto y más ejecutivo"},
        {"rule": "Si preguntan precio, responde eso primero"},
        {"rule": 'Cuando te digan hola, responde parecido a esto: "hola ||| dime"'},
    ]

    filtered = module.filter_trust_rules_for_audience(rules, is_admin=False)

    assert [item["rule"] for item in filtered] == [
        "Si preguntan precio, responde eso primero",
    ]


def test_core_memory_block_keeps_only_business_identity_signals():
    module = load_bublee_module()
    db = module.DatabaseManager(
        str(MODULE_PATH.parent / "bublee.db"),
        str(MODULE_PATH.parent / "vectors.db"),
    )

    block = db.get_core_memory_block()

    assert "clinic_name" in block
    assert "pricing_policy" in block
    assert "v8_prompt_evolutions" not in block
    assert "google_snapshot_text" not in block
    assert "v8_owner_style_control" not in block


def test_instance_workspace_context_block_reads_identity_soul_and_latest_memory():
    module = load_bublee_module()

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "identity").mkdir(parents=True, exist_ok=True)
        (root / "soul").mkdir(parents=True, exist_ok=True)
        (root / "memory").mkdir(parents=True, exist_ok=True)
        (root / "identity" / "IDENTITY.md").write_text(
            "# IDENTITY\n- negocio_actual: Nova\n- sector_actual: otro\n",
            encoding="utf-8",
        )
        (root / "soul" / "SOUL.md").write_text(
            "# SOUL\nNo inventes servicios heredados.\n",
            encoding="utf-8",
        )
        (root / "memory" / "20260411_120000_business_sync.md").write_text(
            "# MEMORY\n- resumen: Nova es infraestructura para preservar intención humana.\n",
            encoding="utf-8",
        )

        original_root = module._instance_runtime_root
        module._instance_runtime_root = lambda: root
        try:
            block = module._instance_workspace_context_block(max_chars=1200)
        finally:
            module._instance_runtime_root = original_root

    lowered = block.lower()
    assert "identidad operativa actual" in lowered
    assert "nova" in lowered
    assert "soul operativa" in lowered
    assert "memoria operativa reciente" in lowered


def test_uploaded_business_context_sync_replaces_legacy_clinic_identity():
    module = load_bublee_module()

    class FakeDB:
        def __init__(self):
            self.clinic = {
                "name": "Clinica de las americas",
                "tagline": "Clinica de las americas",
                "services": ["Botox", "Rellenos"],
                "sector": "estetica",
            }
            self.updated = {}
            self.memory = {}

        def get_clinic(self):
            return dict(self.clinic)

        def update_clinic(self, **kwargs):
            self.updated.update(kwargs)
            self.clinic.update(kwargs)

        def remember(self, key, value, category="identity"):
            self.memory[key] = value

        def recall(self, key):
            return self.memory.get(key, "")

    class FakeKB:
        def __init__(self):
            self.ingested = ""

        def ingest(self, raw_text):
            self.ingested = raw_text
            return {"ok": True}

    nova_context = """
    N O V A
    THE INTENT OPERATING SYSTEM

    Qué es Nova
    Nova no es un agente. Es el substrato de intención: la capa que captura,
    propaga, mide y protege lo que un humano quiso decir cuando configuró un agente.
    No vendemos botox ni tratamientos estéticos. Nova trabaja sobre agentes,
    WhatsApp, runtime, intent ledger y preservación de intención.
    """

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        instance_json = root / "instance.json"
        instance_json.write_text(
            '{"name":"clinica-de-las-americas","label":"Clinica de las americas","sector":"estetica","services":["Botox","Rellenos"]}',
            encoding="utf-8",
        )

        original_root = module._instance_runtime_root
        original_meta_path = module._instance_metadata_path
        original_db = module.db
        original_kb = module.kb
        original_brand = module._BRAND_ASSETS_AVAILABLE
        original_kb_available = module._KB_AVAILABLE
        original_llm = getattr(module, "llm_engine", None)
        fake_db = FakeDB()
        fake_kb = FakeKB()

        module._instance_runtime_root = lambda: root
        module._instance_metadata_path = lambda: instance_json
        module.db = fake_db
        module.kb = fake_kb
        module._BRAND_ASSETS_AVAILABLE = False
        module._KB_AVAILABLE = True
        module.llm_engine = None

        try:
            result = asyncio.run(
                module._sync_uploaded_business_context(
                    nova_context,
                    module.db.get_clinic(),
                    source="test_sync",
                )
            )
        finally:
            module._instance_runtime_root = original_root
            module._instance_metadata_path = original_meta_path
            module.db = original_db
            module.kb = original_kb
            module._BRAND_ASSETS_AVAILABLE = original_brand
            module._KB_AVAILABLE = original_kb_available
            module.llm_engine = original_llm

        assert result["ok"] is True
        assert fake_kb.ingested
        assert "nova" in fake_kb.ingested.lower()
        assert fake_db.updated["name"].lower().startswith("nova")
        assert fake_db.updated["sector"] == "otro"
        assert fake_db.updated["services"] == []
        assert (root / "identity" / "IDENTITY.md").exists()
        assert (root / "soul" / "SOUL.md").exists()
        assert list((root / "memory").glob("*.md"))

        synced_meta = module.json.loads(instance_json.read_text(encoding="utf-8"))
        assert synced_meta["label"].lower().startswith("nova")
        assert synced_meta["sector"] == "otro"
        assert synced_meta["services"] == []


def test_minimum_business_knowledge_does_not_force_ustedeo_with_patients():
    module = load_bublee_module()

    block = module._build_minimum_business_knowledge(
        {"name": "Clinica de las americas", "services": ["Botox"]}
    )

    lowered = block.lower()
    assert "trato de usted con pacientes" not in lowered
    assert "adapta el trato al tono del paciente" in lowered


def test_ensure_minimum_business_state_migrates_legacy_ustedeo_defaults():
    module = load_bublee_module()

    class FakeDB:
        def __init__(self):
            self.clinic = {
                "name": "Clinica de las americas",
                "services": ["Botox"],
                "schedule": {},
                "pricing": {},
                "platform": "telegram",
                "persona_config": {
                    "name": "Bublee",
                    "rol": "bot conversacional del equipo",
                    "registro": "usted",
                    "tone_instruction": (
                        "Hablas como Bublee, bot conversacional del equipo de la clínica en Colombia."
                    ),
                },
            }
            self.updated = {}

        def get_clinic(self):
            return self.clinic

        def update_clinic(self, **kwargs):
            self.updated.update(kwargs)
            self.clinic.update(kwargs)

        def recall(self, key):
            return ""

        def remember(self, *args, **kwargs):
            return None

    fake_db = FakeDB()
    module.db = fake_db
    module.kb = None
    module._KB_AVAILABLE = False
    module._BRAND_ASSETS_AVAILABLE = False

    result = module.ensure_minimum_business_state(force=False)

    assert result["ok"] is True
    persona = fake_db.updated["persona_config"]
    assert persona["registro"] == "auto"
    assert persona["rol"] == "asesora del equipo"
    assert "bot conversacional del equipo" not in persona.get("tone_instruction", "").lower()
    assert "tuteas de forma natural" in persona.get("tone_instruction", "").lower()


def test_patient_message_scope_routes_pure_meta_and_off_topic_outside_business_path():
    module = load_bublee_module()
    clinic = {"services": ["Botox", "Rellenos", "Láser"]}

    assert module._patient_message_scope("Eres un bot?", clinic) == (
        "meta",
        "Eres un bot?",
    )
    assert module._patient_message_scope("háblame de bitcoin", clinic) == (
        "off_topic",
        "háblame de bitcoin",
    )


def test_price_inquiry_does_not_force_external_search():
    module = load_bublee_module()
    analyzer = module.MessageAnalyzer()

    analysis = analyzer.analyze("hola, vi que tienen botox, cuánto sale eso", [])

    assert module._is_price_like_message("hola, vi que tienen botox, cuánto sale eso") is True
    assert analysis.requires_search is False


def test_llm_engine_loads_fourth_gemini_key_before_external_providers(monkeypatch):
    module = load_bublee_module()

    monkeypatch.setenv("GEMINI_API_KEY", "k1")
    monkeypatch.setenv("GEMINI_API_KEY_2", "k2")
    monkeypatch.setenv("GEMINI_API_KEY_3", "k3")
    monkeypatch.setenv("GEMINI_API_KEY_4", "k4")
    module.Config.OPENROUTER_API_KEY = "or"
    module.Config.OPENAI_API_KEY = "oa"
    module.Config.GROQ_API_KEY = "groq"

    engine = module.LLMEngine()

    assert [provider.name for provider in engine.providers[:4]] == [
        "gemini_k1",
        "gemini_k2",
        "gemini_k3",
        "gemini_k4",
    ]


def test_reasoning_uses_fast_tier_for_price_like_messages():
    module = load_bublee_module()
    engine = module.ReasoningEngine(llm=None)
    analysis = types.SimpleNamespace(
        intent=module.IntentType.GENERAL_QUESTION,
        requires_search=False,
    )

    tier = engine._select_model_tier(
        "o sea que no me pueden dar el precio",
        analysis,
        history=[{"role": "assistant", "content": "stub"}],
    )

    assert tier == "fast"


def test_google_requests_prefer_openrouter_and_openai_before_groq():
    module = load_bublee_module()
    engine = module.LLMEngine.__new__(module.LLMEngine)
    engine.providers = [
        types.SimpleNamespace(name="groq"),
        types.SimpleNamespace(name="gemini_k1"),
        types.SimpleNamespace(name="gemini_k2"),
        types.SimpleNamespace(name="openrouter"),
        types.SimpleNamespace(name="openai"),
    ]

    ordered = [p.name for p in module.LLMEngine._ordered_providers(engine, "google/gemini-2.5-pro")]

    assert ordered == ["gemini_k1", "gemini_k2", "openrouter", "openai", "groq"]


def test_llm_complete_reports_attempted_provider_chain_in_metadata():
    module = load_bublee_module()

    class FakeProvider:
        def __init__(self, name, response=None, error=None):
            self.name = name
            self._response = response
            self._error = error

        async def complete(self, *args, **kwargs):
            if self._error is not None:
                raise self._error
            return self._response, {"provider": self.name, "model": f"{self.name}-model", "latency_ms": 12}

    engine = module.LLMEngine.__new__(module.LLMEngine)
    engine.providers = [
        FakeProvider("gemini_k1", error=RuntimeError("boom")),
        FakeProvider("openrouter", response="ok desde openrouter"),
        FakeProvider("groq", response="ok desde groq"),
    ]
    engine._failures = {}
    engine._blocked_until = {}
    engine._blacklist_ttl = 60.0
    engine._cache = {}
    engine._cache_ttl = 300

    original_db = module.db
    module.db = None
    try:
        _, metadata = asyncio.run(
            module.LLMEngine.complete(
                engine,
                messages=[{"role": "user", "content": "hola"}],
                model_tier="fast",
                use_cache=False,
            )
        )
    finally:
        module.db = original_db

    assert metadata["provider"] == "openrouter"
    assert metadata["attempted_providers"] == ["gemini_k1", "openrouter"]


def test_gemini_pro_requests_retry_flash_before_external_fallbacks():
    module = load_bublee_module()

    class GeminiProbeProvider:
        def __init__(self):
            self.name = "gemini_k1"
            self.models = []

        async def complete(self, *args, **kwargs):
            model = kwargs.get("model")
            self.models.append(model)
            if model == "google/gemini-2.5-pro":
                raise RuntimeError("pro unavailable")
            return "respuesta desde flash", {"provider": self.name, "model": model, "latency_ms": 9}

    class FallbackProvider:
        def __init__(self, name):
            self.name = name
            self.calls = 0

        async def complete(self, *args, **kwargs):
            self.calls += 1
            return f"respuesta desde {self.name}", {"provider": self.name, "model": kwargs.get("model"), "latency_ms": 9}

    gemini = GeminiProbeProvider()
    openrouter = FallbackProvider("openrouter")
    groq = FallbackProvider("groq")

    engine = module.LLMEngine.__new__(module.LLMEngine)
    engine.providers = [gemini, openrouter, groq]
    engine._failures = {}
    engine._blocked_until = {}
    engine._blacklist_ttl = 60.0
    engine._cache = {}
    engine._cache_ttl = 300

    original_db = module.db
    module.db = None
    try:
        response, metadata = asyncio.run(
            module.LLMEngine.complete(
                engine,
                messages=[{"role": "user", "content": "necesito ayuda urgente con mi cita"}],
                model_tier="reasoning",
                use_cache=False,
            )
        )
    finally:
        module.db = original_db

    assert response == "respuesta desde flash"
    assert gemini.models == ["google/gemini-2.5-pro", "google/gemini-2.5-flash"]
    assert openrouter.calls == 0
    assert groq.calls == 0
    assert metadata["model"] == "google/gemini-2.5-flash"


def test_generate_keeps_fast_tier_for_price_like_turns_even_with_low_confidence():
    module = load_bublee_module()

    class FakeLLM:
        def __init__(self):
            self.tiers = []

        async def complete(self, *args, **kwargs):
            self.tiers.append(kwargs.get("model_tier"))
            return "No tengo ese dato exacto ahorita", {"model": "fake"}

    fake_llm = FakeLLM()
    generator = module.ResponseGenerator(llm=fake_llm)
    personality = generator._get_default_personality({"name": "Clinica de las americas"})

    asyncio.run(
        generator.generate(
            message="o sea que no me pueden dar el precio",
            analysis=types.SimpleNamespace(intent=module.IntentType.GENERAL_QUESTION),
            reasoning={"confidence": 0.2, "response_strategy": "responder precio primero"},
            clinic={"name": "Clinica de las americas", "sector": "estetica"},
            patient={"is_new": False, "visits": 2},
            history=[{"role": "assistant", "content": "El valor depende de la valoración"}],
            search_context="",
            personality=personality,
            kb_context="",
            chat_id="price_generate_tier_probe",
        )
    )

    assert fake_llm.tiers[0] == "fast"


def test_admin_inbox_query_detects_cliente_te_ha_escrito_variants():
    module = load_bublee_module()

    assert module._is_admin_inbox_query("Holaaa bublee algun cliente te ha escrito?") is True
    assert module._is_admin_inbox_query("Bublee quién te ha escrito") is True
    assert module._is_admin_inbox_query("quien te escribió hoy") is True
    assert module._is_admin_inbox_query("Una disculap, te hago una pregunta quien ha escrito") is True
    assert module._is_admin_inbox_query("qué chats tienes") is True
    assert module._is_admin_inbox_query("hay conversaciones?") is True
    assert module._is_admin_inbox_query("han escrito hoy o estás sola") is True
    assert module._is_admin_inbox_query("quiero ajustar el tono") is False


def test_admin_recent_chat_followup_query_detects_natural_variants():
    module = load_bublee_module()

    assert module._is_admin_recent_chat_followup_query("Y que han hablado") is True
    assert module._is_admin_recent_chat_followup_query("y de qué hablaron") is True
    assert module._is_admin_recent_chat_followup_query("q hablaron") is True
    assert module._is_admin_recent_chat_followup_query("q te han dicho") is True
    assert module._is_admin_recent_chat_followup_query("quiero ajustar el tono") is False


def test_admin_recent_chat_context_followup_detects_anaphoric_variants():
    module = load_bublee_module()

    assert module._is_admin_recent_chat_context_followup("y luego") is True
    assert module._is_admin_recent_chat_context_followup("q t han dicho") is True
    assert module._is_admin_recent_chat_context_followup("cómo quedó eso") is True
    assert module._is_admin_recent_chat_context_followup("quiero ajustar el tono") is False


def test_owner_style_control_ignores_recent_chat_transcript_requests():
    module = load_bublee_module()
    controller = module.OwnerStyleController()

    assert controller.detect_control_intent("muestrame los ultimos 3 mensajes de cada uno") is False
    assert controller.detect_control_intent("muéstrame los últimos 3 mensajes de cada chat") is False
    assert controller.detect_control_intent("responde en 3 mensajes") is True


def test_admin_natural_command_handles_recent_chat_followup_without_llm():
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._admin_pending = {
        "6908159885": {
            "action": "recent_chats_snapshot",
            "latest_chat_id": "6437195704",
            "ts": module.time.time(),
        }
    }
    bublee._pending_buffers = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}

    async def should_not_run(*args, **kwargs):
        raise AssertionError("admin LLM no debería usarse en este seguimiento")

    bublee._admin_llm_brain = should_not_run
    module.owner_style_controller = None
    module.trainer_gateway = None
    module.prompt_evolver = None
    module.anti_robot_filter = None
    saved_messages = []
    module.db = types.SimpleNamespace(
        get_admin=lambda chat_id: {"name": "Santiago"},
        get_history=lambda chat_id, limit=8: [
            {
                "role": "assistant",
                "content": "Me ha escrito 1 chat real en esta instancia. ||| El último que veo es un chat sin nombre guardado.",
            }
        ],
        get_patient_conversation=lambda chat_id, limit=8: [
            {
                "role": "user",
                "content": "Hola buenas noches, se que son las 3 am pero a qué precio tienen el botox",
            },
            {
                "role": "assistant",
                "content": "No tengo un precio exacto para el bótox en este momento ||| El valor final depende de una valoración inicial y de las zonas específicas a tratar",
            },
            {
                "role": "user",
                "content": "Pero un aproximado cuánto podría ser?",
            },
        ],
        get_patient=lambda chat_id: {},
        save_message=lambda chat_id, role, content: saved_messages.append((chat_id, role, content)),
    )

    reply = asyncio.run(
        bublee._admin_natural_command(
            "6908159885",
            "Y que han hablado",
            {"name": "Clinica de las americas", "admin_chat_ids": ["6908159885"]},
        )
    )

    merged = " ".join(reply).lower()
    assert "botox" in merged or "bótox" in merged
    assert "precio" in merged
    assert "cuénteme qué quiere ajustar" not in merged
    assert saved_messages


def test_admin_natural_command_uses_recent_chat_context_followup_without_llm():
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._admin_pending = {
        "6908159885": {
            "action": "recent_chats_snapshot",
            "latest_chat_id": "6437195704",
            "ts": module.time.time(),
        }
    }
    bublee._pending_buffers = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}

    async def should_not_run(*args, **kwargs):
        raise AssertionError("admin LLM no debería usarse en follow-up anafórico")

    bublee._admin_llm_brain = should_not_run
    module.owner_style_controller = module.OwnerStyleController()
    module.trainer_gateway = None
    module.prompt_evolver = None
    module.anti_robot_filter = None
    saved_messages = []
    module.db = types.SimpleNamespace(
        get_admin=lambda chat_id: {"name": "Santiago"},
        get_history=lambda chat_id, limit=8: [],
        get_patient_conversation=lambda chat_id, limit=8: [
            {"role": "user", "content": "hola, vi botox y quiero saber el precio"},
            {"role": "assistant", "content": "Te cuento cómo se maneja y qué zona te interesa"},
            {"role": "user", "content": "la frente y patas de gallo"},
        ],
        get_patient=lambda chat_id: {"name": "Laura"},
        save_message=lambda chat_id, role, content: saved_messages.append((chat_id, role, content)),
    )

    reply = asyncio.run(
        bublee._admin_natural_command(
            "6908159885",
            "y luego",
            {"name": "Clinica de las americas", "admin_chat_ids": ["6908159885"]},
        )
    )

    merged = " ".join(reply).lower()
    assert "laura" in merged or "ese chat" in merged
    assert "botox" in merged
    assert saved_messages


def test_admin_natural_command_handles_shorthand_recent_chat_followup_without_llm():
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._admin_pending = {}
    bublee._pending_buffers = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}

    async def should_not_run(*args, **kwargs):
        raise AssertionError("admin LLM no debería usarse en follow-up shorthand")

    bublee._admin_llm_brain = should_not_run
    module.owner_style_controller = module.OwnerStyleController()
    module.trainer_gateway = None
    module.prompt_evolver = None
    module.anti_robot_filter = None
    saved_messages = []
    module.db = types.SimpleNamespace(
        get_admin=lambda chat_id: {"name": "Santiago"},
        get_history=lambda chat_id, limit=8: [],
        get_recent_patient_chats=lambda limit=10: [
            {"chat_id": "6437195704", "name": "Laura"},
            {"chat_id": "3015559999", "name": "Camilo"},
        ],
        get_patient_conversation=lambda chat_id, limit=8: [
            {"role": "user", "content": "hola, vi botox y quiero saber el precio"},
            {"role": "assistant", "content": "Te cuento cómo se maneja y qué zona te interesa"},
            {"role": "user", "content": "la frente y patas de gallo"},
        ],
        get_patient=lambda chat_id: {"name": "Laura"},
        save_message=lambda chat_id, role, content: saved_messages.append((chat_id, role, content)),
    )

    reply = asyncio.run(
        bublee._admin_natural_command(
            "6908159885",
            "q te han dicho",
            {"name": "Clinica de las americas", "admin_chat_ids": ["6908159885"]},
        )
    )

    merged = " ".join(reply).lower()
    assert "laura" in merged or "ese chat" in merged
    assert "botox" in merged
    assert "quedó aplicado" not in merged
    assert saved_messages


def test_admin_natural_command_handles_recent_chat_transcript_request_without_control_hijack():
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._admin_pending = {
        "6908159885": {
            "action": "recent_chats_snapshot",
            "latest_chat_id": "6437195704",
            "ts": module.time.time(),
        }
    }
    bublee._pending_buffers = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}

    async def should_not_run(*args, **kwargs):
        raise AssertionError("admin LLM no debería usarse en este transcript")

    bublee._admin_llm_brain = should_not_run
    module.owner_style_controller = module.OwnerStyleController()
    module.trainer_gateway = None
    module.prompt_evolver = None
    module.anti_robot_filter = None
    saved_messages = []

    conversations = {
        "6437195704": [
            {"role": "user", "content": "hola, vi botox y quiero saber el precio"},
            {"role": "assistant", "content": "Te cuento cómo se maneja y qué zona te interesa"},
            {"role": "user", "content": "la frente y patas de gallo"},
        ],
        "3015559999": [
            {"role": "user", "content": "quiero cita el jueves"},
            {"role": "assistant", "content": "Te confirmo horario en la tarde"},
            {"role": "user", "content": "me sirve después de las 3"},
        ],
    }

    module.db = types.SimpleNamespace(
        get_admin=lambda chat_id: {"name": "Santiago"},
        get_history=lambda chat_id, limit=8: [
            {
                "role": "assistant",
                "content": "Sí, hay 6 conversaciones. Las más recientes aún no tienen nombre guardado.",
            }
        ],
        get_recent_patient_chats=lambda limit=10: [
            {"chat_id": "6437195704", "name": "Laura"},
            {"chat_id": "3015559999", "name": "Camilo"},
        ],
        get_patient_conversation=lambda chat_id, limit=30: conversations.get(chat_id, []),
        get_patient=lambda chat_id: {"name": "Laura" if chat_id == "6437195704" else "Camilo"},
        save_message=lambda chat_id, role, content: saved_messages.append((chat_id, role, content)),
    )

    reply = asyncio.run(
        bublee._admin_natural_command(
            "6908159885",
            "muestrame los ultimos 3 mensajes de cada uno",
            {"name": "Clinica de las americas", "admin_chat_ids": ["6908159885"]},
        )
    )

    merged = " ".join(reply).lower()
    assert "laura" in merged
    assert "camilo" in merged
    assert "botox" in merged
    assert "jueves" in merged
    assert "quedó aplicado" not in merged
    assert saved_messages


def test_admin_natural_command_handles_recent_chat_transcript_without_snapshot_context():
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._admin_pending = {}
    bublee._pending_buffers = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}

    async def should_not_run(*args, **kwargs):
        raise AssertionError("admin LLM no debería usarse en este transcript sin contexto previo")

    bublee._admin_llm_brain = should_not_run
    module.owner_style_controller = module.OwnerStyleController()
    module.trainer_gateway = None
    module.prompt_evolver = None
    module.anti_robot_filter = None
    saved_messages = []

    conversations = {
        "6437195704": [
            {"role": "user", "content": "hola, vi botox y quiero saber el precio"},
            {"role": "assistant", "content": "Te cuento cómo se maneja y qué zona te interesa"},
            {"role": "user", "content": "la frente y patas de gallo"},
        ],
        "3015559999": [
            {"role": "user", "content": "quiero cita el jueves"},
            {"role": "assistant", "content": "Te confirmo horario en la tarde"},
            {"role": "user", "content": "me sirve después de las 3"},
        ],
    }

    module.db = types.SimpleNamespace(
        get_admin=lambda chat_id: {"name": "Santiago"},
        get_history=lambda chat_id, limit=8: [],
        get_recent_patient_chats=lambda limit=10: [
            {"chat_id": "6437195704", "name": "Laura"},
            {"chat_id": "3015559999", "name": "Camilo"},
        ],
        get_patient_conversation=lambda chat_id, limit=30: conversations.get(chat_id, []),
        get_patient=lambda chat_id: {"name": "Laura" if chat_id == "6437195704" else "Camilo"},
        save_message=lambda chat_id, role, content: saved_messages.append((chat_id, role, content)),
    )

    reply = asyncio.run(
        bublee._admin_natural_command(
            "6908159885",
            "ue has hablado? muestrame los ultimos 3 mensajes de cada uno",
            {"name": "Clinica de las americas", "admin_chat_ids": ["6908159885"]},
        )
    )

    merged = " ".join(reply).lower()
    assert "laura" in merged
    assert "camilo" in merged
    assert "quedó aplicado" not in merged
    assert saved_messages


def test_admin_greeting_prefers_llm_before_local_fallback():
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._admin_pending = {}
    bublee._pending_buffers = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}

    async def fake_brain(*args, **kwargs):
        return {
            "reply": "Todo bien. Qué quieres revisar hoy?",
            "action": "none",
            "data": {},
        }

    async def fake_apply_action(*args, **kwargs):
        return True

    bublee._admin_llm_brain = fake_brain
    bublee._admin_apply_action = fake_apply_action
    module.owner_style_controller = None
    module.trainer_gateway = None
    module.prompt_evolver = None
    module.anti_robot_filter = None
    module.db = types.SimpleNamespace(
        get_admin=lambda chat_id: {"name": "Santiago"},
        get_history=lambda chat_id, limit=8: [],
        save_message=lambda *args, **kwargs: None,
    )

    reply = asyncio.run(
        bublee._admin_natural_command(
            "6908159885",
            "como estas",
            {"name": "Clinica de las americas", "admin_chat_ids": ["6908159885"]},
        )
    )

    merged = " ".join(reply).lower()
    assert "todo bien" in merged
    assert "bien, gracias" not in merged


def test_admin_brain_prompt_asks_model_to_pivot_after_out_of_scope_turn():
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    captured = {}

    class FakeLLM:
        async def complete(self, messages, **kwargs):
            captured["system"] = messages[0]["content"]
            return '{"reply":"Todo bien.","action":"none","data":{}}', {"model": "fake"}

    old_llm = module.llm_engine
    module.llm_engine = FakeLLM()
    module.owner_style_controller = None
    module.skill_engine = None
    module.bus = None
    module.db = types.SimpleNamespace(
        get_admin=lambda chat_id: {"name": "Santiago"},
    )

    try:
        asyncio.run(
            bublee._admin_llm_brain(
                "6908159885",
                "quien ha escrito",
                [{"role": "user", "content": "ponme one day de dua lipa en yt de la tv"}],
                {"name": "Clinica de las americas", "sector": "estetica"},
                "Bublee",
            )
        )
    finally:
        module.llm_engine = old_llm

    system_prompt = captured["system"].lower()
    assert "no uses frases como" in system_prompt
    assert "mi función es" in system_prompt or "mi funcion es" in system_prompt
    assert "si el dueño cambia de tema" in system_prompt


def test_admin_brain_prompt_avoids_scripted_dialogue_examples():
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    captured = {}

    class FakeLLM:
        async def complete(self, messages, **kwargs):
            captured["system"] = messages[0]["content"]
            return '{"reply":"Entendido.","action":"none","data":{}}', {"model": "fake"}

    old_llm = module.llm_engine
    module.llm_engine = FakeLLM()
    module.owner_style_controller = None
    module.skill_engine = None
    module.bus = None
    module.db = types.SimpleNamespace(
        get_admin=lambda chat_id: {"name": "Santiago"},
    )

    try:
        asyncio.run(
            bublee._admin_llm_brain(
                "6908159885",
                "hola",
                [],
                {"name": "Clinica de las americas", "sector": "estetica"},
                "Bublee",
            )
        )
    finally:
        module.llm_engine = old_llm

    system_prompt = captured["system"].lower()
    assert "así hablas con el dueño" not in system_prompt
    assert "ponme one day de dua lipa" not in system_prompt
    assert "hola, santiago. estoy lista." not in system_prompt


def test_admin_natural_command_uses_minimal_outage_fallback_for_generic_chat():
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._admin_pending = {}
    bublee._pending_buffers = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}

    async def broken_brain(*args, **kwargs):
        return None

    bublee._admin_llm_brain = broken_brain
    module.owner_style_controller = None
    module.trainer_gateway = None
    module.prompt_evolver = None
    module.anti_robot_filter = None
    module.db = types.SimpleNamespace(
        get_admin=lambda chat_id: {"name": "Santiago"},
        get_history=lambda chat_id, limit=8: [],
        save_message=lambda *args, **kwargs: None,
    )

    reply = asyncio.run(
        bublee._admin_natural_command(
            "6908159885",
            "hola",
            {"name": "Clinica de las americas", "admin_chat_ids": ["6908159885"]},
        )
    )

    merged = " ".join(reply).lower()
    assert "se me cayó" in merged or "caida" in merged or "caída" in merged
    assert "estoy lista para ayudarte" not in merged
    assert "cuénteme qué quiere ajustar" not in merged


def test_admin_local_fallback_keeps_deterministic_chat_snapshot_route():
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._admin_pending = {}
    bublee._pending_buffers = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}

    module.db = types.SimpleNamespace(
        get_admin=lambda chat_id: {"name": "Santiago"},
        _conn=lambda: None,
    )
    bublee._admin_recent_chat_snapshot = lambda chat_id, clinic: [
        "Veo 2 chats reales en esta instancia.",
        "Los más recientes son Laura y Camilo.",
    ]
    bublee._admin_has_recent_chat_snapshot_context = lambda chat_id: False

    reply = bublee._admin_local_fallback(
        "hay conversaciones?",
        "hay conversaciones?",
        {"name": "Clinica de las americas", "admin_chat_ids": ["6908159885"]},
        "Bublee",
        "6908159885",
    )

    merged = " ".join(reply).lower()
    assert "2 chats reales" in merged
    assert "laura" in merged


def test_admin_local_fallback_uses_synced_business_context_for_owner_questions():
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._admin_pending = {}
    bublee._pending_buffers = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}

    module.db = types.SimpleNamespace(
        get_admin=lambda chat_id: {"name": "Santiago"},
    )

    clinic = {
        "name": "Nova",
        "sector": "otro",
        "services": [],
        "knowledge_base_raw": (
            "Negocio oficial actual: Nova\n"
            "Sector operativo actual: otro\n"
            "Resumen oficial: Nova es una capa para preservar intención humana en agentes.\n"
            "Oferta/servicios actuales: todavía no hay una lista cerrada; no inventes catálogo."
        ),
    }

    reply = bublee._admin_local_fallback(
        "Te acabo de mandar un txt con el negocio real. Que es Nova y por qué me pediste ese archivo?",
        "te acabo de mandar un txt con el negocio real. que es nova y por qué me pediste ese archivo?",
        clinic,
        "Bublee",
        "6908159885",
    )

    merged = " ".join(reply).lower()
    assert "nova" in merged
    assert "preservar intención humana" in " ".join(reply).lower() or "preservar intencion humana" in merged
    assert "branding heredado" in merged or "identidad real" in merged
    assert "botox" not in merged


def test_admin_local_fallback_explains_pdf_and_memory_capability():
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._admin_pending = {}
    bublee._pending_buffers = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}

    module.db = types.SimpleNamespace(
        get_admin=lambda chat_id: {"name": "Santiago"},
    )

    clinic = {
        "name": "Nova",
        "sector": "otro",
        "services": [],
        "knowledge_base_raw": (
            "Negocio oficial actual: Nova\n"
            "Resumen oficial: Nova es una capa para preservar intención humana.\n"
            "Oferta/servicios actuales: todavía no hay una lista cerrada; no inventes catálogo."
        ),
    }

    reply = bublee._admin_local_fallback(
        "puedes leer pdfs y guardar memoria?",
        "puedes leer pdfs y guardar memoria?",
        clinic,
        "Bublee",
        "6908159885",
    )

    merged = " ".join(reply).lower()
    assert "pdf" in merged
    assert "identity/" in " ".join(reply) or "memory/" in " ".join(reply) or "soul/" in " ".join(reply)


def test_admin_llm_brain_recovers_reply_from_malformed_json():
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)

    class FakeLLM:
        async def complete(self, *args, **kwargs):
            return (
                '{"reply":"Nova es una capa para preservar intención humana","action":"none","data":{',
                {"provider": "fake", "model": "fake"},
            )

    module.llm_engine = FakeLLM()
    module.db = types.SimpleNamespace(get_admin=lambda chat_id: {"name": "Santiago"})
    module.skill_engine = None
    module.bus = None
    module.owner_style_controller = None

    result = asyncio.run(
        bublee._admin_llm_brain(
            "6908159885",
            "De que trata nova?",
            [],
            {
                "name": "Nova",
                "sector": "otro",
                "services": [],
                "knowledge_base_raw": "Resumen oficial: Nova es una capa para preservar intención humana.",
            },
            "Bublee",
        )
    )

    assert isinstance(result, dict)
    assert result["action"] == "none"
    assert "Nova es una capa para preservar intención humana" in result["reply"]


def test_admin_natural_command_keeps_reply_when_history_save_fails():
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._admin_pending = {}
    bublee._pending_buffers = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}

    async def fake_brain(*args, **kwargs):
        return {
            "reply": "Todo bien. Qué quieres revisar hoy?",
            "action": "none",
            "data": {},
        }

    async def fake_apply_action(*args, **kwargs):
        return True

    def failing_save(*args, **kwargs):
        raise sqlite3.OperationalError("database or disk is full")

    bublee._admin_llm_brain = fake_brain
    bublee._admin_apply_action = fake_apply_action
    module.owner_style_controller = None
    module.trainer_gateway = None
    module.prompt_evolver = None
    module.anti_robot_filter = None
    module.db = types.SimpleNamespace(
        get_admin=lambda chat_id: {"name": "Santiago"},
        get_history=lambda chat_id, limit=8: [],
        save_message=failing_save,
    )

    reply = asyncio.run(
        bublee._admin_natural_command(
            "6908159885",
            "hola buenos dias",
            {"name": "Clinica de las americas", "admin_chat_ids": ["6908159885"]},
        )
    )

    merged = " ".join(reply).lower()
    assert "todo bien" in merged
    assert "algo salió mal" not in merged


def test_admin_natural_command_bypasses_llm_for_synced_business_context():
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._admin_pending = {}
    bublee._pending_buffers = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}

    async def failing_brain(*args, **kwargs):
        raise AssertionError("el handler admin no debía consultar el brain para contexto oficial")

    bublee._admin_llm_brain = failing_brain
    module.owner_style_controller = None
    module.trainer_gateway = None
    module.prompt_evolver = None
    module.anti_robot_filter = None
    module.db = types.SimpleNamespace(
        get_admin=lambda chat_id: {"name": "Santiago"},
        get_history=lambda chat_id, limit=8: [],
        save_message=lambda *args, **kwargs: None,
    )

    reply = asyncio.run(
        bublee._admin_natural_command(
            "6908159885",
            "Te acabo de mandar un txt con el negocio real. Que es Nova y por qué me pediste ese archivo?",
            {
                "name": "Nova",
                "sector": "otro",
                "services": [],
                "knowledge_base_raw": (
                    "Negocio oficial actual: Nova\n"
                    "Resumen oficial: Nova es una capa para preservar intención humana.\n"
                    "Oferta/servicios actuales: todavía no hay una lista cerrada; no inventes catálogo."
                ),
                "admin_chat_ids": ["6908159885"],
            },
        )
    )

    merged = " ".join(reply).lower()
    assert "nova" in merged
    assert "branding heredado" in merged or "identidad real" in merged
    assert "botox" not in merged


def test_admin_natural_command_prioritizes_conversational_business_override_and_asks_onboarding():
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._admin_pending = {}
    bublee._pending_buffers = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}

    async def failing_brain(*args, **kwargs):
        raise AssertionError("el brain admin no debía correr cuando hay override conversacional explícito")

    class FakeLLM:
        async def complete(self, *args, **kwargs):
            return (
                "¿A qué tipo de empresa le vendes primero: bancos medianos, fintechs o equipos que ya tienen agentes en producción?",
                {"provider": "fake", "model": "fake"},
            )

    class FakeDB:
        def __init__(self):
            self.state = module._empty_conversation_state("6908159885")

        def get_admin(self, chat_id):
            return {"name": "Santiago"}

        def get_history(self, chat_id, limit=8):
            return []

        def save_message(self, *args, **kwargs):
            return None

        def get_conversation_state(self, chat_id):
            return self.state

        def save_conversation_state(self, state):
            self.state = state

    fake_db = FakeDB()

    bublee._admin_llm_brain = failing_brain
    module.llm_engine = FakeLLM()
    module.owner_style_controller = None
    module.trainer_gateway = None
    module.prompt_evolver = None
    module.anti_robot_filter = None
    module.db = fake_db

    reply = asyncio.run(
        bublee._admin_natural_command(
            "6908159885",
            "Ya dejé Nova como negocio activo. Nova es una plataforma de gobernanza de intención para agentes de IA en bancos.",
            {
                "name": "Clinica de las americas",
                "sector": "estetica",
                "services": ["Botox", "Rellenos"],
                "admin_chat_ids": ["6908159885"],
            },
        )
    )

    merged = " ".join(reply).lower()
    override = fake_db.state.collected_data["business_override"]
    assert "bancos medianos" in merged or "tipo de empresa" in merged or "cliente" in merged
    assert "ya dejé" not in merged
    assert "botox" not in merged
    assert override["context_source"] == "conversational"
    assert override["business_name"].lower().startswith("nova")
    assert override["services"] == []


def test_admin_local_fallback_prefers_chat_business_override_over_legacy_clinic():
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._admin_pending = {}
    bublee._pending_buffers = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}

    fake_state = module._empty_conversation_state("6908159885")
    fake_state.collected_data["business_override"] = {
        "context_source": "conversational",
        "business_name": "Nova",
        "sector": "otro",
        "summary": "Nova es una plataforma de gobernanza de intención para agentes de IA en bancos.",
        "raw_context": "Nova es una plataforma de gobernanza de intención para agentes de IA en bancos.",
        "services": [],
        "onboarding_answers": {"problem": "present"},
        "onboarding_asked": ["icp"],
        "confirmed": False,
    }

    module.db = types.SimpleNamespace(
        get_admin=lambda chat_id: {"name": "Santiago"},
        get_conversation_state=lambda chat_id: fake_state,
    )

    reply = bublee._admin_local_fallback(
        "De que trata nova?",
        "de que trata nova?",
        {
            "name": "Clinica de las americas",
            "sector": "estetica",
            "services": ["Botox", "Rellenos"],
        },
        "Bublee",
        "6908159885",
    )

    merged = " ".join(reply).lower()
    assert "nova" in merged
    assert "gobernanza de intención" in " ".join(reply).lower() or "gobernanza de intencion" in merged
    assert "botox" not in merged


def test_admin_business_onboarding_advances_to_next_gap_without_resetting_same_business():
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._admin_pending = {}
    bublee._pending_buffers = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}

    class FakeDB:
        def __init__(self):
            self.state = module._empty_conversation_state("6908159885")

        def get_conversation_state(self, chat_id):
            return self.state

        def save_conversation_state(self, state):
            self.state = state

        def get_admin(self, chat_id):
            return {"name": "Santiago"}

        def get_history(self, chat_id, limit=8):
            return []

        def save_message(self, *args, **kwargs):
            return None

    class FakeLLM:
        def __init__(self):
            self.calls = 0

        async def complete(self, *args, **kwargs):
            self.calls += 1
            if self.calls == 1:
                return ("¿A qué tipo de cliente le vendes primero?", {"provider": "fake", "model": "fake"})
            if self.calls == 2:
                return ("¿Qué problema resuelven en una frase?", {"provider": "fake", "model": "fake"})
            return ("¿Hoy por dónde les llegan los prospectos?", {"provider": "fake", "model": "fake"})

    fake_db = FakeDB()
    fake_llm = FakeLLM()

    module.db = fake_db
    module.llm_engine = fake_llm
    module.owner_style_controller = None
    module.trainer_gateway = None
    module.prompt_evolver = None
    module.anti_robot_filter = None

    first = asyncio.run(
        bublee._admin_natural_command(
            "6908159885",
            "Ya dejé Nova como negocio activo. Nova es una plataforma de gobernanza de intención para agentes de IA en bancos.",
            {"name": "Clinica de las americas", "sector": "estetica", "services": ["Botox"], "admin_chat_ids": ["6908159885"]},
        )
    )
    second = asyncio.run(
        bublee._admin_natural_command(
            "6908159885",
            "Le vendemos primero a bancos medianos y fintechs que ya tienen agentes en producción. El ticket promedio arranca en 20 mil dólares al año.",
            {"name": "Clinica de las americas", "sector": "estetica", "services": ["Botox"], "admin_chat_ids": ["6908159885"]},
        )
    )

    first_text = " ".join(first).lower()
    second_text = " ".join(second).lower()
    override = fake_db.state.collected_data["business_override"]

    assert "tipo de cliente" in first_text or "cliente" in first_text
    assert any(token in second_text for token in ("objec", "ponen", "prospect", "llegan", "canal"))
    assert "tipo de cliente" not in second_text
    assert override["business_name"].lower().startswith("nova")
    assert "icp" in override["onboarding_answers"]


def test_admin_business_onboarding_can_summarize_learned_context_instead_of_reasking(monkeypatch):
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._admin_pending = {}
    bublee._pending_buffers = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}

    class FakeDB:
        def __init__(self):
            self.state = module._empty_conversation_state("6908159885")

        def get_conversation_state(self, chat_id):
            return self.state

        def save_conversation_state(self, state):
            self.state = state

        def get_admin(self, chat_id):
            return {"name": "Santiago"}

        def get_history(self, chat_id, limit=8):
            return []

        def save_message(self, *args, **kwargs):
            return None

    class FakeLLM:
        def __init__(self):
            self.calls = 0

        async def complete(self, *args, **kwargs):
            self.calls += 1
            if self.calls == 1:
                return ("¿A qué tipo de cliente le vendes primero?", {"provider": "fake", "model": "fake"})
            if self.calls == 2:
                return ("¿Cuál es el ticket promedio o el precio de entrada?", {"provider": "fake", "model": "fake"})
            return ("¿Qué problema resuelven en una frase?", {"provider": "fake", "model": "fake"})

    fake_db = FakeDB()
    fake_llm = FakeLLM()

    module.db = fake_db
    module.llm_engine = fake_llm
    module.owner_style_controller = None
    module.trainer_gateway = None
    module.prompt_evolver = None
    module.anti_robot_filter = None

    clinic = {"name": "Clinica de las americas", "sector": "estetica", "services": ["Botox"], "admin_chat_ids": ["6908159885"]}

    asyncio.run(
        bublee._admin_natural_command(
            "6908159885",
            "Ya dejé Nova como negocio activo. Nova es una plataforma de gobernanza de intención para agentes de IA en bancos.",
            clinic,
        )
    )
    asyncio.run(
        bublee._admin_natural_command(
            "6908159885",
            "Le vendemos primero a bancos medianos y fintechs que ya tienen agentes en producción.",
            clinic,
        )
    )
    summary = asyncio.run(
        bublee._admin_natural_command(
            "6908159885",
            "¿qué sabes de Nova hasta ahora?",
            clinic,
        )
    )

    lowered = " ".join(summary).lower()
    assert "tengo nova" in lowered
    assert "cliente objetivo" in lowered
    assert "ticket" in lowered or "precio" in lowered
    assert "me falta" in lowered
    assert "?" not in lowered


def test_health_prefers_clinic_sector_over_stale_config():
    module = load_bublee_module()
    module.db = types.SimpleNamespace(
        get_clinic=lambda: {"name": "Nova", "sector": "otro", "setup_done": True},
        recall=lambda key: "",
        recall_all=lambda: [],
    )
    module.bublee = types.SimpleNamespace(_pending_buffers={})
    module.mcp_manager = None
    module.Config.SECTOR = "estetica"
    module.Config.WHATSAPP_BRIDGE_URL = ""
    module.Config.TELEGRAM_SHARED_ROUTER = False

    payload = asyncio.run(module.health())

    assert payload["clinic"] == "Nova"
    assert payload["sector"] == "otro"


def test_admin_output_pipeline_strips_dangling_trailing_quote():
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    module.owner_style_controller = None
    module.db = types.SimpleNamespace(get_history=lambda chat_id, limit=8: [])

    cleaned = bublee._apply_admin_output_pipeline(
        'Comprendo. Estoy atenta para cualquier configuración o prueba de los servicios que requiera."',
        "6908159885",
        {"name": "Clinica de las americas"},
        user_msg="estoy probando a ver si te sales de contexto",
    )

    assert not cleaned.endswith('"')
    assert "requiera" in cleaned


def test_patient_message_scope_routes_identity_question_to_meta():
    module = load_bublee_module()

    scope, effective = module._patient_message_scope(
        "eres bot o qué",
        {"name": "Clinica de las americas", "services": ["Botox"]},
    )

    assert scope == "meta"
    assert effective == "eres bot o qué"


def test_calendar_admin_notification_uses_direct_human_copy():
    module = load_bublee_module()
    bridge = module.CalendarBridge()
    sent = []

    async def fake_send(chat_id, message, *args, **kwargs):
        sent.append((chat_id, message))

    asyncio.run(
        bridge.notify_admin_availability_request(
            ["admin_1"],
            "Laura",
            "Hola buenas tardes",
            fake_send,
        )
    )

    assert sent
    _, message = sent[0]
    lowered = message.lower()
    assert "te paso una consulta de disponibilidad" in lowered
    assert "no tengo la agenda conectada" in lowered
    assert "hola!" not in lowered


def test_calendar_admin_notification_skips_probe_ids_when_real_admin_exists():
    module = load_bublee_module()
    bridge = module.CalendarBridge()
    sent = []

    async def fake_send(chat_id, message, *args, **kwargs):
        sent.append((chat_id, message))

    asyncio.run(
        bridge.notify_admin_availability_request(
            ["6908159885", "admin_probe_20260328_real", "admin_control_20260328"],
            "Laura",
            "Tienen algo para el jueves?",
            fake_send,
        )
    )

    assert [chat_id for chat_id, _ in sent] == ["6908159885"]


def test_patient_acknowledgement_closes_without_repeating_previous_price_handoff():
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._pending_buffers = {}
    bublee._admin_pending = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}

    class FakeAnalyzer:
        def analyze(self, text, history):
            return types.SimpleNamespace(
                language="es",
                urgency=module.UrgencyLevel.LOW,
                intent=module.IntentType.GENERAL_QUESTION,
                requires_search=False,
                closing_score=0.0,
                lead_temperature="warm",
            )

    class FakeReasoning:
        async def reason(self, *args, **kwargs):
            return {}

    class FakeGenerator:
        def _get_default_personality(self, clinic):
            return types.SimpleNamespace(archetype="amigable")

        def _apply_output_pipeline(self, response, **kwargs):
            return response

        def _repair_fragmented_response(self, response, **kwargs):
            return response

        def get_last_response_metadata(self):
            return {}

        async def generate(self, *args, **kwargs):
            raise AssertionError("no debería llamar al generator para un agradecimiento simple")

    bublee.analyzer = FakeAnalyzer()
    bublee.reasoning = FakeReasoning()
    bublee.generator = FakeGenerator()
    module.db = types.SimpleNamespace(
        get_clinic=lambda: {
            "name": "Clinica de las americas",
            "sector": "estetica",
            "setup_done": 1,
            "admin_chat_ids": ["admin_1"],
            "pricing": {},
            "services": ["Botox"],
            "schedule": {"General": "Lunes a sábado de 9 a.m. a 7 p.m."},
        },
        get_admin=lambda chat_id: None,
        get_or_create_patient=lambda chat_id: {"is_new": False, "name": "Laura"},
        get_history=lambda chat_id, limit=None: [
            {"role": "assistant", "content": "No tengo un aproximado confiable aquí en este momento. ||| Si quieres, lo consulto con el equipo y te confirmo apenas me respondan."}
        ],
        get_conversation_state=lambda chat_id: types.SimpleNamespace(turn_count=1, last_intent=module.IntentType.PRICE_INQUIRY),
        save_message=lambda *args, **kwargs: None,
        save_conversation_state=lambda *args, **kwargs: None,
        record_metric=lambda *args, **kwargs: None,
    )

    bubbles = asyncio.run(bublee.process_message("7000001002", "ah vale gracias"))

    merged = " ".join(bubbles).lower()
    assert "consulto con el equipo" not in merged
    assert "aproximado confiable" not in merged
    assert "aquí estoy" in merged or "aqui estoy" in merged or "cuando quieras" in merged


def test_patient_hours_followup_answers_schedule_without_dragging_price():
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._pending_buffers = {}
    bublee._admin_pending = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}

    class FakeAnalyzer:
        def analyze(self, text, history):
            return types.SimpleNamespace(
                language="es",
                urgency=module.UrgencyLevel.LOW,
                intent=module.IntentType.HOURS_INQUIRY,
                requires_search=False,
                closing_score=0.0,
                lead_temperature="warm",
            )

    class FakeReasoning:
        async def reason(self, *args, **kwargs):
            return {}

    class FakeGenerator:
        def _get_default_personality(self, clinic):
            return types.SimpleNamespace(archetype="amigable")

        def _apply_output_pipeline(self, response, **kwargs):
            return response

        def _repair_fragmented_response(self, response, **kwargs):
            return response

        def get_last_response_metadata(self):
            return {}

        async def generate(self, *args, **kwargs):
            raise AssertionError("no debería llamar al generator para un follow-up puro de horario")

    bublee.analyzer = FakeAnalyzer()
    bublee.reasoning = FakeReasoning()
    bublee.generator = FakeGenerator()
    module.db = types.SimpleNamespace(
        get_clinic=lambda: {
            "name": "Clinica de las americas",
            "sector": "estetica",
            "setup_done": 1,
            "admin_chat_ids": ["admin_1"],
            "pricing": {},
            "services": ["Botox"],
            "schedule": {"General": "Lunes a sábado de 9 a.m. a 7 p.m."},
        },
        get_admin=lambda chat_id: None,
        get_or_create_patient=lambda chat_id: {"is_new": False, "name": "Laura"},
        get_history=lambda chat_id, limit=None: [
            {"role": "user", "content": "precio rápido porfavor"},
            {"role": "assistant", "content": "No tengo un aproximado confiable aquí en este momento. ||| Si quieres, lo consulto con el equipo y te confirmo apenas me respondan."},
        ],
        get_conversation_state=lambda chat_id: types.SimpleNamespace(turn_count=1, last_intent=module.IntentType.PRICE_INQUIRY),
        save_message=lambda *args, **kwargs: None,
        save_conversation_state=lambda *args, **kwargs: None,
        record_metric=lambda *args, **kwargs: None,
    )

    bubbles = asyncio.run(bublee.process_message("7000001003", "y horarios"))

    merged = " ".join(bubbles).lower()
    assert "lunes a sábado" in merged or "lunes a sabado" in merged
    assert "precio" not in merged
    assert "consulto con el equipo" not in merged


def test_calendar_bridge_ignores_casual_a_esta_hora_phrase():
    module = load_bublee_module()
    bridge = module.CalendarBridge()

    assert bridge.needs_calendar("hola, vi botox pero me da pena preguntar a esta hora jaja") is False
    assert bridge.needs_calendar("quiero una cita esta semana en la tarde, tienen espacio?") is True


def test_admin_availability_feedback_is_rewritten_before_sending_to_patient():
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._availability_pending_patient = "patient_1"
    bublee._last_reviewed_chat = None
    bublee._pending_buffers = {}
    bublee._admin_pending = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}

    sent = []

    async def fake_send(chat_id, message, *args, **kwargs):
        sent.append((chat_id, message))

    async def fake_compose(patient_chat_id, admin_text, clinic):
        return "Ya me confirmaron que el jueves de 3 a 5 pm hay disponibilidad. Si te sirve, te lo dejo agendado."

    bublee._send_message = fake_send
    bublee._compose_patient_availability_reply = fake_compose
    module.db = types.SimpleNamespace()

    reply = asyncio.run(
        bublee._process_admin_feedback(
            "6908159885",
            "dile que entre el jueves de 3 a 5 pm hay disponibilidad que si le gustaria agendar a esa hora",
            {"name": "Clinica de las americas"},
        )
    )

    assert sent == [
        (
            "patient_1",
            "Ya me confirmaron que el jueves de 3 a 5 pm hay disponibilidad. Si te sirve, te lo dejo agendado.",
        )
    ]
    assert bublee._availability_pending_patient is None
    assert reply and "listo" in " ".join(reply).lower()


def test_pending_availability_context_uses_human_internal_instruction():
    module = load_bublee_module()

    context = module.build_pending_availability_context()
    lowered = context.lower()

    assert "agenda del dueño" not in lowered
    assert "déjame" in lowered or "dejame" in lowered
    assert "dueño" not in lowered
    assert "respuesta corta" in lowered


def test_live_admin_chat_ids_skip_probe_and_control_variants_when_real_admin_exists():
    module = load_bublee_module()

    ids = module.live_admin_chat_ids(
        ["6908159885", "admin_probe_20260328_real", "admin_control_20260328"]
    )
    assert ids == ["6908159885"]

    ids_without_real = module.live_admin_chat_ids(["admin_1"])
    assert ids_without_real == ["admin_1"]


def test_admin_natural_command_recovers_truncated_llm_json_instead_of_generic_fallback():
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._admin_pending = {}
    bublee._pending_buffers = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}

    async def fake_complete(*args, **kwargs):
        return (
            '{"reply":"No, para nada. Si algo te suena raro me lo pegas y lo rehago",'
            '"action":"none","data":{',
            {},
        )

    module.llm_engine = types.SimpleNamespace(complete=fake_complete)
    module.owner_style_controller = None
    module.trainer_gateway = None
    module.prompt_evolver = None
    module.anti_robot_filter = None
    module.db = types.SimpleNamespace(
        get_admin=lambda chat_id: {"name": "Santiago"},
        get_history=lambda chat_id, limit=8: [],
        save_message=lambda *args, **kwargs: None,
    )

    reply = asyncio.run(
        bublee._admin_natural_command(
            "6908159885",
            "si te digo algo raro te ofendes o no?",
            {"name": "Clinica de las americas", "admin_chat_ids": ["6908159885"]},
        )
    )

    merged = " ".join(reply).lower()
    assert "no, para nada" in merged
    assert "cuénteme qué quiere ajustar" not in merged


def test_synthetic_chat_id_filters_probe_and_test_variants():
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)

    assert bublee._is_synthetic_chat_id("provider_probe_fast_20260329") is True
    assert bublee._is_synthetic_chat_id("pipeline_probe_bot") is True
    assert bublee._is_synthetic_chat_id("stage2_probe_direct_01") is True
    assert bublee._is_synthetic_chat_id("p1_skeptica_v5") is True
    assert bublee._is_synthetic_chat_id("6908159885") is False


def test_repair_fragmented_response_does_not_replace_price_answers_with_template():
    module = load_bublee_module()
    generator = module.ResponseGenerator(llm=None)
    clinic = {
        "name": "Clinica de las americas",
        "sector": "estetica",
        "services": ["Botox", "Rellenos", "Láser"],
    }
    personality = generator._get_default_personality(clinic)

    repaired = generator._repair_fragmented_response(
        response="No tengo el precio exacto cargado ahora, porque cambia según la zona que te valoren",
        clinic=clinic,
        user_msg="Me interesa el botox, que vale",
        personality=personality,
        history=[],
    )

    assert "El valor depende de la valoración y de las zonas a trabajar" not in repaired
    assert "No tengo el precio exacto cargado ahora" in repaired


def test_repair_fragmented_response_preserves_follow_up_instead_of_service_menu():
    module = load_bublee_module()
    generator = module.ResponseGenerator(llm=None)
    clinic = {
        "name": "Clinica de las americas",
        "sector": "estetica",
        "services": ["Botox", "Rellenos", "Láser"],
    }

    repaired = generator._repair_fragmented_response(
        response="En esas zonas primero toca revisar si sí te conviene o si hay otra opción",
        clinic=clinic,
        user_msg="Es la cara y la barriga",
        personality=None,
        history=[{"role": "assistant", "content": "Cuéntame un poco más"}],
    )

    assert "Si quiere, le ubico información o disponibilidad" not in repaired
    assert "En esas zonas primero toca revisar" in repaired


def test_repair_fragmented_response_keeps_short_tail_visible_for_retry():
    module = load_bublee_module()
    generator = module.ResponseGenerator(llm=None)

    repaired = generator._repair_fragmented_response(
        response="No, para nada. Soy Bublee del equipo de la clínica\n\nCu",
        clinic={"name": "Clinica de las americas"},
        user_msg="Eres un bot?",
        personality=None,
        history=[{"role": "assistant", "content": "Hola"}],
    )

    assert repaired.endswith("Cu")
    assert not repaired.endswith("Cu.")


def test_retry_until_human_keeps_model_output_when_only_soft_conflicts_exist():
    module = load_bublee_module()

    class FakeLLM:
        def __init__(self):
            self.calls = 0

        async def complete(self, *args, **kwargs):
            self.calls += 1
            return "hola. Soy Bublee, del equipo de Clinica", {"model": "fake"}

    fake_llm = FakeLLM()
    generator = module.ResponseGenerator(llm=fake_llm)
    personality = generator._get_default_personality({"name": "Clinica de las americas"})
    original = "hola, buenas tardes. Cuéntame qué te gustaría mejorar o qué te trae por acá."

    result = asyncio.run(
        generator._retry_until_human(
            messages=[{"role": "system", "content": "stub"}],
            response=original,
            model_tier="fast",
            personality=personality,
            chat_id="soft_conflict_probe",
            clinic={"name": "Clinica de las americas"},
            user_msg="Hola buenas tardes",
            history=[],
        )
    )

    assert result == original
    assert fake_llm.calls == 0


def test_v8_process_response_preserves_multi_paragraph_patient_reply():
    module = load_bublee_module()
    module.init_v8_systems()

    response = (
        "¡Hola! Para nada, soy Bublee del equipo de la Clínica de las Américas.\n\n"
        "Cuéntame, ¿qué tenías en mente hoy? ¿Hay algún tratamiento que te llame la atención "
        "o alguna zona que quieras revisar?"
    )

    processed = module.v8_process_response(response, chat_id="v8_guard_probe", archetype="amigable")

    assert "Bublee del equipo de la Clínica de las Américas" in processed
    assert "alguna zona que quieras revisar" in processed


def test_postprocess_preserves_later_paragraphs_in_long_patient_reply():
    module = load_bublee_module()
    generator = module.ResponseGenerator(llm=None)
    personality = generator._get_default_personality({"name": "Clinica de las americas"})

    response = (
        "Ay no, para nada! Soy Bublee, una persona de verdad aquí en la clínica.\n\n"
        "Mira, el bótox es excelente para las líneas de expresión en la cara, "
        "pero para la barriga no es el tratamiento indicado. ¿Qué te gustaría mejorar en esa zona? "
        "Tal vez tenemos otra cosa que te sirva súper bien.\n\n"
        "Y sobre el precio del bótox para la cara, la cosa es que depende mucho de cuántas zonas necesites tratar, "
        "porque no es lo mismo solo la frente que frente, entrecejo y patitas de gallo. "
        "Lo mejor es que la doctora te vea en una valoración gratuita para que te diga exactamente qué necesitas y cuánto costaría."
    )

    processed = generator._postprocess(response, personality)

    assert "la barriga no es el tratamiento indicado" in processed
    assert "valoración gratuita" in processed


def test_postprocess_does_not_break_mid_sentence_help_question():
    module = load_bublee_module()
    generator = module.ResponseGenerator(llm=None)
    personality = generator._get_default_personality({"name": "Clinica de las americas"})

    processed = generator._postprocess(
        "No, soy Bublee del equipo de la clínica. ||| Cuéntame, ¿qué te gustaría revisar o en qué te puedo ayudar?",
        personality,
    )

    assert "qué te gustaría revisar o en qué te puedo ayudar" in processed
    assert "o?" not in processed


def test_compact_prompt_does_not_claim_human_identity_or_inject_fewshots():
    module = load_bublee_module()
    generator = module.ResponseGenerator(llm=None)
    clinic = {
        "name": "Clinica de las americas",
        "sector": "estetica",
        "services": ["Botox", "Rellenos", "Láser"],
    }
    personality = generator._get_default_personality(clinic)

    prompt = generator._build_compact_system_prompt(
        clinic=clinic,
        patient={"is_new": True, "visits": 0},
        personality=personality,
        search_context="",
        reasoning={"response_strategy": "responder precio primero"},
        kb_context="",
        context_summary="",
        pre_prompt_injection="",
        chat_id="identity_probe",
        history=[],
    ).lower()

    assert "como parte del equipo" in prompt
    assert "no ocultes que eres bot si te lo preguntan" in prompt
    assert "bot conversacional del equipo" not in prompt
    assert "asesora humana" not in prompt
    assert "así suenas" not in prompt


def test_compact_prompt_keeps_bot_disclosure_abstract_not_literal():
    module = load_bublee_module()
    generator = module.ResponseGenerator(llm=None)
    clinic = {
        "name": "Clinica de las americas",
        "sector": "estetica",
        "services": ["Botox", "Rellenos", "Láser"],
    }
    personality = generator._get_default_personality(clinic)

    prompt = generator._build_compact_system_prompt(
        clinic=clinic,
        patient={"is_new": True, "visits": 0},
        personality=personality,
        search_context="",
        reasoning={"response_strategy": "responder identidad"},
        kb_context="",
        context_summary="",
        pre_prompt_injection="",
        chat_id="identity_instruction_probe",
        history=[],
    ).lower()

    assert "si te preguntan si eres bot, responde eso con honestidad en una sola línea" in prompt
    assert "di 'sí, soy bublee'" not in prompt
    assert 'di "sí, soy bublee"' not in prompt


def test_compact_prompt_does_not_force_first_turn_self_intro():
    module = load_bublee_module()
    generator = module.ResponseGenerator(llm=None)
    clinic = {
        "name": "Clinica de las americas",
        "sector": "estetica",
        "services": ["Botox", "Rellenos", "Láser"],
    }
    personality = generator._get_default_personality(clinic)

    prompt = generator._build_compact_system_prompt(
        clinic=clinic,
        patient={"is_new": True, "visits": 0},
        personality=personality,
        search_context="",
        reasoning={"response_strategy": "responder precio primero"},
        kb_context="",
        context_summary="",
        pre_prompt_injection="",
        chat_id="first_turn_prompt_probe",
        history=[],
    ).lower()

    assert "no te presentes salvo que haga falta" in prompt
    assert "responde como bublee del equipo" not in prompt


def test_compact_prompt_forces_last_user_message_priority():
    module = load_bublee_module()
    generator = module.ResponseGenerator(llm=None)
    clinic = {
        "name": "Clinica de las americas",
        "sector": "estetica",
        "services": ["Botox", "Rellenos", "Láser"],
    }
    personality = generator._get_default_personality(clinic)

    prompt = generator._build_compact_system_prompt(
        clinic=clinic,
        patient={"is_new": True, "visits": 0},
        personality=personality,
        search_context="",
        reasoning={"response_strategy": "responder precio primero"},
        kb_context="",
        context_summary="",
        pre_prompt_injection="",
        chat_id="prompt_probe",
        history=[
            {"role": "user", "content": "Eres un bot?"},
            {"role": "assistant", "content": "No, soy Bublee del equipo de la clínica"},
        ],
    ).lower()

    assert "prioriza el último mensaje" in prompt
    assert "no sigas respondiendo la pregunta anterior" in prompt


def test_compact_prompt_skips_behavior_playbooks_for_patient():
    module = load_bublee_module()
    generator = module.ResponseGenerator(llm=None)
    clinic = {
        "name": "Clinica de las americas",
        "sector": "estetica",
        "services": ["Botox", "Rellenos", "Láser"],
    }
    personality = generator._get_default_personality(clinic)

    module.db = types.SimpleNamespace(
        get_core_memory_block=lambda: "",
        get_trust_rules=lambda limit=12: [],
        get_behavior_playbooks=lambda limit=3: [
            {
                "trigger_text": "si te saludan",
                "response_example": "hola ||| dime",
            }
        ],
    )
    module.owner_style_controller = None

    prompt = generator._build_compact_system_prompt(
        clinic=clinic,
        patient={"is_new": True, "visits": 0},
        personality=personality,
        search_context="",
        reasoning={"response_strategy": "responder precio primero"},
        kb_context="",
        context_summary="",
        pre_prompt_injection="",
        chat_id="playbook_probe",
        history=[],
    ).lower()

    assert "playbooks del dueño" not in prompt
    assert "si te saludan" not in prompt


def test_unanswered_price_request_requires_real_price_signal_not_only_valoracion():
    module = load_bublee_module()

    assert module.detect_unanswered_price_request(
        "Tu sabes de casualidad el precio?",
        "En la clínica primero te hacen una valoración para diseñarte un plan a tu medida.",
    ) is True

    assert module.detect_unanswered_price_request(
        "Tu sabes de casualidad el precio?",
        "El valor depende de las zonas que quieran trabajar y eso se define en valoración.",
    ) is False

    assert module.detect_unanswered_price_request(
        "Tu sabes de casualidad el precio?",
        "Ay, mira, el bótox es muy bueno para la cara y sí lo trabajamos, pero el precio exacto",
    ) is True

    assert module.detect_unanswered_price_request(
        "Pero un aproximado cuánto podría ser?",
        "No tengo un aproximado confiable aquí ahora mismo, pero si quieres lo consulto con el equipo y te confirmo.",
    ) is False


def test_generate_without_pricing_offers_to_consult_team_instead_of_repeating_valoracion():
    module = load_bublee_module()

    class FakeLLM:
        async def complete(self, *args, **kwargs):
            return (
                "No tengo un precio exacto para el bótox en este momento ||| "
                "El valor final depende de una valoración inicial y de las zonas específicas a tratar",
                {"model": "fake"},
            )

    generator = module.ResponseGenerator(llm=FakeLLM())
    personality = generator._get_default_personality({"name": "Clinica de las americas"})

    response = asyncio.run(
        generator.generate(
            message="Pero un aproximado cuánto podría ser?",
            analysis=types.SimpleNamespace(intent=module.IntentType.GENERAL_QUESTION),
            reasoning={"confidence": 1.0, "response_strategy": "responder precio con honestidad"},
            clinic={"name": "Clinica de las americas", "sector": "estetica", "pricing": {}},
            patient={"is_new": False, "visits": 1},
            history=[
                {"role": "user", "content": "Hola buenas noches, se que son las 3 am pero a qué precio tienen el botox"},
                {"role": "assistant", "content": "No tengo un precio exacto para el bótox en este momento"},
            ],
            search_context="",
            personality=personality,
            kb_context="",
            chat_id="price_team_consult_probe",
        )
    )

    lowered = response.lower()
    assert "no tengo un aproximado" in lowered
    assert "consult" in lowered and "equipo" in lowered
    assert "depende de la valoración" not in lowered


def test_missing_price_handoff_detection_catches_varia_without_consult_offer():
    module = load_bublee_module()

    assert module.detect_missing_price_handoff_needed(
        "Hola buenas noches, se que son las 3 am pero a qué precio tienen el botox",
        "El precio del Botox varía según el tratamiento que necesites.",
        {"name": "Clinica de las americas", "pricing": {}},
    ) is True


def test_hallucination_guard_safe_price_reply_offers_team_consult_when_no_pricing():
    module = load_bublee_module()
    guard = module.HallucinationGuard()

    has_hallucination, kind, safe = guard.check(
        "El bótox te puede salir en $350.000",
        {"name": "Clinica de las americas", "pricing": {}},
        "",
    )

    lowered = safe.lower()
    assert has_hallucination is True
    assert kind == "PRICE_INVENTED"
    assert "consult" in lowered and "equipo" in lowered
    assert not any(ch.isdigit() for ch in safe)


def test_process_message_notifies_admin_when_team_consult_is_promised():
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._pending_buffers = {}
    bublee._admin_pending = {}
    bublee._last_reviewed_chat = None
    bublee._availability_pending_patient = None
    bublee._demo_sessions = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}
    bublee._orchestrator = None
    bublee.search = types.SimpleNamespace(detect_procedure=lambda text: None)
    module.auth_engine = None
    module.trainer_gateway = None
    module.nova_rule_sync = None
    module.kb = None
    module.calendar_bridge = None
    module.task_manager = None
    module.owner_style_controller = None
    module.anti_robot_filter = None
    module.response_variation = None
    module.hallucination_guard = None
    module.notify_omni = lambda *args, **kwargs: None

    class FakeAnalyzer:
        def analyze(self, text, history):
            return types.SimpleNamespace(
                intent=module.IntentType.GENERAL_QUESTION,
                urgency=module.UrgencyLevel.NONE,
                language="es",
                requires_search=False,
                closing_score=0.0,
                lead_temperature="cold",
            )

    class FakeReasoning:
        async def reason(self, *args, **kwargs):
            return {"confidence": 1.0, "response_strategy": "responder con handoff al equipo"}

    class FakeGenerator:
        def _get_default_personality(self, clinic):
            return types.SimpleNamespace(archetype="amigable")

        def _should_use_seeded_first_turn(self, text, history):
            return False

        async def generate(self, *args, **kwargs):
            return (
                "No tengo un aproximado confiable aquí en este momento. ||| "
                "Si quieres, lo consulto con el equipo y te confirmo apenas me respondan."
            )

        def get_last_response_metadata(self):
            return {}

        def _repair_fragmented_response(self, response, **kwargs):
            return response

        def _normalize_first_patient_turn(self, response, **kwargs):
            return response

    sent = []

    async def fake_send_message(chat_id, message, *args, **kwargs):
        sent.append((chat_id, message))

    bublee.analyzer = FakeAnalyzer()
    bublee.reasoning = FakeReasoning()
    bublee.generator = FakeGenerator()
    bublee._send_message = fake_send_message
    module.db = types.SimpleNamespace(
        get_clinic=lambda: {
            "name": "Clinica de las americas",
            "sector": "estetica",
            "setup_done": 1,
            "admin_chat_ids": ["admin_1"],
            "pricing": {},
            "services": ["Botox"],
        },
        get_admin=lambda chat_id: None,
        get_or_create_patient=lambda chat_id: {"is_new": True, "name": "Laura"},
        get_history=lambda chat_id, limit=None: [],
        get_conversation_state=lambda chat_id: types.SimpleNamespace(turn_count=0, last_intent=None),
        save_message=lambda *args, **kwargs: None,
        save_conversation_state=lambda *args, **kwargs: None,
        record_metric=lambda *args, **kwargs: None,
    )

    bubbles = asyncio.run(
        bublee.process_message(
            "7000001001",
            "Hola buenas noches, se que son las 3 am pero a qué precio tienen el botox",
        )
    )

    assert any("consulto con el equipo" in bubble.lower() for bubble in bubbles)
    assert sent
    admin_chat_id, admin_message = sent[0]
    assert admin_chat_id == "admin_1"
    assert "laura" in admin_message.lower()
    assert "botox" in admin_message.lower()


def test_process_message_first_turn_short_greeting_uses_llm_when_brain_v10_active():
    module = load_bublee_module()
    module.Config.DEMO_MODE = False
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._pending_buffers = {}
    bublee._admin_pending = {}
    bublee._last_reviewed_chat = None
    bublee._availability_pending_patient = None
    bublee._demo_sessions = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}
    bublee._orchestrator = None
    bublee._remember_route = lambda chat_id, route=None: None
    bublee._resolve_route = lambda chat_id, route=None: {"platform": "whatsapp"}
    bublee._try_conversation_core = lambda **kwargs: None
    bublee.search = types.SimpleNamespace(detect_procedure=lambda text: None)
    module.auth_engine = None
    module.trainer_gateway = None
    module.nova_rule_sync = None
    module.kb = None
    module.calendar_bridge = None
    module.task_manager = None
    module.owner_style_controller = None
    module.anti_robot_filter = None
    module.response_variation = None
    module.hallucination_guard = None
    module.notify_omni = lambda *args, **kwargs: None
    module.v8_process_response = lambda response, **kwargs: response

    class FakeAnalyzer:
        def analyze(self, text, history):
            return types.SimpleNamespace(
                intent=module.IntentType.GENERAL_QUESTION,
                urgency=module.UrgencyLevel.NONE,
                language="es",
                requires_search=False,
                closing_score=0.0,
                lead_temperature="cold",
            )

    class FakeReasoning:
        async def reason(self, *args, **kwargs):
            return {"_metadata": {"model": "test_reasoning"}}

    class FakeGenerator:
        def __init__(self):
            self.generate_calls = 0
            self._brain_v10_llm_first = True

        def _get_default_personality(self, clinic):
            return types.SimpleNamespace(archetype="amigable")

        def _is_greeting_only(self, text):
            return True

        async def generate(self, *args, **kwargs):
            self.generate_calls += 1
            return "respuesta llm limpia"

        def get_last_response_metadata(self):
            return {}

        def _repair_fragmented_response(self, response, **kwargs):
            return response

        def _normalize_first_patient_turn(self, response, **kwargs):
            return response

    bublee.analyzer = FakeAnalyzer()
    bublee.reasoning = FakeReasoning()
    bublee.generator = FakeGenerator()
    module.db = types.SimpleNamespace(
        get_clinic=lambda: {
            "name": "Clinica de las americas",
            "sector": "estetica",
            "setup_done": 1,
            "admin_chat_ids": [],
            "pricing": {},
            "services": ["Botox"],
        },
        get_admin=lambda chat_id: None,
        get_or_create_patient=lambda chat_id: {"is_new": True, "name": ""},
        get_history=lambda chat_id, limit=None: [],
        get_conversation_state=lambda chat_id: types.SimpleNamespace(turn_count=0, last_intent=None),
        save_message=lambda *args, **kwargs: None,
        save_conversation_state=lambda *args, **kwargs: None,
        record_metric=lambda *args, **kwargs: None,
    )

    bubbles = asyncio.run(bublee.process_message("7000001004", "hola"))

    assert bublee.generator.generate_calls == 1
    assert bubbles == ["respuesta llm limpia"]


def test_demo_meta_question_filters_broken_llm_reply_and_explains_function(monkeypatch):
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._pending_buffers = {}
    bublee._admin_pending = {}
    bublee._last_reviewed_chat = None
    bublee._availability_pending_patient = None
    bublee._demo_sessions = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}
    bublee._orchestrator = None
    bublee._remember_route = lambda chat_id, route=None: None
    bublee._resolve_route = lambda chat_id, route=None: {"platform": "whatsapp"}
    bublee._try_conversation_core = lambda **kwargs: []
    bublee.search = types.SimpleNamespace(detect_procedure=lambda text: None)

    class FakeGenerator:
        llm = None

        def _postprocess(self, response, personality):
            return response

    class FakeLLM:
        async def complete(self, *args, **kwargs):
            return (
                "Entiendo, qué pena contigo, Mónica ||| La cago ||| dime el nombre de tu negocio",
                {"provider": "fake", "model": "fake"},
            )

    fake_db = types.SimpleNamespace(
        get_clinic=lambda: {
            "name": "Clinica de las americas",
            "sector": "estetica",
            "admin_chat_ids": [],
        },
        get_admin=lambda chat_id: None,
        get_history=lambda chat_id, limit=None: [
            {"role": "assistant", "content": "todo bien ||| cuéntame qué negocio quieres probar y arrancamos"}
        ],
        save_message=lambda *args, **kwargs: None,
    )

    bublee.generator = FakeGenerator()
    monkeypatch.setattr(module, "db", fake_db)
    monkeypatch.setattr(module, "llm_engine", FakeLLM())
    monkeypatch.setattr(module, "anti_robot_filter", None)
    monkeypatch.setattr(module, "v8_process_response", lambda response, **kwargs: response)
    monkeypatch.setattr(module.Config, "DEMO_MODE", True)
    monkeypatch.setattr(module.Config, "DEMO_BUSINESS_NAME", "")

    bubbles = asyncio.run(
        bublee.process_message("demo-meta-001", "el nombre de mi negocio?? para que??")
    )

    lowered = " ".join(bubbles).lower()
    assert "mónica" not in lowered
    assert "la cago" not in lowered
    assert "clinica de las americas" not in lowered
    assert "asistente virtual" not in lowered
    assert any(token in lowered for token in ("chat", "whatsapp", "demo", "negocio"))
    assert any(token in lowered for token in ("atiend", "respon", "convers", "funci"))


def test_demo_first_turn_rejects_fragmented_opening(monkeypatch):
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._pending_buffers = {}
    bublee._admin_pending = {}
    bublee._last_reviewed_chat = None
    bublee._availability_pending_patient = None
    bublee._demo_sessions = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}
    bublee._orchestrator = None
    bublee._remember_route = lambda chat_id, route=None: None
    bublee._resolve_route = lambda chat_id, route=None: {"platform": "whatsapp"}
    bublee._try_conversation_core = lambda **kwargs: []
    bublee.search = types.SimpleNamespace(detect_procedure=lambda text: None)

    class FakeGenerator:
        llm = None

        def _postprocess(self, response, personality):
            return response

    class FakeLLM:
        async def complete(self, *args, **kwargs):
            return ("hola! Qué", {"provider": "fake", "model": "fake"})

    fake_db = types.SimpleNamespace(
        get_clinic=lambda: {
            "name": "Clinica de las americas",
            "sector": "estetica",
            "admin_chat_ids": [],
        },
        get_admin=lambda chat_id: None,
        get_history=lambda chat_id, limit=None: [],
        save_message=lambda *args, **kwargs: None,
    )

    bublee.generator = FakeGenerator()
    monkeypatch.setattr(module, "db", fake_db)
    monkeypatch.setattr(module, "llm_engine", FakeLLM())
    monkeypatch.setattr(module, "anti_robot_filter", None)
    monkeypatch.setattr(module, "v8_process_response", lambda response, **kwargs: response)
    monkeypatch.setattr(module.Config, "DEMO_MODE", True)
    monkeypatch.setattr(module.Config, "DEMO_BUSINESS_NAME", "")

    bubbles = asyncio.run(
        bublee.process_message("demo-opening-001", "hola")
    )

    lowered = " ".join(bubbles).lower()
    assert "hola! qué" not in lowered
    assert any(token in lowered for token in ("negocio", "prueba", "muestras", "arrancamos", "atienda"))


def test_demo_first_turn_explains_function_and_why_it_needs_business_name(monkeypatch):
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._pending_buffers = {}
    bublee._admin_pending = {}
    bublee._last_reviewed_chat = None
    bublee._availability_pending_patient = None
    bublee._demo_sessions = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}
    bublee._orchestrator = None
    bublee._remember_route = lambda chat_id, route=None: None
    bublee._resolve_route = lambda chat_id, route=None: {"platform": "whatsapp"}
    bublee._try_conversation_core = lambda **kwargs: []
    bublee.search = types.SimpleNamespace(detect_procedure=lambda text: None)

    class FakeGenerator:
        llm = None

        def _postprocess(self, response, personality):
            return response

    class FakeLLM:
        async def complete(self, *args, **kwargs):
            return (
                "hola! Qué gusto saludarte otra vez ||| cuéntame, qué traes en mente para probar? a que le saques todo el jugo",
                {"provider": "fake", "model": "fake"},
            )

    fake_db = types.SimpleNamespace(
        get_clinic=lambda: {
            "name": "Clinica de las americas",
            "sector": "estetica",
            "admin_chat_ids": [],
        },
        get_admin=lambda chat_id: None,
        get_history=lambda chat_id, limit=None: [],
        save_message=lambda *args, **kwargs: None,
    )

    bublee.generator = FakeGenerator()
    monkeypatch.setattr(module, "db", fake_db)
    monkeypatch.setattr(module, "llm_engine", FakeLLM())
    monkeypatch.setattr(module, "anti_robot_filter", None)
    monkeypatch.setattr(module, "v8_process_response", lambda response, **kwargs: response)
    monkeypatch.setattr(module.Config, "DEMO_MODE", True)
    monkeypatch.setattr(module.Config, "DEMO_BUSINESS_NAME", "")

    bubbles = asyncio.run(
        bublee.process_message("demo-opening-002", "hola")
    )

    lowered = " ".join(bubbles).lower()
    assert "qué gusto saludarte otra vez" not in lowered
    assert "clinica de las americas" not in lowered
    assert any(token in lowered for token in ("funci", "chat", "whatsapp", "respon", "atiend", "demo"))
    assert "negocio" in lowered
    assert any(token in lowered for token in ("nombre", "tono", "context", "mostrar", "aterriz"))


def test_demo_first_turn_does_not_inject_runtime_clinic_name_into_onboarding(monkeypatch):
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._pending_buffers = {}
    bublee._admin_pending = {}
    bublee._last_reviewed_chat = None
    bublee._availability_pending_patient = None
    bublee._demo_sessions = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}
    bublee._orchestrator = None
    bublee._remember_route = lambda chat_id, route=None: None
    bublee._resolve_route = lambda chat_id, route=None: {"platform": "whatsapp"}
    bublee._try_conversation_core = lambda **kwargs: []
    bublee.search = types.SimpleNamespace(detect_procedure=lambda text: None)

    class FakeGenerator:
        llm = None

        def _postprocess(self, response, personality):
            return response

    class FakeLLM:
        async def complete(self, *args, **kwargs):
            return (
                "aquí me estás probando como si yo llevara el whatsapp de tu negocio ||| dime cómo se llama y arranco",
                {"provider": "fake", "model": "fake"},
            )

    fake_db = types.SimpleNamespace(
        get_clinic=lambda: {
            "name": "Nova",
            "sector": "otro",
            "admin_chat_ids": [],
        },
        get_admin=lambda chat_id: None,
        get_history=lambda chat_id, limit=None: [],
        save_message=lambda *args, **kwargs: None,
    )

    bublee.generator = FakeGenerator()
    monkeypatch.setattr(module, "db", fake_db)
    monkeypatch.setattr(module, "llm_engine", FakeLLM())
    monkeypatch.setattr(module, "anti_robot_filter", None)
    monkeypatch.setattr(module, "v8_process_response", lambda response, **kwargs: response)
    monkeypatch.setattr(module.Config, "DEMO_MODE", True)
    monkeypatch.setattr(module.Config, "DEMO_BUSINESS_NAME", "")

    bubbles = asyncio.run(
        bublee.process_message("demo-opening-no-clinic-001", "hola")
    )

    lowered = " ".join(bubbles).lower()
    assert "soy bublee de nova" not in lowered
    assert "del equipo de nova" not in lowered
    assert "nova" not in lowered
    assert "negocio" in lowered


def test_demo_onboarding_rejects_corporate_name_request(monkeypatch):
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._pending_buffers = {}
    bublee._admin_pending = {}
    bublee._last_reviewed_chat = None
    bublee._availability_pending_patient = None
    bublee._demo_sessions = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}
    bublee._orchestrator = None
    bublee._remember_route = lambda chat_id, route=None: None
    bublee._resolve_route = lambda chat_id, route=None: {"platform": "whatsapp"}
    bublee._try_conversation_core = lambda **kwargs: []
    bublee.search = types.SimpleNamespace(detect_procedure=lambda text: None)

    class FakeGenerator:
        llm = None

        def _postprocess(self, response, personality):
            return response

    class FakeLLM:
        async def complete(self, *args, **kwargs):
            return (
                "hola, gracias por considerarme para esta demo. me gustaría saber más sobre tu negocio para poder darte una respuesta más precisa y personalizada ||| podrías decirme el nombre de tu negocio",
                {"provider": "fake", "model": "fake"},
            )

    fake_db = types.SimpleNamespace(
        get_clinic=lambda: {
            "name": "Nova",
            "sector": "otro",
            "admin_chat_ids": [],
        },
        get_admin=lambda chat_id: None,
        get_history=lambda chat_id, limit=None: [],
        save_message=lambda *args, **kwargs: None,
    )

    bublee.generator = FakeGenerator()
    monkeypatch.setattr(module, "db", fake_db)
    monkeypatch.setattr(module, "llm_engine", FakeLLM())
    monkeypatch.setattr(module, "anti_robot_filter", None)
    monkeypatch.setattr(module, "v8_process_response", lambda response, **kwargs: response)
    monkeypatch.setattr(module.Config, "DEMO_MODE", True)
    monkeypatch.setattr(module.Config, "DEMO_BUSINESS_NAME", "")

    bubbles = asyncio.run(
        bublee.process_message("demo-onboarding-style-001", "hola")
    )

    lowered = " ".join(bubbles).lower()
    assert "gracias por considerarme" not in lowered
    assert "respuesta más precisa" not in lowered
    assert "respuesta mas precisa" not in lowered
    assert "personalizada" not in lowered
    assert "negocio" in lowered


def test_demo_first_turn_bypasses_conversation_core_until_business_name_exists(monkeypatch):
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._pending_buffers = {}
    bublee._admin_pending = {}
    bublee._last_reviewed_chat = None
    bublee._availability_pending_patient = None
    bublee._demo_sessions = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}
    bublee._orchestrator = None
    bublee._remember_route = lambda chat_id, route=None: None
    bublee._resolve_route = lambda chat_id, route=None: {"platform": "whatsapp"}
    bublee.search = types.SimpleNamespace(detect_procedure=lambda text: None)

    def bad_core(**kwargs):
        return [
            "Hola. Qué bueno tenerte por acá.",
            "Si quieres, retomamos desde donde lo dejamos y te ubico rápido.",
        ]

    bublee._try_conversation_core = bad_core

    class FakeGenerator:
        llm = None

        def _postprocess(self, response, personality):
            return response

    fake_db = types.SimpleNamespace(
        get_clinic=lambda: {
            "name": "Clinica de las americas",
            "sector": "estetica",
            "admin_chat_ids": [],
        },
        get_admin=lambda chat_id: None,
        get_history=lambda chat_id, limit=None: [],
        save_message=lambda *args, **kwargs: None,
    )

    bublee.generator = FakeGenerator()
    monkeypatch.setattr(module, "db", fake_db)
    monkeypatch.setattr(module, "anti_robot_filter", None)
    monkeypatch.setattr(module, "v8_process_response", lambda response, **kwargs: response)
    monkeypatch.setattr(module.Config, "DEMO_MODE", True)
    monkeypatch.setattr(module.Config, "DEMO_BUSINESS_NAME", "")

    bubbles = asyncio.run(
        bublee.process_message("demo-opening-core-bypass-001", "hola")
    )

    lowered = " ".join(bubbles).lower()
    assert "qué bueno tenerte por acá" not in lowered
    assert "que bueno tenerte por aca" not in lowered
    assert "retomamos desde donde lo dejamos" not in lowered
    assert "clinica de las americas" not in lowered
    assert "negocio" in lowered


def test_demo_without_business_name_never_falls_back_to_el_negocio_identity(monkeypatch):
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._pending_buffers = {}
    bublee._admin_pending = {}
    bublee._last_reviewed_chat = None
    bublee._availability_pending_patient = None
    bublee._demo_sessions = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}
    bublee._orchestrator = None
    bublee._remember_route = lambda chat_id, route=None: None
    bublee._resolve_route = lambda chat_id, route=None: {"platform": "whatsapp"}
    bublee._try_conversation_core = lambda **kwargs: []
    bublee.search = types.SimpleNamespace(detect_procedure=lambda text: None)

    class FakeGenerator:
        llm = None

        def _postprocess(self, response, personality):
            return response

    class FakeLLM:
        async def complete(self, *args, **kwargs):
            return (
                "para responderte bien necesito ubicar primero tu negocio ||| dime cómo se llama y seguimos",
                {"provider": "fake", "model": "fake"},
            )

    fake_db = types.SimpleNamespace(
        get_clinic=lambda: {
            "name": "Clinica de las americas",
            "sector": "estetica",
            "admin_chat_ids": [],
        },
        get_admin=lambda chat_id: None,
        get_history=lambda chat_id, limit=None: [
            {"role": "user", "content": "hola"},
            {"role": "assistant", "content": "aquí me pruebas como si yo llevara el whatsapp de tu negocio"},
            {"role": "user", "content": "buenas"},
            {"role": "assistant", "content": "dime cómo se llama el negocio y arranco"},
        ],
        save_message=lambda *args, **kwargs: None,
    )

    bublee.generator = FakeGenerator()
    monkeypatch.setattr(module, "db", fake_db)
    monkeypatch.setattr(module, "llm_engine", FakeLLM())
    monkeypatch.setattr(module, "anti_robot_filter", None)
    monkeypatch.setattr(module, "v8_process_response", lambda response, **kwargs: response)
    monkeypatch.setattr(module.Config, "DEMO_MODE", True)
    monkeypatch.setattr(module.Config, "DEMO_BUSINESS_NAME", "")

    bubbles = asyncio.run(
        bublee.process_message("demo-no-biz-fallback-001", "y ustedes en qué zona están?")
    )

    lowered = " ".join(bubbles).lower()
    assert "del equipo de el negocio" not in lowered
    assert "clinica de las americas" not in lowered
    assert "negocio" in lowered
    assert "zona" not in lowered


def test_demo_confusion_reply_does_not_fall_back_to_real_clinic_identity(monkeypatch):
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._pending_buffers = {}
    bublee._admin_pending = {}
    bublee._last_reviewed_chat = None
    bublee._availability_pending_patient = None
    bublee._demo_sessions = {
        "demo_demo-confusion-001_name": "",
        "demo_demo-confusion-001_ctx": "",
        "demo_demo-confusion-001_found": False,
        "demo_demo-confusion-001_ts": 1.0,
    }
    bublee._emoji_chats = set()
    bublee._chat_routes = {}
    bublee._orchestrator = None
    bublee._remember_route = lambda chat_id, route=None: None
    bublee._resolve_route = lambda chat_id, route=None: {"platform": "whatsapp"}
    bublee._try_conversation_core = lambda **kwargs: []
    bublee.search = types.SimpleNamespace(detect_procedure=lambda text: None)

    class FakeGenerator:
        llm = None

        def _postprocess(self, response, personality):
            return response

    class FakeLLM:
        async def complete(self, *args, **kwargs):
            return (
                "Disculpa la confusión, Mónica. Empecemos de nuevo. Soy Bublee, del equipo de Clínica Las Américas ||| Te ayudo con información, valoración y citas para nuestros tratamientos de estética",
                {"provider": "fake", "model": "fake"},
            )

    fake_db = types.SimpleNamespace(
        get_clinic=lambda: {
            "name": "Clinica de las americas",
            "sector": "estetica",
            "admin_chat_ids": [],
        },
        get_admin=lambda chat_id: None,
        get_history=lambda chat_id, limit=None: [
            {"role": "user", "content": "hola"},
            {"role": "assistant", "content": "todo bien ||| cuéntame qué negocio quieres que te ayude a mover y arrancamos"},
        ],
        save_message=lambda *args, **kwargs: None,
    )

    bublee.generator = FakeGenerator()
    monkeypatch.setattr(module, "db", fake_db)
    monkeypatch.setattr(module, "llm_engine", FakeLLM())
    monkeypatch.setattr(module, "anti_robot_filter", None)
    monkeypatch.setattr(module, "v8_process_response", lambda response, **kwargs: response)
    monkeypatch.setattr(module.Config, "DEMO_MODE", True)
    monkeypatch.setattr(module.Config, "DEMO_BUSINESS_NAME", "")

    bubbles = asyncio.run(
        bublee.process_message("demo-confusion-001", "a que te refieres? no te entiendo?")
    )

    lowered = " ".join(bubbles).lower()
    assert "mónica" not in lowered
    assert "clinica de las americas" not in lowered
    assert "del equipo" not in lowered
    assert any(token in lowered for token in ("chat", "whatsapp", "demo", "funci", "respon", "atiend"))
    assert "negocio" in lowered


def test_demo_conversation_core_identity_probe_stays_business_neutral():
    module = load_bublee_module()
    core_root = MODULE_PATH.parent
    registry = module.PersonaRegistry(core_root / "personas" / "bublee" / "base")
    engine = module.ConversationEngine(registry)

    result = engine.handle(
        clinic={
            "name": "Monica Beauty",
            "sector": "otro",
            "demo_mode": True,
        },
        user_msg="quien eres",
        history=[],
        is_admin=False,
        channel="whatsapp",
    )

    assert result.handled is False
    assert result.reason == "demo_llm_identity_probe"
    assert result.bubbles == []


def test_demo_conversation_core_returning_greeting_stays_on_demo_rails():
    module = load_bublee_module()
    core_root = MODULE_PATH.parent
    registry = module.PersonaRegistry(core_root / "personas" / "bublee" / "base")
    engine = module.ConversationEngine(registry)

    result = engine.handle(
        clinic={
            "name": "Clinica de los molinos",
            "sector": "otro",
            "demo_mode": True,
        },
        user_msg="hola buenas",
        history=[
            {"role": "user", "content": "hola"},
            {"role": "assistant", "content": "soy Bublee. aquí me pruebas como si ya estuviera atendiendo el WhatsApp de tu negocio"},
        ],
        is_admin=False,
        channel="whatsapp",
    )

    assert result.handled is False
    assert result.reason == "demo_llm_greeting"
    assert result.bubbles == []


def test_antirobot_filter_no_longer_preserves_clinic_branding_intro(monkeypatch):
    module = load_bublee_module()
    anti = module.AntiRobotFilter(level=2)

    cleaned = anti.process("Hola, soy Bublee, del equipo de Clínica Las Américas")
    lowered = cleaned.lower()

    assert "del equipo de" not in lowered
    assert "clinica las americas" not in lowered
    assert "clínica las américas" not in lowered


def test_demo_reset_bypasses_conversation_core_when_business_was_already_loaded(monkeypatch):
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._pending_buffers = {}
    bublee._admin_pending = {}
    bublee._last_reviewed_chat = None
    bublee._availability_pending_patient = None
    bublee._demo_sessions = {
        "demo_demo-reset-001_name": "Clinica Las Americas",
        "demo_demo-reset-001_found": True,
        "demo_demo-reset-001_ts": 1.0,
    }
    bublee._emoji_chats = set()
    bublee._chat_routes = {}
    bublee._orchestrator = None
    bublee._remember_route = lambda chat_id, route=None: None
    bublee._resolve_route = lambda chat_id, route=None: {"platform": "whatsapp"}
    bublee.search = types.SimpleNamespace(detect_procedure=lambda text: None)

    def bad_core(**kwargs):
        return [
            "Empecemos de nuevo entonces. En qué podemos ayudarte hoy en Clínica Las Américas?",
            "Tienes alguna zona del rostro o cuerpo que te gustaría mejorar o tratar?",
        ]

    bublee._try_conversation_core = bad_core

    class FakeGenerator:
        llm = None

        def _postprocess(self, response, personality):
            return response

    fake_db = types.SimpleNamespace(
        get_clinic=lambda: {
            "name": "Clinica de las americas",
            "sector": "estetica",
            "admin_chat_ids": [],
        },
        get_admin=lambda chat_id: None,
        get_history=lambda chat_id, limit=None: [
            {"role": "assistant", "content": "ya quedé al frente de este chat"},
        ],
        save_message=lambda *args, **kwargs: None,
    )

    bublee.generator = FakeGenerator()
    monkeypatch.setattr(module, "db", fake_db)
    monkeypatch.setattr(module, "anti_robot_filter", None)
    monkeypatch.setattr(module, "v8_process_response", lambda response, **kwargs: response)
    monkeypatch.setattr(module.Config, "DEMO_MODE", True)
    monkeypatch.setattr(module.Config, "DEMO_BUSINESS_NAME", "")

    bubbles = asyncio.run(
        bublee.process_message("demo-reset-001", "empezar de nuevo")
    )

    lowered = " ".join(bubbles).lower()
    assert "clínica las américas" not in lowered
    assert "clinica las americas" not in lowered
    assert "rostro o cuerpo" not in lowered
    assert "arrancamos de cero" in lowered or "cómo se llama tu negocio" in lowered or "como se llama tu negocio" in lowered


def test_demo_business_correction_bypasses_conversation_core_and_keeps_demo_mode(monkeypatch):
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._pending_buffers = {}
    bublee._admin_pending = {}
    bublee._last_reviewed_chat = None
    bublee._availability_pending_patient = None
    bublee._demo_sessions = {
        "demo_demo-correction-001_name": "Clinica Las Americas",
        "demo_demo-correction-001_found": True,
        "demo_demo-correction-001_url": "https://example.com/las-americas",
        "demo_demo-correction-001_ts": 1.0,
    }
    bublee._emoji_chats = set()
    bublee._chat_routes = {}
    bublee._orchestrator = None
    bublee._remember_route = lambda chat_id, route=None: None
    bublee._resolve_route = lambda chat_id, route=None: {"platform": "whatsapp"}
    bublee.search = types.SimpleNamespace(detect_procedure=lambda text: None)

    def bad_core(**kwargs):
        return [
            "Entiendo qué pena, parece que hubo un malentendido. Disculpa la confusión, pensé que era la Clínica Las Américas.",
        ]

    bublee._try_conversation_core = bad_core

    class FakeGenerator:
        llm = None

        def _postprocess(self, response, personality):
            return response

    fake_db = types.SimpleNamespace(
        get_clinic=lambda: {
            "name": "Clinica de las americas",
            "sector": "estetica",
            "admin_chat_ids": [],
        },
        get_admin=lambda chat_id: None,
        get_history=lambda chat_id, limit=None: [
            {"role": "assistant", "content": "ya quedé al frente de este chat"},
        ],
        save_message=lambda *args, **kwargs: None,
    )

    bublee.generator = FakeGenerator()
    monkeypatch.setattr(module, "db", fake_db)
    monkeypatch.setattr(module, "anti_robot_filter", None)
    monkeypatch.setattr(module, "v8_process_response", lambda response, **kwargs: response)
    monkeypatch.setattr(module.Config, "DEMO_MODE", True)
    monkeypatch.setattr(module.Config, "DEMO_BUSINESS_NAME", "")

    bubbles = asyncio.run(
        bublee.process_message(
            "demo-correction-001",
            "NO, clinica de las Americas?? pense que esto era una demo, mi negocio se llama clinica de los molinos",
        )
    )

    lowered = " ".join(bubbles).lower()
    assert "clínica las américas" not in lowered
    assert "clinica las americas" not in lowered
    assert "pensé que era" not in lowered
    assert "pense que era" not in lowered
    assert "tu negocio" in lowered


def test_send_message_retries_plain_text_when_telegram_markdown_fails():
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._emoji_chats = set()
    bublee._strip_emojis = lambda text: text
    bublee._resolve_route = lambda chat_id, route: {"platform": "telegram"}

    calls = []

    class FakeResponse:
        def __init__(self, status_code, text):
            self.status_code = status_code
            self.text = text

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, json):
            calls.append(json)
            if len(calls) == 1:
                return FakeResponse(400, "Bad Request: can't parse entities")
            return FakeResponse(200, "ok")

    original_client = module.httpx.AsyncClient
    module.httpx.AsyncClient = lambda timeout=15.0: FakeClient()
    try:
        asyncio.run(
            bublee._send_message(
                "6908159885",
                "Bublee quedó pendiente por chat e_v2",
            )
        )
    finally:
        module.httpx.AsyncClient = original_client

    assert len(calls) == 2
    assert calls[0]["parse_mode"] == "Markdown"
    assert "parse_mode" not in calls[1]


def test_retry_until_human_rewrites_incomplete_appointment_reply():
    module = load_bublee_module()

    class FakeLLM:
        async def complete(self, *args, **kwargs):
            return (
                "Te la puedo dejar encaminada. Te sirve cualquier hora de la tarde o prefieres una hora puntual?",
                {"model": "fake"},
            )

    generator = module.ResponseGenerator(llm=FakeLLM())
    personality = generator._get_default_personality(
        {"name": "Clinica de las americas", "sector": "estetica"}
    )

    rewritten = asyncio.run(
        generator._retry_until_human(
            messages=[{"role": "user", "content": "quiero cita el miércoles en la tarde"}],
            response="Para agendar tu cita el miércoles en la tarde.",
            model_tier="fast",
            personality=personality,
            chat_id="appointment_retry_probe",
            clinic={"name": "Clinica de las americas", "sector": "estetica"},
            user_msg="quiero cita el miércoles en la tarde",
            history=[],
        )
    )

    lowered = rewritten.lower()
    assert "prefieres una hora puntual" in lowered or "te sirve cualquier hora de la tarde" in lowered


def test_fragment_detector_catches_dangling_price_follow_ups():
    module = load_bublee_module()

    assert module.looks_fragmented_reply(
        "El valor cambia según las zonas que quieras tratar ||| Si me dices qué parte"
    ) is True

    assert module.looks_fragmented_reply(
        "Para la barriga no se maneja botox, pero para la."
    ) is True

    assert module.looks_fragmented_reply(
        "Ay, mira, el bótox es muy bueno para la cara y sí lo trabajamos, pero el precio exacto"
    ) is True

    assert module.looks_fragmented_reply(
        "El valor del bótox cambia según."
    ) is True


def test_simple_botox_interest_does_not_trigger_medical_search():
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)

    low_signal = types.SimpleNamespace(
        intent=module.IntentType.SERVICE_INFO,
        requires_search=True,
    )
    high_signal = types.SimpleNamespace(
        intent=module.IntentType.SERVICE_INFO,
        requires_search=True,
    )

    assert (
        bublee._should_run_medical_search(
            "hola, vi botox pero me da pena preguntar a esta hora jaja",
            low_signal,
        )
        is False
    )
    assert (
        bublee._should_run_medical_search(
            "quiero saber cuánto dura el botox, qué efectos tiene y si deja la cara tiesa",
            high_signal,
        )
        is True
    )


def test_detect_invented_objection_when_patient_never_mentioned_fear():
    module = load_bublee_module()

    assert module.detect_invented_objection(
        "Es la cara y la barriga",
        "Te preocupa quedar con un aspecto exagerado. Eso es muy común antes del bótox.",
        history=[
            {"role": "user", "content": "Me interesa el botox, que vale"},
            {"role": "assistant", "content": "El valor cambia según las zonas"},
        ],
    ) == "objecion_estetica_no_mencionada"

    assert module.detect_invented_objection(
        "Me da miedo quedar exagerada",
        "Te preocupa quedar con un aspecto exagerado. Eso es muy común antes del bótox.",
        history=[],
    ) == ""


def test_detect_topic_regression_when_bot_topic_is_reopened_after_price_question():
    module = load_bublee_module()

    assert module.detect_topic_regression(
        "Me interesa el botox, que vale",
        "Soy Bublee, del equipo de la clínica, para nada soy un bot. El valor cambia según la zona.",
        history=[
            {"role": "user", "content": "Eres un bot?"},
            {"role": "assistant", "content": "No, soy Bublee del equipo de la clínica"},
        ],
    ) == "tema_bot_reabierto"

    assert module.detect_topic_regression(
        "Me interesa el botox, que vale",
        "El valor cambia según las zonas que quieran trabajar.",
        history=[
            {"role": "user", "content": "Eres un bot?"},
            {"role": "assistant", "content": "No, soy Bublee del equipo de la clínica"},
        ],
    ) == ""


def test_drop_out_of_context_bubbles_keeps_useful_reply_content():
    module = load_bublee_module()

    assert module._drop_out_of_context_bubbles(
        'Soy Bublee, del equipo de la clínica. ||| El valor del bótox varía según las zonas que quieras tratar.',
        drop_topic_regression=True,
    ) == 'El valor del bótox varía según las zonas que quieras tratar.'

    assert module._drop_out_of_context_bubbles(
        'Te preocupa quedar exagerada. ||| Para la barriga no se trabaja con bótox.',
        drop_invented_objection=True,
    ) == 'Para la barriga no se trabaja con bótox.'


def test_detect_ignored_user_zones_when_response_does_not_answer_them():
    module = load_bublee_module()

    assert module.detect_ignored_user_zones(
        "Es la cara y la barriga",
        "Buscamos resultados muy naturales para que no se vea exagerado.",
    ) == ["cara", "barriga"]

    assert module.detect_ignored_user_zones(
        "Es la cara y la barriga",
        "Para la cara sí se maneja bótox, pero para la barriga no se usa.",
    ) == []


def test_apply_output_pipeline_drops_out_of_context_patient_bubbles():
    module = load_bublee_module()
    generator = module.ResponseGenerator(llm=None)
    personality = generator._get_default_personality({"name": "Clinica de las americas"})

    rewritten = generator._apply_output_pipeline(
        response='Soy Bublee del equipo de la clínica. ||| El valor del bótox depende de las zonas que quieras tratar.',
        personality=personality,
        chat_id='pipeline_probe_bot',
        clinic={"name": "Clinica de las americas", "sector": "estetica"},
        user_msg='Me interesa el botox, que vale',
        history=[
            {"role": "user", "content": "Eres un bot?"},
            {"role": "assistant", "content": "No, soy Bublee del equipo de la clínica"},
        ],
        is_admin=False,
    )

    assert "soy bublee" not in rewritten.lower()
    assert "depende de las zonas" in rewritten.lower()

    rewritten = generator._apply_output_pipeline(
        response='Te preocupa quedar exagerada. ||| Para la barriga no se trabaja con bótox.',
        personality=personality,
        chat_id='pipeline_probe_obj',
        clinic={"name": "Clinica de las americas", "sector": "estetica"},
        user_msg='Es la cara y la barriga',
        history=[
            {"role": "user", "content": "Me interesa el botox, que vale"},
            {"role": "assistant", "content": "El valor cambia según las zonas"},
        ],
        is_admin=False,
    )

    assert "quedar exagerada" not in rewritten.lower()
    assert "barriga no se trabaja" in rewritten.lower()


def test_identity_question_helpers_detect_robotic_help_pitch():
    module = load_bublee_module()

    assert module._is_identity_question("Eres un bot?") is True
    assert module._has_generic_help_pitch("Sí, soy Bublee. Cómo le puedo ayudar hoy?") is True
    assert module._has_generic_help_pitch("Sí, soy Bublee del equipo.") is False


def test_generate_applies_price_guardrail_when_model_still_does_not_answer_price():
    module = load_bublee_module()

    class FakeLLM:
        async def complete(self, *args, **kwargs):
            return "Soy Bublee, del equipo de la clínica", {"model": "fake"}

    generator = module.ResponseGenerator(llm=FakeLLM())
    personality = generator._get_default_personality({"name": "Clinica de las americas"})

    response = asyncio.run(
        generator.generate(
            message="Me interesa el botox, que vale",
            analysis=types.SimpleNamespace(intent=module.IntentType.PRICE_INQUIRY),
            reasoning={"confidence": 1.0, "response_strategy": "responder precio primero"},
            clinic={"name": "Clinica de las americas", "sector": "estetica"},
            patient={"is_new": True, "visits": 0},
            history=[
                {"role": "user", "content": "Eres un bot?"},
                {"role": "assistant", "content": "No, soy Bublee del equipo de la clínica"},
            ],
            search_context="",
            personality=personality,
            kb_context="",
            chat_id="price_guardrail_probe",
        )
    )

    assert "depende de las zonas" in response.lower()
    assert "si me dices qué parte te interesa" in response.lower()


def test_retry_until_human_reworks_identity_answer_with_help_pitch():
    module = load_bublee_module()

    class FakeLLM:
        def __init__(self):
            self.calls = 0

        async def complete(self, *args, **kwargs):
            self.calls += 1
            return "Sí, soy Bublee, la asistente virtual de la clínica. ||| Dime qué tratamiento estás mirando.", {"model": "fake"}

    fake_llm = FakeLLM()
    generator = module.ResponseGenerator(llm=fake_llm)
    personality = generator._get_default_personality({"name": "Clinica de las americas"})

    rewritten = asyncio.run(
        generator._retry_until_human(
            messages=[{"role": "system", "content": "stub"}],
            response="Sí, soy Bublee, la asistente virtual de la clínica ||| Cómo le puedo ayudar hoy?",
            model_tier="fast",
            personality=personality,
            chat_id="identity_pitch_probe",
            clinic={"name": "Clinica de las americas", "sector": "estetica"},
            user_msg="Eres un bot?",
            history=[{"role": "user", "content": "Hola buenas tardes"}],
        )
    )

    assert fake_llm.calls == 1
    assert "cómo le puedo ayudar hoy" not in rewritten.lower()
    assert "dime qué tratamiento estás mirando" in rewritten.lower()


def test_retry_until_human_keeps_fast_tier_on_price_like_rewrites():
    module = load_bublee_module()

    class FakeLLM:
        def __init__(self):
            self.tiers = []

        async def complete(self, *args, **kwargs):
            self.tiers.append(kwargs.get("model_tier"))
            return "hola, en qué te ayudo", {"model": "fake"}

    fake_llm = FakeLLM()
    generator = module.ResponseGenerator(llm=fake_llm)
    personality = generator._get_default_personality({"name": "Clinica de las americas"})

    asyncio.run(
        generator._retry_until_human(
            messages=[{"role": "system", "content": "stub"}],
            response="hola, en qué te ayudo",
            model_tier="fast",
            personality=personality,
            chat_id="price_retry_probe",
            clinic={"name": "Clinica de las americas", "sector": "estetica"},
            user_msg="o sea que no me pueden dar el precio",
            history=[{"role": "assistant", "content": "No tengo ese dato exacto"}],
        )
    )

    assert fake_llm.tiers == ["fast", "fast"]


def test_generate_applies_zone_guardrail_when_zone_reply_stays_fragmented():
    module = load_bublee_module()

    class FakeLLM:
        async def complete(self, *args, **kwargs):
            return "Para la cara sí manejamos el Botox. Para", {"model": "fake"}

    generator = module.ResponseGenerator(llm=FakeLLM())
    personality = generator._get_default_personality({"name": "Clinica de las americas"})

    response = asyncio.run(
        generator.generate(
            message="Es la cara y la barriga",
            analysis=types.SimpleNamespace(intent=module.IntentType.GENERAL_QUESTION),
            reasoning={"confidence": 1.0, "response_strategy": "responder por zonas"},
            clinic={"name": "Clinica de las americas", "sector": "estetica"},
            patient={"is_new": True, "visits": 0},
            history=[
                {"role": "user", "content": "Me interesa el botox, que vale"},
                {"role": "assistant", "content": "El valor depende de las zonas"},
            ],
            search_context="",
            personality=personality,
            kb_context="",
            chat_id="zone_guardrail_probe",
        )
    )

    assert "para la cara sí se maneja bótox" in response.lower()
    assert "para la barriga no se usa bótox" in response.lower()


def test_generate_applies_identity_guardrail_when_identity_reply_is_cut_or_corporate():
    module = load_bublee_module()

    class FakeLLM:
        async def complete(self, *args, **kwargs):
            return "Sí, soy Bublee, la asistente virtual de la ||| Cómo le puedo ayudar hoy?", {"model": "fake"}

    generator = module.ResponseGenerator(llm=FakeLLM())
    personality = generator._get_default_personality({"name": "Clinica de las americas"})

    response = asyncio.run(
        generator.generate(
            message="Eres un bot?",
            analysis=types.SimpleNamespace(intent=module.IntentType.GENERAL_QUESTION),
            reasoning={"confidence": 1.0, "response_strategy": "responder identidad con honestidad"},
            clinic={"name": "Clinica de las americas", "sector": "estetica"},
            patient={"is_new": True, "visits": 0},
            history=[{"role": "user", "content": "Hola buenas tardes"}],
            search_context="",
            personality=personality,
            kb_context="",
            chat_id="identity_guardrail_probe",
        )
    )

    assert response.lower() == "sí, soy bublee, el bot de la clínica."


def test_retry_owner_injection_ignores_admin_rules_for_patient_chat():
    module = load_bublee_module()
    generator = module.ResponseGenerator(llm=None)

    module.db = types.SimpleNamespace(
        get_trust_rules=lambda limit=8: [
            {"rule": "a los administradores háblales con respeto y más ejecutivo"},
            {"rule": "Si preguntan precio, responde eso primero"},
        ]
    )
    module.owner_style_controller = types.SimpleNamespace(
        _merged_bucket=lambda scope: {
            "forbidden_phrases": ["claro que sí"] if scope == "patient" else ["no hables así"],
            "forbidden_starts": [],
        }
    )

    conflicts, retry_block = generator._build_owner_rule_retry_injection(
        "claro que sí, depende de la zona",
        is_admin=False,
    )

    assert "claro que sí" in " ".join(conflicts).lower()
    assert "administradores" not in retry_block.lower()
    assert "ejecutivo" not in retry_block.lower()
    assert "no hables así" not in retry_block.lower()


def test_owner_style_patient_addon_stays_soft_and_bot_honest():
    module = load_bublee_module()
    controller = module.OwnerStyleController()
    controller._state = {
        "enabled": True,
        "global": controller._blank_bucket(),
        "admin": controller._seed_admin_defaults(controller._blank_bucket(register="usted")),
        "patient": controller._seed_patient_defaults(controller._blank_bucket(register="tu")),
    }
    controller._loaded = True

    addon = controller.build_prompt_addon(is_admin=False).lower()

    assert "preferencias vivas del negocio" in addon
    assert "control duro del admin" not in addon


def test_demo_first_turn_rejects_generic_sales_pitch_without_explaining_function(monkeypatch):
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._pending_buffers = {}
    bublee._admin_pending = {}
    bublee._last_reviewed_chat = None
    bublee._availability_pending_patient = None
    bublee._demo_sessions = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}
    bublee._orchestrator = None
    bublee._remember_route = lambda chat_id, route=None: None
    bublee._resolve_route = lambda chat_id, route=None: {"platform": "whatsapp"}
    bublee._try_conversation_core = lambda **kwargs: []
    bublee.search = types.SimpleNamespace(detect_procedure=lambda text: None)

    class FakeGenerator:
        llm = None

        def _postprocess(self, response, personality):
            return response

    class FakeLLM:
        async def complete(self, *args, **kwargs):
            return (
                "hola! Qué gusto saludarte. Quería contarte cómo estamos ayudando a negocios como el tuyo a gestionar sus citas de una forma mucho más sencilla y eficiente",
                {"provider": "fake", "model": "fake"},
            )

    fake_db = types.SimpleNamespace(
        get_clinic=lambda: {
            "name": "Clinica de las americas",
            "sector": "estetica",
            "admin_chat_ids": [],
        },
        get_admin=lambda chat_id: None,
        get_history=lambda chat_id, limit=None: [],
        save_message=lambda *args, **kwargs: None,
    )

    bublee.generator = FakeGenerator()
    monkeypatch.setattr(module, "db", fake_db)
    monkeypatch.setattr(module, "llm_engine", FakeLLM())
    monkeypatch.setattr(module, "anti_robot_filter", None)
    monkeypatch.setattr(module, "v8_process_response", lambda response, **kwargs: response)
    monkeypatch.setattr(module.Config, "DEMO_MODE", True)
    monkeypatch.setattr(module.Config, "DEMO_BUSINESS_NAME", "")

    bubbles = asyncio.run(
        bublee.process_message("demo-opening-pitch-001", "hola")
    )

    lowered = " ".join(bubbles).lower()
    assert "qué gusto saludarte" not in lowered
    assert "gestionar sus citas" not in lowered
    assert "eficiente" not in lowered
    assert "clinica de las americas" not in lowered
    assert any(token in lowered for token in ("funci", "chat", "whatsapp", "atiend", "respon"))
    assert "negocio" in lowered
    assert any(token in lowered for token in ("context", "tono", "aterriz", "mostrar", "adapt"))


def test_demo_business_activation_rejects_takeover_language(monkeypatch):
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._pending_buffers = {}
    bublee._admin_pending = {}
    bublee._last_reviewed_chat = None
    bublee._availability_pending_patient = None
    bublee._demo_sessions = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}
    bublee._orchestrator = None
    bublee._remember_route = lambda chat_id, route=None: None
    bublee._resolve_route = lambda chat_id, route=None: {"platform": "whatsapp"}
    bublee._try_conversation_core = lambda **kwargs: []

    class FakeSearch:
        def detect_procedure(self, text):
            return None

        async def search_business_link(self, name):
            return (
                "Clínica de los Molinos en Medellín ofrece tratamientos faciales y procedimientos estéticos no invasivos.",
                "https://clinicadelosmolinos.example",
            )

    class FakeGenerator:
        llm = None

        def _postprocess(self, response, personality):
            return response

    class FakeLLM:
        async def complete(self, *args, **kwargs):
            return (
                "ya tengo Clinica de los Molinos ||| ya quedé al frente de este chat por Clinica de los Molinos ||| escríbeme como si fueras un cliente",
                {"provider": "fake", "model": "fake"},
            )

    fake_db = types.SimpleNamespace(
        get_clinic=lambda: {
            "name": "Clinica de las americas",
            "sector": "estetica",
            "admin_chat_ids": [],
        },
        get_admin=lambda chat_id: None,
        get_history=lambda chat_id, limit=None: [],
        save_message=lambda *args, **kwargs: None,
    )

    bublee.search = FakeSearch()
    bublee.generator = FakeGenerator()
    monkeypatch.setattr(module, "db", fake_db)
    monkeypatch.setattr(module, "llm_engine", FakeLLM())
    monkeypatch.setattr(module, "anti_robot_filter", None)
    monkeypatch.setattr(module, "v8_process_response", lambda response, **kwargs: response)
    monkeypatch.setattr(module.Config, "DEMO_MODE", True)
    monkeypatch.setattr(module.Config, "DEMO_BUSINESS_NAME", "")

    bubbles = asyncio.run(
        bublee.process_message("demo-business-activation-001", "mi negocio se llama Clinica de los Molinos")
    )

    lowered = " ".join(bubbles).lower()
    assert "ya quedé al frente" not in lowered
    assert "ya quede al frente" not in lowered
    assert "clinica de las americas" not in lowered
    assert "cliente" in lowered
    assert any(token in lowered for token in ("me ubiqu", "context", "ubicad", "aterriz"))


def test_demo_business_name_is_captured_even_after_more_than_two_turns(monkeypatch):
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._pending_buffers = {}
    bublee._admin_pending = {}
    bublee._last_reviewed_chat = None
    bublee._availability_pending_patient = None
    bublee._demo_sessions = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}
    bublee._orchestrator = None
    bublee._remember_route = lambda chat_id, route=None: None
    bublee._resolve_route = lambda chat_id, route=None: {"platform": "whatsapp"}
    bublee._try_conversation_core = lambda **kwargs: []

    search_calls = []

    class FakeSearch:
        def detect_procedure(self, text):
            return None

        async def search_business_link(self, name):
            search_calls.append(name)
            return (
                "Clínica de los Molinos en Medellín ofrece tratamientos faciales y procedimientos estéticos no invasivos.",
                "https://clinicadelosmolinos.example",
            )

    class FakeGenerator:
        llm = None

        def _postprocess(self, response, personality):
            return response

    class FakeLLM:
        async def complete(self, *args, **kwargs):
            return (
                "listo, ya me ubiqué con Clinica de los Molinos ||| ya tengo claro el contexto del negocio ||| háblame como si fueras un cliente real y arrancamos",
                {"provider": "fake", "model": "fake"},
            )

    fake_db = types.SimpleNamespace(
        get_clinic=lambda: {
            "name": "Clinica de las americas",
            "sector": "estetica",
            "admin_chat_ids": [],
        },
        get_admin=lambda chat_id: None,
        get_history=lambda chat_id, limit=None: [
            {"role": "user", "content": "hola"},
            {"role": "assistant", "content": "soy Bublee. aquí me pruebas como si ya estuviera atendiendo el WhatsApp de tu negocio"},
            {"role": "user", "content": "a que te refieres? no te entiendo"},
            {"role": "assistant", "content": "te lo pongo simple. aquí me estás probando como si yo llevara el WhatsApp de tu negocio"},
        ],
        save_message=lambda *args, **kwargs: None,
    )

    bublee.search = FakeSearch()
    bublee.generator = FakeGenerator()
    monkeypatch.setattr(module, "db", fake_db)
    monkeypatch.setattr(module, "llm_engine", FakeLLM())
    monkeypatch.setattr(module, "anti_robot_filter", None)
    monkeypatch.setattr(module, "v8_process_response", lambda response, **kwargs: response)
    monkeypatch.setattr(module.Config, "DEMO_MODE", True)
    monkeypatch.setattr(module.Config, "DEMO_BUSINESS_NAME", "")

    bubbles = asyncio.run(
        bublee.process_message("demo-business-late-name-001", "mi negocio se llama Clinica de los Molinos")
    )

    lowered = " ".join(bubbles).lower()
    assert "clinica de los molinos" in lowered
    assert "ya tengo claro el contexto del negocio" in lowered
    assert "te pido el nombre porque" not in lowered
    assert bublee._demo_sessions["demo_demo-business-late-name-001_name"] == "Clinica de los Molinos"
    assert search_calls == ["Clinica de los Molinos"]


def test_demo_business_override_first_turn_skips_runtime_intro_normalizer(monkeypatch):
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._pending_buffers = {}
    bublee._admin_pending = {}
    bublee._last_reviewed_chat = None
    bublee._availability_pending_patient = None
    bublee._demo_sessions = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}
    bublee._orchestrator = None
    bublee._remember_route = lambda chat_id, route=None: None
    bublee._resolve_route = lambda chat_id, route=None: {"platform": "whatsapp"}
    bublee._try_conversation_core = lambda **kwargs: []
    bublee.search = types.SimpleNamespace(detect_procedure=lambda text: None)

    class FakeGenerator:
        llm = None

        def _postprocess(self, response, personality):
            return response

    class FakeLLM:
        async def complete(self, *args, **kwargs):
            return (
                "a qué tipo de empresa le vendes primero, bancos medianos o fintechs con agentes ya en pruebas",
                {"provider": "fake", "model": "fake"},
            )

    fake_db = types.SimpleNamespace(
        get_clinic=lambda: {
            "name": "Clinica de las americas",
            "sector": "estetica",
            "admin_chat_ids": [],
        },
        get_admin=lambda chat_id: None,
        get_history=lambda chat_id, limit=None: [],
        save_message=lambda *args, **kwargs: None,
    )

    bublee.generator = FakeGenerator()
    monkeypatch.setattr(module, "db", fake_db)
    monkeypatch.setattr(module, "llm_engine", FakeLLM())
    monkeypatch.setattr(module, "anti_robot_filter", None)
    monkeypatch.setattr(module, "v8_process_response", lambda response, **kwargs: response)
    monkeypatch.setattr(module.Config, "DEMO_MODE", True)
    monkeypatch.setattr(module.Config, "DEMO_BUSINESS_NAME", "")

    bubbles = asyncio.run(
        bublee.process_message(
            "demo-business-override-001",
            "Ya dejé Nova como negocio activo. Nova es una plataforma de gobernanza de intención para agentes de IA en bancos.",
        )
    )

    lowered = " ".join(bubbles).lower()
    assert "hola, bublee por acá" not in lowered
    assert "del equipo de nova" not in lowered
    assert "tipo de empresa" in lowered or "bancos medianos" in lowered


def test_demo_without_business_name_keeps_onboarding_even_after_multiple_turns(monkeypatch):
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._pending_buffers = {}
    bublee._admin_pending = {}
    bublee._last_reviewed_chat = None
    bublee._availability_pending_patient = None
    bublee._demo_sessions = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}
    bublee._orchestrator = None
    bublee._remember_route = lambda chat_id, route=None: None
    bublee._resolve_route = lambda chat_id, route=None: {"platform": "whatsapp"}
    bublee._try_conversation_core = lambda **kwargs: []
    bublee.search = types.SimpleNamespace(detect_procedure=lambda text: None)

    class FakeGenerator:
        llm = None

        def _postprocess(self, response, personality):
            return response

    class FakeLLM:
        async def complete(self, messages, *args, **kwargs):
            system_text = " ".join(m["content"] for m in messages if m.get("role") == "system").lower()
            if "modo demo" in system_text or "tu negocio" in system_text:
                return (
                    "todavía no tengo el nombre de tu negocio ||| dímelo y desde ahí sí te respondo en contexto",
                    {"provider": "fake", "model": "fake"},
                )
            return (
                "hola! Ese precio cambia según",
                {"provider": "fake", "model": "fake"},
            )

    fake_db = types.SimpleNamespace(
        get_clinic=lambda: {
            "name": "Clinica de las americas",
            "sector": "estetica",
            "admin_chat_ids": [],
        },
        get_admin=lambda chat_id: None,
        get_history=lambda chat_id, limit=None: [
            {"role": "user", "content": "hola"},
            {"role": "assistant", "content": "soy Bublee. aquí me pruebas como si ya estuviera atendiendo el WhatsApp de tu negocio"},
            {"role": "user", "content": "a que te refieres? no te entiendo"},
            {"role": "assistant", "content": "te lo pongo simple. aquí me estás probando como si yo llevara el WhatsApp de tu negocio"},
        ],
        save_message=lambda *args, **kwargs: None,
    )

    bublee.generator = FakeGenerator()
    monkeypatch.setattr(module, "db", fake_db)
    monkeypatch.setattr(module, "llm_engine", FakeLLM())
    monkeypatch.setattr(module, "anti_robot_filter", None)
    monkeypatch.setattr(module, "v8_process_response", lambda response, **kwargs: response)
    monkeypatch.setattr(module.Config, "DEMO_MODE", True)
    monkeypatch.setattr(module.Config, "DEMO_BUSINESS_NAME", "")

    bubbles = asyncio.run(
        bublee.process_message("demo-no-business-004", "cuánto vale el botox?")
    )

    lowered = " ".join(bubbles).lower()
    assert "ese precio cambia según" not in lowered
    assert "negocio" in lowered
    assert "context" in lowered or "dímelo" in lowered or "dimelo" in lowered


def test_demo_business_activation_keeps_search_silent_when_web_context_is_weak(monkeypatch):
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._pending_buffers = {}
    bublee._admin_pending = {}
    bublee._last_reviewed_chat = None
    bublee._availability_pending_patient = None
    bublee._demo_sessions = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}
    bublee._orchestrator = None
    bublee._remember_route = lambda chat_id, route=None: None
    bublee._resolve_route = lambda chat_id, route=None: {"platform": "whatsapp"}
    bublee._try_conversation_core = lambda **kwargs: []

    class FakeSearch:
        def detect_procedure(self, text):
            return None

        async def search_business_link(self, name):
            return ("info muy corta", "")

    class FakeGenerator:
        llm = None

        def _postprocess(self, response, personality):
            return response

    class FakeLLM:
        async def complete(self, *args, **kwargs):
            return (
                "ya me ubiqué con clinica de los molinos aunque no encontré mucha información sobre ellos ya tengo claro el contexto del negocio escríbeme como si fueras un cliente para ver que tipo de servicios ofrecen",
                {"provider": "fake", "model": "fake"},
            )

    fake_db = types.SimpleNamespace(
        get_clinic=lambda: {
            "name": "Clinica de las americas",
            "sector": "estetica",
            "admin_chat_ids": [],
        },
        get_admin=lambda chat_id: None,
        get_history=lambda chat_id, limit=None: [],
        save_message=lambda *args, **kwargs: None,
    )

    bublee.search = FakeSearch()
    bublee.generator = FakeGenerator()
    monkeypatch.setattr(module, "db", fake_db)
    monkeypatch.setattr(module, "llm_engine", FakeLLM())
    monkeypatch.setattr(module, "anti_robot_filter", None)
    monkeypatch.setattr(module, "v8_process_response", lambda response, **kwargs: response)
    monkeypatch.setattr(module.Config, "DEMO_MODE", True)
    monkeypatch.setattr(module.Config, "DEMO_BUSINESS_NAME", "")

    bubbles = asyncio.run(
        bublee.process_message("demo-business-silent-search-001", "mi negocio se llama Clinica de los Molinos")
    )

    lowered = " ".join(bubbles).lower()
    assert "no encontré" not in lowered
    assert "no encontre" not in lowered
    assert "google" not in lowered
    assert "búsqueda" not in lowered
    assert "busqueda" not in lowered
    assert "ya tengo claro el contexto del negocio" in lowered
    assert "cliente" in lowered
    assert "servicios que ofrecen" not in lowered
    assert "parece un lugar" not in lowered


def test_demo_clarify_reply_stays_simple_when_owner_is_confused(monkeypatch):
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._pending_buffers = {}
    bublee._admin_pending = {}
    bublee._last_reviewed_chat = None
    bublee._availability_pending_patient = None
    bublee._demo_sessions = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}
    bublee._orchestrator = None
    bublee._remember_route = lambda chat_id, route=None: None
    bublee._resolve_route = lambda chat_id, route=None: {"platform": "whatsapp"}
    bublee._try_conversation_core = lambda **kwargs: []
    bublee.search = types.SimpleNamespace(detect_procedure=lambda text: None)

    class FakeGenerator:
        llm = None

        def _postprocess(self, response, personality):
            return response

    class FakeLLM:
        async def complete(self, *args, **kwargs):
            return (
                "hola, a gestionar tus conversaciones en WhatsApp. Mi función es responder a tus clientes, resolver dudas ||| me gustaría saber un poco más sobre tu negocio para poder personalizar mis respuestas y hacer que todo sea más natural y agradable para tus clientes ||| el nombre de tu negocio me ayudaría a entender mejor el tono y el estilo que debemos usar",
                {"provider": "fake", "model": "fake"},
            )

    fake_db = types.SimpleNamespace(
        get_clinic=lambda: {
            "name": "Clinica de las americas",
            "sector": "estetica",
            "admin_chat_ids": [],
        },
        get_admin=lambda chat_id: None,
        get_history=lambda chat_id, limit=None: [
            {"role": "user", "content": "hola"},
            {"role": "assistant", "content": "soy Bublee. aquí me pruebas como si ya estuviera atendiendo el WhatsApp de tu negocio"},
        ],
        save_message=lambda *args, **kwargs: None,
    )

    bublee.generator = FakeGenerator()
    monkeypatch.setattr(module, "db", fake_db)
    monkeypatch.setattr(module, "llm_engine", FakeLLM())
    monkeypatch.setattr(module, "anti_robot_filter", None)
    monkeypatch.setattr(module, "v8_process_response", lambda response, **kwargs: response)
    monkeypatch.setattr(module.Config, "DEMO_MODE", True)
    monkeypatch.setattr(module.Config, "DEMO_BUSINESS_NAME", "")

    bubbles = asyncio.run(
        bublee.process_message("demo-clarify-001", "a que te refieres? no te entiendo")
    )

    lowered = " ".join(bubbles).lower()
    assert any(token in lowered for token in ("negocio", "chat", "whatsapp"))
    assert "me gustaría saber un poco más" not in lowered
    assert "tono y el estilo" not in lowered
    assert "whatsapp de tu negocio" in lowered


def test_demo_first_turn_rejects_marketing_contact_pitch(monkeypatch):
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._pending_buffers = {}
    bublee._admin_pending = {}
    bublee._last_reviewed_chat = None
    bublee._availability_pending_patient = None
    bublee._demo_sessions = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}
    bublee._orchestrator = None
    bublee._remember_route = lambda chat_id, route=None: None
    bublee._resolve_route = lambda chat_id, route=None: {"platform": "whatsapp"}
    bublee._try_conversation_core = lambda **kwargs: []
    bublee.search = types.SimpleNamespace(detect_procedure=lambda text: None)

    class FakeGenerator:
        llm = None

        def _postprocess(self, response, personality):
            return response

    class FakeLLM:
        async def complete(self, *args, **kwargs):
            return (
                "hola, gracias por contactarme. a gestionar tus conversaciones en WhatsApp, para que puedas enfocarte en lo que realmente importa, que es tu negocio ||| mi función es sencilla: respondo a tus clientes, les doy información y los ayudo con sus preguntas, para que tú puedas tener más tiempo libre y enfocarte en otras cosas ||| para poder ayudarte de la mejor manera, me gustaría saber un poco más sobre tu negocio. Podrías decirme cómo se llama?",
                {"provider": "fake", "model": "fake"},
            )

    fake_db = types.SimpleNamespace(
        get_clinic=lambda: {
            "name": "Clinica de las americas",
            "sector": "estetica",
            "admin_chat_ids": [],
        },
        get_admin=lambda chat_id: None,
        get_history=lambda chat_id, limit=None: [],
        save_message=lambda *args, **kwargs: None,
    )

    bublee.generator = FakeGenerator()
    monkeypatch.setattr(module, "db", fake_db)
    monkeypatch.setattr(module, "llm_engine", FakeLLM())
    monkeypatch.setattr(module, "anti_robot_filter", None)
    monkeypatch.setattr(module, "v8_process_response", lambda response, **kwargs: response)
    monkeypatch.setattr(module.Config, "DEMO_MODE", True)
    monkeypatch.setattr(module.Config, "DEMO_BUSINESS_NAME", "")

    bubbles = asyncio.run(
        bublee.process_message("demo-opening-marketing-001", "hola")
    )

    lowered = " ".join(bubbles).lower()
    assert "gracias por contactarme" not in lowered
    assert "tiempo libre" not in lowered
    assert "realmente importa" not in lowered
    assert any(token in lowered for token in ("funci", "chat", "whatsapp", "negocio"))


def test_demo_business_activation_without_real_context_does_not_guess_business_type(monkeypatch):
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._pending_buffers = {}
    bublee._admin_pending = {}
    bublee._last_reviewed_chat = None
    bublee._availability_pending_patient = None
    bublee._demo_sessions = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}
    bublee._orchestrator = None
    bublee._remember_route = lambda chat_id, route=None: None
    bublee._resolve_route = lambda chat_id, route=None: {"platform": "whatsapp"}
    bublee._try_conversation_core = lambda **kwargs: []

    class FakeSearch:
        def detect_procedure(self, text):
            return None

        async def search_business_link(self, name):
            return ("info muy corta", "")

    class FakeGenerator:
        llm = None

        def _postprocess(self, response, personality):
            return response

    class FakeLLM:
        async def complete(self, *args, **kwargs):
            return (
                "me parece que clinica de los molinos es un lugar donde se ofrece atención médica de calidad ||| ya tengo claro el contexto del negocio ||| escribame como si fuera un paciente para ver que servicios ofrecen",
                {"provider": "fake", "model": "fake"},
            )

    fake_db = types.SimpleNamespace(
        get_clinic=lambda: {
            "name": "Clinica de las americas",
            "sector": "estetica",
            "admin_chat_ids": [],
        },
        get_admin=lambda chat_id: None,
        get_history=lambda chat_id, limit=None: [],
        save_message=lambda *args, **kwargs: None,
    )

    bublee.search = FakeSearch()
    bublee.generator = FakeGenerator()
    monkeypatch.setattr(module, "db", fake_db)
    monkeypatch.setattr(module, "llm_engine", FakeLLM())
    monkeypatch.setattr(module, "anti_robot_filter", None)
    monkeypatch.setattr(module, "v8_process_response", lambda response, **kwargs: response)
    monkeypatch.setattr(module.Config, "DEMO_MODE", True)
    monkeypatch.setattr(module.Config, "DEMO_BUSINESS_NAME", "")

    bubbles = asyncio.run(
        bublee.process_message("demo-business-no-guess-001", "mi negocio se llama Clinica de los Molinos")
    )

    lowered = " ".join(bubbles).lower()
    assert "me parece que" not in lowered
    assert "atención médica" not in lowered
    assert "atencion medica" not in lowered
    assert "paciente" not in lowered
    assert "servicios ofrecen" not in lowered
    assert "cliente" in lowered


def test_demo_runtime_routes_through_domino_before_legacy_demo_layers(monkeypatch):
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._pending_buffers = {}
    bublee._admin_pending = {}
    bublee._last_reviewed_chat = None
    bublee._availability_pending_patient = None
    bublee._demo_sessions = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}
    bublee._orchestrator = None
    bublee._remember_route = lambda chat_id, route=None: None
    bublee._resolve_route = lambda chat_id, route=None: {"platform": "whatsapp"}
    bublee._try_conversation_core = lambda **kwargs: [
        "Hola. Qué bueno tenerte por acá.",
        "Si quieres, retomamos desde donde lo dejamos y te ubico rápido.",
    ]
    bublee.search = types.SimpleNamespace(detect_procedure=lambda text: None)

    class FakeGenerator:
        llm = None

        def _postprocess(self, response, personality):
            return response

    class FakeLLM:
        async def complete(self, messages, *args, **kwargs):
            system = messages[0]["content"]
            user = messages[1]["content"]
            assert "ACCIÓN DE ESTE TURNO" in system
            assert "mensaje actual del dueño" in user
            return (
                "soy Bublee ||| aquí ya estoy dentro del chat de tu negocio ||| dime cómo se llama y arrancamos bien",
                {"provider": "fake", "model": "fake"},
            )

    fake_db = types.SimpleNamespace(
        get_clinic=lambda: {
            "name": "Clinica de las americas",
            "sector": "estetica",
            "admin_chat_ids": [],
        },
        get_admin=lambda chat_id: None,
        get_history=lambda chat_id, limit=None: [],
        save_message=lambda *args, **kwargs: None,
    )

    called = {"payload": 0}

    def fake_should_route_demo_to_domino(**kwargs):
        return True

    def fake_build_demo_domino_payload(**kwargs):
        called["payload"] += 1
        return {
            "stage": "enter-demo",
            "objective": "test",
            "action": "test",
            "system": "ACCIÓN DE ESTE TURNO\nusa domino",
            "user": "mensaje actual del dueño:\nhola buenas",
        }

    bublee.generator = FakeGenerator()
    monkeypatch.setattr(module, "db", fake_db)
    monkeypatch.setattr(module, "llm_engine", FakeLLM())
    monkeypatch.setattr(module, "anti_robot_filter", None)
    monkeypatch.setattr(module, "v8_process_response", lambda response, **kwargs: response)
    monkeypatch.setattr(module.Config, "DEMO_MODE", True)
    monkeypatch.setattr(module.Config, "DEMO_BUSINESS_NAME", "")
    monkeypatch.setattr(module, "should_route_demo_to_domino", fake_should_route_demo_to_domino, raising=False)
    monkeypatch.setattr(module, "build_demo_domino_payload", fake_build_demo_domino_payload, raising=False)

    bubbles = asyncio.run(
        bublee.process_message("demo-domino-runtime-001", "hola buenas")
    )

    lowered = " ".join(bubbles).lower()
    assert called["payload"] == 1
    assert "qué bueno tenerte por acá" not in lowered
    assert "retomamos desde donde lo dejamos" not in lowered
    assert "chat de tu negocio" in lowered


def test_demo_enter_demo_uses_structural_repair_before_fixed_fallback(monkeypatch):
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._pending_buffers = {}
    bublee._admin_pending = {}
    bublee._last_reviewed_chat = None
    bublee._availability_pending_patient = None
    bublee._demo_sessions = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}
    bublee._orchestrator = None
    bublee._remember_route = lambda chat_id, route=None: None
    bublee._resolve_route = lambda chat_id, route=None: {"platform": "whatsapp"}
    bublee._try_conversation_core = lambda **kwargs: []
    bublee.search = types.SimpleNamespace(detect_procedure=lambda text: None)

    class FakeGenerator:
        llm = None

        def _postprocess(self, response, personality):
            return response

    class FakeLLM:
        def __init__(self):
            self.calls = 0

        async def complete(self, messages, *args, **kwargs):
            self.calls += 1
            if self.calls == 1:
                return ("hola. Aquí me encargo de mover y responder", {"provider": "fake", "model": "fake"})
            if self.calls == 2:
                return ("aquí lo que hago es llevar las conversaciones", {"provider": "fake", "model": "fake"})
            return (
                "estoy aquí para llevar el chat de tu negocio ||| con el nombre sé desde qué contexto responder y no hablarte genérico ||| dime cómo se llama y arrancamos",
                {"provider": "fake", "model": "fake"},
            )

    fake_llm = FakeLLM()

    fake_db = types.SimpleNamespace(
        get_clinic=lambda: {
            "name": "Clinica de las americas",
            "sector": "estetica",
            "admin_chat_ids": [],
        },
        get_admin=lambda chat_id: None,
        get_history=lambda chat_id, limit=None: [],
        save_message=lambda *args, **kwargs: None,
    )

    bublee.generator = FakeGenerator()
    monkeypatch.setattr(module, "db", fake_db)
    monkeypatch.setattr(module, "llm_engine", fake_llm)
    monkeypatch.setattr(module, "anti_robot_filter", None)
    monkeypatch.setattr(module, "v8_process_response", lambda response, **kwargs: response)
    monkeypatch.setattr(module.Config, "DEMO_MODE", True)
    monkeypatch.setattr(module.Config, "DEMO_BUSINESS_NAME", "")

    bubbles = asyncio.run(
        bublee.process_message("demo-enter-repair-001", "hola parce, como funciona esto?")
    )

    lowered = " ".join(bubbles).lower()
    assert fake_llm.calls == 3
    assert "whatsapp de tu negocio" in lowered or "chat de tu negocio" in lowered
    assert "cómo se llama" in lowered or "como se llama" in lowered
    assert "no hablarte genérico" in lowered or "no hablarte generico" in lowered


def test_demo_enter_demo_rejects_single_bubble_structural_reply_without_name_request(monkeypatch):
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._pending_buffers = {}
    bublee._admin_pending = {}
    bublee._last_reviewed_chat = None
    bublee._availability_pending_patient = None
    bublee._demo_sessions = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}
    bublee._orchestrator = None
    bublee._remember_route = lambda chat_id, route=None: None
    bublee._resolve_route = lambda chat_id, route=None: {"platform": "whatsapp"}
    bublee._try_conversation_core = lambda **kwargs: []
    bublee.search = types.SimpleNamespace(detect_procedure=lambda text: None)

    class FakeGenerator:
        llm = None

        def _postprocess(self, response, personality):
            return response

    class FakeLLM:
        def __init__(self):
            self.calls = 0

        async def complete(self, messages, *args, **kwargs):
            self.calls += 1
            if self.calls == 1:
                return ("hola. Aquí me encargo de mover y responder", {"provider": "fake", "model": "fake"})
            if self.calls == 2:
                return ("hola, aquí atiendo las conversaciones que llegan", {"provider": "fake", "model": "fake"})
            return ("aquí me encargo de atender los chats y responder", {"provider": "fake", "model": "fake"})

    fake_llm = FakeLLM()

    fake_db = types.SimpleNamespace(
        get_clinic=lambda: {
            "name": "Clinica de las americas",
            "sector": "estetica",
            "admin_chat_ids": [],
        },
        get_admin=lambda chat_id: None,
        get_history=lambda chat_id, limit=None: [],
        save_message=lambda *args, **kwargs: None,
    )

    bublee.generator = FakeGenerator()
    monkeypatch.setattr(module, "db", fake_db)
    monkeypatch.setattr(module, "llm_engine", fake_llm)
    monkeypatch.setattr(module, "anti_robot_filter", None)
    monkeypatch.setattr(module, "v8_process_response", lambda response, **kwargs: response)
    monkeypatch.setattr(module.Config, "DEMO_MODE", True)
    monkeypatch.setattr(module.Config, "DEMO_BUSINESS_NAME", "")

    bubbles = asyncio.run(
        bublee.process_message("demo-enter-reject-001", "hola parce, como funciona esto?")
    )

    lowered = " ".join(bubbles).lower()
    assert fake_llm.calls == 3
    assert lowered != "aquí me encargo de atender los chats y responder"
    assert "nombre" in lowered or "cómo se llama" in lowered or "como se llama" in lowered


def test_demo_opening_handles_comparing_objection_before_asking_business_name(monkeypatch):
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._pending_buffers = {}
    bublee._admin_pending = {}
    bublee._last_reviewed_chat = None
    bublee._availability_pending_patient = None
    bublee._demo_sessions = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}
    bublee._orchestrator = None
    bublee._remember_route = lambda chat_id, route=None: None
    bublee._resolve_route = lambda chat_id, route=None: {"platform": "whatsapp"}
    bublee._try_conversation_core = lambda **kwargs: []
    bublee.search = types.SimpleNamespace(detect_procedure=lambda text: None)

    class FakeGenerator:
        llm = None

        def _postprocess(self, response, personality):
            return response

    class FakeLLM:
        async def complete(self, messages, *args, **kwargs):
            return ("aquí lo que hago es llevar el chat", {"provider": "fake", "model": "fake"})

    fake_db = types.SimpleNamespace(
        get_clinic=lambda: {
            "name": "Clinica de las americas",
            "sector": "estetica",
            "admin_chat_ids": [],
        },
        get_admin=lambda chat_id: None,
        get_history=lambda chat_id, limit=None: [],
        save_message=lambda *args, **kwargs: None,
    )

    bublee.generator = FakeGenerator()
    monkeypatch.setattr(module, "db", fake_db)
    monkeypatch.setattr(module, "llm_engine", FakeLLM())
    monkeypatch.setattr(module, "anti_robot_filter", None)
    monkeypatch.setattr(module, "v8_process_response", lambda response, **kwargs: response)
    monkeypatch.setattr(module.Config, "DEMO_MODE", True)
    monkeypatch.setattr(module.Config, "DEMO_BUSINESS_NAME", "")

    bubbles = asyncio.run(
        bublee.process_message("demo-compare-001", "solo estoy comparando")
    )

    lowered = " ".join(bubbles).lower()
    assert "compar" in lowered
    assert "negocio" in lowered
    assert "cómo se llama" in lowered or "como se llama" in lowered


def test_demo_opening_handles_bot_fear_before_asking_business_name(monkeypatch):
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._pending_buffers = {}
    bublee._admin_pending = {}
    bublee._last_reviewed_chat = None
    bublee._availability_pending_patient = None
    bublee._demo_sessions = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}
    bublee._orchestrator = None
    bublee._remember_route = lambda chat_id, route=None: None
    bublee._resolve_route = lambda chat_id, route=None: {"platform": "whatsapp"}
    bublee._try_conversation_core = lambda **kwargs: []
    bublee.search = types.SimpleNamespace(detect_procedure=lambda text: None)

    class FakeGenerator:
        llm = None

        def _postprocess(self, response, personality):
            return response

    class FakeLLM:
        async def complete(self, messages, *args, **kwargs):
            return ("mi función es atender consultas", {"provider": "fake", "model": "fake"})

    fake_db = types.SimpleNamespace(
        get_clinic=lambda: {
            "name": "Clinica de las americas",
            "sector": "estetica",
            "admin_chat_ids": [],
        },
        get_admin=lambda chat_id: None,
        get_history=lambda chat_id, limit=None: [],
        save_message=lambda *args, **kwargs: None,
    )

    bublee.generator = FakeGenerator()
    monkeypatch.setattr(module, "db", fake_db)
    monkeypatch.setattr(module, "llm_engine", FakeLLM())
    monkeypatch.setattr(module, "anti_robot_filter", None)
    monkeypatch.setattr(module, "v8_process_response", lambda response, **kwargs: response)
    monkeypatch.setattr(module.Config, "DEMO_MODE", True)
    monkeypatch.setattr(module.Config, "DEMO_BUSINESS_NAME", "")

    bubbles = asyncio.run(
        bublee.process_message("demo-bot-fear-001", "me da miedo que suenes a bot")
    )

    lowered = " ".join(bubbles).lower()
    assert "bot" in lowered or "robot" in lowered
    assert "negocio" in lowered
    assert "cómo se llama" in lowered or "como se llama" in lowered


def test_demo_domino_uses_reasoning_tier_for_opening_stage(monkeypatch):
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._pending_buffers = {}
    bublee._admin_pending = {}
    bublee._last_reviewed_chat = None
    bublee._availability_pending_patient = None
    bublee._demo_sessions = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}
    bublee._orchestrator = None
    bublee._remember_route = lambda chat_id, route=None: None
    bublee._resolve_route = lambda chat_id, route=None: {"platform": "whatsapp"}
    bublee._try_conversation_core = lambda **kwargs: []
    bublee.search = types.SimpleNamespace(detect_procedure=lambda text: None)

    class FakeGenerator:
        llm = None

        def _postprocess(self, response, personality):
            return response

    class FakeLLM:
        def __init__(self):
            self.kwargs = []

        async def complete(self, messages, *args, **kwargs):
            self.kwargs.append(kwargs)
            return (
                "estoy dentro del chat de tu negocio ||| con el nombre sé desde dónde responder ||| dime cómo se llama y arrancamos",
                {"provider": "fake", "model": "fake"},
            )

    fake_llm = FakeLLM()

    fake_db = types.SimpleNamespace(
        get_clinic=lambda: {
            "name": "Clinica de las americas",
            "sector": "estetica",
            "admin_chat_ids": [],
        },
        get_admin=lambda chat_id: None,
        get_history=lambda chat_id, limit=None: [],
        save_message=lambda *args, **kwargs: None,
    )

    bublee.generator = FakeGenerator()
    monkeypatch.setattr(module, "db", fake_db)
    monkeypatch.setattr(module, "llm_engine", fake_llm)
    monkeypatch.setattr(module, "anti_robot_filter", None)
    monkeypatch.setattr(module, "v8_process_response", lambda response, **kwargs: response)
    monkeypatch.setattr(module.Config, "DEMO_MODE", True)
    monkeypatch.setattr(module.Config, "DEMO_BUSINESS_NAME", "")

    asyncio.run(
        bublee.process_message("demo-tier-001", "hola buenas")
    )

    assert fake_llm.kwargs
    assert fake_llm.kwargs[0]["model_tier"] == "reasoning"


def test_demo_domino_accepts_semantic_opening_without_forcing_three_bubbles(monkeypatch):
    module = load_bublee_module()
    bublee = module.BubleeUltra.__new__(module.BubleeUltra)
    bublee._pending_buffers = {}
    bublee._admin_pending = {}
    bublee._last_reviewed_chat = None
    bublee._availability_pending_patient = None
    bublee._demo_sessions = {}
    bublee._emoji_chats = set()
    bublee._chat_routes = {}
    bublee._orchestrator = None
    bublee._remember_route = lambda chat_id, route=None: None
    bublee._resolve_route = lambda chat_id, route=None: {"platform": "whatsapp"}
    bublee._try_conversation_core = lambda **kwargs: []
    bublee.search = types.SimpleNamespace(detect_procedure=lambda text: None)

    class FakeGenerator:
        llm = None

        def _postprocess(self, response, personality):
            return response

    class FakeLLM:
        async def complete(self, messages, *args, **kwargs):
            return (
                "aquí llevo el chat de tu negocio y con el nombre sé desde dónde responder sin hablarte genérico",
                {"provider": "fake", "model": "fake"},
            )

    fake_db = types.SimpleNamespace(
        get_clinic=lambda: {
            "name": "Clinica de las americas",
            "sector": "estetica",
            "admin_chat_ids": [],
        },
        get_admin=lambda chat_id: None,
        get_history=lambda chat_id, limit=None: [],
        save_message=lambda *args, **kwargs: None,
    )

    bublee.generator = FakeGenerator()
    monkeypatch.setattr(module, "db", fake_db)
    monkeypatch.setattr(module, "llm_engine", FakeLLM())
    monkeypatch.setattr(module, "anti_robot_filter", None)
    monkeypatch.setattr(module, "v8_process_response", lambda response, **kwargs: response)
    monkeypatch.setattr(module.Config, "DEMO_MODE", True)
    monkeypatch.setattr(module.Config, "DEMO_BUSINESS_NAME", "")

    bubbles = asyncio.run(
        bublee.process_message("demo-tier-002", "hola buenas")
    )

    lowered = " ".join(bubbles).lower()
    assert "aquí llevo el chat de tu negocio" in lowered or "aqui llevo el chat de tu negocio" in lowered
    assert "dime cómo se llama" not in lowered
