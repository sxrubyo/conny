# ANALYSIS — Bublee Demo / Clínica de las Américas

Fecha: 2026-04-11

## 1. Estructura actual del proyecto

Árbol relevante encontrado en la instancia:

```text
bublee-instances/clinica-de-las-americas/
├── .env
├── instance.json
├── bublee.py
├── bublee_domino.py
├── knowledge_base.py
├── search.py
├── nova_bridge.py
├── brand_assets.py
├── bublee_core/
│   ├── __init__.py
│   ├── conversation_engine.py
│   └── persona_registry.py
├── v7/
│   ├── router.py
│   ├── orchestrator.py
│   ├── postprocess.py
│   ├── agents/
│   └── memory/
├── tests/
│   ├── test_patient_conversation_humanity.py
│   ├── test_demo_profile_matrix.py
│   └── test_domino_runtime.py
└── docs/
    └── superpowers/plans/2026-03-28-bublee-human-patient-dialogue.md
```

Hallazgos estructurales:

- `bublee.py` sigue siendo el runtime dominante y concentra identidad, demo, prompting, DB, aprendizaje, transporte y heurísticas.
- `bublee_core/conversation_engine.py` existe, pero solo cubre una parte del ruteo conversacional. No es todavía el cerebro principal.
- `bublee_domino.py` existe, pero no sustituye el flujo principal; opera como capa adicional.
- No existe `identity/`.
- No existe `skills/`.
- No existe `identity/skills/`.
- No existe `bublee_brain_v10.py` en esta instancia.

Conclusión estructural:

La instancia todavía no está en la arquitectura “identity as files + skills as markdown”. Sigue en transición, pero el comportamiento real todavía depende del monolito.

## 2. Cómo funciona el demo hoy

### 2.1 Punto de entrada

El demo se activa por:

- `DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"` en `bublee.py`.
- La sesión demo vive en `self._demo_sessions`.
- La ruta principal es `_handle_demo_message(...)`.

### 2.2 Flujo real detectado

En `_handle_demo_message(...)` el flujo actual es:

1. Gestiona TTL y reseteo de sesión demo.
2. Borra historial en DB si la sesión expiró.
3. Define claves de sesión:
   - nombre del negocio
   - contexto encontrado
   - URL
   - personalidad
   - tono detectado
   - modelo preferido
   - estado de aprendizaje
4. Define helpers internos `_save(...)` y `_send(...)`.
5. Intercepta palabras de reset (`reset`, `empezar de nuevo`, `otro negocio`, etc.).
6. Antes de la conversación larga, intenta `_try_conversation_core(...)`.
7. Si `conversation_core` maneja el turno, devuelve burbujas y sale.
8. Si no, entra al resto del flujo demo:
   - comandos ocultos (`/formal`, `/luxury`, `/stats`, `/menu`, etc.)
   - selección dinámica de modelo
   - helpers `_llm(...)` y `_llm_conv(...)`
   - heurísticas para nombre del negocio
   - búsqueda / contexto / detección de tono
   - conversación normal estilo “recepcionista”

### 2.3 Bugs y conflictos detectados en el demo

#### Bug A — El demo tiene demasiadas rutas que pueden responder

Hoy pueden tomar control del primer turno:

- `_handle_demo_message(...)`
- `_try_conversation_core(...)`
- `ConversationEngine.handle(...)`
- normalizadores tipo `v8_process_response(...)`
- filtros tipo `_normalize_first_contact_response(...)`
- posibles fallback de Domino

Esto explica respuestas inconsistentes: a veces parece demo, a veces clínica real, a veces bot genérico.

#### Bug B — El demo sigue mezclando comportamiento de clínica real

Aunque `conversation_engine.py` ya evita algunas salidas fijas en demo, `_handle_demo_message(...)` sigue construyendo:

- tono por sector
- comportamiento de recepción
- saludos y reinicios desde código
- menús, estadísticas, respuestas “bot mode”

Eso contamina el demo con comportamiento de producto antiguo.

#### Bug C — El primer turno todavía tiene bypass/normalización fuerte

En el prompt principal se detectó:

- `first_turn_block` se inyecta manualmente si `_is_first_turn`
- `_normalize_first_contact_response(...)` sigue procesando primer turno
- `conversation_engine.py` aún contiene `_build_first_turn(...)` y `_build_returning_greeting(...)`

Conclusión: el modelo no está decidiendo el primer turno de punta a punta. Todavía hay varias compuertas de código.

#### Bug D — El reset existe, pero no controla toda la identidad conversacional

El reset limpia:

- `_demo_sessions`
- historial en `conversations`

Pero no elimina toda posible contaminación porque:

