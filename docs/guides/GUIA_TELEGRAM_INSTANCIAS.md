# Guia Operativa: Instancias Telegram de Bublee

## Estado correcto

- Bublee base vive en `:8001` y hoy está configurada para `whatsapp`.
- Omni vive en `:9001` y usa su propio bot de Telegram para control.
- Las instancias adicionales de Bublee para Telegram no deben exponerse con `http://IP:puerto`.
- Deben vivir detrás de `https://nexusys.duckdns.org` usando una ruta dedicada de Caddy:
  - patrón: `/webhook/<WEBHOOK_SECRET>`

## Regla crítica

Para Telegram:

- `BASE_URL` debe ser el dominio HTTPS público.
- `PORT` debe ser un puerto libre interno.
- Caddy debe enrutar `handle /webhook/<WEBHOOK_SECRET>*` al puerto interno de la instancia.

Ejemplo conceptual:

- `BASE_URL=https://nexusys.duckdns.org`
- `PORT=8003`
- `WEBHOOK_SECRET=bublee_mi-instancia_abcd1234`
- Webhook final registrado en Telegram:
  - `https://nexusys.duckdns.org/webhook/bublee_mi-instancia_abcd1234`

## Qué rompía la instancia clínica

- Estaba en `PLATFORM=telegram`.
- Tenía `BASE_URL=http://3.137.123.141:8002`.
- Telegram rechazaba ese webhook por no ser HTTPS válido.
- Además `:8002` ya estaba ocupado por `whatsapp-bridge`, así que la app entraba en reinicios.

## Qué quedó corregido

- La instancia `clinica-de-las-americas` se movió a `:8003`.
- Su `BASE_URL` quedó en `https://nexusys.duckdns.org`.
- Caddy ahora enruta su webhook dedicado al puerto `8003`.
- El webhook de Telegram quedó registrado correctamente.

## Verificación rápida

### 1. PM2

```bash
pm2 show bublee-clinica-de-las-americas
```

Debe verse `status: online`.

### 2. Salud local

```bash
curl http://127.0.0.1:8003/health
```

Debe devolver `platform: "telegram"`.

### 3. Webhook Telegram

```bash
TOKEN="..."
curl "https://api.telegram.org/bot${TOKEN}/getWebhookInfo"
```

Debe apuntar a:

```text
https://nexusys.duckdns.org/webhook/<WEBHOOK_SECRET>
```

### 4. Ruta HTTPS

```bash
curl -X POST "https://nexusys.duckdns.org/webhook/<WEBHOOK_SECRET>" \
  -H 'Content-Type: application/json' \
  -d '{}'
```

Debe responder:

```json
{"ok": true}
```

## Síntomas y diagnóstico

### No responde en Telegram

Revisar:

```bash
pm2 logs bublee-clinica-de-las-americas --lines 80 --nostream
```

Buscar:

- `Webhook ERROR`
- `address already in use`
- `Connection refused`

### No aparece escribiendo

Si el webhook entra bien, Bublee dispara `sendChatAction` antes de responder.
Si no aparece escribiendo, revisar:

- que el update esté entrando por el webhook correcto
- que el bot correcto sea el que tiene ese `TELEGRAM_TOKEN`
- que no haya otro proceso reescribiendo el webhook del mismo bot

## Regla para nuevas instancias

Cuando crees una nueva instancia Telegram desde el CLI:

- usa el dominio HTTPS compartido como `BASE_URL`
- no uses IP pública con puerto
- verifica que el puerto interno esté libre
- sincroniza Caddy antes de probar el bot

## Comandos útiles

```bash
pm2 ls
pm2 show bublee-clinica-de-las-americas
pm2 logs bublee-clinica-de-las-americas --lines 120 --nostream
docker compose -f /home/ubuntu/xus-https/docker-compose.yml restart caddy
curl http://127.0.0.1:8003/health
```
