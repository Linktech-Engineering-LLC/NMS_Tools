% CHECK_INTERFACES(1) NMS_Tools | SNMP Interface State Checker
% Linktech Engineering
% April 2026

# NAME
**check_interfaces** — SNMP-based network interface state and health checker

# SYNOPSIS
**check_interfaces** -H <host> -C <community> [options]

# DESCRIPTION
**check_interfaces** queries network devices via SNMP to evaluate interface
operational state, admin state, speed, duplex, and error counters.

It is suitable for:
- Monitoring switches and routers  
- Detecting interface failures  
- Automation pipelines  
- Deterministic SNMP diagnostics  

# OPTIONS

## SNMP

**-H, --host <hostname>**  
Target device.

**-C, --community <string>**  
SNMP community string.

**--version <1|2c>**  
SNMP version.

## Filtering

**--match <pattern>**  
Include interfaces matching pattern.

**--exclude <pattern>**  
Exclude interfaces matching pattern.

## Debugging

**--debug-snmp**  
Show SNMP request/response details.

**--verbose**  
Show per-interface metrics.

## Output Modes

**--json**  
Emit structured JSON.

**--quiet**  
Suppress human-readable output.

# EXIT CODES
**0** — All required interfaces OK  
**1** — Non-critical issue  
**2** — Critical interface failure  
**3** — Unknown error

# EXAMPLES

Check all interfaces:
```
check_interfaces -H switch01 -C public
```

Filter by name:
```
check_interfaces -H switch01 -C public --match "uplink"
```

Debug SNMP:
```
check_interfaces -H switch01 -C public --debug-snmp
```

# FUTURE ENHANCEMENTS
- Improved SNMP error classification  
- Deterministic UNKNOWN vs CRITICAL mapping  
- Interface speed/duplex extraction  
- Per-interface timing metrics  

# SEE ALSO
**nms_tools(7)**, **check_ports(1)**

# AUTHOR
Linktech Engineering — https://www.linktechengineering.net/projects/nms-tools/
