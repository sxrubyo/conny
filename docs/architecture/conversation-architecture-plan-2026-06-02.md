# Bublee Conversation Architecture Plan - 2026-06-02

## Bugs graves detectados en conversacion

1. `src/interfaces/web/demo_handler.py` y `src/bublee/demo/handler.py` agregaban una burbuja hardcodeada despues del LLM en primer saludo: "cuentame que te gustaria revisar". Esto hacia que una respuesta buena del modelo sonara a fallback.
2. El modo admin intercepta todo con un prompt corto ("Eres Bublee... 2 burbujas") y no usa una memoria/admin brain real. Resultado: el admin recibe respuestas de bot cuando pide acciones operativas complejas.
3. El modo demo desactiva `is_admin_demo` cuando `sim_mode_active=True`. Si el dueno entra a simulacion, pierde capacidades admin en ese mismo chat.
4. Existen dos handlers de demo casi duplicados: `src/interfaces/web/demo_handler.py` y `src/bublee/demo/handler.py`. Un fix en una ruta puede no aplicar en la otra.
5. Hay respuestas hardcodeadas para comandos y flujos de aprendizaje que se ejecutan antes de pedir criterio al modelo.
6. El fallback de cliente (`_demo_customer_last_resort`) todavia interpreta intenciones por keywords. Debe limitarse a "no hubo modelo" y reportar la causa.
7. El fallback de owner (`_demo_owner_last_resort`) tiene pitch fijo y puede sonar igual en conversaciones distintas.
8. El modo aprendizaje manual puede tomar frases como informacion del negocio cuando el usuario esta corrigiendo o cuestionando.
9. El cambio de negocio en caliente depende de heuristicas de nombre y puede borrar contexto valido.
10. `handle_command` en `bublee_router.py` devuelve respuestas estaticas como "no tengo memoria activa todavia", aunque el sistema si tiene memoria en otros modulos.
11. Los errores de LLM en `_llm` y `_llm_conv` se convierten en `None` sin exponer causa conversacional ni decision de continuidad.
12. Los `except Exception: pass` silencian fallos de DB, sesion, archivos, media y limpieza de contexto.
13. La busqueda del negocio puede marcar `found_online=True` por texto suficiente aunque el enlace sea generico si la validacion no es consistente entre rutas.
14. La decision owner/cliente/admin esta distribuida entre flags de sesion, texto y comandos. No hay una maquina de estados unica.
15. La memoria de conversacion se consulta como historial plano; no separa hechos del dueno, hechos del negocio, preferencias de tono y mensajes de cliente simulado.
16. La normalizacion de primera respuesta puede reescribir respuestas ya producidas por LLM y cambiar identidad/tono.
17. El prompt de cliente simulado contiene demasiadas reglas mezcladas, con contradicciones entre "no eres bot", "si preguntan IA", "persona real" y "creador".
18. El prompt de salud/retail/general esta embebido en un handler de 3k+ lineas, lo que impide testear tonos de forma aislada.
19. Los comandos demo (`/bot`, `/stats`, `/2am`, `/precio`) mezclan marketing, pruebas y conversacion productiva en la misma ruta.
20. El modo bot numerico queda activo en sesion y puede capturar mensajes naturales que parezcan numeros sin confirmacion de contexto.

## Areas reales de mejora arquitectonica

