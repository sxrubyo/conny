from __future__ import annotations

import asyncio
import importlib.util
import sys
import types
import uuid
from pathlib import Path

import pytest


MODULE_PATH = Path("/home/ubuntu/bublee/instances/clinica-de-las-americas/bublee.py")


def load_bublee_module():
    module_name = f"bublee_profile_matrix_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class FakeGenerator:
    llm = None

    def _postprocess(self, response, personality):
        return response


class CountingLLM:
    def __init__(self, response):
        self.response = response
        self.calls = 0

    async def complete(self, *args, **kwargs):
        self.calls += 1
        if isinstance(self.response, (list, tuple)):
            idx = min(self.calls - 1, len(self.response) - 1)
            return self.response[idx], {"provider": "fake", "model": "fake"}
        return self.response, {"provider": "fake", "model": "fake"}


class WeakSearch:
    def __init__(self):
        self.calls = []

    def detect_procedure(self, text):
        return None

    async def search_business_link(self, name):
        self.calls.append(name)
        return ("info muy corta", "")


def build_demo_bublee(module, *, history=None, llm_response="respuesta no usada", core_reply=None):
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
    bublee._try_conversation_core = lambda **kwargs: list(core_reply) if core_reply else []

    search = WeakSearch()
    llm = CountingLLM(llm_response)
    bublee.search = search
    bublee.generator = FakeGenerator()
    initial_history = list(history or [])
    stores = {}

    def _get_store(chat_id):
        return stores.setdefault(chat_id, [dict(item) for item in initial_history])

    module.db = types.SimpleNamespace(
        get_clinic=lambda: {
            "name": "Clinica de las americas",
            "sector": "estetica",
            "admin_chat_ids": [],
        },
        get_admin=lambda chat_id: None,
        get_history=lambda chat_id, limit=None: (
            _get_store(chat_id)[-limit:] if limit else list(_get_store(chat_id))
        ),
        save_message=lambda chat_id, role, msg: _get_store(chat_id).append({"role": role, "content": msg}),
    )
    module.llm_engine = llm
    module.anti_robot_filter = None
    module.v8_process_response = lambda response, **kwargs: response
    module.Config.DEMO_MODE = True
    module.Config.DEMO_BUSINESS_NAME = ""
    return bublee, search, llm


def normalize(value: str) -> str:
    return " ".join((value or "").lower().split())


def run_dialogue(bublee, chat_id: str, messages: list[str]) -> list[str]:
    outputs = []
    for message in messages:
        bubbles = asyncio.run(bublee.process_message(chat_id, message))
        outputs.append(" ||| ".join(bubbles))
    return outputs


OPENING_INPUTS = [
    "hola",
    "holaa",
    "buenas",
    "buen día",
    "hey",
    "hola bublee",
    "quiero probarte",
    "quiero una demo",
    "tengo un negocio",
    "me gustaria probarte",
    "como funcionas",
    "qué haces",
]


CLARIFY_INPUTS = [
    "a que te refieres",
    "a que te refieres? no te entiendo",
    "no te entiendo",
    "explícamelo simple",
    "que es eso",
    "para que",
    "para qué quieres eso",
    "como así",
    "qué quieres decir",
    "no entiendo nada",
    "háblame claro",
    "bajalo a tierra",
]


BUSINESS_NAMES = [
    "Clinica de los Molinos",
    "Spa Luna Viva",
    "Taller Norte 73",
    "Gym Horizonte",
    "Abogados Rivera & Asociados",
    "Pet House Laureles",
    "Casa Magnolia Eventos",
    "Optica Prisma",
    "Dental Nova",
    "Nébula Tattoo Studio",
    "Farmacia Los Cedros",
    "Restaurante Anfora",
    "Hotel Brisa Alta",
    "Inmobiliaria Raiz Viva",
    "Academia Cumbre",
    "Estudio Marea",
    "Consultorio Aura",
    "Barberia Distrito 11",
]


SUBMISSION_TEMPLATES = [
    "mi negocio se llama {name}",
    "el nombre de mi negocio es {name}",
    "nuestro negocio se llama {name}",
    "mi empresa se llama {name}",
    "se llama {name}",
    "mi negocio es {name}",
    "la clínica se llama {name}",
]


BUSINESS_CASES = [
    {
        "case_id": f"profile-{idx:03d}",
        "business_name": name,
        "message": template.format(name=name),
    }
    for idx, (name, template) in enumerate(
        [(name, template) for name in BUSINESS_NAMES for template in SUBMISSION_TEMPLATES],
        start=1,
    )
]


