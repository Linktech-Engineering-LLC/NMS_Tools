# check_html.py — Metadata Schema (Version 1)

check_html.py produces a deterministic JSON object in --json mode.
This schema defines the structure, field names, and data types used by automation systems, monitoring platforms, and downstream tooling.

The schema is stable for version 1 and will only change in future versions with explicit versioning.

## 1. Top‑Level Structure
The JSON output contains four primary sections:

```json
{
  "capture": { ... },
  "backend": { ... },
  "enforcement": { ... },
  "overall": { ... }
}
```

Each section is documented below.

## 2. capture — HTTP/TLS Capture Metadata
The capture object contains normalized response metadata collected during the request.

| Field | Type | Description |
|-------|------|-------------|
| status | integer or null | HTTP status code, or null if TLS failed |
| headers |	object | Normalized header dictionary |
| content_type | string or null | Parsed Content‑Type header |
| body | string or null | HTML body (may be truncated in future versions) |
| response_time | float | Total request time in seconds |
| final_url | string | URL after redirects |
| redirects | integer |	Number of redirects followed |
| tls_error | boolean |	True if TLS handshake failed |

Example:

```json
"capture": {
  "status": 200,
  "headers": { "content-type": "text/html" },
  "content_type": "text/html",
  "body": "<html>...</html>",
  "response_time": 0.143,
  "final_url": "https://example.com/",
  "redirects": 1,
  "tls_error": false
}
```

## 3. backend — Backend Detection Metadata

The backend object contains the results of backend fingerprinting.

| Field | Type | Description |
|-------|------|-------------|
| detected | string or null | The most likely backend (e.g., "nginx", "apache") |
| candidates | array | List of possible backends |
| confidence | float | Confidence score (0.0–1.0) |
| reason | string |	Explanation of detection result |

Example:

```json
"backend": {
  "detected": "nginx",
  "candidates": ["nginx"],
  "confidence": 0.92,
  "reason": "Server header matched known nginx signature"
}
```

If TLS fails:

```json
"backend": {
  "detected": null,
  "candidates": [],
  "confidence": 0.0,
  "reason": "TLS handshake failed"
}
```

## 4. enforcement — Subsystem Results

Each enforcement subsystem returns a structured result:

```json
"enforcement": {
  "status": { ... },
  "content_type": { ... },
  "html": { ... },
  "backend": { ... }
}
```

Each subsystem object contains:

| Field | Type | Description |
|-------|------|-------------|
| status | string | Nagios status (OK, WARNING, CRITICAL, UNKNOWN) |
| message | string | Human‑readable explanation |

## 4.1 Status Enforcement

```json
"status": {
  "status": "OK",
  "message": "Status 200 OK"
}
```

## 4.2 Content‑Type Enforcement

```json
"content_type": {
  "status": "OK",
  "message": "Content-type text/html"
}
```

## 4.3 HTML Enforcement

```json
"html": {
  "status": "OK",
  "message": "HTML body present"
}
```

## 4.4 Backend Enforcement

```json
"backend": {
  "status": "OK",
  "message": "Backend nginx"
}
```

## 5. overall — Final Result

The overall object contains the merged Nagios status and final message.

| Field | Type | Description |
|-------|------|-------------|
| status | integer | Nagios exit code (0–3) |
| message |	string | Final single‑line message |

Example:

```json
"overall": {
  "status": 0,
  "message": "200 OK (text/html)"
}
```

If TLS fails:

```json
"overall": {
  "status": 2,
  "message": "TLS handshake failed"
}
```

## 6. Schema Stability

Version 1 guarantees:

- field names are stable
- object structure is stable
- data types are stable
- no fields will be removed in patch releases

Future versions may add:

- HTML tag metadata
- body size metadata
- redirect chain metadata
- backend fingerprint details

Any additions will be backward‑compatible.

