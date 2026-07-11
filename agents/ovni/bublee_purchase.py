"""
Bublee Purchase Flow — Proceso de compra/contratación de Bublee.

Cuando alguien quiere contratar Bublee para su negocio:
1. Detecta intención de compra
2. Presenta planes
3. Conecta con admin para cerrar

Planes:
- Starter: 1 agente, 1 canal (WhatsApp o Telegram), respuestas básicas
- Pro: 1 agente, multi-canal, búsqueda web, memoria avanzada
- Enterprise: Agentes ilimitados, API, sub-agentes dinámicos, /dreams
"""
from __future__ import annotations
import logging
from typing import Optional, Dict

log = logging.getLogger("bublee.purchase")

ADMIN_CONTACT = "3124348669"

PLANS = {
    "starter": {
        "name": "Starter",
        "price": "Consultar con el equipo",
        "features": [
            "1 agente en 1 canal (WhatsApp o Telegram)",
            "Respuestas inteligentes 24/7",
            "Memoria básica de conversaciones",
            "Personalidad adaptable",
        ],
    },
    "pro": {
        "name": "Pro",
        "price": "Consultar con el equipo",
        "features": [
            "1 agente multi-canal",
            "Búsqueda web en tiempo real",
            "Memoria avanzada + aprendizaje",
            "Modo bot con botones",
            "Reportes semanales",
        ],
    },
    "enterprise": {
        "name": "Enterprise",
        "price": "Personalizado",
        "features": [
            "Agentes ilimitados",
            "Sub-agentes dinámicos desde WhatsApp",
            "API completa",
            "Modo /dreams (auto-mejora nocturna)",
            "Soporte prioritario",
            "White-label disponible",
        ],
    },
}


class PurchaseDetector:
    """Detecta intención de compra en mensajes."""

    PURCHASE_SIGNALS = [
        "cuanto cuesta", "cuanto vale", "precio", "planes",
        "quiero contratarla", "quiero contratar", "como la consigo",
        "me interesa", "como puedo tenerla", "la quiero",
        "how much", "pricing", "plans", "i want this", "how to get",
        "quiero una asi", "como consigo una",
    ]

    def detect(self, text: str) -> bool:
        text_lower = text.lower().strip()
        return any(signal in text_lower for signal in self.PURCHASE_SIGNALS)

    def build_response(self) -> str:
        """Genera la respuesta de Bublee cuando detecta intención de compra."""
        return (
            "Tenemos diferentes planes dependiendo de lo que necesites ||| "
            "Te conecto con el equipo de Kimika AI para que te den los detalles "
            f"y armen algo a tu medida ||| Escríbele a Santiago: {ADMIN_CONTACT}"
        )

    def build_teaser(self) -> str:
        """Mini-preview de lo que incluye."""
        return (
            "Basicamente hay 3 opciones ||| "
            "Starter: un agente en un canal, respuestas 24/7 ||| "
            "Pro: multi-canal, búsqueda web, memoria avanzada ||| "
            f"Enterprise: agentes ilimitados, sub-agentes dinámicos, API ||| "
            f"Para precios específicos escribele al equipo: {ADMIN_CONTACT}"
        )


purchase_detector = PurchaseDetector()
