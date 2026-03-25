# Enforcement.md — Filter Pipeline, Precedence & Edge Cases

## Overview

`check_interfaces.py` uses a two‑phase pipeline — **filtering** then **selection** — to determine which interfaces are discovered, evaluated, and reported. Phases are applied in a deterministic order to ensure consistent, reproducible results regardless of interface enumeration sequence.

This document describes the pipeline phases, the precedence rules that govern their interaction, attribute evaluation behavior, and edge cases.

---

## Discovery Model

Before any filtering or selection is applied, `check_interfaces.py` builds a complete interface inventory from the target host:

| Host Type | Discovery Method                                       |
|-----------|--------------------------------------------------------|
| Local     | Kernel interface data (detected automatically)         |
| Remote    | SNMPv2c via IF‑MIB (requires `-C` community string)   |

The tool determines whether the target is local or remote automatically based on the `-H` value. No manual flag is required.

---

## Pipeline

The pipeline has two phases: **filtering** applies exclusion rules to the full inventory, and **selection** narrows the surviving set to explicitly targeted interfaces.

```
 ┌──────────────────────────────┐
 │   Full Interface Inventory   │  ← Discovery (kernel or SNMP)
 └──────────────┬───────────────┘
                │
          FILTERING PHASE
                │
 ┌──────────────▼───────────────┐
 │  1. Alias exclusion          │  ← Exclude alias interfaces unless --include-aliases
 └──────────────┬───────────────┘     (skipped entirely when --status alias)
                │
 ┌──────────────▼───────────────┐
 │  2. --ignore-virtual         │  ← Remove virtual interfaces (vnet*, virbr*, docker0)
 └──────────────┬───────────────┘
                │
 ┌──────────────▼───────────────┐
 │  3. --exclude-local          │  ← Remove loopback / local-only interfaces (e.g., lo)
 └──────────────┬───────────────┘
                │
 ┌──────────────▼───────────────┐
 │  4. --ignore PATTERN         │  ← Remove interfaces matching substring/regex patterns
 └──────────────┬───────────────┘
                │
          SELECTION PHASE
                │
 ┌──────────────▼───────────────┐
 │  5. --ifaces (targeting)     │  ← If specified, restrict to named/matched interfaces
 └──────────────┬───────────────┘
                │
 ┌──────────────▼───────────────┐
 │   Evaluation Candidate Set   │  ← Surviving interfaces proceed to --status evaluation
 └──────────────────────────────┘
```

**Filters take precedence over selection.** An interface removed during filtering is no longer available for `--ifaces` to target. If `--ifaces` references an interface that was already excluded by a filter, that pattern is unmatched and treated as a CRITICAL failure.

---

## Filtering Phase

Handled by `apply_filters()`. Each stage operates on the output of the previous stage.

### Stage 1: Alias Exclusion

By default, alias interfaces (e.g., `eth0:1`, `br0:backup`) are **excluded** from the candidate set.

- If `--include-aliases` is specified, alias interfaces are retained.
- **Special case:** When `--status alias` is selected, alias filtering is **skipped entirely** — all interfaces (including aliases) pass through this stage regardless of the `--include-aliases` flag. This ensures the alias attribute can be evaluated across the full inventory.

### Stage 2: `--ignore-virtual` — Virtual Interface Exclusion

When specified, removes virtual interfaces from the candidate set. Virtual interfaces are identified by the `is_virtual()` helper and include patterns such as:

- `vnet*` — Virtual network devices (KVM/libvirt)
- `virbr*` — Virtual bridge devices
- `docker0` — Docker default bridge
- Other hypervisor and container‑managed interfaces

### Stage 3: `--exclude-local` — Local Interface Exclusion

When specified, removes local‑only interfaces from the candidate set. Local interfaces are identified by the `is_local()` helper, which evaluates both the interface name and its properties (e.g., `lo`, loopback flag).

### Stage 4: `--ignore PATTERN` — Pattern‑Based Exclusion

Removes interfaces matching a substring or regex pattern. This flag is **repeatable** — multiple patterns can be specified to build a cumulative exclusion list.

```bash
# Ignore all vnet interfaces and docker0
--ignore "vnet.*" --ignore "docker0"

# Ignore a specific interface by name
--ignore "eth2"
```

