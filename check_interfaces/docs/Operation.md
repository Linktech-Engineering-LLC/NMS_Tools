# Operation.md — Runtime Behavior, Output & Logging

## Overview

This document describes the internal runtime lifecycle of `check_interfaces.py` — how it discovers interfaces, produces output, manages logs, and determines exit state. For CLI flags and examples, see [Usage.md](Usage.md). For the filter pipeline and evaluation rules, see [Enforcement.md](Enforcement.md). For the JSON output schema, see [Metadata_schema.md](Metadata_schema.md).

---

## Runtime Lifecycle

```
 ┌──────────────────────────────┐
 │  1. Parse arguments          │
 └──────────────┬───────────────┘
                │
 ┌──────────────▼───────────────┐
 │  2. Detect host type         │  ← Local or remote (automatic)
 └──────────────┬───────────────┘
                │
 ┌──────────────▼───────────────┐
 │  3. Discover interfaces      │  ← Kernel (local) or SNMP (remote)
 └──────────────┬───────────────┘
                │
 ┌──────────────▼───────────────┐
 │  4. Apply filters            │  ← alias → virtual → local → ignore
 └──────────────┬───────────────┘
                │
 ┌──────────────▼───────────────┐
 │  5. Apply selection          │  ← --ifaces targeting
 └──────────────┬───────────────┘
                │
 ┌──────────────▼───────────────┐
 │  6. Evaluate interfaces      │  ← --status attribute check
 └──────────────┬───────────────┘
                │
 ┌──────────────▼───────────────┐
 │  7. Assemble results         │  ← Merge evaluated + unmatched
 └──────────────┬───────────────┘
                │
 ┌──────────────▼───────────────┐
 │  8. Emit output              │  ← JSON → verbose → Nagios (first match)
 └──────────────┬───────────────┘
                │
 ┌──────────────▼───────────────┐
 │  9. Exit with status code    │  ← 0 (OK), 2 (CRITICAL), 3 (UNKNOWN)
 └──────────────────────────────┘
```

---

## Host Detection

The tool automatically determines whether the target is local or remote based on the `-H` value. No manual flag is required.

| Condition                              | Detection | Discovery Method     |
|----------------------------------------|-----------|----------------------|
| `-H` resolves to a local address       | Local     | Kernel interface data |
| `-H` resolves to a remote address      | Remote    | SNMPv2c via IF‑MIB    |

A resolvable hostname is required in all cases. If the hostname cannot be resolved, the tool exits with UNKNOWN.

When the target is detected as local, SNMP options (`-C`, `-p`, `-T`) are silently ignored. Kernel interface data is used regardless of any SNMP configuration provided.

---

## Discovery

### Local Discovery

Reads interface metadata directly from the kernel. No external dependencies or credentials are required.

### SNMP Discovery

Connects to the target device via SNMPv2c and walks the IF‑MIB interface table. Requires a community string (`-C`).

- **Port:** Configurable via `-p` (default: `161`)
- **Timeout:** Configurable via `-T` (falls back to `--timeout` if not specified; global default: `5` seconds)
- **Failure:** SNMP connection failures (unreachable host, authentication failure, timeout) result in CRITICAL or UNKNOWN — never WARNING or OK

---

## Output Modes

The tool supports three output modes. Output mode is determined by checking `-j` / `--json` first, then `-v` / `--verbose`. If neither is specified, Nagios mode is used. Only one mode is active per invocation. If both `-j` and `-v` are specified, `-j` is evaluated first and the tool exits after JSON output.

### Nagios Mode (Default)

Produces a single‑line status string followed by an exit code. This is the format expected by Nagios, Icinga, and compatible monitoring platforms.

```
INTERFACES OK - 12 interfaces checked, 0 failures | ifaces=12 failures=0
```

```
INTERFACES CRITICAL - 12 interfaces checked, 2 failures | ifaces=12 failures=2
```

- **First field:** `INTERFACES` prefix followed by the status word (`OK`, `CRITICAL`, `UNKNOWN`)
- **Summary:** Interface count and failure count
- **Perfdata:** Pipe‑delimited performance data appended after `|`
- **Logging:** Disabled. Nagios mode produces no log output regardless of `--log-dir`.

### Verbose Mode (`-v`, `--verbose`)

Produces structured, tabular output with per‑interface results. Intended for interactive diagnostics and troubleshooting.

```
Interface Summary (local)
Host: localhost (127.0.0.1)
Interfaces: 6
Status Target: oper-status

Name       MAC                  MTU    Speed   Duplex   Admin  Oper   Eval     Flags
------------------------------------------------------------------------------------
br0        0c:c4:7a:32:c2:02    1500   10K     unknown  up     up     OK       UP,RUNNING
eth0       0c:c4:7a:32:c2:02    1500   1K      full     up     up     OK       UP,RUNNING
lo         00:00:00:00:00:00    65536  -       unknown  up     up     OK       UP,RUNNING
```

