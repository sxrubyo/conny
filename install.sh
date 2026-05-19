#!/bin/bash
# install.sh — instala 'conny' como comando del sistema
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$SCRIPT_DIR/conny_cli.py"
[ ! -f "$SRC" ] && { echo "conny_cli.py no encontrado en $SCRIPT_DIR"; exit 1; }
chmod +x "$SRC"
if [[ "$1" == "--user" ]]; then
  mkdir -p "$HOME/.local/bin"
  cp "$SRC" "$HOME/.local/bin/conny"
  chmod +x "$HOME/.local/bin/conny"
  echo "✓ conny instalado en ~/.local/bin/conny"
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
  echo "Ejecuta: source ~/.bashrc"
else
  sudo cp "$SRC" /usr/local/bin/conny
  sudo chmod +x /usr/local/bin/conny
  echo "✓ conny instalado en /usr/local/bin/conny"
fi
echo ""
echo "Prueba: conny init"
