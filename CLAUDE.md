# MELISSA → CONNY — Refactorización Total
# Monolito 1.3MB → Arquitectura modular limpia
# Stack: Claude Opus 4.6 + Ruflo + Caveman

## ARQUITECTURA TARGET

```
src/melissa/
├── core/        ← config, session, router, init
├── brain/       ← engine, memory, learning, uncertainty
├── channels/    ← telegram, voice, cli, web
├── personas/    ← manager, generator
├── integrations/← calendar, search, knowledge
├── admin/       ← api, dashboard
├── production/  ← guard, handoff, monitor
└── utils/       ← i18n, helpers, logger
```

## REGLAS

1. Conservar funcionalidad > perfección
2. Nunca borrar, siempre mover a legacy/
3. Un módulo = una responsabilidad
4. Sin prefijo melissa_ dentro del paquete
5. Commits por fase
6. grep/rg para analizar — NUNCA leer melissa.py entero

## ESTADO

- Fase 0: checkpoint [pendiente]
- Fase 1: análisis [pendiente]
- Fase 2: gate humano [pendiente]
- Fase 3: construcción [pendiente]
- Fase 4: QA [pendiente]
- Fase 5: limpieza [pendiente]