- el `conversation_core` todavía puede entrar con reglas propias
- el prompt principal puede reinyectar tono o contexto heredado
- sigue habiendo lógica histórica del negocio en el monolito

#### Bug E — `bublee_brain_v10` no está integrado realmente en esta instancia

Hallazgo directo:

- en `bublee.py` solo existe:
  - `from bublee_brain_v10 import extract_short_memory, format_memory_block`
- no existe en esta instancia:
  - `bublee_brain_v10.py`
- tampoco existe integración visible de:
  - `init_brain()`
  - `patch_llm_first(generator)`

Resultado:

- esa importación cae silenciosamente al `except`
- no hay memoria corta v10 real
- no hay parche real del primer turno
- el bypass del primer turno sigue dependiendo del código anterior

## 3. Cómo se construye el system prompt hoy

### 3.1 Builders principales encontrados

Builders relevantes:

- `_build_compact_system_prompt(...)`
- `_build_system_prompt(...)`
- `v8_build_quality_system_prompt_addon(...)`
- `trainer_get_system_prompt_addon(...)`
- bloques `kb_block`, `web_block`, `core_mem_block`, `trust_block`, `playbook_block`

### 3.2 Estructura real del prompt

El prompt principal actual se arma en prosa larga, no como un solo archivo de identidad. Mezcla:

- nombre de Bublee
- nombre de clínica
- tagline
- contexto horario y ciudad
- datos de paciente
- memoria corta
- knowledge base
- web context
- core memory
- trust folder
- playbooks
- tono/arquetipo
- bloque de primer turno
- off-topic block
- sector layer
- strategy block
- custom block
- addon v8
- addon trainer

### 3.3 Problema conceptual

El prompt ya es “prosa”, pero no es todavía “identidad como archivos”.

Hoy la identidad sale de:

- datos embebidos en DB
- variables runtime
- bloques concatenados
- heurísticas del sector
- add-ons dinámicos

No sale de:

- `identity/SOUL.md`
- `identity/VOICE.md`
- `identity/BUSINESS.md`
- `identity/MEMORY.md`
- `identity/skills/*.md`

Eso significa que el prompt sigue siendo composición de sistema, no identidad administrable por archivos.

## 4. Qué existe hoy de sistema de aprendizaje

Se detectaron piezas reales de aprendizaje / adaptación:

- `PersonaEvolution`
- `trainer_gateway`
- `nova_rule_sync`
- rutas y referencias a `/feedback`

## Sesión 2026-04-11T09:57Z
- Fallos diagnosticados: 4
- Fallos resueltos: 3
- Fallos con rollback: 0
- Δ promedio: +1.0
- Casos de regresión pasados: 8/10
- Próximo ciclo: bajar el porcentaje de fallback en `enter-demo` y `clarify-demo` sin volver a meter frases rígidas

### Fallo diagnosticado 1
- Tipo: `T1` frase codificada
- Función: `_llm(...)` / `_llm_conv(...)` dentro de `_handle_demo_message(...)`
- Causa raíz: la ruta demo seguía usando `model_tier="fast"`, y el modelo devolvía borradores débiles que el guardrail rechazaba; eso reactivaba el fallback fijo.
- Parche aplicado: el helper demo ahora usa `reasoning` por defecto.
- Δ observado: `+1`

### Fallo diagnosticado 2
- Tipo: `T1` frase codificada
- Función: imports de `bublee_core` y `bublee_domino` en `bublee.py`
- Causa raíz: ambos imports dependían del `cwd`. En tests y cargas por `importlib`, `_DOMINO_AVAILABLE` podía quedar en `False` y `PersonaRegistry` en `None`, saltando a capas legacy.
- Parche aplicado: carga por ruta del archivo de la instancia cuando el import directo falla.
- Δ observado: `+2`

### Fallo diagnosticado 3
- Tipo: `T1` frase codificada
- Función: `_domino_response_is_bad(...)`
- Causa raíz: la validación rechazaba respuestas semánticamente buenas por no venir en exactamente 2-3 burbujas o por no contener literales como `te lo pongo simple`.
- Parche aplicado: el guardrail ahora valida mínimos semánticos por etapa y acepta respuestas válidas aunque no calquen una plantilla.
- Δ observado: `+1`

### Fallo diagnosticado 4
- Tipo: `T6` respuesta cortada / `T2` tono robótico
- Función: reintentos de `_send_domino(...)`
- Causa raíz: los retries seguían apilando el prompt grande completo; el modelo repetía borradores truncos y no reescribía de verdad.
- Parche aplicado: retries compactos, menos temperatura y reglas Domino menos rígidas en `bublee_domino.py`.
- Δ observado: `+1`

