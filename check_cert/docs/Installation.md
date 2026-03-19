# Installation Guide — `check_cert.py`

This document describes how to install `check_cert.py` in two supported modes:
system‑wide or as a Nagios plugin. Choose the installation path that matches
your operational environment.

---

## 1. Requirements

### Python
- Python **3.6 or newer**

### Python Packages
- `cryptography`

Install via `pip` (recommended):

```bash
pip install cryptography
```

Or via your distribution’s package manager:

**openSUSE / SLES**
```bash
sudo zypper install python3-cryptography
```

**RHEL / CentOS / Rocky / Alma**
```bash
sudo yum install python3-cryptography
```

**Fedora**
```bash
sudo dnf install python3-cryptography
```

**Ubuntu / Debian**
```bash
sudo apt install python3-cryptography
```

---

## 2. System‑Wide Installation (General Use)

Use this method when you want `check_cert` available as a normal system tool.

### Install

```bash
sudo cp check_cert.py /usr/local/bin/check_cert
sudo chmod 755 /usr/local/bin/check_cert
```

### Verify

```bash
check_cert -H example.com
```

This produces a single Nagios‑style status line by default.

---

## 3. Nagios Plugin Installation (Monitoring Use)

Use this method when Nagios or NRPE will execute the script.

### Install into the Nagios plugin directory

Common paths:

- `/usr/lib/nagios/plugins/` (Debian/Ubuntu/openSUSE)
- `/usr/lib64/nagios/plugins/` (RHEL/CentOS/Rocky/Alma)

Example:

```bash
sudo cp check_cert.py /usr/lib/nagios/plugins/check_cert
sudo chmod 755 /usr/lib/nagios/plugins/check_cert
sudo chown nagios:nagios /usr/lib/nagios/plugins/check_cert
```

### Verify

```bash
/usr/lib/nagios/plugins/check_cert -H example.com
```

---

## 4. SELinux Notes (RHEL‑based Systems)

If SELinux blocks execution:

```bash
sudo chcon -t nagios_unconfined_plugin_exec_t /usr/lib64/nagios/plugins/check_cert
```

---

## 5. Summary

| Installation Type | Path | Purpose |
|-------------------|-------|---------|
| System‑wide | `/usr/local/bin/check_cert` | Admin use, scripts, cron |
| Nagios plugin | `/usr/lib*/nagios/plugins/check_cert` | Monitoring systems |

---
