# Changelog

## 9.8.4 - 2026-06-02

- made bare `bublee` route to the modern onboarding/chat surface instead of the legacy help screen
- kept `bublee init` untouched while preserving the same banner and branding in the post-onboarding chat UI
- aligned the legacy Python CLI fallback so direct `bublee_cli.py` launches follow the same start behavior

## 9.8.3 - 2026-06-02

- made `bublee` open the real chat interface after onboarding instead of the setup flow
- kept `bublee init` unchanged and preserved its banner/design exactly
- added slash-command chat shortcuts with a Codex-style launcher header

## 9.8.2 - 2026-06-02

- persisted the language selected in `bublee init` so the rest of the CLI loads it automatically
- made `bublee_i18n` read the saved workspace language on startup
- kept the `bublee init` banner unchanged while aligning other launch paths to the same brand

## 9.8.1 - 2026-06-02

- made `bublee` open the guided setup flow by default instead of the old help banner
- removed the default launcher banner from the primary `bublee` path
- aligned the TUI version display with `package.json`

## 9.8.0 - 2026-06-02

- blocked first-contact setup for unknown chats until a valid activation token is provided
- added `bublee token --admin` with `ADMN-` Bublee Pro Admin tokens, offline SQLite generation and web/API developer access
- fixed token casing and case-insensitive token lookup so generated tokens validate reliably
- made `/api/activate`, web registration and developer registration accept Bublee Pro Admin tokens safely
- added admin Soul memory folders under `soul/admins/<chat_id>` for persistent operator context and learned business/ops facts
- introduced typed LLM service errors so quota/API-key failures are shown to admins before any fallback
- changed admin fallback into an explicit opt-in flow via `continuar fallback`
- cleaned npm packaging to exclude patch/fix scripts and private per-business brand asset folders
- fixed first contact greeting regression (`Holaal`) and restored admin capability fallback for audios, PDFs and documents

## 9.7.6 - 2026-05-26

- fixed demo LLM resolution through the Bublee facade so tests and runtime use the configured engine instead of a stale runtime module
- removed the fake “internet dropped” demo fallback and replaced it with contextual owner onboarding when every model response is empty or unusable
- preserved continuity in owner demo flows so Bublee does not repeat “soy una IA” after capability context was already explained
- verified Python, Node/npm and shell entrypoints for Linux/macOS/PowerShell-compatible npm usage

## 9.7.5 - 2026-05-26

- unified `bublee init`, `bublee config` and `bublee doctor` around the active instance `.env`
- mirrored provisioned instance secrets and URLs into the base runtime `.env` after setup and config edits
- replaced brittle `.env` text replacement with parser-based updates that handle quoted, unquoted and `pending` values
- added dashboard exposure setup to `bublee init` for localhost, LAN/IP and custom public URLs

## 9.7.4 - 2026-05-26

- fixed existing installs with a stale/incomplete Python runtime by making bootstrap health check required imports before every command
- added `bublee --bootstrap-check` and wired the shell installer to run it before reporting success
- ensured missing `rich`/CLI dependencies are repaired during install instead of surfacing later at `bublee init`

## 9.7.3 - 2026-05-26

- fixed Termux/proot installs where `bublee init` could start without `rich` installed
- made the npm bootstrap install critical CLI dependencies first and fail loudly if they are missing
- kept heavy production dependencies best-effort so packages like `scikit-learn` cannot leave the CLI half-installed
- expanded runtime health checks to include `rich`, `deep_translator`, `questionary`, `fastapi`, `httpx`, `dotenv` and `pydantic`

## 9.7.2 - 2026-05-26

- removed the obsolete boxed `BUBLEE ULTRA CONFIG v9.7.0` layout from `bublee config`
- added a Gateway/Webhook step to `bublee init` with automatic `localhost.run` tunneling or manual `BASE_URL`
- fixed tunnel routing to target the active instance `PORT` instead of stale defaults like `8002`
- made webhook sync reload the real `.env` and restart PM2 with `--update-env` before calling Telegram `setWebhook`
- unified the default instances path under `~/.bublee/instances`

## 9.7.1 - 2026-05-26

- fixed GitHub/npm bootstrap for fresh installs where `bublee init` still tried to run from `/home/ubuntu/bublee`
- removed the hardcoded working directory in `bublee_app.py`; subcommands now run from the installed `BUBLEE_DIR`
- bumped the package version so existing `~/.bublee/repo` installs resync automatically on reinstall
- kept the public package name as `bublee-ai` for GitHub installs and npm compatibility

