# NMS_Tools  
Deterministic, operator‑grade monitoring tools for Linux and Nagios environments.

![Suite](https://img.shields.io/badge/Linktech_Engineering-Tools_Suite-8A2BE2?style=for-the-badge)
![Status](https://img.shields.io/badge/status-active-brightgreen?style=for-the-badge)
![License](https://img.shields.io/badge/license-MIT-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/python-3.8%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/platform-linux-lightgrey?style=for-the-badge&logo=linux&logoColor=white)
![Nightly Build](https://github.com/Linktech-Engineering-LLC/NMS_Tools/actions/workflows/nightly.yml/badge.svg)
![Build Packages](https://github.com/Linktech-Engineering-LLC/NMS_Tools/actions/workflows/build-packages.yml/badge.svg)


NMS_Tools is a suite of deterministic, operator‑grade monitoring tools designed for Nagios, automation pipelines, and Linux‑based operational workflows.  
Each tool is built with:

- deterministic behavior  
- reproducible output  
- zero side effects in Nagios mode  
- operator‑grade logging  
- consistent architecture and documentation  

The suite is intentionally modular — each tool is self‑contained, predictable, and easy to deploy.

## 🔧 Deterministic Vendor System
NMS_Tools uses a fully deterministic, offline‑capable vendor system.
All third‑party Python dependencies are vendored into:

`libs/`

This ensures:

* reproducible builds
* no reliance on system Python packages
* consistent behavior across distributions
* deterministic Nagios execution

Vendor contents are generated from:

`requirements_vendor.txt`
`tools/vendor_builder.py`

To rebuild the vendor directory:

`source .venv/bin/activate`
`pip install -r requirements_vendor.txt`
`tools/vendor_builder.py`

## 📦 Runtime Dependencies
The suite has a minimal, deterministic dependency footprint:

```code
cryptography
easysnmp
psutil
python-dateutil
requests
six
typing_extensions
urllib3
idna
charset-normalizer
certifi
```

These are the only packages vendored into `libs/`.

## 🛡 Minimum Version Guardrails 

Each tool enforces:

* **Python 3.8+**
* deterministic hostname resolution
* local vs remote mode detection
* SNMP timeout guardrails
* logging directory validation
* Nagios‑safe execution (no side effects unless logging is explicitly enabled)

This ensures predictable, operator‑grade behavior in all environments.

## 🧰 Management Tools
The suite includes several management utilities:

```bash
tools/
    vendor_builder.py     # deterministic vendor system
    version_stamp.py      # build-time version injection
    validate_env.py       # environment guardrails
```
These tools ensure reproducible builds and consistent packaging.

## 📦 Packaging & Installation

NMS_Tools ships with full Linux-native packaging support, including:

- **DEB packages** (Debian / Ubuntu)
- **RPM packages** (RHEL / Rocky / Alma / Fedora / openSUSE)
- **Man pages** for every tool
- **Build scripts** for local packaging

All packaging assets live under:

```
packaging/
    debian/     # DEB metadata
    rpm/        # RPM spec file
    build_deb.sh
    build_rpm.sh
    build_all.sh
```

During packaging, all Markdown man pages in `man/*.md` are automatically
converted to groff (`.1`, `.7`) and installed into the appropriate man
directories. No manual groff editing is required.

### Install (DEB)

```
sudo dpkg -i nms-tools_<version>_all.deb
```

### Install (RPM)

```
sudo rpm -ivh nms_tools-<version>.noarch.rpm
```

---

## 📘 Man Pages

NMS_Tools includes full operator-grade man pages for every tool.

After installation:

```
man check_ports
man check_weather
man check_cert
man check_html
man check_interfaces
man nms_tools
```

Man page sources live in:

```
man/
    check_ports.1.md
    check_weather.1.md
    check_cert.1.md
    check_html.1.md
    check_interfaces.1.md
    nms_tools.7.md
```

These are automatically converted to groff during packaging.

---

## 🧰 Build From Source

To build both DEB and RPM packages locally:

```
./packaging/build_all.sh
```

Or individually:

```
./packaging/build_deb.sh
./packaging/build_rpm.sh
```

This generates:

- `.deb` packages in the project root  
- `.rpm` packages under `~/rpmbuild/RPMS/`  

---

## Versioning and Build Types

NMS_Tools uses automatic version stamping to ensure every build is traceable,
reproducible, and uniquely identifiable.

### Base Version
The base version is defined in:

- `packaging/debian/control` (for DEB builds)
- `packaging/rpm/nms_tools.spec` (for RPM builds)

Example:

Version: 1.0.0

Code

### Push Builds (Standard)
When building normally (e.g., `make packages` or CI push builds), the version
remains the base version:

1.0.0

Code

### Nightly Builds
Nightly builds automatically append a date and commit hash:

1.0.0+20260421.git3f2a9c

Code

This provides:

- exact build date  
- exact commit reference  
- deterministic reproducibility  

Nightly builds are triggered by GitHub Actions and set:

NIGHTLY=1

Code

### Version Banner in Man Page
The suite-level man page (`nms_tools.7`) includes a version banner injected at
build time:

Version: 1.0.0+20260421.git3f2a9c
Build Type: Nightly
Build Date: 20260421
Commit: 3f2a9c

Code

To preview the banner locally:

make preview-man

---

# Available Tools

### ✔ **check_ports**  
Deterministic multi‑port TCP connectivity checker.  
Deterministic TCP availability checker supporting explicit ports (-p) and service names (-s).
Provides single‑service and single‑port Nagios output, verbose diagnostics, JSON mode, and optional operator‑grade logging.

Typical usage:

```check_ports.py -H host -s ssh```
```check_ports.py -H host -p 443```
```check_ports.py -H host -s https,ssh -p 2222```

[check_ports/README.md](check_ports/README.md)

### ✔ **check_weather**  
Weather condition evaluator with rule‑based enforcement.
Uses **requests** and a deterministic provider registry.

Typical usage:

```check_weather.py --location "St John, KS"```
```check_weather.py --location 67576 --json```

[check_weather/README.md](check_weather/README.md)

### ✔ **check_cert**  
Certificate expiration and metadata checker.
Uses the **cryptography** library for deterministic certificate parsing, SAN/issuer extraction, and expiration evaluation.

Typical usage:

```check_cert.py -H example.com```
```check_cert.py -H api.example.com --json```

[check_cert/README.md](check_cert/README.md)

### ✔ **check_html**  
HTML content validator with rule‑based enforcement.
Uses **only Python’s standard library** for deterministic HTTP/HTTPS inspection, backend fingerprinting, and content‑type enforcement.

Typical usage:

```check_html.py -H example.com```
```check_html.py -H example.com --expect-backend nginx```

[check_html/README.md](check_html/README.md)

### ✔ **check_interfaces**  
Network interface state and SNMP‑based status checker.
Uses **local kernel inspection** for local hosts and **easysnmp** for remote hosts.
Provides deterministic admin/oper mapping, JSON output, perfdata, and operator‑grade logging.
Typical usage:

```check_interfaces.py -H switch01```
```check_interfaces.py -H router01 --json```

[check_interfaces/README.md](check_interfaces/README.md)

---

## 🖥 Unified Output Model (All Tools)
All NMS_Tools utilities share a consistent, deterministic output model designed for Nagios, automation pipelines, and operator workflows.

Every tool supports the same four output modes:

### ✔ Nagios Mode (default)

* Single‑line status output
* Includes perfdata when applicable
* No logging or side effects
* Deterministic exit codes (OK/WARNING/CRITICAL/UNKNOWN)

Example:

`OK: all interfaces oper-status | eth0_in_octets=12345c eth0_out_octets=67890c`

### ✔ Verbose Mode (-v)

* Human‑readable, multi‑line diagnostic output
* Includes evaluation details, metadata, and structured summaries
* Logging is allowed if configured

Example:

```bash
Interface Summary (local)
Host: dad (192.168.1.10)
Interfaces: 4
Status Target: oper-status
```

### ✔ JSON Mode (-j)

* Canonical JSON schema
* Stable field ordering
* Suitable for automation, dashboards, and pipelines
* Includes metadata, evaluation results, and normalized structures

Example:

```json
{
  "meta": { "host": "dad", "mode": "local" },
  "interfaces": { ... },
  "status": 0
}
```

### ✔ Quiet Mode (-q)

* Exit code only
* No stdout output
* Useful for shell scripting and conditional logic

## 📝 Logging Model (All Tools)

All tools share the same deterministic logging rules:

* **Logging is disabled in Nagios mode**
  (no side effects, no file writes)
* Logging is enabled only when:
  * --log-dir is explicitly provided
  * The tool is not in Nagios mode
* Log rotation is deterministic and size‑bounded
* Log directories are validated for safety
* Logs are operator‑grade and timestamped

This unified model ensures consistent behavior across the entire suite.

---

# Documentation

Full documentation is available in the `docs/` directory:

- [Documentation Index](docs/index.md)  
- [Installation](docs/installation.md)  
- [Usage](docs/usage.md)  
- [Operation Model](docs/operation.md)  
- [Enforcement Model](docs/enforcement.md)  
- [Metadata Schema](docs/metadata_schema.md)  
- [Roadmap](docs/roadmap.md)  

Each tool also includes its own:

- `README.md` (user‑facing documentation)  
- `FLAGS.md` (internal bitmask flags, if applicable)  

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

# Philosophy

NMS_Tools is built around a few core principles:

- **Determinism** — same input, same output, every time  
- **Operator‑grade clarity** — readable logs, predictable behavior  
- **Zero side effects** — Nagios mode never writes logs or files  
- **Modularity** — each tool is self‑contained  
- **Reproducibility** — consistent architecture across the suite  
- **Transparency** — clear documentation and predictable evaluation rules  

---

# Directory Structure

```
NMS_Tools/
│
├── check_ports/
│   ├── check_ports.py
│   ├── README.md
│   └── FLAGS.md
│
├── check_weather/
│   ├── check_weather.py
│   ├── README.md
│   └── FLAGS.md
│
├── check_cert/
│   ├── check_cert.py
│   └── README.md
│
├── check_html/
│   ├── check_html.py
│   └── README.md
│
├── check_interfaces/
│   ├── check_interfaces.py
│   └── README.md
│
└── docs/
    ├── index.md
    ├── installation.md
    ├── usage.md
    ├── operation.md
    ├── enforcement.md
    ├── metadata_schema.md
    └── roadmap.md
```

---

# Roadmap

See the full roadmap here:  
→ **[docs/roadmap.md](docs/roadmap.md)**

Current roadmap items include:

- Named port support in `check_ports` (e.g., `https` → 443 via `/etc/services`)  
- Flags class rollout to all remaining tools  
- Unified logging lifecycle across the suite  
- Additional operator‑grade documentation  
- Future tool additions (DNS, SSH, HTTP latency, etc.)

---

# License

MIT License — see `LICENSE.md` in the repository root.

## Related Projects (Outside This Repository)

These projects are part of the broader Linktech Engineering ecosystem but are **not** included in the NMS_Tools repository:

- **BotScanner**  
  Deterministic system scanner with reproducible output and operator‑grade logging.  
  https://github.com/Linktech-Engineering-LLC/BotScanner-Community

- **licensegen**  
  Rust‑based deterministic license generator with canonical serialization.  
  https://github.com/Linktech-Engineering-LLC/licensegen

- **rust_logger**  
  Shared Rust logging crate used across multiple Linktech tools.  
  https://github.com/Linktech-Engineering-LLC/rust_logger

- **RunUpdates**  
  Automated source‑file header updater with SPDX and provenance enforcement.  
  https://github.com/Linktech-Engineering-LLC/RunUpdates

These tools follow the same engineering philosophy as NMS_Tools and are often used together in operational environments.
