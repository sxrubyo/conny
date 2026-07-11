# REFACTOR PLAN — bublee.py → src/bublee/

## STATS
- 28,972 lines | 63 classes | 507 functions
- BubleeUltra god-class: 10,377 lines (36%)
- 16 satellite modules imported
- 2 circular dependency risks (bublee_admin, bublee_production)
- 7 true duplicates (satellite always wins)
- ~60k total lines ecosystem

## MIGRATION ORDER (independientes primero)

### Wave 1 — Zero coupling (can move immediately)
1. `src/bublee/utils/i18n.py` ← bublee_i18n.py (standalone)
2. `src/bublee/utils/helpers.py` ← bublee_utils.py (standalone)
3. `src/bublee/brain/uncertainty.py` ← bublee_uncertainty.py (standalone)
4. `src/bublee/integrations/knowledge.py` ← knowledge_base.py (standalone)

### Wave 2 — Low coupling (import from core only)
5. `src/bublee/brain/memory.py` ← bublee_memory_engine.py (standalone)
6. `src/bublee/channels/voice.py` ← bublee_voice.py (standalone)
7. `src/bublee/channels/audio.py` ← bublee_audio.py (needs Config)
8. `src/bublee/core/router.py` ← bublee_router.py (standalone)
9. `src/bublee/core/session.py` ← bublee_session.py (standalone)

### Wave 3 — Medium coupling (import from bublee.py globals)
10. `src/bublee/brain/engine.py` ← bublee_brain_v10.py (imports from __main__)
11. `src/bublee/production/guard.py` ← bublee_send_guard.py (needs db)
12. `src/bublee/production/handoff.py` ← smart_handoff.py (needs db+llm)
13. `src/bublee/admin/api.py` ← bublee_admin_api.py (needs app)

### Wave 4 — The god-class split (BubleeUltra 10k lines)
14. Extract demo logic → `src/bublee/demo/handler.py`
15. Extract buffer/send → `src/bublee/core/messenger.py`
16. Extract FastAPI routes → `src/bublee/api/routes.py`
17. BubleeUltra remains as thin orchestrator (~500 lines)

### Wave 5 — bublee_cli.py (second monolith, 459KB)
18. Separate refactor session

## CIRCULAR DEPS FIX
- bublee_admin imports `db, llm_engine` from bublee → inject via params
- bublee_production imports `db, llm_engine, kb` → inject via params
- Pattern: pass dependencies as constructor args, not global imports

## RISKS
- BubleeUltra has 431 methods — splitting it will break many internal refs
- Demo logic (lines 12507-15000) mixes with core orchestration
- Some functions are 500+ lines with nested closures
- Production DB paths are hardcoded in several places

## FIRST MODULE TO EXTRACT: bublee_i18n.py
- 0 dependencies on bublee.py
- Already a clean standalone module
- Quick win to validate the pattern