Pattern matching is handled by the `matches_ignore()` helper, which supports both substring and regex evaluation.

---

## Selection Phase

Handled by `apply_iface_selection()` after all filters have been applied.

### Stage 5: `--ifaces` — Interface Targeting

When specified, only interfaces matching the argument are retained from the filtered set. Matching is attempted in three tiers, evaluated in order:

1. **Literal match** — case‑insensitive exact name comparison
2. **Substring match** — case‑insensitive substring search
3. **Regex match** — `re.search()` with `re.IGNORECASE`; invalid regex patterns are silently ignored

The first tier that matches wins — an interface will not be re‑evaluated by lower tiers.

- Accepts a comma‑delimited list of patterns (each pattern is tried independently).
- If `--ifaces` is omitted, all filtered interfaces proceed to evaluation.
- This is the only flag that accepts a comma‑delimited list.

```bash
# Literal names
--ifaces "eth0,eth1,br0"

# Regex pattern
--ifaces "GigabitEthernet0/[0-3]"
```

Any pattern that does not match an interface in the filtered set is tracked as **unmatched** and injected into the evaluation results as a CRITICAL failure.

---

## Attribute Evaluation

After the pipeline produces the evaluation candidate set, each surviving interface is validated by `evaluate_status()` against the attribute selected by `--status`. Defaults to `oper-status` if not specified.

**All attribute violations result in CRITICAL.** The evaluation is binary — every interface either passes or fails. There is no WARNING tier.

| Attribute      | Pass Condition                                              | Fail Value                     |
|----------------|-------------------------------------------------------------|--------------------------------|
| `oper-status`  | `oper_up` is `True`                                        | Interface operationally down   |
| `admin-status` | `admin_up` is `True`                                       | Interface administratively disabled |
| `linkspeed`    | `speed` is not `None` and not `0`                          | No speed or zero speed reported|
| `duplex`       | `duplex` is `"full"` **or** interface is a bridge (`br*`)  | Half‑duplex on non‑bridge interface |
| `mtu`          | `mtu` is not `None` and greater than `0`                   | No MTU or zero MTU reported    |
| `alias`        | Interface is **not** an alias (per `is_alias()`)            | Interface is an alias          |

### Duplex — Bridge Exception

Bridge interfaces (`br*`) are given an automatic pass for duplex evaluation with a value of `"n/a"`. Bridges operate at the virtual switching layer and do not negotiate duplex in the traditional sense.

### Linkspeed — Zero and Null

A speed of `0` or `None` is treated as a failure. This catches interfaces that are operationally up but report no negotiated speed — a condition that typically indicates a misconfiguration or driver issue.

### Alias — Identity Check

When `--status alias` is used, the evaluation checks whether an interface **is** an alias (e.g., `eth0:1`), not whether it has a description string. Interfaces that are aliases fail; non‑alias interfaces pass.

> **Note:** This is distinct from the alias **filter** in Stage 1. The filter controls which interfaces enter the candidate set. The `--status alias` evaluation checks whether surviving interfaces are aliases.

---

## Exit Code Mapping

| Code | Status   | Trigger                                                                  |
|------|----------|--------------------------------------------------------------------------|
| 0    | OK       | All evaluated interfaces pass the selected attribute check               |
| 2    | CRITICAL | One or more interfaces fail, unmatched `--ifaces` pattern, SNMP failure  |
| 3    | UNKNOWN  | Unreachable host, invalid arguments, timeout, or unhandled error         |

**There is no WARNING (exit code 1) in the current evaluation model.** All attribute violations produce CRITICAL. The evaluation result is determined by presence or absence of failures — if the failures list is non‑empty, the state is CRITICAL.

### SNMP Connection Failures

SNMP connection failures (unreachable host, authentication failure, timeout) return **CRITICAL** or **UNKNOWN** — never WARNING or OK.

---

## Edge Cases

### Partial and Missing `--ifaces` Matches

When `--ifaces` is specified, the tool evaluates every pattern independently:

- **Matched patterns** proceed through evaluation normally.
- **Unmatched patterns** are injected into the final result as CRITICAL failures with a value of `"not found"`.

The overall state is forced to CRITICAL if any pattern goes unmatched, regardless of whether the matched interfaces pass evaluation. Unmatched interfaces are logged when logging is enabled.

