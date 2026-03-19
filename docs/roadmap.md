# NMS_Tools Roadmap

This document tracks planned enhancements and future tools within the NMS_Tools suite.

---

## check_cert.py — Completed for v3

The following items are now implemented:

- Deterministic JSON schema  
- Verbose and Nagios output modes  
- TLS/cipher extraction  
- SAN, issuer, signature algorithm, and key metadata  
- AIA chain reconstruction  
- OCSP reachability detection  
- Expiration thresholds  
- Python‑3.6 compatibility  
- Stable CLI contract  

---

## check_cert.py — Planned Enhancements

### Chain & Trust Validation
- Chain status field (`ok`, `self_signed`, `missing_intermediate`, `issuer_unknown`)
- Intermediate expiration checks
- Root trust validation (system trust store or custom CA bundle)

### Hostname & SAN Enforcement
- Explicit hostname mismatch detection
- `--require-hostname-match` flag

### OCSP Enhancements
- OCSP response timestamp parsing (`thisUpdate`, `nextUpdate`)
- `--require-ocsp-good` enforcement

### Key & Algorithm Strength
- Minimum ECC curve strength enforcement
- Signature algorithm strength enforcement

### TLS & Cipher Policy
- `--require-tls13-only` convenience flag
- Pattern‑based cipher forbidding

### Metadata Extraction
- SCT extraction
- HSTS preload detection
- keyUsage / extendedKeyUsage extraction

### Operational / UX Improvements
- `--output <file>` for JSON logging
- `--quiet-json` compact mode
- `--perfdata-json` for Nagios perfdata
- Help text refinements
- Verbose output polishers

---

## Future Tools (Concept Stage)

- `check_tls.py` — TLS handshake policy enforcement  
- `check_ocsp.py` — OCSP responder health checks  
- `check_dnssec.py` — DNSSEC validation  
- `check_http.py` — HTTP status/latency/content checks  
- `check_renewal.py` — Certificate renewal pipeline validation  

---

## Notes

Additional items will be added as development continues.

