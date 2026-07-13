# Roadmap — `check_cert.py`

This roadmap outlines completed enhancements, planned improvements, and long‑term goals for the `check_cert` TLS inspection tool. It reflects the current architecture and future direction of the NMS_Tools suite.

The roadmap evolves as the tool grows.

---

## ✅ Completed Enhancements (v1.x Series)

These items are fully implemented and part of the stable JSON schema, verbose output, and enforcement engine.

### TLS Metadata
* Added TLS negotiation state (`tls_state`)
* Added TLS negotiation messages (`tls_messages`)
* Added TLS handshake state (`tls_handshake_state`)
* Added TLS handshake message (`tls_handshake_message`)

### Certificate Metadata
* Added signature algorithm strength classification
  (`signature_algorithm_state`, `signature_algorithm_message`)
* Added hostname match metadata (`hostname_matches`)
* Added warning/critical threshold metadata (`warning_days`, `critical_days`)

### Key Metadata
* Added key strength classification
  (`key_state`, `key_message`)

### AIA Chain Metadata
* Added per‑certificate chain metadata:
    * `subject_cn`
    * `issuer_cn`
    * `signature_algorithm`
    * `key_type`
    * `ocsp_urls`

### OCSP Metadata
* Added OCSP status (`status`)
* Added OCSP reachability (`reachable`)

### Chain Metadata
* Added chain state (`chain_state`)
* Added chain message (`chain_message`)
* Added chain completeness warning enforcement rule
  (`chain_completeness_warning`)

### Enforcement Engine
* Updated enforcement block to include new metadata fields
* Added chain completeness warning rule
* Updated JSON schema to include expanded metadata

---

# 🚀 Near‑Term Enhancements (v1.x Series)

These items refine existing functionality without changing the core architecture. They focus on metadata completeness, diagnostics, and incremental enforcement improvements.

## OCSP & Revocation

* Add OCSP stapling detection  
* Add OCSP stapling enforcement rule  
* Improve OCSP reachability diagnostics  
* Add OCSP response age metadata  
* Add OCSP responder timing metrics  

## Chain Handling

* Improve AIA chain reconstruction logic  
* Add chain depth metadata  
* Add chain signature algorithm metadata  
* Add chain expiration summary (min/max days remaining)  
* Add “chain source” metadata (server‑sent vs reconstructed)  

## Metadata Expansion

* Extract CRL Distribution Points  
* Extract Certificate Transparency SCTs  
* Extract Key Usage and Extended Key Usage  
* Add `is_ca` and `path_length` metadata for intermediate certificates  
* Add certificate fingerprint metadata (SHA‑256)  

## Output Improvements

* Add JSON schema versioning
* Expand JSON schema with optional extended fields (CRL, SCT, EKU, etc.)
* Improve verbose mode grouping and alignment
* Add optional colorized verbose output (disabled by default)

---

# 🧭 Medium‑Term Enhancements (v2.x Series)

New enforcement capabilities, deeper policy controls, and expanded validation logic.

## Policy Enforcement

* Add TLS version policy profiles (modern, intermediate, legacy)  
* Add cipher suite policy profiles  
* Add key size policy profiles  
* Add issuer policy profiles  
* Add OCSP policy profiles (required, optional, ignore)  
* Add wildcard policy profiles  

## Chain Validation

* Full chain reconstruction using AIA + local trust store  
* Add trust store selection (system, custom, bundled)  
* Add chain validation enforcement (strict/lenient modes)  
* Add “trust anchor” metadata  

## Monitoring Enhancements

* Add “certificate age” monitoring (time since issuance)  
* Add “renewal window” monitoring (e.g., warn if > 90% lifetime elapsed)  
* Add “hostname wildcard mismatch” detection  
* Add “certificate reuse” detection across hosts  

---

# 🧱 Long‑Term Enhancements (v3.x Series)

Advanced TLS inspection capabilities and broader integration options.

## Advanced TLS Features

* Extract ALPN negotiation results  
* Extract supported signature algorithms  
* Extract supported cipher suites (client hello probing)  
* Add TLS handshake timing metrics  
* Add session resumption detection  

## Security & Hardening

* Add FIPS‑mode awareness  
* Add weak signature algorithm detection (MD5, SHA1, RSA<1024)  
* Add deprecated curve detection (secp192r1, secp224r1)  
* Add insecure renegotiation detection  

## Integration

* Add Prometheus exporter mode  
* Add syslog output mode  
* Add structured logging mode (JSONL)  
* Add plugin‑style architecture for custom enforcement rules  
* Add REST API wrapper for remote inspection  

---

# 🧩 Developer Experience & Architecture

## Code Quality

* Add full type‑checked stubs for metadata and enforcement  
* Add unit tests for metadata extraction  
* Add unit tests for enforcement logic  
* Add integration tests for real‑world certificates  
* Add deterministic test harness for TLS handshake simulation  

## Documentation

* Expand Metadata_Schema.md with extended fields  
* Add JSON schema reference  
* Add examples for each enforcement rule  
* Add troubleshooting guide  
* Add architecture diagram for enforcement engine  

---

# 🗂 Deferred / Research Items

These items require investigation before committing to implementation.

* Certificate pinning support  
* HPKP historical analysis  
* DNS‑based certificate validation (CAA, TLSA/DANE)  
* Multi‑certificate endpoint support (SNI enumeration)  
* QUIC/HTTP3 certificate inspection  
* OCSP multi‑responder fallback logic  
* Certificate chain caching for performance  

---

# 📌 Versioning Strategy

* **v1.x** — Stability, correctness, deterministic behavior  
* **v2.x** — Policy profiles, deeper enforcement, expanded metadata  
* **v3.x** — Advanced TLS features, integrations, extensibility  

---

# 🏁 Current Status

`check_cert` is currently in the stable **v1.x** phase, with a focus on:

* deterministic metadata extraction
* unified enforcement engine
* expanded JSON schema
* OCSP reachability enforcement
* chain completeness warning
* Nagios compatibility
* JSON/verbose output consistency
* deterministic logging

Future enhancements will be added incrementally and tracked here.
