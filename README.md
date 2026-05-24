# NMS_Tools  
Deterministic, operator‑grade monitoring tools for Linux and Nagios environments.

![Linktech Engineering](https://img.shields.io/badge/LINKTECH%20ENGINEERING-gray)
![Tools Suite](https://img.shields.io/badge/TOOLS%20SUITE-purple)
![Status](https://img.shields.io/badge/STATUS-ACTIVE-brightgreen)
![License](https://img.shields.io/badge/LICENSE-MIT-blue)
![Python](https://img.shields.io/badge/PYTHON-3.12%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Linux-blue)
![Packages](https://img.shields.io/badge/Packages-DEB%20%7C%20RPM-orange)
![Nightly Build](https://img.shields.io/badge/Nightly%20Build-passing-brightgreen)
![Dashboard](https://img.shields.io/badge/Nightly-Dashboard-blue)

---

## Overview

**NMS_Tools** is a suite of deterministic, operator‑grade monitoring and inspection utilities designed for Linux and Nagios‑based environments.  
Each tool is built to produce predictable, machine‑readable output suitable for automation, dashboards, and monitoring pipelines.

The suite currently includes certificate inspection, HTML/HTTP validation, interface inspection, port checking, and weather‑based monitoring utilities.

All tools are compiled as standalone binaries using PyInstaller, requiring no Python runtime.

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

- **DEB** packages for Debian/Ubuntu  
- **RPM** packages for Fedora, openSUSE, and RHEL‑based systems  

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

## Nightly Dashboard

A nightly build dashboard is published via GitHub Pages and includes:

* Latest build status
* Version and commit information
* Download links for DEB/RPM packages
* Checksums
* Recent changes

**Nightly Dashboard:**
https://linktech-engineering-llc.github.io/NMS_Tools/

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

## Philosophy

NMS_Tools is built around a few core principles:

- **Determinism** — predictable, stable output suitable for automation  
- **Operator‑grade design** — tools that behave consistently under load and in production  
- **Linux‑first** — designed for real systems, not cross‑platform abstraction  
- **Nagios‑friendly** — output formats and behaviors that integrate cleanly with monitoring systems  

---

## Contributing

Contributions are welcome.  
Please keep submissions:

- Deterministic  
- Lightweight  
- Operationally focused  
- Consistent with the suite’s monitoring philosophy  

---

## License

MIT License  
See [LICENSE] for details.

