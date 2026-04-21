#!/usr/bin/env bash
set -euo pipefail

echo "[NMS_Tools] Building RPM package..."

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SPEC_FILE="$ROOT_DIR/packaging/rpm/nms_tools.spec"

cd "$ROOT_DIR"

# ------------------------------------------------------------
# Generate man pages (Markdown → groff)
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
# Discover tools dynamically
# ------------------------------------------------------------
echo "[NMS_Tools] Discovering tools..."

TOOLS=$(find "$ROOT_DIR" -maxdepth 1 -type d -name "check_*" -printf "%f\n")

echo "Tools detected:"
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
    "$MAN_OUT_DIR/nms_tools.7"

# ------------------------------------------------------------
# Create source tarball (correct, non-append, RPM-safe)
# ------------------------------------------------------------
echo "[NMS_Tools] Creating source tarball..."

STAGING_DIR="$(mktemp -d)"
cp -r $TOOLS "$STAGING_DIR"/
cp -r "$MAN_OUT_DIR" "$STAGING_DIR"/man

tar -czf "$RPMBUILD/SOURCES/nms_tools-$VERSION.tar.gz" -C "$STAGING_DIR" .

rm -rf "$STAGING_DIR"

# ------------------------------------------------------------
# Prepare rpmbuild tree
# ------------------------------------------------------------
RPMBUILD_DIR="$HOME/rpmbuild"
mkdir -p "$RPMBUILD_DIR"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

cp "$TARBALL" "$RPMBUILD_DIR/SOURCES/"
cp "$SPEC_FILE" "$RPMBUILD_DIR/SPECS/"

# Inject version into spec file copy
sed -i "s/^Version:.*/Version: ${VERSION}/" "$RPMBUILD_DIR/SPECS/nms_tools.spec"

# ------------------------------------------------------------
# Build RPM
# ------------------------------------------------------------
echo "[NMS_Tools] Running rpmbuild..."
rpmbuild -ba "$RPMBUILD_DIR/SPECS/nms_tools.spec"

echo "[NMS_Tools] RPM build complete."
echo "Packages located in: $RPMBUILD_DIR/RPMS/"
