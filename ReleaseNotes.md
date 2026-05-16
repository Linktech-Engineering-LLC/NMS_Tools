# Release Notes

## Release v1.0.0 — Initial Stable Release
NMS_Tools v1.0.0 is the first full, stable release of the suite.
This version establishes the complete toolset, unified installer, packaging workflow, and deterministic runtime environment that define the project going forward.

### Included Tools
This release includes all five core monitoring and inspection utilities:

* check_cert — TLS certificate inspection and expiration monitoring
* check_html — Deterministic HTTP/HTTPS content validation
* check_interfaces — Network interface state and configuration inspection
* check_ports — Port and service availability validation
* check_weather — Deterministic weather client for monitoring pipelines

Each tool produces predictable, machine‑readable output suitable for Nagios, dashboards, and automation.

### Suite‑Level Features

* **Unified installer** (<install.sh>) for consistent deployment
* **Environment validation** (<validate_env.py>) to ensure deterministic operation
* **Deterministic vendor library build** included in the installation workflow
* **Version bumping** integrated into the installer
* **Support for installing tools individually or as a complete suite**

### Packaging

* Added **DEB** packaging for Debian/Ubuntu
* Added **RPM** packaging for Fedora, openSUSE, and RHEL‑based systems
* Packages install cleanly into standard system paths
* Packaging workflow validated and included in CI

### Documentation

* New **suite‑level README.md* describing tools, packaging, installation, and philosophy
* New **Installation.md** documenting the unified installer and environment validation
* Per‑tool READMEs updated and aligned with suite identity

### Build & CI

* GitHub Actions workflows validated
* Nightly build pipeline green
* Packaging build pipeline green
* Dashboard placeholder established for GitHub Pages