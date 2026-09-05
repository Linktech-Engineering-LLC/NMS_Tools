# check_ports.py — Metadata Schema

**Part of:** NMS_Tools Monitoring Suite  
**Document:** Metadata Schema 
**Author:** Leon McClatchey, Linktech Engineering LLC  
**License:** MIT  
**Requires:** Python 3.12+  (development only; not required for frozen binary)
**Last Updated:** 2026‑09-03

## Table of Contents
1. [Overview](#1-overview)
2. [Metadata Structure](#2-metadata-structure)
3. [Field Definitions](#3-field-definitions)
4. [Dynamic Fields](#4-dynamic-fields)
5. [Enforcement Relevance](#5-enforcement-object)
6. [JSON Examples](#6-json-example)
7. [Notes](#7-notes)
8. [See Also](#8-see-also)

---

## 1. Overview

check_ports generates a metadata dictionary describing:
* execution context
* logging configuration
* resolved ports
* service mappings
* enforcement requirements

This metadata is used internally to compute Nagios exit codes and produce structured JSON output.

Unlike full enforcement tools, check_ports does not maintain baseline/nxt drift metadata.
Its enforcement model is rule‑based, not state‑based.

---

## 2. Metadata Structure

Metadata is created by `build_metadata()` and later augmented by:
* `resolve_all_ports()`
* `run_port_checks()`

The final metadata object is included in JSON output and logging.

Top‑level structure:
```json
{
    "log_dir": "...",
    "log_max_mb": 50,
    "mode": "normal",
    "_log_warn_emitted": false,
    "command": "check_ports -H example.com -p 22",
    "logging_enabled": true,

    "host": "example.com",
    "timeout": 3,
    "require_all": false,
    "require_any": false,
    "fail_only": false,

    "service_requested": [],
    "explicit_ports": [],
    "service_ports": [],
    "all_ports": []
}
```

---

## 3. Field Definitions

### log_dir
* **Type:** string or null
* **Description:** Directory for log output.

### log_max_mb
* **Type:** integer
* **Description:** Maximum log file size before rotation.

### mode
* **Type:** string
* **Description:** Operational mode (`normal`, `verbose`, `json`, `quiet`, `nagios`).

### _log_warn_emitted
* **Type:** boolean
* **Description:** Internal flag to prevent duplicate warnings.

### command
* **Type:** string
* **Description:** Full command line used to invoke the tool.

### logging_enabled
* **Type:** boolean
* **Description:** True if logging is active (disabled in `nagios` mode).

### Tool‑Specific Fields
#### host
* **Type:** string
* **Description:** Target host for port checks.

#### timeout
* **Type:** integer
* **Description:** Connection timeout per port.

#### require_all
* **Type:** boolean
* **Description:** Enforcement rule: all ports must succeed.

#### require_any
* **Type:** boolean
* **Description:** Enforcement rule: at least one port must succeed.

#### fail_only
* **Type:** boolean
* **Description:** Enforcement rule: only failures matter.

---

## 4. Dynamic Fields
These fields are populated during execution.

### service_requested
* **Type:** list of strings
* **Description:** Services requested via `--service`.

### explicit_ports
* **Type:** list of integers
* **Description:** Ports explicitly provided via `--ports`.

### service_ports
* **Type:** list of integers
* **Description:** Ports resolved from service names.

### all_ports
* **Type:** list of integers
* **Description:** Combined, deduplicated, sorted list of all ports to check.

---

## 5. Enforcement Object

Created by:
```python
enf = build_enforcement_object(meta, results, port_to_service)
```

The enforcement object contains:
* port results
* service mappings
* rule evaluation
* summary fields used for Nagios exit code computation

Example structure:
```json
{
    "port_results": {
        "22": "open",
        "80": "closed"
    },
    "port_to_service": {
        "22": "ssh",
        "80": "http"
    },
    "require_all": false,
    "require_any": false,
    "fail_only": false,
    "success_count": 1,
    "failure_count": 1,
    "state": "WARNING",
    "summary": "1 open, 1 closed"
}
```

This object is passed to:
* `compute_nagios_code()`
* `output_results()`

---

## 6. JSON Example

### JSON Output (simplified)
```json
{
    "metadata": {
        "host": "example.com",
        "timeout": 3,
        "require_all": false,
        "require_any": false,
        "fail_only": false,
        "explicit_ports": [22, 80],
        "service_ports": [],
        "all_ports": [22, 80],
        "command": "check_ports -H example.com -p 22,80",
        "mode": "json"
    },
    "results": [
        {"port": 22, "status": "open"},
        {"port": 80, "status": "closed"}
    ],
    "enforcement": {
        "state": "WARNING",
        "success_count": 1,
        "failure_count": 1,
        "summary": "1 open, 1 closed"
    }
}
```

---

## 7. Notes

* `check_ports` uses rule‑based enforcement, not baseline/nxt drift.
* Metadata is always JSON and always included in JSON mode output.
* Enforcement object is deterministic and fully derived from metadata + results.
* No persistent metadata is stored; each run is independent.

---

## 8. See Also
* [Installation](Installation.md)
* [Enforcement](Enforcement.md)
* [Operation](Operation.md)
* [Usage](Usage.md)
* [FLAGS.md](../../../docs/FLAGS.md)