### Validación ejecutada
- `python3 -m pytest -q tests/test_domino_runtime.py tests/test_patient_conversation_humanity.py -k 'demo or brain_v10 or domino'`
- Resultado: `38 passed`
- `python3 -m py_compile bublee.py bublee_domino.py`
- Resultado: `OK`

### Runtime real
- `hola buenas` todavía cae seguido al fallback demo seguro.
- `y eso qué es?` ya no cae a identidad de clínica real, pero sigue saliendo más consultivo de lo deseado.
- `mi negocio se llama clínica de los molinos` ya activa bien el negocio y no arrastra branding viejo.
- `hola, cuánto vale el botox?` ya no se corta a media frase; ahora entrega una respuesta completa.
- `empezar de nuevo` resetea bien la sesión demo.
- referencias a `/aprender`
- tablas:
  - `feedback`
  - `conversation_feedback`
  - `learned_optimizations`
  - `self_improvement_log`
  - `core_memory`
  - `behavior_playbooks`
  - `trust_folder`

También hay modo de “aprendizaje manual” en demo:

- `blearn_key = sk + "_learn"`
- comentarios y flujo alrededor de “el dueño está contando su negocio”

Conclusión:

El aprendizaje no está ausente. Lo que falta es unificarlo en una arquitectura clara y estable. Hoy está repartido entre DB, trainer, Nova, playbooks y lógica demo.

## 5. DB schema actual relevante

Tablas detectadas en `bublee.py`:

- `clinic`
- `conversations`
- `appointments`
- `patients`
- `conversation_states`
- `contact_routes`
- `models`
- `system_config`
- `memories`
- `tasks`
- `mcp_plugins`
- `metrics`
- `learned_optimizations`
- `self_improvement_log`
- `feedback`
- `response_cache`
- `activation_tokens`
- `admins`
- `auth_sessions`
- `conversation_feedback`
- `trust_folder`
- `behavior_playbooks`
- `core_memory`

Conclusión:

La base ya soporta memoria, feedback, playbooks y núcleo de identidad aprendida. El problema no es falta de almacenamiento; es falta de una capa de compilación de identidad coherente.

## 6. Conflictos que pueden surgir con la nueva arquitectura

### Conflicto 1 — Doble autoridad conversacional

Si se añade `identity/` sin apagar rutas viejas, Bublee seguirá teniendo dos cerebros:

- el monolito
- la identidad por archivos

Eso produciría respuestas híbridas e incoherentes.

### Conflicto 2 — Demo vs clínica real

La instancia de la clínica hoy está haciendo dos papeles:

- atención real de clínica
- demo para dueños de negocio

Si no se separa bien el modo demo, seguirá filtrándose branding real o tono de recepción.

### Conflicto 3 — `conversation_core` todavía interviene demasiado pronto

Aunque hoy ya devuelve `False` en varios casos demo, sigue siendo una capa con reglas de primer turno, saludos, probes y follow-ups. Si no se redefine su rol, va a seguir compitiendo con el LLM.

### Conflicto 4 — `bublee_brain_v10` fantasma

El código ya intenta usar `bublee_brain_v10`, pero el archivo no existe en la instancia. Eso produce una falsa sensación de integración.

### Conflicto 5 — System prompt demasiado ensamblado

Mientras el prompt siga concatenando muchos bloques desde el monolito, será difícil garantizar una identidad consistente. El modelo puede sonar distinto por builder, no por identidad.

## 7. Estado real respecto a la visión del AGENTS.md

### Ya existe

- una capa `bublee_core`
- pruebas demo/humanity
- memoria en DB
- playbooks / trust / core memory
- lógica demo
- prompt largo en prosa

### No existe todavía

- `identity/`
- `identity/skills/`
- `SOUL.md`
- `VOICE.md`
- `BUSINESS.md`
- `MEMORY.md`
- `bublee_identity_engine.py`
- `bublee_skills_engine.py`
- `bublee_librarian.py`
- `bublee_training_pipeline.py`
- `bublee_demo_v2.py`

Conclusión:

La visión del `AGENTS.md` no está implementada aún. La instancia está en un estado intermedio con piezas buenas, pero dominada por el monolito.

## 8. Plan de implementación ajustado a lo encontrado

### Fase 1 — Corregir autoridad de identidad

1. Crear `identity/` y archivos base:
   - `SOUL.md`
   - `VOICE.md`
   - `BUSINESS.md`
   - `MEMORY.md`
2. Crear `identity/skills/`.
3. Añadir un loader explícito que compile identidad desde archivos.

Objetivo:

Que el modelo reciba identidad desde archivos, no desde saludos y plantillas hardcodeadas.

### Fase 2 — Desarmar el bypass del primer turno

