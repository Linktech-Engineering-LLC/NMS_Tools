# Metadata Schema — check_cert.py

This document defines the canonical JSON schema emitted by check_cert.py when using --json.

The schema is:

* Deterministic (stable ordering)
* Strict (no surprise fields)
* Automation‑safe (consistent structure)
* Versioned implicitly by the tool version

Any schema change requires a version bump and migration notes.

## 1. Top‑Level Structure

The JSON output is a single object with the following top‑level keys, in guaranteed order:

```json
{
  "host": "",
  "port": 443,
  "timestamp_utc": "",
  "expiration": { ... },
  "certificate": { ... },
  "hostname_matches": false,
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
```

Each section is documented below.

## 2. Host & Connection Metadata

```Code
"host": "example.com",
"port": 443,
"timestamp_utc": "2026-05-18T18:19:55Z"
```

| Field |	Description |
| :--- | :--- |
| host | Hostname provided via -H |
| port | Port used for TLS connection |
| timestamp_utc | Time of evaluation in UTC |

## 3. Expiration Metadata

```json
"expiration": {
  "not_before": "2025-02-12T00:00:00Z",
  "not_after": "2026-05-18T18:19:55Z",
  "days_remaining": 60
}
```

| Field	| Description |
| :--- | :--- |
| not_before | Certificate validity start |
| not_after |	Certificate expiration timestamp |
| days_remaining | Integer days until expiration |

## 4. Certificate Metadata

```json
"certificate": {
  "subject_cn": "example.com",
  "issuer_cn": "Example CA",
  "serial_number": "01A3F9",
  "signature_algorithm": "sha256",
  "wildcard": false
}
```

| Field	| Description |
| :--- | :--- |
| subject_cn | Subject Common Name |
| issuer_cn |	Issuer Common Name |
| serial_number |	Hexadecimal serial number |
| signature_algorithm |	e.g., sha256, sha384, ecdsa-with-SHA256 |
| wildcard |	Whether the certificate is a wildcard cert |

## 5. Hostname Match Metadata

```json
"hostname_matches": true
```

| Field	| Description |
| :--- | :--- |
| hostname_matches |	Whether the certificate matches the requested hostname |

## 6. Key Metadata

```json
"key": {
  "type": "ecdsa",
  "size": 256,
  "curve": "prime256v1"
}
```

| Field	| Description |
| :--- | :--- |
| type |	rsa, ecdsa, or unknown |
| size | RSA key size in bits, or ECDSA curve size |
| curve |	ECDSA curve name (null for RSA) |

## 7. Subject Alternative Names (SAN)

```json
"san": [
  "example.com",
  "*.example.com"
]
```

Always an array, even if empty.

## 8. TLS Session Metadata

```json
"tls": {
  "version": "tls1.3",
  "cipher": "TLS_AES_256_GCM_SHA384"
}
```

| Field	| Description |
| :--- | :--- |
| version	| Negotiated TLS version |
| cipher |	Negotiated cipher suite |

## 9. AIA Metadata

```json
"aia": {
  "ocsp": [
    "http://ocsp.example.com"
  ],
  "ca_issuers": [
    "http://ca.example.com/intermediate.crt"
  ]
}
```

| Field	| Description |
| :--- | :--- |
| ocsp  |	OCSP responder URLs |
| ca_issuers |	AIA “CA Issuers” URLs |

Both arrays are always present.

## 10. Chain Metadata

```json
"chain": {
  "ok": true,
  "depth": 2,
  "warnings": [],
  "intermediates": [
    {
      "subject_cn": "Example Intermediate CA",
      "issuer_cn": "Example Root CA"
    }
  ],
  "root_subject_cn": "Example Root CA",
  "root_issuer_cn": "Example Root CA"
}
```

| Field	| Description |
| :--- | :--- |
| ok |	Whether the chain validated successfully |
| depth |	Number of certificates in the chain |
| warnings |	Missing intermediates, mismatches, non‑standard chains |
| intermediates |	Minimal metadata for intermediate certs |
| root_subject_cn |	Subject CN of the root certificate |
| root_issuer_cn |	Issuer CN of the root certificate |

## 11. OCSP Metadata

```json
"ocsp": {
  "urls": [
    "http://ocsp.example.com"
  ],
  "state": "unknown",
  "revocation_reason": null
}
```

| Field	| Description |
| :--- | :--- |
| urls |	OCSP responder URLs |
| state |	good, revoked, unknown, error |
| revocation_reason |	Null or string (future expansion) |

## 12. Warnings & Errors

```json
"warnings": [],
"errors": []
```

* warnings: Non‑fatal issues (chain gaps, weak algorithms, missing AIA)
* errors: Fatal issues (handshake failure, parsing errors)

Both arrays are always present.

## 13. Enforcement Metadata

```json
"enforcement": {
  "applied": ["min-tls", "require-aead"],
  "passed": ["require-aead"],
  "failed": ["min-tls"],
  "errors": []
}
```

This structure is defined in detail in Enforcement.md.

## 14. Deterministic Ordering

The canonical ordering of top‑level keys is:

* host
* port
* timestamp_utc
* expiration
* certificate
* hostname_matches
* key
* san
* tls
* aia
* chain
* ocsp
* warnings
* errors
* enforcement

This ordering is guaranteed for all JSON output.

## 15. Versioning

Any change to:

* field names
* field types
* field presence rules
* ordering
* enforcement structure

…requires:

* a version bump
* a CHANGELOG entry
* migration notes

## 16. Example Full JSON Output

```json
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
    "wildcard": false
  },
  "hostname_matches": true,
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
    "ocsp": [
      "http://ocsp.example.com"
    ],
    "ca_issuers": [
      "http://ca.example.com/intermediate.crt"
    ]
  },
  "chain": {
    "ok": true,
    "depth": 2,
    "warnings": [],
    "intermediates": [
      {
        "subject_cn": "Example Intermediate CA",
        "issuer_cn": "Example Root CA"
      }
    ],
    "root_subject_cn": "Example Root CA",
    "root_issuer_cn": "Example Root CA"
  },
  "ocsp": {
    "urls": [
      "http://ocsp.example.com"
    ],
    "state": "unknown",
    "revocation_reason": null
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
```
