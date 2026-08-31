# Roadmap — `check_cert.py`

**Part of:** NMS_Tools Monitoring Suite  
**Document:** Roadmap  
**Author:** Leon McClatchey, Linktech Engineering LLC  
**License:** MIT  
**Last Updated:** 2026‑08‑17

## Table of Contents

1. [Overview](#1-overview)
2. [Completed Enhancements (v1.x Series)](#2-completed-enhancements-v1x-series)  
    1. [2.1 TLS Metadata](#21-tls-metadata)  
    2. [2.2 Certificate Metadata](#22-certificate-metadata)  
    3. [2.3 Key Metadata](#23-key-metadata)  
    4. [2.4 AIA Chain Metadata](#24-aia-chain-metadata)  
    5. [2.5 OCSP Metadata](#25-ocsp-metadata)  
    6. [2.6 Chain Metadata](#26-chain-metadata)  
    7. [2.7 Enforcement Engine](#27-enforcement-engine)
3. [Near‑Term Enhancements (v1.x Series)](#3-near-term-enhancements-v1x-series)  
    1. [3.1 OCSP & Revocation](#31-ocsp--revocation)  
    2. [3.2 Chain Handling](#32-chain-handling)  
    3. [3.3 Metadata Expansion](#33-metadata-expansion)  
    4. [3.4 Output Improvements](#34-output-improvements)
4. [Medium‑Term Enhancements (v2.x Series)](#4-medium-term-enhancements-v2x-series)  
    1. [4.1 Policy Enforcement](#41-policy-enforcement)  
    2. [4.2 Chain Validation](#42-chain-validation)  
    3. [4.3 Monitoring Enhancements](#43-monitoring-enhancements)
5. [Long‑Term Enhancements (v3.x Series)](#5-long-term-enhancements-v3x-series)  
    1. [5.1 Advanced TLS Features](#51-advanced-tls-features)  
    2. [5.2 Security & Hardening](#52-security--hardening)  
    3. [5.3 Integration](#53-integration)
6. [Developer Experience & Architecture](#6-developer-experience--architecture)  
    1. [6.1 Code Quality](#61-code-quality)  
    2. [6.2 Documentation](#62-documentation)
7. [Deferred / Research Items](#7-deferred--research-items)
8. [Versioning Strategy](#8-versioning-strategy)
9. [Current Status](#9-current-status)

---

## 1. Overview

This roadmap outlines completed enhancements, planned improvements, and long‑term goals for the `check_cert` TLS inspection tool. It reflects the current architecture and future direction of the NMS_Tools suite.

The roadmap evolves as the tool grows.

---

## 2. ✅ Completed Enhancements (v1.x Series)

These items are fully implemented and part of the stable JSON schema, verbose output, and enforcement engine.

### 2.1 TLS Metadata
* Added TLS negotiation state (`tls_state`)
* Added TLS negotiation messages (`tls_messages`)
* Added TLS handshake state (`tls_handshake_state`)
* Added TLS handshake message (`tls_handshake_message`)

### 2.2 Certificate Metadata
* Added signature algorithm strength classification
  (`signature_algorithm_state`, `signature_algorithm_message`)
* Added hostname match metadata (`hostname_matches`)
* Added warning/critical threshold metadata (`warning_days`, `critical_days`)

### 2.3 Key Metadata
* Added key strength classification
  (`key_state`, `key_message`)

### 2.4 AIA Chain Metadata
* Added per‑certificate chain metadata:
    * `subject_cn`
    * `issuer_cn`
    * `signature_algorithm`
    * `key_type`
    * `ocsp_urls`

### 2.5 OCSP Metadata
* Added OCSP status (`status`)
* Added OCSP reachability (`reachable`)

### 2.6 Chain Metadata
* Added chain state (`chain_state`)
* Added chain message (`chain_message`)
* Added chain completeness warning enforcement rule
  (`chain_completeness_warning`)

### 2.7 Enforcement Engine
* Updated enforcement block to include new metadata fields
* Added chain completeness warning rule
* Updated JSON schema to include expanded metadata

---

## 3🚀 Near‑Term Enhancements (v1.x Series)

These items refine existing functionality without changing the core architecture. They focus on metadata completeness, diagnostics, and incremental enforcement improvements.

### 3.1 OCSP & Revocation

* Add OCSP stapling detection  
* Add OCSP stapling enforcement rule  
* Improve OCSP reachability diagnostics  
* Add OCSP response age metadata  
* Add OCSP responder timing metrics  

### 3.2 Chain Handling

* Improve AIA chain reconstruction logic  
* Add chain depth metadata  
* Add chain signature algorithm metadata  
* Add chain expiration summary (min/max days remaining)  
* Add “chain source” metadata (server‑sent vs reconstructed)  

### 3.3 Metadata Expansion

* Extract CRL Distribution Points  
* Extract Certificate Transparency SCTs  
* Extract Key Usage and Extended Key Usage  
* Add `is_ca` and `path_length` metadata for intermediate certificates  
* Add certificate fingerprint metadata (SHA‑256)  

### 3.4 Output Improvements

* Add JSON schema versioning
* Expand JSON schema with optional extended fields (CRL, SCT, EKU, etc.)
* Improve verbose mode grouping and alignment
* Add optional colorized verbose output (disabled by default)

---

## 4. 🧭 Medium‑Term Enhancements (v2.x Series)

New enforcement capabilities, deeper policy controls, and expanded validation logic.

### 4.1 Policy Enforcement

* Add TLS version policy profiles (modern, intermediate, legacy)  
* Add cipher suite policy profiles  
* Add key size policy profiles  
* Add issuer policy profiles  
* Add OCSP policy profiles (required, optional, ignore)  
* Add wildcard policy profiles  

### 4.2 Chain Validation

* Full chain reconstruction using AIA + local trust store  
* Add trust store selection (system, custom, bundled)  
* Add chain validation enforcement (strict/lenient modes)  
* Add “trust anchor” metadata  

### 4.3 Monitoring Enhancements

* Add “certificate age” monitoring (time since issuance)  
* Add “renewal window” monitoring (e.g., warn if > 90% lifetime elapsed)  
* Add “hostname wildcard mismatch” detection  
* Add “certificate reuse” detection across hosts  

---

## 5. 🧱 Long‑Term Enhancements (v3.x Series)

Advanced TLS inspection capabilities and broader integration options.

### 5.1 Advanced TLS Features

* Extract ALPN negotiation results  
* Extract supported signature algorithms  
* Extract supported cipher suites (client hello probing)  
* Add TLS handshake timing metrics  
* Add session resumption detection  

### 5.2 Security & Hardening

* Add FIPS‑mode awareness  
* Add weak signature algorithm detection (MD5, SHA1, RSA<1024)  
* Add deprecated curve detection (secp192r1, secp224r1)  
* Add insecure renegotiation detection  

### 5.3 Integration

* Add Prometheus exporter mode  
* Add syslog output mode  
* Add structured logging mode (JSONL)  
* Add plugin‑style architecture for custom enforcement rules  
* Add REST API wrapper for remote inspection  

---

## 6. 🧩 Developer Experience & Architecture

### 6.1 Code Quality

* Add full type‑checked stubs for metadata and enforcement  
* Add unit tests for metadata extraction  
* Add unit tests for enforcement logic  
* Add integration tests for real‑world certificates  
* Add deterministic test harness for TLS handshake simulation  

### 6.2 Documentation

* Expand Metadata_Schema.md with extended fields  
* Add JSON schema reference  
* Add examples for each enforcement rule  
* Add troubleshooting guide  
* Add architecture diagram for enforcement engine  

---

## 7. 🗂 Deferred / Research Items

These items require investigation before committing to implementation.

* Certificate pinning support  
* HPKP historical analysis  
* DNS‑based certificate validation (CAA, TLSA/DANE)  
* Multi‑certificate endpoint support (SNI enumeration)  
* QUIC/HTTP3 certificate inspection  
* OCSP multi‑responder fallback logic  
* Certificate chain caching for performance  

---

## 8. 📌 Versioning Strategy

* **v1.x** — Stability, correctness, deterministic behavior  
* **v2.x** — Policy profiles, deeper enforcement, expanded metadata  
* **v3.x** — Advanced TLS features, integrations, extensibility  

---

## 9. 🏁 Current Status

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
