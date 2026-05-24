# Packaging

## Overview

NMS_Tools is distributed as:

- Standalone Linux binaries (PyInstaller)
- DEB packages (Debian/Ubuntu)
- RPM packages (Fedora/RHEL/openSUSE)
- Nightly builds (binaries + packages + metadata)

This document describes how packages are built, how they are structured, and how to reproduce the packaging process locally.

---

## Build Outputs

All build artifacts are placed under:

build/
linux-x86_64/     # Final PyInstaller binaries
temp/             # PyInstaller working directory
packages/         # DEB/RPM output


Each tool produces a single self-contained binary:

check_cert
check_html
check_interfaces
check_ports
check_weather


---

## Package Layout

### DEB Package (Debian/Ubuntu)

/usr/bin/check_cert
/usr/bin/check_html
/usr/bin/check_interfaces
/usr/bin/check_ports
/usr/bin/check_weather
/usr/share/doc/nms-tools/
/usr/share/licenses/nms-tools/


### RPM Package (Fedora/RHEL/openSUSE)

/usr/bin/check_cert
/usr/bin/check_html
/usr/bin/check_interfaces
/usr/bin/check_ports
/usr/bin/check_weather
/usr/share/doc/nms_tools/
/usr/share/licenses/nms_tools/


### Optional Nagios Plugin Installation

Packages may optionally install tools into:

/usr/local/nagios/libexec/


or:

/usr/local/nagios/libexec/NMS_Tools/


This is controlled by the packaging spec and can be toggled per environment.

---

## Building Packages Locally

### 1. Build all binaries

```bash
./scripts/build_all.sh
```

This produces:

build/linux-x86_64/check_*

### 2. Build DEB package

```bash
./packaging/build_deb.sh
```

### 3. Build RPM package

```bash
./packaging/build_rpm.sh
```

Both scripts:
* Copy binaries into staging directories
* Generate control/spec metadata
* Produce final packages under:
  build/packages/

---

## Versioning

NMS_Tools uses deterministic version stamping:

* Version is defined in VERSION
* Build scripts embed the version into:
  * DEB control file
  * RPM spec file
  * Nightly build metadata
  * GitHub release assets

Nightly builds append a timestamp:

1.4.0+nightly.20260524

## Nightly Builds

Nightly builds include:

* All binaries
* DEB/RPM packages
* SHA256 checksums
* Build metadata (commit, timestamp, tool versions)

Published automatically to:

https://linktech-engineering-llc.github.io/NMS_Tools/

---

## Reproducibility

Packaging is designed to be deterministic:

* PyInstaller spec files are curated and tracked in Git
* No auto-generated spec files
* All paths are absolute and stable
* No Python runtime required
* No external dependencies
* Identical builds across machines

---

## Customizing Installation Paths

To install tools into a Nagios plugin directory, modify:

### DEB

[DEBIAN/install]

### RPM

[nms_tools.spec]

Example:

/usr/local/nagios/libexec/NMS_Tools/check_cert

This allows packaging for:

* Nagios Core
* Icinga
* Naemon
* NRPE/NCPA agents

---

## Publishing Releases

Releases are published via GitHub Actions:

* Tag a version (v1.4.0)
* CI builds binaries + packages
* CI uploads release assets
* CI updates nightly dashboard

Manual publishing is also supported via:

./packaging/publish_release.sh

## Notes

* All binaries are self-contained and require no Python installation.
* Packaging scripts are idempotent and safe to re-run.
* DEB/RPM metadata follows distro guidelines.
* Nagios plugin installation is fully supported.