1. Crear `ConversationStateMachine` unica para `owner_onboarding`, `owner_learning`, `owner_demo`, `customer_simulation`, `admin_ops`, `handoff_waiting`.
2. Crear `SpeakerRoleResolver` con evidencia explicita para decidir `admin`, `owner`, `customer`, `unknown`.
3. Mover todo fallback a `FallbackPolicy` con contrato: solo cuando no hay salida de LLM, excepcion o score bajo.
4. Crear `LLMDecisionResult` con `text`, `provider`, `model`, `had_output`, `error_kind`, `confidence`, `fallback_allowed`.
5. Reemplazar `return _send(r or fallback)` por una funcion central `send_model_or_last_resort`.
6. Unificar los dos handlers de demo en un solo modulo importado por ambas rutas.
7. Extraer prompts a archivos versionados por rol: `prompts/admin.md`, `prompts/owner.md`, `prompts/customer.md`.
8. Crear prompt registry con checksum para saber que prompt se uso en cada respuesta.
9. Separar `AdminBrain` de `DemoBrain`. El admin necesita capacidades operativas, no pitch.
10. Dar memoria propia al admin: negocios, comandos recientes, clientes activos, errores, decisiones y preferencias.
11. Crear `BusinessProfileMemory` para nombre, URL confirmada, servicios, ubicacion, precios, horarios y fuentes.
12. Crear `ConversationMemoryWindow` con resumen incremental, no solo ultimos N mensajes.
13. Persistir estado de demo en DB; `_demo_sessions` en memoria pierde continuidad con restart.
14. Crear migracion SQLite para sesiones demo versionadas.
15. Añadir `source_confidence` a resultados de busqueda de negocio.
16. Validar URL encontrada con nombre, ciudad y dominio antes de presentarla al dueno.
17. Crear estado `business_candidate_pending_confirmation` para que "si somos nosotros" no se vuelva nombre de negocio.
18. Crear detector LLM de "esto no es mi negocio" en vez de keywords.
19. Crear `DocumentIngestionService` para PDF, imagen, audio y texto, con errores visibles al usuario.
20. Guardar documentos leidos como fuentes del negocio, no como texto pegado en contexto.
21. Crear `AudioTranscriptionResult` y exponer cuando audio no se pudo transcribir por causa real.
22. Separar comandos slash de lenguaje natural: slash ejecuta, natural va primero al LLM.
23. Convertir `/models` y modelos en una configuracion persistente por instancia/chat.
24. Crear cascada de modelos con backoff, quota handling y reporte de proveedor agotado.
25. Exponer errores 429/401/403 al admin con decision "esperar, cambiar modelo o fallback".
26. Añadir telemetria por respuesta: modelo usado, latencia, fallback, repair, guard clean.
27. Convertir `SendGuard` en postprocesador quirurgico, no filtro semantico amplio.
28. Crear pruebas de "no se agregan burbujas por codigo si LLM ya respondio".
29. Crear pruebas de "admin no cae en demo cuando sim_mode_active".
30. Crear pruebas de "dueno pregunta en ingles y Bublee continua en ingles".
31. Crear pruebas de "confirmacion de negocio no pisa nombre ya cargado".
32. Crear pruebas de "documento recibido sin texto no se trata como negocio aprendido".
33. Crear pruebas de "precio desconocido dispara handoff o confirmacion, no invento".
34. Crear pruebas de "quien te hizo" por LLM con guard de seguridad final.
35. Crear `ResponseQualityGate` reutilizable para owner/customer/admin.
36. Mover listas de banned phrases a fixtures testables.
37. Eliminar `except Exception: pass` o reemplazarlos por `log.warning` con contexto.
38. Hacer que `_send` sea pura: limpiar, guardar y dividir no deberian mutar estado conversacional.
39. Separar "split bubbles" de "normalize casing" y "guard clean".
40. Eliminar prompts enormes dentro de funciones y pasarlos por builders testeables.
41. Crear `ConversationTrace` por mensaje para depurar por que eligio una ruta.
42. Crear `AdminActionRouter` para "muestrame conversaciones", "reinicia", "crea instancia", "cambia prompt".
43. Crear `ToolPermissionPolicy` para diferenciar acciones terminal seguras, confirmables y bloqueadas.
44. Conectar `smart_handoff` con el admin brain para que el admin vea contexto completo antes de responder.
45. Añadir timeout visible de handoff por cliente y por admin.
46. Crear "shadow response" en pruebas: LLM responde, fallback alternativo se calcula pero no se envia.
47. Añadir replay harness de conversaciones reales anonimizadas.
48. Crear matriz de roles por canal: Telegram, WhatsApp bridge, WhatsApp Cloud, CLI.
49. Evitar que `Config.DEMO_MODE` cambie identidad del negocio si ya existe instancia.
50. Crear contract tests para instalacion npm/GitHub: `bublee`, `bublee init`, `bublee chat`, `bublee config`.
51. Versionar prompts y reglas por instancia para que un cliente nuevo no herede datos del autor.
52. Crear `BusinessSearchService` con Brave, Apify y fallback web; hoy la logica esta acoplada al handler.
53. Añadir cache de busqueda con invalidacion por correccion del dueno.
54. Crear `LocalePolicy` para idioma por chat y por instancia.
55. Añadir un "conversation doctor" que explique: ruta elegida, estado, modelo, memoria usada y por que hubo fallback.

## Plan de ejecucion

### Fase 0 - Fix inmediato aplicado

- Quitar la burbuja hardcodeada de primer saludo en los dos handlers de demo.
- Añadir prueba para garantizar que el LLM puede responder una sola burbuja sin que el codigo agregue CTA.

### Fase 1 - Cortar los bugs que mas dañan experiencia

- Unificar fallback bajo una sola politica.
- Loguear errores de LLM y DB que hoy se silencian.
- Separar admin de demo aunque `sim_mode_active` este activo.
- Crear trazas por respuesta para saber si hablo LLM, repair o fallback.

### Fase 2 - Estado y memoria real

- Persistir demo state en SQLite.
- Crear memoria separada de admin, owner, negocio y cliente simulado.
- Resolver confirmaciones de negocio con estado explicito.
- Guardar fuentes de busqueda/documentos como entidades, no como texto pegado.

### Fase 3 - Arquitectura modular

- Fusionar los dos demo handlers.
- Extraer prompts a registry versionado.
- Crear engines por rol: `AdminBrain`, `OwnerDemoBrain`, `CustomerSimBrain`.
- Crear tests de contrato por rol/canal.

### Fase 4 - Operacion y automejora

- AdminActionRouter para operar instancias desde chat.
- Conversation doctor para diagnostico en vivo.
- Replay harness con conversaciones reales.
- Quality dashboards para tasa de fallback, latencia, modelo y loops.

