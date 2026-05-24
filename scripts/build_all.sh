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
for TOOL in $(ls "$SRC_ROOT"); do
    if [ -d "$SRC_ROOT/$TOOL" ]; then
        echo ""
        echo "----------------------------------------"
        echo " Starting build for: $TOOL"
        echo "----------------------------------------"
        ./scripts/build_one.sh "$TOOL"
    fi
done

echo ""
echo "========================================"
echo " All builds completed successfully"
echo "========================================"
