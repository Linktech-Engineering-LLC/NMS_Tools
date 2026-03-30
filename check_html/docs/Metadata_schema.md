# check_html.py — Metadata Schema (Version 1, Final)
check_html.py produces a deterministic JSON object when --json is used.
This schema defines the complete structure, field names, and data types used by automation systems, monitoring platforms, and downstream tooling.

The schema is stable for Version 1.
Future versions will increment the schema version and remain backward‑compatible.

## 1. Top‑Level Structure
The JSON output contains five primary sections:

```json
{
  "meta": { ... },
  "capture": { ... },
  "backend": { ... },
  "enforcement": { ... },
  "perfdata": { ... },
  "overall": { ... }
}
```
Each section is documented below.

## 2. meta — Execution Metadata
The meta object contains deterministic metadata describing the execution environment and runtime behavior.

| Field | Type |	Description |
| :--- | :--- | :--- |
| script_name |	string |	Name of the tool (check_html) |
| version |	string |	Tool version string |
| mode |	string |	Execution mode (json, verbose, quiet, nagios) |
| timestamp |	string |	ISO‑8601 timestamp of execution |
| log_dir |	string or null |	Log directory if provided |
| log_enabled |	boolean |	True only if --log-dir is provided and mode is not Nagios |
| warnings |	array |	List of non‑fatal warnings (rotation failures, etc.) |

Example:

```json
"meta": {
  "script_name": "check_html",
  "version": "1.0.0",
  "mode": "json",
  "timestamp": "2026-03-30T08:56:38",
  "log_dir": "/var/log/nms_tools",
  "log_enabled": true,
  "warnings": []
}
```

## 3. capture — HTTP/TLS Capture Metadata
The capture object contains normalized metadata collected during the HTTP/HTTPS request.

| Field | Type | Description |
| :--- | :--- | :--- |
| status | integer or null | HTTP status code, or null if TLS failed |
| headers | object | Normalized header dictionary |
| content_type | string or null | Parsed Content‑Type header |
| body | string or null | HTML body (present only in JSON mode) |
| response_time | float | Total request time in seconds |
| final_url | string | URL after redirects |
| redirects | integer | Number of redirects followed |
| tls_error | string or null | Error message if TLS handshake failed |

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
  "tls_error": null
}
```

## 4. backend — Backend Detection Metadata
The backend object contains the results of backend fingerprinting.

| Field | Type | Description |
| :--- | :--- | :--- |
| detected | string or null | Most likely backend (e.g., "nginx", "apache") |
| candidates | array | List of possible backends |
| confidence | float | Confidence score (0.0–1.0) |
| reason | string | Explanation of detection result |

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

## 5. enforcement — Subsystem Results
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
| :--- | :--- | :--- |
| status | string | Nagios status (OK, WARNING, CRITICAL, UNKNOWN) |
| message | string | Human‑readable explanation |
| ok | boolean | True if subsystem passed |
| expected | string or number or null | Expected value (if applicable) |
| actual | string or number or null | Actual observed value |

### 5.1 Status Enforcement

```json
"status": {
  "status": "OK",
  "message": "Status 200 OK",
  "ok": true,
  "expected": 200,
  "actual": 200
}
```

### 5.2 Content‑Type Enforcement

```json
"content_type": {
  "status": "OK",
  "message": "Content-type text/html",
  "ok": true,
  "expected": "text/html",
  "actual": "text/html"
}
```

### 5.3 HTML Enforcement

```json
"html": {
  "status": "OK",
  "message": "HTML body present",
  "ok": true,
  "expected": "non-empty body",
  "actual": "present"
}
```

### 5.4 Backend Enforcement

```json
"backend": {
  "status": "OK",
  "message": "Backend nginx",
  "ok": true,
  "expected": "nginx",
  "actual": "nginx"
}
```

## 6. perfdata — Performance Metrics
Perfdata fields are emitted for monitoring systems and graphing engines.

| Field | Type | Description |
| :--- | :--- | :--- |
| latency | float | Response latency in seconds |
| size | integer | Body size in bytes |
| warn_rt | float | Warning threshold for latency |
| crit_rt | float | Critical threshold for latency |
| warn_size | integer | Warning threshold for size |
| crit_size | integer | Critical threshold for size |

Example:

```json
"perfdata": {
  "latency": 0.143,
  "size": 4521,
  "warn_rt": 0.5,
  "crit_rt": 1.0,
  "warn_size": 204800,
  "crit_size": 512000
}
```

## 7. overall — Final Result
The overall object contains the merged Nagios status and final message.

| Field | Type | Description |
| :--- | :--- | :--- |
| status | integer | Nagios exit code (0–3) |
| message | string | Final single‑line message |

Example:

```json
"overall": {
  "status": 0,
  "message": "200 OK (text/html)"
}
```

TLS failure example:

```json
"overall": {
  "status": 2,
  "message": "TLS handshake failed"
}
```

## 8. Output Modes and Nagios/Icinga Behavior

check_html.py has **four mutually exclusive output modes**:

1. **JSON mode** (`--json`)
2. **Verbose mode** (`--verbose`)
3. **Quiet mode** (`--quiet`)
4. **Nagios/Icinga mode** (default when no other mode is selected)

Only one mode can ever be active.

### Logging Behavior
Logging is enabled only when **both** of the following are true:

- `--log-dir` is provided  
- The active mode is **not** Nagios/Icinga mode  

### Nagios/Icinga Mode Rules
Nagios/Icinga mode is the default fallback mode and is designed to be
completely side‑effect‑free:

- Never writes logs (even if `--log-dir` is provided)
- Never prints warnings or rotation notices
- Never prints verbose or JSON structures
- Emits exactly **one clean line** of output
- Produces standard Nagios exit codes (0–3)

Nagios/Icinga mode is activated automatically when no other output mode
(`--json`, `--verbose`, `--quiet`) is selected.

## 9. Schema Stability

Version 1 guarantees:

* field names are stable
* object structure is stable
* data types are stable
* no fields will be removed in patch releases

Future versions may add:

* HTML tag metadata
* redirect chain metadata
* backend fingerprint details
* body truncation metadata

All additions will be backward‑compatible.