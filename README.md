# NMS_Tools  
Deterministic, operator‑grade monitoring tools for Linux and Nagios environments.

<!-- Branding -->
[![Linktech Engineering](https://img.shields.io/badge/LINKTECH%20ENGINEERING-gray)](https://github.com/Linktech-Engineering-LLC)
![Tools Suite](https://img.shields.io/badge/TOOLS%20SUITE-purple)
![Status](https://img.shields.io/badge/STATUS-ACTIVE-brightgreen)
![Source License: MIT](https://img.shields.io/badge/Source%20License-MIT-green?style=flat-square)
![Binary License: Proprietary](https://img.shields.io/badge/Binary%20License-Proprietary-red?style=flat-square)

<!-- Technical -->
![Python](https://img.shields.io/badge/PYTHON-3.12%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Linux-blue)
![Packages](https://img.shields.io/badge/Packages-DEB%20%7C%20RPM-orange)

<!-- Build Status -->
[![Nightly Build](https://github.com/Linktech-Engineering-LLC/NMS_Tools/actions/workflows/nightly.yml/badge.svg)](https://github.com/Linktech-Engineering-LLC/NMS_Tools/actions/workflows/nightly.yml)
[![Stable Build](https://github.com/Linktech-Engineering-LLC/NMS_Tools/actions/workflows/release.yml/badge.svg)](https://github.com/Linktech-Engineering-LLC/NMS_Tools/actions/workflows/release.yml)

<!-- Dashboards -->
[![Nightly Dashboard](https://img.shields.io/badge/Nightly-Dashboard-blue)](https://linktech-engineering-llc.github.io/NMS_Tools/)
[![Stable Dashboard](https://img.shields.io/badge/Stable-Dashboard-green)](https://linktech-engineering-llc.github.io/NMS_Tools/stable/)

<!-- Versions -->
[![Latest Release](https://img.shields.io/github/v/release/Linktech-Engineering-LLC/NMS_Tools)](https://github.com/Linktech-Engineering-LLC/NMS_Tools/releases/latest)
![Nightly Version](https://img.shields.io/badge/Nightly-latest-blue)

---

## Overview

**NMS_Tools** is a suite of deterministic, operator‑grade monitoring and inspection utilities designed for Linux and Nagios‑based environments.
Each tool produces predictable, machine‑readable output suitable for automation, dashboards, and monitoring pipelines.

The suite includes:

* TLS certificate inspection
* HTML/HTTP validation
* network interface inspection
* port/service availability checks
* deterministic weather ingestion
* market/ticker analysis (via PythonTools finance subsystem)

All tools are compiled as standalone PyInstaller binaries requiring no Python runtime.
This ensures consistent behavior across distributions, monitoring systems, and automation pipelines.

---

## Tools in This Suite

| Tool | Description | Documentation |
|------|-------------|---------------|
| **check_cert** | TLS certificate inspection and expiration validation | [src/check_cert/README.md](src/check_cert/README.md) |
| **check_html** | HTTP/HTTPS content validation and deterministic HTML checks | [src/check_html/README.md](src/check_html/README.md) |
| **check_interfaces** | Network interface inspection and operational state reporting | [src/check_interfaces/README.md](src/check_interfaces/README.md) |
| **check_ports** | Port and service availability inspection | [src/check_ports/README.md](src/check_ports/README.md) |
| **check_weather** | Deterministic weather client for monitoring pipelines | [src/check_weather/README.md](src/check_weather/README.md) |
| **check_ticker** | Deterministic market/ticker client using PythonTools finance providers | [src/check_ticker/README.md](src/check_ticker/README.md)

---

## Packaging

NMS_Tools is distributed in multiple formats to support diverse deployment environments:

### DEB (Debian/Ubuntu)
Native packaging for Debian‑based systems.

### RPM (Fedora/RHEL/openSUSE)
Native packaging for RPM‑based systems.

### TGZ (Portable Archive)
A portable, installation‑free archive containing all binaries and runtime directories.
Ideal for embedded systems, containers, and custom deployments.

### ZIP (Portable Archive)
Windows‑friendly and cross‑platform archive format for tooling pipelines and CI/CD systems.

All packaging formats include:
* standalone PyInstaller binaries
* deterministic directory layout
* logging directories
* configuration directories
* schema bundles (where applicable)

---

## Installation

NMS_Tools is distributed as:

### **Standalone binaries (PyInstaller)**
Download from the GitHub Releases page:

https://github.com/Linktech-Engineering-LLC/NMS_Tools/releases

Each tool is a self‑contained executable requiring no Python installation.

### **DEB package (Debian/Ubuntu)**

```bash
sudo dpkg -i nms-tools_<version>.deb
```

### **RPM package (Fedora/RHEL/openSUSE)**

```bash
sudo rpm -i nms_tools-<version>-1.noarch.rpm
```

### TGZ (Portable)

```bash
tar -xzf nms_tools-<version>.tgz
./nms_tools/check_cert --help
```

### ZIP (Portable)

```bash
unzip nms_tools-<version>.zip
./nms_tools/check_cert --help
```

--- 

## Dashboards

### Nightly Dashboard

Live rolling builds with metadata, checksums, and artifacts:
https://linktech-engineering-llc.github.io/NMS_Tools/

### Stable Dashboard

Versioned, immutable release builds:
https://linktech-engineering-llc.github.io/NMS_Tools/stable/

## Downloads

**Stable releases:**
https://github.com/Linktech-Engineering-LLC/NMS_Tools/releases

**Nightly builds:**
https://linktech-engineering-llc.github.io/NMS_Tools/

## Building From Source

NMS_Tools uses a two‑stage build system:

---

### Stage 1 — Freeze all tools (PyInstaller)

The freeze step is performed by the executable build script:

```bash
./scripts/build.py
```

This script:
* freezes every tool into a standalone PyInstaller binary
* validates directory layout
* ensures PythonTools is installed in the active venv
* writes all binaries to:

```Code
dist/
```

**PythonTools must be installed in the current virtual environment before running this step.**

Install PythonTools:

```bash
pip install PythonTools
```

or from source:

```bash
cd ../PythonTools
pip install .
```

### Stage 2 — Full packaging (DEB, RPM, TGZ, ZIP)

The full packaging pipeline is executed via:

```bash
packaging/build_all.sh
```

This script:

1. **automatically** calls `./scripts/build.py` to freeze all tools
2. assembles DEB packages
3. assembles RPM packages
4. creates TGZ portable archives
5. creates ZIP portable archives
6. copies frozen binaries into the correct packaging layout
7. writes all final artifacts to:

```Code
packaging/output/
```

This is the same packaging model used by RunUpdates and PythonTools.

#### Building a single tool (freeze only)

```bash
./scripts/build.py --tool check_cert
```

#### Building archives only (after freeze)

```bash
packaging/build_all.sh --archives
```

#### Building DEB/RPM only (after freeze)

```bash
packaging/build_all.sh --packages
```

---

## Repository Structure

```Code
src/
  check_cert/
  check_html/
  check_interfaces/
  check_ports/
  check_weather/
  check_ticker/
scripts/
  build.py
packaging/
  debian/
  rpm/
  output/
.github/
  workflows/
```

---

## Quick Start

NMS_Tools provides deterministic, standalone monitoring utilities that behave consistently across environments.  
Each tool is a single PyInstaller‑compiled binary with predictable exit codes and machine‑readable output.

### Check a TLS certificate

```bash
check_cert --host example.com --port 443
```

### Validate HTML/HTTP content

```bash
check_html --url https://example.com --expect-title "Example Domain"
```

### Inspect network interfaces

```bash
check_interfaces
```

### Check port availability

```bash
check_ports --host 192.168.1.10 --port 22
```

### Query deterministic weather data

```bash
check_weather --city "Wichita, KS"
```

### Market/ticker

```bash
check_ticker AAPL --history 5 --trend
```

All tools return Nagios‑compatible exit codes (0=OK, 1=WARNING, 2=CRITICAL, 3=UNKNOWN) and structured output suitable for automation, dashboards, and monitoring pipelines.

---

## Why NMS_Tools?

Traditional monitoring scripts often suffer from:

* inconsistent output formats  
* reliance on system Python installations  
* unpredictable behavior across distributions  
* non‑deterministic parsing  
* ad‑hoc logic that breaks under load  

NMS_Tools solves these problems by providing:

### **Deterministic Output**
Every tool produces stable, machine‑readable output designed for automation, dashboards, and monitoring pipelines.

### **Standalone Binaries**
All tools are compiled with PyInstaller — no Python runtime, no dependency drift, no environment issues.

### **Operator‑Grade Behavior**
Tools are designed for real production environments:
* consistent exit codes  
* predictable failure modes  
* clear error messages  
* stable CLI interfaces  

### **Linux‑First Design**
NMS_Tools targets real Linux systems, not cross‑platform abstractions.  
Packaging is native (`DEB` and `RPM`), and behavior is tuned for operational reliability.

### **Nagios‑Friendly**
Output formats, exit codes, and CLI patterns integrate cleanly with:
* Nagios  
* Icinga  
* Sensu  
* Zabbix  
* custom monitoring pipelines  

NMS_Tools is built for operators who need tools that behave the same way every time — no surprises, no guesswork.

---

## Project Ecosystem

NMS_Tools is part of the **Linktech Engineering Tools Suite**, alongside:
* **PythonTools** — deterministic foundation library
* **RunUpdates** — update orchestration
* **TimerDeck** — systemd automation
* **VSCode-Updater** — editor update automation
* **BotScanner** — security analysis

NMS_Tools relies heavily on **PythonTools** for:
* deterministic subprocess execution
* unified logging
* schema loading
* finance/ticker provider architecture
* trend analysis
* frozen‑bundle compatibility

Together, these projects form a cohesive ecosystem of operator‑grade automation tools.

---

## Philosophy

NMS_Tools is built around a few core principles:

* **Determinism** — predictable, stable output suitable for automation  
* **Operator‑grade design** — tools that behave consistently under load and in production  
* **Linux‑first** — designed for real systems, not cross‑platform abstraction  
* **Nagios‑friendly** — output formats and behaviors that integrate cleanly with monitoring systems  

---

## Contributing

Contributions are welcome.  
Please keep submissions:

* Deterministic  
* Lightweight  
* Operationally focused  
* Consistent with the suite’s monitoring philosophy  

See [CONTRIBUTING](CONTRIBUTING.md) for details.

---

## License

MIT License  
See [LICENSE](LICENSE) for details.

