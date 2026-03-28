# Logging — check_cert.py (Stabilized Architecture)

The logging subsystem in check_cert.py provides deterministic, operator‑grade log entries suitable for:

- Monitoring systems
- SIEM ingestion
- Troubleshooting
- Audit trails

Logging is mode‑independent: every run produces the same structured banners regardless of Nagios, verbose, or JSON output. Logs are written only when --log-dir is provided.

---

## 1. Log File Naming

Log files are written to the directory specified by:

    --log-dir /path/to/logs

Each run appends to a file named:

    check_cert-YYYYMMDD.log

A new file is created each day.

---

## 2. Log Entry Format

Each log entry is a single line:

    YYYY-MM-DD HH:MM:SS; [BANNER] key=value key=value ...

This format is deterministic, grep‑friendly, and SIEM‑friendly.

---

## 3. Log Banners

check_cert uses four canonical banners, always in this order:

1. [START]
2. [CERT]
3. [RESULT]
4. [END]

---

## 4. START Banner

Records:

- Script name
- Host / port / SNI
- Timeout
- Insecure flag
- Warning / critical thresholds
- Output mode

Example:

    2026-03-28 12:19:11; [START] check_cert host=example.com port=443 sni=example.com timeout=5 insecure=false warning_days=30 critical_days=15 mode=json

---

## 5. CERT Banner

Records all extracted metadata:

- TLS session
- Certificate metadata
- Key metadata
- SAN count
- OCSP metadata
- Chain metadata

Example:

    2026-03-28 12:19:11; [CERT] host=example.com tls_version=TLSv1.3 cipher=TLS_AES_256_GCM_SHA384 subject_cn=example.com issuer_cn=ZeroSSL signature_algorithm=sha384 wildcard=false self_signed=false hostname_matches=true san_count=1 expires=2026-06-13 expiration_days=77 key_type=ecdsa rsa_bits=null ecc_curve=secp256r1 ocsp_urls=0 ocsp_status=none chain_server_sent=false chain_reconstructed=true chain_valid=true chain_errors=0

All fields are flattened into key=value pairs for SIEM compatibility.

---

## 6. RESULT Banner

Records:

- Nagios state
- Number of failed rules
- List of failed rules

Example:

    2026-03-28 12:19:11; [RESULT] state=0 failed=0 failures=[]

---

## 7. END Banner

Marks completion.

Example:

    2026-03-28 12:19:11; [END]

---

## 8. Logging Behavior Summary

- Append‑only
- Deterministic
- Mode‑independent
- Aligned with JSON and verbose output
- Uses canonical banners

---

## 9. Example Full Log Sequence

    2026-03-28 12:19:11; [START] check_cert host=example.com port=443 sni=example.com timeout=5 insecure=false warning_days=30 critical_days=15 mode=json
    2026-03-28 12:19:11; [CERT] host=example.com tls_version=TLSv1.3 cipher=TLS_AES_256_GCM_SHA384 subject_cn=example.com issuer_cn=ZeroSSL signature_algorithm=sha384 wildcard=false self_signed=false hostname_matches=true san_count=1 expires=2026-06-13 expiration_days=77 key_type=ecdsa rsa_bits=null ecc_curve=secp256r1 ocsp_urls=0 ocsp_status=none chain_server_sent=false chain_reconstructed=true chain_valid=true chain_errors=0
    2026-03-28 12:19:11; [RESULT] state=0 failed=0 failures=[]
    2026-03-28 12:19:11; [END]

---

## 10. Alignment With JSON and Enforcement

Every CERT field corresponds directly to a JSON field:

- tls → tls
- certificate → certificate
- key → key
- aia → aia
- ocsp → ocsp
- chain → chain

The RESULT banner corresponds to the JSON enforcement block.

