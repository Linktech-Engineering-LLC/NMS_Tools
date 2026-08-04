```markdown
# check_ports.py  
Deterministic multi-port connectivity checker for Nagios and operator workflows.

<p align="center">

  <img src="https://img.shields.io/badge/status-stable-brightgreen?style=for-the-badge" />
  <img src="https://img.shields.io/badge/license-MIT-blue?style=for-the-badge" />
  <img src="https://img.shields.io/badge/python-3.6%2B-blue?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/platform-linux-lightgrey?style=for-the-badge&logo=linux&logoColor=white" />
  <img src="https://img.shields.io/badge/Linktech_Engineering-Tools_Suite-8A2BE2?style=for-the-badge" />

</p>

`check_ports.py` performs fast, deterministic TCP connectivity checks against one or more ports on a target host. It supports mixed port lists, ranges, JSON output, verbose/quiet modes, and operator‑grade logging with rotation. The tool is designed for reliability, reproducibility, and clean integration into monitoring systems.

---

## Features

* Deterministic TCP port checking (open / closed / timeout / unreachable)
* Supports individual ports, comma‑separated lists, and ranges (e.g., `22,80,8000-8010`)
* JSON output for automation and dashboards
* Verbose and quiet modes for operator workflows
* Nagios‑compliant exit codes and single‑line output
* Operator‑grade logging with rotation and structured banners
* Zero side effects in Nagios mode
* Consistent with the NMS_Tools suite architecture

---

## Usage

```bash
check_ports.py -H <host> -p <ports> [options]
```

## Required Arguments

At least one of the following must be provided:

| Flag | Description |
| :--- | :--- |
| `-H`, `--host` | Target hostname or IP address |
| `-p`, `--ports` | Port list or range (e.g., `22,80,8000-8010`) |
| `-s`, `--service` | One or more named services (e.g., `ssh,http,mysql`) |

You must specify **either** `--ports` or `--service` (or both).  
If neither is provided, the tool returns `UNKNOWN`.

---

## CLI Flags

These flags control output mode and evaluation behavior.

| Flag | Description |
| --- | --- |
| ``-j``, ``--json`` | Emit structured JSON output |
| ``-v``, ``--verbose`` | One line per port with status |
| ``-q``, ``--quiet`` | Suppress all output; exit code only |
| ``--require-all`` | All ports must be open to return OK |
| ``--require-any`` | At least one port must be open to return OK |
| ``--fail-only`` | Suppress open ports in verbose output; logs and JSON always include all ports |
| ``--timeout ``<seconds>`` | Per‑port timeout (default: 5 seconds) |
| ``--log-dir ``<path>`` | Enable logging and write logs to the specified directory |
| ``--log-max-mb ``<size>`` | Maximum log file size before rotation (default: 50 MB) |
| ``--version`` | Show version and exit |

---

## Port Parsing

The `--ports` argument accepts:

* Single ports: `22`
* Comma‑separated lists: `22,80,443`
* Ranges: `8000-8010`
* Mixed lists and ranges: `22,2222,8080,5000-5004`

All ports are expanded into a deterministic, sorted list before scanning.

## Service Resolution (Internal)
check_ports.py includes an internal service map used for labeling and logging.
This feature is not exposed as a CLI flag.

Examples of internal mappings:

```Code
ssh   → 22
http  → 80
https → 443
mysql → 3306
```

If a port corresponds to a known service, verbose mode and logs display service‑aware labels:

```Code
ssh(22)
mysql(3306)
http(80)
```

Explicit ports (from --ports) are always shown as raw numbers.

---

## Output Modes

Only one output mode is active at a time. Priority order:

1. `--json`
2. `--verbose`
3. `--quiet`
4. *(default)* Nagios single‑line output

### JSON Mode

```bash
check_ports.py -H server -p 22,80 -j
```

Produces:

```json
{
  "host": "server",
  "results": [
    {"port": 22, "status": "open"},
    {"port": 80, "status": "closed"}
  ],
  "open_ports": [22],
  "closed_ports": [80],
  "timeout_ports": [],
  "unreachable_ports": []
}
```

### Verbose Mode

Verbose mode shows a human‑readable breakdown of what the tool resolved and the status of each port check.
It prints:
* the host
* the requested services
* the resolved service‑to‑port mapping
* explicit ports
* all ports being checked
* one line per port with its status

Example:

```Code
Host: server
Explicit ports: 22, 9999
All ports:      22, 9999

