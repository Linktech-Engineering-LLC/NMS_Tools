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
3. [See Also](#3-see-also)

---

## 1. Installation
Installation, deployment, Nagios integration, NRPE configuration, logging setup, SELinux notes, and troubleshooting are documented centrally:

**See:** [NMS_Tools/docs/Installation.md](../../../docs/Installation.md)

All NMS_Tools binaries share the same installation and deployment model.

---

## 2. Tool Verification
After installation, verify check_html using the following commands.

### Basic Port Check
```bash
check_ports -H http://example.com -p 22
```

### Multiple Ports
```bash
check_ports -H example.com -p 22,80,443
```

### Verbose Mode
```bash
check_ports -H example.com -p 443 -v
```

### JSON Mode
```bash
check_ports -H example.com -p 443 -j | jq
```

### Version Check
```bash
check_ports -V
```

## 3. See Also
* [Enforcement](Enforcement.md)
* [Metadata_schema](Metadata_schema.md)
* [Operation](Operation.md)
* [Usage](Usage.md)
* [FLAGS.md](../../../docs/FLAGS.md)
