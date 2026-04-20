#!/usr/bin/env bash
set -euo pipefail

echo "[NMS_Tools] Running full packaging pipeline..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[NMS_Tools] Building DEB..."
"$SCRIPT_DIR/build_deb.sh"

echo "[NMS_Tools] Building RPM..."
"$SCRIPT_DIR/build_rpm.sh"

echo "[NMS_Tools] All packaging complete."
