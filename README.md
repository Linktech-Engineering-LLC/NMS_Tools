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
Each tool is built to produce predictable, machine‑readable output suitable for automation, dashboards, and monitoring pipelines.

The suite currently includes certificate inspection, HTML/HTTP validation, interface inspection, port checking, and weather‑based monitoring utilities.

All tools are compiled as standalone binaries using PyInstaller, requiring no Python runtime.

The suite currently includes certificate inspection, HTML/HTTP validation, interface inspection, port checking, and weather‑based monitoring utilities.

---

## Tools in This Suite

| Tool | Description | Documentation |
|------|-------------|---------------|
| **check_cert** | TLS certificate inspection and expiration validation | [src/check_cert/README.md](src/check_cert/README.md) |
| **check_html** | HTTP/HTTPS content validation and deterministic HTML checks | [src/check_html/README.md](src/check_html/README.md) |
| **check_interfaces** | Network interface inspection and operational state reporting | [src/check_interfaces/README.md](src/check_interfaces/README.md) |
| **check_ports** | Port and service availability inspection | [src/check_ports/README.md](src/check_ports/README.md) |
| **check_weather** | Deterministic weather client for monitoring pipelines | [src/check_weather/README.md](src/check_weather/README.md) |

---

## Packaging

NMS_Tools is packaged for Linux environments using native system formats:

* **DEB** packages for Debian/Ubuntu  
* **RPM** packages for Fedora, openSUSE, and RHEL‑based systems  

Packages install cleanly into standard system paths and are suitable for deployment in monitoring environments.

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

### Build all PyInstaller binaries

```Bash
./scripts/build_all.sh
```

Outputs to:

`build/linux-x86_64/`

### Build DEB/RPM packages

```Bash
make packages
```

Outputs to:

```Code
packaging/*.deb
~/rpmbuild/RPMS/noarch/*.rpm
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
scripts/
  build_one.sh
  build_all.sh
packaging/
  debian/
  rpm/
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

