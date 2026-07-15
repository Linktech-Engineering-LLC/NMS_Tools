#!/usr/bin/env bash
#
# build_tgz_zip.sh — Build portable TGZ/ZIP packages for NMS_Tools
#

set -euo pipefail

echo "[NMS_Tools] Building TGZ/ZIP portable packages..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git rev-parse --show-toplevel)"

OUTPUT_DIR="$SCRIPT_DIR/output"
STAGING_DIR="$SCRIPT_DIR/staging/nms-tools"

# PyInstaller output directory (works locally AND in GitHub Actions)
BIN_SRC="$REPO_ROOT/dist"

VERSION_FILE="$REPO_ROOT/VERSION"
VERSION="$(cat "$VERSION_FILE")"

# Clean staging/output
rm -rf "$STAGING_DIR"
mkdir -p "$STAGING_DIR/bin"
mkdir -p "$OUTPUT_DIR"

cp "$REPO_ROOT/LICENSE_BINARY.txt" "$STAGING_DIR/"

echo "[NMS_Tools] Staging frozen executables from: $BIN_SRC"

# Validate freeze output
if [ ! -d "$BIN_SRC" ]; then
    echo "ERROR: Frozen binaries not found in $BIN_SRC"
    echo "Run scripts/build.py first."
    exit 1
fi

# Copy frozen tools
cp "$BIN_SRC"/* "$STAGING_DIR/bin/"

echo "[NMS_Tools] Creating TGZ package..."
(
    cd "$SCRIPT_DIR/staging"
    tar -czf "$OUTPUT_DIR/nms-tools_${VERSION}.tgz" nms-tools
)

echo "[NMS_Tools] Creating ZIP package..."
(
    cd "$SCRIPT_DIR/staging"
    zip -r "$OUTPUT_DIR/nms-tools_${VERSION}.zip" nms-tools >/dev/null
)

echo "[NMS_Tools] TGZ/ZIP packages created:"
echo " - $OUTPUT_DIR/nms-tools_${VERSION}.tgz"
echo " - $OUTPUT_DIR/nms-tools_${VERSION}.zip"

echo "[NMS_Tools] TGZ/ZIP build complete."
