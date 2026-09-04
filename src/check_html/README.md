# check_html — HTTP/HTTPS Inspection & Content Validation Tool

**Part of:** NMS_Tools Monitoring Suite  
**Script:** `check_html.py`  
**Author:** Leon McClatchey, Linktech Engineering LLC  
**License:** MIT  
**Requires:** Python 3.12+  (development only; not required for frozen binary)
**Last Updated:** 2026‑08‑17

![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-stable-brightgreen)
![Nagios Plugin](https://img.shields.io/badge/Nagios-plugin-success)
![NMS_Tools](https://img.shields.io/badge/NMS_Tools-check__html-blueviolet)

## Table of Contents

1. [Overview](#1-overview)
2. [Features](#2-features)
3. [Usage](#3-usage)
4. [Output Modes](#4-output-modes)  
    1. [5.1 Nagios/Icinga Mode](#41-nagiosicinga-mode)  
    2. [5.2 JSON Mode](#42-json-mode)  
    3. [5.3 Verbose Mode](#43-verbose-mode)  
    4. [5.4 Quiet Mode](#44-quiet-mode)
5. [Enforcement Model](#5-enforcement-model)
6. [Perfdata](#6-perfdata)
7. [CLI Reference](#7--cli-reference)
    1. [7.1 CLI Flags](#71-cli-flags)
8. [Exit Codes](#8-exit-codes)
9. [Documents](#9-documents)
10. [Tools in the Suite](#10-tools-in-this-suite)
11. [License](#11-license)

---

## 1. Overview

check_html is a deterministic HTTP/HTTPS inspection tool designed for monitoring environments.
It performs endpoint validation, backend fingerprinting, and content checks while producing clean, predictable output across JSON, verbose, quiet, and Nagios/Icinga modes.

## 2. Features

* Deterministic HTTP/HTTPS request pipeline with TLS awareness
* Status code validation (--expect-status)
* Content-Type validation (--expect-type)
* Optional HTML body presence validation (--require-html)
* Backend fingerprinting (headers, banners, HTML signatures)
* Stable JSON schema for automation
* Clean, noise‑free CLI parser
* Nagios/Icinga‑compatible exit codes and perfdata
* Fast, dependency‑light implementation

## 3. Usage
Basic usage:

```bash
./check_html -H <host>
```

The following are the most commonly used options. For the full flag reference, see [Section 7.1](#71-cli-flags).

```Code
-H, --host           Target hostname or IP
-p, --port           Port (default: 80 or 443 based on scheme)
--http               Force HTTP
--https              Force HTTPS
-j, --json           Output JSON
-v, --verbose        Verbose diagnostic output
-q, --quiet          Suppress all stdout (exit code only)
--timeout            Connection timeout (default: 5s)
--expect-status      Expected HTTP status code (e.g., 200)
--expect-type        Expected Content-Type (e.g., text/html)
--require-html       Require HTML content in the response body
--require-backend    Require detected backend (e.g., nginx)
--log-dir            Enable logging (disabled in Nagios mode)
```

Nagios/Icinga mode (default) produces a single deterministic line:

```Code
OK - 200 OK (text/html) | latency=0.0012s;;; size=331B;;;
```

## 4. Output Modes

check_html has four mutually exclusive output modes:

### 4.1 Nagios/Icinga Mode (default)

* Activated when no other mode is selected
* Prints exactly one clean line
* Never writes logs (even if --log-dir is provided)
* Designed for deterministic plugin behavior

### 4.2 JSON Mode (-j)

Machine‑readable structured output including:

* meta (mode, timestamp, logging state)
* capture (status, headers, content type, body, timing, redirects)
* backend detection
* enforcement results
* perfdata
* final merged status

### 4.3 Verbose Mode (-v)

Human‑readable diagnostic report including:

* connection details
* TLS session (if HTTPS)
* headers
* backend detection
* enforcement summary
* final result

### 4.4 Quiet Mode (-q)

* Prints nothing
* Performs full enforcement internally
* Returns the correct Nagios exit code
* Logging is allowed if --log-dir is provided

## 5. Enforcement Model

check_html applies deterministic validation rules:

* **Status Enforcement** — validates status code and expected value
* **Content-Type Enforcement** — validates presence and expected type
* **HTML Enforcement** — validates HTML body when required
* **Backend Enforcement** — fingerprints server backend and validates expectations

Nagios severity precedence:

**CRITICAL > WARNING > UNKNOWN > OK**

## 6. Perfdata

Perfdata fields include:

* latency — response time
* size — body size in bytes
* warn_rt, crit_rt — latency thresholds
* warn_size, crit_size — size thresholds

Perfdata is included in:

* Nagios/Icinga mode
* Verbose mode
* JSON mode

Not included in Quiet mode (no output).

## 7. 🔧 CLI Reference

usage: check_html -H <host> [options]

### 7.1 CLI Flags
These are the **user‑facing CLI flags** for `check_html`.
Internal bitmask flags used by the enforcement engine are documented globally in `FLAGS.md`.

#### Output Modes
| Flag | Description |
| --- | --- |
| ``-v``, ``--verbose`` | Verbose output mode |
| ``-j``, ``--json`` | JSON output mode |
| ``-q``, ``--quiet`` | Quiet mode (exit code only) |
| ``--color`` | Colorize terminal output (verbose/JSON) |
| ``--output ``FILE`` | Write output to FILE instead of stdout |

#### Logging
| Flag | Description |
| --- | --- |
| ``--log-dir ``DIR`` | Directory to store logs |
| ``--log-max-mb ``SIZE`` | Maximum log size before rotation (default: 50 MB) |

#### Core Options
| Flag | Description |
| --- | --- |
| ``-H ``HOST``, ``--host ``HOST`` | Target hostname or URL |
| ``-p ``PORT``, ``--port ``PORT`` | Port to connect to (default: 80) |
| ``--timeout ``SECONDS`` | Connection timeout (default: 5 seconds) |

#### Connection Options
| Flag | Description |
| --- | --- |
| ``--https`` | Force HTTPS request |
| ``--http`` | Force HTTP request |
| ``--no-redirect`` | Do not follow redirects |
| ``--max-redirects ``N`` | Maximum redirects allowed (default: 5) |

#### HTTP Status Requirements
| Flag | Description |
| --- | --- |
| ``--expect-status ``CODE`` | Expected HTTP status (default: 200) |
| ``--expect-family ``FAMILY`` | Expected status family (e.g., ``2xx``) |
| ``--forbid-status ``CODE`` | Fail if this status is returned |

#### Content-Type Requirements
| Flag | Description |
| --- | --- |
| ``--require-content-type ``TYPE`` | Required Content-Type (default: ``text/html``) |
| ``--forbid-content-type ``TYPE`` | Fail if this Content-Type is returned |

#### HTML Requirements
| Flag | Description |
| --- | --- |
| ``--require-tag ``TAG`` | Require specific HTML tag (repeatable) |
| ``--forbid-tag ``TAG`` | Forbid specific HTML tag (repeatable) |
| ``--require-text ``TEXT`` | Require specific text (repeatable) |
| ``--forbid-text ``TEXT`` | Forbid specific text (repeatable) |
| ``--max-size ``BYTES`` | Maximum allowed page size |

#### Backend Fingerprinting
| Flag | Description |
| --- | --- |
| ``--require-tomcat`` | Require Apache Tomcat backend |
| ``--forbid-tomcat`` | Fail if backend is Tomcat |
| ``--require-apache`` | Require Apache HTTPD backend |
| ``--forbid-apache`` | Fail if backend is Apache |
| ``--require-nginx`` | Require Nginx backend |
| ``--forbid-nginx`` | Fail if backend is Nginx |
| ``--require-iis`` | Require Microsoft IIS backend |
| ``--forbid-iis`` | Fail if backend is IIS |
| ``--require-jetty`` | Require Jetty backend |
| ``--forbid-jetty`` | Fail if backend is Jetty |
| ``--require-express`` | Require Node.js/Express backend |
| ``--forbid-express`` | Fail if backend is Express |
| ``--require-gunicorn`` | Require Gunicorn backend |
| ``--forbid-gunicorn`` | Fail if backend is Gunicorn |
| ``--require-backend ``TYPE`` | Require backend from list (repeatable) |
| ``--forbid-backend ``TYPE`` | Forbid backend from list (repeatable) |

#### Security Requirements
| Flag | Description |
| --- | --- |
| ``--require-https`` | Fail if HTTPS is not used |
| ``--require-https-redirect`` | Require HTTP→HTTPS redirect |
| ``--require-hsts`` | Require Strict-Transport-Security header |
| ``--require-header ``HEADER:VALUE`` | Require specific header |

#### Nagios Thresholds
| Flag | Description |
| --- | --- |
| ``--warning-rt ``SECONDS`` | Warning threshold for response time (default: 0.5s) |
| ``--critical-rt ``SECONDS`` | Critical threshold for response time (default: 1.0s) |
| ``--warning-size ``BYTES`` | Warning threshold for page size (default: 204800) |
| ``--critical-size ``BYTES`` | Critical threshold for page size (default: 512000) |

#### Internal Flags
Internal bitmask flags used by the enforcement engine (JSON/VERBOSE/QUIET priority, FAIL_ONLY behavior, REQUIRE_ALL/REQUIRE_ANY semantics, etc.) are documented globally:

See: [FLAGS](../../docs/FLAGS.md)

## 8. Exit Codes

| Code | Meaning |
| :---: | :--- |
| 0 |	OK |
| 1 | WARNING |
| 2 | CRITICAL |
| 3 | UNKNOWN |

Exit codes are determined by merged enforcement results.

## 9. Documents
Documentation is available under:

check_html/docs/
Including:

* [Installation.md](docs/Installation.md)
* [Usage.md](docs/Usage.md)
* [Enforcement.md](docs/Enforcement.md)
* [Metadata_Schema.md](docs/Metadata_schema.md)
* [Operation.md](docs/Operation.md)
* [Roadmap.md](docs/Roadmap.md)
* [Logging.md](docs/Logging.md)

## 10. Tools in This Suite

| Tool | Description | Documentation |
|------|-------------|---------------|
| **check_cert** | TLS certificate inspection and expiration validation | [../check_cert/README.md](../check_cert/README.md) |
| **check_html** | HTTP/HTTPS content validation and deterministic HTML checks | - |
| **check_interfaces** | Network interface inspection and operational state reporting | [../check_interfaces/README.md](../check_interfaces/README.md) |
| **check_ports** | Port and service availability inspection | [../check_ports/README.md](../check_ports/README.md) |
| **check_weather** | Deterministic weather client for monitoring pipelines | [../check_weather/README.md](../check_weather/README.md) |
| **check_ticker** | Deterministic market/ticker client using PythonTools finance providers | [README.md](README.md) |


## 11. License
* Source code: MIT [LICENSE](../../LICENSE) for details.
* Frozen binary: Proprietary [LICENSE_BINARY](../../LICENSE_BINARY.txt)
