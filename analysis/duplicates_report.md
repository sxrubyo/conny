# Duplicates Report: conny.py vs Satellites

## File Sizes
| file | lines |
|------|-------|
| conny.py | 28,972 |
| conny_voice.py | 156 |
| conny_audio.py | 349 |
| conny_memory.py | 219 |
| conny_memory_engine.py | 292 |
| conny_router.py | 307 |
| conny_session.py | 320 |
| conny_brain_v10.py | 804 |
| conny_production.py | 353 |

## voice vs audio: DIFFERENT THINGS
- voice = text post-processing (ConnyVoice class: humanize, split, anti-robot)
- audio = audio file handling (AudioHandler class: mime types, cache)
- NO overlap between them

## memory vs memory_engine: DIFFERENT THINGS
- memory = file-based session/knowledge storage (ConnyMemory class)
- memory_engine = entity extraction + vector stuff (ConnyMemoryEngine class)
- 1 shared name `_extract_entities` but different signatures/purpose

---

## Duplicate Functions Table

| function | in conny.py (line) | in satellite (file:line) | winner |
|----------|---------------------|--------------------------|--------|
| `_humanize` / `humanize` | 9606 (nested, per-bubble strip) | voice:73 (full pipeline w/ persona) | **satellite** - more complete |
| `_extract_entities` | 8229 (text->Dict[str,Any]) | mem_engine:264 (messages->phones/emails/names) | **different purpose** - both keep |
| `_detect_incoming_platform` / `detect_incoming_platform` | 3637 (simple if/elif) | router:26 (handles entry/changes/value structure) | **satellite** - handles more platforms |
| `reset_session` / `demo_reset_session` | 21830 (async endpoint) | session:200 (pure logic) | **satellite** - cleaner separation |
| `_detect_demo_owner_language` | 12615 (nested inside another fn) | session:210 (top-level, documented) | **satellite** - proper module-level |
| `_owner_confusion_or_language_signal` | 12678 (nested) | session:265 (top-level, documented) | **satellite** - proper module-level |
| `_lang_text` | 12671 (nested) | session:303 (top-level, documented) | **satellite** - proper module-level |
| `_is_low_quality_first_turn_bubble` / `is_low_quality_first_turn` | 8966 | brain:405 | **satellite** - part of full scoring system |
| `_init_brain_v10` / `init_brain` | 20200 (wrapper that imports+calls) | brain:673 (actual implementation) | **satellite** - is the real code; conny.py just calls it |

## Summary

- **True duplicates needing dedup**: 7 functions (session: 4, router: 1, voice: 1, brain: 1)
- **False positives** (same name, different purpose): 1 (`_extract_entities`)
- **Wrapper/caller** (conny.py imports satellite): 1 (`_init_brain_v10`)
- **Satellites with ZERO overlap**: voice (5 unique), audio (2 unique), memory (14 unique), production (just __init__)
- **Biggest win**: session.py has 4 functions that are nested/buried in conny.py -- satellite versions are cleaner

## Recommendation

1. Kill duplicates in conny.py for: `_detect_demo_owner_language`, `_owner_confusion_or_language_signal`, `_lang_text`, `_detect_incoming_platform`
2. Replace conny.py's `_humanize` with import from voice
3. `_init_brain_v10` already does the right thing (imports from satellite) -- just confirm it runs
4. Keep both `_extract_entities` -- they do different jobs
