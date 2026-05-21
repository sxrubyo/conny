# REFACTOR PLAN — conny.py → src/conny/

## STATS
- 28,972 lines | 63 classes | 507 functions
- ConnyUltra god-class: 10,377 lines (36%)
- 16 satellite modules imported
- 2 circular dependency risks (conny_admin, conny_production)
- 7 true duplicates (satellite always wins)
- ~60k total lines ecosystem

## MIGRATION ORDER (independientes primero)

### Wave 1 — Zero coupling (can move immediately)
1. `src/conny/utils/i18n.py` ← conny_i18n.py (standalone)
2. `src/conny/utils/helpers.py` ← conny_utils.py (standalone)
3. `src/conny/brain/uncertainty.py` ← conny_uncertainty.py (standalone)
4. `src/conny/integrations/knowledge.py` ← knowledge_base.py (standalone)

### Wave 2 — Low coupling (import from core only)
5. `src/conny/brain/memory.py` ← conny_memory_engine.py (standalone)
6. `src/conny/channels/voice.py` ← conny_voice.py (standalone)
7. `src/conny/channels/audio.py` ← conny_audio.py (needs Config)
8. `src/conny/core/router.py` ← conny_router.py (standalone)
9. `src/conny/core/session.py` ← conny_session.py (standalone)

### Wave 3 — Medium coupling (import from conny.py globals)
10. `src/conny/brain/engine.py` ← conny_brain_v10.py (imports from __main__)
11. `src/conny/production/guard.py` ← conny_send_guard.py (needs db)
12. `src/conny/production/handoff.py` ← smart_handoff.py (needs db+llm)
13. `src/conny/admin/api.py` ← conny_admin_api.py (needs app)

### Wave 4 — The god-class split (ConnyUltra 10k lines)
14. Extract demo logic → `src/conny/demo/handler.py`
15. Extract buffer/send → `src/conny/core/messenger.py`
16. Extract FastAPI routes → `src/conny/api/routes.py`
17. ConnyUltra remains as thin orchestrator (~500 lines)

### Wave 5 — conny_cli.py (second monolith, 459KB)
18. Separate refactor session

## CIRCULAR DEPS FIX
- conny_admin imports `db, llm_engine` from conny → inject via params
- conny_production imports `db, llm_engine, kb` → inject via params
- Pattern: pass dependencies as constructor args, not global imports

## RISKS
- ConnyUltra has 431 methods — splitting it will break many internal refs
- Demo logic (lines 12507-15000) mixes with core orchestration
- Some functions are 500+ lines with nested closures
- Production DB paths are hardcoded in several places

## FIRST MODULE TO EXTRACT: conny_i18n.py
- 0 dependencies on conny.py
- Already a clean standalone module
- Quick win to validate the pattern
