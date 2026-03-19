# Usage Examples — `check_cert.py`

This document provides practical examples for real‑world usage of
`check_cert.py` in both system and monitoring environments.

---

## 1. Basic Checks

```bash
check_cert -H example.com
```

---

## 2. Verbose Output

```bash
check_cert -H example.com -v
```

---

## 3. JSON Output

```bash
check_cert -H example.com --json
```

---

## 4. Checking Non‑Standard Ports

```bash
check_cert -H mail.example.com -p 587 -S
```

---

## 5. Enforcing TLS Versions

Require TLS 1.3:

```bash
check_cert -H example.com --require-tls TLSv1.3
```

Minimum TLS 1.2:

```bash
check_cert -H example.com --min-tls TLSv1.2
```

---

## 6. Enforcing Ciphers

Require a specific cipher:

```bash
check_cert -H example.com --require-cipher TLS_AES_256_GCM_SHA384
```

Forbid CBC:

```bash
check_cert -H example.com --forbid-cbc
```

---

## 7. Key Requirements

Minimum RSA size:

```bash
check_cert -H example.com --min-rsa 2048
```

Require ECC curve:

```bash
check_cert -H example.com --require-curve secp256r1
```

---

## 8. OCSP Enforcement

Require OCSP reachability:

```bash
check_cert -H example.com --require-ocsp
```

Forbid OCSP:

```bash
check_cert -H example.com --forbid-ocsp
```

---

## 9. Wildcard Enforcement

Require wildcard:

```bash
check_cert -H example.com --require-wildcard
```

Forbid wildcard:

```bash
check_cert -H example.com --forbid-wildcard
```

---

## 10. Nagios Integration

### Command Definition

```
define command {
    command_name    check_cert
    command_line    /usr/lib/nagios/plugins/check_cert -H $HOSTADDRESS$ -w 30 -c 10
}
```

### Service Definition

```
define service {
    use                 generic-service
    host_name           myserver
    service_description TLS Certificate
    check_command       check_cert
}
```

---

## 11. Example Outputs

### Default

```
OK - 60 days remaining (2026-05-18 18:19:55 UTC) | days_remaining=60;30;15;0;
```

### Verbose

(Truncated for brevity)

```
Host: example.com
Port: 443
TLS Version: tlsv1.3
Cipher: TLS_AES_256_GCM_SHA384
Issuer CN: Example CA
...
```

### JSON

```json
{
  "subject_cn": "example.com",
  "issuer_cn": "Example CA",
  "sigalg": "sha256",
  "key_type": "ecdsa",
  "tls_version": "tlsv1.3",
  "cipher": "TLS_AES_256_GCM_SHA384",
  "ocsp_status": "reachable",
  "chain_ok": true,
  "expiration_days": 60,
  "warnings": [],
  "errors": []
}
```

---
