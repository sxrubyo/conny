# Instrucciones para Agentes — Bublee en AWS

## Reglas de oro
1. Trabaja SOLO en /home/ubuntu/bublee/ (código) y /home/ubuntu/bublee/instances/ (instancias)
2. NO toques carpetas legacy: bublee-dev2, bublee-private, bublee-ai, bublee-dev-react, bublee-old-backup
3. PM2: usa ecosystem.config.js para iniciar/detener procesos
4. Caddy: editar con sudo, validar con "sudo caddy validate --config /etc/caddy/Caddyfile"
5. Rama git activa: refactor-v10 (NO main)
6. Antes de crear una instancia: asegúrate de tener un bot de Telegram REAL
7. Los webhooks usan prefijo "conny_" por legacy. Mantener consistencia con Caddyfile.

## Stack
- Python 3.11+ / FastAPI / uvicorn / SQLite
- Caddy (SSL automático, DuckDNS)
- PM2 (gestión de procesos)
- n8n en puerto 5678 (workflows)

## Puertos activos
- 8001: Main Bublee (@Xus_enterprises_bot)
- 8003: Clínica de las Américas (@melissaxai_bot)
- 8006: Melissa-X (@admelissabot)
- 5678: n8n (workflows)

## Para verificar estado
pm2 list
curl -s http://localhost:8001/health
curl -s http://localhost:8003/health
curl -s http://localhost:8006/health
