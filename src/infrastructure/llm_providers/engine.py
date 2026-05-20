import json
import time
import httpx
import hashlib
import re
import logging
from typing import List, Dict, Tuple, Any
from conny_config import Config

log = logging.getLogger("conny.llm")

try:
    from conny import model_manager
except ImportError:
    model_manager = None


class LLMProvider:
    """Interfaz base para proveedores LLM."""
    name: str = "base"

    async def complete(self, messages: List[Dict], model: str,
                       temperature: float = 0.7, max_tokens: int = 1000,
                       **kwargs) -> Tuple[str, Dict]:
        raise NotImplementedError

    async def embed(self, text: str) -> List[float]:
        raise NotImplementedError


def _parse_http_json_response(response: httpx.Response, provider_name: str) -> Dict[str, Any]:
    body = response.text or ""
    stripped = body.strip()
    content_type = (response.headers.get("content-type") or "").strip() or "unknown"
    if not stripped:
        raise ValueError(f"{provider_name} devolvió body vacío [{content_type}]")
    try:
        parsed = response.json()
    except Exception as exc:
        snippet = re.sub(r"\s+", " ", stripped)[:220]
        raise ValueError(
            f"{provider_name} devolvió body no-JSON [{content_type}]: {snippet}"
        ) from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{provider_name} devolvió JSON no-objeto [{content_type}]")
    return parsed


class GroqProvider(LLMProvider):
    """Groq — el mas rapido (~500ms). Llama-3.3-70b."""
    name = "groq"
    BASE  = "https://api.groq.com/openai/v1"
    MDLS  = {"reasoning": "llama-3.3-70b-versatile",
              "fast":      "llama-3.3-70b-versatile",
              "lite":      "llama-3.1-8b-instant"}

    def __init__(self, key: str): self.key = key

    async def complete(self, messages, model="fast", temperature=0.7, max_tokens=1000, **kw):
        start = time.time()
        if isinstance(model, str) and model in self.MDLS:
            m = self.MDLS[model]
        elif isinstance(model, str) and model.startswith("groq/"):
            m = model.split("/", 1)[1]
        elif isinstance(model, str) and model not in ("fast", "reasoning", "lite"):
            m = model
        else:
            m = self.MDLS["fast"]
        async with httpx.AsyncClient(timeout=15.0) as c:
            r = await c.post(f"{self.BASE}/chat/completions",
                headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
                json={"model": m, "messages": messages, "temperature": temperature, "max_tokens": max_tokens})
            r.raise_for_status()
        payload = _parse_http_json_response(r, self.name)
        text = payload["choices"][0]["message"]["content"].strip()
        return text, {"model": m, "latency_ms": int((time.time()-start)*1000), "provider": "groq"}

    async def embed(self, text):
        raise NotImplementedError


class GeminiProvider(LLMProvider):
    """Google Gemini directo. Soporta rotacion de claves."""
    name = "gemini"
    BASE  = "https://generativelanguage.googleapis.com/v1beta"
    MDLS  = {"reasoning": "gemini-2.5-pro",        # Pro para razonamiento complejo
              "fast":      "gemini-2.5-flash",      # Flash para velocidad
              "lite":      "gemini-2.5-flash-lite"}

    def __init__(self, key: str, label: str = "gemini"):
        self.key   = key
        self.name  = label

    async def complete(self, messages, model="fast", temperature=0.7, max_tokens=1000, **kw):
        start = time.time()
        if isinstance(model, str) and model in self.MDLS:
            gm = self.MDLS[model]
        elif isinstance(model, str) and model.startswith("google/"):
            gm = model.split("/", 1)[1]
        elif isinstance(model, str) and model.startswith("gemini-"):
            gm = model
        else:
            gm = self.MDLS["fast"]
        system_parts, contents = [], []
        for m in messages:
            if m["role"] == "system":
                system_parts.append({"text": m["content"]})
            elif m["role"] == "user":
                contents.append({"role": "user",  "parts": [{"text": m["content"]}]})
            elif m["role"] == "assistant":
                contents.append({"role": "model", "parts": [{"text": m["content"]}]})
        payload = {"contents": contents,
                   "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens}}
        if system_parts:
            payload["systemInstruction"] = {"parts": system_parts}
        url = f"{self.BASE}/models/{gm}:generateContent?key={self.key}"
        async with httpx.AsyncClient(timeout=20.0) as c:
            r = await c.post(url, json=payload)
            r.raise_for_status()
        payload = _parse_http_json_response(r, self.name)
        text = payload["candidates"][0]["content"]["parts"][0]["text"].strip()
        return text, {"model": gm, "latency_ms": int((time.time()-start)*1000), "provider": self.name}

    async def embed(self, text):
        url = f"{self.BASE}/models/text-embedding-004:embedContent?key={self.key}"
        async with httpx.AsyncClient(timeout=30.0) as c:
            r = await c.post(url, json={"content": {"parts": [{"text": text}]}})
            r.raise_for_status()
        return r.json()["embedding"]["values"]


class OpenRouterProvider(LLMProvider):
    """OpenRouter — acceso a todos los modelos."""
    name = "openrouter"
    BASE  = "https://openrouter.ai/api/v1"
    MDLS  = {"reasoning": "anthropic/claude-sonnet-4",
              "fast":      "google/gemini-2.5-flash",
              "lite":      "google/gemini-2.5-flash-lite"}

    def __init__(self, key: str): self.key = key

    async def complete(self, messages, model="fast", temperature=0.7, max_tokens=1000, **kw):
        start = time.time()
        m = self.MDLS.get(model, model if isinstance(model, str) else self.MDLS["fast"])
        async with httpx.AsyncClient(timeout=25.0) as c:
            r = await c.post(f"{self.BASE}/chat/completions",
                headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json",
                         "HTTP-Referer": "https://conny.ai", "X-Title": "Conny Ultra"},
                json={"model": m, "messages": messages, "temperature": temperature, "max_tokens": max_tokens})
            r.raise_for_status()
        payload = _parse_http_json_response(r, self.name)
        text = payload["choices"][0]["message"]["content"].strip()
        return text, {"model": m, "latency_ms": int((time.time()-start)*1000), "provider": "openrouter"}

    async def embed(self, text):
        async with httpx.AsyncClient(timeout=30.0) as c:
            r = await c.post(f"{self.BASE}/embeddings",
                headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
                json={"model": "openai/text-embedding-3-small", "input": text})
            r.raise_for_status()
        return r.json()["data"][0]["embedding"]


