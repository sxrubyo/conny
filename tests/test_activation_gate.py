import asyncio
import importlib.util
import sys
import types
import uuid
from pathlib import Path


MODULE_PATH = Path("/home/ubuntu/conny/conny.py")
sys.path.insert(0, str(MODULE_PATH.parent))


def load_conny_module():
    module_name = f"conny_activation_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_new_instance_unknown_chat_requires_activation_token() -> None:
    module = load_conny_module()
    module.Config.DEMO_MODE = False
    module.auth_engine = None

    class FakeDB:
        def get_clinic(self):
            return {"setup_done": 0, "admin_chat_ids": [], "setup_step": "idle"}

        def get_admin(self, chat_id):
            return None

        def record_metric(self, *args, **kwargs):
            raise AssertionError("no debe llegar a fallback/error")

    module.db = FakeDB()
    conny = module.ConnyUltra.__new__(module.ConnyUltra)
    conny._chat_routes = {}
    conny._remember_route = lambda chat_id, route=None: None
    conny._handle_admin_message = lambda *args, **kwargs: (_ for _ in ()).throw(
        AssertionError("un no-admin no debe entrar al setup")
    )

    result = asyncio.run(conny.process_message("client-1", "Hey"))

    assert result == ["Ingresa tu Token de Activación para comenzar."]


def test_admin_pro_token_activation_creates_admin_role_and_consumes_token(monkeypatch) -> None:
    from conny_utils import generate_admin_activation_token
    from src.core.admin_engines import AuthEngine

    token = generate_admin_activation_token("Terminal Ops")

    class FakeDB:
        def __init__(self):
            self.sessions = {}
            self.admins = []
            self.consumed = []
            self.clinic = {"admin_chat_ids": []}

        def get_auth_session(self, chat_id):
            return self.sessions.get(chat_id)

        def set_auth_session(self, chat_id, flow, step, temp_data):
            self.sessions[chat_id] = {"flow": flow, "step": step, "temp_data": dict(temp_data)}

        def clear_auth_session(self, chat_id):
            self.sessions.pop(chat_id, None)

        def get_activation_token(self, raw):
            return {"token": token, "clinic_label": "ADMIN_PRO:Terminal Ops"} if raw == token else None

        def create_admin(self, **kwargs):
            self.admins.append(kwargs)
            return True

        def consume_activation_token(self, raw, chat_id):
            self.consumed.append((raw, chat_id))

        def get_clinic(self):
            return self.clinic

        def update_clinic(self, **kwargs):
            self.clinic.update(kwargs)

    fake_db = FakeDB()
    fake_conny = types.SimpleNamespace(db=fake_db)
    monkeypatch.setitem(sys.modules, "conny", fake_conny)

    auth = AuthEngine()

    assert auth.is_auth_message("admin-chat", token) is True
    assert asyncio.run(auth.process("admin-chat", token)) == ["Código Conny Pro válido. Cómo te llamas?"]
    assert asyncio.run(auth.process("admin-chat", "Santiago")) == ["Hola Santiago. Tu email?"]
    assert asyncio.run(auth.process("admin-chat", "santiago@example.com")) == ["Elige una contraseña segura"]
    assert asyncio.run(auth.process("admin-chat", "super-secret")) == ["Confirmas? (si/no)"]
    final = asyncio.run(auth.process("admin-chat", "si"))

    assert "Conny Pro Admin quedó activado" in final[0]
    assert fake_db.admins[0]["role"] == "admin_pro"
    assert fake_db.consumed == [(token, "admin-chat")]
    assert fake_db.clinic["admin_chat_ids"] == ["admin-chat"]


def test_activation_helpers_accept_admin_pro_tokens() -> None:
    from conny_utils import (
        generate_admin_activation_token,
        is_activation_token,
        is_admin_activation_token,
    )

    token = generate_admin_activation_token("API Dev")

    assert token.startswith("ADMN-")
    assert token == token.upper()
    assert is_admin_activation_token(token) is True
    assert is_activation_token(token) is True


def test_llm_service_error_exposes_quota_before_fallback() -> None:
    from src.core.globals import LLMServiceError

    err = RuntimeError(
        "HTTP 429: Gemini HTTP 429 (RESOURCE_EXHAUSTED): You exceeded your current quota"
    )
    wrapped = LLMServiceError("Todos los LLM fallaron", attempted=["gemini"], last_error=err)

    assert "cuota/rate limit" in wrapped.public_message
    assert "HTTP 429" in wrapped.public_message
    assert "gemini" in wrapped.public_message
