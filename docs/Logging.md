# Logging Architecture — NMS_Tools (2026)

NMS_Tools implements a deterministic, operator‑grade logging system shared across
all tools in the suite. Logging is **opt‑in**, **caller‑gated**, and **disabled by
default** to preserve Nagios/Icinga single‑line output semantics.

This document defines the logging behavior, rotation rules, metadata schema, and
operational expectations for all tools.

---

## 1. Logging Overview

Logging is enabled only when the caller provides:

    --log-dir /path/to/logs

If omitted, logging is fully disabled and no files are created.

Logging is used for:

- Troubleshooting
- Auditing
- Operator visibility
- Post‑incident review
- Development and diagnostics

Nagios mode **never** writes logs unless explicitly requested.

---

## 2. Log Directory Behavior

When `--log-dir` is provided:

- The directory is created automatically if it does not exist
- Creation uses `os.makedirs(..., exist_ok=True)` for deterministic behavior
- If the executing user lacks permission to create or write to the directory:
  - Logging is disabled
  - A single warning is emitted (verbose/JSON modes only)
  - Tool execution continues normally

Example:

    ./check_html.py -H example.com --log-dir /var/log/nms_tools

If the directory cannot be created:

    WARNING: Unable to write to log directory '/var/log/nms_tools': <error>

Nagios mode never prints this warning to stdout.

---

## 3. Log File Naming

Each tool writes to a deterministic log file:

- `check_cert.py` → `check_cert.log`
- `check_html.py` → `check_html.log`
- `check_interfaces.py` → `check_interfaces.log`

Log files are always located inside the caller‑provided `--log-dir`.

Example:

    /var/log/nms_tools/check_html.log

---

## 4. Log Format

NMS_Tools uses a deterministic, phase‑driven log format shared across all tools.

Each log entry is a single line with the structure:

    <timestamp>; [<TAG>] <event> <key=value> <key=value> ...

### Timestamp
Localtime, formatted as:

    YYYY-MM-DD HH:MM:SS

### TAG
A deterministic phase identifier, not a severity level.

Common tags include:

- `[START]`   — tool invocation and input parameters
- `[HTML]`    — HTTP/HTTPS capture details (check_html)
- `[CERT]`    — certificate capture/validation (check_cert)
- `[SNMP]`    — interface enumeration (check_interfaces)
- `[RESULT]`  — final state, failure list, merged severity
- `[END]`     — completion marker

### Event and Metadata
After the tag, each entry contains:

- an event label (e.g., `check_html`, `capture`, `validation`)
- a deterministic list of `key=value` fields

Example:

    2026-03-30 08:56:38; [START] check_html url=mom timeout=5 https=False redirects=5 expect_status=200 expect_family=None mode=quiet

    2026-03-30 08:56:38; [HTML] url=mom status=200 status_ok=True latency_ms=1.4655590057373047 content_type=text/html content_type_ok=True text_present=True regex_match=True backend=apache backend_ok=True size=45 size_ok=True redirects=0 redirect_ok=True https_used=True hsts=False errors=0 perf_latency=0.0014655590057373047 perf_size=45 perf_warn_rt=0.5 perf_crit_rt=1.0 perf_warn_size=204800 perf_crit_size=512000

    2026-03-30 08:56:38; [RESULT] state=0 failed=0 failures=[]

    2026-03-30 08:56:38; [END]

---

## 5. Logged Events

Each tool logs events relevant to its domain.

### check_cert.py
- Hostname resolution
- TLS handshake lifecycle
- Certificate parsing
- Chain validation
- Enforcement results
- Internal warnings/errors

### check_html.py
- Hostname resolution
- Connection lifecycle
- Redirects
- HTTP/HTTPS capture details
- Backend detection
- Enforcement results
- Internal warnings/errors

### check_interfaces.py
- Hostname resolution
- SNMP connection lifecycle
- Local interface enumeration
- Remote interface enumeration
- Enforcement results
- Internal warnings/errors

---

## 6. Log Rotation

Rotation is deterministic, size‑based, and uses compressed archives.

### Rules
- Default max size: **50 MB**
- Configurable via:

      --log-max-mb SIZE

- When the active log exceeds the limit:
  - The log file is atomically moved to a timestamped archive path
  - The archive is immediately compressed into a `.zip` file
  - A new log file is created
  - A rotation notice is written as the first line of the new log

Example rotated archive:

    check_html_20260330_085638.log.zip

Example rotation notice:

    2026-03-30 08:56:38; [INFO] log rotated to check_html_20260330_085638.log.zip

### Behavior Guarantees
- No log data is ever deleted
- No nested archive folders are created
- Rotation is atomic and safe for Nagios/NRPE execution
- Failures emit a single warning (verbose/JSON only) and do not interrupt tool execution

---

## 7. Log Access

On Linux systems, log files are plain text and can be viewed using standard tools:

    cat check_html.log
    less check_html.log
    less +F check_html.log    # follow mode (live updates)

These are the canonical methods for inspecting logs on Linux.

A Windows‑based C# log viewer exists for development and operator tooling, but it
is not part of the Linux deployment workflow and does not affect logging behavior
on Linux systems.

No special utilities are required; logs are designed to be readable with basic
Unix text tools.

---

## 8. Nagios/Icinga Behavior

Nagios/Icinga mode is designed to be completely side‑effect‑free.  
Logging is disabled in this mode, even if `--log-dir` is provided.

Logging is enabled only when **both** of the following are true:

1. `--log-dir` is provided  
2. The tool is **not** in Nagios/Icinga mode

Nagios/Icinga mode:

- Never writes logs (even if `--log-dir` is set)
- Always emits a single clean line to stdout
- Never prints log paths, warnings, or internal details
- Never emits rotation notices
- Never prints verbose or diagnostic output

This ensures deterministic, plugin‑safe behavior for monitoring systems.

---

## 9. Error Handling

If logging cannot be initialized:

- The tool prints a deterministic warning to stderr (not stdout)
- Logging is silently disabled
- Tool execution continues normally

Example:

    WARNING: Logging disabled (cannot write to /var/log/nms_tools)

---

## 10. Summary

| Feature | Behavior |
| :--- | :--- |
| Default state | Logging disabled |
| Enable logging | `--log-dir /path` |
| Rotation | Size‑based, deterministic |
| Max size | 50 MB (configurable) |
| Format | Timestamped, structured |
| Nagios mode | No logs unless explicitly enabled |

Logging is designed to be deterministic, operator‑grade, and consistent across
all tools in the NMS_Tools suite.
