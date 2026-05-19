from __future__ import annotations
import logging
import asyncio
import re
import json
import time
import random
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

log = logging.getLogger("conny.demo")

class ConnyDemo:
    """
    Componente especializado para el Modo Demo.
    Maneja la experiencia de intriga progresiva y trucos de venta.
    """
    
    def __init__(self, conny):
        self.conny = conny

    async def handle(self, chat_id: str, text: str, clinic: Dict, 
                    attachments: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """MODO DEMO — Delegamos a la lógica original por ahora."""
        # Para máxima estabilidad, llamamos al método en conny.py que ya conocemos.
        return await self.conny._handle_demo_message(chat_id, text, clinic, attachments)
