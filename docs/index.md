# NMS_Tools Documentation

Welcome to the documentation for **NMS_Tools**, a suite of deterministic,
audit‑transparent monitoring and network‑inspection tools used across Linktech
Engineering infrastructure.

This documentation covers installation, usage, operation, enforcement, metadata
schema details, and the project roadmap.

---

## Available Tools

### `check_ports.py`
Deterministic multi‑port TCP connectivity checker.

- Supports lists, ranges, and mixed port sets  
- JSON, verbose, quiet, and Nagios modes  
- Operator‑grade logging with rotation  
- Deterministic evaluation rules  
- Tool documentation: [`check_ports/README.md`](../check_ports/README.md)  
- Flags reference: [`check_ports/FLAGS.md`](../check_ports/FLAGS.md)

---

### `check_weather.py`
Rule‑based weather condition evaluator using deterministic JSON schemas.

- Supports temperature, wind, visibility, precipitation, and condition rules  
- JSON, verbose, quiet, and Nagios modes  
- Deterministic rule engine  
- Tool documentation: [`check_weather/README.md`](../check_weather/README.md)  
- Flags reference: [`check_weather/FLAGS.md`](../check_weather/FLAGS.md)

---

### `check_cert.py`
Deterministic TLS certificate inspection and policy enforcement.

- JSON, verbose, and Nagios output modes  
- TLS version, cipher, SAN, issuer, signature algorithm, and key metadata  
- AIA chain reconstruction and OCSP metadata extraction  
- Deterministic JSON schema for automation  
- Tool documentation: [`check_cert/README.md`](../check_cert/README.md)

---

### `check_html.py`
Deterministic HTTP/HTTPS inspection and content‑validation tool.

- TLS‑aware request pipeline  
- HTTP status, headers, content‑type, and HTML body capture  
- Backend fingerprinting and enforcement  
- Deterministic JSON schema for automation  
- Tool documentation: [`check_html/README.md`](../check_html/README.md)

---

### `check_interfaces.py`
Network interface state and SNMP‑based status checker.

- Deterministic interface enumeration  
- SNMP‑based operational state evaluation  
- JSON, verbose, and Nagios modes  
- Tool documentation: [`check_interfaces/README.md`](../check_interfaces/README.md)

---

## Documentation Suite

### Core Guides
- **Installation Guide** — [`Installation.md`](Installation.md)  
- **Usage Guide** — [`Usage.md`](Usage.md)  
- **Operation Guide** — [`Operation.md`](Operation.md)  

### Reference
- **Enforcement Model** — [`Enforcement.md`](Enforcement.md)  
- **Metadata Schema** — [`Metadata_Schema.md`](Metadata_Schema.md)  

### Project
- **Roadmap** — [`roadmap.md`](roadmap.md)  
- **Contributing Guidelines** — `CONTRIBUTING.md`  
- **Changelog** — `CHANGELOG.md`  

Each document has a single responsibility:

| Document | Purpose |
|----------|---------|
| Installation | How to install and run the suite |
| Usage | CLI flags, examples, Nagios integration |
| Operation | Runtime behavior, exit codes, troubleshooting |
| Enforcement | Policy engine, rule semantics, failure behavior |
| Metadata Schema | Canonical JSON structure for automation |
| Roadmap | Planned enhancements and future tools |
| CONTRIBUTING | Guidelines for contributors |
| CHANGELOG | Version history and schema changes |

---

## Project Website

The official project page for NMS_Tools is available at:

**https://www.linktechengineering.net/projects/nms-tools/**

This site provides:

- Suite overview  
- Tool descriptions  
- Branding and identity  
- Cross‑project navigation  
- Public documentation  
- Related ecosystem projects  

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
See [`roadmap.md`](roadmap.md) for planned enhancements and upcoming tools.
