# check_html.py — Enforcement Model

**Part of:** NMS_Tools Monitoring Suite  
**Document:** Enforcement Model  
**Author:** Leon McClatchey, Linktech Engineering LLC  
**License:** MIT  
**Requires:** Python 3.12+  
**Last Updated:** 2026‑08‑17

## Table of Contents

1. [Overview](#1-overview)
2. [Enforcement Overview](#2-enforcement-overview)
3. [Status Enforcement](#2-status-enforcement)  
    1. [3.1 Inputs](#21-inputs)  
    2. [3.2 Rules](#22-rules)
4. [Content‑Type Enforcement](#3-content-type-enforcement)  
    1. [4.1 Inputs](#31-inputs)  
    2. [4.2 Rules](#32-rules)
5. [HTML Enforcement](#4-html-enforcement)  
    1. [5.1 Inputs](#41-inputs)  
    2. [5.2 Rules](#42-rules)
6. [Backend Enforcement](#5-backend-enforcement)  
    1. [6.1 Inputs](#51-inputs)  
    2. [6.2 Rules](#52-rules)
7. [Severity Merging](#6-severity-merging)
8. [Final Message Construction](#7-final-message-construction)
9. [Output Mode Interaction](#8-output-mode-interaction)  
    1. [9.1 JSON Mode](#81-json-mode)  
    2. [9.2 Verbose Mode](#82-verbose-mode)  
    3. [9.3 Quiet Mode](#83-quiet-mode)  
    4. [9.4 Nagios/Icinga Mode](#84-nagiosicinga-mode)  
    5. [9.5 Logging Behavior](#85-logging-behavior)

---

## 1. Overview

check_html.py implements a deterministic, multi‑stage enforcement engine.
Each subsystem evaluates a specific aspect of the HTTP/HTTPS response and returns a structured result:

* status — Nagios status (OK, WARNING, CRITICAL, UNKNOWN)
* message — Human‑readable explanation
* ok — Boolean pass/fail indicator
* expected — Expected value (if applicable)
* actual — Observed value (if applicable)

The final status is computed using strict Nagios severity precedence:

**CRITICAL > WARNING > UNKNOWN > OK**

This document defines the complete enforcement model for Version 1.

## 2. Enforcement Overview
The enforcement engine evaluates four independent domains:

1. Status Enforcement
2. Content‑Type Enforcement
3. HTML Enforcement
4. Backend Enforcement  

Each subsystem receives:

* the normalized capture object
* backend detection results
* CLI‑provided enforcement rules

Each subsystem returns a structured result:

```json
{
  "status": "OK",
  "message": "Status 200 OK",
  "ok": true,
  "expected": 200,
  "actual": 200
}
```

The engine merges these results into a final Nagios status and message.

## 3. Status Enforcement
Status enforcement validates the HTTP status code.

### 3.1 Inputs

* status from capture
* --expect-status (optional)
* TLS handshake state

### 3.2 Rules
**TLS failure**

```Code
CRITICAL - TLS handshake failed
```

**Expected status mismatch**

If --expect-status is provided:

```Code
CRITICAL - Expected 200, got 404
```

**Forbidden statuses**
| Status | Meaning | Result |
| :--- | :--- | :--- |
| 4xx |	Client error |	CRITICAL|
| 5xx |	Server error |	CRITICAL |

**Success**

```Code
OK - Status 200 OK
```
## 4. Content‑Type Enforcement
Validates the presence and correctness of the Content-Type header.

### 4.1 Inputs

* content_type from capture
* --require-type (optional)

### 4.2 Rules

Missing content‑type

```Code
UNKNOWN - No content-type header
```

**Required type mismatch**

```Code
CRITICAL - Expected content-type text/html, got application/json
```

**Success**

```Code
OK - Content-type text/html
```

## 5. HTML Enforcement
Validates the presence of an HTML body.

### 5.1 Inputs

* body from capture
* --require-html (optional)

### 5.2 Rules

**Missing HTML body (only if required)**

```Code
UNKNOWN - No HTML body
```

**Not required**
If --require-html is not provided:

```Code
OK - HTML body present or not required
```

**Success**

```Code
OK - HTML body present
```

## 6. Backend Enforcement
Validates the detected backend against operator expectations.

### 6.1 Inputs
* backend detection result
* --require-backend (optional)
* TLS handshake state

### 6.2 Rules

**TLS failure**
Backend cannot be evaluated:

```Code
UNKNOWN - Backend check skipped due to TLS failure
```

**Missing backend detection**

```Code
UNKNOWN - Unable to determine backend
```

**Backend mismatch**

```Code
CRITICAL - Backend mismatch: expected nginx, detected apache
```

**Success**

```Code
OK - Backend nginx
```

## 7. Severity Merging
Final status is computed using strict Nagios precedence:

**CRITICAL > WARNING > UNKNOWN > OK**

Examples:

* Any CRITICAL → final result is CRITICAL
* No CRITICAL but at least one UNKNOWN → UNKNOWN
No CRITICAL but at least one WARNING → WARNING
* Only UNKNOWN + OK → UNKNOWN
* All OK → OK

This ensures deterministic, operator‑grade behavior.

## 8. Final Message Construction
The final message is selected using:

* The highest‑severity subsystem’s message
* A clean, single‑line summary
* Optional OK‑path enhancement:

```Code
OK - 200 OK (text/html)
```

Nagios/Icinga mode always prints exactly one line.

## 9. Output Mode Interaction

check_html.py has four mutually exclusive output modes:

1. **JSON mode** (`--json`)
2. **Verbose mode** (`--verbose`)
3. **Quiet mode** (`--quiet`)
4. **Nagios/Icinga mode** (default when no other mode is selected)

Only one mode can ever be active.

### 9.1 JSON Mode
- Prints the full metadata object
- Includes capture, backend, enforcement, perfdata, and meta sections
- Intended for automation and downstream tooling

### 9.2 Verbose Mode
- Prints multi-line human-readable output
- Includes banners, subsystem summaries, and final status

### 9.3 Quiet Mode
- **Prints nothing**
- **Suppresses all stdout**
- Still performs full enforcement
- Still returns the correct Nagios exit code
- Logging is enabled only if `--log-dir` is provided

### 9.4 Nagios/Icinga Mode
- Activated when no other mode is selected
- Prints exactly **one clean line**
- Never writes logs (even if `--log-dir` is provided)
- Never prints warnings, verbose text, or JSON
- Designed for deterministic plugin behavior

### 9.5 Logging Behavior
Logging is enabled only when:

- `--log-dir` is provided  
- **and** the active mode is **not** Nagios/Icinga mode

Quiet mode **does** allow logging (if `--log-dir` is set), but still prints nothing.