class OpenAIProvider(LLMProvider):
    """OpenAI — ultimo recurso."""
    name = "openai"
    BASE  = "https://api.openai.com/v1"
    MDLS  = {"reasoning": "gpt-4o", "fast": "gpt-4o-mini", "lite": "gpt-4o-mini"}

    def __init__(self, key: str): self.key = key

    async def complete(self, messages, model="fast", temperature=0.7, max_tokens=1000, **kw):
        start = time.time()
        if isinstance(model, str) and model in self.MDLS:
            m = self.MDLS[model]
        elif isinstance(model, str) and model.startswith("openai/"):
            m = model.split("/", 1)[1]
        elif isinstance(model, str) and model.startswith("gpt-"):
            m = model
        else:
            m = self.MDLS["fast"]
        async with httpx.AsyncClient(timeout=25.0) as c:
            r = await c.post(f"{self.BASE}/chat/completions",
                headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
                json={"model": m, "messages": messages, "temperature": temperature, "max_tokens": max_tokens})
            r.raise_for_status()
        payload = _parse_http_json_response(r, self.name)
        text = payload["choices"][0]["message"]["content"].strip()
        return text, {"model": m, "latency_ms": int((time.time()-start)*1000), "provider": "openai"}

    async def embed(self, text):
        async with httpx.AsyncClient(timeout=30.0) as c:
            r = await c.post(f"{self.BASE}/embeddings",
                headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
                json={"model": "text-embedding-3-small", "input": text})
            r.raise_for_status()
        return r.json()["data"][0]["embedding"]


