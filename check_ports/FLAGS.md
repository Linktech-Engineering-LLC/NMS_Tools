# Internal Flags — check_ports.py

`check_ports.py` uses the standard NMS_Tools bitmask flag engine.  
These flags are **internal**, not user‑facing CLI options.  
They control evaluation logic, output modes, and operator workflows.

Each flag corresponds to a single bit in the mask.  
Flags may be combined using bitwise OR (`|`).

---

## Flag Table

| Flag Name      | Bit Value | Description |
|----------------|-----------|-------------|
| `VERBOSE`      | `0x01`    | Enables verbose per‑port output. Set internally when `--verbose` is active. |
| `JSON`         | `0x02`    | Enables JSON output mode. Set internally when `--json` is active. |
| `QUIET`        | `0x04`    | Suppresses all output except the exit code. Set internally when `--quiet` is active. |
| `REQUIRE_ALL`  | `0x08`    | All ports must be open to return OK. Mirrors the `--require-all` CLI flag. |
| `REQUIRE_ANY`  | `0x10`    | At least one port must be open to return OK. Mirrors the `--require-any` CLI flag. |
| `FAIL_ONLY`    | `0x20`    | Only log failing ports. Used for operator workflows and log reduction. |

---

## Bitmask Behavior

The flag mask is constructed during argument parsing and passed into the enforcement object.

Example:

```python
flags = 0
```

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

The enforcement object evaluates the mask to determine:

* output mode
* Nagios evaluation rules
* logging verbosity
* whether to suppress successful ports

## Output Mode Priority

Only one output mode is active at a time.
Priority is enforced by the mask:

1. JSON
2. VERBOSE
3. QUIET
4. (default) Nagios single‑line output

This ensures deterministic behavior across all NMS_Tools plugins.

## Evaluation Logic
The following flags influence Nagios state:

* REQUIRE_ALL
* REQUIRE_ANY

If neither is set:

* Any closed, timeout, or unreachable port → CRITICAL
* All ports open → `OK`

If both are set (should not happen via CLI):

* REQUIRE_ALL takes precedence

## FAIL_ONLY Behavior

When FAIL_ONLY is set:

* Only failing ports (closed, timeout, unreachable) are logged
* Successful ports (open) are suppressed
* JSON output still includes all ports (for correctness)

This flag is intended for operator workflows where log noise must be minimized.

## Notes

* These flags are not exposed directly to the user.
* They are part of the internal architecture shared across the NMS_Tools suite.
* The bitmask system ensures deterministic, reproducible behavior across all tools.
