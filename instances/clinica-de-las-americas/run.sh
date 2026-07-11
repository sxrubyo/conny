#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUBLEE_HOME="${BUBLEE_HOME:-$HOME/.bublee}"
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

# ── Pre-flight: sin al menos una key de LLM, Bublee arranca "bien" y muere
#    feo (error críptico) en el primer mensaje. Mejor fallar acá con un
#    mensaje claro que se pueda diagnosticar desde los logs de PM2 en 2 segundos.
if [ -z "$GEMINI_API_KEY" ] && [ -z "$GROQ_API_KEY" ] && [ -z "$OPENROUTER_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
  echo "[bublee] ERROR: no encontré ninguna key de LLM en $ENV_FILE" >&2
  echo "[bublee] Se necesita al menos una de: GEMINI_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY, OPENAI_API_KEY" >&2
  exit 1
fi

echo "[bublee] $(date '+%Y-%m-%d %H:%M:%S') arrancando instancia en $SCRIPT_DIR (puerto ${PORT:-8001})"

PYTHON_OVERRIDE="${BUBLEE_PYTHON_BIN:-${PYTHON_BIN:-$(read_env_value BUBLEE_PYTHON_BIN)}}"
if [ -z "$PYTHON_OVERRIDE" ]; then
  PYTHON_OVERRIDE="$(read_env_value PYTHON_BIN)"
fi

pick_python() {
  local candidates=(
    "$PYTHON_OVERRIDE"
    "$SCRIPT_DIR/.venv/bin/python"
    "$SCRIPT_DIR/.venv/bin/python3"
    "$BUBLEE_HOME/runtime/bin/python"
    "$BUBLEE_HOME/runtime/bin/python3"
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
  echo "[bublee] No encontré un intérprete Python ejecutable para esta instancia." >&2
  exit 1
fi

cd "$SCRIPT_DIR"
exec "$PYTHON_BIN_SELECTED" "$SCRIPT_DIR/bublee.py"
