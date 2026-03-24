# check_cert — TLS Certificate Inspection & Monitoring Tool
![Python Version](https://img.shields.io/badge/python-3.6%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-stable-brightgreen)
![Nagios Plugin](https://img.shields.io/badge/Nagios-plugin-success)
![NMS_Tools](https://img.shields.io/badge/NMS_Tools-check__cert-blueviolet)

check_cert is an operator‑grade TLS certificate inspection tool designed for Nagios, automation pipelines, and standalone diagnostics. It performs deterministic metadata extraction, monitoring checks, and optional policy enforcement, with clean output modes for Nagios, verbose inspection, and JSON integration.

This tool is part of the **NMS_Tools** monitoring suite.

## 📘 Features

* Deterministic TLS session metadata
* Certificate parsing and normalization
* CN, SAN, wildcard, issuer, signature algorithm
* Key metadata (RSA bits, ECC curve)
* Expiration and validity checks
* OCSP URL extraction and reachability
* AIA URL extraction
* Chain presence and reconstruction metadata
* Monitoring enforcement (expiration, hostname, SAN, self‑signed, chain, OCSP)
* Unified enforcement engine across all output modes
* Clean Nagios output
* Structured JSON output for automation
* Python 3.6+ compatible

## 🚀 Quick Start

Check a certificate:

```Code
./check_cert.py -H example.com
```

Check with insecure mode (skip TLS verification):

```Code
./check_cert.py -H example.com --insecure
```

Verbose inspection:

```Code
./check_cert.py -H example.com -v
```

JSON output:

```Code
./check_cert.py -H example.com -j
```

Nagios thresholds:

```Code
./check_cert.py -H example.com -w 14 -c 7
```


## 🧭 Output Modes

### Nagios (default)

Single‑line, deterministic output:

```Code
OK - certificate valid, expires in 357 days on 2027-03-15
```

Exit codes follow Nagios conventions:

| Code | Meaning |
| :---: | :--- |
| 0 | OK |
| 1 | WARNING |
| 2 | CRITICAL |
| 3 | UNKNOWN |

### Verbose Mode (-v / --verbose)

Shows:

* Connection details
* TLS session metadata
* Certificate metadata
* Key metadata
* SAN/CN
* Chain diagnostics
* OCSP metadata
* Warnings & errors
* Enforcement summary

This mode is ideal for debugging and operator inspection.

### JSON Mode (-j / --json)

Machine‑readable structured output including:

* TLS metadata
* Certificate metadata
* Key metadata
* SAN/CN
* Chain metadata
* OCSP metadata
* Expiration metadata
* Unified enforcement block

Perfect for automation, dashboards, and log ingestion.

## 🔒 Enforcement Model

check_cert uses a unified enforcement engine:

### Monitoring Enforcement

Enabled by default:

* Expiration thresholds (-w, -c)
* Hostname match
* SAN presence
* Self‑signed detection
* Chain presence
* OCSP reachability

These can be disabled individually:

```Code
--no-check-san
--no-check-self-signed
--no-check-chain
--no-check-ocsp
```

### Policy Enforcement

Optional, stricter rules for:

* TLS versions
* Cipher suites
* Key sizes
* Issuer rules
* OCSP requirements

Both enforcement layers produce an EnforcementResults structure, which is merged into a single deterministic enforcement block used by all output modes.

## 🔧 CLI Reference

```Code
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
```

## 📦 Installation

Clone the NMS_Tools repository:

```Code
git clone https://github.com/LinktechEngineering/NMS_Tools
cd NMS_Tools/check_cert
```

Run directly:

```Code
./check_cert.py -H example.com
```

Or install dependencies:

```bash
pip install cryptography
pip install typing_extensions   # only for Python < 3.8
```

## 📚 Documentation

Full documentation is available under:

```Code
check_cert/docs/
```

Including:

* Installation.md
* Usage.md
* Enforcement.md
* Metadata.md
* Roadmap.md

## 🛠 Roadmap
Future enhancements are tracked in:

```Code
check_cert/docs/Roadmap.md
```

Planned items include:

* OCSP stapling enforcement
* Full AIA chain reconstruction
* TLS version policy profiles
* Cipher policy profiles
* SCT (Certificate Transparency) extraction
* CRL distribution point extraction
* Extended JSON schema

## 📄 License

This tool is released under the MIT License.