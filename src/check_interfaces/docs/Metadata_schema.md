# Metadata_schema.md — JSON Output Schema Reference

## Overview

This document defines the JSON output schema produced by `check_interfaces.py` when invoked with -j or --json. The output is a single JSON object with three top‑level keys: interfaces, meta, and status.

---

## Top‑Level Structure

{
  "interfaces": { ... },
  "meta": { ... },
  "status": { ... }
}

| Key        | Type   | Description                                          |
|------------|--------|------------------------------------------------------|
| interfaces | object | Per‑interface metadata, keyed by interface name      |
| meta       | object | Operational metadata for the invocation              |
| status     | object | Evaluation results and overall state                 |

---

## interfaces

An object where each key is an interface name and each value is an interface metadata object.

Example:

"interfaces": {
  "eth0": { ... },
  "br0": { ... }
}

### Interface Object

| Field     | Type             | Description                                                        |
|-----------|------------------|--------------------------------------------------------------------|
| name      | string           | Interface name                                                     |
| mac       | string           | MAC address (normalized; zeroed if unavailable)                    |
| mtu       | integer          | Maximum transmission unit                                          |
| speed     | integer or null  | Negotiated link speed in Mbps; null if unavailable                 |
| duplex    | string           | "full", "half", "unknown", or "n/a" for bridge interfaces          |
| admin_up  | boolean          | Administrative status                                              |
| oper_up   | boolean          | Operational status                                                 |
| flags     | array of strings | Kernel flags                                                       |
| ifType    | integer or null  | SNMP IF‑MIB type; null for local discovery                         |
| ipv4      | array of objects | IPv4 addresses; see Address Object                                 |
| ipv6      | array of objects | IPv6 addresses; see Address Object                                 |
| counters  | object           | Traffic counters; see Counters Object                              |

### Address Object

| Field     | Type            | Description                                                    |
|-----------|-----------------|----------------------------------------------------------------|
| address   | string          | IP address                                                     |
| netmask   | string          | Subnet mask                                                    |
| broadcast | string or null  | Broadcast address or null                                      |

### Counters Object

These counters come directly from IF‑MIB and EtherLike‑MIB.

| Field          | Type    | Description                                 |
|----------------|---------|---------------------------------------------|
| in_octets      | integer | Total inbound octets                        |
| in_ucast       | integer | Inbound unicast packets                     |
| in_multicast   | integer | Inbound multicast packets                   |
| in_broadcast   | integer | Inbound broadcast packets                   |
| in_discards    | integer | Inbound discards                            |
| in_errors      | integer | Inbound errors                              |
| in_unknown     | integer | Inbound unknown protocol packets (if present) |
| out_octets     | integer | Total outbound octets                       |
| out_ucast      | integer | Outbound unicast packets                    |
| out_multicast  | integer | Outbound multicast packets                  |
| out_broadcast  | integer | Outbound broadcast packets                  |
| out_discards   | integer | Outbound discards                           |
| out_errors     | integer | Outbound errors                             |

Note: Some devices omit in_unknown; the field may be absent.

---

## meta

Operational metadata describing the invocation context, host detection, and active filters.

Example:

"meta": {
  "host": "mom",
  "ip": "192.168.0.2",
  "mode": "snmp",
  "script_name": "check_interfaces",
  "status_target": "oper-status",
  "interface_count": 7,
  "exclude_local": true,
  "include_aliases": false,
  "ignore": null,
  "log_dir": null,
  "log_max_mb": 50
}

### Meta Fields

| Field           | Type             | Description                                                          |
|-----------------|------------------|----------------------------------------------------------------------|
| host            | string           | Target hostname from -H                                              |
| ip              | string           | Resolved IP address                                                  |
| mode            | string           | "local" or "snmp"                                                    |
| script_name     | string           | Basename of the script                                               |
| status_target   | string           | Attribute selected via --status                                      |
| interface_count | integer          | Number of interfaces after filtering                                 |
| exclude_local   | boolean          | Whether --exclude-local was used                                     |
| include_aliases | boolean          | Whether --include-aliases was used                                   |
| ignore          | array or null    | List of ignore patterns, or null                                     |
| log_dir         | string or null   | Log directory path, or null                                          |
| log_max_mb      | integer          | Log rotation threshold                                               |
| warnings        | array of strings | Present only when warnings were emitted                              |

Note: warnings is omitted entirely when no warnings occur.

---

## status

Evaluation results and overall state for the selected attribute.

Example:

"status": {
  "state": "OK",
  "failures": [],
  "results": {
    "eth0": { "ok": true, "value": "up" }
  }
}

### Status Fields

| Field     | Type             | Description                                                      |
|-----------|------------------|------------------------------------------------------------------|
| state     | string           | "OK", "CRITICAL", or "UNKNOWN"                                  |
| failures  | array of strings | Names of interfaces or patterns that failed                     |
| results   | object           | Per‑interface evaluation results                                |

### Result Object

| Field | Type    | Description                                                                  |
|-------|---------|------------------------------------------------------------------------------|
| ok    | boolean | Whether the interface passed the selected attribute check                    |
| value | string  | Evaluated value ("up", "down", "full", "not found", etc.)                    |

### State Determination

| Condition                            | state        | Exit Code |
|--------------------------------------|--------------|-----------|
| No failures                          | OK           | 0         |
| One or more failures                 | CRITICAL     | 2         |
| Infrastructure error                 | UNKNOWN      | 3         |

---

## Example — Clean Run

{
  "interfaces": {
    "eth0": {
      "admin_up": true,
      "duplex": "full",
      "flags": ["UP", "RUNNING"],
      "ifType": 6,
      "ipv4": [],
      "ipv6": [],
      "mac": "0c:c4:7a:32:c2:02",
      "mtu": 1500,
      "name": "eth0",
      "oper_up": true,
      "speed": 1000,
      "counters": {
        "in_broadcast": 0,
        "in_discards": 0,
        "in_errors": 0,
        "in_multicast": 0,
        "in_octets": 123456,
        "in_ucast": 789,
        "out_broadcast": 0,
        "out_discards": 0,
        "out_errors": 0,
        "out_multicast": 0,
        "out_octets": 654321,
        "out_ucast": 987
      }
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

---

## See Also

[Usage.md](Usage.md)
[Operation.md](Operation.md)  
[Enforcement.md](Enforcement.md)
