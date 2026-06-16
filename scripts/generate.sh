#!/bin/bash

VERSION="local-test"
COMMIT="abcdef1"
DATESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
PYI_VERSION=$(pyinstaller --version 2>/dev/null || echo "none")

mkdir -p dashboard

cat > metadata.json <<EOF
{
  "meta_version": 2,
  "build": {
    "date": "${DATESTAMP}",
    "commit": "${COMMIT}",
    "version": "${VERSION}",
    "branch": "local",
    "workflow_run_id": "0"
  },
  "toolchain": {
    "python": "$(python3 --version | awk '{print $2}')",
    "pyinstaller": "${PYI_VERSION}"
  },
  "artifacts": [
EOF

FIRST=true
for f in artifacts/*; do
  [ -f "$f" ] || continue
  NAME=$(basename "$f")
  SIZE=$(stat -c%s "$f")
  SHA256=$(sha256sum "$f" | awk '{print $1}')
  CRC32=$(crc32 "$f" 2>/dev/null || echo "00000000")

  TYPE="unknown"
  OS="unknown"
  ARCH="unknown"

  case "$NAME" in
    *.zip) TYPE="zip"; OS="any"; ARCH="any" ;;
    *.tgz) TYPE="tgz"; OS="any"; ARCH="any" ;;
    *.deb) TYPE="deb"; OS="linux"; ARCH="amd64" ;;
    *.rpm) TYPE="rpm"; OS="linux"; ARCH="x86_64" ;;
  esac

  if [ "$FIRST" = true ]; then
    FIRST=false
  else
    echo "," >> metadata.json
  fi

  cat >> metadata.json <<EOF
    {
      "name": "${NAME}",
      "size": ${SIZE},
      "sha256": "${SHA256}",
      "crc32": "${CRC32}",
      "type": "${TYPE}",
      "os": "${OS}",
      "arch": "${ARCH}"
    }
EOF
done

echo "  ]" >> metadata.json
echo "}" >> metadata.json
