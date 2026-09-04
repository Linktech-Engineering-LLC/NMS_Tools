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
6. [CLI Summary](#6-cli-summary)
    1. [6.1 CLI Reference](#61-cli-reference)
    2. [6.2 CLI Flags](#62-cli-flags)
7. [Output Modes](#7-output-modes)
8. [Filtering Pipeline](#8-filtering-pipeline)
9. [Evaluation Logic](#9-evaluation-logic)
10. [Perfdata](#10-perfdata)
11. [Logging](#11-logging)
12. [Exit Codes](#12-exit-codes)
13. [Requirements](#13-requirements)
14. [Documents](#14-documents)
15. [Tools in this Suite](#15-tools-in-this-suite)
16. [License](#16-license)

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

### 6.1 CLI Reference

usage: check_interfaces -H <host> [options]

### 6.2 CLI Flags

These are the **user‑facing CLI flags** for `check_interfaces`.
Internal bitmask flags used by the enforcement engine are documented globally in `FLAGS.md`.

#### Output Modes
| Flag | Description |
| --- | --- |
| ``-v``, ``--verbose`` | Verbose output mode |
| ``-j``, ``--json`` | JSON output mode |
| ``-q``, ``--quiet`` | Quiet mode (exit code only) |
| ``--color`` | Colorize terminal output (verbose/JSON) |
| ``--output ``FILE`` | Write output to FILE instead of stdout |

#### Logging
| Flag | Description |
| --- | --- |
| ``--log-dir ``DIR`` | Directory to store logs |
| ``--log-max-mb ``SIZE`` | Maximum log size before rotation (default: 50 MB) |

#### Core Options
| Flag | Description |
| --- | --- |
| ``-H ``HOST``, ``--host ``HOST`` | Target hostname or IP address |
| ``-t ``SECONDS``, ``--timeout ``SECONDS`` | Connection timeout (default: 5 seconds) |

#### SNMP Options (SNMPv2c)
| Flag | Description |
| --- | --- |
| ``-C ``STRING``, ``--community ``STRING`` | SNMPv2c community string (required for remote hosts) |
| ``-p ``PORT``, ``--snmp-port ``PORT`` | SNMP port (default: 161) |
| ``-T ``SECONDS``, ``--snmp-timeout ``SECONDS`` | SNMP timeout (defaults to ``--timeout``; ignored in local mode) |

#### SNMPv3 Options
| Flag | Description |
| --- | --- |
| ``--v3-user ``NAME`` | SNMPv3 security name |
| ``--v3-auth ``{MD5,SHA}`` | SNMPv3 authentication protocol |
| ``--v3-auth-pass ``PASS`` | SNMPv3 authentication password |
| ``--v3-priv ``{DES,AES}`` | SNMPv3 privacy protocol |
| ``--v3-priv-pass ``PASS`` | SNMPv3 privacy password |

#### Interface Filtering Options
| Flag | Description |
| --- | --- |
| ``--include-aliases`` | Include alias interfaces (e.g., ``eth0:1``, ``br0:backup``) |
| ``--ignore-virtual`` | Ignore virtual interfaces (e.g., ``vnet*``, ``virbr*``, ``docker0``) |
| ``--exclude-local`` | Exclude local-only interfaces such as ``lo`` |
| ``--ignore ``PATTERN`` | Ignore interfaces matching substring or regex (repeatable) |

#### Targeting Options
| Flag | Description |
| --- | --- |
| ``--status ``ATTR`` | Interface attribute to evaluate (``oper-status``, ``admin-status``, ``linkspeed``, ``duplex``, ``mtu``, ``alias``, ``flags``, ``iftype``) |
| ``--perfdata ``METRIC`` | Perfdata metric to output (``in_octets``, ``out_octets``, ``in_errors``, ``out_errors``, ``in_discards``, ``out_discards``, ``in_ucast``, ``out_ucast``, ``in_multicast``, ``out_multicast``, ``in_broadcast``, ``out_broadcast``) |
| ``--ifaces ``LIST`` | Comma-delimited list or regex pattern of interfaces to evaluate |

#### Internal Flags
Internal bitmask flags used by the enforcement engine (JSON/VERBOSE/QUIET priority, FAIL_ONLY behavior, REQUIRE_ALL/REQUIRE_ANY semantics, etc.) are documented globally:

See: [FLAGS](../../docs/FLAGS.md)


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

## 15. Tools in This Suite

| Tool | Description | Documentation |
|------|-------------|---------------|
| **check_cert** | TLS certificate inspection and expiration validation | [../check_cert/README.md](../check_cert/README.md) |
| **check_html** | HTTP/HTTPS content validation and deterministic HTML checks | [../check_html/README.md](../check_html/README.md) |
| **check_interfaces** | Network interface inspection and operational state reporting | - |
| **check_ports** | Port and service availability inspection | [../check_ports/README.md](../check_ports/README.md) |
| **check_weather** | Deterministic weather client for monitoring pipelines | [../check_weather/README.md](../check_weather/README.md) |
| **check_ticker** | Deterministic market/ticker client using PythonTools finance providers | [README.md](README.md) |

---
## 16. License
* Source code: MIT [LICENSE](../../LICENSE) for details.
* Frozen binary: Proprietary [LICENSE_BINARY](../../LICENSE_BINARY.txt)
