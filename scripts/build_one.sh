#!/bin/bash
#
# build_one.sh — Build a single NMS_Tools component
# Usage: ./scripts/build_one.sh <toolname>
#

set -e

TOOL="$1"

if [ -z "$TOOL" ]; then
    echo "ERROR: No tool specified."
    echo "Usage: ./scripts/build_one.sh <toolname>"
    exit 1
fi

SPEC_FILE="specs/${TOOL}.spec"
BUILD_DIR="build/linux-x86_64"

# Ensure the spec file exists
if [ ! -f "$SPEC_FILE" ]; then
    echo "ERROR: Spec file not found: $SPEC_FILE"
    exit 1
fi

# Ensure build directory exists
mkdir -p "$BUILD_DIR"

echo "========================================"
echo " Building tool: $TOOL"
echo " Spec file:     $SPEC_FILE"
echo " Output:        $BUILD_DIR"
echo "========================================"

# Build using curated spec file
pyinstaller "$SPEC_FILE" --clean

# Cleanup PyInstaller temp build directory
if [ -d "build/$TOOL" ]; then
    rm -rf "build/$TOOL"
fi

echo "[SUCCESS] Build complete for $TOOL"
echo "Binary located at: $BUILD_DIR/$TOOL"
