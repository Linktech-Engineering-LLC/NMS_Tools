# NMS_Tools

![Python Version](https://img.shields.io/badge/python-3.6%2B-blue)
![License](https://img.shields.io/badge/license-Apache%202.0-green)
![Status](https://img.shields.io/badge/status-active-success)
![Last Commit](https://img.shields.io/github/last-commit/Linktech-Engineering-LLC/NMS_Tools)

A collection of deterministic, audit‑transparent network management and monitoring tools used across Linktech Engineering infrastructure.

Each tool is designed with:

- Predictable, reproducible behavior  
- Strict output contracts  
- Clear operational modes  
- Minimal external dependencies  
- Compatibility with Nagios/Icinga and standalone system use  

---

## Tools

### `check_cert.py`

A deterministic TLS certificate inspection and policy enforcement tool with:

- JSON, verbose, and Nagios output modes  
- TLS version and cipher extraction  
- SAN, issuer, signature algorithm, and key metadata  
- AIA chain reconstruction  
- OCSP metadata extraction  
- Expiration thresholds and policy enforcement  
- Deterministic JSON schema for automation  
- Clean, noise‑free CLI parser and help output  

---

### `check_html.py`

A deterministic HTTP/HTTPS inspection and content‑validation tool with:

- JSON, verbose, and Nagios output modes  
- TLS‑aware request pipeline with handshake detection  
- HTTP status, headers, content‑type, and HTML body capture  
- Backend fingerprinting and backend enforcement  
- Content‑type and HTML presence rules  
- Deterministic JSON schema for automation  
- Clean, noise‑free CLI parser and help output  
- Nagios‑aware severity merging (CRITICAL > WARNING > UNKNOWN > OK)

---

## Documentation

The `docs/` directory contains the full documentation suite for all tools:

- **Installation:** `docs/Installation.md`  
- **Usage Guide:** `docs/Usage.md`  
- **Operation Guide:** `docs/Operation.md`  
- **Enforcement Model:** `docs/Enforcement.md`  
- **Metadata Schema:** `docs/Metadata_Schema.md`  
- **Roadmap:** `docs/roadmap.md`  

Each document has a single responsibility:

| Document | Purpose |
|----------|---------|
| Installation | How to install and run the tools |
| Usage | CLI flags, examples, Nagios integration |
| Operation | Runtime behavior, exit codes, troubleshooting |
| Enforcement | Policy engine, rule semantics, failure behavior |
| Metadata Schema | Canonical JSON structure for automation |
| Roadmap | Planned enhancements and future tools |

---

## Philosophy

NMS_Tools follows Linktech Engineering’s deterministic engineering principles:

- No hidden state  
- No ambiguous output  
- No silent failures  
- Audit‑transparent behavior  
- Predictable exit codes  
- Clean separation between human and machine output modes  

Each tool is built to be reliable in both interactive and automated environments.

---

## Status

Active development.  
See `docs/roadmap.md` for planned enhancements and upcoming tools in the suite.

## Quick Start

Clone the repository:

```bash
git clone https://github.com/LinktechEngineering/NMS_Tools.git
cd NMS_Tools
```

Run a certificate check:

```bash
./check_cert.py -H example.com
```

Run an HTML check:

```bash
./check_html.py -H example.com
```

---

# ⭐ **Suite Overview (Markdown)**

```markdown
## Suite Overview

NMS_Tools is a collection of deterministic, audit‑transparent monitoring tools used across Linktech Engineering infrastructure.  
Each tool follows the same engineering principles:

- Predictable, reproducible behavior  
- Strict output contracts  
- Noise‑free CLI design  
- Clear separation between human and machine output modes  
- Minimal external dependencies  
- Compatibility with Nagios/Icinga and standalone system use  

Current tools in the suite:

- **check_cert.py** — TLS certificate inspection and policy enforcement  
- **check_html.py** — HTTP/HTTPS inspection and content‑validation  

Additional tools will be added as the suite evolves.  
See `docs/roadmap.md` for planned enhancements.

## Contributing

Contributions are welcome.  
All tools in the suite follow the same design principles:

- Deterministic behavior  
- Clear, documented output modes  
- Minimal dependencies  
- Operator‑grade clarity  
- Stable JSON schemas  

Before submitting a pull request:

1. Review the existing documentation in `docs/`  
2. Ensure new code follows the deterministic engineering model  
3. Include or update documentation for any new flags, behaviors, or metadata  
4. Keep CLI help output clean, grouped, and noise‑free  
5. Maintain compatibility with Python 3.6+  

For major changes, open an issue first to discuss the design and approach.
