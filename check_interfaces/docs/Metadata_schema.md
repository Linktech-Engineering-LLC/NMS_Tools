# Metadata_schema.md — JSON Output Schema Reference

## Overview

This document defines the JSON output schema produced by `check_interfaces.py` when invoked with `-j` or `--json`. The output is a single JSON object with three top‑level keys: `interfaces`, `meta`, and `status`.

For CLI usage, see [Usage.md](Usage.md). For runtime behavior and output mode details, see [Operation.md](Operation.md).

---

## Top‑Level Structure

```json
{
  "interfaces": { ... },
  "meta": { ... },
  "status": { ... }
}
```

| Key          | Type   | Description                                          |
|--------------|--------|------------------------------------------------------|
| `interfaces` | object | Per‑interface metadata, keyed by interface name      |
| `meta`       | object | Operational metadata for the invocation              |
| `status`     | object | Evaluation results and overall state                 |

---

## `interfaces`

An object where each key is an interface name and each value is an interface metadata object.

```json
"interfaces": {
  "eth0": { ... },
  "br0": { ... }
}
```

### Interface Object

| Field       | Type             | Description                                                        |
|-------------|------------------|--------------------------------------------------------------------|
| `name`      | string           | Interface name (matches the object key)                            |
| `mac`       | string           | MAC address (e.g., `"0c:c4:7a:32:c2:02"`)                         |
| `mtu`       | integer          | Maximum transmission unit                                          |
| `speed`     | integer \| null  | Negotiated link speed in Mbps. `null` if unavailable (e.g., loopback) |
| `duplex`    | string           | Duplex mode: `"full"`, `"half"`, or `"unknown"`                    |
| `admin_up`  | boolean          | Administrative status — is the interface enabled?                  |
| `oper_up`   | boolean          | Operational status — is the interface up?                          |
| `flags`     | array of strings | Kernel flags (e.g., `["UP", "RUNNING"]`)                           |
| `ifType`    | string \| null   | SNMP interface type (IF‑MIB). `null` for local discovery.          |
| `ipv4`      | array of objects | IPv4 addresses assigned to the interface. See **Address Object**.   |
| `ipv6`      | array of objects | IPv6 addresses assigned to the interface. See **Address Object**.   |

### Address Object

| Field       | Type            | Description                                                    |
|-------------|-----------------|----------------------------------------------------------------|
| `address`   | string          | IP address (e.g., `"192.168.0.1"`)                             |
| `netmask`   | string          | Subnet mask (e.g., `"255.255.255.0"`)                          |
| `broadcast` | string \| null  | Broadcast address. `null` for point‑to‑point or loopback.      |

---

## `meta`

Operational metadata describing the invocation context, host detection, and active filters.

```json
"meta": {
  "host": "localhost",
  "ip": "127.0.0.1",
  "mode": "local",
  "script_name": "check_interfaces",
  "status_target": "oper-status",
  "interface_count": 6,
  "exclude_local": false,
  "include_aliases": false,
  "ignore": null,
  "log_dir": "/var/log/nms_tools",
  "log_max_mb": 50,
  "warnings": [
    "[WARN] Unable to write to log directory: /root/logs — [Errno 13] Permission denied: '/root/logs'"
  ]
}
```

| Field             | Type             | Description                                                          |
|-------------------|------------------|----------------------------------------------------------------------|
| `host`            | string           | Target hostname as provided via `-H`                                 |
| `ip`              | string           | Resolved IP address of the target                                    |
| `mode`            | string           | Host detection mode: `"local"` or `"remote"`                         |
| `script_name`     | string           | Script basename without extension (e.g., `"check_interfaces"`)       |
| `status_target`   | string           | Evaluation attribute (e.g., `"oper-status"`, `"duplex"`)             |
| `interface_count` | integer          | Total number of interfaces after filtering                           |
| `exclude_local`   | boolean          | Whether `--exclude-local` was specified                              |
| `include_aliases` | boolean          | Whether `--include-aliases` was specified                            |
| `ignore`          | string \| null   | Ignore pattern(s) provided via `--ignore`. `null` if not specified.  |
| `log_dir`         | string \| null   | Log directory path provided via `--log-dir`. `null` if not specified.|
| `log_max_mb`      | integer          | Log rotation threshold in MB                                         |
| `warnings`        | array of strings | **Conditional.** Present only when warnings were emitted during execution. Absent on clean runs. |

---

## `status`

Evaluation results for all interfaces against the selected `--status` attribute.

```json
"status": {
  "state": "OK",
  "failures": [],
  "results": {
    "eth0": { "ok": true, "value": "up" },
    "eth1": { "ok": false, "value": "down" }
  }
}
```

| Field      | Type             | Description                                                      |
|------------|------------------|------------------------------------------------------------------|
| `state`    | string           | Overall evaluation state: `"OK"`, `"CRITICAL"`, or `"UNKNOWN"`  |
| `failures` | array of strings | Interface names that failed evaluation. Empty when all pass.     |
| `results`  | object           | Per‑interface evaluation results, keyed by interface name        |

### Result Object

| Field   | Type    | Description                                                                  |
|---------|---------|------------------------------------------------------------------------------|
| `ok`    | boolean | Whether the interface passed the selected attribute check                    |
| `value` | string  | Evaluated value (e.g., `"up"`, `"down"`, `"full"`, `"not found"`)            |

### State Determination

| Condition                            | `state`      | Exit Code |
|--------------------------------------|--------------|-----------|
| `failures` is empty                  | `"OK"`       | 0         |
| `failures` contains one or more entries | `"CRITICAL"` | 2      |
| Infrastructure error                 | `"UNKNOWN"`  | 3         |

---

## Conditional Fields

| Field            | Condition                                                         |
|------------------|-------------------------------------------------------------------|
| `meta.warnings`  | Present only when at least one warning was emitted (e.g., log directory failure). Absent on clean runs. |
| `meta.log_dir`   | `null` when `--log-dir` is not specified                          |
| `meta.ignore`    | `null` when `--ignore` is not specified                           |

---

## Example — Clean Run

```json
{
  "interfaces": {
    "eth0": {
      "admin_up": true,
      "duplex": "full",
      "flags": ["UP", "RUNNING"],
      "ifType": null,
      "ipv4": [],
      "ipv6": [],
      "mac": "0c:c4:7a:32:c2:02",
      "mtu": 1500,
      "name": "eth0",
      "oper_up": true,
      "speed": 1000
    }
  },
  "meta": {
    "exclude_local": false,
    "host": "localhost",
    "ignore": null,
    "include_aliases": false,
    "interface_count": 1,
    "ip": "127.0.0.1",
    "log_dir": null,
    "log_max_mb": 50,
    "mode": "local",
    "script_name": "check_interfaces",
    "status_target": "oper-status"
  },
  "status": {
    "failures": [],
    "results": {
      "eth0": {
        "ok": true,
        "value": "up"
      }
    },
    "state": "OK"
  }
}
```

Note: `meta.warnings` is absent on clean runs — it is not emitted as an empty array.

---

## See Also

- [Usage.md](Usage.md) — CLI reference and examples
- [Operation.md](Operation.md) — Runtime behavior, output formatting, and logging lifecycle
- [Enforcement.md](Enforcement.md) — Filter pipeline, precedence, and edge cases
