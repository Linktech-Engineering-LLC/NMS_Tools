#!/usr/bin/env bash
#
# build_all.sh — Full NMS_Tools packaging pipeline
#

set -euo pipefail

echo "==============================================="
echo "[NMS_Tools] Starting full packaging pipeline..."
echo "==============================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git rev-parse --show-toplevel)"

OUTPUT_DIR="$SCRIPT_DIR/output"
DIST_DIR="$REPO_ROOT/dist"
VERSION_FILE="$REPO_ROOT/VERSION"
VERSION="$(cat "$VERSION_FILE")"

echo "[NMS_Tools] Version: $VERSION"

# ------------------------------------------------------------
# Clean previous output
# ------------------------------------------------------------
echo "[NMS_Tools] Cleaning previous output..."
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

# ------------------------------------------------------------
# 1. Freeze all tools
# ------------------------------------------------------------
echo "[NMS_Tools] Freezing all tools..."
"$REPO_ROOT/scripts/build.py"

# Validate freeze output
if [ ! -d "$DIST_DIR" ] || [ -z "$(ls -A "$DIST_DIR")" ]; then
    echo "ERROR: No frozen binaries found in $DIST_DIR"
    exit 1
fi

# ------------------------------------------------------------
# 2. Build TGZ/ZIP portable packages
# ------------------------------------------------------------
echo "[NMS_Tools] Building TGZ/ZIP..."
"$SCRIPT_DIR/build_tgz_zip.sh"

# ------------------------------------------------------------
# 3. Build DEB
# ------------------------------------------------------------
echo "[NMS_Tools] Building DEB..."
"$SCRIPT_DIR/build_deb.sh"

# ------------------------------------------------------------
# 4. Build RPM
# ------------------------------------------------------------
echo "[NMS_Tools] Building RPM..."
"$SCRIPT_DIR/build_rpm.sh"

echo "==============================================="
echo "[NMS_Tools] All packaging complete."
echo "Artifacts located in: $OUTPUT_DIR"
echo "==============================================="
