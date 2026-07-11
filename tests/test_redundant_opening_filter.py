from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_redundant_greeting_and_intro_are_removed_after_first_turn():
    from src.core.globals import ResponseGenerator

    generator = ResponseGenerator(llm=None)
    history = [{"role": "assistant", "content": "Hola, soy Bublee de la clínica."}]
    cleaned = generator._strip_redundant_turn_opening(
        "Hola! Soy Bublee, la recepcionista virtual de Clínica Las Américas. En qué puedo ayudarte hoy?",
        user_msg="Cómo estás",
        history=history,
    )
    assert cleaned == ""


def test_identity_question_keeps_honest_identity_but_removes_redundant_hola():
    from src.core.globals import ResponseGenerator

    generator = ResponseGenerator(llm=None)
    history = [{"role": "assistant", "content": "Hola, soy Bublee de la clínica."}]
    cleaned = generator._strip_redundant_turn_opening(
        "Hola! Sí, soy Bublee, una IA que ayuda al equipo de la clínica.",
        user_msg="Eres una IA?",
        history=history,
    )
    assert not cleaned.lower().startswith("hola")
    assert "soy bublee" in cleaned.lower()
    assert "ia" in cleaned.lower()


if __name__ == "__main__":
    test_redundant_greeting_and_intro_are_removed_after_first_turn()
    test_identity_question_keeps_honest_identity_but_removes_redundant_hola()
    print("redundant_opening_filter tests passed")
