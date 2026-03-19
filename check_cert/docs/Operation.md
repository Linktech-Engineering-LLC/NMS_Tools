# Operation Guide — `check_cert.py`

This document explains how `check_cert.py` behaves at runtime, how to interpret
its output, and how to use its enforcement features.

---

## 1. Default Behavior

When run without `-v` or `--json`, the tool emits a **single Nagios‑style line**:

```
OK - 60 days remaining (2026-05-18 18:19:55 UTC) | days_remaining=60;30;15;0;
```

This is intentional and designed for:

- Monitoring systems  
- Cron jobs  
- Shell scripts  
- Automated pipelines  

---

## 2. Detailed Output Modes

### Verbose Mode (`-v`)

```bash
check_cert -H example.com -v
```

Displays:

- TLS version and cipher  
- Certificate metadata  
- SAN list  
- AIA URLs  
- Parsed intermediate certificates  
- Key information  
- Expiration timestamp  

### JSON Mode (`--json`)

```bash
check_cert -H example.com --json
```

Emits a deterministic JSON object suitable for:

- Automation  
- Log ingestion  
- Pipelines  
- Programmatic inspection  

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

---

## 5. Enforcement Features

### OCSP

```
--require-ocsp
--forbid-ocsp
--ocsp-status {good,revoked,unknown,invalid}
```

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
- Outbound HTTP for OCSP and AIA retrieval  

---