| `--ifaces` Value   | eth0 exists | eth99 exists | Behavior                                                      |
|---------------------|-------------|--------------|---------------------------------------------------------------|
| `"eth0"`            | Yes         | —            | eth0 evaluated normally                                       |
| `"eth99"`           | —           | No           | CRITICAL — eth99: not found                                   |
| `"eth0,eth99"`      | Yes         | No           | eth0 evaluated normally; eth99: not found; overall CRITICAL   |
| `"eth0,eth1"`       | Yes         | Yes          | Both evaluated normally                                       |

The tool never aborts early on the first miss — all patterns are resolved before the result is assembled.

### Filter–Selection Interaction

Because filtering runs **before** selection, exclusion flags can remove interfaces that `--ifaces` intends to target:

```bash
# docker0 is removed by --ignore-virtual before --ifaces can select it
./check_interfaces.py -H server01 --ignore-virtual --ifaces "docker0"
# Result: CRITICAL — docker0: not found
```

This is by design. Filters enforce infrastructure policy; selection targets specific interfaces within that policy. An operator who needs to evaluate a virtual interface should omit `--ignore-virtual`.

### `--status alias` Bypasses Alias Filtering

When the evaluation target is `alias`, Stage 1 of the filter pipeline is skipped. This prevents the filter from excluding the very interfaces the operator is trying to evaluate. All other filters (virtual, local, ignore) still apply normally.

### Overlapping Filters

Filters are cumulative and subtractive. An interface excluded by `--ignore-virtual` cannot be re‑included by a later stage. The pipeline is strictly ordered — each stage operates only on the output of the previous stage.

### `--include-aliases` with `--ignore`

If `--include-aliases` retains an alias interface in Stage 1, a subsequent `--ignore` pattern in Stage 4 can still remove it. `--ignore` always has final authority within the filtering phase.

### Local Host with SNMP Flags

When the target is detected as local, SNMP‑specific options (`-C`, `-p`, `-T`) are ignored. The tool uses kernel interface data regardless of SNMP configuration.

### Regex Patterns in `--ifaces` and `--ignore`

Both `--ifaces` and `--ignore` support regex patterns. Operators should anchor patterns when precision is required:

```bash
# Matches "eth0", "eth01", "eth0:1" — may be too broad
--ignore "eth0"

# Anchored — matches only "eth0" exactly
--ignore "^eth0$"
```

### Invalid Regex in `--ifaces`

If a pattern in `--ifaces` is not valid regex, the regex match tier is silently skipped. The pattern is still evaluated as a literal and substring match. No error or warning is emitted.

---

## Filter Interaction Summary

| Scenario                                             | Result                                              |
|------------------------------------------------------|-----------------------------------------------------|
| No filters, no selection                             | All discovered interfaces are evaluated             |
| `--ifaces` only                                      | Only named/matched interfaces are evaluated         |
| `--exclude-local` + `--ignore-virtual`               | Physical, non‑local interfaces only                 |
| `--ignore-virtual` + `--ifaces "docker0"`            | CRITICAL — docker0 filtered before selection        |
| `--ifaces "eth0,eth99"` (eth99 missing)              | eth0 evaluated; eth99 CRITICAL not found            |
| `--include-aliases` + `--ignore "eth0:.*"`           | Aliases included, then specific aliases removed     |
| `--status alias`                                     | Alias filter bypassed; all interfaces evaluated     |
| `--status alias` + `--ignore-virtual`                | Alias filter bypassed, virtual interfaces excluded  |

---

## Design Principles

1. **Deterministic** — The same input always produces the same output, regardless of enumeration order.
2. **Subtractive by default** — Filters remove interfaces from evaluation. The only additive flag is `--include-aliases`.
3. **Filters before selection** — Exclusion filters enforce infrastructure policy. Selection targets specific interfaces within that policy. Filters always win.
4. **Binary evaluation** — Every interface either passes or fails. There is no graduated severity. Failures are CRITICAL.
5. **Explicit over implicit** — No interface is silently included or excluded. Verbose output (`-v`) reports every filter decision and the reason for inclusion or exclusion.
6. **Fail‑closed on connectivity** — SNMP failures are CRITICAL or UNKNOWN, never OK or WARNING. An inability to inspect is treated as a monitoring failure.
