from __future__ import annotations

import importlib.util
import sys
import uuid
from pathlib import Path
import tempfile


MODULE_PATH = Path("/home/ubuntu/bublee/instances/clinica-de-las-americas/bublee_domino.py")


def load_domino_module():
    module_name = f"bublee_domino_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_domino_payload_first_turn_prioritizes_action_over_branding():
    module = load_domino_module()

    payload = module.build_demo_domino_payload(
        user_text="hola buenas",
        history=[],
        business_name="",
        business_ctx="",
        found_online=False,
        explain_name=False,
    )

    assert payload["stage"] == "enter-demo"
    assert "AMO / DUEÑO" in payload["system"]
    assert "ACCIÓN DE ESTE TURNO" in payload["system"]
    assert "de clínica las américas" not in payload["system"].lower()
    assert "no te describas como bot, software, recepcionista virtual o producto" in payload["system"].lower()


def test_domino_payload_explain_name_stage_is_explicit():
    module = load_domino_module()

    payload = module.build_demo_domino_payload(
        user_text="a que te refieres? no te entiendo",
        history=[{"role": "user", "content": "hola"}],
        business_name="",
        business_ctx="",
        found_online=False,
        explain_name=True,
    )

    assert payload["stage"] == "clarify-demo"
    assert "explicar para qué necesitas el nombre del negocio" in payload["system"].lower()


def test_domino_payload_enter_demo_demands_short_structured_opening_and_name_request():
    module = load_domino_module()

    payload = module.build_demo_domino_payload(
        user_text="hola parce, como funciona esto?",
        history=[],
        business_name="",
        business_ctx="",
        found_online=False,
        explain_name=False,
    )

    lowered = payload["system"].lower()
    assert payload["stage"] == "enter-demo"
    assert "responde en 2 o 3 burbujas" in lowered
    assert "deja completas las ideas" in lowered
    assert "pide el nombre del negocio" in lowered


def test_domino_routes_greetings_after_business_back_to_identity_layer():
    module = load_domino_module()

    assert module.should_route_demo_to_domino(
        user_text="hola otra vez",
        business_name="Clinica de los Molinos",
        history=[{"role": "assistant", "content": "ok"}],
    ) is True


def test_domino_routes_customer_simulation_through_identity_layer_when_business_exists():
    module = load_domino_module()

    assert module.should_route_demo_to_domino(
        user_text="hola, cuanto vale el botox",
        business_name="Clinica de los Molinos",
        history=[{"role": "assistant", "content": "ok"}],
    ) is True


def test_domino_payload_simulate_stage_keeps_action_inside_business_chat():
    module = load_domino_module()

    payload = module.build_demo_domino_payload(
        user_text="hola, cuanto vale el botox",
        history=[{"role": "assistant", "content": "ya tengo clinica de los molinos en contexto"}],
        business_name="Clinica de los Molinos",
        business_ctx="clinica estética en medellín",
        found_online=True,
    )

    lowered = payload["system"].lower()
    assert payload["stage"] == "simulate"
    assert "ya estás adentro del trabajo" not in lowered
    assert "responde con criterio operativo" in lowered
    assert "volver meta la demo" in lowered
    assert "deja de hablar de demo" in lowered


def test_domino_payload_reset_stage_stays_business_neutral():
    module = load_domino_module()

    payload = module.build_demo_domino_payload(
        user_text="empezar de nuevo",
        history=[{"role": "assistant", "content": "ok"}],
        business_name="Clinica de los Molinos",
        business_ctx="",
        found_online=False,
        force_stage="reset-demo",
    )

    assert payload["stage"] == "reset-demo"
    assert "branding heredado" in payload["system"].lower()
    assert "reiniciar la demo" in payload["system"].lower()


