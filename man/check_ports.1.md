% CHECK_PORTS(1) NMS_Tools | Deterministic Multi-Port TCP Checker
% Linktech Engineering
% April 2026

# NAME
**check_ports** — deterministic multi-port TCP availability checker with service resolution

# SYNOPSIS
**check_ports** -H <host> [-p <ports>] [-s <services>] [options]

# DESCRIPTION
**check_ports** is a deterministic, audit-transparent TCP port checker used for
monitoring, diagnostics, and automation. It evaluates one or more TCP ports on a
target host and produces consistent, machine-parseable output suitable for
Nagios, automation pipelines, and operator workflows.

The tool supports:
- Explicit ports (`-p`) and service names (`-s`)
- Multiple ports, ranges, and mixed lists
- Deterministic timeout behavior
- JSON, verbose, quiet, and Nagios output modes
- Operator-grade logging with rotation and structured START/RESULT/END banners
- Strict evaluation rules for open / closed / timeout / unreachable states

Service names are resolved using the system’s service database (e.g. `/etc/services`).

# OPTIONS

## Required Arguments

**-H, --host <hostname>**  
Target hostname or IP address.

## Port and Service Selection

**-p, --ports <list>**  
Comma-separated list of ports or ranges.  
Examples: `80`, `80,443`, `8000-8100`.

**-s, --service <names>**  
Comma-separated list of service names (e.g., `ssh`, `https`, `mysql`).  
Each service is resolved to its associated TCP port.

At least one of `--ports` or `--service` must be provided.

## Optional Arguments

**--timeout <seconds>**  
Per-port timeout. Default: 5 seconds.

**--require-all**  
Return CRITICAL unless *all* ports are open.

**--require-any**  
Return OK if *any* port is open.

**--fail-only**  
Suppress output for successful ports in verbose or JSON modes.

**--json**  
Emit structured JSON output.

**--verbose**  
Emit human-readable diagnostics including resolved services, explicit ports,
and per-port results.

**--quiet**  
Suppress human-readable output (exit code only).

**--log-dir <path>**  
Directory for log files. Logging is disabled if omitted.

**--log-max-mb <size>**  
Maximum log file size before rotation.

**--version**  
Show version and exit.

# EXIT CODES
**0** — All required ports are open  
**1** — One or more ports failed (WARNING)  
**2** — Required ports failed (CRITICAL)  
**3** — Unknown error (UNKNOWN)

# PORT STATES
**open** — TCP connection succeeded  
**closed** — Connection refused  
**timeout** — No response before timeout  
**unreachable** — Host unreachable or DNS failure  

# OUTPUT MODES

## Nagios (default)
Single-line status suitable for monitoring systems.

### Single-service checks
OK - ssh (22) is open
WARNING - mysql (3306) is closed

### Single explicit port
OK - Port 2222 is open
WARNING - Port 8080 is closed

### Multi-port checks
WARNING - Closed ports: 22, 123
CRITICAL - Problem ports: 22, 123, 5000

## Verbose
Human-readable diagnostics including:
- Host
- Services requested
- Resolved service ports
- Explicit ports
- Combined port list
- Per-port results

Example:
Host: db01
Services requested: mysql
Service ports:      3306
Explicit ports:     None
All ports:          3306

db01:3306 = open

## JSON
Deterministic machine-parseable structure including:
- explicit ports
- service ports
- combined port list
- per-port results
- categorized open/closed/timeout/unreachable lists

## Logging
If `--log-dir` is provided, the tool writes operator-grade logs with rotation:

[START] cmd="..." host=... ports_explicit=[...] ports_service=[...] ports_all=[...]
[PORT] host=... port=... status=...
[RESULT] state=... message="..."
[END]

Logs are written only in non-Nagios modes.

# EXAMPLES

Check a single service:
```check_ports.py -H db01 -s mysql```

Check a single explicit port:
```check_ports.py -H router -p 2222```

Check multiple services:
```check_ports.py -H web01 -s https,ssh```

Check mixed explicit + service:
```check_ports.py -H app01 -s redis -p 8080```

Verbose diagnostics:
```check_ports.py -H cache01 -s redis --verbose```

JSON output:
```check_ports.py -H db01 -s mysql --json```

# FILES
Logging is disabled unless `--log-dir` is explicitly provided.

When enabled, logs are written to the directory specified by `--log-dir`.
No default log directory is assumed or created.

# FUTURE ENHANCEMENTS
- Named port support via `/etc/services` expansion  
- Port parsing preview (`--explain-ports`)  
- JSON schema versioning  
- Perfdata block for Nagios  
- Structured diagnostic mode (`--debug`)  
- Per-port timing metrics  
- Connection lifecycle tracing  

# SEE ALSO
**check_cert(1)**, **check_html(1)**, **check_weather(1)**, **check_interfaces(1)**, **nms_tools(7)**

# AUTHOR
Linktech Engineering — https://www.linktechengineering.net/projects/nms-tools/