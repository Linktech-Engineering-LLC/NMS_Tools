# check_ports — Usage Guide

**Part of:** NMS_Tools Monitoring Suite  
**Document:** Usage Guide  
**Author:** Leon McClatchey, Linktech Engineering LLC  
**License:** MIT  
**Requires:** Python 3.12+  (development only; not required for frozen binary)
**Last Updated:** 2026‑09-03

## Table of Contents
1. [Overview](#1-overview)
2. [Basic Usage](#2-basic-usage)
3. [Port Selection](#3-port-selection)
4. [Service Resolution](#4-service-resolution)
5. [Enforcement Flags](#5-enforcement-flags)
6. [Output Modes](#6-output-modes)
7. [Examples](#7-examples)
8. [Notes](#8-notes)
9. [See Also](#9-see-also)

---

## 1. Overview

`check_ports` performs deterministic TCP port reachability checks and returns Nagios‑compatible exit codes.
It supports:
* explicit port lists
* service‑to‑port resolution
* rule‑based enforcement
* verbose and JSON output modes
* quiet/Nagios modes for monitoring systems

This guide describes the user‑facing usage patterns.

---

## 2. Basic Usage

The simplest invocation checks one or more ports on a host:
```bash
check_ports -H example.com -p 22
```
If multiple ports are provided:
```bash
check_ports -H example.com -p 22,80,443
```
The tool attempts a TCP connection to each port and reports:
* **open**
* **closed**
* **timeout**

Severity is determined by enforcement rules.

---

## 3. Port Selection

### Explicit Ports
Use `-p` or `--ports`:
```bash
check_ports -H example.com -p 22,443
```
Ports may be comma‑separated or space‑separated.

### Service Names
Use --service to resolve known services to ports:
```bash
check_ports -H example.com --service ssh
```
Multiple services are allowed:
```bash
check_ports -H example.com --service ssh --service http
```

### Combined
Explicit ports and service names may be mixed:
```bash
check_ports -H example.com -p 22 --service http
```
All ports are merged, deduplicated, and sorted.

---

## 4. Service Resolution
Service names map to ports using the tool’s internal service table.

Examples:

| Service | Port |
| --- | --- |
| ssh | 22 |
| http | 80 |
| https | 443 |
| smtp | 25 |

Unknown services produce an UNKNOWN state.

Resolved ports are stored in:
* service_requested
* service_ports
* all_ports

---

## 5. Enforcement Flags
`check_ports` supports rule‑based enforcement:

### require_all
All ports must succeed:
```bash
check_ports -H example.com -p 22,80 --require-all
```
Any failure → **CRITICAL**.

### require_any
At least one port must succeed:
```bash
check_ports -H example.com -p 22,80 --require-any
```
All failures → **CRITICAL**.

### fail_only
Only failures matter:
```bash
check_ports -H example.com -p 22,80 --fail-only
```
Successes do not affect severity.

---

## 6. Output Modes
### Normal Mode
Human‑readable summary:
```bash
check_ports -H example.com -p 22
```

### Verbose Mode
Expanded detail:
```bash
check_ports -H example.com -p 22 -v
```

### JSON Mode
Structured JSON output:
```bash
check_ports -H example.com -p 22 -j
```

### Quiet Mode
Exit code only:
```bash
check_ports -H example.com -p 22 -q
```

### Nagios Mode
Single‑line output + exit code:
```bash
check_ports -H example.com -p 22 --nagios
```

---

## 7. Examples
### Check SSH
```bash
check_ports -H example.com --service ssh
```

### Check HTTPS
```bash
check_ports -H example.com --service https
```

### Check Multiple Ports
```bash
check_ports -H example.com -p 22,80,443
```

### Require All Ports to Succeed
```bash
check_ports -H example.com -p 22,443 --require-all
```

### Require At Least One Success
```bash
check_ports -H example.com -p 22,443 --require-any
```

### Verbose Output
```bash
check_ports -H example.com -p 22 -v
```

#### JSON Output
```bash
check_ports -H example.com -p 22 -j
```

### Version
```bash
check_ports -V
```

---

## 8. Notes
* Port resolution is deterministic and logged in verbose mode.
* Enforcement is rule‑based, not drift‑based.
* JSON mode includes metadata, results, and enforcement.
* Nagios mode suppresses logs but performs full enforcement.
* Invalid ports or unknown services produce `UNKNOWN` state.

---

## 9. See Also
* [Installation](Installation.md)
* [Enforcement](Enforcement.md)
* [Metadata_schema](Metadata_schema.md)
* [Operation](Operation.md)
* [FLAGS.md](../../../docs/FLAGS.md)
