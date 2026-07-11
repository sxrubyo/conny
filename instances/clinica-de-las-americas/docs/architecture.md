# Bublee v10 — modular scaffold

## Estado actual

- `bublee.py` sigue siendo el runtime productivo real.
- `bublee_core/conversation_engine.py` y `bublee_domino.py` existen, pero no concentran toda la logica.
- La identidad, memoria y soul ya viven en archivos reales: `identity/`, `memory/`, `soul/`.

## Objetivo del scaffold

Separar el monolito en modulos pequenos sin cortar produccion:

- `bublee_core/`: estado, identidad, memoria y contexto conversacional
- `bublee_agents/`: agentes por dominio de negocio
- `bublee_skills/`: capacidades aisladas como demo, tono y postproceso
- `bublee_integrations/`: WhatsApp y LLM

## Regla de migracion

1. El runtime sigue entrando por `bublee.py`.
2. Cada extraccion futura se mueve con tests verdes.
3. Ningun modulo nuevo toma trafico real hasta tener validacion binaria.

## Primera frontera prioritaria

- override conversacional del negocio
- onboarding del negocio nuevo
- lectura/escritura de `identity/`, `memory/`, `soul/`
- transporte WhatsApp separado de logica conversacional
