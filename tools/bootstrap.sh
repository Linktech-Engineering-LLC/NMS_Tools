#!/usr/bin/env bash
set -euo pipefail

# -----------------------------------------
#  NMS_Tools Bootstrap Script (Python 3.12)
# -----------------------------------------

REQUIRED="3.12"
VENV_DIR=".venv"

echo "==> Checking Python version"

# Find python executable
PY=$(command -v python3 || true)
if [ -z "$PY" ]; then
    echo "ERROR: python3 not found on PATH"
    exit 1
fi

# Extract version
VER=$($PY -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")

echo "    Found Python $VER at: $PY"

# Compare versions
if [ "$VER" != "$REQUIRED" ]; then
    echo "ERROR: Python $REQUIRED is required, but $VER is installed."
    echo "Please install Python $REQUIRED and re-run this script."
    exit 1
fi

echo "==> Python version OK"

# Create venv
if [ -d "$VENV_DIR" ]; then
    echo "==> Existing venv detected at $VENV_DIR"
    echo "    Remove it if you want a clean rebuild."
else
    echo "==> Creating venv using Python $REQUIRED"
    $PY -m venv "$VENV_DIR"
fi

# Activate venv
echo "==> Activating venv"
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "==> Upgrading pip"
pip install --upgrade pip

# Install requirements
if [ -f "requirements.txt" ]; then
    echo "==> Installing dependencies from requirements.txt"
    pip install -r requirements.txt
else
    echo "WARNING: requirements.txt not found — skipping dependency install"
fi

echo "==> Bootstrap complete"
echo "Environment ready at $VENV_DIR"
