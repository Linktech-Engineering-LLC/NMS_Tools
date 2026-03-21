# check_html.py — Enforcement Model

check_html.py implements a deterministic, multi‑stage enforcement engine.
Each subsystem evaluates a specific aspect of the HTTP/HTTPS response and returns:

- a Nagios status (OK, WARNING, CRITICAL, UNKNOWN)
- a human‑readable message

The final status is computed using Nagios‑aware severity merging:

**CRITICAL > WARNING > UNKNOWN > OK**

This document describes each enforcement subsystem, its rules, and its failure behavior.

## 1. Enforcement Overview
The enforcement engine evaluates four independent domains:

1. **Status Enforcement**
2. **Content‑Type Enforcement**
3. **HTML Enforcement**
4. **Backend Enforcement**

Each subsystem receives:

- the normalized capture object
- backend detection results
- CLI‑provided enforcement rules

Each subsystem returns a structured result:

- status
- message

The engine merges these results into a final Nagios status and message.

## 2. Status Enforcement

Status enforcement validates the HTTP status code.

### 2.1 Inputs

- status from capture
- --expect-status (optional)
- TLS handshake state

### 2.2 Rules

**Missing status (TLS failure)**

```Code
CRITICAL - TLS handshake failed
```

**Expected status mismatch**

If --expect-status is provided:

```Code
CRITICAL - Expected 200, got 404
```

**Forbidden statuses**

Certain statuses are always considered failures:

| Status | Meaning | Result |
|--------|---------|--------|
| 4xx |	Client | error | CRITICAL |
| 5xx | Server | error | CRITICAL |

**Success**
If the status is present and acceptable:

```Code
OK - Status 200 OK
```

## 3. Content‑Type Enforcement

Content‑type enforcement validates the presence and correctness of the Content-Type header.

### 3.1 Inputs

- content_type from capture
- --require-type (optional)

### 3.2 Rules

**Missing content‑type**

```Code
UNKNOWN - No content-type header
```

**Required type mismatch**

If --require-type is provided:

```Code
CRITICAL - Expected content-type text/html, got application/json
```

**Success**

```Code
OK - Content-type text/html
```

## 4. HTML Enforcement

HTML enforcement validates the presence of an HTML body.

### 4.1 Inputs

- body from capture
- --require-html (optional)

### 4.2 Rules

**Missing HTML body**
If --require-html is set:

```Code
UNKNOWN - No HTML body
```

**Future enhancements (not in v1)**

- required tags
- forbidden tags
- required text patterns
- HTML size thresholds

**Success**

```Code
OK - HTML body present
```

## 5. Backend Enforcement

Backend enforcement validates the detected backend against operator expectations.

### 5.1 Inputs

- backend detection result
- --require-backend (optional)
- TLS handshake state

### 5.2 Rules

**TLS failure**

Backend detection is skipped, and enforcement returns:

```Code
CRITICAL - Backend check skipped due to TLS failure
```

**Missing backend detection**

If detection could not determine a backend:

```Code
UNKNOWN - Unable to determine backend
```

**Backend mismatch**

If --require-backend is provided:

```Code
CRITICAL - Backend mismatch: expected nginx, detected apache
```

**Success**

```Code
OK - Backend nginx
```

## 6. Severity Merging

Each subsystem returns a Nagios status.
The final status is computed using strict Nagios precedence:

**CRITICAL > WARNING > UNKNOWN > OK**

Examples:

- If any subsystem returns **CRITICAL**, the final result is **CRITICAL**.
- If no *CRITICAL*s but at least one **WARNING**, final result is **WARNING**.
- If only **UNKNOWN** and OK, final result is **UNKNOWN**.
- Only if all subsystems return **OK** does the final result become **OK**.

This ensures deterministic, operator‑grade behavior.

## 7. Final Message Construction

The final message is selected using:

1. The highest‑severity subsystem’s message
2. A clean, single‑line summary
3. Optional OK‑path enhancement:

```Code
OK - 200 OK (text/html)
```

This ensures:

- failures are clear
- OK messages are informative
- Nagios output is always single‑line and noise‑free