# check_cert — TLS Certificate Inspection & Monitoring Tool

![Python Version](https://img.shields.io/badge/python-3.6%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-stable-brightgreen)
![Nagios Plugin](https://img.shields.io/badge/Nagios-plugin-success)
![NMS_Tools](https://img.shields.io/badge/NMS_Tools-check__cert-blueviolet)

**check_cert** is an operator‑grade TLS certificate inspection and monitoring tool designed for:

- Nagios / Icinga / Sensu
- Automation pipelines
- CI/CD validation
- Standalone diagnostics

The tool produces **deterministic**, **structured**, and **audit‑transparent** output across all modes:

- Nagios (default)
- Verbose inspection
- JSON for automation
- Canonical log banners (START / CERT / RESULT / END)

check_cert is part of the **NMS_Tools** monitoring suite.

---

## 📘 Features

### 🔍 Deterministic Metadata Extraction
- Canonical metadata builder (single source of truth)
- TLS session metadata (version, cipher, AEAD/CBC/RC4 classification)
- Certificate metadata (CN, SAN, issuer, signature algorithm, wildcard)
- Key metadata (RSA bits, ECC curve)
- Expiration and validity metadata

### 🔗 Chain, AIA, and OCSP
- Server‑sent chain detection
- AIA issuer URL extraction
- AIA chain reconstruction
- Chain validation (server_sent, reconstructed, valid, errors)
- OCSP URL extraction
- OCSP reachability metadata

### 🛡 Unified Enforcement Engine
- Monitoring enforcement (expiration, hostname, SAN, self‑signed, chain, OCSP)
- Optional policy enforcement (TLS versions, ciphers, key sizes)
- Deterministic enforcement block used across all output modes

### 📤 Clean Output Modes
- Nagios single‑line output with perfdata
- Verbose operator‑grade inspection
- JSON structured output for automation
- Canonical logging subsystem (START / CERT / RESULT / END)

### 🧱 Architecture
- Fully deterministic behavior
- No side effects
- Clean separation of:
  - metadata extraction  
  - enforcement  
  - output formatting  
  - logging  

---

## 🚀 Quick Start

Check a certificate:

`./check_cert.py -H example.com`


Check with insecure mode (skip TLS verification):

`./check_cert.py -H example.com --insecure`


Verbose inspection:

`./check_cert.py -H example.com -v`


JSON output:

`./check_cert.py -H example.com -j`


Nagios thresholds:

`./check_cert.py -H example.com -w 14 -c 7`


---

## 🧭 Output Modes

### ⭐ Nagios (default)

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

### ⭐ Verbose Mode (`-v` / `--verbose`)

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

### ⭐ JSON Mode (`-j` / `--json`)

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

## 🔒 Enforcement Model

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

## 📜 Logging Subsystem
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

## 🔧 CLI Reference

usage: check_cert.py -H HOST [options]

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

## 📦 Installation

Clone the NMS_Tools repository:

```bash
git clone https://github.com/LinktechEngineering/NMS_Tools
cd NMS_Tools/check_cert
```

Run directly:

```bash
./check_cert.py -H example.com
```

## 📚 Documentation
Documentation is available under:

Code
check_cert/docs/
Including:

* [Installation.md](docs/Installation.md)
* [Usage.md](docs/Usage.md)
* [Enforcement.md](docs/Enforcement.md)
* [Metadata_Schema.md](docs/Metadata_schema.md)
* [Operation.md](docs/Operation.md)
* [Roadmap.md](docs/Roadmap.md)
* [Logging.md](docs/Logging.md)

## 🛠 Roadmap
Future enhancements tracked in:

check_cert/docs/Roadmap.md

* Planned items include:
* OCSP stapling enforcement
* Full AIA chain reconstruction
* TLS version policy profiles
* Cipher policy profiles
* SCT extraction
* CRL distribution point extraction
* Extended JSON schema
* Stabilization of check_interfaces.py to match check_cert architecture
* Add Logging.md documenting canonical log banners

## 📄 License

Released under the MIT License.