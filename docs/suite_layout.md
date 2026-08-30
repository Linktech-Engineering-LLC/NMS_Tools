# NMS_Tools Suite Layout

**Suite:** NMS_Tools Monitoring Suite
**Maintainer:** Leon McClatchey, Linktech Engineering LLC
**Document Type:** Suite LayoutSuite Layout
**Last Updated:** 2026‑08‑30

## 📘 Table of Contents
1. [Overview](#1-overview)
2. [Build Output Layout](#2-build-output-layout)
3. [Installation Locations](#3-installation-locations)
4. [Runtime Requirements](#4-runtime-requirements)
5. [Using the Tools](#5-using-the-tools)
6. [Optional Suite Directory](#6-optional-suite-directory)
7. [Man Pages](#7-man-pages)
8. [Support Model](#8-support-model)

## 1. Overview

NMS_Tools is a suite of self‑contained, frozen Linux binaries designed for deterministic, audit‑transparent monitoring in Nagios, Icinga, NRPE, NCPA, and standalone operator workflows.

All tools:
* are distributed as **PyInstaller‑frozen executables**
* require **no Python runtime**
* require **no pip**, **no virtualenv**, and *no external dependencies**
* behave identically across distributions
* support Nagios/Icinga exit codes
* support JSON, verbose, quiet, and machine‑mode output

The suite may be installed as:
* individual binaries
* DEB/RPM packages
* a unified suite directory (optional)

## 2. Build Output Layout
After freezing, all tools are emitted directly into `dist/`:

dist/check_cert
dist/check_html
dist/check_weather
dist/check_ports
dist/check_interfaces
dist/check_ticker

## 3. Installation Locations

### System‑wide (recommended)

/usr/local/bin/

### Nagios plugin directory (optional)

/usr/local/nagios/libexec/

### Suite directory (legacy / optional)

/usr/local/nagios/NMS_Tools/

The suite directory layout is preserved for operators who prefer a single folder containing all tools.

## 4. Runtime Requirements

* Linux (x86_64)
* No Python installation
* No pip
* No virtual environment
* No external dependencies

All tools are fully self‑contained.

## 5. Using the Tools

Tools can be executed directly:

```bash
/usr/local/bin/check_cert --help
```

Or from the suite directory:

```bash
/usr/local/nagios/NMS_Tools/check_cert/check_cert --help
```

Nagios command definitions typically look like:

command[check_cert]=/usr/local/bin/check_cert -H www.example.com

All tools return Nagios‑compatible exit codes:
* `0` `OK`
* `1` `WARNING`
* `2` `CRITICAL`
* `3` `UNKNOWN`

## 6. Optional Suite Directory
If installed as a suite directory, the layout is:

NMS_Tools/
│
├── VERSION
│
├── check_cert
├── check_html
├── check_weather
├── check_ports
├── check_interfaces
├── check_ticker
│
└── man/
    ├── man1/
    └── man7/

This directory is optional and exists only for operators who prefer a unified suite folder.

## 7. Man Pages

If installed, man pages are available under:

man1/   (individual tools)
man7/   (suite overview)

Man pages are optional and included only when requested.

## 8. Support Model

* Tools are designed to run **only as frozen binaries**
* Individual binaries copied out of the suite directory are fully supported
* Python scripts are **not** distributed and **not** supported
* No external dependencies are required
* All tools behave deterministically regardless of installation path