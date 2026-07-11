# Bublee Agent Memory

Fecha: 2026-06-24

## Problema Investigado

Habia mezcla entre agentes de Telegram:

- `ovni` y `melissa-x` compartian el mismo bot de Telegram.
- Produccion tenia token propio, pero Telegram no tenia webhook configurado.
- La base `bublee` tenia un tercer bot activo no incluido en el esquema pedido.
- Varias rutas y bases de datos seguian usando nombres `conny`, lo que hace dificil distinguir produccion, demo, cliente/admin y Ovni.

## Estado Operativo Corregido

| Rol | Proceso PM2 | Carpeta | Puerto | Telegram |
| --- | --- | --- | --- | --- |
| Base/admin local | `bublee` | `/home/ubuntu/bublee` | `8001` | desactivado en `.env` |
| Produccion cliente/admin | `bublee-clinica-de-las-americas` | `/home/ubuntu/bublee-instances/clinica-de-las-americas` | `8003` | token produccion |
| Demo aislada / cuarentena | `bublee-melissa-x` | `/home/ubuntu/bublee-instances/melissa-x` | `8006` | desactivado en `.env` |
| Ovni controlador | `bublee-ovni` | `/home/ubuntu/bublee-instances/ovni` | `8008` | token Ovni |

## Hallazgos Raiz

1. `melissa-x` tenia el mismo `TELEGRAM_TOKEN` que `ovni`. En cualquier restart podia robar el webhook de Ovni.
2. Produccion usaba `BASE_URL=http://3.130.46.55:8003`; Telegram rechazo el webhook con `400 Bad Request` porque no era HTTPS.
3. `shared_telegram_routes.json` en el repo tenia default a `clinica-de-las-americas`, pero sin rutas explicitas. Esto es peligroso si se activa el router compartido.
4. `clinica-de-las-americas` apuntaba `DB_PATH` y `VECTOR_DB_PATH` a `/home/ubuntu/conny-instances/...`.
5. La frase `Ingresa tu Token de Activacion para comenzar.` sale cuando `setup_done=false`. `melissa-x` estaba sin setup y con token Ovni, por eso podia aparecer en el bot equivocado.

## Cambios Aplicados

- `/home/ubuntu/bublee/.env`: Telegram desactivado para evitar tercer bot activo.
- `/home/ubuntu/bublee-instances/clinica-de-las-americas/.env`: `BASE_URL` HTTPS, `INSTANCE_ID=production`, DB local en `bublee-instances`.
- `/home/ubuntu/bublee-instances/ovni/.env`: DB local en `bublee-instances`, shared router desactivado.
- `/home/ubuntu/bublee-instances/melissa-x/.env`: token Telegram eliminado y `PLATFORM=disabled`.
- `/home/ubuntu/bublee/shared_telegram_routes.json`: default vacio para evitar fallback silencioso.

## Reglas Actuales

- Ovni solo debe operar con el bot cuyo ID empieza por `8749260201`.
- Produccion solo debe operar con el bot cuyo ID empieza por `8779529912`.
- Ninguna instancia demo o base debe tener el token de Ovni.
- Ninguna instancia demo o base debe registrar webhook si no tiene un rol explicito.

## Pasada 2: Limpieza De Webhooks Y Dominio Publico

Fecha: 2026-06-24

### Cambios Aplicados

- Produccion registra Telegram en `https://bublee.nexusys.duckdns.org/webhook/bublee_production_2ed44661cb56cd55`.
- Ovni registra Telegram en `https://aibublee.duckdns.org/webhook/bublee_ovni_019d2bbd1d0b135b`.
- `melissa-x` queda desactivada, sin token, con `BASE_URL=https://aibublee.duckdns.org` y `WEBHOOK_SECRET=bublee_melissa-x_019d2bbd1d0b135b`.
- Caddy efectivo (`/etc/caddy/Caddyfile`) y copia de trabajo (`/home/ubuntu/Caddyfile`) ya no tienen rutas `conny_` ni alias `connyai`.
- La base legacy `/home/ubuntu/bublee-instances/melissa-x/conny.db` se movio a `legacy/2026-06-24-conny-db-quarantine/` con manifiesto. El runtime usa `bublee.db`.
- `scripts/audit_agents.py` ahora falla si vuelve un `WEBHOOK_SECRET` legacy, un `DB_PATH` legacy o `conny_`/`connyai` en Caddy.

### Verificacion

- `python3 /home/ubuntu/bublee/scripts/audit_agents.py`: OK.
- `python3 /home/ubuntu/bublee/scripts/audit_runtime_cleanliness.py`: OK.
- `python3 -m compileall /home/ubuntu/bublee/scripts/audit_agents.py /home/ubuntu/bublee/scripts/audit_runtime_cleanliness.py`: OK.
- Caddy valido con `/etc/caddy/Caddyfile` y servicio reiniciado.
- PM2 online para `bublee-clinica-de-las-americas`, `bublee-ovni` y `bublee-melissa-x`.
- Telegram status: produccion y Ovni `ok=true`, `pending_update_count=0`; `melissa-x` `enabled=false`.

## Pasada 3: Registry De Instancias

