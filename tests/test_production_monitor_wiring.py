import asyncio
import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class FakeDB:
    def __init__(self):
        self.saved = []

    def save_message(self, chat_id, role, content, **kwargs):
        self.saved.append((chat_id, role, content, kwargs))

    def get_clinic(self):
        return {"name": "Clinica", "persona_config": '{"name": "Lucia"}'}


class FakeLLM:
    def __init__(self):
        self.calls = 0

    async def complete(self, *args, **kwargs):
        self.calls += 1
        return "respuesta directa", {"model": "direct-model", "provider": "fake"}


class FakeAnalyzer:
    def __init__(self):
        self.calls = 0

    def analyze(self, text, history=None):
        self.calls += 1
        return {"text": text, "history": history or []}


class FakeReasoning:
    def __init__(self):
        self.calls = 0

    async def reason(self, text, analysis, clinic, history, conv_state):
        self.calls += 1
        return {
            "response_strategy": "responder con datos del negocio",
            "confidence": 0.9,
            "_metadata": {"model": "reason-model", "provider": "fake"},
        }


class FakeGenerator:
    def __init__(self, response="respuesta central"):
        self.calls = 0
        self.response = response
        self.kwargs = None

    async def generate(self, **kwargs):
        self.calls += 1
        self.kwargs = kwargs
        return self.response


class FakeRuntime:
    def __init__(self, generator_response="respuesta central"):
        self._instance_id = "test"
        self._agent_name = "Bublee"
        self.analyzer = FakeAnalyzer()
        self.reasoning = FakeReasoning()
        self.generator = FakeGenerator(generator_response)
        self.sent_messages = []

    def _split_bubbles(self, text, chat_id=None):
        return [part.strip() for part in text.split("|||") if part.strip()]

    async def _send_message(self, chat_id, text):
        self.sent_messages.append((chat_id, text))


class FakeMemory:
    def recall_patient(self, chat_id):
        return {"name": "Valen"}

    def get_context_for_prompt(self, chat_id):
        return ""

    def remember_patient(self, chat_id, data):
        return None


class FakeSentiment:
    def should_escalate(self, text, history):
        return False, ""


class FakeLanguage:
    def detect(self, text):
        return "es"

    def get_language_instruction(self, detected):
        return ""


class FakeLearning:
    async def get_teachings(self, instance_id, limit=20):
        return []

    async def learn_from_turn(self, instance_id, text, response):
        return None


class FakeUncertainty:
    def __init__(self, confidence):
        self.confidence = confidence
        self.gaps = []

    def confidence_score(self, response, text, history):
        return self.confidence

    async def log_gap(self, instance_id, text, response, confidence, chat_id):
        self.gaps.append((instance_id, text, response, confidence, chat_id))


def _install_fake_modules(confidence=0.9, business_context=None):
    db = FakeDB()
    llm = FakeLLM()
    uncertainty = FakeUncertainty(confidence)
    if business_context is None:
        business_context = (
            "Servicios confirmados por admin: consulta, horarios, orientación inicial, "
            "valoración, precios cargados y disponibilidad general para pacientes."
        )

    fake_bublee = types.SimpleNamespace(
        db=db,
        llm_engine=llm,
        kb=None,
        v8_process_response=lambda response, **kwargs: response,
    )
    fake_smart = types.SimpleNamespace(
        CrossSessionMemory=lambda instance_id: FakeMemory(),
        SentimentTracker=lambda: FakeSentiment(),
        LanguageDetector=lambda: FakeLanguage(),
        get_time_greeting=lambda: "hola",
        is_conversation_ending=lambda text: False,
        get_natural_closing=lambda tone: "hasta luego",
    )
    fake_prompt_ops = types.SimpleNamespace(
        build_business_context=lambda clinic, db_obj, instance_id: business_context
    )
    fake_learning = types.SimpleNamespace(learning_engine=FakeLearning())
    fake_uncertainty = types.SimpleNamespace(uncertainty_detector=uncertainty)

    replacements = {
        "bublee": fake_bublee,
        "bublee_smart_features": fake_smart,
        "bublee_core.prompt_ops": fake_prompt_ops,
        "bublee_learning": fake_learning,
        "bublee_uncertainty": fake_uncertainty,
    }
    previous = {name: sys.modules.get(name) for name in replacements}
    sys.modules.update(replacements)
    return previous, db, llm, uncertainty


def _restore_modules(previous):
    for name, module in previous.items():
        if module is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = module


def test_production_uses_central_reasoning_generator_before_direct_llm():
    from src.core.production_monitor import BubleeProduction

    previous, db, llm, _ = _install_fake_modules(confidence=0.9)
    try:
        runtime = FakeRuntime(generator_response="respuesta central")
        result = asyncio.run(BubleeProduction(runtime).handle(
            chat_id="patient-1",
            text="hola, quiero saber horarios",
            clinic={"name": "Clinica", "admin_chat_ids": ["admin-1"], "services": ["consulta"]},
            history=[],
            conv_state={},
        ))
    finally:
        _restore_modules(previous)

    assert result == ["respuesta central"]
    assert runtime.analyzer.calls == 1
    assert runtime.reasoning.calls == 1
    assert runtime.generator.calls == 1
    assert llm.calls == 1
    assert db.saved[-1][1] == "assistant"
    assert db.saved[-1][2] == "respuesta central"


