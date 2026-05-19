"""Demo mode multilingual support."""
from conny_i18n import get_i18n, SUPPORTED_LANGUAGES

_I18N = None
try:
    _I18N = get_i18n()
except Exception:
    pass


def demo_t(key: str) -> str:
    if _I18N:
        return _I18N.demo(key)
    defaults = {
        "enter_name": "Enter your name",
        "enter_email": "Enter your email",
        "enter_phone": "Enter your phone",
        "ask_interest": "What are you interested in?",
        "schedule_demo": "Schedule demo",
        "demo_confirmed": "Demo confirmed! We'll contact you soon.",
        "company_name": "Company name",
        "company_size": "Company size",
    }
    return defaults.get(key, key)


def get_demo_greeting(lang: str = "es") -> str:
    greetings = {
        "es": "¡Hola! Te gustaría ver una demostración de Conny?",
        "en": "Hello! Would you like to see a demo of Conny?",
        "pt": "Olá! Você gostaria de ver uma demonstração da Conny?",
        "fr": "Bonjour! Voulez-vous voir une démo de Conny?",
        "de": "Hallo! Möchten Sie eine Demo von Conny sehen?",
    }
    return greetings.get(lang, greetings["es"])