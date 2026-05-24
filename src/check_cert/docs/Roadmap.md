# Roadmap — `check_cert.py`

This document outlines planned enhancements, future capabilities, and long‑term improvements for the `check_cert` TLS inspection tool. Items are grouped by category and prioritized for clarity. The roadmap is forward‑looking and will evolve as the NMS_Tools suite grows.

---

# 🚀 Near‑Term Enhancements (v1.x Series)

These items refine existing functionality without changing the core architecture. They focus on metadata completeness, diagnostics, and incremental enforcement improvements.

## OCSP & Revocation

- Add OCSP stapling detection  
- Add OCSP stapling enforcement rule  
- Improve OCSP reachability diagnostics  
- Add OCSP response age metadata  
- Add OCSP responder timing metrics  

## Chain Handling

- Improve AIA chain reconstruction logic  
- Add chain depth metadata  
- Add chain signature algorithm metadata  
- Add chain expiration summary (min/max days remaining)  
- Add “chain source” metadata (server‑sent vs reconstructed)  

## Metadata Expansion

- Extract CRL Distribution Points  
- Extract Certificate Transparency SCTs  
- Extract Key Usage and Extended Key Usage  
- Add `is_ca` and `path_length` metadata for intermediate certificates  
- Add certificate fingerprint metadata (SHA‑256)  

## Output Improvements

- Expand JSON schema with optional extended fields  
- Add JSON schema versioning  
- Improve verbose mode grouping and alignment  
- Add optional colorized verbose output (disabled by default)  

---

# 🧭 Medium‑Term Enhancements (v2.x Series)

These items introduce new enforcement capabilities and deeper policy controls.

## Policy Enforcement

- Add TLS version policy profiles (modern, intermediate, legacy)  
- Add cipher suite policy profiles  
- Add key size policy profiles  
- Add issuer policy profiles  
- Add OCSP policy profiles (required, optional, ignore)  
- Add wildcard policy profiles  

## Chain Validation

- Full chain reconstruction using AIA + local trust store  
- Add trust store selection (system, custom, bundled)  
- Add chain validation enforcement (strict/lenient modes)  
- Add “trust anchor” metadata  

## Monitoring Enhancements

- Add “certificate age” monitoring (time since issuance)  
- Add “renewal window” monitoring (e.g., warn if > 90% lifetime elapsed)  
- Add “hostname wildcard mismatch” detection  
- Add “certificate reuse” detection across hosts  

---

# 🧱 Long‑Term Enhancements (v3.x Series)

These items expand the tool into a full TLS inspection engine.

## Advanced TLS Features

- Extract ALPN negotiation results  
- Extract supported signature algorithms  
- Extract supported cipher suites (client hello probing)  
- Add TLS handshake timing metrics  
- Add session resumption detection  

## Security & Hardening

- Add FIPS‑mode awareness  
- Add weak signature algorithm detection (MD5, SHA1, RSA<1024)  
- Add deprecated curve detection (secp192r1, secp224r1)  
- Add insecure renegotiation detection  

## Integration

- Add Prometheus exporter mode  
- Add syslog output mode  
- Add structured logging mode (JSONL)  
- Add plugin‑style architecture for custom enforcement rules  
- Add REST API wrapper for remote inspection  

---

# 🧩 Developer Experience & Architecture

## Code Quality

- Add full type‑checked stubs for metadata and enforcement  
- Add unit tests for metadata extraction  
- Add unit tests for enforcement logic  
- Add integration tests for real‑world certificates  
- Add deterministic test harness for TLS handshake simulation  

## Documentation

- Expand Metadata_Schema.md with extended fields  
- Add JSON schema reference  
- Add examples for each enforcement rule  
- Add troubleshooting guide  
- Add architecture diagram for enforcement engine  

---

# 🗂 Deferred / Research Items

These items require investigation before committing to implementation.

- Certificate pinning support  
- HPKP historical analysis  
- DNS‑based certificate validation (CAA, TLSA/DANE)  
- Multi‑certificate endpoint support (SNI enumeration)  
- QUIC/HTTP3 certificate inspection  
- OCSP multi‑responder fallback logic  
- Certificate chain caching for performance  

---

# 📌 Versioning Strategy

- **v1.x** — Stability, correctness, deterministic behavior  
- **v2.x** — Policy profiles, deeper enforcement, expanded metadata  
- **v3.x** — Advanced TLS features, integrations, extensibility  

---

# 🏁 Current Status

`check_cert` is currently in the stable **v1.x** phase, with a focus on:

- deterministic metadata extraction  
- unified enforcement engine  
- OCSP reachability enforcement  
- Nagios compatibility  
- JSON/verbose output consistency  
- deterministic logging  

Future enhancements will be added incrementally and tracked here.

