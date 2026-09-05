# check_html.py — Installation Guide

**Part of:** NMS_Tools Monitoring Suite  
**Document:** Installation Guide  
**Author:** Leon McClatchey, Linktech Engineering LLC  
**License:** MIT  
**Requires:** Python 3.12+  (development only; not required for frozen binary)
**Last Updated:** 2026‑08‑17

## Table of Contents
1. [Installation](#1-installation)
2. [Tool Verification](#2-tool-verification)
3. [Documents](#3-documents)

---

## 1. Installation
Installation, deployment, Nagios integration, NRPE configuration, logging setup, SELinux notes, and troubleshooting are documented centrally:

**See:** [NMS_Tools/docs/Installation.md](../../../docs/Installation.md)

All NMS_Tools binaries share the same installation and deployment model.

---

## 2. Tool Verification
After installation, verify check_html using the following commands.

### Universal Location Check (Recommended)
`-l` accepts any supported location format:
ZIP, city/state, or latitude/longitude.
Additional flags are available and documented in check_weather `-h`.
```bash
check_weather -l "New York, NY"
check_weather -l 10001
check_weather -l "40.7128,-74.0060"
```

### Verbose Mode
```bash
check_weather -l "New York, NY" -v
```

### JSON Mode
```bash
check_weather -l "New York, NY" -j 
```

### Version Check
```bash
check_weather -V
```

## 3. Documents
* [CHANGELOG](CHANGELOG.md)
* [Architecture](Architecture.md)
* [FLAGS.md](../../../docs/FLAGS.md)
* [Enforcement](Enforcement.md)
* [Logging](Logging.md)
* [Operation](Operation.md)
* [Provider_Architecture](Provider_Architecture.md)
* [Usage](Usage.md)