def test_low_confidence_alerts_admin_without_patient_fallback():
    from src.core.production_monitor import BubleeProduction

    previous, db, llm, uncertainty = _install_fake_modules(confidence=0.2)
    try:
        runtime = FakeRuntime(generator_response="no tengo esa info")
        result = asyncio.run(BubleeProduction(runtime).handle(
            chat_id="patient-2",
            text="cuanto cuesta la consulta",
            clinic={"name": "Clinica", "admin_chat_ids": ["admin-1"], "services": ["consulta"]},
            history=[],
            conv_state={},
        ))
    finally:
        _restore_modules(previous)

    assert result == []
    assert len(runtime.sent_messages) == 2
    assert runtime.sent_messages[0][1] == "respuesta directa"
    assert runtime.sent_messages[1][1] == "respuesta directa"
    assert uncertainty.gaps
    assert llm.calls == 2
    assert [row[1] for row in db.saved] == ["user"]
    assert all("dame un momento que verifico" not in row[2] for row in db.saved)


def test_insufficient_confirmed_knowledge_alerts_admin_without_llm_or_patient_reply():
    from src.core.production_monitor import BubleeProduction

    previous, db, llm, _ = _install_fake_modules(confidence=0.9, business_context="")
    try:
        runtime = FakeRuntime(generator_response="respuesta no deberia salir")
        result = asyncio.run(BubleeProduction(runtime).handle(
            chat_id="patient-3",
            text="Me interesa una cirugía",
            clinic={"name": "Clinica", "admin_chat_ids": ["admin-1"], "services": ["consulta general"]},
            history=[],
            conv_state={},
        ))
    finally:
        _restore_modules(previous)

    assert result == []
    assert len(runtime.sent_messages) == 2
    assert runtime.sent_messages[0][1] == "respuesta directa"
    assert runtime.sent_messages[1][1] == "respuesta directa"
    assert runtime.generator.calls == 0
    assert llm.calls == 2
    assert [row[1] for row in db.saved] == ["user"]


def test_local_cache_intercepts_taught_questions():
    from src.core.production_monitor import BubleeProduction

    previous, db, llm, _ = _install_fake_modules(confidence=0.9)
    
    class MockLearning:
        async def get_teachings(self, instance_id, limit=100):
            return [{"question": "[admin enseñó] cuanto vale el botox", "answer": "Desde 800.000 COP"}]
        async def learn_from_turn(self, instance_id, text, response):
            return None
            
    import sys
    sys.modules["bublee_learning"].learning_engine = MockLearning()
    
    try:
        runtime = FakeRuntime(generator_response="respuesta generador")
        result = asyncio.run(BubleeProduction(runtime).handle(
            chat_id="patient-4",
            text="cuánto vale el BOTOX??",
            clinic={"name": "Clinica", "admin_chat_ids": ["admin-1"], "services": ["consulta"]},
            history=[],
            conv_state={},
        ))
    finally:
        _restore_modules(previous)

    assert result == ["Desde 800.000 COP"]
    assert llm.calls == 0
    assert runtime.generator.calls == 0
    assert db.saved[-1][1] == "assistant"
    assert db.saved[-1][2] == "Desde 800.000 COP"


def test_booking_request_without_calendly_escalates_to_admin():
    from src.core.production_monitor import BubleeProduction

    previous, db, llm, _ = _install_fake_modules(confidence=0.9, business_context="Clinica Las Americas es un centro de medicina estetica y cirugia plastica premium con Botox.")
    try:
        runtime = FakeRuntime(generator_response="respuesta generador")
        result = asyncio.run(BubleeProduction(runtime).handle(
            chat_id="patient-5",
            text="Hola, tienen espacio disponible para una cita?",
            clinic={"name": "Clinica", "admin_chat_ids": ["admin-1"], "services": ["Botox"]},
            history=[],
            conv_state={},
        ))
    finally:
        _restore_modules(previous)

    assert result == ["respuesta generador"]
    assert len(runtime.sent_messages) == 3
    assert runtime.sent_messages[0][1] == "respuesta directa"
    assert runtime.sent_messages[1][1] == "respuesta directa"
    assert "Conversación en curso" in runtime.sent_messages[2][1]
    assert llm.calls == 2


if __name__ == "__main__":
    test_production_uses_central_reasoning_generator_before_direct_llm()
    test_low_confidence_alerts_admin_without_patient_fallback()
    test_insufficient_confirmed_knowledge_alerts_admin_without_llm_or_patient_reply()
    test_local_cache_intercepts_taught_questions()
    test_booking_request_without_calendly_escalates_to_admin()
    print("production_monitor_wiring tests passed")
