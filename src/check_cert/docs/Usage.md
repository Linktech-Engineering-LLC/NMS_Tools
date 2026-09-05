md
# Usage Guide — check_cert.py

**Part of:** NMS_Tools Monitoring Suite  
**Document:** Usage Guide  
**Author:** Leon McClatchey, Linktech Engineering LLC  
**License:** MIT  
**Requires:** Python 3.12+  (development only; not required for frozen binary)
**Last Updated:** 2026‑08‑17

## Table of Contents

1. [Overview](#1-overview)
2. [Basic Checks](#2-basic-checks)
3. [Verbose Output](#3-verbose-output)
4. [JSON Output](#4-json-output)
5. [Expiration Thresholds](#5-expiration-thresholds)
6. [Enforcement Rules](#6-enforcement-rules)  
    1. [6.1 OCSP Enforcement](#61-ocsp-enforcement)  
    2. [6.2 TLS Requirements](#62-tls-requirements)  
    3. [6.3 Key Requirements](#63-key-requirements)  
    4. [6.4 Certificate Requirements](#64-certificate-requirements)
7. [Port, Timeout, SNI, and IP Mode](#7-port-timeout-sni-and-ip-mode)
8. [Insecure Mode](#8-insecure-mode)
9. [Nagios Integration](#9-nagios-integration)
10. [Example Outputs](#10-example-outputs)
11. [Troubleshooting](#11-troubleshooting)
12. [Network Requirements](#12-network-requirements)
13. [Hostname Resolution](#13-hostname-resolution)
14. [Exit Codes](#14-exit-codes)
15. [Full Flag Reference (Alphabetical)](#15-full-flag-reference-alphabetical)
16. [Enforcement Rule Summary](#16-enforcement-rule-summary)
17. [JSON Structure (High‑Level)](#17-json-structure-high-level)
18. [Deterministic Behavior Guarantees](#18-deterministic-behavior-guarantees)
19. [Logging](#19-logging)
20. [Version Information](#20-version-information)
21. [Additional Examples](#21-additional-examples)
22. [NMS_Tools Integration Notes](#22-nms_tools-integration-notes)
23. [See Also](#23-see-also)

---

## 1. Overview

This guide explains how to invoke `check_cert`, how each flag behaves, and how to combine modes, thresholds, and enforcement rules. All behavior is deterministic and consistent across the NMS_Tools suite.

---

## 2. Basic Checks

```bash
check_cert -H example.com
```

This emits a single Nagios‑style line:

```
OK - 85 days remaining (2026-06-13 00:00:00 UTC)
```
This default mode is designed for:

* Monitoring systems
* Cron jobs
* Shell scripts
* Automated pipelines

Nagios mode supports:

* OK
* WARNING
* CRITICAL
* UNKNOWN

Exit codes are determined by expiration thresholds and enforcement failures.

## 3. Verbose Output

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
* AIA URLs and intermediate chain
* OCSP metadata
* Chain validation summary
* General warnings and errors
* Enforcement summary

Verbose mode is grouped, noise‑free, and deterministic.

Chain warnings appear only in verbose/JSON, never in Nagios output.

## 4. JSON Output

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

## 5. Expiration Thresholds

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

## 6. Enforcement Rules

Enforcement rules validate certificate, TLS, and OCSP properties.

Failures appear in:

* JSON → enforcement.failed
* Verbose → “Enforcement Summary”
* Nagios → CRITICAL

### 6.1 OCSP Enforcement

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

Full OCSP response parsing is planned.

### 6.2 TLS Requirements

```Code
--min-tls VERSION
--require-tls VERSION
--require-cipher CIPHER
--forbid-cipher CIPHER
--require-aead
--forbid-cbc
--forbid-rc4
```

### 6.3 Key Requirements

```Code
--min-rsa BITS
--require-curve CURVE
```

### 6.4 Certificate Requirements

```Code
--require-wildcard
--forbid-wildcard
-I, --issuer ISSUER
-A, --sigalg ALGORITHM
```

## 7. Port, Timeout, SNI, and IP Mode

Port

```bash
check_cert -H mail.example.com -p 587
```

Timeout

```Code
--timeout SECONDS
```

Disable SNI

```Code
--no-sni
```

IP‑Only Mode

```Code
--ip-mode
```
Forces IP‑only checks:

* Disables hostname matching
* Disables SNI

Useful for IP‑based monitoring

## 8. Insecure Mode

Skip certificate validation during the TLS handshake:

```Code
--insecure
```

This does not disable:

* Chain validation
* Hostname matching
* Enforcement rules

It only affects the TLS handshake.

## 9. Nagios Integration

Command Definition

```Code
define command {
    command_name    check_cert
    command_line    /usr/lib/nagios/plugins/check_cert -H $HOSTADDRESS$ -w 30 -c 10
}
```

Service Definition

```Code
define service {
    use                 generic-service
    host_name           myserver
    service_description TLS Certificate
    check_command       check_cert
}
```

## 10. Example Outputs

Default

```Code
OK - 60 days remaining (2026-05-18 18:19:55 UTC)
```

Verbose (truncated)

```Code
Host: example.com
Port: 443
TLS Version: tls1.3
Cipher: TLS_AES_256_GCM_SHA384
Issuer CN: Example CA
```

JSON (truncated)

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

Chain validation warnings

* Missing intermediates
* Mismatched issuer/subject
* Non‑standard chain structure

Chain warnings never affect exit codes unless enforcement rules are used.

## 12. Network Requirements

* Outbound TCP to target host
* Outbound HTTP for AIA retrieval
* Outbound HTTP for OCSP (future retrieval)

## 13. Hostname Resolution

All NMS_Tools plugins that accept -H require the hostname to be resolvable via the system resolver.

If the hostname cannot be resolved:

* The tool fails fast with a deterministic error
* No network operations are attempted
* In Nagios mode, the tool exits UNKNOWN with a single clean line

### 13.1 Deterministic Error Example

```Code
UNKNOWN - Hostname resolution failed for 'badhost.example'
```

## 14. Exit Codes

```Code
0   OK
1   WARNING
2   CRITICAL
3   UNKNOWN
```

**Rules**

* Expiration thresholds → WARNING/CRITICAL
* Enforcement failures → CRITICAL
* Resolution/timeout/internal errors → UNKNOWN

## 15. Full Flag Reference (Alphabetical)

```Code
-A, --sigalg ALGORITHM
--forbid-cbc
--forbid-ocsp
--forbid-rc4
--forbid-wildcard
-H HOST
--ip-mode
-I, --issuer ISSUER
--insecure
--json
--min-rsa BITS
--min-tls VERSION
--no-sni
-p, --port PORT
--require-aead
--require-cipher CIPHER
--require-curve CURVE
--require-ocsp
--require-tls VERSION
--require-wildcard
--ocsp-status STATUS
--timeout SECONDS
-v, --verbose
-w DAYS
-c DAYS
--version
```

## 16. Enforcement Rule Summary


| Rule | Type |	Flag |	Failure | Condition |	Impact |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TLS Version |	--min-tls, --require-tls |	Version too low or mismatched |	CRITICAL |
| Cipher |	--require-cipher, --forbid-cipher, --require-aead, --forbid-cbc, --forbid-rc4 |	Negotiated cipher violates rule |	CRITICAL |
| Key Strength | --min-rsa, --require-curve |	RSA bits too low or EC curve mismatch |	CRITICAL |
| Certificate |	--require-wildcard, --forbid-wildcard, --issuer, --sigalg |	Certificate does not meet requirement |	CRITICAL |
| OCSP |	--require-ocsp, --forbid-ocsp, --ocsp-status |	OCSP presence/state violates rule |	CRITICAL |

## 17. JSON Structure (High‑Level)

```json
{
  "host": "...",
  "port": 443,
  "timestamp_utc": "...",
  "expiration": {
    "not_before": "...",
    "not_after": "...",
    "days_remaining": 0
  },
  "certificate": {
    "subject_cn": "...",
    "issuer_cn": "...",
    "serial_number": "...",
    "san": ["..."],
    "key": {
      "type": "rsa|ec",
      "bits": 2048,
      "curve": null
    },
    "signature_algorithm": "..."
  },
  "tls": {
    "version": "tls1.3",
    "cipher": "..."
  },
  "aia": {
    "issuer_urls": ["..."],
    "ocsp_urls": ["..."]
  },
  "ocsp": {
    "status": "unknown",
    "revocation_reason": null
  },
  "chain": {
    "validated": true,
    "warnings": []
  },
  "hostname_matches": true,
  "enforcement": {
    "passed": true,
    "failed": []
  },
  "warnings": [],
  "errors": []
}
```

## 18. Deterministic Behavior Guarantees

* No side effects
* Deterministic output
* Deterministic error handling
* Strict separation of modes

Chain warnings never affect Nagios output

## 19. Logging

check_cert includes a deterministic, operator‑grade logging system consistent with the 2026 NMS_Tools architecture.

Logging is enabled automatically when the tool runs and writes to the suite‑standard log directory defined in the unified NMS_Tools configuration file.

### 19.1 Logging Features

* Deterministic formatting  
* Timestamped entries in localtime  
* No external dependencies  
* No registry usage  
* No mutation of system state  
* No temporary files  
* No side effects outside the log directory  

### 19.2 Logged Events

* Hostname resolution attempts  
* Connection lifecycle  
* TLS negotiation details  
* Certificate parsing  
* Chain validation  
* Enforcement evaluation  
* Internal warnings and errors  

### 19.3 Log Rotation

Log rotation is handled by the shared NMS_Tools logging framework:

* Size‑based rotation  
* Deterministic naming  
* No compression  
* No deletion outside retention policy  

### 19.4 Viewing Logs

Logs are plain‑text and can be viewed directly using any standard text viewer:

```bash
cat /path/to/nms_tools/logs/check_cert.log
```

## 20. Version Information

```bash
check_cert --version
```

Outputs:

```Code
check_cert VERSION (NMS_Tools SUITE_VERSION)
```

Versioning follows semantic versioning with JSON schema stability guarantees.

## 21. Additional Examples

SMTP STARTTLS

```bash
check_cert -H mail.example.com -p 587 --starttls smtp
```

IMAP STARTTLS

```bash
check_cert -H mail.example.com -p 143 --starttls imap
```

LDAPS

```bash
check_cert -H ldap.example.com -p 636
```

IP‑Only Mode

```bash
check_cert -H 203.0.113.10 --ip-mode
```

No‑SNI

```bash
check_cert -H example.com --no-sni
```

Enforcement Example

```bash
check_cert -H example.com --min-tls tls1.3 --require-aead --min-rsa 2048
```

JSON Pipeline

```bash
check_cert -H example.com --json | jq '.expiration.days_remaining'
```

## 22. NMS_Tools Integration Notes

check_cert follows all NMS_Tools suite standards:

* Deterministic behavior
* Canonical JSON
* Clean Nagios output
* Fast‑fail hostname resolution
* Unified error model
* Consistent flag patterns
* No external dependencies
* No registry usage
* No environment mutation

All tools requiring -H must receive a resolvable hostname.
All tools follow the same UNKNOWN behavior on resolution failure.

---

## 23. See Also
* [Enforcement](Enforcement.md)
* [Installation](Installation.md)
* [Operations](Operation.md)
* [Roadmap](Roadmap.md)
* [Metadata_schema](Metadata_schema.md)
* [FLAGS.md](../../../docs/FLAGS.md)
