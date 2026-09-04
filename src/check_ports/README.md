# check_ports.py — Deterministic Multi‑Port Connectivity Checker
Fast, deterministic TCP port checking for Nagios, operators, and automation workflows.

**Part of:** NMS_Tools Monitoring Suite  
**Script:** `check_ports.py`  
**Author:** Leon McClatchey, Linktech Engineering LLC  
**License:** MIT  
**Requires:** Python 3.12+  (development only; not required for frozen binary)
**Last Updated:** 2026‑08‑17

![Python Version](https://img.shields.io/badge/python-3.6%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-stable-brightgreen)
![Nagios Plugin](https://img.shields.io/badge/Nagios-plugin-success)
![NMS_Tools](https://img.shields.io/badge/NMS_Tools-check__ports-blueviolet)

## Table of Contents
1. [Overview](#1-overview)  
2. [Features](#2-features)  
3. [Usage](#3-usage)  
    1. [3.1 Required Arguments](#31-required-arguments)
    2. [3.2 Port / Service Selection](#32-port--service-selection)
    3. [3.3 CLI Flags](#33-cli-flags)
4. [Output Modes](#4-output-modes)  
    1. [4.1 Nagios/Icinga Mode](#41-nagiosicinga-mode)  
    2. [4.2 JSON Mode](#42-json-mode)  
    3. [4.3 Verbose Mode](#43-verbose-mode)  
    4. [4.4 Quiet Mode](#44-quiet-mode)
5. [Enforcement Model](#5-enforcement-model) 
6. [Logging](#6-logging)  
7. [Exit Codes](#7-exit-codes)  
8. [Examples](#8-examples)
9. [Logging Directory Structure](#9-logging-directory-structure)
10. [Future Enhancements](#10-future-enhancements)
11. [Documents](#11-documents)
12. [Tools in this Suite](#12-tools-in-this-suite)  
13. [License](#13-license)

---

## 1. Overview
`check_ports.py` performs fast, deterministic TCP connectivity checks against one or more ports on a target host. It supports mixed port lists, ranges, JSON output, verbose/quiet modes, and operator‑grade logging with rotation. The tool is designed for reliability, reproducibility, and clean integration into monitoring systems.

---

## 2. Features

* Deterministic TCP availability checking (open / closed / timeout / unreachable)
* Supports numeric ports, comma‑lists, and ranges (`22`,`80`,`8000-8010`)
* **Supports service‑name resolution via** `/etc/services` and `socket.getservbyname()`
    * Examples: `--service http,https,ssh,mysql`
    * Service‑aware labels appear in verbose, JSON, and logs (`ssh(22)`, `mysql(3306)`)
* Deterministic expansion of mixed numeric + service‑name inputs
* JSON output for automation, dashboards, and test harness integration
* Verbose mode for operator workflows (one line per port with service‑aware labels)
* Quiet mode for Nagios (exit code only)
* Nagios‑compatible single‑line output (default mode)
* Nagios evaluation filters: `--require-all`, `--require-any`, `--fail-only`
* Operator‑grade logging with rotation, structured banners, and service‑aware entries
* Zero side effects in Nagios mode (no logs, no files, no color, no banners)
* Fully aligned with NMS_Tools suite architecture and enforcement model

---

## 3. Usage

```bash
check_ports -H <host> (--ports <ports> | --service <name>) [options]
```
### 3.1 Required Arguments

At least one of the following must be provided:

| Flag | Description |
| :--- | :--- |
| `-H`, `--host` | Target hostname or IP address |
| `-p`, `--ports` | Port list or range (e.g., `22,80,8000-8010`) |
| `-s`, `--service` | One or more named services (e.g., `ssh,http,mysql`) |

You must specify **either** `--ports` or `--service` (or both).  
If neither is provided, the tool returns `UNKNOWN`.

### 3.2 Port / Service Selection

#### Numeric Ports (`--ports`)
Supports:
* Single ports: `22`
* Comma‑lists: `22`,`80`,`443`
* Ranges: `8000-8010`
* Mixed lists: `22`,`2222`,`8080`,`5000-5004`

All ports are expanded into a deterministic, sorted list.

#### Service Names (`--service`)
Service names are resolved using:
* /etc/services
* socket.getservbyname()

Examples:
```bash
--service http,https,ssh
--service smtp,pop3,imap
```

Service‑aware labels appear in:
* verbose output
* JSON output
* logs

Examples:
```code
ssh(22)
mysql(3306)
http(80)
```

Explicit ports always appear as raw numbers.

### 3.3 CLI Flags

These are the **user‑facing CLI flags** for `check_ports`. Internal bitmask flags used by the enforcement engine are documented globally in `FLAGS.md`.

| Flag | Description |
| --- | --- |
| ``-v``, ``--verbose`` | Verbose output mode |
| ``-j``, ``--json`` | JSON output mode |
| ``-q``, ``--quiet`` | Quiet mode (exit code only) |
| ``--color`` | Colorize terminal output (verbose/JSON) |
| ``--output ``FILE`` | Write output to FILE instead of stdout |
| ``--log-dir ``DIR`` | Directory for logs |
| ``--log-max-mb ``SIZE`` | Max log size before rotation (default: 50 MB) |
| ``--require-all`` | All ports must be open |
| ``--require-any`` | At least one port must be open |
| ``--fail-only`` | Only report failed ports in verbose/JSON |
| ``-t``, ``--timeout`` | Per‑port timeout (default: 5 seconds) |
| ``-V``, ``--version`` | Show version and exit |

[Full flag documentation:](../../docs/FLAGS.md)

---

## 4. Output Modes

Only one output mode is active at a time. Priority order:
1. JSON
2. Verbose
3. Quiet
4. Nagios (default)

### 4.1 Nagios/Icinga Mode
Default mode when no other output flag is provided.

Example:
```code
CRITICAL - Problem ports: 80
```

Nagios state is determined by:
* `--require-all`
* `--require-any`
* default mixed‑state logic

### 4.2 JSON Mode

```bash
check_ports.py -H server -p 22,80 -j
```

Produces:
```json
{
  "host": "server",
  "results": [
    {"port": 22, "status": "open"},
    {"port": 80, "status": "closed"}
  ],
  "open_ports": [22],
  "closed_ports": [80],
  "timeout_ports": [],
  "unreachable_ports": []
}
```

Service‑aware JSON:
```json
{"port": "ssh(22)", "status": "open"}
```


### 4.3 Verbose Mode

Verbose mode shows a human‑readable breakdown of what the tool resolved and the status of each port check.
It prints:
* the host
* the requested services
* the resolved service‑to‑port mapping
* explicit ports
* all ports being checked
* one line per port with its status

Example:

```Code
Host: server
Explicit ports: 22, 9999
All ports:      22, 9999

ssh(22) = open
9999 = closed
```

With `--fail-only`, verbose mode suppresses open ports:

```Code
9999 = closed
```

```Service ports: ssh(22), mysql(3306)```

Each per‑port result also includes the service name when applicable:

```Mom:ssh(22) = closed```
```Mom:2222 = open```
```Mom:mysql(3306) = open```

Explicit ports (those provided via -p) are always shown as raw port numbers.
Verbose mode is intended for operators who want to see exactly what the tool resolved and how each port responded. It does not output JSON or Nagios‑formatted text.

### 4.4 Quiet Mode

No output — exit code only.

---

## 5. Enforcement Model
check_ports.py uses the standard NMS_Tools enforcement engine:
* Bitmask flags (VERBOSE, JSON, QUIET, REQUIRE_ALL, REQUIRE_ANY, FAIL_ONLY)
* Deterministic evaluation rules
* Unified state resolution for Nagios, JSON, verbose, and quiet modes

Internal flags:

| Flag | Bit | Description |
| --- | --- | --- |
| ``VERBOSE`` | ``0x01`` | Verbose output |
| ``JSON`` | ``0x02`` | JSON mode |
| ``QUIET`` | ``0x04`` | Quiet mode |
| ``REQUIRE_ALL`` | ``0x08`` | All ports must be open |
| ``REQUIRE_ANY`` | ``0x10`` | At least one port must be open |
| ``FAIL_ONLY`` | ``0x20`` | Only log failing ports |

---

---

## 6. Logging

Logging is enabled if:

* mode != "nagios"
* `--log-dir` is specified

When logging is enabled, the tool writes:
* a [START] banner with command, host, and resolved ports
* one [PORT] line per port
* a [RESULT] summary line
* a final [END] banner

### Service‑Aware Logging

When services are specified using -s, log entries now include the service name alongside the port number:

[PORT] host=Mom port=ssh(22) status=closed
[PORT] host=Mom port=mysql(3306) status=open

Explicit ports (those provided via -p) are always logged as raw port numbers:

[PORT] host=Mom port=2222 status=open

The [RESULT] line includes grouped breakdowns:

```service_open=mysql(3306) service_closed=ssh(22) explicit_open=2222```

This makes logs fully service‑aware and consistent with verbose, JSON, and Nagios modes.

### Example:

```bash
check_ports.py -H server -p 22,80 -j --log-dir /var/log/nms_tools
```

Log entries follow the suite‑standard format:

```
2026-04-20 11:29:55; [START] check_ports.py host=server ports_explicit=[22,80] ports_service=[] ports_all=[22,80] timeout=5 require_all=False require_any=False
2026-04-20 11:29:55; [PORT] host=server port=22 status=open
2026-04-20 11:29:55; [PORT] host=server port=80 status=closed
2026-04-20 11:29:55; [RESULT] state=CRITICAL message="json output" explicit_open=22 explicit_closed=80
2026-04-20 11:29:55; [END]
```

If services are specified using -s, log entries include service names:

```bash
check_ports.py -H server -s ssh,http -j --log-dir /var/log/nms_tools
```

Produces:

2026-04-20 11:29:55; [START] check_ports.py host=server ports_explicit=[] ports_service=[22,80] ports_all=[22,80] timeout=5 require_all=False require_any=False
2026-04-20 11:29:55; [PORT] host=server port=ssh(22) status=open
2026-04-20 11:29:55; [PORT] host=server port=http(80) status=closed
2026-04-20 11:29:55; [RESULT] state=CRITICAL message="json output" service_open=ssh(22) service_closed=http(80)
2026-04-20 11:29:55; [END]


Log rotation is automatic when the file exceeds `--log-max-mb` (default: 50 MB).

---

## 7. Exit Codes
| Code | Meaning |
| --- | --- |
| 0 | OK |
| 1 | WARNING |
| 2 | CRITICAL |
| 3 | UNKNOWN |

---

## 8. Examples

### Check a single port

```bash
check_ports.py -H server -p 22
```

### Check a range

```bash
check_ports.py -H server -p 8000-8010
```

### Check mixed ports with JSON output

```bash
check_ports.py -H server -p 22,80,443,8000-8005 -j
```

### Quiet mode for Nagios

```bash
check_ports.py -H server -p 22,80 -q
```

---

## 9. Logging Directory Structure

```
<log_dir>/
    check_ports.log
    check_ports_20260420_112955.log.zip
```

## 10. Future Enhancements

The following improvements are planned for future releases of `check_ports.py`:

### Port Parsing & Resolution
* **Named port support** (e.g., `https` → 443 via `/etc/services`)
* Strict validation for unknown port names
* Deterministic expansion of mixed numeric + named ports

### Output & Evaluation
* JSON schema versioning for long‑term compatibility
* Optional perfdata block for Nagios
* Additional evaluation modes (e.g., require-open-count=N)

### Logging & Diagnostics
* Structured diagnostic mode (`--debug`)
* Per‑port timing metrics
* Connection lifecycle tracing (SYN, timeout, refusal)

### UX Improvements
* Help text refinements
* Port parsing preview (`--explain-ports`)

---

## 11. Documents
Documentation is available under:

check_html/docs/
Including:
* [FLAGS](docs/FLAGS.md)
* [Enforcement](docs/Enforcement.md)
* [Installation](docs/Installation.md)
* [Metadata_schema](docs/Metadata_schema.md)
* [Operation](docs/Operation.md)
* [Usage](docs/Usage.md)

---

## 12. Tools in This Suite

| Tool | Description | Documentation |
|------|-------------|---------------|
| **check_cert** | TLS certificate inspection and expiration validation | [../check_cert/README.md](../check_cert/README.md) |
| **check_html** | HTTP/HTTPS content validation and deterministic HTML checks | [../check_html/README.md](../check_html/README.md) |
| **check_interfaces** | Network interface inspection and operational state reporting | [../check_interfaces/README.md](../check_interfaces/README.md) |
| **check_ports** | Port and service availability inspection | - |
| **check_weather** | Deterministic weather client for monitoring pipelines | [../check_weather/README.md](../check_weather/README.md) |
| **check_ticker** | Deterministic market/ticker client using PythonTools finance providers | [README.md](README.md) |

---

## 13. License

MIT License — see LICENSE.md in the repository root.

