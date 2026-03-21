# check_html.py — Operation Guide
check_html.py is a deterministic HTTP/HTTPS inspection and content‑validation tool.
This document describes the runtime pipeline, capture behavior, enforcement model, output modes, and exit code logic.

## 1. Overview

Every execution of check_html.py follows a deterministic nine‑stage pipeline:

- Parse CLI
- Build URL / protocol selection
- Perform HTTP/TLS request
- Capture normalized response fields
- Backend detection
- Enforcement subsystems
- Build unified result object
- Output mode selection
- Exit with Nagios status code

Each stage produces structured data consumed by the next stage.
No stage performs implicit behavior or hidden side effects.

## 2. Stage 1 — CLI Parsing

The CLI parser:

- normalizes host, scheme, and port
- resolves protocol (--http, --https, or auto‑detect)
- loads enforcement options
- selects output mode (-j/--json, -v/--verbose, or default)
- validates incompatible or missing arguments

The parser is noise‑free and grouped for operator clarity.

## 3. Stage 2 — URL Construction & Protocol Selection

The tool constructs a canonical URL using:

- host
- scheme
- port
- path (default /)

Protocol rules:

- --https forces HTTPS
- --http forces HTTP
- otherwise:
- - port 443 → HTTPS
- - all other ports → HTTP

This stage also prepares request parameters (timeout, redirect limit, SNI behavior).

## 4. Stage 3 — HTTP/TLS Request

The request engine performs:

- TLS handshake (if HTTPS)
- redirect following (up to --max-redirects)
- final URL resolution
- response timing measurement

If the TLS handshake fails:

- no HTTP request is attempted
- backend detection is skipped
- enforcement subsystems receive a TLS failure state

## 5. Stage 4 — Response Capture

All response metadata is normalized into a structured capture object:

- status — HTTP status code or None
- headers — normalized header dictionary
- content_type — parsed from headers or None
- body — HTML body or None
- response_time — seconds
- final_url — after redirects
- redirects — count
- tls_error — boolean

This object is the foundation for backend detection and enforcement.

## 6. Stage 5 — Backend Detection

Backend detection runs only if TLS succeeded.

The detector analyzes:

- headers
- server banners
- HTML signatures
- known backend fingerprints

It produces:

- detected backend
- candidates
- confidence
- reason

If TLS failed, backend detection is skipped and the reason is set to "TLS handshake failed".

## 7. Stage 6 — Enforcement Subsystems

Each enforcement subsystem returns:

- a Nagios status
- a human‑readable message

The final status is determined by Nagios‑aware severity merging:

**CRITICAL > WARNING > UNKNOWN > OK**

### 7.1 Status Enforcement

- validates expected status
- handles forbidden statuses
- handles missing status (TLS failure)

### 7.2 Content‑Type Enforcement

- enforces presence of Content‑Type
- enforces required/forbidden types
- TLS failure → UNKNOWN

### 7.3 HTML Enforcement

- enforces presence of HTML body
- enforces required/forbidden tags (future)
- TLS failure → UNKNOWN

### 7.4 Backend Enforcement

- enforces required/forbidden backend
- TLS failure → CRITICAL

## 8. Stage 7 — Unified Result Object

All capture data, backend detection, and enforcement results are merged into a single deterministic result object:

- capture
- backend
- enforcement
- overall (final status + message)

This object drives all output modes.

## 9. Stage 8 — Output Modes

Exactly one output mode is selected:

### JSON Mode (-j or --json)

- full structured result
- stable schema for automation

### Verbose Mode (-v or --verbose)

- multi‑section operator output
- includes capture, backend, enforcement, and final result

### Default Mode (Nagios Single‑Line)

- one line only
- example OK:

Co```de
OK - 200 OK (text/html)
```

- example failure:

```Code
CRITICAL - TLS handshake failed
```

## 10. Stage 9 — Exit Codes

check_html.py uses standard Nagios exit codes:

| Code | Meaning |
|------|---------|
| 0	| OK |
| 1 | WARNING |
| 2 | CRITICAL |
| 3 | UNKNOWN |

Exit codes are determined by the merged enforcement results.

## 11. Troubleshooting

### TLS handshake failure

```Code
CRITICAL - TLS handshake failed
```

Occurs when the server rejects or cannot complete TLS negotiation.

### Missing content‑type

```Code
UNKNOWN - No content-type header
```

### Missing HTML body

```Code
UNKNOWN - No HTML body
```

### Backend mismatch

```Code
CRITICAL - Backend mismatch: expected nginx, detected apache
```