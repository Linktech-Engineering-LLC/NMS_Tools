#!/usr/bin/env bash
set -euo pipefail

echo "[NMS_Tools] Building RPM package..."

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SPEC_FILE="$ROOT_DIR/packaging/rpm/nms_tools.spec"

cd "$ROOT_DIR"

# Ensure man pages are generated
echo "[NMS_Tools] Generating man pages..."
make man

# Extract version
VERSION=$(grep -m1 "Version:" "$SPEC_FILE" | awk '{print $2}')
TARBALL="nms_tools-${VERSION}.tar.gz"

echo "[NMS_Tools] Creating source tarball..."
git archive --format=tar.gz --output="$TARBALL" HEAD

# Prepare rpmbuild tree
RPMBUILD_DIR="$HOME/rpmbuild"
mkdir -p "$RPMBUILD_DIR"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

cp "$TARBALL" "$RPMBUILD_DIR/SOURCES/"
cp "$SPEC_FILE" "$RPMBUILD_DIR/SPECS/"

echo "[NMS_Tools] Running rpmbuild..."
rpmbuild -ba "$RPMBUILD_DIR/SPECS/nms_tools.spec"

echo "[NMS_Tools] RPM build complete."
echo "Packages located in: $RPMBUILD_DIR/RPMS/"
