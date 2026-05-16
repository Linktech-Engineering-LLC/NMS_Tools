# NMS_Tools  
Deterministic, operator‑grade monitoring tools for Linux and Nagios environments.

![Linktech Engineering](https://img.shields.io/badge/LINKTECH%20ENGINEERING-gray)
![Tools Suite](https://img.shields.io/badge/TOOLS%20SUITE-purple)
![Status](https://img.shields.io/badge/STATUS-ACTIVE-brightgreen)
![License](https://img.shields.io/badge/LICENSE-MIT-blue)
![Python](https://img.shields.io/badge/PYTHON-3.10%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Linux-blue)
![Packages](https://img.shields.io/badge/Packages-DEB%20%7C%20RPM-orange)
![Nightly Build](https://img.shields.io/badge/Nightly%20Build-passing-brightgreen)
![Build Packages](https://img.shields.io/badge/Build%20NMS_Tools%20Packages-passing-brightgreen)
![Dashboard](https://img.shields.io/badge/Nightly-Dashboard-blue)

---

## Overview

**NMS_Tools** is a suite of deterministic, operator‑grade monitoring and inspection utilities designed for Linux and Nagios‑based environments.  
Each tool is built to produce predictable, machine‑readable output suitable for automation, dashboards, and monitoring pipelines.

The suite currently includes certificate inspection, HTML/HTTP validation, interface inspection, port checking, and weather‑based monitoring utilities.

---

## Tools in This Suite

### **check_cert**
TLS certificate inspection and validation tool.  
Designed for monitoring certificate expiration, chain validation, and operational readiness.

→ See: `check_cert/README.md`

---

### **check_html**
HTTP/HTTPS content validation tool.  
Performs deterministic checks on status codes, headers, and HTML content.

→ See: `check_html/README.md`

---

### **check_interfaces**
Network interface inspection tool.  
Reports interface state, IP configuration, carrier status, and operational metrics.

→ See: `check_interfaces/README.md`

---

### **check_ports**
Port and service inspection tool.  
Validates port availability, service responsiveness, and connection behavior.

→ See: `check_ports/README.md`

---

### **check_weather**
Weather client for monitoring pipelines and dashboards.  
Provides deterministic current, hourly, and weekly forecasts with normalized output.

→ See: `check_weather/README.md`

---

## Packaging

NMS_Tools is packaged for Linux environments using native system formats:

- **DEB** packages for Debian/Ubuntu  
- **RPM** packages for Fedora, openSUSE, and RHEL‑based systems  

Packages install cleanly into standard system paths and are suitable for deployment in monitoring environments.

---

## Installation

NMS_Tools can be deployed as a complete suite using the included `install.sh` script.  
A detailed installation guide is available in `Installation.md`.

Each tool may also be installed independently if only specific functionality is required.

--- 

## Nightly Dashboard

A nightly build dashboard is published via GitHub Pages and includes:

- Latest build status  
- Version and commit information  
- Download links for DEB/RPM packages  

**(Link will appear here once GitHub Pages is active)**  
`https://linktech-engineering-llc.github.io/NMS_Tools/`

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
See `LICENSE` for details.
