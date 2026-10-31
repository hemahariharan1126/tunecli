#!/usr/bin/env bash
# =========================================
#       ⚡ Starting M! TuneCLI ⚡
# =========================================

set -e

# Navigate to script directory
cd "$(dirname "$0")"

echo "========================================="
echo "      ⚡ Starting M! TuneCLI ⚡"
echo "========================================="
echo ""

# 1. Check for Python 3.10+
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] python3 is not installed or not in your PATH."
    echo "Please install Python 3.10+ using your package manager."
    exit 1
fi

# 2. Ensure .env exists
if [ ! -f ".env" ]; then
    echo "[INFO] Creating default .env file from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
    else
        echo "# TuneCLI Environment Config" > .env
    fi
fi

# 3. Create Virtual Environment if not present
if [ ! -d "venv" ]; then
    echo "[INFO] First time setup detected."
    echo "[INFO] Creating isolated Virtual Environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# 4. Check dependencies
if [ ! -f "venv/.installed" ]; then
    echo "[INFO] Installing required dependencies... This may take a minute."
    python -m pip install --upgrade pip >/dev/null 2>&1 || true
    python -m pip install -r requirements.txt
    touch venv/.installed
fi

# 5. Check for libmpv on Linux / macOS
if ! python -c "import mpv" &>/dev/null; then
    echo "[WARNING] MPV native library (libmpv) was not detected!"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Please install it using Homebrew: brew install mpv"
    else
        echo "Please install it using your package manager, e.g.:"
        echo "  Debian/Ubuntu: sudo apt install libmpv-dev mpv"
        echo "  Arch Linux:    sudo pacman -S mpv"
        echo "  Fedora:        sudo dnf install mpv-libs-devel mpv"
    fi
    echo ""
fi

# 6. Launch Application
echo "[INFO] Launching Application..."
exec python main.py