ssh(22) = open
9999 = closed
```

With `--fail-only`, verbose mode suppresses open ports:

```Code
9999 = closed
```

```Service ports: ssh(22), mysql(3306)```

Each per‑port result also includes the service name when applicable:

```Mom:ssh(22) = closed```
```Mom:2222 = open```
```Mom:mysql(3306) = open```

Explicit ports (those provided via -p) are always shown as raw port numbers.
Verbose mode is intended for operators who want to see exactly what the tool resolved and how each port responded. It does not output JSON or Nagios‑formatted text.

### Quiet Mode

No output — exit code only.

### Nagios Mode (default)

```
CRITICAL - Problem ports: 80
```

---

## Internal Flags (Bitmask)

`check_ports.py` uses the standard NMS_Tools bitmask flag engine.  
These flags are not user‑facing CLI options — they control internal behavior and evaluation logic.

| Flag | Bit | Description |
|------|-----|-------------|
| `VERBOSE` | `0x01` | Enables verbose per‑port output (used internally when `--verbose` is active) |
| `JSON` | `0x02` | Enables JSON output mode |
| `QUIET` | `0x04` | Suppresses all output except exit code |
| `REQUIRE_ALL` | `0x08` | All ports must be open to return OK |
| `REQUIRE_ANY` | `0x10` | At least one port must be open to return OK |
| `FAIL_ONLY` | `0x20` | Only log failing ports (used by operator workflows) |

These flags are combined into a single integer mask and evaluated by the enforcement object.

---

## Logging

Logging is enabled if:

* mode != "nagios"
* `--log-dir` is specified

When logging is enabled, the tool writes:
* a [START] banner with command, host, and resolved ports
* one [PORT] line per port
* a [RESULT] summary line
* a final [END] banner

### Service‑Aware Logging

When services are specified using -s, log entries now include the service name alongside the port number:

[PORT] host=Mom port=ssh(22) status=closed
[PORT] host=Mom port=mysql(3306) status=open

Explicit ports (those provided via -p) are always logged as raw port numbers:

[PORT] host=Mom port=2222 status=open

The [RESULT] line includes grouped breakdowns:

```service_open=mysql(3306) service_closed=ssh(22) explicit_open=2222```

This makes logs fully service‑aware and consistent with verbose, JSON, and Nagios modes.

### Example:

```bash
check_ports.py -H server -p 22,80 -j --log-dir /var/log/nms_tools
```

Log entries follow the suite‑standard format:

```
2026-04-20 11:29:55; [START] check_ports.py host=server ports_explicit=[22,80] ports_service=[] ports_all=[22,80] timeout=5 require_all=False require_any=False
2026-04-20 11:29:55; [PORT] host=server port=22 status=open
2026-04-20 11:29:55; [PORT] host=server port=80 status=closed
2026-04-20 11:29:55; [RESULT] state=CRITICAL message="json output" explicit_open=22 explicit_closed=80
2026-04-20 11:29:55; [END]
```

If services are specified using -s, log entries include service names:

```bash
check_ports.py -H server -s ssh,http -j --log-dir /var/log/nms_tools
```

Produces:

2026-04-20 11:29:55; [START] check_ports.py host=server ports_explicit=[] ports_service=[22,80] ports_all=[22,80] timeout=5 require_all=False require_any=False
2026-04-20 11:29:55; [PORT] host=server port=ssh(22) status=open
2026-04-20 11:29:55; [PORT] host=server port=http(80) status=closed
2026-04-20 11:29:55; [RESULT] state=CRITICAL message="json output" service_open=ssh(22) service_closed=http(80)
2026-04-20 11:29:55; [END]


Log rotation is automatic when the file exceeds `--log-max-mb` (default: 50 MB).

---

## Nagios Exit Codes

| Code | Meaning |
| :---: | :--- |
| 0 | OK |
| 1 | WARNING |
| 2 | CRITICAL |
| 3 | UNKNOWN |

Nagios state is determined by:

* `--require-all` → all ports must be open  
* `--require-any` → at least one port must be open  
* default
  * WARNING if some ports are open and some are closed
  * CRITICAL if all ports fail

---

## Examples

### Check a single port

```bash
check_ports.py -H server -p 22
```

### Check a range

```bash
check_ports.py -H server -p 8000-8010
```

### Check mixed ports with JSON output

```bash
check_ports.py -H server -p 22,80,443,8000-8005 -j
```

### Quiet mode for Nagios

```bash
check_ports.py -H server -p 22,80 -q
```

---

## Logging Directory Structure

```
<log_dir>/
    check_ports.log
    check_ports_20260420_112955.log.zip
```

## Future Enhancements

The following improvements are planned for future releases of `check_ports.py`:

### Port Parsing & Resolution
* **Named port support** (e.g., `https` → 443 via `/etc/services`)
* Strict validation for unknown port names
* Deterministic expansion of mixed numeric + named ports

### Output & Evaluation
* JSON schema versioning for long‑term compatibility
* Optional perfdata block for Nagios
* Additional evaluation modes (e.g., require-open-count=N)

### Logging & Diagnostics
* Structured diagnostic mode (`--debug`)
* Per‑port timing metrics
* Connection lifecycle tracing (SYN, timeout, refusal)

### UX Improvements
* Help text refinements
* Port parsing preview (`--explain-ports`)

---

## License

MIT License — see LICENSE.md in the repository root.
```
