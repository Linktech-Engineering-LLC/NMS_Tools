# Usage Guide — check_cert.py
This guide explains how to invoke check_cert.py, what each flag does, and how to combine modes, thresholds, and enforcement rules.

## 1. Basic Checks

```bash
check_cert -H example.com
```
This emits a single Nagios‑style line:

```Code
OK - 85 days remaining (2026-06-13 00:00:00 UTC)
```
This default mode is designed for:

### Monitoring systems

* Cron jobs
* Shell scripts
* Automated pipelines

Nagios mode supports:

* OK
* WARNING
* CRITICAL
* UNKNOWN

Exit codes are determined by expiration thresholds and enforcement failures.

## 2. Verbose Output

```bash
check_cert -H example.com -v
```

Verbose mode displays:

* Connection details
* TLS version and cipher
* Certificate metadata
* Hostname match result (hostname_matches)
* SAN list
* Key information
* AIA URLs and intermediate chain
* OCSP metadata
* Chain validation summary
* General warnings and errors
* Enforcement summary

Verbose mode is grouped, noise‑free, and deterministic.

Chain warnings appear only in verbose/JSON, never in Nagios output.

## 3. JSON Output

```bash
check_cert -H example.com --json
```

Emits a deterministic JSON object containing:

* Certificate metadata
* Hostname match result
* Key metadata
* SAN list
* TLS session details
* Expiration timestamps and days remaining
* AIA metadata
* Chain metadata
* OCSP metadata
* General warnings and errors
* Enforcement results

JSON mode is ideal for:

* Automation
* Log ingestion
* Programmatic inspection
* Monitoring pipelines

All JSON fields follow a strict canonical ordering.

## 4. Expiration Thresholds

Set Nagios thresholds:

```Code
-w DAYS   Warning threshold
-c DAYS   Critical threshold
```

Example:

```bash
check_cert -H example.com -w 30 -c 10
```

Behavior:

* days_remaining <= critical → CRITICAL
* days_remaining <= warning → WARNING
* otherwise → OK

Thresholds apply only to expiration unless enforcement rules are used.

Any enforcement failure produces CRITICAL.

## 5. Enforcement Rules

Enforcement rules validate certificate, TLS, and OCSP properties.

Failures appear in:

* JSON → enforcement.failed
* Verbose → “Enforcement Summary”
* Nagios → CRITICAL

### OCSP Enforcement

```Code
--require-ocsp
--forbid-ocsp
--ocsp-status {good,revoked,unknown,invalid}
```

**Note:**

OCSP support is currently limited to:

* Extracting OCSP URLs
* Reporting presence/absence
* Reporting placeholder state (unknown)
* revocation_reason always null
* Full OCSP response parsing is planned.

### TLS Requirements

```Code
--min-tls VERSION
--require-tls VERSION
--require-cipher CIPHER
--forbid-cipher CIPHER
--require-aead
--forbid-cbc
--forbid-rc4
```

### Key Requirements

```Code
--min-rsa BITS
--require-curve CURVE
```

### Certificate Requirements

```Code
--require-wildcard
--forbid-wildcard
-I, --issuer ISSUER
-A, --sigalg ALGORITHM
```

## 6. Port, Timeout, SNI, and IP Mode

**Port**

```bash
check_cert -H mail.example.com -p 587
```

**Timeout**

```Code
--timeout SECONDS
```

**Disable SNI**

```Code
--no-sni
```

**IP‑Only Mode**

```Code
--ip-mode
```

Forces IP‑only checks:

* Disables hostname matching
* Disables SNI
* Useful for IP‑based monitoring

## 7. Insecure Mode

Skip certificate validation during the TLS handshake:

```Code
--insecure
```

This does **not** disable:

* Chain validation
* Hostname matching
* Enforcement rules

It only affects the TLS handshake.

## 8. Nagios Integration

### Command Definition

```Code
define command {
    command_name    check_cert
    command_line    /usr/lib/nagios/plugins/check_cert -H $HOSTADDRESS$ -w 30 -c 10
}
```

### Service Definition

```Code
define service {
    use                 generic-service
    host_name           myserver
    service_description TLS Certificate
    check_command       check_cert
}
```

## 9. Example Outputs

### Default

```Code
OK - 60 days remaining (2026-05-18 18:19:55 UTC)
```

### Verbose (truncated)

```Code
Host: example.com
Port: 443
TLS Version: tls1.3
Cipher: TLS_AES_256_GCM_SHA384
Issuer CN: Example CA
```

...
### JSON (truncated, schema‑accurate)

```json
{
  "host": "example.com",
  "port": 443,
  "timestamp_utc": "2026-05-18T18:19:55Z",
  "expiration": {
    "days_remaining": 60
  },
  "certificate": {
    "subject_cn": "example.com",
    "issuer_cn": "Example CA"
  },
  "hostname_matches": true,
  "tls": {
    "version": "tls1.3",
    "cipher": "TLS_AES_256_GCM_SHA384"
  },
  "warnings": [],
  "errors": []
}
```

## 10. Troubleshooting

**“tls_handshake_failed”**

* Port blocked
* TLS version mismatch
* SNI mismatch

**“no_certificate_present”**

* Host does not serve TLS on the given port
* Missing -p for non‑443 services

**“hostname_resolution_failed”**

* Hostname not resolvable
* Tool exits UNKNOWN
* No network operations attempted

**OCSP unreachable**

* Firewall blocking outbound HTTP
* OCSP responder offline

**Chain validation warnings**

* Missing intermediates
* Mismatched issuer/subject
* Non‑standard chain structure

Chain warnings never affect exit codes unless enforcement rules are used.

## 11. Network Requirements

* Outbound TCP to target host
* Outbound HTTP for AIA retrieval
* Outbound HTTP for OCSP (future retrieval)

## 12. Hostname Resolution

All NMS_Tools plugins that accept -H require the hostname to be resolvable via the system resolver (DNS, /etc/hosts, or equivalent).

If the hostname cannot be resolved:

* The tool fails fast with a deterministic error
* No network operations are attempted
* In Nagios mode, the tool exits UNKNOWN with a single clean line

### Deterministic Error Example

```Code
UNKNOWN - Hostname resolution failed for 'badhost.example'
```

This behavior is consistent across all tools in the suite.