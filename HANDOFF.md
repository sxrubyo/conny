# Conny Sprint Handoff
_Last updated: 2026-05-14 07:15 UTC_

## Goal
Conny v9.0 — admin control, memory engine, humanization, Nova proxy

## Status
- [x] Phase 0: Tooling installed (repomix, power repos)
- [x] Phase 1: Architecture mapped + broken imports fixed
- [x] Phase 2: Admin API built (conny_admin_api.py)
- [x] Phase 3: Memory engine (conny_memory_engine.py)
- [x] Phase 4: Humanization + CoT (conny_voice.py, conny_cron.py)
- [x] Phase 5: Structure created (core/, nova/rules/, docs/)
- [x] Phase 6: Tests (28/28 passing)
- [x] Phase 7: GitHub push + npm publish (v9.0.0 live)
- [x] Phase 8: Cleanup — 12 obsolete docs deleted, instructions.md upgraded

## Modified Files (this sprint)
- conny.py (admin API mount, memory init, cron scheduler, v9 branding)
- conny_admin.py (fixed SyntaxError)
- conny_production.py (fixed SyntaxError)
- conny_utils.py (added missing json import)
- conny_admin_api.py (NEW — /admin REST endpoints)
- conny_memory_engine.py (NEW — episodic/semantic/procedural memory)
- conny_uncertainty.py (NEW — confidence scoring)
- conny_voice.py (NEW — humanization post-processor)
- conny_nova_proxy.py (NEW — transparent LLM proxy)
- conny_cron.py (NEW — APScheduler weekly consolidation)
- core/__init__.py (NEW — clean public API)
- nova/rules/default.yaml (NEW — governance rules)
- docs/architecture_map.json (NEW — 79-file dependency graph)
- tests/test_*.py (5 NEW test files, 28 tests)
- package.json (v9.0.0)
- requirements.txt (added watchdog, apscheduler, scikit-learn, numpy, pyjwt)
- CLAUDE.md (NEW — project rules)
- instructions.md (rewritten for v9.0)
- DELETED: 12 obsolete Omni docs

## PM2 Status
- conny: online (v9.0.0, port 8001)
- conny-clinica-de-las-americas: online (port 8003)
- whatsapp-bridge: online (port 8002)
- nova-core: online

## Git
- Branch: main
- Tag: v9.0.0
- Remote: origin (github.com/sxrubyo/conny)
- npm: conny-ai@9.0.0 published

## Next Steps
- Wire memory_engine.ingest_conversation() into the response pipeline (after every conversation)
- Wire uncertainty_detector into process_message (alert admin on low confidence)
- Wire conny_voice.humanize() as post-processor on all response paths
- Add Domino quality check to non-demo paths (production instances)
- Consolidate GUIA_*.md files into a single OPERATIONS.md
