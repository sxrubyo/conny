# Conny v10.0 — System Instructions & Agent Programming Capabilities

## Architecture

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
  conny_admin_api.py    → FastAPI /admin endpoints (persona, model, teach, gaps, chats, dashboard)
  conny_memory_engine.py→ episodic + semantic + procedural memory with TF-IDF recall
  conny_voice.py        → humanization post-processor (robot pattern removal)
  conny_uncertainty.py  → confidence scoring + admin alerts
  conny_nova_proxy.py   → transparent LLM proxy (memory + governance + voice)
  conny_brain_v10.py    → conversation intelligence (LLM-first, anti-loop)
  conny_domino.py       → response quality control
  nova_bridge.py          → Nova governance client (validate before send)
  conny_cron.py         → APScheduler (weekly memory consolidation, Sun 3am)
  conny_send_guard.py   → quality control guard rails protecting against fragment ejections
```

## Core Principles

1. **Never break production.** Both PM2 instances must stay online. Branch before refactoring.
2. **Plan before acting.** Research → Strategy → Execution. Use subagents to investigate.
3. **Validate exhaustively.** Run `pytest tests/` + `pm2 logs conny --lines 20` after changes.
4. **No secrets in git.** Protect `.env`, `auth_info_*`, `*.db` files.

## Instance Isolation

- Each client: isolated directory, own `.env`, own SQLite DB, own Brand Vault.
- Port assignment: unique per instance, set in `.env` as `PORT=`.
- Telegram: shared router on main instance, routing by `chat_id` via `conny pair`.
- WhatsApp: one bridge session per instance, never share `auth_info_*` folder.
- Core code sync: `conny_core/`, `conny_agents/`, brain, domino — shared across instances.
- Client data: NEVER sync databases, conversations, or credentials.

## Response Rules (enforced by conny_voice.py & conny_send_guard.py)

### Never say:
- "como IA" / "como asistente virtual" / "como inteligencia artificial"
- "no tengo la capacidad" / "está fuera de mi alcance"
- "no puedo procesar" / "no puedo entender"
- "Hola! Soy Conny, tu asistente virtual"
- "Por supuesto!" / "Claro que sí!" / "Con gusto!"

### Always:
- Sound like a real Colombian receptionist (warm, concise, direct).
- One question per turn, focused on advancing the conversation.
- Max 1 exclamation mark per response.
- Never start a response with the bot's name.
- If uncertain: deflect naturally, alert admin, log gap.
- **Guard Rails (conny_send_guard.py):** If the LLM response contains multiple bubbles (`|||`), short or severe fragments (e.g. "ok") at the end must be popped while keeping preceding rich bubbles, instead of discarding the entire response.

## Admin API & Real-Time WhatsApp Dashboard

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

### Real-Time Chat Dashboard
The admin dashboard is a premium single-page application built with zero-dependency Vanilla CSS and responsive panels. It acts exactly like a WhatsApp Web client:
- **Dashboard URL:** `http://localhost:8001/admin/{instance_id}/dashboard?key=YOUR_API_KEY` (Key is stored in `localStorage` for all future requests).
- **List Chats API (`GET /admin/{instance_id}/chats`):** Returns sidebar active chats, snippets, and counts.
- **Chat Details API (`GET /admin/{instance_id}/chats/{chat_id}`):** Returns chronological message bubbles with performance metrics (tokens used, latency_ms, used model) and raw cognitive analysis.
- **Real-Time Sync:** Automatically syncs every 4 seconds via polling.

---

## Agentic Programming Skills Catalog

To accelerate development and implement world-class features for Conny, the coding agent has access to **over 130+ specialized skills**. These are organized into domain folders and can be activated/referenced using the `$skill-name` notation to leverage custom workflows, automated testing, and optimization pipelines.

### 1. High-Fidelity & Modern Frontend
- **`$frontend-skill`**: Standard for beautiful user interfaces. Emphasizes custom HSL color systems, glassmorphism, responsive panels, typography, and polished micro-animations. Avoids Tailwind unless explicitly requested.
  - *Trigger:* When iterating on or designing new views for the Conny Admin Dashboard.
- **`$video-to-website`**: Dynamic scroll-driven animated sites.
  - *Trigger:* When building landing pages or product showcases for Conny.
- **`$figma-implement-design`** & **`$figma`**: Transpile Figma assets and design nodes into production-ready code with 1:1 visual fidelity.
  - *Trigger:* When the user provides Figma specifications or node URLs.

### 2. Systematic Quality & Debugging
- **`$systematic-debugging`**: Root-cause analysis before any code changes. Isolates errors systematically across Conny's voice filters, domino checks, and LLM proxies.
  - *Trigger:* When diagnosing word-eating bugs, pipeline crashes, or test failures.
- **`$playwright`** & **`$playwright-interactive`**: Automates real headless browser environments to test dashboard UI responsiveness, authorization, and polling.
  - *Trigger:* When testing and validating dashboard UI changes end-to-end.
- **`$verification-quality`**: Rigorous QA checks and validation matrices.
  - *Trigger:* Pre-release and pre-deployment code reviews.

### 3. Orchestration & Collaborative Swarms
- **`$swarm-orchestration`** & **`$swarm-advanced`**: Spawns multiple specialized subagents (researchers, architects, coders, reviewers) to execute major feature updates across 3+ modules concurrently.
  - *Trigger:* When carrying out large migrations, multi-tenant DB restructuring, or multi-channel integration.
- **`$sparc-methodology`**: Enforces the structured workflow: Specification, Pseudocode, Architecture, Refinement, Completion.
  - *Trigger:* For new, complex feature designs.

### 4. Memory & Performance Systems
- **`$memory-management`** & **`$agentdb-vector-search`**: Manages semantic lookup and HNSW fast searches inside Conny's memory engines.
  - *Trigger:* Optimizing conversation history recall or context retrieval latencies.
- **`$performance-analysis`** & **`$agentdb-optimization`**: Profiles latency, database query times, and memory allocations.
  - *Trigger:* When LLM proxy latencies exceed 1.5 seconds.
- **`$security-audit`** & **`$security-best-practices`**: CVE detection, credential isolation, and input sanitization audits.
  - *Trigger:* When modifying `/admin` endpoints, CORS configurations, or JWT authentication layers.

### 5. Task & Workflow Automation
- **`$commit-work`**: Reviews, stages, and splits changes into high-quality, conventional commits with detailed descriptions.
  - *Trigger:* When finalizing features and submitting pull requests.
- **`$session-handoff`**: Prepares detailed state snapshots, unresolved items, and progress logs to transition seamlessly between agent sessions.
  - *Trigger:* Before session termination or when approaching context limit constraints.
- **`$linear`**: Syncs tasks, bug reports, and progress directly with Linear tickets.
  - *Trigger:* When the user requests status updates or ticket creation.

---

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
2. Make changes using `$systematic-debugging` and `$sparc-methodology`.
3. `py_compile` on every edited .py file.
4. `pytest tests/` must pass.
5. Propagate runtime changes to all sub-instances with `conny sync`.
6. `pm2 restart conny` → verify with health endpoint and dashboard access.
7. Use `$commit-work` to commit with conventional, descriptive messages.
8. Merge to main only after verification.