- **Header block** — Detection mode (`local` or `remote`), resolved host and IP, interface count, and status target
- **Table columns** — Name, MAC, MTU, Speed, Duplex, Admin, Oper, Eval, Flags
- **Speed** — Human‑readable format (e.g., `1K` = 1000 Mbps, `10K` = 10000 Mbps, `-` = unavailable)
- **Warnings** — Appended after the table with a `[WARN]` prefix when applicable
- **Logging** — Eligible. Log output is written when `--log-dir` is specified.

### JSON Mode (`-j`, `--json`)

Produces structured JSON output with three top‑level keys:

| Key            | Contents                                                         |
|----------------|------------------------------------------------------------------|
| `interfaces`   | Per‑interface metadata: name, MAC, MTU, speed (raw), duplex, admin/oper status, flags, IPv4/IPv6 addresses, ifType |
| `meta`         | Operational metadata: host, IP, detection mode (`local` or `remote`), status target, filters, interface count, log settings |
| `status`       | Evaluation results: per‑interface pass/fail, failures list, overall state (`OK`, `CRITICAL`, `UNKNOWN`) |

- **Speed** — Raw integer (e.g., `1000`, `10000`, `null` if unavailable)
- **Warnings** — Present in `meta.warnings` array only when a warning was emitted (e.g., log directory failure). Absent on clean runs.
- **Logging** — Eligible. Log output is written when `--log-dir` is specified.

For full field definitions and data types, see [Metadata_schema.md](Metadata_schema.md).

---

## Performance Data (Perfdata)

In Nagios mode, performance data is appended to the status line after the `|` delimiter. This data is consumed by Nagios for graphing and trend analysis.

| Metric     | Description                              |
|------------|------------------------------------------|
| `ifaces`   | Total number of interfaces evaluated     |
| `failures` | Number of interfaces that failed evaluation |

```
| ifaces=12 failures=0
```

Perfdata is only emitted in Nagios mode. Verbose and JSON modes include equivalent data in their own formats.

---

## Logging

Logging is **opt‑in** and only active in verbose and JSON modes. Nagios mode disables logging entirely to ensure clean single‑line output.

### Activation

Logging is enabled when `--log-dir` is specified and the output mode is verbose or JSON.

### Log File Naming

Log files follow the NMS_Tools convention:

```
<log-dir>/check_interfaces.log
```

The log file is named after the script basename with `.log` appended.

### Log Creation

- The tool attempts to create the log directory if it does not exist.
- The parent path of `--log-dir` must be writable by the executing user.
- If the log directory cannot be created or is not writable:
  - **Verbose mode:** A `[WARN]` line is appended after the interface table. The tool continues without logging.
  - **JSON mode:** The failure is included in `meta.warnings` with a `[WARN]` prefix. The tool continues without logging.
  - **Nagios mode:** Logging is disabled by design; this condition does not apply.
- The warning is emitted once per invocation regardless of how many log writes are attempted.

### Log Rotation

Log files are rotated when they exceed the size threshold specified by `--log-max-mb` (default: `50` MB).

### Log Content

Log entries are single‑line, timestamped records. Each invocation produces:

- Interface evaluation results via `log_interface()`
- Filter decisions (when applicable)
- SNMP connection events (when applicable)

---

## Error Handling

### SNMP Failures

| Failure                  | Exit Code | Status   |
|--------------------------|-----------|----------|
| Host unreachable         | 2 or 3   | CRITICAL or UNKNOWN |
| Authentication failure   | 2 or 3   | CRITICAL or UNKNOWN |
| SNMP timeout             | 2 or 3   | CRITICAL or UNKNOWN |

SNMP connection failures never produce OK or WARNING. An inability to reach the target is treated as a monitoring failure.

### DNS Resolution

If the hostname provided via `-H` cannot be resolved, the tool exits with UNKNOWN (exit code 3).

### Invalid Arguments

Invalid or conflicting arguments cause the tool to exit with UNKNOWN (exit code 3) and an error message.

### Unmatched `--ifaces` Patterns

Patterns specified in `--ifaces` that do not match any interface in the filtered set are injected into the results as CRITICAL failures with a value of `"not found"`. The tool does not abort on the first miss — all patterns are resolved before the result is assembled.

---

## Exit Code Determination

The final exit code is determined after all interfaces have been evaluated and all `--ifaces` patterns have been resolved.

| Condition                                          | Exit Code | Status   |
|----------------------------------------------------|-----------|----------|
| All interfaces pass, no unmatched patterns         | 0         | OK       |
| One or more attribute failures or unmatched patterns | 2       | CRITICAL |
| Infrastructure error (DNS, timeout, invalid args)  | 3         | UNKNOWN  |

The evaluation is binary — if the failures list is non‑empty, the exit code is CRITICAL. There is no WARNING tier.

---

## See Also

- [Installation.md](Installation.md) — Deployment and Nagios integration
- [Usage.md](Usage.md) — CLI reference and examples
- [Enforcement.md](Enforcement.md) — Filter pipeline, precedence, and edge cases
- [Metadata_schema.md](Metadata_schema.md) — JSON output schema reference
