# check_cert — TLS Certificate Inspection & Monitoring Tool

**Part of:** NMS_Tools Monitoring Suite  
**Script:** `check_cert.py`  
**Author:** Leon McClatchey, Linktech Engineering LLC  
**License:** MIT  
**Requires:** Python 3.12+  (development only; not required for frozen binary)
**Last Updated:** 2026-08-17

![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-stable-brightgreen)
![Nagios Plugin](https://img.shields.io/badge/Nagios-plugin-success)
![NMS_Tools](https://img.shields.io/badge/NMS_Tools-check__cert-blueviolet)

## Table of Contents
1. [Overview](#1-overview)
2. [Features](#2--features)
    1. [2.1 Deterministic Metadata Extraction](#21-deterministic-metadata-extraction)
    2. [2.2 Chain, AIA, and OCSP](#22--chain-aia-and-ocsp)
    3. [2.3 Unified Enforcement Engine](#23--unified-enforcement-engine)
    4. [2.4 Clean Output Modes](#24--clean-output-modes)
3. [Quick Start](#3--quick-start)
4. [Output Modes](#4--output-modes)
    1. [4.1 Nagios Mode](#41--nagios-default)
    2. [4.2 Verbose Mode](#42--verbose-mode--v----verbose)
    3. [4.3 JSON Mode](#43--json-mode--j----json)
5. [Enforcement Model](#5--enforcement-model)
6. [Logging Subsystem](#6--logging-subsystem)
7. [CLI Reference](#7--cli-reference)
8. [Installation](#8--installation)
9. [PythonTools Requirement](#9--pythontools-requirement-script-mode)
10. [Documentation](#10--documentation)
11. [Roadmap](#11--roadmap)
12. [License](#12l--license)

---

## 1. Overview

**check_cert** is an operator‑grade TLS certificate inspection and monitoring tool designed for:

* Nagios / Icinga / Sensu
* Automation pipelines
* CI/CD validation
* Standalone diagnostics

The tool produces **deterministic**, **structured**, and **audit‑transparent** output across all modes:

* Nagios (default)
* Verbose inspection
* JSON for automation
* Canonical log banners (START / CERT / RESULT / END)

check_cert is part of the **NMS_Tools** monitoring suite.

---

## 2. 📘 Features

### 2.1🔍 Deterministic Metadata Extraction

check_cert extracts a complete, operator‑grade metadata set:

#### TLS Metadata
* TLS version
* Cipher suite
* AEAD / CBC / RC4 classification
* TLS negotiation state (tls_state)
* TLS negotiation messages (tls_messages[])
* TLS handshake state (tls_handshake_state)
* TLS handshake message (tls_handshake_message)

#### Certificate Metadata
* Subject CN
* SAN list
* Issuer CN
* Wildcard detection
* Self‑signed detection
* Hostname match (`hostname_matches`)
* Signature algorithm + strength classification
  * `signature_algorithm_state`
  * `signature_algorithm_message`
* Expiration timestamp
* Days remaining
* Warning / critical thresholds

#### Key Metadata
* Key type (RSA / ECDSA)
* RSA bit length
* ECC curve
* Key strength classification
  * `key_state`
  * `key_message`

### 2.2 🔗 Chain, AIA, and OCSP

#### AIA Metadata
* Issuer URLs
* AIA chain reconstruction
* Per‑certificate metadata:
  * subject_cn
  * issuer_cn
  * signature_algorithm
  * key_type
  * ocsp_urls

#### Chain Metadata
* Server‑sent chain detection
* AIA‑reconstructed chain
* Chain validity
* Chain errors
* Chain state (`chain_state`)
* Chain message (`chain_message`)

#### OCSP Metadata
* OCSP URLs
* OCSP status (none, present, etc.)
* Reachability (reachable)

### 2.3 🛡 Unified Enforcement Engine

All output modes share a deterministic enforcement block.

#### Monitoring Enforcement (default)
* Expiration
* Hostname match
* SAN presence
* Self‑signed detection
* Chain validity
* OCSP reachability
* Chain completeness warning
  * New rule: `chain_completeness_warning`
  * Triggered when server omits intermediates

#### Policy Enforcement (optional)
* TLS version rules
* Cipher rules
* Key size rules
* Issuer rules
* OCSP requirements

#### Deterministic Enforcement Block

All modes produce:

```Code
"enforcement": {
  "applied": [...],
  "passed": [...],
  "failed": [...],
  "errors": [],
  "state": 0|1|2|3
}
```

### 2.4 📤 Clean Output Modes

#### ⭐ Nagios (default)

Deterministic single‑line output:

```Code
OK - certificate valid, expires on 2026-06-13 | days_remaining=77;30;15
```

Exit codes follow Nagios conventions:

| Code | Meaning |
| --- | --- |
| 0 | OK |
| 1 | WARNING |
| 2 | CRITICAL |
| 3 | UNKNOWN |

#### ⭐ Verbose Mode (-v)

Full operator‑grade inspection including:
* TLS negotiation
* TLS handshake
* Certificate metadata
* Key metadata
* SAN/CN
* AIA chain
* OCSP
* Chain validation
* Warnings / errors
* Enforcement summary

#### ⭐ JSON Mode (-j)

Machine‑readable structured output with a stable schema.

**Updated JSON Schema (Current Version)** 

```json
{
  "host": "...",
  "port": 443,
  "sni": "...",
  "timeout": 5,
  "insecure": false,

  "tls": {
    "version": "tlsv1.3",
    "cipher": "TLS_AES_256_GCM_SHA384",
    "tls_state": "OK",
    "tls_messages": [...],
    "tls_handshake_state": "OK",
    "tls_handshake_message": "...",
    "cipher_is_aead": true,
    "cipher_is_cbc": false,
    "cipher_is_rc4": false
  },

  "certificate": {
    "subject_cn": "...",
    "issuer_cn": "...",
    "signature_algorithm": "...",
    "signature_algorithm_state": "OK",
    "signature_algorithm_message": "...",
    "wildcard": false,
    "self_signed": false,
    "hostname_matches": true,
    "san": [...],
    "expires": "...",
    "expiration_days": 39,
    "warning_days": 30,
    "critical_days": 15
  },

  "key": {
    "type": "ecdsa",
    "rsa_bits": null,
    "ecc_curve": "secp256r1",
    "key_state": "OK",
    "key_message": "Strong ECDSA curve: secp256r1"
  },

  "aia": {
    "issuer_urls": [...],
    "chain": [
      {
        "url": "...",
        "subject_cn": "...",
        "issuer_cn": "...",
        "signature_algorithm": "...",
        "key_type": "...",
        "ocsp_urls": [...]
      }
    ]
  },

  "ocsp": {
    "urls": [...],
    "status": "none",
    "reachable": false
  },

  "chain": {
    "server_sent": false,
    "reconstructed": true,
    "valid": true,
    "errors": [],
    "chain_state": "WARNING",
    "chain_message": "Chain reconstructed via AIA (server did not send intermediates)"
  },

  "warnings": [],
  "errors": [],

  "enforcement": {
    "applied": [...],
    "passed": [...],
    "failed": ["chain_completeness_warning"],
    "errors": [],
    "state": 1
  }
}
```

### 🧱 Architecture
- Fully deterministic behavior
- No side effects
- Clean separation of:
  - metadata extraction  
  - enforcement  
  - output formatting  
  - logging  

---

## 3. 🚀 Quick Start

Check a certificate:

`./check_cert -H example.com`


Check with insecure mode (skip TLS verification):

`./check_cert -H example.com --insecure`


Verbose inspection:

`./check_cert -H example.com -v`


JSON output:

`./check_cert -H example.com -j`


Nagios thresholds:

`./check_cert -H example.com -w 14 -c 7`


---

## 4. 🧭 Output Modes

### 4.1 ⭐ Nagios (default)

Deterministic single‑line output:

`OK - certificate valid, expires on 2026-06-13 | days_remaining=77;30;15`


Exit codes follow Nagios conventions:

| Code | Meaning |
| :---: | :--- |
| 0 | OK |
| 1 | WARNING |
| 2 | CRITICAL |
| 3 | UNKNOWN |

---

### 4.2 ⭐ Verbose Mode (`-v` / `--verbose`)

Verbose mode provides a complete operator‑grade inspection:

- Connection details  
- TLS session metadata  
- Certificate metadata  
- Key metadata  
- SAN/CN  
- AIA metadata  
- OCSP metadata  
- Chain validation  
- General warnings  
- General errors  
- Chain summary  
- Enforcement summary  

Ideal for diagnostics and debugging.

---

### 4.3 ⭐ JSON Mode (`-j` / `--json`)

Machine‑readable structured output with a **stable schema**:

- `tls`  
- `certificate`  
- `key`  
- `aia`  
- `ocsp`  
- `chain`  
- `warnings`  
- `errors`  
- `enforcement`  

Example (truncated):

```json
{
  "host": "example.com",
  "tls": {
    "version": "TLSv1.3",
    "cipher": "TLS_AES_256_GCM_SHA384",
    "cipher_is_aead": true
  },
  "certificate": {
    "subject_cn": "example.com",
    "issuer_cn": "ZeroSSL ECC Domain Secure Site CA",
    "expiration_days": 77
  },
  "chain": {
    "server_sent": false,
    "reconstructed": true,
    "valid": true,
    "errors": []
  },
  "enforcement": {
    "state": 0,
    "failed": [],
    "applied": ["expiration", "hostname_match", "san_present", "chain_valid"]
  }
}
```

## 5. 🔒 Enforcement Model

check_cert uses a unified enforcement engine shared across all output modes.

**Monitoring Enforcement (default)**

* Expiration thresholds (-w, -c)
* Hostname match
* SAN presence
* Self‑signed detection
* Chain validation
* OCSP reachability

Disable individual checks:

```
--no-check-san
--no-check-self-signed
--no-check-chain
--no-check-ocsp
```

**Policy Enforcement (optional)**

Stricter rules for:

* TLS versions
* Cipher suites
* Key sizes
* Issuer rules
* OCSP requirements

**Enforcement Block (JSON)**

All modes share a deterministic enforcement block:

```
"enforcement": {
  "applied": [...],
  "passed": [...],
  "failed": [...],
  "errors": [],
  "state": 2
}
```

## 6. 📜 Logging Subsystem
check_cert writes deterministic log entries using canonical banners:

[START]

* Script name
* Host / port / SNI
* Timeout
* Insecure flag
* Warning / critical thresholds
* Mode

[CERT]

* TLS metadata
* Certificate metadata
* Key metadata
* OCSP metadata
* Chain metadata

[RESULT]

* Nagios state
* Failed rules
* Failure list

[END]

* Marks completion

Example:

```
2026-03-28 12:19:11; [START] check_cert host=example.com port=443 ...
2026-03-28 12:19:11; [CERT] host=example.com tls_version=TLSv1.3 ...
2026-03-28 12:19:11; [RESULT] state=0 failed=0 failures=[]
2026-03-28 12:19:11; [END]
```

## 7. 🔧 CLI Reference

usage: check_cert -H HOST [options]

Connection:
  -H, --host HOST
  -p, --port PORT
  --sni NAME
  --timeout SECONDS
  --insecure

Nagios thresholds:
  -w, --warning DAYS
  -c, --critical DAYS

Output modes:
  -v, --verbose
  -j, --json

Monitoring controls:
  --no-check-san
  --no-check-self-signed
  --no-check-chain
  --no-check-ocsp

## 8. 📦 Installation

Clone the NMS_Tools repository:

```bash
git clone https://github.com/LinktechEngineering/NMS_Tools
cd NMS_Tools/check_cert
```

Run directly:

```bash
./check_cert -H example.com
```

## 9. 📦 PythonTools Requirement (Script Mode)

When running `check_cert` **as a Python script**, the `PythonTools` library must be installed.
The frozen binary (`dist/check_cert`) bundles PythonTools internally, but the script version does not.

### Install PythonTools

Clone the PythonTools repository:

```bash
git clone https://github.com/LinktechEngineering/PythonTools
cd PythonTools
pip install .
```

Or install in editable mode:

```bash
pip install -e .
```

### Why this is required

`check_cert.py` imports several PythonTools modules, including:
* deterministic logging subsystem
* CLI helpers
* invariant utilities
* shared metadata helpers
* common error/exception models

These modules are bundled into the frozen binary, but not into the script version.
Therefore, PythonTools must be installed when running check_cert.py directly.

## 10. 📚 Documentation
Documentation is available under:

check_cert/docs/
Including:

* [Installation.md](docs/Installation.md)
* [Usage.md](docs/Usage.md)
* [Enforcement.md](docs/Enforcement.md)
* [Metadata_Schema.md](docs/Metadata_schema.md)
* [Operation.md](docs/Operation.md)
* [Roadmap.md](docs/Roadmap.md)
* [Logging.md](docs/Logging.md)

## 11. 🛠 Roadmap

* OCSP stapling enforcement
* SCT extraction
* CRL distribution point extraction
* Extended JSON schema
* Stabilization of check_interfaces.py to match check_cert architecture
* Additional chain completeness heuristics
* Add Logging.md documenting canonical log banners

## 12l 📄 License

Released under the MIT License.