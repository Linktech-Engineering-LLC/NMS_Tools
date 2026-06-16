% NMS_TOOLS(7) NMS_Tools | Suite Overview and Architecture
% Linktech Engineering
% April 2026

# NAME
**nms_tools** — deterministic network monitoring and inspection tool suite
# VERSION
This build of **NMS_Tools** was generated with the following metadata:

- **Version:** {{VERSION}}
- **Build Type:** {{BUILD_TYPE}}
- **Build Date:** {{BUILD_DATE}}
- **Commit:** {{GIT_HASH}}

These fields are automatically injected during packaging and reflect the
exact state of the repository at build time.

# DESCRIPTION
**NMS_Tools** is a unified collection of deterministic, audit‑transparent
monitoring and inspection utilities used across Linktech Engineering
infrastructure. Each tool follows strict engineering principles:

- Predictable, reproducible behavior  
- No hidden state  
- Audit‑transparent output  
- Strict separation between human and machine modes  
- Minimal dependencies  
- Monitoring‑friendly design  

The suite provides consistent CLI patterns, JSON schemas, logging behavior, and
operational semantics across all included tools.

# INCLUDED TOOLS

## check_ports.py — Deterministic Multi‑Port TCP Checker

`check_ports.py` performs deterministic TCP availability checks against one or more
ports on a target host. It supports explicit ports (`-p`) and service names (`-s`),
resolving services through the system’s service database (e.g., `/etc/services`).

The tool provides:
- Deterministic open / closed / timeout / unreachable evaluation
- Single‑service and single‑port Nagios‑grade output
- Multi‑port Nagios output for monitoring systems
- Verbose mode with full resolution context
- JSON mode for automation pipelines
- Optional operator‑grade logging with START / PORT / RESULT / END banners

Typical usage:
```check_ports.py -H host -s ssh```
```check_ports.py -H host -p 443```
```check_ports.py -H host -s https,ssh -p 2222```

See **check_ports(1)** for full documentation.

## check_weather.py — Deterministic Weather Condition Evaluator
check_weather.py evaluates current weather conditions using a deterministic rule
engine and a provider registry. It is designed for automation workflows that
depend on environmental state (e.g., wind thresholds, precipitation detection).

The tool provides:

- Deterministic evaluation of temperature, wind, precipitation, and visibility
- Provider registry with pluggable backends (Open‑Meteo, NOAA, etc.)
- JSON and verbose output modes
- Rule‑based condition evaluation (e.g., “unsafe”, “advisory”, “clear”)
- Optional operator‑grade logging

Typical usage:

```check_weather.py --location "St John, KS"```
```check_weather.py --location 67576 --json```

See **check_weather(1)** for full documentation.

## check_cert.py — TLS Certificate Inspection and Policy Enforcement
check_cert.py performs deterministic TLS certificate inspection and policy
evaluation. It extracts certificate metadata, validates chains, and enforces
expiration and signature policies.

The tool provides:

- Deterministic JSON metadata extraction
- Expiration, SAN, issuer, and signature algorithm evaluation
- AIA chain reconstruction
- OCSP metadata extraction
- Policy enforcement with Nagios‑grade exit codes
- Clean separation between human and machine output modes

Typical usage:

```check_cert.py -H example.com```
```check_cert.py -H api.example.com --json```

See **check_cert(1)** for full documentation.

## check_html.py — HTTP/HTTPS Inspection and Content Validation
check_html.py performs deterministic HTTP/HTTPS inspection with content‑type,
status‑code, and backend validation. It is designed for monitoring web services
and enforcing expected response characteristics.

The tool provides:

- TLS‑aware request pipeline with handshake detection
- Status, headers, content‑type, and HTML body capture
- Backend fingerprinting and backend enforcement
- Deterministic JSON schema for automation
- Nagios‑aware severity merging (CRITICAL > WARNING > UNKNOWN > OK)

Typical usage:

```check_html.py -H example.com```
```check_html.py -H example.com --expect-backend nginx```

See **check_html(1)** for full documentation.

## check_interfaces.py — Network Interface and SNMP Operational State Checker
check_interfaces.py evaluates network interface state using SNMP and local
system inspection. It is designed for deterministic monitoring of link status,
administrative state, and operational counters.

The tool provides:

- SNMP‑based interface enumeration and state evaluation
- Deterministic admin/oper status mapping
- Optional local interface inspection (Linux)
- JSON and verbose output modes
- Operator‑grade logging with START/RESULT/END lifecycle

Typical usage:

```check_interfaces.py -H switch01```
```check_interfaces.py -H router01 --json```

See **check_interfaces(1)** for full documentation.

# DIRECTORY STRUCTURE
A typical installation includes:

```
/usr/local/bin/              Executables
/usr/local/share/man/man1/   Tool man pages
/usr/local/share/man/man7/   Suite overview (this page)
/var/log/nms_tools/          Optional logging directory
```

# LOGGING
Tools may emit operator‑grade logs with rotation when configured via:

```
--log-dir <path>
--log-max-mb <size>
```

Logging is deterministic and free of noise, suitable for automation and
post‑incident analysis.

# JSON OUTPUT
All tools support deterministic JSON output for automation pipelines.  
Schemas are versioned and documented in:

```
docs/Metadata_Schema.md
```

# NAGIOS / MONITORING INTEGRATION
Each tool supports Nagios‑compatible exit codes:

- **0** — OK  
- **1** — WARNING  
- **2** — CRITICAL  
- **3** — UNKNOWN  

Future versions will include optional perfdata blocks.

# FUTURE ENHANCEMENTS
- Centralized man‑page generation pipeline  
- Named port support in check_ports  
- Provider registry expansion in check_weather  
- TLS chain validation improvements in check_cert  
- Structured HTML parsing in check_html  
- Enhanced SNMP diagnostics in check_interfaces  
- Unified JSON schema versioning  
- Packaging for RPM/DEB distributions  

# SEE ALSO
**check_ports(1)**, **check_weather(1)**, **check_cert(1)**,  
**check_html(1)**, **check_interfaces(1)**

# AUTHOR
Linktech Engineering — https://www.linktechengineering.net/projects/nms-tools/
