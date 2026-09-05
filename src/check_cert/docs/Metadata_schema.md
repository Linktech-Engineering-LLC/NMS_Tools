# Metadata Schema — check_cert.py

**Part of:** NMS_Tools Monitoring Suite  
**Document:** Metadata Schema  
**Author:** Leon McClatchey, Linktech Engineering LLC  
**License:** MIT  
**Requires:** Python 3.12+  (development only; not required for frozen binary)
**Last Updated:** 2026‑08‑17

## Table of Contents

1. [Overview](#1-overview)
2. [Top‑Level Structure](#2-top-level-structure)
3. [Host & Connection Metadata](#3-host--connection-metadata)
4. [TLS Session Metadata](#4-tls-session-metadata)
5. [Certificate Metadata](#5-certificate-metadata)
6. [Key Metadata](#6-key-metadata)
7. [AIA Metadata](#7-aia-metadata)
8. [OCSP Metadata](#8-ocsp-metadata)
9. [Chain Metadata](#9-chain-metadata)
10. [Warnings & Errors](#10-warnings--errors)
11. [Enforcement Metadata](#11-enforcement-metadata)
12. [Deterministic Ordering](#12-deterministic-ordering)
13. [Example Full JSON Output](#13-example-full-json-output)
14. [See Also](#14-see-also)

---

## 1. Overview

This document defines the **canonical JSON schema** emitted by `check_cert.py` when using `--json`.

The schema is:
* **Deterministic** (stable ordering)
* **Strict** (no surprise fields)
* **Automation‑safe** (consistent structure)
* **Aligned** with verbose output and log banners
* **Versioned implicitly** by the tool version

Any schema change requires a version bump and migration notes.

---

# 2. Top‑Level Structure

The JSON output is a single object with the following top‑level keys, in **guaranteed canonical order**:

```json
{
  "host": "",
  "port": 443,
  "sni": "",
  "timeout": 5,
  "insecure": false,

  "tls": { ... },
  "certificate": { ... },
  "key": { ... },
  "aia": { ... },
  "ocsp": { ... },
  "chain": { ... },

  "warnings": [],
  "errors": [],

  "enforcement": { ... }
}
```

## 3. Host & Connection Metadata

```json
"host": "example.com",
"port": 443,
"sni": "example.com",
"timeout": 5,
"insecure": false
```

| Field |	Description |
| :--- | :--- |
| host |	Hostname provided via -H |
| port |	TLS port (default 443) |
| sni |	SNI override (defaults to host) |
| timeout |	Connection timeout (seconds) |
| insecure |	Whether certificate verification was disabled |

## 4. TLS Session Metadata

```json
"tls": {
  "version": "TLSv1.3",
  "cipher": "TLS_AES_256_GCM_SHA384",
  "cipher_is_aead": true,
  "cipher_is_cbc": false,
  "cipher_is_rc4": false
}
```

| Field |	Description |
| :--- | :--- |
| version |	Negotiated TLS version |
| cipher |	Negotiated cipher suite |
| cipher_is_aead |	Whether cipher is AEAD |
| cipher_is_cbc |	Whether cipher is CBC |
| cipher_is_rc4 |	Whether cipher is RC4 |

## 5. Certificate Metadata

```json
"certificate": {
  "subject_cn": "example.com",
  "issuer_cn": "ZeroSSL ECC Domain Secure Site CA",
  "signature_algorithm": "sha384",
  "wildcard": false,
  "self_signed": false,
  "hostname_matches": true,
  "san": ["example.com"],
  "expires": "2026-06-13 23:59:59",
  "expiration_days": 77,
  "warning_days": 30,
  "critical_days": 15
}
```

| Field |	Description |
| :--- | :--- |
| subject_cn |	Subject Common Name |
| issuer_cn |	Issuer Common Name |
| signature_algorithm |	e.g., sha256, sha384 |
| wildcard |	Whether CN is a wildcard |
| self_signed |	Whether issuer == subject |
| hostname_matches |	Whether certificate matches requested hostname |
| san |	Array of SAN entries (always present) |
| expires |	Expiration timestamp (UTC) |
| expiration_days |	Days until expiration |
| warning_days |	Warning threshold used |
| critical_days |	Critical threshold used |

## 6. Key Metadata

```json
"key": {
  "type": "ecdsa",
  "rsa_bits": null,
  "ecc_curve": "secp256r1"
}
```

| Field |	Description |
| :--- | :--- |
| type |	rsa, ecdsa, or unknown |
| rsa_bits |	RSA key size (null for ECDSA) |
| ecc_curve |	Curve name (null for RSA) |

## 7. AIA Metadata

```json
"aia": {
  "issuer_urls": [
    "http://zerossl.crt.sectigo.com/ZeroSSLECCDomainSecureSiteCA.crt"
  ],
  "chain": [
    {
      "url": "http://zerossl.crt.sectigo.com/ZeroSSLECCDomainSecureSiteCA.crt",
      "subject_cn": "ZeroSSL ECC Domain Secure Site CA",
      "issuer_cn": "USERTrust ECC Certification Authority",
      "signature_algorithm": "sha384",
      "key_type": "ecdsa",
      "ocsp_urls": []
    }
  ]
}
```

| Field |	Description |
| :--- | :--- |
| issuer_urls |	AIA “CA Issuers” URLs |
| chain |	Reconstructed chain certificates (if any) |

## 8. OCSP Metadata

```json
"ocsp": {
  "urls": [],
  "status": "none",
  "reachable": false
}
```

| Field |	Description |
| :--- | :--- |
| urls |	OCSP responder URLs |
| status |	none, good, revoked, unknown |
| reachable |	Whether OCSP responder was reachable |

## 9. Chain Metadata

```json
"chain": {
  "server_sent": false,
  "reconstructed": true,
  "valid": true,
  "errors": []
}
```

| Field |	Description |
| :--- | :--- |
| server_sent |	Whether server provided intermediates |
| reconstructed |	Whether AIA reconstruction succeeded |
| valid |	Whether chain validated |
| errors |	Array of chain errors (always present) |

## 10. Warnings & Errors

```json
"warnings": [],
"errors": []
```

| Field |	Description |
| :--- | :--- |
| warnings |	Non‑fatal issues (weak RSA, weak signature, expiration approaching) |
| errors |	Fatal issues (chain invalid, handshake failure, no certificate) |

Both arrays are always present.

## 11. Enforcement Metadata

```json
"enforcement": {
  "applied": ["expiration", "hostname_match", "san_present", "chain_valid"],
  "passed": ["hostname_match", "expiration"],
  "failed": ["chain_valid"],
  "errors": [],
  "state": 2
}
```

| Field |	Description |
| :--- | :--- |
| applied |	Rules evaluated |
| passed |	Rules that passed |
| failed |	Rules that failed |
| errors |	Internal enforcement errors |
| state |	Nagios state (0 OK, 1 WARN, 2 CRIT, 3 UNKNOWN) |

## 12. Deterministic Ordering

The canonical ordering of top‑level keys is:

1. host
2. port
3. sni
4. timeout
5. insecure
6. tls
7. certificate
8. key
9. aia
10. ocsp
11. chain
12. warnings
13. errors
14. enforcement

This ordering is guaranteed for all JSON output.

## 13. Example Full JSON Output

```json
{
  "host": "example.com",
  "port": 443,
  "sni": "example.com",
  "timeout": 5,
  "insecure": false,

  "tls": {
    "version": "TLSv1.3",
    "cipher": "TLS_AES_256_GCM_SHA384",
    "cipher_is_aead": true,
    "cipher_is_cbc": false,
    "cipher_is_rc4": false
  },

  "certificate": {
    "subject_cn": "example.com",
    "issuer_cn": "ZeroSSL ECC Domain Secure Site CA",
    "signature_algorithm": "sha384",
    "wildcard": false,
    "self_signed": false,
    "hostname_matches": true,
    "san": ["example.com"],
    "expires": "2026-06-13 23:59:59",
    "expiration_days": 77,
    "warning_days": 30,
    "critical_days": 15
  },

  "key": {
    "type": "ecdsa",
    "rsa_bits": null,
    "ecc_curve": "secp256r1"
  },

  "aia": {
    "issuer_urls": [
      "http://zerossl.crt.sectigo.com/ZeroSSLECCDomainSecureSiteCA.crt"
    ],
    "chain": []
  },

  "ocsp": {
    "urls": [],
    "status": "none",
    "reachable": false
  },

  "chain": {
    "server_sent": false,
    "reconstructed": true,
    "valid": true,
    "errors": []
  },

  "warnings": [],
  "errors": [],

  "enforcement": {
    "applied": ["expiration", "hostname_match", "san_present", "chain_valid"],
    "passed": ["expiration", "hostname_match"],
    "failed": [],
    "errors": [],
    "state": 0
  }
}
```

---

## 14. See Also
* [Enforcement](Enforcement.md)
* [Installation](Installation.md)
* [Operations](Operation.md)
* [Roadmap](Roadmap.md)
* [Usage](Usage.md)
* [FLAGS.md](../../../docs/FLAGS.md)
