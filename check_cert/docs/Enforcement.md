# Enforcement Guide — `check_cert.py`

This document defines the enforcement model used by `check_cert.py`: how rules are evaluated, how failures affect exit codes, and how enforcement results appear in Nagios, verbose, and JSON output modes.

Enforcement is **deterministic**, **unified**, and **policy‑driven**. It combines **monitoring enforcement** (enabled by default) and **policy enforcement** (enabled via CLI flags).

---

## 1. Enforcement Model

`check_cert.py` uses a unified enforcement engine that merges:

- **Monitoring enforcement:**
  - expiration
  - hostname
  - SAN
  - self‑signed
  - chain
  - OCSP
- **Policy enforcement:**
  - TLS version
  - cipher rules
  - key rules
  - issuer rules
  - OCSP rules

Both layers produce an `enforcement` structure that is merged into a single deterministic result used by:

- Nagios mode  
- verbose mode  
- JSON mode  

This guarantees consistent behavior across all output modes.

---

## 2. Enforcement Lifecycle

The enforcement engine follows a fixed lifecycle.

### 2.1 Determine Active Rules

**Monitoring rules** are enabled by default.  
**Policy rules** are enabled only when explicitly requested via CLI flags.

Monitoring rules can be disabled individually:

```Code
--no-check-san
--no-check-self-signed
--no-check-chain
--no-check-ocsp
```


### 2.2 Evaluate Rules

Each rule is evaluated independently against the collected metadata.  
A failure in one rule does not prevent evaluation of others; enforcement never short‑circuits.

### 2.3 Aggregate Results

Each layer (monitoring and policy) produces:

- `applied`
- `passed`
- `failed`
- `errors`

These are merged into a unified enforcement result.

### 2.4 Compute Exit Code

- Any failed rule → **CRITICAL**
- Any internal error → **CRITICAL**
- Otherwise → expiration thresholds determine OK/WARNING/CRITICAL

### 2.5 Render Output

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
  "errors": []
}
```

Field meanings

| Field |	Meaning |
| :--- | :--- | 
| applied | Rules that were evaluated |
| passed | Rules that succeeded |
| failed | Rules that failed (triggers CRITICAL) |
| errors | Internal errors during evaluation (also CRITICAL) |

This schema is identical for monitoring, policy, and merged enforcement.

## 4. Monitoring Enforcement Rules (Enabled by Default)

These rules validate core certificate and TLS properties required for safe operation.

### 4.1 Expiration

Controlled by:

```
-w DAYS
-c DAYS
```

### 4.2 Hostname Match
Ensures the certificate matches the requested hostname (CN/SAN).

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

### 4.5 Chain Presence

Disable with:

```Code
--no-check-chain
```

### 4.6 OCSP Presence

Disable with:

```Code
--no-check-ocsp
```

## 5. Policy Enforcement Rules (Explicitly Enabled)
These rules validate certificate, key, TLS, and OCSP properties beyond basic monitoring.

### 5.1 Certificate Rules

--require-wildcard  
Certificate must contain at least one wildcard SAN entry.

--forbid-wildcard  
Certificate must not contain any wildcard SAN entries.

-I, --issuer <ISSUER>  
Issuer Common Name must match the provided string.

-A, --sigalg <ALGORITHM>  
Signature algorithm must match the provided value.

### 5.2 Key Rules

--min-rsa <BITS>  
RSA key must be at least the specified size.

--require-curve <CURVE>  
ECDSA key must use the specified curve.

### 5.3 TLS Rules

--min-tls <VERSION>  
Negotiated TLS version must be at least the specified version.

--require-tls <VERSION>  
Negotiated TLS version must match exactly.

--require-cipher <CIPHER>  
Cipher suite must match the provided name.

--forbid-cipher <CIPHER>  
Cipher suite must not match the provided name.

--require-aead  
Cipher must be AEAD.

--forbid-cbc  
Cipher must not use CBC mode.

--forbid-rc4  
Cipher must not use RC4.

### 5.4 OCSP Rules

--require-ocsp  
Certificate must contain at least one OCSP responder URL.

--forbid-ocsp  
Certificate must not contain any OCSP responder URLs.

--ocsp-status {good,revoked,unknown,invalid}  
Checks the reported OCSP status (placeholder behavior).

**Note:**

Current OCSP support includes:

* extracting OCSP URLs
* reporting presence/absence
* reporting placeholder status

Full OCSP reachability and response parsing are planned.

## 6. Enforcement in Output Modes

### 6.1 Nagios Mode (Default)

If any rule fails:

```Code
CRITICAL - enforcement failure: <rule_name>;
```

Nagios mode:

* emits one line only
* suppresses chain and diagnostic details
* does not show enforcement internals
* uses the merged enforcement result

## 6.2 Verbose Mode (-v)

Verbose mode includes a full “Enforcement Summary”:

```Code
=== Enforcement Summary ===
Applied:
  - hostname_match
  - expiration
Passed:
  - hostname_match
  - expiration
Failed:
  (none)
Errors:
  (none)
```

When rules fail, the failed list includes human‑readable reasons.

## 6.3 JSON Mode (--json / -j)
JSON mode includes a structured enforcement object:

```json
"enforcement": {
  "applied": ["hostname_match", "expiration"],
  "passed": ["hostname_match", "expiration"],
  "failed": [],
  "errors": []
}
```

This is suitable for:

* log ingestion
* monitoring pipelines
* dashboards
* programmatic policy enforcement

## 7. Exit Code Behavior

| Condition | Exit Code |	Meaning |
| :--- | :---: | :--- |
| All rules pass | 0 | OK |
| Any rule fails | 2 | CRITICAL |
| Any rule errors | 2 |	CRITICAL |
| No rules applied | Based on expiration thresholds | OK/WARNING/CRITICAL |

Enforcement failures always override expiration thresholds.

## 8. Examples

### 8.1 Passing Enforcement

**Command:**

```Code
check_cert -H example.com --min-tls tls1.2 --require-aead
```

**Result:**

* TLS 1.3 negotiated
* AEAD cipher used
* All rules pass

**Nagios:**

```Code
OK - certificate valid, expires in 60 days on 2026-05-18;
```

## 8.2 Failing Enforcement

**Command:**

```Code
check_cert -H legacy.example.com --min-tls tls1.2
```

**Result:**

* TLS 1.1 negotiated
* min-tls rule fails

**Nagios:**

```Code
CRITICAL - enforcement failure: min-tls;
```

**Verbose:**

```Code
Failed: min-tls (negotiated tls1.1 < required tls1.2)
```

### 8.3 Mixed Results (All Passing)

**Command:**

```Code
check_cert -H example.com --min-tls tls1.2 --forbid-cbc
```

**Result:**

* TLS 1.3 negotiated
* Non‑CBC cipher used
* All rules pass → OK

## 9. Future Enhancements

Planned enforcement extensions include:

* full OCSP reachability and response parsing
* chain reconstruction and path validation rules
* Certificate Transparency (SCT) rules
* key usage and extended key usage rules
* revocation checking