#!/usr/bin/env bash
set -euo pipefail

echo "[NMS_Tools] Building RPM package..."

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SPEC_FILE="$ROOT_DIR/packaging/rpm/nms-tools.spec"

cd "$ROOT_DIR"

# ------------------------------------------------------------
# Set up rpmbuild directory structure
# ------------------------------------------------------------
RPMBUILD_DIR="$HOME/rpmbuild"
mkdir -p "$RPMBUILD_DIR"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

# ------------------------------------------------------------
# Generate man pages
# ------------------------------------------------------------
echo "[NMS_Tools] Generating man pages..."

MAN_SRC_DIR="$ROOT_DIR/man"
MAN_OUT_DIR="$ROOT_DIR/man/generated"

rm -rf "$MAN_OUT_DIR"
mkdir -p "$MAN_OUT_DIR"

for md in "$MAN_SRC_DIR"/*.md; do
    base=$(basename "$md" .md)
    section="${base##*.}"
    name="${base%.*}"
    out="$MAN_OUT_DIR/$name.$section"
    echo "  $md → $out"
    pandoc -s -t man "$md" -o "$out"
done

# ------------------------------------------------------------
# Discover built tools
# ------------------------------------------------------------
echo "[NMS_Tools] Discovering tools..."
TOOLS=$(find "$ROOT_DIR/dist" -maxdepth 1 -type f -name "check_*" -printf "%f\n")
echo "$TOOLS"

# ------------------------------------------------------------
# Version stamping
# ------------------------------------------------------------
BASE_VERSION=$(grep -m1 "Version:" "$SPEC_FILE" | awk '{print $2}')
DATESTAMP=$(date +%Y%m%d)
GIT_HASH=$(git rev-parse --short HEAD)

if [[ "${NIGHTLY:-0}" == "1" ]]; then
    VERSION="${BASE_VERSION}+${DATESTAMP}.git${GIT_HASH}"
else
    VERSION="$BASE_VERSION"
fi

echo "[NMS_Tools] Using version: $VERSION"

sed -i \
    -e "s/{{VERSION}}/${VERSION}/" \
    -e "s/{{BUILD_TYPE}}/${NIGHTLY:-0}/" \
    -e "s/{{BUILD_DATE}}/${DATESTAMP}/" \
    -e "s/{{GIT_HASH}}/${GIT_HASH}/" \
    "$MAN_OUT_DIR/nms-tools.7"

# ------------------------------------------------------------
# Create source tarball (hyphens, matching spec)
# ------------------------------------------------------------
echo "[NMS_Tools] Creating source tarball..."

STAGING_DIR="$(mktemp -d)"
TOP="$STAGING_DIR/nms-tools-$VERSION"

mkdir -p "$TOP"

cp "$ROOT_DIR/LICENSE_BINARY.txt" "$TOP/"
cp "$ROOT_DIR/README.md" "$TOP/"
cp "$ROOT_DIR/LICENSE" "$TOP/"

# Copy binaries
for tool in $TOOLS; do
    cp "$ROOT_DIR/dist/$tool" "$TOP/$tool"
done

# Copy man pages
mkdir -p "$TOP/man/generated"
cp -r "$MAN_OUT_DIR"/* "$TOP/man/generated/"

# Create tarball
TARBALL="$RPMBUILD_DIR/SOURCES/nms-tools-$VERSION.tar.gz"
tar -czf "$TARBALL" -C "$STAGING_DIR" "nms-tools-$VERSION"

rm -rf "$STAGING_DIR"

# ------------------------------------------------------------
# Prepare rpmbuild tree
# ------------------------------------------------------------
cp "$SPEC_FILE" "$RPMBUILD_DIR/SPECS/"
sed -i "s/^Version:.*/Version: ${VERSION}/" "$RPMBUILD_DIR/SPECS/nms-tools.spec"

# ------------------------------------------------------------
# Build RPM
# ------------------------------------------------------------
echo "[NMS_Tools] Running rpmbuild..."
rpmbuild -ba "$RPMBUILD_DIR/SPECS/nms-tools.spec"

mkdir -p "$ROOT_DIR/packaging/output"
find "$RPMBUILD_DIR/RPMS" -name "*.rpm" -exec cp {} "$ROOT_DIR/packaging/output/" \;

# ------------------------------------------------------------
# Optional: rename RPM to underscore format
# ------------------------------------------------------------
for f in "$ROOT_DIR/packaging/output"/nms-tools-*.rpm; do
    base=$(basename "$f")
    new=$(echo "$base" | sed 's/nms-tools-/nms-tools_/')
    mv "$f" "$ROOT_DIR/packaging/output/$new"
done

echo "[NMS_Tools] RPM build complete."
echo "Packages located in: $ROOT_DIR/packaging/output/"
