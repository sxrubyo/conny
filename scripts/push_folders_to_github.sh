#!/bin/bash
set -e

echo "Refrescando el snapshot (copiando todas las carpetas seguras)..."
cd /home/ubuntu/omnisync
./scripts/refresh_home_snapshot.sh --mode safe

echo "Sincronizando los archivos a tu repositorio privado..."
cd /home/ubuntu/omni-migrate-sync-private
# Copiar el snapshot limpio a la raíz del repositorio
rsync -av --exclude='.git/' /home/ubuntu/home_snapshot/ubuntu/ ./

echo "Subiendo a GitHub..."
git add .
git commit -m "feat: migrate entire workspace folders" || true
git push origin main

echo ""
echo "¡Listo! Tus carpetas (bublee, omnisync, etc.) ahora están visibles y guardadas en tu GitHub privado."
echo "Para restaurarlo en la nueva máquina:"
echo "1. Clona el repositorio: git clone <tu-repo-privado> temp_home"
echo "2. Copia todo a tu home: rsync -av temp_home/ /home/ubuntu/"
echo "3. Entra a /home/ubuntu/omnisync y ejecuta: omni migrate sync (para reinstalar paquetes globales y configuraciones del sistema)"