Fecha: 2026-06-24

### Cambios Aplicados

- Se creo `/home/ubuntu/bublee/instances.registry.json` como mapa unico de roles activos.
- El registry define `role`, `process_name`, `.env`, puerto esperado, bot ID esperado, prefijo de webhook y restricciones de dominio por instancia.
- `scripts/audit_agents.py` ya no guarda el mapa de instancias hardcodeado; carga el registry y valida contra ese archivo.

### Roles En Registry

- `base`: admin local sin token Telegram.
- `production`: cliente/admin productivo, bot ID `8779529912`, puerto `8003`.
- `melissa-x`: demo/cuarentena, sin token, puerto `8006`.
- `ovni`: controlador, bot ID `8749260201`, puerto `8008`.

### Mapas Por Carpeta

- `/home/ubuntu/bublee/ROLE.md`
- `/home/ubuntu/bublee-instances/clinica-de-las-americas/ROLE.md`
- `/home/ubuntu/bublee-instances/ovni/ROLE.md`
- `/home/ubuntu/bublee-instances/melissa-x/ROLE.md`

`scripts/audit_agents.py` valida que cada `ROLE.md` exista y declare el `ID registry` y `Rol` correctos.

## Pasada 4: Guard Operacional PM2

Fecha: 2026-06-24

### Cambios Aplicados

- Se creo `/home/ubuntu/bublee/scripts/preflight_agents.sh`.
- Se creo `/home/ubuntu/bublee/docs/operations/PM2_RESTART_GUARD.md`.
- `/home/ubuntu/bublee/ecosystem.config.js` ahora incluye tambien `bublee-melissa-x`, alineado con PM2 real.

### Verificacion

- `/home/ubuntu/bublee/scripts/preflight_agents.sh`: OK.
- `node --check /home/ubuntu/bublee/ecosystem.config.js`: OK.

## Pasada 5: Archivo Legacy De Parches

Fecha: 2026-06-24

### Cambios Aplicados

- Se creo `/home/ubuntu/bublee/legacy/2026-06-24-one-off-patches/`.
- Se movieron fuera de la raiz activa:
  - `patches/`
  - `recover.sql`
  - `bublee_patch.py`
  - `patch.py`
  - `fix_intro.py`
  - `fix_order.py`
  - `fix_prospect.py`
- Se agrego manifiesto en `/home/ubuntu/bublee/legacy/2026-06-24-one-off-patches/MANIFEST.md`.

### Verificacion

- `/home/ubuntu/bublee/scripts/preflight_agents.sh`: OK despues del movimiento.
- Los archivos movidos ya no existen en la raiz activa.

## Pasada 6: Branding Estatico

Fecha: 2026-06-24

### Cambios Aplicados

- Se reemplazaron referencias en `src/interfaces/web/static`:
  - `conny_logo_12jun` -> `bublee_logo_12jun`
  - `conny_master_key` -> `bublee_master_key`
  - `conny_dev_mode` -> `bublee_dev_mode`
- Se archivaron `conny_logo_12jun.png` y `conny_logo_12jun.svg` en `/home/ubuntu/bublee/legacy/2026-06-24-static-conny-assets/`.
- Se creo `/home/ubuntu/bublee/scripts/audit_static_branding.py`.
- `preflight_agents.sh` ahora incluye la auditoria de branding estatico.

### Verificacion

- `python3 /home/ubuntu/bublee/scripts/audit_static_branding.py`: OK.
- `/home/ubuntu/bublee/scripts/preflight_agents.sh`: OK.
- `find /home/ubuntu/bublee/src/interfaces/web/static -iname '*conny*'`: sin resultados.

## Pasada 7: Identidad Honesta Centralizada

Fecha: 2026-06-24

### Cambios Aplicados

- Se creo `/home/ubuntu/bublee/bublee_core/identity_policy.py`.
- Se sincronizo `identity_policy.py` a:
  - `/home/ubuntu/bublee-instances/clinica-de-las-americas/bublee_core/identity_policy.py`
  - `/home/ubuntu/bublee-instances/ovni/bublee_core/identity_policy.py`
  - `/home/ubuntu/bublee-instances/melissa-x/bublee_core/identity_policy.py`
- `production_monitor.py`, `prompt_ops.py` y `v7/agents/captacion.py` usan la politica compartida.
- Se corrigio una contradiccion de prompt que decia no fingir ser humana pero tambien "NUNCA confirmes ser bot/IA".
- Se ampliaron auditorias a `src/core/globals.py`, demos, CLI y handlers web demo.
- Se archivaron backups raiz de produccion y `conny.db` en `/home/ubuntu/bublee-instances/clinica-de-las-americas/legacy/2026-06-24-root-backups/`.

### Verificacion

- `python3 /home/ubuntu/bublee/scripts/audit_runtime_cleanliness.py`: OK.
- `/home/ubuntu/bublee/scripts/preflight_agents.sh`: OK.
- `pm2 restart bublee-clinica-de-las-americas bublee-ovni bublee-melissa-x --update-env`: OK.
- Health local `8003`, `8006`, `8008`: online.
- Telegram status produccion y Ovni: `ok=true`, `pending_update_count=0`.
