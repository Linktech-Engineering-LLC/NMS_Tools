#!/bin/bash
#
# build_all.sh — Build all NMS_Tools components
# Usage: ./scripts/build_all.sh
#

set -e

SRC_ROOT="src"

echo "========================================"
echo " Building ALL NMS_Tools components"
echo " Source root: $SRC_ROOT"
echo "========================================"

# Loop through each tool directory under src/
for TOOL_DIR in "$SRC_ROOT"; do
    [ -d "$TOOL_DIR" ] || continue
        echo ""
        echo "----------------------------------------"
        echo " Starting build for: $(basename "$TOOL_DIR")"
        echo "----------------------------------------"
        ./scripts/build_one.sh "$(basename "$TOOL_DIR")"
    fi
done

echo ""
echo "========================================"
echo " All builds completed successfully"
echo "========================================"
