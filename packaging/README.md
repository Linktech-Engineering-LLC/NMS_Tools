# NMS_Tools Packaging Guide

This directory contains all packaging assets for building DEB and RPM packages
for the NMS_Tools suite. Packaging is fully deterministic, operator‑grade, and
aligned with standard Linux distribution practices.

The packaging system supports:

- Debian / Ubuntu (DEB)
- RHEL / Rocky / Alma / CentOS / Fedora (RPM)
- openSUSE / SLES (RPM)
- Local builds using dpkg-buildpackage and rpmbuild
- Automated builds via build scripts

---

# Directory Structure

packaging/
    debian/               Debian packaging metadata
    rpm/                  RPM spec file
    build_deb.sh          Build script for DEB packages
    build_rpm.sh          Build script for RPM packages
    build_all.sh          Unified build script

---

# Building DEB Packages (Debian / Ubuntu)

## Requirements
- dpkg-dev
- debhelper (compat level 13)
- python3
- python3-requests
- python3-yaml

## Build Steps

From the project root:

```
./packaging/build_deb.sh
```

This script performs:

1. Man page generation (`make man`)
2. Source tarball creation
3. dpkg-buildpackage invocation

Resulting packages appear in the project root:

```
../nms-tools_1.0.0-1_all.deb
```

---

# Building RPM Packages (RHEL / Rocky / Alma / Fedora / openSUSE)

## Requirements
- rpm-build
- python3
- python3-requests
- python3-pyyaml

## Build Steps

From the project root:

```
./packaging/build_rpm.sh
```

This script performs:

1. Man page generation (`make man`)
2. Source tarball creation
3. rpmbuild invocation

Resulting packages appear in:

```
~/rpmbuild/RPMS/noarch/
```

---

# Unified Build (Both RPM and DEB)

To build both formats:

```
./packaging/build_all.sh
```

This runs:

- build_deb.sh
- build_rpm.sh

in sequence.

---

# Installing Packages

## Install DEB (Debian / Ubuntu)

```
sudo dpkg -i nms-tools_1.0.0-1_all.deb
```

## Install RPM (RHEL / Rocky / Alma / Fedora / openSUSE)

```
sudo rpm -ivh nms_tools-1.0.0-1.noarch.rpm
```

---

# Installed File Layout

Executables:

```
/usr/bin/check_ports
/usr/bin/check_weather
/usr/bin/check_cert
/usr/bin/check_html
/usr/bin/check_interfaces
```

Man pages:

```
/usr/share/man/man1/*.1.gz
/usr/share/man/man7/nms_tools.7.gz
```

Optional logs (if configured):

```
/var/log/nms_tools/
```

---

# Notes

- Man pages are generated from Markdown sources in the `man/` directory.
- The Makefile handles Markdown → groff conversion.
- Packaging scripts assume the repository root contains the Makefile.
- No systemd units or services are installed (NMS_Tools is CLI‑only).

---

# Maintainer

Leon McClatchey  
Linktech Engineering  