1. Eliminar la autoridad de primer turno en:
   - `_build_first_turn(...)`
   - `_build_returning_greeting(...)`
   - `_normalize_first_contact_response(...)`
   - cualquier seeded first turn todavía activo
2. Dejar esas capas solo como guardrails o fallback de basura.

Objetivo:

Que el modelo decida el saludo y la explicación desde identidad + estado, no desde frases predefinidas.

### Fase 3 — Aislar el demo

1. Redefinir el demo como modo de venta para dueños de negocio.
2. En demo:
   - nunca usar nombre real de clínica como fallback
   - nunca comportarse como recepcionista de clínica real
   - siempre pedir el nombre del negocio con razón clara
   - usar memoria del negocio dado por el dueño

Objetivo:

Que el demo sea estable y no herede branding real.

### Fase 4 — Integrar `bublee_brain_v10` de verdad o retirarlo

Opciones:

- o se crea realmente `bublee_brain_v10.py` en la instancia y se integra completo
- o se elimina el import parcial actual

No debe quedar en estado fantasma.

### Fase 5 — Unificar aprendizaje

1. Dejar `/aprender` y `/feedback` apuntando a una sola tubería clara.
2. Promover aprendizajes a:
   - `VOICE.md`
   - `BUSINESS.md`
   - `MEMORY.md`
   - `identity/skills/*.md`

Objetivo:

Que el entrenamiento sea conversación → archivo de identidad → prompt, no conversación → parches dispersos.

## 9. Diagnóstico final

El problema principal no es que Bublee “no tenga IA suficiente”.

El problema real es de arquitectura:

- demasiadas rutas deciden cómo hablar
- el demo comparte ADN con la clínica real
- el primer turno todavía está demasiado controlado por código
- la identidad no vive aún en archivos versionables
- `bublee_brain_v10` está referenciado pero no existe en esta instancia

La siguiente implementación debe atacar primero la autoridad conversacional, no solo retocar frases.

## Sesión 2026-04-11 — business sync real

- Fallos diagnosticados: 3
- Fallos resueltos: 3
- Fallos con rollback: 0
- Δ promedio: +2
- Casos de regresión pasados: 10/10
- Próximo ciclo: bajar el tono todavía más y sacar del canal admin algunas frases demasiado ejecutivas, pero ya sin perder el contexto real del negocio.

### Fallo T3/T4/T6 — identidad oficial no llegaba al runtime admin

- Evidencia:
  - La DB ya tenía `clinic.name = Nova`, `sector = otro` y `knowledge_base_raw` oficial.
  - `/health` seguía reportando `sector = estetica`.
  - El dueño preguntaba `De que trata nova?` y Bublee contestaba desde branding heredado o caía en `Cuénteme qué quiere ajustar.`
- Causa raíz:
  - El sync escribía DB + `instance.json` + `identity/`/`memory/`/`soul/`, pero el canal admin seguía usando `Config` vieja y fallbacks que no leían la verdad operativa vigente.
  - Además, `_admin_llm_brain(...)` podía caerse a fallback por JSON truncado del proveedor.
