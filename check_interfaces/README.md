# check_interfaces — Network Interface State & Attribute Monitoring Tool

![Python Version](https://img.shields.io/badge/python-3.6%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-stable-brightgreen)
![Nagios Plugin](https://img.shields.io/badge/Nagios-plugin-success)
![NMS_Tools](https://img.shields.io/badge/NMS_Tools-check__interfaces-blueviolet)

`check_interfaces.py` is an operator‑grade network interface monitoring plugin for Nagios and compatible monitoring systems.  
It performs deterministic, rule‑driven validation of interface state, speed, and attributes across local and remote network devices, with canonical filtering and enforcement logic built for production infrastructure.

---

## Features

- **Local / Remote Auto‑Detection** — Automatically determines whether the target host is local or remote. Local hosts are inspected using kernel interface data; remote hosts are inspected via SNMPv2c using IF‑MIB.
- **Attribute‑Based Evaluation** — Validates interfaces against a selectable attribute: operational status, administrative status, link speed, duplex, MTU, or alias.
- **Canonical Filtering** — Operators control which interfaces are evaluated using alias inclusion, virtual exclusion, local exclusion, pattern‑based ignore rules, and explicit interface targeting.
- **Deterministic Output** — Produces clean, predictable output suitable for operator review, automated parsing, and Nagios integration.
- **Nagios‑Compatible Exit Codes** — Returns standard plugin exit codes (OK, WARNING, CRITICAL, UNKNOWN) for direct integration with Nagios, Icinga, and compatible monitoring platforms.
- **Perfdata Output** — Emits valid performance data parseable by standard Nagios graphing and trending tools.
- **Multiple Output Modes** — Supports verbose, JSON, and quiet modes alongside the default Nagios‑compatible output.
- **Opt‑In Logging** — When a log directory is specified via `--log-dir`, appends timestamped, single‑line entries with configurable size‑based rotation. Logging is disabled in default (Nagios) mode.

---

## Requirements

- Python 3.6+
- [pysnmp](https://pysnmp.readthedocs.io/) — SNMPv2c interface discovery (required for remote hosts)
- SNMPv2c access to the target device (required for remote hosts only)
- Target hostname must be DNS‑resolvable or reachable by IP

---

## Quick Start

```bash
# Local host — uses kernel interface data automatically
./check_interfaces.py -H localhost

# Remote host — requires SNMP community string
./check_interfaces.py -H switch01.example.com -C public

# Evaluate link speed instead of operational status
./check_interfaces.py -H switch01.example.com -C public --status linkspeed

# Check specific interfaces only
./check_interfaces.py -H switch01.example.com -C public --ifaces "GigabitEthernet0/1,GigabitEthernet0/2"

# Exclude virtual and loopback interfaces
./check_interfaces.py -H switch01.example.com -C public --ignore-virtual --exclude-local

# Ignore interfaces matching a pattern (repeatable)
./check_interfaces.py -H switch01.example.com -C public --ignore "vnet.*" --ignore "docker0"

# Verbose output for diagnostics
./check_interfaces.py -H switch01.example.com -C public -v

# JSON output for automation
./check_interfaces.py -H switch01.example.com -C public -j

# Enable logging with custom directory
./check_interfaces.py -H switch01.example.com -C public -v --log-dir /var/log/nms_tools
```

> **Note:** Full CLI reference, argument details, and advanced usage patterns are documented in [Usage.md](docs/Usage.md).

---

## Attribute Evaluation

The `--status` flag selects which interface attribute is validated. Defaults to `oper-status`.

| Attribute      | Evaluates                                                        |
|----------------|------------------------------------------------------------------|
| `oper-status`  | Operational state of each interface (up/down)                    |
| `admin-status` | Administrative state (enabled/disabled)                          |
| `linkspeed`    | Negotiated link speed against expected thresholds                |
| `duplex`       | Duplex mode (full/half)                                          |
| `mtu`          | Maximum transmission unit value                                  |
| `alias`        | Interface alias or description field                             |

---

## Filtering

`check_interfaces.py` uses a canonical filtering pipeline to determine which interfaces are evaluated. Connection types are detected automatically — operators control filtering through explicit flags:

| Flag               | Purpose                                                                    |
|--------------------|----------------------------------------------------------------------------|
| `--ifaces`         | Target specific interfaces by name (comma‑delimited) or regex pattern      |
| `--include-aliases`| Include alias interfaces (e.g., `eth0:1`, `br0:backup`) in discovery       |
| `--ignore-virtual` | Exclude virtual interfaces (e.g., `vnet*`, `virbr*`, `docker0`)            |
| `--exclude-local`  | Exclude local‑only interfaces such as `lo`                                 |
| `--ignore`         | Ignore interfaces matching a substring or regex pattern (repeatable)       |

Filters are applied in a deterministic order to ensure consistent, reproducible results regardless of enumeration sequence.

> **Note:** Detailed enforcement logic, filter precedence, and edge‑case behavior are documented in [Enforcement.md](docs/Enforcement.md).

---

## Output Modes

| Mode                | Description                                                                      |
|---------------------|----------------------------------------------------------------------------------|
| Default             | Clean, single‑line status output with perfdata — suitable for Nagios integration |
| `-v`, `--verbose`   | Extended diagnostics including per‑interface state, filtered entries, and reasons |
| `-j`, `--json`      | Structured JSON output for programmatic consumption and automation               |
| `-q`, `--quiet`     | Exit code only — no stdout output                                                |

In default (Nagios) mode, output is a single clean status line with exit code. All diagnostic detail is suppressed unless `-v` is explicitly specified. Logging is disabled in default mode.

---

## Exit Codes

| Code | Status   | Meaning                                                    |
|------|----------|------------------------------------------------------------|
| 0    | OK       | All evaluated interfaces pass validation                   |
| 1    | WARNING  | One or more interfaces have non‑critical attribute issues  |
| 2    | CRITICAL | Interface down, SNMP failure, or required interface missing|
| 3    | UNKNOWN  | Unreachable host, invalid arguments, or unhandled error    |

SNMP connection failures return CRITICAL or UNKNOWN — never WARNING.

---

## Logging

Logging is **opt‑in** and **disabled in default (Nagios) mode** to keep Nagios output clean and deterministic.

To enable logging, specify a log directory with `--log-dir`:

```bash
./check_interfaces.py -H switch01.example.com -C public -v --log-dir /var/log/nms_tools
```

| Option          | Description                                           | Default     |
|-----------------|-------------------------------------------------------|-------------|
| `--log-dir DIR` | Directory to store logs; logging disabled if omitted   | *(disabled)*|
| `--log-max-mb MB`| Maximum log file size in MB before rotation           | 50          |

When enabled, logging follows NMS_Tools suite conventions:

- **Format:** Single‑line, timestamped entries for deterministic audit trails
- **Mode:** Append‑only with size‑based rotation
- **Gating:** Diagnostic detail stays in verbose output; the log captures operational events

---

## Documentation

| Document                                       | Description                                   |
|------------------------------------------------|-----------------------------------------------|
| [Usage.md](docs/Usage.md)                      | Complete CLI reference and argument details    |
| [Operation.md](docs/Operation.md)              | Operational behavior, inspection internals     |
| [Enforcement.md](docs/Enforcement.md)          | Filter pipeline, precedence, and edge cases    |

---

## License

This tool is part of the **NMS_Tools** suite by [Linktech Engineering LLC](https://github.com/Linktech-Engineering).  
Licensed under the [MIT License](../LICENSE).

See the [NMS_Tools README](../README.md) for suite‑wide documentation, community standards, and contributor guidelines.