FORBIDDEN_DEMO_TOKENS = (
    "clinica de las americas",
    "clínica las américas",
    "del equipo",
    "recepcionista virtual",
    "gracias por contactarme",
    "tiempo libre",
    "realmente importa",
    "ya quedé al frente",
    "ya quede al frente",
    "no encontré",
    "no encontre",
    "google",
    "me parece que",
    "paciente",
    "servicios ofrecen",
)


@pytest.mark.parametrize("user_msg", OPENING_INPUTS)
def test_demo_opening_matrix_stays_human_and_on_demo_rails(user_msg):
    module = load_bublee_module()
    bublee, _search, llm = build_demo_bublee(
        module,
        llm_response=(
            "soy Bublee ||| aquí me estás probando como si mañana me dejaran al frente del WhatsApp de tu negocio ||| dime cómo se llama y arrancamos con contexto"
        ),
    )

    bubbles = asyncio.run(bublee.process_message(f"matrix-opening-{abs(hash(user_msg))}", user_msg))
    lowered = normalize(" ".join(bubbles))

    assert llm.calls >= 1
    assert "soy bublee" in lowered
    assert "whatsapp de tu negocio" in lowered
    assert ("nombre" in lowered or "cómo se llama" in lowered or "como se llama" in lowered) and "negocio" in lowered
    for token in FORBIDDEN_DEMO_TOKENS:
        assert token not in lowered


@pytest.mark.parametrize("user_msg", CLARIFY_INPUTS)
def test_demo_clarify_matrix_stays_short_and_non_markety(user_msg):
    module = load_bublee_module()
    history = [
        {"role": "user", "content": "hola"},
        {"role": "assistant", "content": "soy Bublee. aquí me pruebas como si ya estuviera atendiendo el WhatsApp de tu negocio"},
    ]
    bublee, _search, llm = build_demo_bublee(
        module,
        history=history,
        llm_response=(
            "te lo pongo simple ||| si sé cómo se llama tu negocio, ya te respondo como si ese WhatsApp fuera tuyo ||| sin ese contexto te hablaría genérico"
        ),
    )

    bubbles = asyncio.run(bublee.process_message(f"matrix-clarify-{abs(hash(user_msg))}", user_msg))
    lowered = normalize(" ".join(bubbles))

    assert llm.calls >= 1
    assert "te lo pongo simple" in lowered
    assert "whatsapp" in lowered or "chat" in lowered
    assert "contexto" in lowered or "genérico" in lowered or "generico" in lowered
    assert "me gustaría saber un poco más" not in lowered
    assert "tono y el estilo" not in lowered


@pytest.mark.parametrize("case", BUSINESS_CASES, ids=[case["case_id"] for case in BUSINESS_CASES])
def test_demo_business_matrix_captures_name_without_guessing(case):
    module = load_bublee_module()
    bublee, search, llm = build_demo_bublee(
        module,
        llm_response=(
            f"listo, ya me ubiqué con {case['business_name']} ||| ya tengo claro el contexto del negocio ||| háblame como si fueras un cliente real y arrancamos"
        ),
    )

    chat_id = f"matrix-business-{case['case_id']}"
    bubbles = asyncio.run(bublee.process_message(chat_id, case["message"]))
    lowered = normalize(" ".join(bubbles))
    session_name = bublee._demo_sessions[f"demo_{chat_id}_name"]

    assert llm.calls >= 1
    assert search.calls == [case["business_name"]]
    assert session_name == case["business_name"]
    assert normalize(case["business_name"]) in lowered
    assert "ya tengo claro el contexto del negocio" in lowered
    assert "cliente real" in lowered or "cliente" in lowered
    for token in FORBIDDEN_DEMO_TOKENS:
        assert token not in lowered


