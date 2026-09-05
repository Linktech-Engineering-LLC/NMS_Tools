# check_ports — Enforcement Model

**Part of:** NMS_Tools Monitoring Suite  
**Document:** Enforcement Model  
**Author:** Leon McClatchey, Linktech Engineering LLC  
**License:** MIT  
**Requires:** Python 3.12+  (development only; not required for frozen binary)
**Last Updated:** 2026‑09-03

## Table of Contents
1. [Overview](#1-overview)
2. [nforcement Inputs](#2-enforcement-inputs)
3. [Enforcement Logic](#3-enforcement-logic)
4. [Enforcement Object Structure](#4-enforcement-object-structure)
5. [Nagios Exit Code Rules](#5-nagios-exit-code-rules)
6. [JSON Example](#6-json-example)
7. [Notes](#7-notes)
8. [See Also](#8-see-also)

---

## 1. Overview
`check_ports` uses a **rule‑based enforcement model** to determine the final Nagios exit code.

Unlike drift‑based enforcement tools, `check_ports` does **not** compare baseline vs nxt state.
Instead, enforcement is computed entirely from:
* resolved ports
* per‑port results
* service mappings
* user‑specified requirement flags

The enforcement engine produces a deterministic object consumed by `compute_nagios_code()` and included in JSON output.

---

## 2. Enforcement Inputs

Enforcement is driven by the following metadata fields:

### require_all
* All ports must succeed.
* If any port fails → CRITICAL.

### require_any
* At least one port must succeed.
* If all ports fail → CRITICAL.

### fail_only
* Only failures matter.
* Successes do not affect severity.

### explicit_ports
* Ports explicitly provided by the user.

### service_ports
* Ports resolved from service names.

### all_ports
* Combined, deduplicated list of ports to check.

### results
* A list of per‑port results produced by `run_port_checks()`.

### port_to_service
* Mapping of ports to service names (if applicable).

---

## 3. Enforcement Logic

Enforcement is computed in build_enforcement_object() and consists of:

1. Counting successes and failures
    * `success_count`
    * `failure_count`
2. Applying requirement filters
    * `require_all`
    * `require_any`
    * `fail_only`
3. Determining enforcement state
    * `"OK"`
    * `"WARNING"`
    * `"CRITICAL"`
    * `"UNKNOWN"`
4. Generating a human‑readable summary
    * `"3 open, 1 closed"`
    * `"all ports reachable"`
    * `"no ports reachable"`

The enforcement object is then passed to `compute_nagios_code()`.

---

## 4. Enforcement Object Structure

A typical enforcement object looks like:
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

### Field Definitions
* **port_results**: Mapping of port → `"open"` or `"closed"`.
* **port_to_service**: Mapping of port → service name (if requested).
* **require_all / require_any / fail_only**: Enforcement rule flags.
* **success_count / failure_count**: Totals used for severity evaluation.
* **state**: Final enforcement state before Nagios code conversion.
* **summary**: Human‑readable enforcement summary.

---

## 5. Nagios Exit Code Rules

compute_nagios_code() converts enforcement state into Nagios exit codes:

| Enforcement State | Exit Code | Meaning |
| --- | --- | --- |
| **OK** | 0 | All requirements satisfied |
| **WARNING** | 1 | Partial failure or soft rule violation |
| **CRITICAL** | 2 | Hard rule violation (require_all / require_any) |
| **UNKNOWN** | 3 | Invalid input or internal error |

### Examples
* require_all = true and any port fails → CRITICAL
* require_any = true and all ports fail → CRITICAL
* Mixed results with no strict rules → WARNING
* All ports succeed → OK

---

## 6. JSON Example

### JSON Mode Output (simplified)
```json
{
    "metadata": {
        "host": "example.com",
        "timeout": 3,
        "explicit_ports": [22, 80],
        "all_ports": [22, 80],
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

* Enforcement is **stateless**: each run is independent.
* No baseline/nxt metadata is stored.
* Enforcement is purely rule‑based, not drift‑based.
* JSON mode always includes the enforcement object.
* Nagios mode suppresses logs but still performs full enforcement.

---

## 8. See Also
* [Installation](Installation.md)
* [Metadata_schema](Metadata_schema.md)
* [Operation](Operation.md)
* [Usage](Usage.md)
* [FLAGS.md](../../../docs/FLAGS.md)
