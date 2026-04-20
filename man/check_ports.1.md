% CHECK_PORTS(1) NMS_Tools | Deterministic Multi-Port TCP Checker
% Linktech Engineering
% April 2026

# NAME
**check_ports** — deterministic multi-port TCP availability checker

# SYNOPSIS
**check_ports** -H <host> -p <ports> [options]

# DESCRIPTION
**check_ports** is a deterministic, audit-transparent TCP port checker used for
monitoring, diagnostics, and automation. It evaluates one or more TCP ports on a
target host and produces consistent, machine-parseable output suitable for
Nagios, automation pipelines, and operator workflows.

The tool supports:
- Multiple ports, ranges, and mixed lists  
- Deterministic timeout behavior  
- JSON, verbose, quiet, and Nagios output modes  
- Operator-grade logging with rotation  
- Strict evaluation rules for open/closed/timeout/refused states  

Future versions will support named ports via `/etc/services`.

# OPTIONS

## Required Arguments

**-H, --host <hostname>**  
Target hostname or IP address.

**-p, --ports <list>**  
Comma-separated list of ports or ranges.  
Examples: `80`, `80,443`, `8000-8100`.

## Optional Arguments

**--timeout <seconds>**  
Per-port timeout. Default: 3 seconds.

**--require-all**  
Return CRITICAL unless *all* ports are open.

**--require-any**  
Return OK if *any* port is open.

**--fail-only**  
Suppress output for successful ports.

**--json**  
Emit structured JSON output.

**--verbose**  
Enable detailed connection diagnostics.

**--quiet**  
Suppress human-readable output.

**--log-dir <path>**  
Directory for log files.

**--log-max-mb <size>**  
Maximum log file size before rotation.

**--version**  
Show version and exit.

# EXIT CODES
**0** — All required ports are open  
**1** — One or more ports failed (WARNING)  
**2** — Required ports failed (CRITICAL)  
**3** — Unknown error (UNKNOWN)

# OUTPUT MODES

## Human-readable
Summaries of open/closed/timeout states.

## JSON
Deterministic machine-parseable structure for automation.

## Nagios
Single-line status with perfdata (future enhancement).

# EXAMPLES

Check a single port:
```
check_ports -H example.com -p 443
```

Check multiple ports:
```
check_ports -H db01 -p 5432,6432
```

Check a range:
```
check_ports -H app01 -p 8000-8100
```

Require all ports to be open:
```
check_ports -H web01 -p 80,443 --require-all
```

Emit JSON:
```
check_ports -H cache01 -p 6379 --json
```

# FILES
**/var/log/nms_tools/** — default log directory (if configured)

# FUTURE ENHANCEMENTS
- Named port support via `/etc/services`  
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
