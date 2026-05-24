# Operation Guide — `check_cert.py`

This document explains how `check_cert.py` behaves at runtime, how to interpret
its output, and how enforcement, monitoring checks, and thresholds influence
exit codes. All behavior is deterministic and consistent across the NMS_Tools suite.

---

## 1. Default Behavior

When run without `-v` or `--json`, the tool emits a **single Nagios‑style line**:

OK - 60 days remaining (2026-05-18 18:19:55 UTC)

Code

This mode is designed for:

- Monitoring systems  
- Cron jobs  
- Shell scripts  
- Automated pipelines  

Nagios mode supports:

- **OK**
- **WARNING**
- **CRITICAL**
- **UNKNOWN**

Exit codes are determined by:

- expiration thresholds  
- monitoring checks  
- policy enforcement rules  

Nagios mode **never** emits multiple lines.

---

## 2. Output Modes

`check_cert.py` supports three output modes:

- **Nagios (default)** — single line  
- **Verbose (`-v`)** — human‑readable diagnostics  
- **JSON (`-j`)** — structured machine‑readable output  

Verbose and JSON modes are **opt‑in**.

---

## 3. Verbose Mode (`-v` / `--verbose`)

```bash
check_cert -H example.com -v
```

Verbose mode displays:

* Connection details
* TLS version and cipher
* Certificate metadata
* Hostname match result
* SAN list
* Key information
* AIA URLs and reconstructed chain
* OCSP URLs, status, and reachability
* Chain validation summary
* General warnings and errors
* Full enforcement summary

Verbose mode is intended for operators, debugging, and incident analysis.

## 4. JSON Mode (--json / -j)

```bash
check_cert -H example.com --json
```

JSON mode emits a deterministic object containing:

* Certificate metadata
* Key metadata
* SAN list
* TLS session details
* Expiration timestamps and days remaining
* OCSP URLs, status, and reachability
* Chain metadata
* General warnings and errors
* Full enforcement structure
* Hostname match metadata

JSON mode is ideal for:

* Automation
* Log ingestion
* Monitoring pipelines
* Programmatic inspection

All fields appear in canonical order.

## 5. Exit Codes

| Code | Meaning |
| :---: | :--- |
| 0 | OK |
| 1 | WARNING |
| 2 | CRITICAL |
| 3 | UNKNOWN |

### Exit Code Rules

* Expiration thresholds → OK/WARNING/CRITICAL
* Any enforcement failure → CRITICAL
* Any internal error → CRITICAL
* Hostname resolution failure → UNKNOWN
* Timeout or connection failure → UNKNOWN
* UNKNOWN always emits a single clean line.

## 6. Thresholds

Expiration thresholds

```bash
-w DAYS   Warning threshold
-c DAYS   Critical threshold
```

Example:

```bash
check_cert -H example.com -w 30 -c 10
```

Behavior

* days_remaining <= critical → CRITICAL
* days_remaining <= warning → WARNING
* otherwise → OK

Enforcement failures always override expiration thresholds.

## 7. Monitoring Checks (Default‑On)

Monitoring checks validate core certificate and TLS properties.

They can be individually disabled:

```Code
--no-check-expiration
--no-check-chain
--no-check-hostname
--no-check-san
--no-check-self-signed
```

### OCSP Monitoring

OCSP reachability is disabled by default and enabled with:

```Code
--check-ocsp
```

When enabled:

* OCSP URLs are extracted
* Reachability is tested via HTTP
* Failure triggers CRITICAL

This is a real network test, not placeholder behavior.

## 8. Policy Enforcement Rules (Explicit‑On)

Policy rules validate certificate, key, TLS, and OCSP properties beyond monitoring.

### Certificate Rules

```Code
--require-wildcard
--forbid-wildcard
-I ISSUER, --issuer ISSUER
-A SIGALG, --sigalg SIGALG
```

### Key Rules

```Code
--min-rsa BITS
--require-curve CURVE
```

### TLS Rules

```Code
--min-tls VERSION
--require-tls VERSION
--require-cipher CIPHER
--forbid-cipher CIPHER
--require-aead
--forbid-cbc
--forbid-rc4
```

### OCSP Rules

```Code
--require-ocsp
--forbid-ocsp
--ocsp-status {good,revoked,unknown,invalid}
```

OCSP status values include:

* good
* revoked
* unknown
* invalid
* none (no OCSP URLs present)

## 9. Enforcement Behavior

Enforcement results appear in:

* Nagios: CRITICAL if any rule fails
* Verbose: full “Enforcement Summary”
* JSON: structured enforcement object

Example JSON:

```json
"enforcement": {
  "applied": ["hostname_match", "expiration", "ocsp"],
  "passed": ["hostname_match", "expiration"],
  "failed": ["ocsp"],
  "errors": [],
  "state": 2
}
```

Enforcement never short‑circuits — all rules are evaluated.

## 10. Logging Behavior

Logging is enabled when a log directory is provided:

```Code
--log-dir /path/to/logs
```

Features:

* Deterministic formatting
* Timestamped entries
* Size‑based rotation (--log-max-mb)
* No external dependencies
* No registry usage
* Logged events include:
* Hostname resolution
* Connection lifecycle
* TLS negotiation
* Certificate parsing
* Chain validation
* OCSP reachability
* Enforcement evaluation

## 11. Troubleshooting

“tls_handshake_failed”

* Port blocked
* TLS version mismatch
* SNI mismatch

“no_certificate_present”

* Host does not serve TLS on the given port
* Missing -p for non‑443 services

“hostname_resolution_failed”

* Hostname not resolvable
* Tool exits UNKNOWN
* No network operations attempted

OCSP unreachable

* Firewall blocking outbound HTTP
* OCSP responder offline
* Certificate contains no OCSP URLs

Chain validation warnings

* Missing intermediates
* Mismatched issuer/subject
* Non‑standard chain structure

Chain warnings do not affect exit codes unless enforcement rules are used.

## 12. Network Requirements

* Outbound TCP to target host
* Outbound HTTP for AIA retrieval
* Outbound HTTP for OCSP reachability (when enabled)
