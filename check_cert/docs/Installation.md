# Installation Guide — `check_cert.py`

This document describes how to install `check_cert.py` in two supported modes:
system‑wide or as a Nagios plugin. Choose the installation path that matches
your operational environment.

---

## 1. Requirements

### Python Version

check_cert.py supports:

* Python 3.6 or newer
* Python 3.6–3.7 require typing_extensions

### Python Packages

Required:

* cryptography
** typing_extensions (only for Python < 3.8)

Install via pip:

```bash
pip install cryptography
pip install typing_extensions   # only for Python < 3.8
```

Or install via your distribution’s package manager:
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

**Optional: Install using the provided requirements.txt**
If you cloned the full NMS_Tools repository, you may install dependencies using the tool‑level requirements file:

```bash
pip install -r requirements.txt
```

## 2. Logging Requirements (Optional)

Logging is enabled only when a log directory is provided:

```Code
--log-dir /path/to/logs
```

If omitted, logging is disabled.

Log rotation is controlled by:

```Code
--log-max-mb SIZE
```

Default: 50 MB

The directory must be writable by the user or service executing the script.

Example:

```bash
mkdir -p /var/log/nms_tools
chmod 755 /var/log/nms_tools
```

## 3. System‑Wide Installation (General Use)

Use this method when you want check_cert available as a normal system tool.

Install
```bash
sudo cp check_cert.py /usr/local/bin/check_cert
sudo chmod 755 /usr/local/bin/check_cert
```

Verify

```bash
check_cert -H example.com
```

This produces a single Nagios‑style status line by default.

## 4. Nagios Plugin Installation (Monitoring Use)
Use this method when Nagios or NRPE will execute the script.

### Install into the Nagios plugin directory

Common paths:

* /usr/lib/nagios/plugins/ (Debian/Ubuntu/openSUSE)
* /usr/lib64/nagios/plugins/ (RHEL/CentOS/Rocky/Alma)

Example:

```bash
sudo cp check_cert.py /usr/lib/nagios/plugins/check_cert
sudo chmod 755 /usr/lib/nagios/plugins/check_cert
sudo chown nagios:nagios /usr/lib/nagios/plugins/check_cert
```

Verify

```bash
/usr/lib/nagios/plugins/check_cert -H example.com
```

Nagios mode always emits a single clean line.

## 5. SELinux Notes (RHEL‑based Systems)
If SELinux blocks execution:

```bash
sudo chcon -t nagios_unconfined_plugin_exec_t /usr/lib64/nagios/plugins/check_cert
```

## 6. Hostname Resolution Requirement

All NMS_Tools plugins that accept -H require the hostname to be resolvable.

If the hostname cannot be resolved:

* The tool fails fast
* No network operations occur
* Nagios mode returns:

```Code
UNKNOWN - Hostname resolution failed for '<host>'
```

## 7. Summary

| Installation Type | Path | Purpose |
| :--- | :--- | :--- |
| System‑wide |	/usr/local/bin/check_cert |	Admin use, scripts, cron |
| Nagios plugin | /usr/lib*/nagios/plugins/check_cert |	Monitoring systems |
| Optional logs | --log-dir /path/to/logs |	Deterministic logging |
