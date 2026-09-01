# Usage.md — CLI Reference & Examples

**Part of:** NMS_Tools Monitoring Suite  
**Document:** Usage Guide  
**Author:** Leon McClatchey, Linktech Engineering LLC  
**License:** MIT  
**Requires:** Python 3.12+  (development only; not required for frozen binary)
**Last Updated:** 2026‑08‑17

## Table of Contents
1. [Overview](#1-overview)
2. [Synopsis](#2-synopsis)
3. [Required Arguments](#3-required-arguments)
4. [Core Options](#4-core-options)
5. [SNMP Options](#5-snmp-options)
6. [Evaluation](#6-evaluation)
    [1. Evaluation Attributes](#61-evaluation-attributes)
7. [Perfdata Metrics](#7-perfdata-metrics)
8. [Filtering & Selection](#8-filtering--selection)
9. [Output Modes](#9-output-modes)
10. [Logging](#10-logging)
11. [General](#11-general)
12. [Examples](#12-examples)
13. [Exit Codes](#13-exit-codes)
14. [See Also](#14-see-also)

---

## 1. Overview

This document describes the command‑line interface for `check_interfaces`, including:
* required and optional flags
* SNMP parameters
* evaluation attributes
* filtering and selection rules
* output modes
* logging behavior
* perfdata selection
* complete usage examples

For runtime behavior, see [Operation.md](Operation.md).
For evaluation rules, see [Enforcement.md](Enforcement.md).
For JSON schema, see [Metadata_schema.md](Metadata_schema.md).

---

## 2. Synopsis
```bash
check_interfaces.py -H <host> [options]
```
The -H target determines local vs SNMP mode automatically.

---

## 3. Required Arguments

| Flag            | Description                                                            |
|-----------------|------------------------------------------------------------------------|
| -H, --host      | Target hostname or IP address. Determines local vs remote detection automatically. A resolvable hostname is required. |

---

## 4. Core Options

| Flag                | Description                                      | Default |
|---------------------|--------------------------------------------------|---------|
| -t, --timeout       | General connection timeout in seconds            | 5       |
| --log-dir DIR       | Directory to store logs (verbose/JSON only)      | —       |
| --log-max-mb MB     | Maximum log size before rotation                 | 50      |

Logging is disabled in Nagios mode.

---

## 5. SNMP Options

Required for remote hosts. Ignored when the target is detected as local.

| Flag                    | Description                                           | Default |
|-------------------------|-------------------------------------------------------|---------|
| -C, --community         | SNMPv2c community string (required for remote hosts) | —       |
| -p, --snmp-port         | SNMP port                                             | 161     |
| -T, --snmp-timeout      | SNMP timeout; overrides --timeout for SNMP           | —       |

---

## 6. Evaluation

| Flag               | Description                                                        | Default        |
|--------------------|--------------------------------------------------------------------|----------------|
| --status <attr>    | Attribute to evaluate on each interface                            | oper-status    |

### 6.1 Evaluation Attributes

| Value          | Meaning                                                                |
|----------------|------------------------------------------------------------------------|
| oper-status    | Operational status (is the interface up?)                              |
| admin-status   | Administrative status (is the interface enabled?)                      |
| linkspeed      | Negotiated link speed (non-zero required)                              |
| duplex         | Duplex mode (full required; bridges pass automatically)                |
| mtu            | MTU value (must be > 0)                                                |
| alias          | Alias identity (fails if interface is an alias)                        |
| flags          | Kernel flags (evaluates presence of UP/RUNNING)                        |
| iftype         | SNMP ifType (evaluates type validity)                                  |

All attribute violations result in CRITICAL.  
There is no WARNING tier.

---

## 7. Perfdata Metrics

The `--perfdata` flag selects a single SNMP counter to output in Nagios perfdata.

Valid values:

Inbound:
* in_octets  
* in_ucast  
* in_multicast  
* in_broadcast  
* in_discards  
* in_errors  

Outbound:
* out_octets  
* out_ucast  
* out_multicast  
* out_broadcast  
* out_discards  
* out_errors  

Only one metric may be selected.

Perfdata is only emitted in Nagios mode.

---

## 8. Filtering & Selection

| Flag                  | Description                                                              | Repeatable |
|-----------------------|--------------------------------------------------------------------------|------------|
| --ifaces LIST         | Comma‑delimited list or regex pattern of interfaces to evaluate          | No         |
| --ignore PATTERN      | Exclude interfaces matching substring or regex                           | Yes        |
| --ignore-virtual      | Exclude virtual interfaces (vnet*, virbr*, docker0, etc.)                | No         |
| --exclude-local       | Exclude loopback and local‑only interfaces (lo)                          | No         |
| --include-aliases     | Include alias interfaces (excluded by default)                           | No         |

Filtering always occurs **before** selection.  
See [Enforcement.md](Enforcement.md) for full pipeline details.

---

## 9. Output Modes

| Flag              | Mode    | Description                                                     |
|-------------------|---------|-----------------------------------------------------------------|
| *(default)*       | Nagios  | Single‑line output with exit code; logging disabled             |
| -v, --verbose     | Verbose | Human‑readable table; logging enabled                           |
| -j, --json        | JSON    | Full structured output including counters; logging enabled      |
| -q, --quiet       | Quiet   | Exit code only                                                  |

Output mode precedence:

1. JSON  
2. Verbose  
3. Nagios (default)  

If both `-j` and `-v` are provided, JSON wins.

---

## 10. Logging

Logging is opt‑in and only active in verbose and JSON modes.

| Flag                | Description                                            | Default |
|---------------------|--------------------------------------------------------|---------|
| --log-dir PATH      | Directory for log output                               | —       |
| --log-max-mb MB     | Maximum log size before rotation                       | 50      |

Nagios mode never logs.

---

## 11. General

| Flag              | Description                                      | Default |
|-------------------|--------------------------------------------------|---------|
| --timeout SEC     | General timeout for all operations               | 5       |
| -V, --version     | Print version and exit                           | —       |

---

## 12. Examples

### Local Host

Check all local interfaces:
```bash
./check_interfaces -H localhost
```

Verbose diagnostics:
```bash
./check_interfaces -H localhost -v
```

### Remote Host (SNMP)
```bash
./check_interfaces -H switch01 -C public
```

### Targeted Interfaces

Literal list:
```bash
./check_interfaces -H switch01 -C public --ifaces "eth0,eth1"
```

Regex:
```bash
./check_interfaces -H switch01 -C public --ifaces "GigabitEthernet0/[0-3]"
```

### Attribute Checks

Linkspeed:
```bash
./check_interfaces -H switch01 -C public --status linkspeed
```

Duplex:
```bash
./check_interfaces -H switch01 -C public --status duplex
```

MTU:
```bash
./check_interfaces -H switch01 -C public --status mtu
```

Alias identity:
```bash
./check_interfaces -H switch01 -C public --status alias
```

### Filtering

Exclude virtual and local interfaces:
```bash
./check_interfaces -H linux01 --ignore-virtual --exclude-local
```

Ignore patterns:
```bash
./check_interfaces -H switch01 -C public --ignore "vnet.*" --ignore "docker0"
```

Include alias interfaces:
```bash
./check_interfaces -H switch01 -C public --include-aliases
```

### Combined Filtering + Selection
```bash
./check_interfaces -H switch01 -C public --ignore "mgmt" --ifaces "GigabitEthernet0/[0-9]"
```


### JSON Output
```bash
./check_interfaces -H switch01 -C public -j
```

### Logging
```bash
./check_interfaces -H switch01 -C public -v --log-dir /var/log/nms_tools
```

Custom rotation:
```bash
./check_interfaces -H switch01 -C public -v --log-dir /var/log/nms_tools --log-max-mb 100
```

### SNMP Options

Non‑standard port:
```bash
./check_interfaces -H switch01 -C public -p 1161
```

Extended timeout:
```bash
./check_interfaces -H switch01 -C public -T 30
```

---

## 13. Exit Codes

| Code | Status   | Meaning                                                                  |
|------|----------|--------------------------------------------------------------------------|
| 0    | OK       | All evaluated interfaces pass                                            |
| 2    | CRITICAL | Attribute failure, unmatched --ifaces pattern, or SNMP failure           |
| 3    | UNKNOWN  | DNS failure, timeout, invalid arguments, or unhandled error              |

There is no WARNING tier.

---

## 14. See Also

[Installation.md](Installation.md)
[Enforcement.md](Enforcement.md)
[Operation.md](Operation.md)
[Metadata_schema.md](Metadata_schema.md)
