# check_html.py — Usage Guide

**Part of:** NMS_Tools Monitoring Suite  
**Document:** Usage Guide  
**Author:** Leon McClatchey, Linktech Engineering LLC  
**License:** MIT  
**Requires:** Python 3.12+  (development only; not required for frozen binary)
**Last Updated:** 2026‑08‑17

## Table of Contents
1. [Overview](#1-overview)
2. [Basic Usage](#2-basic-usage)
3. [Output Modes](#3-output-modes)
4. [Protocol Selection](#4-protocol-selection)
5. [Enforcement Options](#5-enforcement-options)
6. [Timeout and Redirects](#6-timeout-and-redirects)
7. [Examples](#7-examples)
8. [Nagios Integration](#8-nagios-integration)
9. [Exit Codes](#9-exit-codes)
10. [Help Output](#10-help-output)
11. [Hostname Resolution](#11-hostname-resolution)

## 1. Overview
check_html is a deterministic HTTP/HTTPS inspection and content‑validation tool.
It supports JSON, verbose, and Nagios output modes, and is designed for operators, automation systems, and monitoring platforms.

This guide describes the command‑line interface, output modes, examples, and Nagios integration.

## 2. Basic Usage
**HTTP check**
```bash
./check_html -H example.com
```
**HTTPS check**
```bash
./check_html -H example.com --https
```
**Explicit port**
```bash
./check_html -H example.com -p 8080
```
## 3. Output Modes
check_html supports three deterministic output modes.

### 3.1 JSON Mode (-j / --json)
Structured output for automation:

```bash
./check_html -H example.com --json
```
Produces a canonical JSON object containing:

* capture metadata
* backend detection
* enforcement results
* final status and message

### 3.2 Verbose Mode (-v / --verbose)
Human‑readable, multi‑section output:

```bash
./check_html -H example.com -v
```

Sections include:

* Request summary
* Capture details
* Backend detection
* Status enforcement
* Content‑type enforcement
* HTML enforcement
* Final result

### 3.3 Default Mode (Nagios Single‑Line)
No flags required:

```bash
./check_html -H example.com
``` 
Example OK:

```Code
OK - 200 OK (text/html)
```
Example failure:

```Code
CRITICAL - TLS handshake failed
```
This mode is used for Nagios/Icinga integration.

## 4. Protocol Selection

**Force HTTPS**
```bash
./check_html -H example.com --https
```

**Force HTTP**
```bash
./check_html -H example.com --http
```

**Auto‑detect (default)**

If neither flag is provided:

* HTTPS is used if the port is 443
* Otherwise HTTP is used

This behavior is deterministic and consistent across all output modes.

## 5. Enforcement Options
**Expected HTTP status**

```bash
./check_html -H example.com --expect-status 200
```

**Require HTML body**
```bash
./check_html -H example.com --require-html
```

**Require specific content‑type**
```bash
./check_html -H example.com --require-type text/html
```

**Backend enforcement**
```bash
./check_html -H example.com --require-backend nginx
```
Backend detection is based on server headers and known patterns.

## 6. Timeout and Redirects

**Set timeout (seconds)**
```bash
./check_html -H example.com -t 10
```
Default timeout is 10 seconds.

**Limit redirects**
```bash
./check_html -H example.com -t 5
```

Limit redirects
```bash
./check_html -H example.com --max-redirects 3
```

Redirects are followed deterministically up to the specified limit.

## 7. Examples

**Check a normal website**
```bash
./check_html -H example.com
```

**Check an HTTPS site with verbose output**
```bash
./check_html -H example.com --https -v
```

**Enforce HTML and content‑type**
```bash
./check_html -H example.com --require-html --require-type text/html
```

**Enforce backend fingerprint**
```bash
./check_html -H example.com --require-backend nginx
```

**JSON output for automation**
```bash
./check_html -H api.example.com --json
```

## 8. Nagios Integration

**Command definition**

```Cfg
define command {
    command_name    check_html
    command_line    /usr/local/nagios/libexec/check_html -H $ARG1$
}
```

**Service definition**

```Code
define service {
    use                 generic-service
    host_name           example.com
    service_description HTML Check
    check_command       check_html!example.com
}
```

**Example Nagios output**

```Code
OK - 200 OK (text/html)
``` 

## 9. Exit Codes
check_html uses standard Nagios exit codes:

| Code | Meaning |
| :---: | :--- |
| 0 | OK |
| 1 | WARNING |
| 2 | CRITICAL |
| 3 | UNKNOWN |

Exit codes are determined by the enforcement subsystem using Nagios‑aware severity merging:

**CRITICAL > WARNING > UNKNOWN > OK**

## 10. Help Output
View all flags:

```bash
./check_html --help
```

The CLI parser is noise‑free, grouped, and deterministic.

## 11. Hostname Resolution

All NMS_Tools plugins that accept -H require the hostname to be resolvable via the system resolver (DNS, /etc/hosts, or equivalent).

If the hostname cannot be resolved:

* The tool fails fast with a deterministic error message
* No network operations are attempted
* In Nagios mode, the tool exits UNKNOWN with a single clean line

**Deterministic Error Example**

```Code
UNKNOWN - Hostname resolution failed for 'badhost.example'
```

This behavior is consistent across all tools in the suite and is required for operator‑grade determinism and Nagios/Icinga compatibility.

