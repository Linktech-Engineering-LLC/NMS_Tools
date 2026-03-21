# NMS_Tools Documentation

Welcome to the documentation for **NMS_Tools**, a suite of deterministic,
audit‑transparent network management and monitoring tools used across Linktech
Engineering infrastructure.

This documentation covers installation, usage, operation, enforcement, metadata
schema details, and the project roadmap.

---

## Available Tools

### `check_cert.py`
A deterministic TLS certificate inspection and policy enforcement tool with:

- JSON, verbose, and Nagios output modes  
- TLS version and cipher extraction  
- SAN, issuer, signature algorithm, and key metadata  
- AIA chain reconstruction  
- OCSP metadata extraction  
- Expiration thresholds and policy enforcement  
- Deterministic JSON schema for automation  

### `check_html.py`

A deterministic HTTP/HTTPS inspection and content‑validation tool with:

- JSON, verbose, and Nagios output modes
- TLS‑aware request pipeline with handshake detection
- HTTP status, headers, content‑type, and HTML body capture
- Backend fingerprinting and backend enforcement
- Content‑type and HTML presence rules
- Deterministic JSON schema for automation
- Clean, noise‑free CLI parser and help output

---

## Documentation Suite

### Core Guides
- **Installation Guide** — `Installation.md`  
- **Usage Guide** — `Usage.md`  
- **Operation Guide** — `Operation.md`  

### Reference
- **Enforcement Model** — `Enforcement.md`  
- **Metadata Schema** — `Metadata_Schema.md`  

### Project
- **Roadmap** — `roadmap.md`  
- **Contributing Guidelines** — `CONTRIBUTING.md`  
- **Changelog** — `CHANGELOG.md`  

Each document has a single responsibility:

| Document | Purpose |
|----------|---------|
| Installation | How to install and run the tool |
| Usage | CLI flags, examples, Nagios integration |
| Operation | Runtime behavior, exit codes, troubleshooting |
| Enforcement | Policy engine, rule semantics, failure behavior |
| Metadata Schema | Canonical JSON structure for automation |
| Roadmap | Planned enhancements and future tools |
| CONTRIBUTING | Guidelines for contributors |
| CHANGELOG | Version history and schema changes |

---

## Philosophy

NMS_Tools follows Linktech Engineering’s deterministic engineering principles:

- Predictable, reproducible behavior  
- No hidden state  
- Audit‑transparent output  
- Strict separation between human and machine modes  
- Minimal dependencies  
- Monitoring‑friendly design  

---

## Status

Active development.  
See `roadmap.md` for planned enhancements and upcoming tools.
