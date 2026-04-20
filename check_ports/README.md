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

- Deterministic TCP port checking (open / closed / timeout / unreachable)
- Supports individual ports, comma‑separated lists, and ranges (e.g., `22,80,8000-8010`)
- JSON output for automation and dashboards
- Verbose and quiet modes for operator workflows
- Nagios‑compliant exit codes and single‑line output
- Operator‑grade logging with rotation and structured banners
- Zero side effects in Nagios mode
- Consistent with the NMS_Tools suite architecture

---

## Usage

```bash
check_ports.py -H <host> -p <ports> [options]
```

## Required Arguments

| Flag | Description |
| :--- | :--- |
| `-H`, `--host` | Target hostname or IP address |
| `-p`, `--ports` | Port list or range (e.g., `22,80,8000-8010`) |

---

## CLI Flags

These flags control output mode and evaluation behavior.

| Flag | Description |
|------|-------------|
| `-j`, `--json` | Emit structured JSON output |
| `-v`, `--verbose` | One line per port with status |
| `-q`, `--quiet` | Suppress all output; exit code only |
| `--require-all` | All ports must be open to return OK |
| `--require-any` | At least one port must be open to return OK |
| `--fail-only` | Only log failing ports (open ports suppressed in logs) |
| `--timeout <seconds>` | Per‑port timeout (default: 5 seconds) |
| `--log-dir <path>` | Enable logging and write logs to the specified directory |
| `--log-max-mb <size>` | Maximum log file size before rotation (default: 50 MB) |
| `--version` | Show version and exit |

---

## Port Parsing

The `--ports` argument accepts:

- Single ports: `22`
- Comma‑separated lists: `22,80,443`
- Ranges: `8000-8010`
- Mixed lists and ranges: `22,2222,8080,5000-5004`

All ports are expanded into a deterministic, sorted list before scanning.

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

Shows one line per port:

```
server:22 = open
server:80 = closed
```

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

- mode != "nagios"
- `--log-dir` is specified

Example:

```bash
check_ports.py -H server -p 22,80 -j --log-dir /var/log/nms_tools
```

Log entries follow the suite‑standard format:

```
2026-04-20 11:29:55; [START] check_ports.py host=server ports=22,80 timeout=5 require_all=False require_any=False
2026-04-20 11:29:55; [PORT] host=server port=22 status=open
2026-04-20 11:29:55; [PORT] host=server port=80 status=closed
2026-04-20 11:29:55; [RESULT] state=CRITICAL message="json output"
2026-04-20 11:29:55; [END]
```

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

- `--require-all` → all ports must be open  
- `--require-any` → at least one port must be open  
- default → any closed/unreachable/timeout port triggers CRITICAL  

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
- **Named port support** (e.g., `https` → 443 via `/etc/services`)
- Strict validation for unknown port names
- Deterministic expansion of mixed numeric + named ports

### Output & Evaluation
- JSON schema versioning for long‑term compatibility
- Optional perfdata block for Nagios
- Additional evaluation modes (e.g., require-open-count=N)

### Logging & Diagnostics
- Structured diagnostic mode (`--debug`)
- Per‑port timing metrics
- Connection lifecycle tracing (SYN, timeout, refusal)

### UX Improvements
- Help text refinements
- Port parsing preview (`--explain-ports`)


---

## License

MIT License — see LICENSE.md in the repository root.
```
