# check_interfaces — Network Interface State & Attribute Monitoring Tool

![Python Version](https://img.shields.io/badge/python-3.6%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-stable-brightgreen)
![Nagios Plugin](https://img.shields.io/badge/Nagios-plugin-success)
![NMS_Tools](https://img.shields.io/badge/NMS_Tools-check__interfaces-blueviolet)

`check_interfaces.py` is an operator‑grade network interface monitoring plugin for Nagios and compatible monitoring systems.  
It provides deterministic interface discovery, attribute evaluation, and perfdata emission across both **local Linux hosts** and **remote SNMP devices**, using a unified, normalized interface schema.

The tool supports three output modes — **Nagios**, **verbose**, and **JSON** — making it equally suitable for alerting, diagnostics, and automation.

---

## Features

### ✔ Unified SNMP + Local Interface Discovery
- Local mode uses kernel interface data (`/sys/class/net`, psutil).
- Remote mode uses SNMPv2c (IF‑MIB).
- All interfaces are normalized into a consistent schema.

### ✔ Multiple Output Modes
- **Nagios single‑line** (default)
- **Verbose diagnostic mode** (`-v`)
- **JSON structured mode** (`-j`)
- **Quiet mode** (`-q`)

### ✔ Perfdata Mode
Select a single counter to emit as perfdata:

--perfdata in_octets
--perfdata out_errors
--perfdata in_errors
--perfdata out_errors
--perfdata in_discards
--perfdata out_discards
--perfdata in_ucast
--perfdata out_ucast
--perfdata in_multicast
--perfdata out_multicast
--perfdata in_broadcast
--perfdata out_broadcast

Perfdata is always raw (Nagios‑safe) and always included in single‑line output.

### ✔ Attribute‑Based Evaluation
Evaluate interfaces using:

- `oper-status` (default)
- `linkspeed`
- `duplex`
- `mtu`
- `flags`

Each interface produces an evaluation result; the global state is derived from failures.

### ✔ Canonical Filtering Pipeline
Operators can control which interfaces are evaluated using:

- `--ifaces` (explicit list or regex)
- `--ignore` (repeatable)
- `--exclude-local`
- `--include-aliases`

Filtering is deterministic and backend‑agnostic.

### ✔ Normalized Counters (IF‑MIB)
All counters follow the IF‑MIB model:

- Octets (in/out)
- Ucast (in/out)
- Multicast (in/out)
- Broadcast (in/out)
- Discards (in/out)
- Errors (in/out)
- Unknown protocols

### ✔ Clean Speed Normalization
Speeds are normalized to Mbps and displayed as:

- `10G`
- `1G`
- `100M`
- `10M`
- `-` (unknown)

### ✔ Nagios‑Compatible Exit Codes
Returns standard plugin exit codes:

- `0` OK  
- `1` WARNING  
- `2` CRITICAL  
- `3` UNKNOWN  

---

## Requirements

- Python 3.6+
- `pysnmp` (required for SNMP mode)
- SNMPv2c access for remote hosts
- Target hostname must be resolvable

---

## Quick Start

### Local Host

```bash
./check_interfaces.py -H localhost
```

### Remote Host (SNMP)

```bash
./check_interfaces.py -H switch01 -C public
```

### Evaluate Link Speed

```bash
./check_interfaces.py -H switch01 -C public --status linkspeed
```

### Select Perfdata Metric

```bash
./check_interfaces.py -H switch01 -C public --perfdata in_octets
```

### Verbose Diagnostic Output

```bash
./check_interfaces.py -H switch01 -C public -v
```

### JSON Output

```bash
./check_interfaces.py -H switch01 -C public -j | jq
```

### Exclude Local Interfaces

```bash
./check_interfaces.py -H switch01 -C public --exclude-local
```

### Ignore Interfaces by Pattern

```bash
./check_interfaces.py -H switch01 -C public --ignore "vnet.*" --ignore docker0
```

## Output Modes

### ✔ Nagios Mode (default)

Single‑line output with perfdata:

```Code
OK: all interfaces oper-status | eth0_in_octets=12345c br0_in_octets=67890c
```

### ✔ Verbose Mode (-v)

Human‑readable diagnostic output:

```Code
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
    Ucast:      In=34768217   Out=28905155
    ...
```

### ✔ JSON Mode (-j)
Structured output for automation:

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
      "counters": { ... }
    }
  },
  "status": { ... },
  "meta": { ... }
}
```

## Filtering

`check_interfaces.py` uses a canonical filtering pipeline to determine which interfaces are evaluated.  
Filtering is deterministic, backend‑agnostic, and applied identically in both SNMP and local modes.

### `--ifaces`
Select specific interfaces to evaluate. Supports:

- **Literal names**

```--ifaces eth0,eth1,br0```


- **Regex patterns**

```
--ifaces "eth[0-2]"
--ifaces "^br[0-9]+$"
```


- **Mixed literal + regex**

```--ifaces "eth0,eth1,^vnet[0-9]+$"```


The argument is parsed as a **single comma‑delimited expression**, where each element may be a literal or a regex.  
If any regex metacharacters are detected, that element is treated as a pattern.

### Additional Filters

| Flag               | Purpose                                                                    |
|--------------------|----------------------------------------------------------------------------|
| `--ignore`         | Ignore interfaces matching a substring or regex (repeatable)               |
| `--exclude-local`  | Exclude loopback and local‑only interfaces                                 |
| `--ignore-virtual` | Exclude virtual interfaces (e.g., `vnet*`, `virbr*`, `docker0`)            |
| `--include-aliases`| Include SNMP alias interfaces (e.g., `eth0:1`, `br0:backup`)               |

Filters are applied in a deterministic order to ensure consistent, reproducible results regardless of enumeration sequence.


## Exit Codes

| Code | Meaning |
| :---: | :--- |
| 0 | All interfaces OK |
| 1 | Non‑critical issues |
| 2 | Critical failure |
| 3 | Unknown / error |

SNMP failures return CRITICAL or UNKNOWN.

## Logging

Logging is **opt‑in** and disabled in default mode.

Enable logging:

```bash
./check_interfaces.py -H switch01 -C public -v --log-dir /var/log/nms_tools
```

Logging follows NMS_Tools conventions:

* Single‑line, timestamped entries
* Size‑based rotation
* No logging in default Nagios mode

## Document

| Document | Description |
|----------|-------------|
| [Installation.md](docs/Installation.md) | Installation and environment setup |
| [Usage.md](docs/Usage.md)        | Full CLI reference and examples |
| [Operation.md](docs/Operation.md)    | Discovery, normalization, and output pipeline |
| [Enforcement.md](docs/Enforcement.md)  | Status evaluation and filtering logic |
| [Metadata_schema.md](docs/Metadata_schema.md) | Normalized interface schema |

## License

Part of the **NMS_Tools** suite by Linktech Engineering LLC.
Licensed under MIT.

See the suite‑wide README for contributor guidelines and community standards.

---

# 🎯 **This README is now fully aligned with the tool’s current behavior**

It reflects:

- perfdata mode  
- verbose diagnostic output  
- JSON schema  
- normalized counters  
- speed formatting  
- SNMP/local parity  
- filtering pipeline  
- evaluation logic  
- logging behavior  