## 9.7.0 - 2026-05-26

- corregido el arranque PM2 para usar `run.sh` y selección dinámica de Python, evitando `--interpreter python3` duro y rutas rotas de venv
- añadido `bublee_runtime_ops.py` como capa compartida de inspección para puertos, PM2, túneles, Python y webhook
- rehecho `bublee config` como panel interactivo real de red, modelos, gateway, entorno y doctor
- convertido `bublee_doctor.py` en motor de self-healing con resincronización de webhook, reinstalación de dependencias y re-registro de PM2
- endurecido `npm/bublee.js` para aceptar Python 3.9+ real, detectar runtime corrupto y recrearlo automáticamente
- corregido `install.sh` para dejar de depender de una rama fija vieja y validar mejor el bootstrap
- añadida sincronización de `run.sh`, `bublee_doctor.py`, `bublee_runtime_ops.py` y `bublee_ultra_config.py` a las instancias
- alineado `bublee_app.py` para que `config` y `doctor` usen las superficies reales en lugar de mocks

## 9.6.1 - 2026-05-20

- Refactorización de arquitectura hacia un diseño DDD (Domain-Driven Design) modular
- Extracción del orquestador central (BubleeOrchestrator) hacia `src/core/orchestrator.py`
- Extracción del clasificador de nombres y flujos de onboarding hacia `src/domain/onboarding_flow.py`
- Migración de dependencias, scripts de guardias, admin api y prospect pitch a la jerarquía de `/src`
- Actualización de manifiestos y limpieza de archivos de bootstrapping obsoletos

## 9.6.0 - 2026-05-19

- corregido el flujo demo-owner para que frases mixtas como `Ah vale. El nombre de mi negocio se llama...` entren al bind real del negocio y no caigan otra vez en onboarding o en modo paciente
- eliminado el escape que permitía rescatar respuestas inválidas del LLM en el quality chain del demo
- sincronizado el `business_name` del send guard en la ruta real de `_send`, evitando rescates genéricos como `Hola! Soy Bublee` o pedidos repetidos del nombre del negocio
- endurecido el clasificador demo para no tomar `mi nombre es...` como nombre de negocio ni usar señales demasiado genéricas como `vale` o `tengo` para saltar al flujo de cliente
- ajustado el send guard para no marcar respuestas de memoria directas como `Te llamas Santiago` como si estuvieran cortadas
- añadidas regresiones para bind con prefijo conversacional, rescate de fragmentos severos y memoria corta del nombre del dueño

## 8.2.0 - 2026-05-11

- añadido soporte multilenguaje real en el runtime público y liberado en npm
- reforzada la regla de idioma en demo y binding para que Bublee espeje el idioma del dueño aunque no esté en la tabla de locales
- corregido el empaquetado npm para incluir `bublee_i18n.py`, que antes quedaba fuera del tarball

## 8.1.1 - 2026-05-10

- corregido el flujo demo-owner en inglés para no tomar frases como `Just English sorry` o `I don't talk Spanish` como nombre de negocio
- endurecida la detección de idioma para mantener el inglés durante confirmaciones, correcciones y preguntas meta del dueño
- localizado el binding del negocio, confirmaciones de URL, correcciones y resets para que respeten el idioma activo del dueño
- afinados los heurísticos de nombre de negocio para distinguir mejor entre lenguaje/meta y nombres reales
- añadidas pruebas para onboarding demo en inglés, corrección de match equivocado y preservación del idioma en sesión

## 8.1.0 - 2026-05-09

- corrigido el filtro de frases robóticas para que deje de truncar salidas válidas del LLM
- invertida la prioridad de respuesta en demo/chat: el LLM decide primero y los fallbacks quedan como último recurso real
- endurecido el flujo demo para no rebinder confirmaciones como si fueran nuevos negocios y para mantener modo owner/admin sin secuestros
- productizado `smart_handoff.py` con persistencia completa de contexto, ack inmediato, timeout de 10 minutos y reanudación limpia
- añadido `bublee_bridge.py` con memoria SQLite, `/history`, `/clear`, `/export` y prueba automatizada de continuidad
- añadido modo `bublee_cli.py --non-interactive` para validación scripted del runtime
- reducidos `bare except` en `bublee.py` y cubiertos con pruebas nuevas de bridge, handoff y filtros
- incluido el nuevo runtime auxiliar en el paquete npm
