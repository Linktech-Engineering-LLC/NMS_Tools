# check_html.py — Operation Guide (Version 1 Final)

check_html.py is a deterministic HTTP/HTTPS inspection and content‑validation tool.
This document describes the runtime pipeline, capture behavior, backend detection,
enforcement model, output modes, and exit code logic.

## 1. Overview

Every execution of check_html.py follows a deterministic nine‑stage pipeline:

1. Parse CLI
2. Build URL / protocol selection
3. Perform HTTP/TLS request
4. Capture response metadata
5. Perform backend detection (if TLS succeeded)
6. Run enforcement subsystems
7. Build unified result object
8. Select output mode
9. Exit with Nagios status code

Each stage produces structured data consumed by the next stage.
No stage performs implicit behavior or hidden side effects.

## 2. Stage 1 — CLI Parsing

* The CLI parser:
* normalizes host, scheme, and port
* resolves protocol (--http, --https, or auto‑detect)
* loads enforcement options
* selects output mode (--json, --verbose, --quiet, or default)
* validates incompatible or missing arguments

The parser is noise‑free and grouped for operator clarity.

## 3. Stage 2 — URL Construction & Protocol Selection

The tool constructs a canonical URL using:

* host
* scheme
* port
* path (default /)

Protocol rules:

* --https forces HTTPS
* --http forces HTTP

otherwise:

* port 443 → HTTPS
* all other ports → HTTP

This stage also prepares request parameters (timeout, redirect limit, SNI behavior).

## 4. Stage 3 — HTTP/TLS Request

The request engine performs:

* TLS handshake (if HTTPS)
* redirect following (up to --max-redirects)
* final URL resolution
* response timing measurement
* If the TLS handshake fails:
* no HTTP request is attempted
* backend detection is skipped
* enforcement subsystems receive a TLS failure state

## 5. Stage 4 — Response Capture

All response metadata is normalized into a structured capture object:

* Status — HTTP status code or null
* headers — normalized header dictionary
* content_type — parsed from headers or null
* body — HTML body or null (JSON mode only)
* response_time — seconds
* final_url — after redirects
* redirects — count
* tls_error — string or null (error message if TLS failed)

This object is the foundation for backend detection and enforcement.

## 6. Stage 5 — Backend Detection

Backend detection runs only if TLS succeeded.

The detector analyzes:

* headers
* server banners
* HTML signatures
* known backend fingerprints

It produces:

* detected
* candidates
* confidence

reason

If TLS failed:

* backend detection is skipped
* detected = null
* candidates = []
* confidence = 0.0
* reason = "TLS handshake failed"

## 7. Stage 6 — Enforcement Subsystems
Each enforcement subsystem returns:

* status — Nagios status
* message — human‑readable explanation
* ok — boolean
* expected — expected value (if applicable)
* actual — observed value (if applicable)

The final status is determined by Nagios‑aware severity merging:

**CRITICAL > WARNING > UNKNOWN > OK**

### 7.1 Status Enforcement

* validates expected status
* handles forbidden statuses
* TLS failure → CRITICAL

### 7.2 Content‑Type Enforcement

* enforces presence of Content‑Type
* enforces required type
* TLS failure → UNKNOWN

### 7.3 HTML Enforcement

* enforces presence of HTML body only if --require-html is set
* otherwise OK even if body is empty
* TLS failure → UNKNOWN

## 7.4 Backend Enforcement

* enforces required backend
* TLS failure → UNKNOWN (backend cannot be evaluated)

## 8. Stage 7 — Unified Result Object

All capture data, backend detection, perfdata, and enforcement results are merged
into a single deterministic result object:

* meta
* capture
* backend
* enforcement
* perfdata
* overall (final status + message)

This object drives all output modes.

## 9. Stage 8 — Output Modes

Exactly one output mode is selected:

### JSON Mode (--json)

* prints the full structured result
* includes meta, capture, backend, enforcement, perfdata, and overall
* stable schema for automation

### Verbose Mode (--verbose)

* prints multi‑section operator output
* includes capture, backend, enforcement, and final result

### Quiet Mode (--quiet)

* prints nothing
* suppresses all stdout
* performs full enforcement internally
* returns the correct Nagios exit code
* logging is allowed if --log-dir is provided

### Nagios/Icinga Mode (default)

* Activated when no other mode is selected.
* prints exactly one clean line
* never writes logs (even if --log-dir is provided)
* never prints warnings, verbose text, or JSON
* designed for deterministic plugin behavior

Example OK:

```Code
OK - 200 OK (text/html)
```

Example failure:

```Code
CRITICAL - TLS handshake failed
```

## 10. Stage 9 — Exit Codes

check_html.py uses standard Nagios exit codes:

| Code | Meaning |
| :---: | :--- |
| 0 | OK |
| 1 | WARNING |
| 2 | CRITICAL |
| 3 | UNKNOWN |

Exit codes are determined by the merged enforcement results.

## 11. Troubleshooting
### TLS handshake failure

```Code
CRITICAL - TLS handshake failed
```

### Missing content‑type

```Code
UNKNOWN - No content-type header
```

### Missing HTML body (when required)

```Code
UNKNOWN - No HTML body
```

### Backend mismatch

```Code
CRITICAL - Backend mismatch: expected nginx, detected apache
```