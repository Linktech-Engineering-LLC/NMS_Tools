# Enforcement Guide — `check_cert.py`

**Part of:** NMS_Tools Monitoring Suite  
**Document:** Enforcement Model  
**Author:** Leon McClatchey, Linktech Engineering LLC  
**License:** MIT  
**Requires:** Python 3.12+  (development only; not required for frozen binary)
**Last Updated:** 2026‑08‑17

## Table of Contents

1. [Overview](#1-overview)

2. [Enforcement Model](#2-enforcement-model)  
    1. [2.1 Monitoring Enforcement (Default‑On)](#21-monitoring-enforcement-default-on)  
    2. [2.2 Policy Enforcement (Explicit‑On)](#22-policy-enforcement-explicit-on)

3. [Enforcement Lifecycle](#3-enforcement-lifecycle)  
    1. [3.1 Determine Active Rules](#31-determine-active-rules)  
    2. [3.2 Evaluate Rules](#32-evaluate-rules)  
    3. [3.3 Aggregate Results](#33-aggregate-results)  
    4. [3.4 Compute Exit Code](#34-compute-exit-code)  
    5. [3.5 Render Output](#35-render-output)

4. [Enforcement Result Schema](#4-enforcement-result-schema)  
    1. [4.1 Field Meanings](#41-field-meanings)

5. [Monitoring Enforcement Rules](#5-monitoring-enforcement-rules)  
    1. [5.1 Expiration](#51-expiration)  
    2. [5.2 Hostname Match](#52-hostname-match)  
    3. [5.3 SAN Presence](#53-san-presence)  
    4. [5.4 Self‑Signed Detection](#54-self-signed-detection)  
    5. [5.5 Chain Validation](#55-chain-validation)  
    6. [5.6 OCSP Reachability](#56-ocsp-reachability)

6. [Policy Enforcement Rules](#6-policy-enforcement-rules)  
    1. [6.1 Certificate Rules](#61-certificate-rules)  
    2. [6.2 Key Rules](#62-key-rules)  
    3. [6.3 TLS Rules](#63-tls-rules)  
    4. [6.4 OCSP Rules](#64-ocsp-rules)

7. [Enforcement in Output Modes](#7-enforcement-in-output-modes)  
    1. [7.1 Nagios Mode](#71-nagios-mode)  
    2. [7.2 Verbose Mode](#72-verbose-mode)  
    3. [7.3 JSON Mode](#73-json-mode)

8. [Exit Code Behavior](#8-exit-code-behavior)

9. [Examples](#9-examples)  
    1. [9.1 Passing Enforcement](#91-passing-enforcement)  
    2. [9.2 Failing Enforcement](#92-failing-enforcement)  
    3. [9.3 OCSP Failure](#93-ocsp-failure)

10. [Future Enhancements](#10-future-enhancements)

---

## 1. Overview

This document defines the enforcement model used by `check_cert.py`: how rules are evaluated, how failures affect exit codes, and how enforcement results appear in Nagios, verbose, and JSON output modes.

Enforcement is **deterministic**, **unified**, and **policy‑driven**. It merges:

- **Monitoring enforcement** (enabled by default)
- **Policy enforcement** (enabled via CLI flags)

Both layers feed a single enforcement engine that produces a unified result used across all output modes.

---

## 2. Enforcement Model

`check_cert.py` evaluates two categories of rules:

### 2.1  Monitoring Enforcement (default‑on)

These rules validate core certificate and TLS properties:
* expiration  
* hostname match  
* SAN presence  
* self‑signed detection  
* chain validation  
* OCSP reachability (opt‑in via `--check-ocsp`)  

Monitoring rules can be individually disabled using:

--no-check-expiration
--no-check-chain
--no-check-hostname
--no-check-san
--no-check-self-signed

OCSP monitoring is **disabled by default** and enabled with:

--check-ocsp

### 2.2 Policy Enforcement (explicit‑on)

These rules validate certificate, key, TLS, and OCSP properties beyond basic monitoring:
* TLS version  
* cipher rules  
* key rules  
* issuer rules  
* wildcard rules  
* OCSP rules (`--require-ocsp`, `--forbid-ocsp`, `--ocsp-status`)  

Policy rules are enabled only when explicitly requested.

---

## 3. Enforcement Lifecycle

The enforcement engine follows a deterministic lifecycle.

### 3.1 Determine Active Rules

* Monitoring rules: enabled unless explicitly disabled  
* Policy rules: enabled only when flags are provided  

### 3.2 Evaluate Rules

Each rule is evaluated independently.  
Enforcement **never short‑circuits** — all rules run even if one fails.

### 3.3 Aggregate Results

Each rule contributes to:
* `applied`  
* `passed`  
* `failed`  
* `errors`  

Monitoring and policy results are merged into a unified enforcement object.

### 3.4 Compute Exit Code

* Any failed rule → **CRITICAL**  
* Any internal error → **CRITICAL**  
* Otherwise → expiration thresholds determine OK/WARNING/CRITICAL  

### 3.5 Render Output

* **Nagios:** single line, no diagnostics  
* **Verbose:** full “Enforcement Summary”  
* **JSON:** structured `enforcement` object  

---

## 4. Enforcement Result Schema

All enforcement results follow this canonical structure:

```json
{
  "applied": ["rule1", "rule2"],
  "passed": ["rule1"],
  "failed": ["rule2"],
  "errors": [],
  "state": 2
}
```

### 4.1 Field meanings

| Field |	Meaning |
| :--- | :--- |
| applied |	Rules that were evaluated |
| passed |	Rules that succeeded |
| failed |	Rules that failed (triggers CRITICAL) |
| errors |	Internal errors during evaluation |
| state |	Final enforcement state (0=OK, 2=CRITICAL) |

## 5. Monitoring Enforcement Rules (Default‑On)
These rules validate essential certificate and TLS properties.

### 5.1 Expiration

Controlled by:

```Code
-w DAYS
-c DAYS
```

Disable with:

```Code
--no-check-expiration
```

### 5.2 Hostname Match

Ensures CN/SAN matches the requested hostname.

Disable with:

```Code
--no-check-hostname
```

### 5.3 SAN Presence

Disable with:

```Code
--no-check-san
```

### 5.4 Self‑Signed Detection

Disable with:

```Code
--no-check-self-signed
```

### 5.5 Chain Validation

Disable with:

```Code
--no-check-chain
```

### 5.6 OCSP Reachability

Enabled with:

```Code
--check-ocsp
```

Behavior:

* Extract OCSP URLs
* Attempt HTTP reachability
* Fail if unreachable

This is a real network test, not a placeholder.

## 6. Policy Enforcement Rules

These rules validate certificate, key, TLS, and OCSP properties beyond monitoring.

### 6.1 Certificate Rules

```Code
--require-wildcard
--forbid-wildcard
-I ISSUER, --issuer ISSUER
-A SIGALG, --sigalg SIGALG
```

### 6.2 Key Rules

```Code
--min-rsa BITS
--require-curve CURVE
```

### 6.3 TLS Rules

```Code
--min-tls VERSION
--require-tls VERSION
--require-cipher CIPHER
--forbid-cipher CIPHER
--require-aead
--forbid-cbc
--forbid-rc4
```

### 6.4 OCSP Rules

```Code
--require-ocsp
--forbid-ocsp
--ocsp-status {good,revoked,unknown,invalid}
```

Behavior:

* --require-ocsp → certificate must contain OCSP URLs
* --forbid-ocsp → certificate must NOT contain OCSP URLs
* --ocsp-status → compare against reported status

Status values are currently:

* good
* revoked
* unknown
* invalid
* none (no OCSP URLs present)

## 7. Enforcement in Output Modes

### 7.1 Nagios Mode (Default)

If any rule fails:

```Code
CRITICAL - enforcement failure: <rule_name>;
```

Nagios mode:

* emits one line only
* suppresses diagnostics
* uses merged enforcement result

### 7.2 Verbose Mode (-v)

Example:

```Code
=== Enforcement Summary ===
Applied:
  - hostname_match
  - expiration
  - ocsp
Passed:
  - hostname_match
  - expiration
Failed:
  - ocsp (no OCSP responders reachable)
Errors:
  (none)
```

### 7.3 JSON Mode (--json / -j)

Example:

```json
"enforcement": {
  "applied": ["hostname_match", "expiration", "ocsp"],
  "passed": ["hostname_match", "expiration"],
  "failed": ["ocsp"],
  "errors": [],
  "state": 2
}
```

## 8. Exit Code Behavior

| Condition |	Exit Code |	Meaning |
| :--- | :---: | :--- |
| All rules pass |	0 |	OK |
| Any rule fails |	2 |	CRITICAL |
| Any rule errors |	2 |	CRITICAL |
| No rules applied |	Based on expiration thresholds |	OK/WARNING/CRITICAL |

Enforcement failures always override expiration thresholds.

## 9. Examples
### 9.1 Passing Enforcement

```bash
check_cert.py -H example.com --min-tls TLSv1.2 --require-aead
```

* Result:
* TLS 1.3 negotiated
* AEAD cipher used
* All rules pass

Nagios:

```Code
OK - certificate valid, expires in 60 days;
```

### 9.2 Failing Enforcement

```bash
check_cert.py -H legacy.example.com --min-tls TLSv1.2
```

Result:

* TLS 1.1 negotiated
* min-tls fails

Nagios:

```Code
CRITICAL - enforcement failure: min-tls;
```

Verbose:

```Code
Failed: min-tls (negotiated TLSv1.1 < required TLSv1.2)
```

### 9.3 OCSP Failure (Real Example)

```bash
check_cert.py -H www.linktechengineering.net --check-ocsp
```

Result:

* No OCSP URLs present
* Reachability = false
* ocsp rule fails

JSON:

* json
* "failed": ["ocsp"]

Nagios:

```Code
CRITICAL - enforcement failure: ocsp;
```

## 10. Future Enhancements

Planned enforcement extensions include:

* full OCSP response parsing
* certificate transparency (SCT) rules
* key usage and extended key usage rules
* chain reconstruction policies
* revocation checking
