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

# 1. Freeze all tools
echo "[NMS_Tools] Freezing all tools..."
"$REPO_ROOT/scripts/build_all.sh"

# 2. Build TGZ/ZIP portable packages
echo "[NMS_Tools] Building TGZ/ZIP..."
"$SCRIPT_DIR/build_tgz_zip.sh"

# 3. Build DEB
echo "[NMS_Tools] Building DEB..."
"$SCRIPT_DIR/build_deb.sh"

# 4. Build RPM
echo "[NMS_Tools] Building RPM..."
"$SCRIPT_DIR/build_rpm.sh"

echo "==============================================="
echo "[NMS_Tools] All packaging complete."
echo "==============================================="
