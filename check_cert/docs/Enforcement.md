# Enforcement Guide — `check_cert.py`

This document defines the enforcement model used by `check_cert.py`: how rules are evaluated, how failures affect exit codes, and how enforcement results appear in Nagios, verbose, and JSON output modes.

Enforcement is **deterministic**, **unified**, and **policy‑driven**. It merges:

- **Monitoring enforcement** (enabled by default)
- **Policy enforcement** (enabled via CLI flags)

Both layers feed a single enforcement engine that produces a unified result used across all output modes.

---

## 1. Enforcement Model

`check_cert.py` evaluates two categories of rules:

### **1. Monitoring Enforcement (default‑on)**  
These rules validate core certificate and TLS properties:

- expiration  
- hostname match  
- SAN presence  
- self‑signed detection  
- chain validation  
- OCSP reachability (opt‑in via `--check-ocsp`)  

Monitoring rules can be individually disabled using:

--no-check-expiration
--no-check-chain
--no-check-hostname
--no-check-san
--no-check-self-signed

Code

OCSP monitoring is **disabled by default** and enabled with:

--check-ocsp

Code

### **2. Policy Enforcement (explicit‑on)**  
These rules validate certificate, key, TLS, and OCSP properties beyond basic monitoring:

- TLS version  
- cipher rules  
- key rules  
- issuer rules  
- wildcard rules  
- OCSP rules (`--require-ocsp`, `--forbid-ocsp`, `--ocsp-status`)  

Policy rules are enabled only when explicitly requested.

---

## 2. Enforcement Lifecycle

The enforcement engine follows a deterministic lifecycle.

### **2.1 Determine Active Rules**

- Monitoring rules: enabled unless explicitly disabled  
- Policy rules: enabled only when flags are provided  

### **2.2 Evaluate Rules**

Each rule is evaluated independently.  
Enforcement **never short‑circuits** — all rules run even if one fails.

### **2.3 Aggregate Results**

Each rule contributes to:

- `applied`  
- `passed`  
- `failed`  
- `errors`  

Monitoring and policy results are merged into a unified enforcement object.

### **2.4 Compute Exit Code**

- Any failed rule → **CRITICAL**  
- Any internal error → **CRITICAL**  
- Otherwise → expiration thresholds determine OK/WARNING/CRITICAL  

### **2.5 Render Output**

- **Nagios:** single line, no diagnostics  
- **Verbose:** full “Enforcement Summary”  
- **JSON:** structured `enforcement` object  

---

## 3. Enforcement Result Schema

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

**Field meanings**

| Field |	Meaning |
| :--- | :--- |
| applied |	Rules that were evaluated |
| passed |	Rules that succeeded |
| failed |	Rules that failed (triggers CRITICAL) |
| errors |	Internal errors during evaluation |
| state |	Final enforcement state (0=OK, 2=CRITICAL) |

## 4. Monitoring Enforcement Rules (Default‑On)
These rules validate essential certificate and TLS properties.

### 4.1 Expiration

Controlled by:

```Code
-w DAYS
-c DAYS
```

Disable with:

```Code
--no-check-expiration
```

### 4.2 Hostname Match

Ensures CN/SAN matches the requested hostname.

Disable with:

```Code
--no-check-hostname
```

### 4.3 SAN Presence

Disable with:

```Code
--no-check-san
```

### 4.4 Self‑Signed Detection

Disable with:

```Code
--no-check-self-signed
```

### 4.5 Chain Validation

Disable with:

```Code
--no-check-chain
```

### 4.6 OCSP Reachability

Enabled with:

```Code
--check-ocsp
```

Behavior:

* Extract OCSP URLs
* Attempt HTTP reachability
* Fail if unreachable

This is a real network test, not a placeholder.

## 5. Policy Enforcement Rules (Explicit‑On)

These rules validate certificate, key, TLS, and OCSP properties beyond monitoring.

### 5.1 Certificate Rules

```Code
--require-wildcard
--forbid-wildcard
-I ISSUER, --issuer ISSUER
-A SIGALG, --sigalg SIGALG
```

### 5.2 Key Rules

```Code
--min-rsa BITS
--require-curve CURVE
```

### 5.3 TLS Rules

```Code
--min-tls VERSION
--require-tls VERSION
--require-cipher CIPHER
--forbid-cipher CIPHER
--require-aead
--forbid-cbc
--forbid-rc4
```

### 5.4 OCSP Rules

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

## 6. Enforcement in Output Modes

### 6.1 Nagios Mode (Default)

If any rule fails:

```Code
CRITICAL - enforcement failure: <rule_name>;
```

Nagios mode:

* emits one line only
* suppresses diagnostics
* uses merged enforcement result

### 6.2 Verbose Mode (-v)

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

### 6.3 JSON Mode (--json / -j)

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

## 7. Exit Code Behavior

| Condition |	Exit Code |	Meaning |
| :--- | :---: | :--- |
| All rules pass |	0 |	OK |
| Any rule fails |	2 |	CRITICAL |
| Any rule errors |	2 |	CRITICAL |
| No rules applied |	Based on expiration thresholds |	OK/WARNING/CRITICAL |

Enforcement failures always override expiration thresholds.

## 8. Examples
### 8.1 Passing Enforcement

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

### 8.2 Failing Enforcement

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

### 8.3 OCSP Failure (Real Example)

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

## 9. Future Enhancements

Planned enforcement extensions include:

* full OCSP response parsing
* certificate transparency (SCT) rules
* key usage and extended key usage rules
* chain reconstruction policies
* revocation checking
