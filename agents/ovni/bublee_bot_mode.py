"""
Bublee Bot Mode — Modo interactivo con botones reales de WhatsApp.

El admin puede activarlo con: /bot on
Se desactiva con: /bot off

Cuando está activo, Bublee envía botones interactivos para:
- Menú principal (Ver precios, Agendar cita, Hablar con humano)
- Opciones de servicio
- Confirmaciones rápidas (Si/No)
"""
from __future__ import annotations
import os
import logging
import httpx
from typing import Dict, List, Optional

log = logging.getLogger("bublee.bot_mode")

BRIDGE_URL = os.getenv("WHATSAPP_BRIDGE_URL", "http://127.0.0.1:8002")


class BotMode:
    """Gestiona el modo bot con botones interactivos."""

    def __init__(self):
        self._enabled_chats: set = set()
        self._menus: Dict[str, Dict] = {}

    def is_enabled(self, chat_id: str) -> bool:
        return chat_id in self._enabled_chats

    def enable(self, chat_id: str):
        self._enabled_chats.add(chat_id)
        log.info(f"[bot_mode] enabled for {chat_id}")

    def disable(self, chat_id: str):
        self._enabled_chats.discard(chat_id)
        log.info(f"[bot_mode] disabled for {chat_id}")

    async def send_buttons(self, chat_id: str, text: str,
                           buttons: List[Dict], footer: str = "") -> bool:
        """Send a button message via the bridge."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.post(
                    f"{BRIDGE_URL}/send-buttons",
                    json={
                        "to": chat_id,
                        "text": text,
                        "buttons": buttons,
                        "footer": footer,
                    },
                )
                return r.status_code == 200
        except Exception as e:
            log.error(f"[bot_mode] send_buttons error: {e}")
            return False

    async def send_list(self, chat_id: str, text: str, sections: List[Dict],
                        button_text: str = "Ver opciones", footer: str = "") -> bool:
        """Send a list message via the bridge."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.post(
                    f"{BRIDGE_URL}/send-list",
                    json={
                        "to": chat_id,
                        "text": text,
                        "buttonText": button_text,
                        "sections": sections,
                        "footer": footer,
                    },
                )
                return r.status_code == 200
        except Exception as e:
            log.error(f"[bot_mode] send_list error: {e}")
            return False

    async def send_main_menu(self, chat_id: str, business_name: str = ""):
        """Send the main interactive menu."""
        text = f"Como te puedo ayudar?"
        if business_name:
            text = f"Hola! Soy la asistente de {business_name}. Como te puedo ayudar?"

        buttons = [
            {"id": "btn_prices", "text": "Ver precios"},
            {"id": "btn_schedule", "text": "Agendar cita"},
            {"id": "btn_human", "text": "Hablar con alguien"},
        ]
        await self.send_buttons(chat_id, text, buttons, footer="Powered by Kimika AI")

    async def send_services_list(self, chat_id: str, services: List[Dict]):
        """Send services as an interactive list."""
        rows = [
            {"title": s.get("name", ""), "id": f"svc_{i}", "description": s.get("price", "")}
            for i, s in enumerate(services)
        ]
        sections = [{"title": "Servicios disponibles", "rows": rows[:10]}]
        await self.send_list(
            chat_id,
            "Estos son nuestros servicios. Toca uno para mas info:",
            sections,
            button_text="Ver servicios",
        )

    async def send_confirmation(self, chat_id: str, question: str):
        """Send a yes/no confirmation."""
        buttons = [
            {"id": "btn_yes", "text": "Si, confirmar"},
            {"id": "btn_no", "text": "No, cancelar"},
        ]
        await self.send_buttons(chat_id, question, buttons)

    def handle_button_response(self, button_id: str, chat_id: str) -> Optional[str]:
        """Process a button click and return the action to take."""
        actions = {
            "btn_prices": "show_prices",
            "btn_schedule": "start_scheduling",
            "btn_human": "transfer_to_human",
            "btn_yes": "confirm",
            "btn_no": "cancel",
        }
        return actions.get(button_id)


# Singleton
bot_mode = BotMode()
