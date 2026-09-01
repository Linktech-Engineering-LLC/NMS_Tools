# check_interfaces — Network Interface State & Attribute Monitoring Tool

**Part of:** NMS_Tools Monitoring Suite  
**Script:** `check_interfaces.py`  
**Author:** Leon McClatchey, Linktech Engineering LLC  
**License:** MIT  
**Requires:** Python 3.12+  
**Last Updated:** 2026-08-17

![Python Version](https://img.shields.io/badge/python-3.6%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-stable-brightgreen)
![Nagios Plugin](https://img.shields.io/badge/Nagios-plugin-success)
![NMS_Tools](https://img.shields.io/badge/NMS_Tools-check__interfaces-blueviolet)

## Table of Contents
1. [Overview](#1-overview)
2. [Deterministic Behavior Guarantees](#2-deterministic-behavior-guarantees)
3. [Backend Parity (Local + SNMP)](#3-backend-parity-local--snmp)
4. [Capabilities](#4-capabilities)
5. [Quick Start](#5-quick-start)
5. [CLI Summary](#6-cli-summary)
6. [Output Modes](#7-output-modes)
8. [Filtering Pipeline](#8-filtering-pipeline)
9. [Evaluation Logic](#9-evaluation-logic)
10. [Perfdata](#10-perfdata)
11. [Logging](#11-logging)
12. [Exit Codes](#12-exit-codes)
13. [Requirements](#13-requirements)
14. [Documents](#14-documents)
15. [License](#15-license)

## 1. Overview

`check_interfaces` is an operator‑grade network interface monitoring plugin for Nagios and compatible monitoring systems.  
It provides deterministic interface discovery, attribute evaluation, and perfdata emission across both **local Linux hosts** and **remote SNMP devices**, using a unified, normalized interface schema.

The tool supports three output modes — **Nagios**, **verbose**, and **JSON** — making it equally suitable for alerting, diagnostics, and automation.

---

## 2. Deterministic Behavior Guarantees

`check_interfaces` follows the NMS_Tools determinism contract:
* **Deterministic enumeration**
  Interfaces are discovered in a stable, reproducible order.
* **Deterministic filtering**
  All filters (--ifaces, --ignore, --exclude-local, etc.) apply in a fixed sequence.
* **Deterministic evaluation**
  Each interface produces a stable evaluation result for the selected attribute.
* **Deterministic exit codes**
  Global state is derived from evaluation failures using Nagios‑standard semantics.
* **Deterministic perfdata emission**
  Perfdata is always raw, Nagios‑safe, and emitted in a stable order.

---

## 3. Backend Parity (Local + SNMP)

Local and SNMP modes produce **identical normalized interface objects**, including:
* MTU
* MAC
* speed
* duplex
* flags
* counters
* admin/oper state

All counters follow the IF‑MIB model.

---

## 4. Capabilities

### Unified SNMP + Local Interface Discovery
* Local mode uses `/sys/class/net` and psutil.
* Remote mode uses SNMPv2c (IF‑MIB).
* All interfaces normalized into a consistent schema.

### Multiple Output Modes
* Nagios single‑line
* Verbose diagnostic (`-v`/`--verbose`)
* JSON structured (`-j`/`--json`)
* Quiet (`-q`/'--quiet`)

### Attribute‑Based Evaluation

Evaluate interfaces using:
* `oper-status` (default)
* `linkspeed`
* `duplex`
* `mtu`
* `flags`

### Canonical Filtering Pipeline

Deterministic, backend‑agnostic filtering using:
* `--ifaces` (literal + regex)
* `--ignore` (repeatable)
* `--exclude-local`
* `--ignore-virtual`
* `--include-aliases`

### Normalized Counters (IF‑MIB)
* Octets
* Ucast
* Multicast
* Broadcast
* Discards
* Errors
* Unknown protocols

### Clean Speed Normalization

Speeds normalized to Mbps:
* `10G`, `1G`, `100M`, `10M`, `-`

---

## 5. Quick Start

### Local Host
./check_interfaces -H localhost

### Remote Host (SNMP)
./check_interfaces -H switch01 -C public

### Evaluate Link Speed
./check_interfaces -H switch01 -C public --status linkspeed

### Select Perfdata Metric
./check_interfaces -H switch01 -C public --perfdata in_octets

### Verbose Diagnostic Output
./check_interfaces -H switch01 -C public -v

### JSON Output
./check_interfaces -H switch01 -C public -j | jq

---

## 6. CLI Summary
| Flag | Description |
| --- | --- |
| ``-H`` | Hostname (local or SNMP) |
| ``-C`` | SNMP community |
| ``--status`` | Evaluation attribute |
| ``--perfdata`` | Select perfdata counter |
| ``--ifaces`` | Literal/regex interface selection |
| ``--ignore`` | Ignore interfaces (repeatable) |
| ``--exclude-local`` | Remove loopback/local-only |
| ``--ignore-virtual`` | Remove virtual interfaces |
| ``--include-aliases`` | Include SNMP alias interfaces |
| ``-v`` | Verbose mode |
| ``-j`` | JSON mode |
| ``-q`` | Quiet mode |
| ``--log-dir`` | Enable logging |

---

## 7. Output Modes

### Nagios Mode (default)

Single‑line output with perfdata:
```code
OK: all interfaces oper-status | eth0_in_octets=12345c br0_in_octets=67890c
```

### Verbose Mode (-v)

```code
Interface: eth0
  MAC: 98:4b:e1:60:65:a8
  MTU: 1500
  Speed: 1G
  Duplex: full
  Admin: up
  Oper: up
  Flags: UP,RUNNING
  Eval: OK (oper-status)
  IPv4: none
  IPv6: none
  Counters:
    Octets:     In=1170978183  Out=2859282825
    Ucast:      In=34768217    Out=28905155
    Multicast:  In=182         Out=0
    Broadcast:  In=0           Out=0
    Errors:     In=0           Out=0
    Discards:   In=0           Out=0
```

### JSON Mode (-j)

```json
{
  "interfaces": {
    "eth0": {
      "mac": "98:4b:e1:60:65:a8",
      "mtu": 1500,
      "speed": 1000,
      "duplex": "full",
      "admin_up": true,
      "oper_up": true,
      "flags": ["UP", "RUNNING"],
      "counters": {
        "in_octets": 1170978183,
        "out_octets": 2859282825,
        "in_ucast": 34768217,
        "out_ucast": 28905155,
        "in_multicast": 182,
        "out_multicast": 0,
        "in_broadcast": 0,
        "out_broadcast": 0,
        "in_errors": 0,
        "out_errors": 0,
        "in_discards": 0,
        "out_discards": 0
      },
      "eval": "OK"
    }
  },
  "status": {
    "global": "OK",
    "failed": []
  },
  "meta": {
    "host": "switch01",
    "mode": "snmp",
    "timestamp": "2026-08-17T14:22:05Z"
  }
}
```

---

## 8. Filtering Pipeline
Filtering is deterministic and applied identically in both SNMP and local modes.

`--ifaces`
Literal + regex selection:
```code
--ifaces eth0,eth1,^vnet[0-9]+$
```

### Additional Filters

| Flag | Purpose |
| --- | --- |
| ``--ignore`` | Ignore interfaces matching substring/regex |
| ``--exclude-local`` | Remove loopback/local-only |
| ``--ignore-virtual`` | Remove vnet*, virbr*, docker0 |
| ``--include-aliases`` | Include SNMP alias interfaces |

---

## 9. Evaluation Logic

Each interface produces an evaluation result based on the selected attribute:
* `oper-status`
* `linkspeed`
* `duplex`
* `mtu`
* `flags`

Global state is derived from failures:
* any CRITICAL → CRITICAL
* any WARNING → WARNING
* none → OK

---

## 10. Perfdata

Select a single counter:
* `in_octets`
* `out_octets`
* `in_errors`
* `out_errors`
* `in_discards`
* `out_discards`
* `in_ucast`
* `out_ucast`
* `in_multicast`
* `out_multicast`
* `in_broadcast`
* `out_broadcast`

Perfdata is always raw and Nagios‑safe.

---

## 11. Logging

Logging is opt‑in:

```code
./check_interfaces -H switch01 -C public -v --log-dir /var/log/nms_tools
```

Logging follows NMS_Tools conventions:
* single‑line entries
* size‑based rotation
* no logging in default Nagios mode

---

## 12. Exit Codes

| Code | Meaning |
| --- | --- |
| 0 | All interfaces OK |
| 1 | Non‑critical issues |
| 2 | Critical failure |
| 3 | Unknown / error |

SNMP failures return CRITICAL or UNKNOWN.

---

## 13. Requirements
* Python 3.12+
* `pysnmp` (for SNMP mode)
* SNMPv2c access for remote hosts
* Hostname must be resolvable

---

## 14. Documents

| Document | Description |
|----------|-------------|
| [Installation.md](docs/Installation.md) | Installation and environment setup |
| [Usage.md](docs/Usage.md)        | Full CLI reference and examples |
| [Operation.md](docs/Operation.md)    | Discovery, normalization, and output pipeline |
| [Enforcement.md](docs/Enforcement.md)  | Status evaluation and filtering logic |
| [Metadata_schema.md](docs/Metadata_schema.md) | Normalized interface schema |

---

## 15. License

Part of the **NMS_Tools** suite by Linktech Engineering LLC.
Licensed under MIT.

See the suite‑wide README for contributor guidelines and community standards.

---