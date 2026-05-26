#!/bin/bash
# Conny AI - The AI Receptionist Engine
# Ultimate GitHub Installer Script
set -e

C_PRIMARY="\033[38;5;135m"
C_SUCCESS="\033[38;5;46m"
C_MUTED="\033[38;5;240m"
BOLD="\033[1m"
RESET="\033[0m"

echo -e "\n  ${C_PRIMARY}${BOLD}✦ Conny AI - Ultimate Installer${RESET}"
echo -e "  ${C_MUTED}─────────────────────────────────────────${RESET}"

# Handle sudo gracefully (Termux / Root environments)
SUDO=""
if command -v sudo &> /dev/null; then
    SUDO="sudo"
fi

# 1. Install chafa if possible
if ! command -v chafa &> /dev/null; then
    echo -e "\n  ${BOLD}1. Instalando motor True-Color (chafa)...${RESET}"
    if command -v pkg &> /dev/null; then
        pkg install -y chafa || true
    elif command -v apt-get &> /dev/null; then
        $SUDO apt-get update -yqq && $SUDO apt-get install -yqq chafa || true
    elif command -v brew &> /dev/null; then
        brew install chafa || true
    else
        echo -e "  ${C_MUTED}No se pudo instalar chafa automáticamente. Se usará el logo clásico.${RESET}"
    fi
else
    echo -e "\n  ${BOLD}1. Motor True-Color detectado (chafa).${RESET}"
fi

# 2. Verify Python sanely (3.9+), without hardcoding minor versions
PYTHON_BIN=""
for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
        if "$candidate" - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info >= (3, 9) else 1)
PY
        then
            PYTHON_BIN="$candidate"
            break
        fi
    fi
done

if [ -n "$PYTHON_BIN" ]; then
    PY_VERSION="$($PYTHON_BIN -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')"
    echo -e "\n  ${BOLD}2. Python detectado:${RESET} ${C_SUCCESS}${PYTHON_BIN} (${PY_VERSION})${RESET}"
else
    echo -e "\n  ${BOLD}2. Python 3.9+ no detectado localmente.${RESET}"
    echo -e "  ${C_MUTED}Conny intentará crear su runtime cuando se ejecute por primera vez.${RESET}"
fi

# 3. Install NPM Package
if ! command -v npm &> /dev/null; then
    echo -e "\n  \033[31mError: Node.js y npm son requeridos. Instálalos primero.\033[0m"
    exit 1
fi

echo -e "\n  ${BOLD}3. Limpiando versiones anteriores...${RESET}"
npm uninstall -g conny-ai @blackboss/conny || true

echo -e "\n  ${BOLD}4. Instalando Conny CLI y Motor AI...${RESET}"
npm install -g "${CONNY_INSTALL_PACKAGE:-conny-ai@latest}"

echo -e "\n  ${BOLD}5. Verificando bootstrap del CLI...${RESET}"
if command -v conny >/dev/null 2>&1; then
    conny --version || true
fi

echo -e "\n  ${C_SUCCESS}${BOLD}✔ ¡Conny instalado con éxito!${RESET}"
echo -e "  Ejecuta ${C_PRIMARY}conny init${RESET} en tu terminal para empezar la magia.\n"