def test_demo_owner_questions_after_business_keep_context_without_reasking():
    module = load_bublee_module()
    bublee, _search, llm = build_demo_bublee(
        module,
        llm_response=[
            "soy Bublee ||| aquí me estás probando como si ya llevara el WhatsApp de tu negocio ||| dime cómo se llama y arrancamos con contexto",
            "listo, ya me ubiqué con clinica de los molinos ||| ya tengo claro el contexto del negocio ||| háblame como si fueras un cliente real y arrancamos",
            "me sirve para ajustar tono, contexto y tipo de cliente ||| con eso ya respondo desde tu negocio y no genérico",
            "tranquilo ||| con lo que ya me diste me basta para arrancar sin forzarte más info",
            "de una ||| tírame el mensaje como si viniera de un cliente real y lo trabajo desde ahí",
        ],
    )

    outputs = run_dialogue(
        bublee,
        "owner-after-business",
        [
            "hola",
            "mi negocio se llama clinica de los molinos",
            "ok pero para que te serviria eso",
            "no quiero darte mucha info aun",
            "quiero ver como respondes",
        ],
    )
    why_reply = normalize(outputs[2])
    low_info_reply = normalize(outputs[3])
    simulation_reply = normalize(outputs[4])

    assert llm.calls >= 2
    assert "tono" in why_reply or "contexto" in why_reply or "genérico" in why_reply or "generico" in why_reply
    assert "nombre del negocio" not in low_info_reply
    assert any(
        marker in low_info_reply
        for marker in ("me basta para arrancar", "base suficiente para arrancar", "cliente real", "lo trabajo desde ahí")
    )
    assert "tírame el mensaje" in outputs[4] or "tirame el mensaje" in simulation_reply
    assert "cliente real" in simulation_reply


def test_demo_bot_skepticism_does_not_claim_to_be_human():
    module = load_bublee_module()
    bublee, _search, llm = build_demo_bublee(
        module,
        llm_response=[
            "de una ||| dime cómo se llama tu negocio y arrancamos con contexto",
            "listo, ya me ubiqué con spa luna viva ||| ya tengo claro el contexto del negocio ||| háblame como si fueras un cliente real",
            "esa es justamente la idea de la prueba ||| responder natural, con criterio y sin libreto raro",
        ],
    )

    outputs = run_dialogue(
        bublee,
        "owner-bot-skeptic",
        [
            "tengo un negocio",
            "se llama spa luna viva",
            "me da miedo que suenes a bot",
        ],
    )
    reply = normalize(outputs[-1])

    assert llm.calls >= 2
    assert "persona real" not in reply
    assert "te lo prometo" not in reply
    assert "libreto" in reply or "natural" in reply
    assert "cliente" in reply or "prueba" in reply


def test_demo_weak_context_does_not_invent_price():
    module = load_bublee_module()
    bublee, _search, _llm = build_demo_bublee(
        module,
        core_reply=["el corte de cabello es 20 mil pesos", "quieres cita para mañana"],
    )

    outputs = run_dialogue(
        bublee,
        "weak-price",
        [
            "mi negocio se llama barberia distrito 11",
            "hola, cuanto vale el corte",
        ],
    )
    reply = normalize(outputs[-1])

    assert "20 mil" not in reply
    assert "pesos" not in reply
    assert any(
        marker in reply
        for marker in (
            "depende del caso",
            "número exacto",
            "numero exacto",
            "te lo confirmo",
            "producto exacto",
            "sin inventar",
        )
    )


def test_demo_weak_context_does_not_claim_stock():
    module = load_bublee_module()
    bublee, _search, _llm = build_demo_bublee(
        module,
        core_reply=["sí lo tenemos disponible", "te lo separo de una"],
    )

    outputs = run_dialogue(
        bublee,
        "weak-stock",
        [
            "mi negocio se llama farmacia los cedros",
            "hola, necesito un medicamento y quiero saber si lo tienen",
        ],
    )
    reply = normalize(outputs[-1])

    assert "sí lo tenemos" not in reply
    assert "si lo tenemos" not in reply
    assert "nombre exacto" in reply or "referencia" in reply or "presentación" in outputs[-1] or "presentacion" in reply


def test_demo_weak_context_does_not_claim_availability():
    module = load_bublee_module()
    bublee, _search, _llm = build_demo_bublee(
        module,
        core_reply=["para mañana en la tarde no tengo el calendario al día", "te averiguo y te escribo"],
    )

    outputs = run_dialogue(
        bublee,
        "weak-availability",
        [
            "mi negocio se llama spa luna viva",
            "hola, tienen agenda mañana en la tarde",
        ],
    )
    reply = normalize(outputs[-1])

    assert "tenemos algunas citas" not in reply
    assert "estoy revisando" not in reply
    assert "calendario" not in reply
    assert "te averiguo y te escribo" not in reply
    assert "qué hora te acomodaría mejor" in outputs[-1] or "que hora te acomodaria mejor" in reply
