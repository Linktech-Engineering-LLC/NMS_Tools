# check_html.py — Installation Guide

**Part of:** NMS_Tools Monitoring Suite  
**Document:** Installation Guide  
**Author:** Leon McClatchey, Linktech Engineering LLC  
**License:** MIT  
**Requires:** Python 3.12+  (development only; not required for frozen binary)
**Last Updated:** 2026‑08‑17

## Table of Contents
1. Installation
2. Tool Verification

---

## 1. Installation
Installation, deployment, Nagios integration, NRPE configuration, logging setup, SELinux notes, and troubleshooting are documented centrally:

**See:** [NMS_Tools/docs/Installation.md](../../../docs/Installation.md)

All NMS_Tools binaries share the same installation and deployment model.

---

## 2. Tool Verification
After installation, verify check_html using the following commands.

### Basic Ticker Check
```bash
check_ticker AAPL
```

### Trend Analysis
```bash
check_ticker AAPL --trend
```

### History Window
```bash
check_ticker AAPL --history 5
```

### Verbose Mode
```bash
check_ticker AAPL -v
```

### JSON Mode
```bash
check_ticker AAPL -j
```

### Version Check
```bash
check_ticker -V
```
