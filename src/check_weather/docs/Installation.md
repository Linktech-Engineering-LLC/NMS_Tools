# Installation

**Part of:** NMS_Tools Monitoring Suite  
**Script:** export_icons.py  
**Version:** 3.0.0  
**Author:** Leon McClatchey, Linktech Engineering LLC  
**License:** MIT  
**Last Updated:** 2026‑08‑16

## Table of Contents
1. [Platform Requirements](#1-platform-requirements)
2. [Install the Frozen Binary](#2-install-the-frozen-binary)
  * [Nagios (RHEL / CentOS / Fedora)](#nagios-rhel--centos--fedora)
  * [Nagios (Debian / Ubuntu)](#nagios-debian--ubuntu)
  * [Icinga 2 (RHEL‑based)](#icinga-2-rhelbased)
  * [Icinga 2 (SUSE‑based)](#icinga-2-susebased)
  * [Custom plugin directory](#custom-plugin-directory)
3. [SELinux Considerations](#3-selinux-considerations)
4. [Validate the Installation](#4-validate-the-installation)
5. [Cache Directories](#5-cache-directories)
6. [Logging Directory (Optional)](#6-logging-directory-optional)
7. [Additional Documentation](#7-additional-documentation)

## 1. Platform Requirements

* Linux server used for Nagios/Icinga plugin execution
* Outbound HTTPS allowed to:
  * `https://api.open-meteo.com` (forecast provider)
  * `https://geocoding-api.open-meteo.com` (location resolver)
  * `https://api.zippopotam.us` (ZIP resolver)
  * `https://api.weather.gov` (NWS provider)

`check_weather` is a **frozen binary**.

It has no runtime Python dependency and requires no virtual environment.

All PythonTools modules are embedded inside the binary.

## 2. Install the Frozen Binary

Place the binary into your monitoring plugins directory.

### Nagios (RHEL / CentOS / Fedora)

```bash
install -m 755 check_weather /usr/lib64/nagios/plugins/
```

### Nagios (Debian / Ubuntu)

```bash
install -m 755 check_weather /usr/lib/nagios/plugins/
```

### Icinga 2 (RHEL‑based)

```bash
install -m 755 check_weather /usr/lib64/nagios/plugins/
```

### Icinga 2 (SUSE‑based)

```bash
install -m 755 check_weather /usr/lib/nagios/plugins/
```

### Custom plugin directory

```bash
install -m 755 check_weather /opt/monitoring/plugins/
```

## 3. SELinux Considerations

If SELinux is enforcing, ensure the monitoring engine can make outbound HTTPS requests.

Depending on your environment’s restrictions, you may need to:

* allow outbound network access for the Nagios/Icinga process
* create a targeted policy module if your baseline requires it

No SELinux changes are required on permissive systems.

## 4. Validate the Installation

Run a simple test:

```bash
check_weather -l "St John, KS"
```

Expected behavior:
* single‑line Nagios/Icinga status output
* clean perfdata fields
* no verbose output unless -v is used
* Verbose mode (-v) includes:
* resolver details
* provider metadata
* cache metadata
* JSON output (if --json is used)

## 5. Cache Directories

check_weather automatically creates and manages two cache directories:

```Code
~/.cache/nms_tools/weather/
~/.cache/nms_tools/location/
```

These are created on first run.
No manual setup is required.

## 6. Logging Directory (Optional)

Logging is disabled unless --log-dir is provided.

Example:

```bash
check_weather -l "St John, KS" --log-dir /var/log/nms_tools/
```

Log files follow the unified NMS_Tools logging model:
* rotation
* archive
* max size
* deterministic formatting

See **Logging.md** for details.

## 7. Additional Documentation
* [Usage.md](Usage.md) — CLI usage, examples, threshold configuration
* [Operation.md](Operation.md) — resolver logic, provider behavior, error handling
* [Provider_Architecture.md](Provider_Architecture.md) — provider registry contract and fetch logic
* [Metadata_Schema.md](Metadata_Schema.md) — JSON schema for all output modes
* [Enforcement.md](Enforcement.md) — Nagios/Icinga rules, severity model, deterministic guarantees
