# Bublee Produccion Cliente/Admin

## Identidad

- ID registry: `production`
- Rol: `production-client-admin`
- Proceso PM2: `bublee-clinica-de-las-americas`
- Puerto: `8003`

## Responsabilidad

Instancia productiva del cliente/admin. Atiende el bot de produccion y no debe compartir token, DB ni webhook con Ovni o demos.

## Telegram

- Bot ID esperado: `8779529912`
- Base URL: `https://bublee.nexusys.duckdns.org`
- Webhook: `bublee_production_2ed44661cb56cd55`

## Reglas

- No usar token de Ovni.
- No apuntar a rutas, DB o dominios legacy Conny.
- No habilitar router compartido sin registry explicito.
