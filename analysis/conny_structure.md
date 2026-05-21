# conny.py — Structural Map

**Total:** 28,972 lines | 63 classes | 507 functions (76 top-level, 431 methods)

---

## Classes by Domain

### Brain / Intelligence (lines 1525–5504)

| Line | Class | ~Size |
|------|-------|-------|
| 1525 | EmotionalMirrorEngine | 228 |
| 1753 | ClientPersonaDetector | 163 |
| 1916 | TimeContextualizer | 132 |
| 2048 | ConversationRhythmAnalyzer | 106 |
| 2154 | SectorClosingScripts | 523 |
| 2677 | ResponseQualityPatcher | 430 |
| 4294 | AntiRobotFilter | 357 |
| 4651 | ConversationIntelligence | 339 |
| 4990 | HyperHumanEngine | 73 |
| 5063 | SmartVariety | 200 |
| 5263 | ConversionFunnelTracker | 113 |
| 5376 | MultilingualHandler | 62 |
| 5438 | PersonaEvolution | 67 |

### Config / Data Models (lines 3107–4035)

| Line | Class | ~Size |
|------|-------|-------|
| 3107 | Config | 815 |
| 3922 | IntentType(Enum) | 19 |
| 3941 | SentimentType(Enum) | 8 |
| 3949 | UrgencyLevel(Enum) | 9 |
| 3958 | MessageAnalysis | 22 |
| 3980 | ConversationState | 13 |
| 3993 | MemoryItem | 14 |
| 4007 | Task | 14 |
| 4021 | MCPPlugin | 14 |
| 4035 | PersonalityProfile | 259 |

### Infrastructure / LLM (lines 5505–7882)

| Line | Class | ~Size |
|------|-------|-------|
| 5505 | ModelManager | 623 |
| 6128 | DatabaseManager | 1291 |
| 7419 | LLMProvider | 31 |
| 7450 | GroqProvider(LLMProvider) | 33 |
| 7483 | GeminiProvider(LLMProvider) | 50 |
| 7533 | OpenRouterProvider(LLMProvider) | 32 |
| 7565 | OpenAIProvider(LLMProvider) | 36 |
| 7601 | LLMEngine | 282 |

### Core Processing (lines 7883–10107)

| Line | Class | ~Size |
|------|-------|-------|
| 7883 | MessageAnalyzer | 470 |
| 8353 | ReasoningEngine | 324 |
| 8677 | ResponseGenerator | 1431 |

### Channels / Integrations (lines 10108–11638)

| Line | Class | ~Size |
|------|-------|-------|
| 10108 | WhatsAppConnector | 393 |
| 10501 | CalendarBridge | 251 |
| 10752 | WebSearchEngine | 451 |
| 11203 | MCPCapability(Enum) | 12 |
| 11215 | MCPPluginBase(ABC) | 30 |
| 11245 | CalendarPlugin(MCPPluginBase) | 110 |
| 11355 | NotificationsPlugin(MCPPluginBase) | 70 |
| 11425 | MCPManager | 78 |
| 11503 | TaskManager | 136 |

### Orchestrator (lines 11639–22015) — THE GOD CLASS

| Line | Class | ~Size |
|------|-------|-------|
| 11639 | **ConnyUltra** | **10,377** |

### Production / QA (lines 22016–25309)

| Line | Class | ~Size |
|------|-------|-------|
| 22016 | ConversationSimulator | 678 |
| 22694 | HallucinationGuard | 211 |
| 22905 | FailurePredictorEngine | 271 |
| 23176 | SmartContextManager | 135 |
| 23311 | AppointmentStateMachine | 233 |
| 23544 | ConversationRecoveryEngine | 182 |
| 23726 | ResponseVariationEngine | 89 |
| 23815 | ProactiveCampaignEngine | 164 |
| 23979 | AdminIntelligentBriefing | 158 |
| 24137 | SelfTestSuite | 1173 |

### Observatory / Telemetry (lines 25310–25814)

| Line | Class | ~Size |
|------|-------|-------|
| 25326 | EventType | 15 |
| 25341 | AgentEvent | 26 |
| 25367 | EventBus | 69 |
| 25436 | AgentTracer | 65 |
| 25501 | ConversationObserver | 89 |
| 25590 | AIDiagnostician | 410 |

### Trainer / Learning (lines 25815–27825)

| Line | Class | ~Size |
|------|-------|-------|
| 26000 | SkillEngine | 160 |
| 26160 | TrainerGateway | 345 |
| 26505 | OwnerStyleController | 855 |
| 27360 | PromptEvolver | 274 |
| 27634 | AdminClientMode | 191 |
| 27825 | NovaRuleSync | ~1147 |

---

## Major Sections (by line range)

| Lines | Section |
|-------|---------|
| 1–172 | Imports & module loading |
| 173–1519 | V9 Patches (Colombian vocab, WhatsApp patterns, archetypes, skills, natural responses) |
| 1520–2676 | Emotional/Persona engines |
| 2677–3106 | Response quality patching |
| 3107–3921 | Config (815 lines!) |
| 3922–5504 | Data models + Intelligence classes |
| 5505–7418 | ModelManager + DatabaseManager |
| 7419–7882 | LLM Providers |
| 7883–10107 | Core pipeline (Analyzer -> Reasoning -> Response) |
| 10108–11638 | Channels (WhatsApp, Calendar, Web, MCP, Tasks) |
| 11639–22015 | ConnyUltra (orchestrator god-class) |
| 20327–22015 | FastAPI routes (inside ConnyUltra? No — top-level after class) |
| 22016–25309 | Production hardening (simulator, guards, recovery) |
| 25310–25814 | Observatory (events, tracing, diagnostics) |
| 25815–28972 | Trainer (skills, gateway, style, prompt evolution, admin) |

---

## Satellite Files

| File | Lines |
|------|-------|
| conny.py | 28,972 |
| conny_cli.py | 11,716 |
| conny-omni.py | 3,828 |
| smart_handoff.py | 1,150 |
| conny_brain_v10.py | 804 |
| conny_admin.py | 772 |
| conny_domino.py | 696 |
| conny_bridge.py | 656 |
| conny_i18n.py | 618 |
| conny-chat.py | 578 |
| conny_send_guard.py | 550 |
| conny_tui.py | 502 |
| conny_nuke_robot_phrases.py | 493 |
| conny_pitch_upgrade.py | 471 |
| conny_generator.py | 446 |
| conny_cli_bb.py | 437 |
| conny_production.py | 353 |
| conny_audio.py | 349 |
| conny_smart_features.py | 333 |
| knowledge_base.py | 330 |
| conny_session.py | 320 |
| conny_router.py | 307 |
| conny_sync_fix.py | 306 |
| conny_app.py | 304 |
| conny_memory_engine.py | 292 |
| conny_pairing.py | 253 |
| conny_patch.py | 291 |
| All others | <250 each |
| **TOTAL** | **59,992** |

---

## Key Findings

- **ConnyUltra** is a 10,377-line god-class (36% of the file)
- FastAPI routes live at top-level after line ~20327 (admin, webhook, API, analytics, calendar, demo)
- 507 total functions; most are methods inside classes
- The file has grown by accretion: V9 patches bolted on at the top, Observatory/Trainer appended at the bottom
- Config alone is 815 lines of hardcoded data
