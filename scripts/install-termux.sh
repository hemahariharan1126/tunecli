#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================================
# TuneCLI — Automated 1-Click Termux Environment Setup Script
# ==============================================================================
set -e

# Terminal colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}====================================================${NC}"
echo -e "${CYAN}      TuneCLI Termux Environment Provisioner       ${NC}"
echo -e "${CYAN}====================================================${NC}"

# 1. Verify Termux environment
if [ ! -d "/data/data/com.termux" ]; then
    echo -e "${RED}[ERROR] This script is meant to be run inside Termux on Android.${NC}"
    exit 1
fi

# 2. Update Termux packages & install system dependencies
echo -e "\n${YELLOW}[1/4] Updating packages and installing precompiled binaries...${NC}"
pkg update -y
pkg install -y python ffmpeg mpv termux-api git clang

# 3. Setup Python Virtual Environment
TUNECLI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$HOME/.tunecli-venv"

echo -e "\n${YELLOW}[2/4] Initializing Python Virtual Environment in ${VENV_DIR}...${NC}"
if [ ! -d "$VENV_DIR" ]; then
    python -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"

# 4. Install lightweight Android requirements
echo -e "\n${YELLOW}[3/4] Installing lightweight Python dependencies...${NC}"
pip install --upgrade pip setuptools wheel
pip install -r "$TUNECLI_DIR/requirements-android.txt"

# 5. Create executable shortcut in Termux PATH
echo -e "\n${YELLOW}[4/4] Creating 'tunecli' launcher in \$PREFIX/bin...${NC}"
mkdir -p "$PREFIX/bin"

cat << EOF > "$PREFIX/bin/tunecli"
#!/data/data/com.termux/files/usr/bin/bash
# Acquire wake-lock to prevent Android Doze from cutting audio
if command -v termux-wake-lock >/dev/null 2>&1; then
    termux-wake-lock
fi

source "$VENV_DIR/bin/activate"
cd "$TUNECLI_DIR"
python main.py "\$@"

# Release wake-lock upon exit
if command -v termux-wake-unlock >/dev/null 2>&1; then
    termux-wake-unlock
fi
EOF

chmod +x "$PREFIX/bin/tunecli"

echo -e "\n${GREEN}====================================================${NC}"
echo -e "${GREEN}      ✅ TuneCLI Setup Completed Successfully!       ${NC}"
echo -e "${GREEN}====================================================${NC}"
echo -e "You can now launch TuneCLI from anywhere by typing:"
echo -e "\n    ${CYAN}tunecli${NC}\n"
echo -e "${YELLOW}Tip:${NC} Make sure the 'Termux:API' APK is installed from F-Droid"
echo -e "for seamless background audio and wake-lock management."
