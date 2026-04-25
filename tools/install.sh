#!/usr/bin/env bash
set -e

TARGET="/usr/local/nagios/NMS_Tools"
SRC="$(cd "$(dirname "$0")" && pwd)"

echo "[install] Installing NMS_Tools suite..."
echo "[install] Source: $SRC"
echo "[install] Target: $TARGET"

# Check Python version
echo "[install] Checking Python version..."
if ! python3 -c 'import sys; exit(0 if sys.version_info >= (3,8) else 1)'; then
    echo "[install] ERROR: Python 3.8+ is required."
    exit 1
fi
echo "[install] Python version OK."

# Create target directory
sudo mkdir -p "$TARGET"

# Copy suite contents
sudo cp -r "$SRC"/* "$TARGET"

# Permissions
sudo chmod -R 755 "$TARGET"
sudo find "$TARGET" -type f -name "*.py" -exec chmod 755 {} \;

# Version
VERSION=$(cat "$TARGET/VERSION")
echo "[install] Installed NMS_Tools version: $VERSION"

echo "[install] Installation complete."
