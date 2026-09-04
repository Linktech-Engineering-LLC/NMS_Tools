# Internal Flags — check_ports.py

**Part of:** NMS_Tools Monitoring Suite  
**Document:** Internal Flags Reference
**Author:** Leon McClatchey, Linktech Engineering LLC  
**License:** MIT  
**Requires:** Python 3.12+  (development only; not required for frozen binary)
**Last Updated:** 2026‑08‑17

## Table of Contents
1. [Overview](#1-overview)
2. [Flag Table](#2-flag-table)
3. [Bitmask Behavior](#3-bitmask-behavior)
4. [Output Mode Priority](#4-output-mode-priority)
5. [Evaluation Logic](#5-evaluation-logic)
6. [FAIL_ONLY Behavior](#6-fail_only-behavior)
7. [Notes](#7-notes)

---

## 1. Overview

The NMS_Tools suite uses a shared **bitmask flag engine** to control internal behavior across all monitoring and automation plugins. These flags are **internal**, not user‑facing CLI options, and they define evaluation logic, output modes, formatting rules, and operator workflows.

Each flag corresponds to a single bit in the mask, and multiple flags may be combined using bitwise OR (`|`).
The resulting mask is passed into the tool’s enforcement or output subsystem, ensuring deterministic and reproducible behavior across the entire suite.
---

## 2. Flag Table

| Flag Name | Bit Value | Description |
| --- | --- | --- |
| ``VERBOSE`` | ``0x01`` | Enables verbose per‑port output. Set internally when ``--verbose`` is active. |
| ``JSON`` | ``0x02`` | Enables JSON output mode. Set internally when ``--json`` is active. |
| ``QUIET`` | ``0x04`` | Suppresses all output except the exit code. Set internally when ``--quiet`` is active. |
| ``REQUIRE_ALL`` | ``0x08`` | All ports must be open to return OK. Mirrors the ``--require-all`` CLI flag. |
| ``REQUIRE_ANY`` | ``0x10`` | At least one port must be open to return OK. Mirrors the ``--require-any`` CLI flag. |
| ``FAIL_ONLY`` | ``0x20`` | Only log failing ports. Used for operator workflows and log reduction. |

---

## 3. Bitmask Behavior

The flag mask is constructed during argument parsing and passed into the enforcement object.

Example:

```python
flags = 0

if args.verbose:
    flags |= VERBOSE

if args.json:
    flags |= JSON

if args.quiet:
    flags |= QUIET

if args.require_all:
    flags |= REQUIRE_ALL

if args.require_any:
    flags |= REQUIRE_ANY

if args.fail_only:
    flags |= FAIL_ONLY
```

The enforcement object evaluates the mask to determine:

* output mode
* Nagios evaluation rules
* logging verbosity
* whether to suppress successful ports

## 4. Output Mode Priority

Only one output mode is active at a time.
Priority is enforced by the mask:

1. JSON
2. VERBOSE
3. QUIET
4. (default) Nagios single‑line output

This ensures deterministic behavior across all NMS_Tools plugins.

Service‑aware labels (e.g., ssh(22), mysql(3306)) appear in:
* verbose mode
* JSON mode
* logging

They do **not** appear in Nagios mode.

## 5. Evaluation Logic
The following flags influence Nagios state:

* REQUIRE_ALL
* REQUIRE_ANY

If neither is set:

* Any closed, timeout, or unreachable port → CRITICAL
* All ports open → `OK`

If both are set (should not happen via CLI):

* REQUIRE_ALL takes precedence

## 6. FAIL_ONLY Behavior

When FAIL_ONLY is set:

* Only failing ports (`closed`, `timeout`, `unreachable`) are logged
* Successful ports (`open`) are suppressed
* JSON output still includes **all** ports (for correctness)
* Nagios output remains unchanged

This flag is intended for operator workflows where log noise must be minimized.

## 7. Notes

* These flags are **not** exposed directly to the user.
* They are part of the internal architecture shared across the NMS_Tools suite.
* The bitmask system ensures deterministic, reproducible behavior across all tools.
* Service‑aware formatting is applied automatically when --service is used.
