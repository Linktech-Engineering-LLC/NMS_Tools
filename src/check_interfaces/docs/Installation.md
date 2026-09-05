# Installation.md — Deployment & Nagios Integration

**Part of:** NMS_Tools Monitoring Suite  
**Document:** Installation Guide  
**Author:** Leon McClatchey, Linktech Engineering LLC  
**License:** MIT  
**Requires:** Python 3.12+  (development only; not required for frozen binary)
**Last Updated:** 2026‑09-03

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
After installation, verify check_interfaces using the following commands.

### Local Host (Kernel Interface Discovery)
```bash
check_interfaces -H localhost -v
```
Expected: verbose output listing all local interfaces.

### Remote Host (SNMP IF‑MIB Discovery)
```bash
check_interfaces -H switch01.example.com -C public -v
```
Expected: verbose output listing all SNMP‑discovered interfaces.

### Attribute Evaluation Example
```bash
check_interfaces -H switch01 -C public --status linkspeed
```

### Perfdata Example
```bash
check_interfaces -H switch01 -C public --perfdata in_octets
```

### JSON Mode
```bash
check_interfaces -H switch01 -C public -j
```

### Version Check
```bash
check_interfaces -V
```

## 3. See Also
* [Enforcement](Enforcement.md)
* [Metadata_schema](Metadata_schema.md)
* [Enforcement](Enforcement.md)
* [Usage](Usage.md)
* [FLAGS.md](../../../docs/FLAGS.md)
