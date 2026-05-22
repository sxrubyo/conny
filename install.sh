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

# 1. Install chafa if possible
if ! command -v chafa &> /dev/null; then
    echo -e "\n  ${BOLD}1. Instalando motor True-Color (chafa)...${RESET}"
    if command -v apt-get &> /dev/null; then
        sudo apt-get update -yqq && sudo apt-get install -yqq chafa
    elif command -v brew &> /dev/null; then
        brew install chafa
    else
        echo -e "  ${C_MUTED}No se pudo instalar chafa automáticamente. Se usará el logo clásico.${RESET}"
    fi
else
    echo -e "\n  ${BOLD}1. Motor True-Color detectado (chafa).${RESET}"
fi

# 2. Install NPM Package from Github
if ! command -v npm &> /dev/null; then
    echo -e "\n  \033[31mError: Node.js y npm son requeridos. Instálalos primero.\033[0m"
    exit 1
fi

echo -e "\n  ${BOLD}2. Instalando Conny CLI y Motor AI desde GitHub...${RESET}"
npm install -g git+https://github.com/sxrubyo/conny.git

echo -e "\n  ${C_SUCCESS}${BOLD}✔ ¡Conny instalado con éxito!${RESET}"
echo -e "  Ejecuta ${C_PRIMARY}conny init${RESET} en tu terminal para empezar la magia.\n"