- Parche aplicado:
  - Se añadió un lector de contexto operativo efectivo desde DB + `IDENTITY.md` en [bublee.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee.py#L3337).
  - El sync ya promueve el contexto cargado a DB, `instance.json`, `identity/`, `memory/`, `soul/` y espejo `.openclaw` en [bublee.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee.py#L3765).
  - El handler admin ahora intercepta preguntas sobre negocio/archivo/PDF/memoria y responde desde el contexto oficial sin depender del LLM en [bublee.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee.py#L18015).
  - El fallback admin ahora sabe explicar qué aprendió, por qué pidió el archivo y dónde escribe memoria en [bublee.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee.py#L18478).
  - El parser del admin brain recupera `reply` aun con JSON truncado en [bublee.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee.py#L18262).
  - `/health` ahora prioriza `clinic.sector` sobre `Config.SECTOR` en [bublee.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee.py#L20572).

### Verificación fresca

- Tests:
  - `pytest -q /home/ubuntu/bublee-instances/clinica-de-las-americas/tests/test_patient_conversation_humanity.py -k 'workspace_context_block or uploaded_business_context_sync or admin_local_fallback or admin_llm_brain_recovers_reply or health_prefers_clinic_sector or admin_natural_command_bypasses_llm_for_synced_business_context'`
  - Resultado: `10 passed`
- Sintaxis:
  - `python3 -m py_compile /home/ubuntu/bublee-instances/clinica-de-las-americas/bublee.py`
- Runtime:
  - `GET http://127.0.0.1:8003/health` -> `clinic=Nova`, `sector=otro`
  - `POST /test` con `De que trata nova?` -> responde desde `Nova`, ya no desde Botox/Rellenos
  - `POST /test` con `Te acabo de mandar un txt...` -> explica que el archivo reemplazó branding heredado
  - `POST /test` con `puedes leer pdfs y guardar memoria?` -> confirma lectura de PDF/TXT/DOCX/MD/JSON y escritura en `identity/`, `memory/` y `soul/`

## Sesión 2026-04-11 — override conversacional + scaffold v10

- Fallos diagnosticados: 2
- Fallos resueltos: 2
- Fallos con rollback: 0
- Δ promedio: +2
- Casos de regresión pasados: 5/5
- Próximo ciclo: mover la lógica de onboarding conversacional desde `bublee.py` a `bublee_core/context.py` sin cambiar el comportamiento binario ya validado.

### Fallo T3/T4 — el negocio dicho en conversación no tenía autoridad real

- Evidencia:
  - El dueño podía decir `Ya dejé Nova como negocio activo...` y Bublee seguía operando desde defaults heredados.
  - La instancia contestaba desde `.env` o desde el sync oficial, pero no existía una capa de prioridad por chat.
  - En runtime, el caso real debía devolver una pregunta útil; antes devolvía confirmaciones o contexto heredado.
- Causa raíz:
  - `_effective_business_runtime_context(...)` solo leía DB + archivos oficiales.
  - El canal admin no tenía estado de override conversacional persistido por `chat_id`.
  - El onboarding no existía como estado: solo había sync oficial por archivo y ramas demo separadas.
- Parche aplicado:
  - Se añadieron helpers de estado seguro + override conversacional por chat en [bublee.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee.py#L3363).
  - El contexto efectivo del chat ahora puede priorizar `business_override` conversacional sobre runtime oficial en [bublee.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee.py#L3390).
  - Se creó detección de negocio explícito + inferencia de huecos de onboarding en [bublee.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee.py#L3415) y [bublee.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee.py#L3455).
  - El admin ahora intercepta contexto nuevo y hace una sola pregunta útil en vez de llamar al brain general en [bublee.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee.py#L17903) y [bublee.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee.py#L18067).
  - `_admin_llm_brain(...)` y `_admin_local_fallback(...)` ahora leen el contexto efectivo del chat en vez del runtime plano en [bublee.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee.py#L18205) y [bublee.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee.py#L18573).

### Verificación fresca

- Tests:
  - `pytest -q /home/ubuntu/bublee-instances/clinica-de-las-americas/tests/test_patient_conversation_humanity.py -k 'conversational_business_override or synced_business_context or pdf_and_memory_capability or health_prefers_clinic_sector or admin_natural_command_bypasses_llm_for_synced_business_context'`
  - Resultado: `5 passed`
- Sintaxis:
  - `python3 -m py_compile /home/ubuntu/bublee-instances/clinica-de-las-americas/bublee.py`
- Runtime:
  - `POST /test` con `Ya dejé Nova como negocio activo. Nova es una plataforma de gobernanza de intención para agentes de IA en bancos.` y `user_id=6908159885`
  - Resultado: `¿A qué tipo de cliente le vendes primero?`

### Scaffold v10 dejado listo

- `.gitignore` local creado en [/.gitignore](/home/ubuntu/bublee-instances/clinica-de-las-americas/.gitignore)
- `.env.example` sin secretos creado en [/.env.example](/home/ubuntu/bublee-instances/clinica-de-las-americas/.env.example)
- arquitectura documentada en [architecture.md](/home/ubuntu/bublee-instances/clinica-de-las-americas/docs/architecture.md)
- módulos placeholder creados:
  - [conversation.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee_core/conversation.py)
  - [identity.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee_core/identity.py)
  - [memory.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee_core/memory.py)
  - [context.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee_core/context.py)
  - [captacion.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee_agents/captacion.py)
  - [objeciones.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee_agents/objeciones.py)
  - [agenda.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee_agents/agenda.py)
  - [conocimiento.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee_agents/conocimiento.py)
  - [seguimiento.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee_agents/seguimiento.py)
  - [escalacion.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee_agents/escalacion.py)
  - [demo_mode.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee_skills/demo_mode.py)
  - [tone_detection.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee_skills/tone_detection.py)
  - [text_processing.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee_skills/text_processing.py)
  - [whatsapp.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee_integrations/whatsapp.py)
  - [llm.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee_integrations/llm.py)

## Sesión 2026-04-11 — demo onboarding sin branding heredado

- Fallos diagnosticados: 3
- Fallos resueltos: 2
- Fallos con rollback: 0
- Δ promedio: +1
- Casos de regresión pasados: 10/10
- Próximo ciclo: bajar el tono todavía seco del onboarding demo sin volver a meter frases rígidas, y resumir mejor el contexto admin sin reciclar `raw_context`.

### Conversación de diagnóstico — 2026-04-11 19:00 UTC

### Instancia: clinica-de-las-americas
### Endpoint: http://127.0.0.1:8003/test

| Turno | Input | Output (primeras 20 palabras) | Fallo | Tipo |
|-------|-------|-------------------------------|-------|------|
| 1 | hola | Hola, soy Bublee de Nova... | SÍ | T1/T4 |
| 2 | buenas, me pueden ayudar... | antes de mostrarte cómo funciono... | SÍ | T1/T2 |
| 3 | cuánto vale el botox | nuestro botox cuesta... | SÍ | T4 |
| 8 | y ustedes en qué zona están | Hola, Bublee por acá, del equipo de el negocio... | SÍ | T1/T4 |
| owner-3 | qué sabes de Nova hasta ahora | seguía preguntando ticket | SÍ | T3 |

### Primer fallo detectado: Turno 1 — Tipo T1/T4
### Hipótesis: el flujo real estaba entrando por `_handle_demo_message(...)`, no por `process_message(...)` de paciente, y esa ruta demo tenía bypasses duros antes del LLM.

### Fallo T1/T4 — demo abría con identidad heredada y operaba sin negocio cargado

- Evidencia:
  - `DEMO_MODE=true` enviaba todo no-admin a [bublee.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee.py#L14193).
  - El primer turno salía con `Hola, soy Bublee de Nova`.
  - Sin nombre de negocio, el demo igual contestaba Botox/precio/zona o caía en `del equipo de el negocio`.
- Causa raíz:
  - `_handle_demo_message(...)` tenía aperturas hardcodeadas y un `_send(...)` que reescribía el primer turno con `_normalize_first_contact_response(...)`.
  - El demo dejaba pasar `conversation_core` y la capa de recepcionista normal antes de tener `business_name`.
  - El onboarding aceptaba salidas largas o corporativas del modelo sin validación estructural fuerte.
- Parche aplicado:
  - Se eliminó la reescritura rígida del primer turno demo en [bublee.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee.py#L14745) y [bublee.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee.py#L14963).
  - El demo ya no entra a `conversation_core` mientras falte `business_name` en [bublee.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee.py#L14803).
  - Se añadió onboarding demo guiado por LLM con retry y validador estructural en [bublee.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee.py#L14972).
  - Las ramas de apertura, aclaración de nombre e identidad ahora pasan por ese onboarding en [bublee.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee.py#L15041), [bublee.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee.py#L15116) y [bublee.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee.py#L15445).

### Fallo T3 — admin no resumía lo aprendido sobre Nova

- Evidencia:
  - Después de ICP correcto, `¿qué sabes de Nova hasta ahora?` seguía disparando la siguiente pregunta de onboarding.
- Causa raíz:
  - `_admin_maybe_handle_business_onboarding(...)` trataba la petición de resumen como si siguiera en el loop de huecos.
- Parche aplicado:
  - Se añadió resumen explícito del override conversacional en [bublee.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee.py#L3651).
  - La rama admin ahora detecta `qué sabes / qué aprendiste / resúmeme` y devuelve estado conocido + huecos pendientes en [bublee.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee.py#L18240).

### Verificación fresca

- Tests:
  - `pytest -q /home/ubuntu/bublee-instances/clinica-de-las-americas/tests/test_patient_conversation_humanity.py -k 'demo_first_turn_explains_function_and_why_it_needs_business_name or demo_first_turn_does_not_inject_runtime_clinic_name_into_onboarding or demo_onboarding_rejects_corporate_name_request or demo_without_business_name_never_falls_back_to_el_negocio_identity or demo_confusion_reply_does_not_fall_back_to_real_clinic_identity or admin_business_onboarding_can_summarize_learned_context_instead_of_reasking'`
  - Resultado: `6 passed`
- Sintaxis:
  - `python3 -m py_compile /home/ubuntu/bublee-instances/clinica-de-las-americas/bublee.py`
- Runtime:
  - Paciente demo ya no menciona `Clínica Las Américas`, `Nova` ni `el negocio` como identidad falsa.
  - Paciente demo ya no inventa Botox/precios/ubicación mientras falte el nombre del negocio.
  - Admin `¿qué sabes de Nova hasta ahora?` ya devuelve resumen en vez de volver a preguntar ticket.

### Estado real al cierre del ciclo

- Mejora conseguida:
  - se quitó la identidad heredada y la demo dejó de operar desde un negocio falso
  - el admin ya resume contexto nuevo
- Pendiente:
  - el onboarding demo todavía suena demasiado seco y repetitivo
  - varios turnos siguen cayendo al fallback mínimo porque Gemini no está resolviendo el tono con suficiente naturalidad en esta rama

## Sesión 2026-04-18 — demo menos repetitivo y onboarding dueño corregido

- Fallos diagnosticados: 3
- Fallos resueltos: 2
- Fallos con rollback: 0
- Δ promedio: +1
- Casos de regresión pasados: 7/7 focales, 14/14 domino
- Próximo ciclo: bajar el tono todavía consultivo de `enter-demo/clarify-demo` sin depender tanto del fallback contextual.

### Conversación de diagnóstico — 2026-04-18 16:40 UTC

### Instancia: clinica-de-las-americas
### Endpoint: http://127.0.0.1:8003/test

| Turno | Input | Output (primeras 20 palabras) | Fallo | Tipo |
|-------|-------|-------------------------------|-------|------|
| 1 | hola | arranquemos por el nombre de tu negocio | SÍ | T1/T2 |
| 2 | buenas, me pueden ayudar con algo? | arranquemos por el nombre de tu negocio | SÍ | T1/T2 |
| 3 | cuánto vale el botox? | arranquemos por el nombre de tu negocio | SÍ | T1/T2 |
| 4 | está muy caro, en otro lado... | lo que hago aquí es atender tus consultas... | SÍ | T2 |
| owner-2 | Le vendemos primero a bancos... | cuál es el proceso para tramitar un ticket... | SÍ | T3 |

### Primer fallo detectado: Turno 1 — Tipo T1/T2
### Hipótesis: el demo seguía cayendo a un fallback fijo porque `auto` estaba desviado a una mini-cascada local fuera de `llm_engine`, y el prompt de Domino seguía dejando pasar salidas consultivas o fragmentadas.

### Fallo T1/T2 — demo repetía el mismo fallback o sonaba a consultora

- Evidencia:
  - `hola`, `buenas`, `cuánto vale el botox`, `y eso qué es` y `y ustedes en qué zona están` devolvían prácticamente la misma línea.
  - En logs, `attempt=1/2/3` devolvía cosas como `aquí lo que hago es...`, `mi función es...`, `de manera efectiva...`.
- Causa raíz:
  - `auto` en [bublee.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee.py) se convertía a `gemini` manual si había keys, en vez de usar `llm_engine`.
  - Eso saltaba blocklist temporal, cascada completa y dobles de test.
  - La capa Domino en [bublee_domino.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee_domino.py) todavía permitía tonos de consultora y estructura demasiado abierta para `enter-demo` y `clarify-demo`.
  - Cuando el modelo seguía flojo, el último recurso era una sola frase fija.
- Parche aplicado:
  - `auto` ahora usa el motor global real en [bublee.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee.py).
  - Se endureció la detección de tono consultivo en [bublee_domino.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee_domino.py).
  - Se apretaron las reglas de `enter-demo` y `clarify-demo` en [bublee_domino.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee_domino.py).
  - Se reemplazó el fallback único por un fallback contextual mínimo según el turno en [bublee.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee.py).

### Fallo T3 — onboarding dueño confundía `ticket` con soporte

- Evidencia:
  - Después de `Le vendemos primero a bancos medianos y fintechs...`, la siguiente pregunta fue sobre `ticket de soporte`.
- Causa raíz:
  - `_demo_question_matches_gap(...)` aceptaba `ticket` como cualquier match semántico, aunque fuera soporte y no precio de entrada.
- Parche aplicado:
  - Se endureció el matching del gap `ticket` en [bublee.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee.py) para exigir señales de precio/entrada y rechazar soporte/incidencias.

### Verificación fresca

- Tests focales:
  - `pytest -q /home/ubuntu/bublee-instances/clinica-de-las-americas/tests/test_patient_conversation_humanity.py -k 'looks_fragmented_reply_flags_short_dangling_fragments or demo_business_override_first_turn_skips_runtime_intro_normalizer or demo_without_business_name_keeps_onboarding_even_after_multiple_turns or demo_domino_uses_reasoning_tier_for_opening_stage or demo_runtime_routes_through_domino_before_legacy_demo_layers or demo_enter_demo_uses_structural_repair_before_fixed_fallback or demo_enter_demo_rejects_single_bubble_structural_reply_without_name_request'`
  - Resultado: `7 passed`
- Tests domino:
  - `pytest -q /home/ubuntu/bublee-instances/clinica-de-las-americas/tests/test_domino_runtime.py`
  - Resultado: `14 passed`
- Sintaxis:
  - `python3 -m py_compile /home/ubuntu/bublee-instances/clinica-de-las-americas/bublee.py /home/ubuntu/bublee-instances/clinica-de-las-americas/bublee_domino.py`
- Runtime:
  - `hola` -> `estoy dentro del chat de tu negocio ||| cómo se llama?`
  - `cuánto vale el botox?` -> `sin el nombre de tu negocio te hablaría genérico ||| dímelo y sigo desde ahí`
  - `siguen ahí?` -> `sí, aquí sigo ||| cómo se llama tu negocio?`
  - `a qué te refieres? no te entiendo` -> ya no repite la misma línea del saludo; pide el nombre desde un fallback contextual.
  - Owner flow `Nova`:
    - primera pregunta: `a qué tipo de cliente le vendes primero`
    - segunda pregunta: `cuál es el ticket promedio o la entrada más común`
    - resumen: correcto

### Estado real al cierre del ciclo

- Mejora conseguida:
  - el demo dejó de responder todo con exactamente la misma frase
  - el onboarding del dueño dejó de desviarse a `ticket de soporte`
  - el motor demo volvió a usar la cascada real y recuperó cobertura de tests
- Pendiente:
  - la voz demo todavía no es indistinguiblemente humana; cuando falla el LLM, el fallback sigue siendo correcto pero todavía demasiado funcional

## Sesión 2026-04-18 — objeciones tempranas antes del nombre del negocio

- Fallos diagnosticados: 2
- Fallos resueltos: 2
- Fallos con rollback: 0
- Δ promedio: +1
- Casos de regresión pasados: 9/9 focales
- Próximo ciclo: hacer que la primera apertura sin negocio suene menos “estructura de sistema” y más persona real sin volver a respuestas rígidas.

### Conversación de diagnóstico — 2026-04-18 16:48 UTC

### Instancia: clinica-de-las-americas
### Endpoint: http://127.0.0.1:8003/test

| Turno | Input | Output (primeras 20 palabras) | Fallo | Tipo |
|-------|-------|-------------------------------|-------|------|
| 1 | solo estoy comparando | estoy dentro del chat de tu negocio... | SÍ | T2 |
| 2 | me da miedo que suenes a bot | estoy dentro del chat de tu negocio... | SÍ | T2 |

### Primer fallo detectado: Turno 1 — Tipo T2
### Hipótesis: el demo sin negocio seguía cayendo al fallback genérico de apertura, sin distinguir objeciones tempranas del dueño.

### Fallo T2 — objeciones tempranas ignoradas

- Evidencia:
  - `solo estoy comparando` devolvía la misma respuesta que un saludo.
  - `me da miedo que suenes a bot` devolvía la misma respuesta que un saludo.
- Causa raíz:
  - `_demo_identity_fallback(...)` en [bublee.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee.py) no tenía ramas específicas para estas objeciones y caía directo en `mode == opening`.
- Parche aplicado:
  - Se añadieron ramas específicas para `comparando` y `miedo a sonar bot` en [bublee.py](/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee.py).
  - El fallback ahora responde primero a la objeción y después pide el nombre del negocio.

### Verificación fresca

- Tests:
  - `pytest -q /home/ubuntu/bublee-instances/clinica-de-las-americas/tests/test_patient_conversation_humanity.py -k 'demo_opening_handles_comparing_objection_before_asking_business_name or demo_opening_handles_bot_fear_before_asking_business_name'`
  - Resultado: `2 passed`
- Regresión focal ampliada:
  - `pytest -q /home/ubuntu/bublee-instances/clinica-de-las-americas/tests/test_patient_conversation_humanity.py -k 'looks_fragmented_reply_flags_short_dangling_fragments or demo_business_override_first_turn_skips_runtime_intro_normalizer or demo_without_business_name_keeps_onboarding_even_after_multiple_turns or demo_domino_uses_reasoning_tier_for_opening_stage or demo_runtime_routes_through_domino_before_legacy_demo_layers or demo_enter_demo_uses_structural_repair_before_fixed_fallback or demo_enter_demo_rejects_single_bubble_structural_reply_without_name_request or demo_opening_handles_comparing_objection_before_asking_business_name or demo_opening_handles_bot_fear_before_asking_business_name'`
  - Resultado: `9 passed`
- Runtime:
  - `solo estoy comparando` -> `todo bien, comparar tiene sentido ||| con el nombre de tu negocio te muestro cómo respondería de verdad ||| cómo se llama?`
  - `me da miedo que suenes a bot` -> `si suena a bot, no sirve ||| con el nombre de tu negocio sí te lo aterrizo a tu chat real ||| cómo se llama?`
