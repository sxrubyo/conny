# Conny v9.0 — System Instructions

## Architecture (current)

```
Port Map:
  8001 → conny (demo mode, shared telegram router)
  8003 → conny-clinica-de-las-americas (production)
  8002 → whatsapp-bridge (Baileys)
  9001 → nova-core (governance, optional)

PM2 processes:
  conny                         → /home/ubuntu/conny/run.sh
  conny-clinica-de-las-americas → /home/ubuntu/conny-instances/clinica-de-las-americas/run.sh
  whatsapp-bridge                 → Baileys bridge
  nova-core                       → Nova governance server

Key modules:
  conny.py              → monolith engine (1.3MB, all core logic)
  conny_admin_api.py    → FastAPI /admin endpoints (persona, model, teach, gaps)
  conny_memory_engine.py→ episodic + semantic + procedural memory with TF-IDF recall
  conny_voice.py        → humanization post-processor (robot pattern removal)
  conny_uncertainty.py  → confidence scoring + admin alerts
  conny_nova_proxy.py   → transparent LLM proxy (memory + governance + voice)
  conny_brain_v10.py    → conversation intelligence (LLM-first, anti-loop)
  conny_domino.py       → response quality control
  nova_bridge.py          → Nova governance client (validate before send)
  conny_cron.py         → APScheduler (weekly memory consolidation, Sun 3am)
```

## Core Principles

1. **Never break production.** Both PM2 instances must stay online. Branch before refactoring.
2. **Plan before acting.** Research → Strategy → Execution. Use subagents to investigate.
3. **Validate exhaustively.** Run `pytest tests/` + `pm2 logs conny --lines 20` after changes.
4. **No secrets in git.** Protect `.env`, `auth_info_*`, `*.db` files.

## Instance Isolation

- Each client: isolated directory, own `.env`, own SQLite DB, own Brand Vault
- Port assignment: unique per instance, set in `.env` as `PORT=`
- Telegram: shared router on main instance, routing by `chat_id` via `conny pair`
- WhatsApp: one bridge session per instance, never share `auth_info_*` folder
- Core code sync: `conny_core/`, `conny_agents/`, brain, domino — shared across instances
- Client data: NEVER sync databases, conversations, or credentials

## Response Rules (enforced by conny_voice.py)

### Never say:
- "como IA" / "como asistente virtual" / "como inteligencia artificial"
- "no tengo la capacidad" / "está fuera de mi alcance"
- "no puedo procesar" / "no puedo entender"
- "Hola! Soy Conny, tu asistente virtual"
- "Por supuesto!" / "Claro que sí!" / "Con gusto!"

### Always:
- Sound like a real Colombian receptionist (warm, concise, direct)
- One question per turn, focused on advancing the conversation
- Max 1 exclamation mark per response
- Never start a response with the bot's name
- If uncertain: deflect naturally, alert admin, log gap

## Admin API (new in v9.0)

```bash
# Change personality at runtime
curl -X POST localhost:8001/admin/{instance}/persona \
  -H "X-Admin-Key: $KEY" \
  -d '{"tone": "colombian_warm", "verbosity": "concise"}'

# Change LLM model
curl -X POST localhost:8001/admin/{instance}/model \
  -H "X-Admin-Key: $KEY" \
  -d '{"provider": "gemini", "model_id": "gemini-2.5-flash"}'

# Teach a new fact
curl -X POST localhost:8001/admin/{instance}/teach \
  -H "X-Admin-Key: $KEY" \
  -d '{"question": "cuanto cuesta botox", "answer": "desde 800k COP"}'

# View knowledge gaps
curl localhost:8001/admin/{instance}/gaps -H "X-Admin-Key: $KEY"
```

## Troubleshooting

```bash
# Check services
pm2 list
ss -tlnp | grep -E "800[0-9]"

# Check logs (last errors)
pm2 logs conny --lines 50 --nostream | grep -i error

# Test demo mode
curl -X POST localhost:8001/test \
  -H "X-Master-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"message": "hola", "chat_id": "test_001"}'

# Verify Telegram webhook
curl "https://api.telegram.org/bot$TOKEN/getWebhookInfo"

# Run tests
cd /home/ubuntu/conny && .venv/bin/python -m pytest tests/ -v
```

## Workflow for Changes

1. `git checkout -b fix/description`
2. Make changes
3. `py_compile` on every edited .py file
4. `pytest tests/` must pass
5. `pm2 restart conny` → verify with health endpoint
6. Commit with descriptive message
7. Merge to main only after verification
