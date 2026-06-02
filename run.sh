#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONNY_HOME="${CONNY_HOME:-$HOME/.conny}"
ENV_FILE="$SCRIPT_DIR/.env"

read_env_value() {
  local key="$1"
  if [ -f "$ENV_FILE" ]; then
    grep -E "^${key}=" "$ENV_FILE" | tail -n 1 | cut -d'=' -f2- | sed 's/^"//;s/"$//;s/^'\''//;s/'\''$//'
  fi
}

# Export all .env variables so they're available to the Python process
if [ -f "$ENV_FILE" ]; then
  set -a
  source "$ENV_FILE"
  set +a
fi

PYTHON_OVERRIDE="${CONNY_PYTHON_BIN:-${PYTHON_BIN:-$(read_env_value CONNY_PYTHON_BIN)}}"
if [ -z "$PYTHON_OVERRIDE" ]; then
  PYTHON_OVERRIDE="$(read_env_value PYTHON_BIN)"
fi

pick_python() {
  local candidates=(
    "$PYTHON_OVERRIDE"
    "$SCRIPT_DIR/.venv/bin/python"
    "$SCRIPT_DIR/.venv/bin/python3"
    "$CONNY_HOME/runtime/bin/python"
    "$CONNY_HOME/runtime/bin/python3"
    "$(command -v python3 2>/dev/null || true)"
    "$(command -v python 2>/dev/null || true)"
  )
  local candidate=""
  for candidate in "${candidates[@]}"; do
    if [ -n "$candidate" ] && [ -x "$candidate" ]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

PYTHON_BIN_SELECTED="$(pick_python || true)"
if [ -z "$PYTHON_BIN_SELECTED" ]; then
  echo "[conny] No encontré un intérprete Python ejecutable para esta instancia." >&2
  exit 1
fi

cd "$SCRIPT_DIR"
exec "$PYTHON_BIN_SELECTED" "$SCRIPT_DIR/conny.py"
