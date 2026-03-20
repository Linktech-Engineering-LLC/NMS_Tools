# Operation Guide — `check_cert.py`

This document explains how `check_cert.py` behaves at runtime, how to interpret
its output, and how to use its enforcement features.

---

## 1. Default Behavior

When run without `-v` or `--json`, the tool emits a **single Nagios‑style line**:

```
OK - 60 days remaining (2026-05-18 18:19:55 UTC);
```

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

Expiration thresholds and enforcement failures influence the exit code.
---

## 2. Detailed Output Modes

### Verbose Mode (`-v` / `--verbose`)

```bash
check_cert -H example.com -v
```

Displays:

- Connection details
- TLS version and cipher
- Certificate metadata
- SAN list
- Key information  
- AIA URLs and intermediate chain
- OCSP metadata
- Chain validation summary
- General warnings and errors
- Enforcement summary

Verbose mode is intended for operators and debugging

### JSON Mode (`--json` / `-j` )

```bash
check_cert -H example.com --json
```

Emits a deterministic JSON object suitable for:

- Certificate metadata
- Key metadata  
- SAN list
- TLS session details
- Expiration timestamp and days remaining
- OCSP metadata
- Chain metadata
- General warnings and errors
- Enforcement results

This mode is ideal for:
- Automation
- Log ingestion
- Programmatic inspection
- Monitoring pipelines

Verbose and JSON modes are **opt‑in**.

---

## 3. Exit Codes

| Code | Meaning |
|------|---------|
| 0 | OK |
| 1 | WARNING |
| 2 | CRITICAL |
| 3 | UNKNOWN |

---

## 4. Thresholds

### Expiration thresholds

```bash
-w DAYS   Warning threshold
-c DAYS   Critical threshold
```

Example:

```bash
check_cert -H example.com -w 30 -c 10
```
### Behavior:

days_remaining <= critical → CRITICAL

days_remaining <= warning → WARNING

otherwise → OK

Enforcement failures always produce CRITICAL.
---

## 5. Enforcement Features
Enforcement rules evaluate certificate, TLS, and OCSP properties.
Results appear in:

- JSON: enforcement.applied, passed, failed, errors

- Verbose: “Enforcement Summary” section

- Nagios: CRITICAL if any rule fails

### OCSP Enforcement

```
--require-ocsp
--forbid-ocsp
--ocsp-status {good,revoked,unknown,invalid}
```
#### Note:  
OCSP support is currently limited to:

Extracting OCSP URLs

Reporting presence/absence

Reporting placeholder status

Full OCSP reachability and response parsing are planned.

### Key Requirements

```
--min-rsa BITS
--require-curve CURVE
```

### TLS Requirements

```
--min-tls VERSION
--require-tls VERSION
--require-cipher CIPHER
--forbid-cipher CIPHER
--require-aead
--forbid-cbc
--forbid-rc4
```

### Certificate Requirements

```
--require-wildcard
--forbid-wildcard
-I, --issuer
-A, --sigalg
```

---

## 6. Troubleshooting

### “tls_handshake_failed”
- Port blocked  
- TLS version mismatch  
- SNI mismatch  

### “no_certificate_present”
- Host does not serve TLS on the given port  
- Missing `-p` for non‑443 services  

### OCSP unreachable
- Firewall blocking outbound HTTP  
- OCSP responder offline  

### Chain validation warnings
- Missing intermediates  
- Mismatched issuer/subject  
- Non‑standard chain structure  

---

## 7. Network Requirements

- Outbound TCP to target host
- Outbound HTTP for AIA retrieval 
- Outbound HTTP for OCSP (future retrieval)  

---
