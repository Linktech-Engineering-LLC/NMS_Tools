% NMS_TOOLS(7) NMS_Tools | Suite Overview and Architecture
% Linktech Engineering
% April 2026

# NAME
**nms_tools** — deterministic network monitoring and inspection tool suite

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

## check_ports(1)
Deterministic multi-port TCP availability checker.

## check_weather(1)
Weather condition evaluator with deterministic rule engine and provider registry.

## check_cert(1)
TLS certificate inspection and policy enforcement tool.

## check_html(1)
HTTP/HTTPS inspection and content validation tool.

## check_interfaces(1)
Network interface state and SNMP-based operational status checker.

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
