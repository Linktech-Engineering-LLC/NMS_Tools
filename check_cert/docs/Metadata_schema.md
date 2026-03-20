# Metadata Schema — check_cert.py
This document defines the **canonical JSON schema** emitted by check_cert.py
when using --json.
The schema is **deterministic, stable,** and **ordered**, ensuring reliable
parsing for automation, monitoring pipelines, and log ingestion systems.

All fields follow these principles:

- **Deterministic ordering**
- **No optional fields that appear inconsistently**
- **Explicit nulls only when semantically meaningful**
- **No nested surprises**
- **Stable names across versions**

Future schema changes require a version bump and migration notes.

## 1. Top‑Level Structure
The JSON output is a single object with the following top‑level keys:

{
  "host": "",
  "port": 443,
  "timestamp_utc": "",
  "expiration": {
    "not_before": "",
    "not_after": "",
    "days_remaining": 0
  },
  "certificate": { ... },
  "key": { ... },
  "san": [],
  "tls": { ... },
  "aia": { ... },
  "chain": { ... },
  "ocsp": { ... },
  "warnings": [],
  "errors": [],
  "enforcement": { ... }
}
Each section is documented below.

## 2. Host & Connection Metadata
"host": "example.com",
"port": 443,
"timestamp_utc": "2026-05-18T18:19:55Z"


| Field | Description |
|-------|-------------|
| host | Hostname provided via -H |
| port | Port used for TLS connection |
| timestamp_utc | Time of evaluation in UTC |

## 3. Expiration Metadata
"expiration": {
  "not_before": "2025-02-12T00:00:00Z",
  "not_after": "2026-05-18T18:19:55Z",
  "days_remaining": 60
}

| Field | Description |
|-------|-------------|
| not_before | Certificate validity start |
| not_after	| Certificate expiration timestamp |
| days_remaining | Integer days until expiration |

## 4. Certificate Metadata
json
"certificate": {
  "subject_cn": "example.com",
  "issuer_cn": "Example CA",
  "serial_number": "01A3F9...",
  "signature_algorithm": "sha256",
  "version": 3
}

| Field | Description |
|-------|-------------|
| subject_cn | Subject Common Name |
| issuer_cn	| Issuer Common Name |
| serial_number	| Hexadecimal serial number |
| signature_algorithm | e.g., sha256, sha384, ecdsa-with-SHA256 |
| version |Certificate version (usually 3) |

## 5. Key Metadata
json
"key": {
  "type": "ecdsa",
  "size": 256,
  "curve": "prime256v1"
}

| Field | Description |
|-------|-------------|
| type | rsa, ecdsa, or unknown |
| size | RSA key size in bits, or ECDSA curve size |
| curve	| ECDSA curve name (null for RSA) |

## 6. Subject Alternative Names (SAN)
json
"san": [
  "example.com",
  "*.example.com"
]
Always an array, even if empty.

## 7. TLS Session Metadata
json
"tls": {
  "version": "tls1.3",
  "cipher": "TLS_AES_256_GCM_SHA384"
}

| Field | Description |
|-------|-------------|
| version | Negotiated TLS version |
| cipher | Negotiated cipher suite |

## 8. AIA Metadata
json
"aia": {
  "issuer_urls": [
    "http://ca.example.com/intermediate.crt"
  ]
}

| Field | Description |
|-------|-------------|
| issuer_urls | AIA “CA Issuers” URLs extracted from certificate |

## 9. Chain Metadata
json
"chain": {
  "validated": true,
  "warnings": [],
  "intermediates": [
    {
      "subject_cn": "Example Intermediate CA",
      "issuer_cn": "Example Root CA"
    }
  ]
}

| Field | Description |
|-------|-------------|
| validated	| Whether the chain validated successfully |
| warnings	| Missing intermediates, mismatches, non‑standard chains |
| intermediates	| List of intermediate certificates (minimal metadata) |

## 10. OCSP Metadata
json
"ocsp": {
  "urls": [
    "http://ocsp.example.com"
  ],
  "status": "unknown"
}

| Field | Description |
|-------|-------------|
| urls | OCSP responder URLs |
| status | Placeholder: good, revoked, unknown, invalid |

Full OCSP response parsing is planned for a future version.

## 11. Warnings & Errors
json
"warnings": [],
"errors": []

- warnings: Non‑fatal issues (chain gaps, weak algorithms, missing AIA)
- errors: Fatal issues (handshake failure, parsing errors)

Both arrays are always present.

## 12. Enforcement Metadata
json
"enforcement": {
  "applied": ["min-tls", "require-aead"],
  "passed": ["require-aead"],
  "failed": ["min-tls"],
  "errors": []
}
This structure is defined in detail in **Enforcement.md**.

## 13. Deterministic Ordering
The canonical ordering of top‑level keys is:

1. host
2. port
3. timestamp_utc
4. expiration
5. certificate
6. key
7. san
8. tls
9. aia
10. chain
11. ocsp
12. warnings
13. errors
14. enforcement

This ordering is guaranteed for all JSON output.

## 14. Versioning
The schema is versioned implicitly by the tool version.

Any change to:

- field names
- field types
- field presence rules
- ordering
- enforcement structure

…requires:

- a version bump
- an entry in CHANGELOG
- migration notes

## 15. Example Full JSON Output
{
  "host": "example.com",
  "port": 443,
  "timestamp_utc": "2026-05-18T18:19:55Z",
  "expiration": {
    "not_before": "2025-02-12T00:00:00Z",
    "not_after": "2026-05-18T18:19:55Z",
    "days_remaining": 60
  },
  "certificate": {
    "subject_cn": "example.com",
    "issuer_cn": "Example CA",
    "serial_number": "01A3F9",
    "signature_algorithm": "sha256",
    "version": 3
  },
  "key": {
    "type": "ecdsa",
    "size": 256,
    "curve": "prime256v1"
  },
  "san": [
    "example.com",
    "*.example.com"
  ],
  "tls": {
    "version": "tls1.3",
    "cipher": "TLS_AES_256_GCM_SHA384"
  },
  "aia": {
    "issuer_urls": [
      "http://ca.example.com/intermediate.crt"
    ]
  },
  "chain": {
    "validated": true,
    "warnings": [],
    "intermediates": [
      {
        "subject_cn": "Example Intermediate CA",
        "issuer_cn": "Example Root CA"
      }
    ]
  },
  "ocsp": {
    "urls": [
      "http://ocsp.example.com"
    ],
    "status": "unknown"
  },
  "warnings": [],
  "errors": [],
  "enforcement": {
    "applied": ["min-tls", "require-aead"],
    "passed": ["require-aead"],
    "failed": ["min-tls"],
    "errors": []
  }
}
