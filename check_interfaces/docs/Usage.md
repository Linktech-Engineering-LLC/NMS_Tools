# Usage.md — CLI Reference & Examples

## Synopsis

```
check_interfaces.py -H <host> [-C <community>] [options]
```

---

## Required Arguments

| Flag            | Description                                                            |
|-----------------|------------------------------------------------------------------------|
| `-H`, `--host`  | Target hostname or IP address. Determines local vs. remote detection automatically. A resolvable hostname is required. |

---

## SNMP Options

Required for remote hosts. Ignored when the target is detected as local.

| Flag                  | Description                                           | Default      |
|-----------------------|-------------------------------------------------------|--------------|
| `-C`, `--community`   | SNMPv2c community string. Required for remote hosts. | —            |
| `-p`, `--snmp-port`   | SNMP port on the target device.                      | `161`        |
| `-T`, `--snmp-timeout` | SNMP‑specific timeout in seconds. Overrides `--timeout` for SNMP operations. If not specified, falls back to `--timeout`. | —  |

---

## Evaluation

| Flag               | Description                                                        | Default        |
|--------------------|--------------------------------------------------------------------|----------------|
| `--status <attr>`  | Attribute to evaluate on each interface. See **Evaluation Attributes** below. | `oper-status` |

### Evaluation Attributes

| Value          | Evaluates                                                                |
|----------------|--------------------------------------------------------------------------|
| `oper-status`  | Operational status — is the interface up?                                |
| `admin-status` | Administrative status — is the interface enabled?                        |
| `linkspeed`    | Negotiated link speed — is a non‑zero speed reported?                    |
| `duplex`       | Duplex mode — is full‑duplex negotiated? (bridges pass automatically)    |
| `mtu`          | MTU value — is a valid MTU reported?                                     |
| `alias`        | Alias identity — is the interface an alias (e.g., `eth0:1`)?             |

All attribute violations result in **CRITICAL**. There is no WARNING tier. See [Enforcement.md](Enforcement.md) for detailed evaluation rules and edge cases.

---

## Filtering & Selection

| Flag                  | Description                                                              | Repeatable |
|-----------------------|--------------------------------------------------------------------------|------------|
| `--ifaces <list>`     | Comma‑delimited list of interfaces to target. Supports literal, substring, and regex matching. | No |
| `--ignore <pattern>`  | Exclude interfaces matching a substring or regex pattern.                | Yes        |
| `--ignore-virtual`    | Exclude virtual interfaces (vnet\*, virbr\*, docker0, etc.).              | No         |
| `--exclude-local`     | Exclude loopback and local‑only interfaces (e.g., `lo`).                 | No         |
| `--include-aliases`   | Include alias interfaces (excluded by default).                          | No         |

> **Pipeline order:** Filters are applied before selection. An interface removed by `--ignore-virtual` cannot be targeted by `--ifaces`. See [Enforcement.md](Enforcement.md) for the full pipeline and precedence rules.

---

## Output Modes

| Flag                    | Mode    | Description                                                     |
|-------------------------|---------|-----------------------------------------------------------------|
| *(default)*             | Nagios  | Single‑line output with exit code. Logging is disabled.          |
| `-v`, `--verbose`       | Verbose | Tabular per‑interface output with header block. Logging eligible.|
| `-j`, `--json`          | JSON    | Structured JSON output with full metadata. Logging eligible.     |

Only one output mode can be active at a time. If both `-j` and `-v` are specified, `-j` is evaluated first and the tool exits after JSON output.

---

## Logging

Logging is opt‑in and only available in verbose and JSON modes. Disabled in default Nagios mode.

| Flag                  | Description                                            | Default  |
|-----------------------|--------------------------------------------------------|----------|
| `--log-dir <path>`    | Directory for log output. Created automatically if it does not exist; parent path must be writable. | —  |
| `--log-max-mb <size>` | Maximum log file size in MB before rotation.           | `50`     |

---

## General

| Flag              | Description                                      | Default |
|-------------------|--------------------------------------------------|---------|
| `--timeout <sec>` | General operation timeout in seconds.            | `5`     |
| `-V`, `--version` | Print version and exit.                          | —       |

---

## Examples

### Basic — Local Host

Check all local interfaces for operational status:

```bash
./check_interfaces.py -H localhost
```

Verbose output for diagnostics:

```bash
./check_interfaces.py -H localhost -v
```

### Basic — Remote Host

Check all interfaces on a switch via SNMP:

```bash
./check_interfaces.py -H switch01.example.com -C public
```

### Targeted Interfaces

Monitor specific uplinks:

```bash
./check_interfaces.py -H switch01 -C public --ifaces "GigabitEthernet0/1,GigabitEthernet0/2"
```

Monitor interfaces matching a regex pattern:

```bash
./check_interfaces.py -H switch01 -C public --ifaces "GigabitEthernet0/[0-3]"
```

### Attribute Checks

Check link speed on all interfaces:

```bash
./check_interfaces.py -H switch01 -C public --status linkspeed
```

Check duplex negotiation:

```bash
./check_interfaces.py -H switch01 -C public --status duplex
```

Verify MTU configuration:

```bash
./check_interfaces.py -H switch01 -C public --status mtu
```

Identify alias interfaces:

```bash
./check_interfaces.py -H switch01 -C public --status alias
```

### Filtering

Exclude virtual and local interfaces:

```bash
./check_interfaces.py -H linux-server01 --ignore-virtual --exclude-local
```

Exclude specific interfaces by pattern:

```bash
./check_interfaces.py -H switch01 -C public --ignore "vnet.*" --ignore "docker0"
```

Include alias interfaces (excluded by default):

```bash
./check_interfaces.py -H switch01 -C public --include-aliases
```

### Combined Filtering and Selection

Monitor physical uplinks, excluding management interfaces:

```bash
./check_interfaces.py -H switch01 -C public --ignore "mgmt" --ifaces "GigabitEthernet0/[0-9]"
```

### JSON Output

Full structured output for automation or dashboards:

```bash
./check_interfaces.py -H switch01 -C public -j
```

### Logging

Enable logging with verbose output:

```bash
./check_interfaces.py -H switch01 -C public -v --log-dir /var/log/nms_tools
```

With a custom log rotation threshold:

```bash
./check_interfaces.py -H switch01 -C public -v --log-dir /var/log/nms_tools --log-max-mb 100
```

### SNMP Options

Non‑standard SNMP port:

```bash
./check_interfaces.py -H switch01 -C public -p 1161
```

Extended SNMP timeout for slow devices:

```bash
./check_interfaces.py -H switch01 -C public -T 30
```

---

## Exit Codes

| Code | Status   | Meaning                                                                  |
|------|----------|--------------------------------------------------------------------------|
| 0    | OK       | All evaluated interfaces pass the selected attribute check               |
| 2    | CRITICAL | One or more failures: attribute violation, missing `--ifaces` target, or SNMP failure |
| 3    | UNKNOWN  | Unreachable host, invalid arguments, timeout, or unhandled error         |

There is no WARNING (exit code 1) in the current evaluation model.

---

## See Also

- [Installation.md](Installation.md) — Deployment and Nagios integration
- [Enforcement.md](Enforcement.md) — Filter pipeline, precedence, and edge cases
- [Operation.md](Operation.md) — Operational behavior, logging lifecycle, and output formatting
- [Metadata_schema.md](Metadata_schema.md) — JSON output schema reference
