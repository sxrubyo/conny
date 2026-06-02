from __future__ import annotations
import os
import re
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

log = logging.getLogger("conny.evolution")

class EvolutionManager:
    """
    Maneja la auto-evolución de Conny.
    Escribe en SOUL.md e IDENTITY.md y persiste cambios en DB.
    """

    def __init__(self, instance_id: str, db, instance_path: Optional[Union[str, Path]] = None):
        self.instance_id = instance_id
        self.db = db
        # Intentar determinar la ruta de la instancia
        if instance_path:
            self.base_path = Path(instance_path)
        else:
            self.base_path = Path(f"/home/ubuntu/conny-instances/{instance_id}")
            if not self.base_path.exists():
                self.base_path = Path(".") # Fallback

        self.soul_path = self.base_path / "soul" / "SOUL.md"
        self.identity_path = self.base_path / "identity" / "IDENTITY.md"
        
        # Asegurar que los directorios existen
        self.soul_path.parent.mkdir(parents=True, exist_ok=True)
        self.identity_path.parent.mkdir(parents=True, exist_ok=True)

    async def apply_instruction(self, text: str) -> str:
        """
        Analiza un mensaje del admin y aplica cambios si detecta instrucciones de evolución.
        """
        text_low = text.lower().strip()
        
        # 1. Cambio de Saludo
        saludo_match = re.search(r"(?:cambia|pon|usa|setea)\s+(?:tu|el)\s+saludo\s+(?:a|por|como)\s+[\"']?(.+?)[\"']?$", text, re.IGNORECASE)
        if saludo_match:
            new_greeting = saludo_match.group(1).strip()
            # Si el saludo tiene |||, lo dividimos en dos burbujas
            if "|||" in new_greeting:
                g1, g2 = [p.strip() for p in new_greeting.split("|||", 1)]
                self.db.update_clinic(custom_greeting_1=g1, custom_greeting_2=g2)
            else:
                self.db.update_clinic(custom_greeting_1=new_greeting)
            
            await self._update_soul(f"El admin pidió cambiar el saludo a: {new_greeting}")
            return f"entendido, ya actualicé mi saludo a: {new_greeting}"

        # 2. Frases prohibidas
        forbidden_match = re.search(r"(?:no\s+uses|no\s+digas|deja\s+de\s+usar|prohibido\s+decir)\s+(?:la\s+frase|la\s+palabra|el\s+termino)?\s*[\"']?(.+?)[\"']?$", text, re.IGNORECASE)
        if forbidden_match:
            phrase = forbidden_match.group(1).strip()
            # Guardar en business_rules
            clinic = self.db.get_clinic()
            rules = clinic.get("business_rules", {})
            if isinstance(rules, str): rules = json.loads(rules)
            
            forbidden = rules.get("forbidden_phrases", [])
            if phrase not in forbidden:
                forbidden.append(phrase)
            rules["forbidden_phrases"] = forbidden
            
            self.db.update_clinic(business_rules=json.dumps(rules, ensure_ascii=False))
            await self._update_soul(f"REGLA CRÍTICA: No usar jamás la frase o palabra: '{phrase}'")
            return f"anotado. no volveré a decir '{phrase}' nunca más"

        # 3. Datos del Admin
        if "me llamo" in text_low or "mi nombre es" in text_low:
            name_match = re.search(r"(?:me llamo|soy|mi nombre es)\s+([A-ZÁÉÍÓÚ][a-záéíóú]+(?:\s+[A-ZÁÉÍÓÚ][a-záéíóú]+)?)", text)
            if name_match:
                admin_name = name_match.group(1)
                await self._update_identity(f"Nombre del Administrador: {admin_name}")
                # El profile ya se actualiza en runtime.py, pero esto refuerza los archivos .md
                return f"mucho gusto {admin_name}, ya guardé tu nombre en mi identidad operativa"

        return ""

    async def _update_soul(self, observation: str):
        """Añade una observación al archivo SOUL.md."""
        try:
            content = ""
            if self.soul_path.exists():
                content = self.soul_path.read_text(encoding="utf-8")
            
            new_entry = f"\n- [{datetime.now().strftime('%Y-%m-%d %H:%M')}] {observation}"
            if "# EVOLUCIÓN" not in content:
                content += "\n\n# EVOLUCIÓN\n"
            
            content += new_entry
            self.soul_path.write_text(content, encoding="utf-8")
        except Exception as e:
            log.error(f"Error updating SOUL.md: {e}")

    async def _update_identity(self, line: str):
        """Actualiza o añade una línea al archivo IDENTITY.md."""
        try:
            content = ""
            if self.identity_path.exists():
                content = self.identity_path.read_text(encoding="utf-8")
            
            if line not in content:
                content += f"\n- {line}"
                self.identity_path.write_text(content, encoding="utf-8")
        except Exception as e:
            log.error(f"Error updating IDENTITY.md: {e}")
