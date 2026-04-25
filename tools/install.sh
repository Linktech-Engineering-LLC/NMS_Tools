#!/usr/bin/env bash
set -e

TARGET="/usr/local/nagios/NMS_Tools"
SRC="$(cd "$(dirname "$0")" && pwd)"

echo "[install] Installing NMS_Tools suite..."
echo "[install] Source: $SRC"
echo "[install] Target: $TARGET"

# ------------------------------------------------------------
# Python version check
# ------------------------------------------------------------
echo "[install] Checking Python version..."
if ! python3 -c 'import sys; exit(0 if sys.version_info >= (3,8) else 1)'; then
    echo "[install] ERROR: Python 3.8+ is required."
    exit 1
fi
echo "[install] Python version OK."

# ------------------------------------------------------------
# Create base directory
# ------------------------------------------------------------
sudo mkdir -p "$TARGET"
sudo mkdir -p "$TARGET/tools"
sudo mkdir -p "$TARGET/libs"

# ------------------------------------------------------------
# Copy tool scripts only
# ------------------------------------------------------------
echo "[install] Copying tool scripts..."

TOOLS=(
    "check_ports/check_ports.py"
    "check_weather/check_weather.py"
    "check_cert/check_cert.py"
    "check_html/check_html.py"
    "check_interfaces/check_interfaces.py"
)

for tool in "${TOOLS[@]}"; do
    if [[ -f "$SRC/$tool" ]]; then
        sudo cp "$SRC/$tool" "$TARGET/tools/"
        echo "[install]   + $(basename "$tool")"
    else
        echo "[install] WARNING: Missing tool: $tool"
    fi
done

# ------------------------------------------------------------
# Copy vendored libs
# ------------------------------------------------------------
echo "[install] Copying vendored libraries..."
if [[ -d "$SRC/libs" ]]; then
    sudo cp -r "$SRC/libs/"* "$TARGET/libs/" 2>/dev/null || true
else
    echo "[install] WARNING: No libs directory found."
fi

# ------------------------------------------------------------
# Copy VERSION file
# ------------------------------------------------------------
if [[ -f "$SRC/VERSION" ]]; then
    sudo cp "$SRC/VERSION" "$TARGET/"
else
    echo "[install] WARNING: VERSION file missing."
fi

# ------------------------------------------------------------
# Permissions
# ------------------------------------------------------------
sudo chmod -R 755 "$TARGET"
sudo find "$TARGET/tools" -type f -name "*.py" -exec chmod 755 {} \;

# ------------------------------------------------------------
# Summary
# ------------------------------------------------------------
VERSION=$(cat "$TARGET/VERSION" 2>/dev/null || echo "unknown")

echo ""
echo "[install] ==============================================="
echo "[install] NMS_Tools installation complete"
echo "[install] Version: $VERSION"
echo "[install] Tools installed: ${#TOOLS[@]}"
echo "[install] Vendor packages: $(ls "$TARGET/libs" | wc -l)"
echo "[install] Location: $TARGET"
echo "[install] ==============================================="
