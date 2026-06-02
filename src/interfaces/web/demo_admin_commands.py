from __future__ import annotations
import logging
import re
import json
from typing import Any, Dict, List, Optional

log = logging.getLogger("conny.demo_admin")

_COLOMBIAN_PHONE = re.compile(r"(?:\+?57)?3\d{9}(?!\d)")
_ANY_PHONE = re.compile(r"(?:\+?\d{1,3})?\d{7,15}(?!\d)")
_CONTACT_TRIGGERS = re.compile(
    r"(?:contact|comunic|escrib[eí]|env[ií]|mand[aá]|habla|presenta|saluda|dile|diga|di\b)",
    re.IGNORECASE,
)


def _strip_jid(raw: str) -> str:
    return raw.split("@")[0].strip() if raw else ""


def is_admin_chat(chat_id: str, clinic: Dict, db) -> bool:
    from src.conny.utils.helpers import _parse_admin_ids
    raw = _strip_jid(chat_id)
    normalized_admin_ids = {_strip_jid(aid) for aid in _parse_admin_ids(clinic.get("admin_chat_ids", []))}
    if raw in normalized_admin_ids:
        return True
    try:
        if db.get_admin(chat_id) or db.get_admin(raw):
            return True
    except Exception:
        pass
    return False


def looks_like_contact_command(text: str) -> bool:
    if not text or len(text) < 10:
        return False
    stripped = re.sub(r"\s+", "", text)
    return bool(_ANY_PHONE.search(stripped)) and bool(_CONTACT_TRIGGERS.search(text))


def extract_phone_number(text: str) -> Optional[str]:
    stripped = re.sub(r"\s+", "", text)
    m = _COLOMBIAN_PHONE.search(stripped)
    if m:
        num = m.group(0).lstrip("+")
        return num if num.startswith("57") else "57" + num
    m = _ANY_PHONE.search(stripped)
    if m:
        return m.group(0).lstrip("+")
    return None


async def parse_name(text: str, llm_engine) -> str:
    if not llm_engine:
        return ""
    try:
        r, _ = await llm_engine.complete(
            [{"role": "system", "content": "Extrae el nombre de la persona a contactar del mensaje. Si no hay nombre, responde ''"},
             {"role": "user", "content": text}],
            model_tier="fast", temperature=0.1, max_tokens=100,
        )
        name = r.strip().strip('"').strip("'") if r else ""
        return name if name and len(name) < 50 else ""
    except Exception:
        return ""


async def handle_admin_contact_command(
    self, chat_id: str, text: str, clinic: Dict, db, llm_engine,
    admin_name: str = "", demo_llm=None,
) -> List[str]:
    phone = extract_phone_number(text)
    if not phone:
        if demo_llm:
            try:
                r = await demo_llm(
                    "Eres Conny. Te pidieron contactar a alguien pero no diste el número.",
                    "Respondé corto, pedí el número.",
                    temp=0.8, max_t=200,
                )
                if r:
                    return [r]
            except Exception:
                pass
        return []

    target_name = await parse_name(text, llm_engine)
    jid = f"{phone}@s.whatsapp.net"

    intro = ""
    if demo_llm:
        try:
            r = await demo_llm(
                "Acabas de recibir el primer mensaje de alguien nuevo.",
                "Preséntate breve, como en WhatsApp. corto, natural. Máximo 2 líneas.",
                temp=0.85, max_t=400,
            )
            if r:
                intro = r
        except Exception:
            pass

    if not intro:
        try:
            r, _ = await llm_engine.complete(
                [{"role": "system", "content": "Eres Conny. Preséntate breve y natural, como en WhatsApp. Máximo 2 líneas."},
                 {"role": "user", "content": "Hola"}],
                model_tier="fast", temperature=0.85, max_tokens=400,
            )
            if r:
                intro = r.strip()
        except Exception:
            pass

    if not intro:
        return []

    import os, httpx
    bridge_url = os.environ.get("WHATSAPP_BRIDGE_URL", "http://127.0.0.1:8002")

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(f"{bridge_url}/send", json={"to": jid, "message": intro})
        if r.status_code >= 400:
            log.error(f"[demo_admin] send error: {r.status_code}")
            return []
    except Exception as e:
        log.error(f"[demo_admin] send error: {e}")
        return []

    admin_ref = f" {admin_name}" if admin_name else ""
    name_ref = f" a {target_name}" if target_name else ""
    if demo_llm:
        try:
            r = await demo_llm(
                "Eres Conny. Acabas de hacer lo que el admin te pidió. Respondé en 2 burbujas separadas por |||. Primera: confirmá. Segunda: preguntá si necesita algo más.",
                f"Confirmale al admin{admin_ref} que ya enviaste el mensaje{name_ref}.",
                temp=0.82, max_t=400,
            )
            if r:
                parts = [p.strip() for p in r.split("|||") if p.strip()]
                if len(parts) >= 2:
                    return parts[:2]
        except Exception:
            pass

    try:
        gen_eng = llm_engine
        if hasattr(self, "generator") and self.generator:
            gen_eng = getattr(self.generator, "llm", None) or llm_engine
        if gen_eng:
            r, _ = await gen_eng.complete(
                [{"role": "system", "content": "Eres Conny. Respondé en 2 mensajes separados por |||. Primero confirmá, segundo preguntá si necesita algo más."},
                 {"role": "user", "content": f"Confirmale al admin{admin_ref} que ya enviaste el mensaje{name_ref}."}],
                model_tier="fast", temperature=0.82, max_tokens=400,
            )
            if r:
                parts = [p.strip() for p in r.split("|||") if p.strip()]
                if parts:
                    return parts[:2]
    except Exception:
        pass

    return []
