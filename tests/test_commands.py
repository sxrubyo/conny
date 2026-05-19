"""Tests for conny_commands.py"""
import sys
import asyncio
sys.path.insert(0, ".")


def _run(coro):
    return asyncio.run(coro)


def test_user_help_command():
    from conny_commands import CommandHandler
    handler = CommandHandler("test")
    result = _run(handler.handle("user123", "/ayuda", is_admin=False))
    assert result is not None
    assert "Comandos disponibles" in result[0]


def test_user_horarios():
    from conny_commands import CommandHandler
    handler = CommandHandler("test")
    clinic = {"schedule": "L-V 8am-6pm"}
    result = _run(handler.handle("user123", "/horarios", is_admin=False, clinic=clinic))
    assert result is not None
    assert "8am" in result[0]


def test_admin_pausa():
    from conny_commands import CommandHandler
    handler = CommandHandler("test")
    result = _run(handler.handle("admin1", "/pausa", is_admin=True))
    assert result is not None
    assert handler.is_paused()
    result = _run(handler.handle("admin1", "/reanudar", is_admin=True))
    assert not handler.is_paused()


def test_admin_personalidad():
    from conny_commands import CommandHandler
    handler = CommandHandler("test_cmd")
    result = _run(handler.handle("admin1", '/personalidad tono=formal nombre="Sofía"', is_admin=True))
    assert result is not None
    assert "actualizada" in result[0].lower()


def test_admin_aprender():
    from conny_commands import CommandHandler
    handler = CommandHandler("test_learn")
    result = _run(handler.handle("admin1", '/aprender ¿cuánto vale? → $80.000', is_admin=True))
    assert result is not None
    assert "listo" in result[0].lower() or "aprendido" in result[0].lower()


def test_not_a_command():
    from conny_commands import CommandHandler
    handler = CommandHandler("test")
    result = _run(handler.handle("user123", "hola quiero una cita", is_admin=False))
    assert result is None
