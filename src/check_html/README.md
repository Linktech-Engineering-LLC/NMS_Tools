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
3. [Installation](#3-installation)
4. [Usage](#4-usage)
5. [Output Modes](#5-output-modes)  
    1. [5.1 Nagios/Icinga Mode](#51-nagiosicinga-mode)  
    2. [5.2 JSON Mode](#52-json-mode)  
    3. [5.3 Verbose Mode](#53-verbose-mode)  
    4. [5.4 Quiet Mode](#54-quiet-mode)
6. [Enforcement Model](#6-enforcement-model)
7. [Perfdata](#7-perfdata)
8. [Exit Codes](#8-exit-codes)
9. [Documents](#9-documents)
10. [License](#10-license)

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

## 3. Installation

check_html.py requires:

* Python 3.6+
* requests library

Install dependencies:

```bash
pip install requests
```

The tool is standalone and does not require system packages or external binaries.

## 4. Usage
Basic usage:

```bash
./check_html -H <host>
```

Common options:

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

## 5. Output Modes

check_html has four mutually exclusive output modes:

### 5.1 Nagios/Icinga Mode (default)

* Activated when no other mode is selected
* Prints exactly one clean line
* Never writes logs (even if --log-dir is provided)
* Designed for deterministic plugin behavior

### 5.2 JSON Mode (-j)

Machine‑readable structured output including:

* meta (mode, timestamp, logging state)
* capture (status, headers, content type, body, timing, redirects)
* backend detection
* enforcement results
* perfdata
* final merged status

### 5.3 Verbose Mode (-v)

Human‑readable diagnostic report including:

* connection details
* TLS session (if HTTPS)
* headers
* backend detection
* enforcement summary
* final result

### 5.4 Quiet Mode (-q)

* Prints nothing
* Performs full enforcement internally
* Returns the correct Nagios exit code
* Logging is allowed if --log-dir is provided

## 6. Enforcement Model

check_html applies deterministic validation rules:

* **Status Enforcement** — validates status code and expected value
* **Content-Type Enforcement** — validates presence and expected type
* **HTML Enforcement** — validates HTML body when required
* **Backend Enforcement** — fingerprints server backend and validates expectations

Nagios severity precedence:

**CRITICAL > WARNING > UNKNOWN > OK**

## 7. Perfdata

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


## 10. License

This tool is part of the NMS_Tools suite.
See the root project for licensing, documentation, and contributor guidelines.