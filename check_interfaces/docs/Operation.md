# Operation.md — Runtime Behavior, Output & Logging

## Overview

This document describes the internal runtime lifecycle of `check_interfaces.py` — how it discovers interfaces, retrieves counters, applies filters, produces output, manages logs, and determines exit state.

For CLI usage, see Usage.md.  
For the filter pipeline and evaluation rules, see Enforcement.md.  
For the JSON output schema, including counters, see Metadata_schema.md.

---

## Runtime Lifecycle

 1. Parse arguments  
 2. Detect host type (local or SNMP)  
 3. Discover interfaces  
 4. Retrieve counters (SNMP only)  
 5. Apply filters  
 6. Apply selection  
 7. Evaluate interfaces  
 8. Assemble results  
 9. Emit output (JSON → verbose → Nagios)  
10. Exit with status code  

---

## Host Detection

The tool automatically determines whether the target is local or remote based on the `-H` value.

| Condition                        | Mode   | Discovery Method       |
|----------------------------------|--------|------------------------|
| Host resolves to local address   | local  | Kernel                 |
| Host resolves to remote address  | snmp   | SNMPv2c IF‑MIB         |

A resolvable hostname is required. If DNS resolution fails, the tool exits with UNKNOWN.

SNMP flags (`-C`, `-p`, `-T`) are ignored when the host is detected as local.

---

## Discovery

### Local Discovery

Local mode retrieves:

- interface names  
- MAC addresses  
- MTU  
- flags  
- admin/oper status  
- IPv4/IPv6 addresses  
- speed (if available)  

Local mode **does not** retrieve counters.

### SNMP Discovery

SNMP mode retrieves:

- all fields retrieved in local mode  
- SNMP IF‑MIB counters  
- SNMP ifType  
- SNMP‑reported speed  

SNMP parameters:

- Port: `-p` (default 161)  
- Timeout: `-T` (default 5 seconds)  
- Community: `-C` (required)  

SNMP failures (timeout, unreachable host, authentication failure) result in CRITICAL or UNKNOWN.

---

## Counter Retrieval (SNMP Only)

When operating in SNMP mode, the tool retrieves the following counters per interface:

Inbound:

- in_octets  
- in_ucast  
- in_multicast  
- in_broadcast  
- in_discards  
- in_errors  
- in_unknown (if supported by device)

Outbound:

- out_octets  
- out_ucast  
- out_multicast  
- out_broadcast  
- out_discards  
- out_errors  

Counters appear in JSON output under:

`interfaces.<name>.counters`


Counters are **not displayed** in verbose mode.

---

## Filtering and Selection

Filtering and selection follow the deterministic pipeline described in Enforcement.md:

1. Alias filtering  
2. Virtual filtering  
3. Local filtering  
4. Pattern ignore  
5. Selection via `--ifaces`  

Filters always run before selection.

Unmatched `--ifaces` patterns are injected as synthetic failures.

---

## Evaluation

Each surviving interface is evaluated against the attribute selected via `--status`.

Evaluation is binary:

- pass → OK  
- fail → CRITICAL  

There is no WARNING tier.

Evaluation rules are defined in Enforcement.md.

---

## Output Modes

Output mode is determined in this order:

1. JSON (`-j`)  
2. Verbose (`-v`)  
3. Nagios (default)  

Only one mode is active per invocation.

### JSON Mode (`-j`)

JSON mode emits:

- interfaces (full metadata including counters)  
- meta (host, mode, filters, log settings, warnings)  
- status (results, failures, state)  

Speed is raw integer Mbps.  
Counters are included for SNMP mode.

Warnings appear only when present.

Logging is active when `--log-dir` is specified.

### Verbose Mode (`-v`)

Verbose mode emits:

- header block  
- table of interfaces  
- evaluation results  
- warnings (if any)  

Verbose mode **does not** display counters.

Logging is active when `--log-dir` is specified.

### Nagios Mode (default)

Nagios mode emits a single line:

`INTERFACES OK - 7 interfaces checked, 0 failures | ifaces=7 failures=0`


Nagios mode:

- does not log  
- does not show counters  
- does not show warnings  
- is always single‑line  

Perfdata includes:

- ifaces  
- failures  

---

## Logging

Logging is **opt‑in** and only active in verbose and JSON modes.

### Activation

Logging is enabled when:

- `--log-dir` is specified  
- AND output mode is verbose or JSON  

Nagios mode never logs.

### Log Directory Behavior

- The tool attempts to create the directory if missing  
- Parent directory must be writable  
- If creation fails:

  - Verbose mode prints a `[WARN]` line  
  - JSON mode adds a warning to `meta.warnings`  
  - Logging is disabled for the run  

### Log File Naming

`<log-dir>/check_interfaces.log`


### Log Rotation

Logs rotate when exceeding `--log-max-mb` (default 50 MB).

### Log Content

Each log entry is a single‑line timestamped record containing:

- interface evaluation results  
- SNMP connection events  
- filter decisions  
- unmatched pattern notices  

---

## Error Handling

### SNMP Failures

| Failure Type          | Exit Code | Status     |
|-----------------------|-----------|------------|
| Host unreachable      | 3         | UNKNOWN    |
| Timeout               | 3         | UNKNOWN    |
| Authentication error  | 2         | CRITICAL   |
| Invalid OIDs          | 2         | CRITICAL   |

### DNS Resolution Failure

Unresolvable hostname → UNKNOWN (exit code 3).

### Invalid Arguments

Invalid or conflicting arguments → UNKNOWN (exit code 3).

### Unmatched `--ifaces` Patterns

Unmatched patterns:

- are injected into results  
- appear in `status.failures`  
- force CRITICAL  

---

## Exit Code Determination

| Condition                                | Exit Code | Status     |
|------------------------------------------|-----------|------------|
| All interfaces pass                      | 0         | OK         |
| Any failures or unmatched patterns       | 2         | CRITICAL   |
| Infrastructure error                     | 3         | UNKNOWN    |

There is no WARNING tier.

---

## See Also

[Installation.md](Installation.md)
[Usage.md](Usage.md)
[Enforcement.md](Enforcement.md)
[Metadata_schema.md](Metadata_schema.md)
