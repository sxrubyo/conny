# Plan Arquitectura Real De Agentes

## Objetivo

Separar Bublee en capas y roles para que cada agente se encuentre, arranque y responda de forma deterministica.

## Arquitectura Objetivo

| Capa | Responsabilidad | Debe Contener |
| --- | --- | --- |
| `control/ovni` | Comando, diagnostico, cambios de runtime, auditoria | Un solo token, acceso a estado de instancias, sin flujo paciente |
| `production/client` | Atencion real de cliente/admin | Un token de produccion, DB propia, identidad propia |
| `production/demo` | Demos aisladas | Tokens propios o sin Telegram, memoria descartable |
| `admin/base` | Panel, CLI, generacion de instancias | Sin bot publico salvo decision explicita |
| `shared/router` | Ingress comun opcional | Rutas explicitas por `bot_id`, `chat_id` e `instance_id`; sin fallback por default |

## Fase 1: Contencion

1. Verificar que solo dos tokens queden activos en Telegram: produccion y Ovni.
2. Mantener `TELEGRAM_SHARED_ALLOW_DEFAULT_FALLBACK=false`.
3. Evitar cualquier `TELEGRAM_TOKEN` duplicado entre `.env`.
4. Hacer health check y `telegram/status` tras cada restart.

## Fase 2: Inventario Y Limpieza

1. Generar inventario automatico de procesos PM2, carpetas, `.env`, puertos, tokens truncados, DB paths y webhook secrets.
2. Marcar archivos legacy `conny_*` y `patch_*` como runtime activo, script historico, backup o eliminar despues de backup.
3. Crear `instances/<id>/ROLE.md` por instancia con mapa minimo.

## Fase 3: Router Deterministico

1. Reemplazar `shared_telegram_routes.json` por un registro versionado:

```json
{
  "bots": {
    "8749260201": {"role": "ovni", "instance": "ovni", "port": 8008},
    "8779529912": {"role": "production", "instance": "production", "port": 8003}
  },
  "chat_routes": {},
  "fallback": null
}
```

2. Resolver destino por prioridad: `bot_id` primero, `chat_id` solo si el bot es compartido, nunca fallback a cliente si no hay match.
3. Registrar eventos de routing con `bot_id`, `instance_id`, `chat_id`, `decision`, `reason`.

## Fase 4: Separacion De Memoria

1. Una DB por instancia bajo `/home/ubuntu/bublee-instances/<instance>/`.
2. Prohibir paths `/home/ubuntu/conny-instances` en runtime Bublee.
3. Crear migracion controlada si se necesita copiar memoria vieja.

## Fase 5: Estandar De Arranque

1. Un `ecosystem.config.js` generado desde `instances.registry.json`.
2. Cada proceso debe tener `INSTANCE_ID`, `ROLE`, `PORT`, `BASE_URL`, `DB_PATH` y `TELEGRAM_TOKEN` solo si el rol lo permite.
3. El startup debe fallar o degradar explicitamente si detecta token duplicado.

## Checks Minimos Permanentes

- `python scripts/audit_agents.py` debe fallar si hay tokens duplicados.
- `python scripts/audit_agents.py` debe fallar si produccion no tiene webhook HTTPS.
- `python scripts/audit_agents.py` debe fallar si Ovni no apunta al puerto 8008.
- Tests deben cubrir activation gate para que demos sin setup no puedan responder desde tokens de control.
