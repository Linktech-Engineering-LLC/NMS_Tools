# Enforcement Guide — check_cert.py
This document defines the enforcement model used by check_cert.py, how rules are
evaluated, how failures affect exit codes, and how enforcement results appear in
verbose and JSON output modes.

Enforcement is **optional**, **deterministic**, and **policy‑driven**.
When enabled, enforcement rules validate certificate, TLS, key, and OCSP
properties beyond simple expiration checks.

## 1. Enforcement Model
Enforcement is built on three core principles:

### 1. Deterministic Evaluation
All rules are evaluated in a fixed, predictable order:

1. Certificate rules
2. Key rules
3. TLS rules
4. OCSP rules

This ensures stable output for automation and monitoring systems.

### 2. Independent Rule Evaluation
Each rule is evaluated independently:

- A failure in one rule does not prevent evaluation of others.
- All results are collected and reported.
- Enforcement never short‑circuits.

### 3. Exit Code Integration
If any enforcement rule fails:

- Nagios mode returns CRITICAL (2)
- Verbose mode shows a detailed “Enforcement Summary”
- JSON mode includes structured enforcement results

Expiration thresholds still apply, but enforcement failures override them.

## 2. Enforcement Lifecycle
The enforcement engine follows a consistent lifecycle:

### 1. Rule Application  
Determine which rules are active based on CLI flags.

### 2. Rule Evaluation  
Each rule is evaluated against the collected certificate/TLS metadata.

### 3.Result Aggregation  
Results are merged into a unified EnforcementResult object containing:

- applied
- passed
- failed
- errors

### 4. Exit Code Decision

- If any rule fails → CRITICAL
- If all rules pass → OK (unless expiration thresholds trigger WARNING/CRITICAL)

### 5. Output Rendering

- Nagios: single‑line CRITICAL
- Verbose: full “Enforcement Summary”
- JSON: structured enforcement object

## 3. Enforcement Result Schema
All enforcement results follow a canonical structure:

json
{
  "applied": ["rule1", "rule2"],
  "passed": ["rule1"],
  "failed": ["rule2"],
  "errors": []
}

**Field meanings**

| **Field** |           **Meaning**                             |
|:----------|:--------------------------------------------------|
|applied	|Rules that were evaluated                          |
|passed	    |Rules that succeeded                               |
|failed 	|Rules that failed (triggers CRITICAL)              |
|errors 	|Internal errors during evaluation (also CRITICAL)  |

## 4. Rule Categories
Enforcement rules fall into four categories.

### 4.1 Certificate Rules
--require-wildcard
Certificate must contain a wildcard SAN entry.

--forbid-wildcard
Certificate must not contain any wildcard SAN entries.

-I, --issuer <ISSUER>
Issuer Common Name must match the provided string.

-A, --sigalg <ALGORITHM>
Signature algorithm must match the provided value
(e.g., sha256, sha384, ecdsa-with-SHA256).

### 4.2 Key Rules
--min-rsa <BITS>
RSA key must be at least the specified size.

--require-curve <CURVE>
ECDSA key must use the specified curve
(e.g., prime256v1, secp384r1).

### 4.3 TLS Rules
--min-tls <VERSION>
TLS session must negotiate at least the specified version
(e.g., tls1.2, tls1.3).

--require-tls <VERSION>
TLS session must negotiate exactly the specified version.

--require-cipher <CIPHER>
Cipher suite must match the provided name.

--forbid-cipher <CIPHER>
Cipher suite must not match the provided name.

--require-aead
Cipher must be AEAD (e.g., GCM, ChaCha20‑Poly1305).

--forbid-cbc
Cipher must not use CBC mode.

--forbid-rc4
Cipher must not use RC4.

### 4.4 OCSP Rules
--require-ocsp
Certificate must contain at least one OCSP responder URL.

--forbid-ocsp
Certificate must not contain any OCSP responder URLs.

--ocsp-status {good,revoked,unknown,invalid}
Placeholder rule that checks the reported OCSP status.

Note:  
OCSP support is currently limited to:

Extracting OCSP URLs

Reporting presence/absence

Reporting placeholder status

Full OCSP reachability and response parsing are planned.

## 5. Enforcement in Output Modes

### 5.1 Nagios Mode (default)
If any rule fails:

Code
CRITICAL - enforcement failure: <rule_name>;
Nagios mode:

Emits **one line only**

Suppresses all chain warnings and diagnostics

Includes no enforcement details beyond the fact of failure

### 5.2 Verbose Mode (-v)
Verbose mode includes a full “Enforcement Summary”:

Code
Enforcement Summary
-------------------
Applied: require-aead, min-tls
Passed:  require-aead
Failed:  min-tls (negotiated tls1.1 < required tls1.2)
Errors:  none

### 5.3 JSON Mode (--json)
JSON mode includes a structured enforcement object:

json
"enforcement": {
  "applied": ["min-tls", "require-aead"],
  "passed": ["require-aead"],
  "failed": ["min-tls"],
  "errors": []
}
This is ideal for:

- Log ingestion
- Monitoring pipelines
- Programmatic policy enforcement

## 6. Exit Code Behavior
|   **Condition**   | **Exit Code**	                  |    **Meaning**        |
|*------------------|*-------------------------------:|*----------------------|
|All rules pass	    |0	                              |OK                     |
|Any rule fails	    |2	                              |CRITICAL               |
|Any rule errors	|2	                              |CRITICAL               |
|No rules applied	|Depends on expiration thresholds |	OK/WARNING/CRITICAL   |

Enforcement failures always override expiration thresholds.

## 7. Examples
### 7.1 Passing Enforcement
Command:

Code
check_cert -H example.com --min-tls tls1.2 --require-aead
Result:

- TLS 1.3 negotiated
- AEAD cipher used
- All rules pass

Nagios:

Code
OK - 60 days remaining (2026-05-18 18:19:55 UTC);

### 7.2 Failing Enforcement
Command:

Code
check_cert -H legacy.example.com --min-tls tls1.2
Result:

TLS 1.1 negotiated

Rule fails

Nagios:

Code
CRITICAL - enforcement failure: min-tls;

Verbose:

Code
Failed: min-tls (negotiated tls1.1 < required tls1.2)

### 7.3 Mixed Results
Command:

Code
check_cert -H example.com --min-tls tls1.2 --forbid-cbc
Result:

TLS 1.3 negotiated (passes min-tls)

CBC cipher not used (passes forbid-cbc)

All rules pass → OK.

## 8. Future Enhancements
Planned enforcement extensions include:

Full OCSP reachability and response parsing

Chain reconstruction and path validation rules

Certificate transparency (SCT) rules

Key usage and extended key usage rules

Revocation checking