class LLMEngine:
    """
    Motor LLM con cascada de 6 proveedores.
    Groq -> Gemini(key1) -> Gemini(key2) -> Gemini(key3) -> OpenRouter -> OpenAI

    V8.1 — Fixes de fallos silenciosos:
    - Blacklist temporal (60s) en vez de permanente
    - Detección de respuesta vacía o inválida
    - Timeout de provider < timeout de caller (nunca zombie)
    - _push_to_engine solo en OpenRouter (único multi-modelo real)
    - Métricas de fallo por provider en DB para diagnóstico
    """

    # Providers que soportan modelos externos (OpenRouter puede usar cualquier modelo)
    _MULTI_MODEL_PROVIDERS = {"openrouter"}

    def __init__(self):
        self.providers: List[LLMProvider] = []
        self._failures:     Dict[str, int]   = {}   # conteo de fallos
        self._blocked_until: Dict[str, float] = {}  # timestamp hasta cuando está bloqueado
        self._last_success: Dict[str, float] = {}
        self._blacklist_ttl  = 60.0   # segundos de bloqueo tras 3 fallos consecutivos
        self._cache: Dict[str, Tuple[str, float]] = {}
        self._cache_ttl = 300

        if Config.GROQ_API_KEY:
            self.providers.append(GroqProvider(Config.GROQ_API_KEY))
            log.info("[llm] Groq OK")
        _all_gemini_keys = Config.GEMINI_API_KEYS or [
            Config.GEMINI_API_KEY,   Config.GEMINI_API_KEY_2,
            Config.GEMINI_API_KEY_3, Config.GEMINI_API_KEY_4,
            Config.GEMINI_API_KEY_5, Config.GEMINI_API_KEY_6,
        ]
        for i, key in enumerate(_all_gemini_keys):
            if key:
                self.providers.append(GeminiProvider(key, f"gemini_k{i+1}"))
                log.info(f"[llm] Gemini key{i+1} OK")
        if Config.OPENROUTER_API_KEY:
            self.providers.append(OpenRouterProvider(Config.OPENROUTER_API_KEY))
            log.info("[llm] OpenRouter OK")
        if Config.OPENAI_API_KEY:
            self.providers.append(OpenAIProvider(Config.OPENAI_API_KEY))
            log.info("[llm] OpenAI OK")

        n = len(self.providers)
        if n == 0:
            log.critical("[llm] SIN PROVEEDORES — el bot no podra generar respuestas inteligentes")
        else:
            log.info(f"[llm] cascada lista: {n} proveedores")

    def _hash(self, messages, **kw):
        return hashlib.md5((json.dumps(messages, sort_keys=True) + json.dumps(kw, sort_keys=True)).encode()).hexdigest()

    def _get_requested_model(self, model_tier: str) -> str:
        try:
            if model_manager:
                effective = model_manager.get_effective_models()
                chosen = effective.get(model_tier)
                if chosen:
                    return chosen
        except Exception:
            pass
        return Config.LLM_MODELS.get(model_tier, model_tier)

    def _ordered_providers(self, requested_model: str) -> List[LLMProvider]:
        providers = list(self.providers)

        def _priority(provider: LLMProvider) -> int:
            name = provider.name
            if requested_model.startswith("google/") or requested_model.startswith("gemini-"):
                if name.startswith("gemini"):
                    return 0
                if name == "openrouter":
                    return 1
                return 2
            if requested_model.startswith("anthropic/") or requested_model.startswith("meta-llama/") or requested_model.startswith("mistralai/"):
                if name == "openrouter":
                    return 0
                return 2
            if requested_model.startswith("openai/") or requested_model.startswith("gpt-"):
                if name == "openai":
                    return 0
                if name == "openrouter":
                    return 1
                return 2
            if requested_model.startswith("groq/") or requested_model.startswith("llama-"):
                if name == "groq":
                    return 0
                if name == "openrouter":
                    return 1
                return 2
            return 0

        return sorted(
            providers,
            key=lambda provider: (
                _priority(provider),
                self._failures.get(provider.name, 0),
                -self._last_success.get(provider.name, 0.0),
                provider.name,
            ),
        )

    def _resolve_provider_model(self, provider: LLMProvider,
                                requested_model: str,
                                model_tier: str) -> str:
        name = provider.name
        if name.startswith("gemini") and (
            requested_model.startswith("google/") or requested_model.startswith("gemini-")
        ):
            return requested_model
        if name == "openai" and (
            requested_model.startswith("openai/") or requested_model.startswith("gpt-")
        ):
            return requested_model
        if name == "groq" and (
            requested_model.startswith("groq/") or requested_model.startswith("llama-")
        ):
            return requested_model
        if name == "openrouter":
            return requested_model
        return model_tier

    def _is_blocked(self, provider_name: str) -> bool:
        """Blacklist temporal: bloqueado solo por _blacklist_ttl segundos."""
        until = self._blocked_until.get(provider_name, 0)
        if until and time.time() < until:
            return True
        # Tiempo expirado — resetear fallos para darle otra oportunidad
        if until and time.time() >= until:
            self._failures[provider_name] = 0
            self._blocked_until[provider_name] = 0
            log.info(f"[llm] {provider_name} desbloqueado (blacklist expirado)")
        return False

    def _register_failure(self, provider_name: str, error: Exception):
        """Registra un fallo y bloquea si acumula 3 consecutivos."""
        self._failures[provider_name] = self._failures.get(provider_name, 0) + 1
        count = self._failures[provider_name]
        log.warning(f"[llm] {provider_name} fallo #{count}: {str(error)[:100]}")
        status_code = getattr(getattr(error, "response", None), "status_code", None)
        block_after = 3
        block_ttl = self._blacklist_ttl
        if status_code in (401, 402, 403):
            block_after = 1
            block_ttl = max(block_ttl, 1800.0)
        elif status_code in (429, 500, 502, 503, 504):
            block_after = 2
            block_ttl = max(block_ttl, 180.0)
        if count >= block_after:
            self._blocked_until[provider_name] = time.time() + block_ttl
            log.error(f"[llm] {provider_name} BLOQUEADO por {block_ttl}s tras {count} fallos")
        # Guardar métrica en DB para que el admin pueda ver con /v8
        try:
            if db:
                db.record_metric("llm_failure", provider_name, count,
                                 {"error": str(error)[:80], "blocked": count >= block_after, "status_code": status_code})
        except Exception:
            pass

    def _is_valid_response(self, text: str) -> bool:
        """Detecta respuestas vacías o inválidas que no deben llegar al usuario."""
        if not text or not text.strip():
            return False
        stripped = text.strip()
        # Respuesta puramente de error del API
        if stripped.startswith("Error") and len(stripped) < 30:
            return False
        # JSON de error de OpenRouter / Gemini que se filtró
        if stripped.startswith('{"error"') or stripped.startswith('{"status"'):
            return False
        return True

    async def complete(self, messages: List[Dict],
                       model_tier: str = "fast",
                       temperature: float = 0.7,
                       max_tokens: int = 1000,
                       use_cache: bool = True,
                       **kwargs) -> Tuple[str, Dict]:
        requested_model = self._get_requested_model(model_tier)
        if use_cache and db:
            ck = self._hash(messages, t=temperature, m=max_tokens,
                            tier=model_tier, requested_model=requested_model)
            cached = db.get_cached_response(ck)
            if cached and self._is_valid_response(cached):
                return cached, {"cached": True}

        last_error = None
        attempted  = []
        for provider in self._ordered_providers(requested_model):
            if self._is_blocked(provider.name):
                log.debug(f"[llm] {provider.name} saltado (blacklist activo)")
                continue
            attempted.append(provider.name)
            try:
                provider_model = self._resolve_provider_model(provider, requested_model, model_tier)
                # Timeout del provider siempre menor que el del caller
                # para evitar zombies. El caller (admin_brain) usa 12s,
                # los providers internos usan hasta 25s — reducimos aquí.
                response, metadata = await asyncio.wait_for(
                    provider.complete(
                        messages, model=provider_model,
                        temperature=temperature, max_tokens=max_tokens, **kwargs),
                    timeout=10.0   # siempre < 12s del caller
                )

                # Verificar que la respuesta sea válida — no vacía ni error
                if not self._is_valid_response(response):
                    err = ValueError(f"respuesta inválida/vacía: '{response[:40]}'")
                    self._register_failure(provider.name, err)
                    last_error = err
                    log.warning(f"[llm] {provider.name} devolvió respuesta inválida — siguiente")
                    continue

                # Éxito — resetear fallos
                self._failures[provider.name] = 0
                self._last_success[provider.name] = time.time()
                if use_cache and db:
                    db.cache_response(ck, response)
                if db:
                    db.record_metric("llm", "completion",
                                     metadata.get("latency_ms", 0),
                                     {"provider": metadata.get("provider"), "tier": model_tier,
                                      "requested_model": requested_model})
                log.info(
                    f"[llm] {provider.name} OK ({metadata.get('latency_ms',0)}ms) | "
                    f"tier={model_tier} requested={requested_model}"
                )
                return response, metadata

            except asyncio.TimeoutError as e:
                te = TimeoutError(f"timeout 10s")
                self._register_failure(provider.name, te)
                last_error = te
            except Exception as e:
                self._register_failure(provider.name, e)
                last_error = e

        providers_tried = ", ".join(attempted) if attempted else "ninguno"
        raise RuntimeError(f"Todos los LLM fallaron [{providers_tried}]: {last_error}")

    def get_health(self) -> Dict:
        """Estado de salud de cada provider. Usado por /v8 y diagnóstico."""
        now = time.time()
        result = {}
        for p in self.providers:
            blocked_until = self._blocked_until.get(p.name, 0)
            result[p.name] = {
                "failures": self._failures.get(p.name, 0),
                "blocked":  now < blocked_until,
                "unblocks_in": max(0, int(blocked_until - now)) if now < blocked_until else 0,
            }
        return result

    async def embed(self, text: str) -> List[float]:
        for p in self.providers:
            try:
                return await p.embed(text)
            except Exception:
                continue
        return self._simple_embedding(text)

    def _simple_embedding(self, text: str, dim: int = 384) -> List[float]:
        words = text.lower().split()
        vec = [0.0] * dim
        for i, w in enumerate(words[:dim]):
            vec[i % dim] += hash(w) % 100 / 100.0
        norm = math.sqrt(sum(x*x for x in vec))
        return [x/norm for x in vec] if norm > 0 else vec


# Instancia global
llm_engine: LLMEngine = None

def init_llm():
    global llm_engine
    llm_engine = LLMEngine()

# ═══════════════════════════════════════════════════════════════════════════════
# ANALIZADOR DE MENSAJES AVANZADO
# ═══════════════════════════════════════════════════════════════════════════════

