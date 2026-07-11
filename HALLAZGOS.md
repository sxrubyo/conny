# Hallazgos de auditoria Bublee

Fecha: 2026-07-06

Alcance inicial: root `/home/ubuntu/bublee`, instancia real `instances/clinica-de-las-americas` y agente `agents/ovni`.

## Confirmaciones de arquitectura

- `BubleeProduction` real no esta en `src/domain/production.py`. El runtime importa `BubleeProduction` desde `src/core/production_monitor.py`.
- El modo demo real entra por `src/core/runtime.py:854` cuando `Config.DEMO_MODE=True` y delega a `src/interfaces/web/demo_handler.py:15`.
- En este checkout, las copias activas estan bajo `instances/clinica-de-las-americas` y `agents/ovni`, no bajo `/home/ubuntu/bublee-instances`.

## Hallazgos

| ID | Severidad | Archivo:linea | Bug | Estado |
|---|---|---:|---|---|
| H-001 | Critico | `src/core/production_monitor.py:255` | Produccion llama `llm_engine.complete()` directo y no pasa por `ReasoningEngine.reason()` ni `ResponseGenerator.generate()`. Eso deja muerto el razonador real y tambien evita que `brain_v10` afecte respuestas de pacientes por este camino. | Arreglado en root, clinica y Ovni. Test: `tests/test_production_monitor_wiring.py` |
| H-002 | Critico | `src/core/production_monitor.py:333` | Si la confianza baja de 0.5, se alerta al admin pero igual se sobreescribe la respuesta al paciente con texto hardcodeado: `dame un momento que verifico eso`. Esto contradice la regla de no mandar fallback generico al paciente/prospecto cuando el agente no sabe responder. | Arreglado en root, clinica y Ovni: alerta admin + guarda mensaje user + no envia fallback al paciente. Test: `tests/test_production_monitor_wiring.py` |
| H-003 | Medio | `bublee_commands.py:172` | `/aprendizaje` importa `SelfImprovementEngine` desde `bublee_admin.py` legacy. El runtime usa la clase real de `src/core/admin_engines.py`, por lo que hay dos implementaciones vivas para la misma funcion. | Arreglado en root, clinica y Ovni. Test: `tests/test_admin_wiring.py` |
| H-004 | Medio | `src/bublee/admin/dashboard.py:620` y `src/bublee/admin/dashboard.py:733` | El dashboard admin alternativo conserva comparaciones exactas de confirmacion (`si`, `ok`, `claro`). Esto ya fue corregido en `src/core/admin_engines.py`, pero esta copia puede divergir si alguien la usa. | Arreglado en root, clinica y Ovni. Test: `tests/test_admin_wiring.py` |
| H-005 | Medio | `src/interfaces/web/demo_handler.py:1738` y `src/interfaces/web/demo_handler.py:1915` | Demo devuelve textos hardcodeados de "no te escuche / no entendi" cuando no puede interpretar nombre de negocio. No es el fallback global de IA, pero si es una respuesta generica repetible enviada a prospectos. | Arreglado en root, clinica y Ovni: esas ramas vuelven al onboarding LLM. Validacion: grep sin esos textos en `src/interfaces/web/demo_handler.py` |
| H-006 | Bajo | `bublee_cli.py:2076` y `bublee_cli.py:3753` | La master key todavia se imprime en la CLI local como resumen operativo. No aparece en `bublee-chat.py` como prompt enviado a LLM, pero queda expuesta en terminal/logs si se capturan salidas. | Pendiente |
| H-007 | Critico | `src/core/globals.py:9788` y `bublee_core/prompt_ops.py:143` | Produccion podia volver a saludar/presentarse en cada turno ("Hola, soy Bublee...") aunque ya hubiera historial. El transcript del 2026-07-06 muestra al paciente cansandose por repeticion. | Arreglado en root, clinica y Ovni: prompt de continuidad + filtro post-LLM. Test: `tests/test_redundant_opening_filter.py` |
| H-008 | Critico | `src/core/production_monitor.py:255` | Si el admin no cargo suficiente informacion, el LLM podia inventar datos de la clinica o responder generalidades. Ejemplo del transcript: afirmar servicios amplios/cirugias sin validar contra conocimiento cargado. | Arreglado en root, clinica y Ovni: gate de conocimiento insuficiente alerta admin y no envia respuesta al paciente. Test: `tests/test_production_monitor_wiring.py` |

## Fixes previos verificados

- `bublee_utils.py`: existen `is_affirmative()`, `is_negative()` y `notify_owner_of_ai_failure()`.
- `bublee.py`: `init_bublee()` llama `auto_patch()` de `brain_v10`.
- `bublee_brain_v10.py`: el patch es idempotente con `_brain_v10_patched` y usa `inspect.signature(...).bind`.
- `src/core/admin_engines.py`: usa `is_affirmative()` en setup/activacion, expira sesiones abandonadas a 900 segundos y tiene `analyze_performance()` + `apply_improvements()`.
- `src/core/runtime.py`: `AdminLearningEngine(db)` aparece una sola vez en `initialize()`, `_split_bubbles()` usa limite variable, y los catch-all finales notifican al dueño con `notify_owner_of_ai_failure()` y no mandan fallback hardcodeado al remitente.
- `src/core/globals.py`: no queda `def _with_intro` muerto y existe deteccion `respuesta_repetitiva`.
- `bublee-omni.py`: no queda default activo `omni_secret_change_me`; solo queda mencionado en comentario historico.
- `bublee-chat.py`: no aparece `Master Key` en prompts.

## Riesgos abiertos

- Conectar `ReasoningEngine` y `ResponseGenerator` en produccion puede cambiar comportamiento visible para pacientes. Debe hacerse con test/stub primero y sincronizacion real solo con aprobacion explicita.
- El manejo de baja confianza puede requerir decision de producto: silencio al paciente + alerta inmediata al admin cumple la regla estricta, pero puede sentirse como demora si el admin no responde rapido.
