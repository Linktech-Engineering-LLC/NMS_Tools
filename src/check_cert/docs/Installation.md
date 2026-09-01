# Installation Guide — `check_cert.py`

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
After installation, verify check_cert using the following commands.

### Basic Certificate Check
```bash
check_cert -H example.com
```

### Expiry Threshold Check
```bash
check_cert -H example.com --days 30
```

### Verbose Mode
```bash
check_cert -H example.com -v
```

### Version Check
```bash
check_cert -V
```