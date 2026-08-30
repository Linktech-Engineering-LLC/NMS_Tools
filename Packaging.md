# Packaging

**Suite:** NMS_Tools Monitoring Suite
**Maintainer:** Leon McClatchey, Linktech Engineering LLC
**Document Type:** Packaging Guide
**Last Updated:** 2026‑08‑30

## 📘 Table of Contents
1. [Overview](#1-overview)
2. [Build Outputs](#2-build-outputs)
3. [Package Layout](#3-package-layout)
  * [DEB Package](#deb-package-debianubuntu)
  * [RPM Package](#rpm-package-fedorarhelopensuse)
  * [Optional Nagios Plugin Installation](#optional-nagios-plugin-installation)
4. [Building Packages Locally](#4-building-packages-locally)
  * [Build All Binaries](#build-all-binaries)
  * [Build DEB Package](#build-deb-package)
  * [Build RPM Package](#build-rpm-package)
5. [Versioning](#5-versioning)
6. [Nightly Builds](#6-nightly-builds)
7. [Reproducibility](#7-reproducibility)
8. [Customizing Installation Paths](#8-customizing-installation-paths)
  * [DEB](#deb)
  * [RPM](#rpm)
9. [Publishing Releases](#9-publishing-releases)
10. [Notes](#10-notes)

---

## 1. Overview

NMS_Tools is distributed as:

* Standalone Linux binaries (PyInstaller)
* DEB packages (Debian/Ubuntu)
* RPM packages (Fedora/RHEL/openSUSE)
* Nightly builds (binaries + packages + metadata)

This document describes how packages are built, how they are structured, and how to reproduce the packaging process locally.

---

## 2. Build Outputs

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

## 3. Package Layout

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

## 4. Building Packages Locally

### Build all binaries

```bash
./scripts/build_all.sh
```

This produces:

build/linux-x86_64/check_*

### Build DEB package

```bash
./packaging/build_deb.sh
```

### Build RPM package

```bash
./packaging/build_rpm.sh
```

Both scripts:
* Copy binaries into staging directories
* Generate control/spec metadata
* Produce final packages under:
  build/packages/

---

## 5. Versioning

NMS_Tools uses deterministic version stamping:

* Version is defined in `VERSION`
* Build scripts embed the version into:
  * DEB control file
  * RPM spec file
  * Nightly build metadata
  * GitHub release assets

Nightly builds append a timestamp:

1.4.0+nightly.20260524

## 6. Nightly Builds

Nightly builds include:

* All binaries
* DEB/RPM packages
* SHA256 checksums
* Build metadata (commit, timestamp, tool versions)

Published automatically to:

https://linktech-engineering-llc.github.io/NMS_Tools/

---

## 7. Reproducibility

Packaging is designed to be deterministic:

* PyInstaller spec files are curated and tracked in Git
* No auto-generated spec files
* All paths are absolute and stable
* No Python runtime required
* No external dependencies
* Identical builds across machines

---

## 8. Customizing Installation Paths

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

## 9. Publishing Releases

Releases are published via GitHub Actions:

* Tag a version (`v1.4.0`)
* CI builds binaries + packages
* CI uploads release assets
* CI updates nightly dashboard

Manual publishing is also supported via:

./packaging/publish_release.sh

---

## 10. Notes

* All binaries are self-contained and require no Python installation.
* Packaging scripts are idempotent and safe to re-run.
* DEB/RPM metadata follows distro guidelines.
* Nagios plugin installation is fully supported.
