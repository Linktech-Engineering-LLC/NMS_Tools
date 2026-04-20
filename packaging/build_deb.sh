#!/usr/bin/env bash
set -euo pipefail

echo "[NMS_Tools] Building DEB package..."

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEB_DIR="$ROOT_DIR/packaging/debian"

cd "$ROOT_DIR"

# Ensure man pages are generated
echo "[NMS_Tools] Generating man pages..."
make man

# Build source tarball
echo "[NMS_Tools] Creating source tarball..."
VERSION=$(grep -m1 "Version:" packaging/rpm/nms_tools.spec | awk '{print $2}')
TARBALL="nms_tools-${VERSION}.tar.gz"
git archive --format=tar.gz --output="$TARBALL" HEAD

# Build DEB
echo "[NMS_Tools] Running dpkg-buildpackage..."
dpkg-buildpackage -us -uc

echo "[NMS_Tools] DEB build complete."
