#!/bin/bash
# Bublee AI - The AI Receptionist Engine
# Ultimate GitHub Installer Script
set -e

C_PRIMARY="\033[38;5;135m"
C_SUCCESS="\033[38;5;46m"
C_MUTED="\033[38;5;240m"
C_WARN="\033[38;5;214m"
BOLD="\033[1m"
RESET="\033[0m"

echo -e "\n  ${C_PRIMARY}${BOLD}✦ Bublee AI Installer${RESET}"
echo -e "  ${C_MUTED}Production-ready AI receptionist runtime for WhatsApp and Telegram.${RESET}"
echo -e "  ${C_MUTED}────────────────────────────────────────────────────────${RESET}"

TMP_LOGS=()

cleanup_logs() {
    for log_file in "${TMP_LOGS[@]}"; do
        [ -f "$log_file" ] && rm -f "$log_file"
    done
}
trap cleanup_logs EXIT

run_with_activity() {
    local label="$1"
    shift
    local log_file
    log_file="$(mktemp)"
    TMP_LOGS+=("$log_file")

    echo -ne "  ${C_PRIMARY}⠋${RESET} ${label}"
    "$@" >"$log_file" 2>&1 &
    local pid=$!
    local frames=("⠋" "⠙" "⠹" "⠸" "⠼" "⠴" "⠦" "⠧" "⠇" "⠏")
    local i=0
    local elapsed=0

    while kill -0 "$pid" 2>/dev/null; do
        printf "\r  ${C_PRIMARY}%s${RESET} %s ${C_MUTED}(%ss)${RESET}" "${frames[$((i % ${#frames[@]}))]}" "$label" "$elapsed"
        sleep 1
        i=$((i + 1))
        elapsed=$((elapsed + 1))
    done

    if wait "$pid"; then
        printf "\r  ${C_SUCCESS}✓${RESET} %s ${C_MUTED}(%ss)${RESET}\n" "$label" "$elapsed"
        return 0
    fi

    printf "\r  \033[31m✕${RESET} %s\n" "$label"
    echo -e "  \033[31mCommand failed. Installer log:${RESET}"
    sed 's/^/    /' "$log_file"
    return 1
}

# Handle sudo gracefully (Termux / Root environments)
SUDO=""
if command -v sudo &> /dev/null; then
    SUDO="sudo"
fi

# 1. Install chafa if possible. In Termux/proot, `pkg` exists but cannot run as root.
if ! command -v chafa &> /dev/null; then
    echo -e "\n  ${BOLD}1. Preparing terminal visuals${RESET}"
    CURRENT_UID="$(id -u 2>/dev/null || echo 1)"
    if command -v pkg &> /dev/null && [ "$CURRENT_UID" != "0" ]; then
        run_with_activity "Installing optional True-Color renderer with pkg" pkg install -y chafa || true
    elif command -v apt-get &> /dev/null; then
        run_with_activity "Installing optional True-Color renderer with apt" bash -c "$SUDO apt-get update -yqq && $SUDO apt-get install -yqq chafa" || true
    elif command -v brew &> /dev/null; then
        run_with_activity "Installing optional True-Color renderer with Homebrew" brew install chafa || true
    else
        echo -e "  ${C_WARN}!${RESET} Optional renderer not available. Bublee will use the classic logo."
    fi
else
    echo -e "\n  ${BOLD}1. Terminal visuals ready${RESET}"
    echo -e "  ${C_SUCCESS}✓${RESET} True-Color renderer detected."
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
    echo -e "\n  ${BOLD}2. Runtime compatibility${RESET}"
    echo -e "  ${C_SUCCESS}✓${RESET} Python runtime detected: ${C_SUCCESS}${PYTHON_BIN} ${PY_VERSION}${RESET}"
else
    echo -e "\n  ${BOLD}2. Runtime compatibility${RESET}"
    echo -e "  ${C_WARN}!${RESET} Python 3.9+ was not detected locally."
    echo -e "  ${C_MUTED}Bublee will try to provision its isolated runtime on first launch.${RESET}"
fi

# 3. Install NPM Package
if ! command -v npm &> /dev/null; then
    echo -e "\n  \033[31mError: Node.js and npm are required before installing Bublee.\033[0m"
    exit 1
fi

echo -e "\n  ${BOLD}3. Removing previous global builds${RESET}"
run_with_activity "Cleaning old Bublee packages" npm uninstall -g bublee-ai @innvisor/bublee-ai @blackboss/bublee || true

echo -e "\n  ${BOLD}4. Installing Bublee from GitHub${RESET}"
echo -e "  ${C_MUTED}Source: ${BUBLEE_INSTALL_PACKAGE:-github:sxrubyo/bublee#main}${RESET}"
run_with_activity "Downloading and linking Bublee CLI" npm install -g "${BUBLEE_INSTALL_PACKAGE:-github:sxrubyo/bublee#main}"

echo -e "\n  ${BOLD}5. Verifying the command line experience${RESET}"
if command -v bublee >/dev/null 2>&1; then
    if ! bublee --version; then
        echo -e "\n  \033[31mError: Bublee was installed, but the CLI could not start.\033[0m"
        exit 1
    fi
    run_with_activity "Preparing Python runtime and required CLI packages" bublee --bootstrap-check
else
    echo -e "\n  \033[31mError: npm finished, but the 'bublee' command is not available in PATH.\033[0m"
    exit 1
fi

echo -e "\n  ${C_SUCCESS}${BOLD}✓ Bublee is installed and ready.${RESET}"
echo -e "  Start your first guided setup with ${C_PRIMARY}bublee init${RESET}."
echo -e "  For system repair and diagnostics, run ${C_PRIMARY}bublee doctor --fix${RESET}.\n"
