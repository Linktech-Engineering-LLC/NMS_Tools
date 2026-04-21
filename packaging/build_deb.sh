#!/usr/bin/env bash
set -euo pipefail

echo "[NMS_Tools] Building DEB package..."

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEBIAN_DIR="$ROOT_DIR/packaging/debian"
PKG_NAME="nms-tools"

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
# Prepare DEB staging directory
# ------------------------------------------------------------
STAGE="$DEBIAN_DIR/$PKG_NAME"
rm -rf "$STAGE"
mkdir -p "$STAGE/DEBIAN"
mkdir -p "$STAGE/usr/local/bin"
mkdir -p "$STAGE/usr/share/man/man1"
mkdir -p "$STAGE/usr/share/man/man7"

# Copy control file template
cp "$DEBIAN_DIR/control" "$STAGE/DEBIAN/control"

# ------------------------------------------------------------
# Version stamping (AFTER staging exists)
# ------------------------------------------------------------
BASE_VERSION=$(grep -m1 "^Version:" "$DEBIAN_DIR/control" | awk '{print $2}')
DATESTAMP=$(date +%Y%m%d)
GIT_HASH=$(git rev-parse --short HEAD)

if [[ "${NIGHTLY:-0}" == "1" ]]; then
    VERSION="${BASE_VERSION}+${DATESTAMP}.git${GIT_HASH}"
else
    VERSION="$BASE_VERSION"
fi

echo "[NMS_Tools] Using version: $VERSION"

# Inject version into staged DEBIAN/control
sed -i "s/^Version:.*/Version: ${VERSION}/" "$STAGE/DEBIAN/control"
sed -i \
    -e "s/{{VERSION}}/${VERSION}/" \
    -e "s/{{BUILD_TYPE}}/${NIGHTLY:-0}/" \
    -e "s/{{BUILD_DATE}}/${DATESTAMP}/" \
    -e "s/{{GIT_HASH}}/${GIT_HASH}/" \
    "$MAN_OUT_DIR/nms_tools.7"

# ------------------------------------------------------------
# Install tools dynamically
# ------------------------------------------------------------
echo "[NMS_Tools] Installing tools..."

for tool in $TOOLS; do
    script="$tool/$tool.py"
    if [[ -f "$script" ]]; then
        echo "  Installing $script"
        install -m 0755 "$script" "$STAGE/usr/local/bin/"
    fi
done

# ------------------------------------------------------------
# Install generated man pages
# ------------------------------------------------------------
echo "[NMS_Tools] Installing man pages..."

for manfile in "$MAN_OUT_DIR"/*.1; do
    install -m 0644 "$manfile" "$STAGE/usr/share/man/man1/"
done

for manfile in "$MAN_OUT_DIR"/*.7; do
    install -m 0644 "$manfile" "$STAGE/usr/share/man/man7/"
done

gzip -9 "$STAGE/usr/share/man/man1/"*.1
gzip -9 "$STAGE/usr/share/man/man7/"*.7

# ------------------------------------------------------------
# Build DEB package
# ------------------------------------------------------------
echo "[NMS_Tools] Building DEB package..."

cd "$DEBIAN_DIR"
dpkg-deb --build "$PKG_NAME" "../nms-tools_${VERSION}.deb"

echo "[NMS_Tools] DEB build complete."
echo "Package located at: $DEBIAN_DIR/../nms-tools_${VERSION}.deb"
