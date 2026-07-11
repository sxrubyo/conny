"""bublee_web_search.py — Web search via Brave → Apify cascade."""
from __future__ import annotations

import logging
import os
from typing import List, Dict, Optional

import httpx

log = logging.getLogger("bublee.web_search")

BRAVE_API_KEY = os.getenv("BRAVE_API_KEY", "")
BRAVE_URL = "https://api.search.brave.com/res/v1/web/search"


async def search_web(query: str, num_results: int = 5) -> List[Dict[str, str]]:
    """Busca en internet: Brave (primario) → Apify (fallback con 20 keys)."""
    # 1. Brave Search
    if BRAVE_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(
                    BRAVE_URL,
                    params={"q": query, "count": num_results},
                    headers={"X-Subscription-Token": BRAVE_API_KEY, "Accept": "application/json"},
                )
                if r.status_code == 200:
                    data = r.json()
                    results = []
                    for item in data.get("web", {}).get("results", [])[:num_results]:
                        results.append({
                            "title": item.get("title", ""),
                            "snippet": item.get("description", ""),
                            "url": item.get("url", ""),
                        })
                    if results:
                        log.debug(f"[web_search] Brave: {len(results)} resultados")
                        return results
        except Exception as _be:
            log.debug(f"[web_search] Brave falló: {_be}")

    # 2. Apify cascade (20 keys disponibles en .env)
    try:
        from search import apify_search as _apify_search
        apify_results = await _apify_search(query, count=num_results)
        if apify_results:
            normalized = []
            for r in apify_results:
                normalized.append({
                    "title": r.get("title", ""),
                    "snippet": r.get("description") or r.get("snippet", ""),
                    "url": r.get("url", ""),
                })
            log.info(f"[web_search] Apify: {len(normalized)} resultados para '{query[:50]}'")
            return normalized
    except Exception as _ae:
        log.debug(f"[web_search] Apify falló: {_ae}")

    log.warning(f"[web_search] sin resultados para: {query[:60]}")
    return []


async def search_business(business_name: str, city: str = "Medellín") -> str:
    """Busca info de un negocio y retorna string para el LLM.
    Si no encuentra nada, retorna string vacío (NO inventa)."""
    query = f"{business_name} {city} servicios precios horario"
    results = await search_web(query, num_results=5)
    if not results:
        return ""
    lines = []
    for r in results:
        title = r.get("title", "")
        snippet = r.get("snippet", "")[:200]
        url = r.get("url", "")
        if snippet:
            lines.append(f"- {title}: {snippet} ({url})")
        elif title:
            lines.append(f"- {title} ({url})")
    return "\n".join(lines)


async def search_topic(topic: str) -> str:
    """Búsqueda general, retorna resultados formateados."""
    results = await search_web(topic, num_results=3)
    if not results:
        return ""
    lines = []
    for r in results:
        snippet = r.get("snippet", "")[:200]
        lines.append(f"- {r.get('title','')}: {snippet}")
    return "\n".join(lines)
