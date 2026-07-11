"""
Bublee Search — Web search using Gemini's google_search_retrieval grounding.
Free, no API key needed beyond Gemini key (which we already have).
"""
from __future__ import annotations
import os
import json
import logging
import httpx
from typing import Optional

log = logging.getLogger("bublee.search")


async def search_business(query: str, city: str = "") -> str:
    """
    Search for a business using Gemini with grounding (Google Search built-in).
    Returns structured info about the business.
    """
    keys = [k for k in [
        os.getenv("GEMINI_API_KEY", ""),
        os.getenv("GEMINI_API_KEY_2", ""),
        os.getenv("GEMINI_API_KEY_3", ""),
    ] if k]

    if not keys:
        return ""

    search_query = f"{query} {city}".strip() if city else query
    prompt = f"""Busca información real sobre este negocio: "{search_query}"

Necesito:
- Nombre completo del negocio
- Dirección (si la encuentras)
- Horarios de atención
- Servicios que ofrecen
- Precios (si están disponibles públicamente)
- Teléfono o contacto
- Cualquier info relevante de su web o Google Maps

Si no encuentras el negocio exacto, di "No encontré información específica" y sugiere preguntar más detalles.
Responde en formato conciso, sin markdown."""

    for key in keys:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/"
                    f"gemini-2.5-flash:generateContent?key={key}",
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "tools": [{"google_search_retrieval": {}}],
                    },
                )
                if r.status_code == 429:
                    continue
                r.raise_for_status()
                data = r.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    text_parts = [p.get("text", "") for p in parts if "text" in p]
                    result = "\n".join(text_parts).strip()
                    if result:
                        log.info(f"[search] found info for '{search_query}' ({len(result)} chars)")
                        return result[:2000]
        except Exception as e:
            log.warning(f"[search] error with key: {e}")
            continue

    return ""


async def search_general(query: str) -> str:
    """General web search for any topic."""
    keys = [k for k in [
        os.getenv("GEMINI_API_KEY", ""),
        os.getenv("GEMINI_API_KEY_2", ""),
    ] if k]

    if not keys:
        return ""

    for key in keys:
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                r = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/"
                    f"gemini-2.5-flash:generateContent?key={key}",
                    json={
                        "contents": [{"parts": [{"text": query}]}],
                        "tools": [{"google_search_retrieval": {}}],
                    },
                )
                if r.status_code == 429:
                    continue
                r.raise_for_status()
                data = r.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    return "\n".join(p.get("text", "") for p in parts if "text" in p).strip()[:1500]
        except Exception:
            continue
    return ""