def test_domino_payload_bind_business_stage_pushes_to_real_simulation():
    module = load_domino_module()

    payload = module.build_demo_domino_payload(
        user_text="mi negocio se llama clinica de los molinos",
        history=[],
        business_name="Clinica de los Molinos",
        business_ctx="clinica estética en medellín",
        found_online=True,
        force_stage="bind-business",
    )

    lowered = payload["system"].lower()
    assert payload["stage"] == "bind-business"
    assert "simulación real" in lowered or "simulacion real" in lowered
    assert "no recites plantillas" in lowered


def test_domino_payload_bind_business_forces_client_invitation_without_takeover():
    module = load_domino_module()

    payload = module.build_demo_domino_payload(
        user_text="mi negocio se llama clinica de los molinos",
        history=[],
        business_name="Clinica de los Molinos",
        business_ctx="info muy corta",
        found_online=False,
        force_stage="bind-business",
    )

    lowered = payload["system"].lower()
    assert "responde en 2 o 3 burbujas" in lowered
    assert "cliente real" in lowered or "cliente" in lowered
    assert "no digas que ya quedaste al frente" in lowered or "no uses lenguaje de takeover" in lowered


def test_domino_ignores_bootstrap_openclaw_memory_noise():
    module = load_domino_module()

    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp)
        memory_dir = workspace / "memory"
        memory_dir.mkdir(parents=True, exist_ok=True)
        (workspace / "SOUL.md").write_text("# SOUL\nalma util", encoding="utf-8")
        (workspace / "USER.md").write_text("# USER\nsantiago", encoding="utf-8")
        (workspace / "IDENTITY.md").write_text("# IDENTITY\neco nova", encoding="utf-8")
        (memory_dir / "2026-04-09-noise.md").write_text(
            "# Session\n"
            "- Session Key: abc\n"
            "assistant: New session started\n"
            "user: Run your Session Startup sequence - read the required files before responding\n"
            "Current time: now\n",
            encoding="utf-8",
        )
        module.OPENCLAW_WORKSPACE = workspace
        module.load_domino_sources.cache_clear()
        payload = module.build_demo_domino_payload(
            user_text="hola buenas",
            history=[],
            business_name="",
            business_ctx="",
            found_online=False,
            explain_name=False,
        )

        lowered = payload["system"].lower()
        assert "run your session startup sequence" not in lowered
        assert "new session started" not in lowered
        assert "current time:" not in lowered


def test_domino_tone_guard_flags_consultive_demo_opening():
    module = load_domino_module()

    issues = module.demo_opening_tone_issues(
        "con la gestión de tus mensajes. Para empezar, cuál es el nombre de tu negocio? "
        "con eso, puedo entender mejor cómo puedo apoyarte de manera efectiva"
    )

    assert issues
    assert any("consult" in issue or "abstract" in issue for issue in issues)


def test_domino_tone_guard_flags_precise_explanatory_opening():
    module = load_domino_module()

    issues = module.demo_opening_tone_issues(
        "lo que haría aquí es atender tus preguntas. Para hacerlo de la mejor manera, "
        "necesito saber el nombre de tu negocio para entender mejor el contexto"
    )

    assert issues
    assert any("abstract" in issue for issue in issues)


def test_domino_tone_guard_flags_customer_service_generic_phrasing():
    module = load_domino_module()

    issues = module.demo_opening_tone_issues(
        "llevo el control de este chat. para darte una mejor atención necesito saber "
        "el nombre del negocio con el que estoy interactuando para tener una idea más clara"
    )

    assert issues
    assert any("consult" in issue or "abstract" in issue for issue in issues)


def test_domino_soul_excerpt_avoids_boundary_noise():
    module = load_domino_module()

    excerpt = module._soul_excerpt(
        "Be genuinely helpful, not performatively helpful. "
        "Have opinions. "
        "Remember you're a guest. "
        "Each session, you wake up fresh."
    )

    lowered = excerpt.lower()
    assert "be genuinely helpful" in lowered
    assert "have opinions" in lowered
    assert "guest" not in lowered
    assert "wake up fresh" not in lowered
