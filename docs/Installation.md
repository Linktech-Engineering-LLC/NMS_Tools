# Installation Guide — NMS_Tools Monitoring Suite

**Suite:** NMS_Tools Monitoring Suite
**Maintainer:** Leon McClatchey, Linktech Engineering LLC
**Document Type:** Installation Guide
**Last Updated:** 2026‑08‑30

## Table of Contents
1. [Overview](#1-overview)
2. [Prerequisites](#2-prerequisites)
3. [Download & Installation](#3-download--installation)
4. [Deployment](#4-deployment)
5. [Nagios Integration](#5-nagios-integration)
6. [NRPE Integration](#6-nrpe-integration)
7. [Logging Setup](#7-logging-setup)
8. [SELinux Notes](#8-selinux-notes-rhelbased-systems)
9. [Hostname Resolution Requirement](#9-hostname-resolution-requirement)
10. [File Permissions](#10-file-permissions)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Overview
NMS_Tools is distributed as a set of **frozen binaries** packaged in RPM, DEB, TGZ, and ZIP formats.
All Python dependencies (cryptography, pysnmp, psutil, internal modules) are bundled inside each binary — **no Python installation is required** on the target host.

This document describes installation, deployment, Nagios/NRPE integration, logging setup, SELinux considerations, and troubleshooting for all NMS_Tools binaries.

Individual tools (e.g., `check_cert`, `check_html`, `check_interfaces`) include their own Verification sections but share the same installation model.

---

## 2. Prerequisites

### Hostname Resolution
All NMS_Tools binaries require the `-H` target to be resolvable via DNS or `/etc/hosts`.

### SNMP Access (for SNMP‑based tools)
* SNMPv2c community string
* Device must expose IF‑MIB

### Monitoring Platform (optional)
Nagios, Icinga, or any Nagios‑compatible system

### Python (development only)
Python is not required for running frozen binaries.
It is only required if you are modifying or building the tools from source.

---

## 3. Download & Installation

NMS_Tools binaries are distributed in multiple formats.

### Install via RPM (RHEL / Rocky / Alma / Fedora)

```bash
sudo rpm -ivh nms_tools-<version>.rpm
```

### Install via DEB (Debian / Ubuntu)

```bash
sudo dpkg -i nms_tools_<version>.deb
```

### Install via TGZ (generic Linux)

```bash
tar xvf nms_tools-<version>.tgz
sudo cp nms_tools/bin/* /usr/local/bin/
```

### Install via ZIP (generic)

```bash
unzip nms_tools-<version>.zip
sudo cp nms_tools/bin/* /usr/local/bin/
```

After installation, all tools will be available as binaries:
check_cert
check_html
check_interfaces
check_dns
check_http
check_process
check_storage
...

---

## 4. Deployment
### Standalone Execution
Run any tool directly:
```bash
check_cert -H example.com
check_html -H https://example.com
check_interfaces -H localhost
```

### Nagios Plugin Directory
Copy or symlink binaries into your Nagios plugin directory:
```bash
# Copy
sudo cp check_* /usr/local/nagios/libexec/

# Or symlink
sudo ln -s /usr/local/bin/check_cert /usr/local/nagios/libexec/check_cert
sudo ln -s /usr/local/bin/check_html /usr/local/nagios/libexec/check_html
sudo ln -s /usr/local/bin/check_interfaces /usr/local/nagios/libexec/check_interfaces
```

Ensure correct permissions:
```bash
sudo chown nagios:nagios /usr/local/nagios/libexec/check_*
sudo chmod 755 /usr/local/nagios/libexec/check_*
```

Plugin directory may vary (e.g., `/usr/lib64/nagios/plugins/` on RHEL).

---

## 5. Nagios Integration

### Command Definitions

Add to `commands.cfg`:

```cfg
define command {
    command_name    check_interfaces
    command_line    $USER1$/check_interfaces -H $HOSTADDRESS$ -C $ARG1$
}

define command {
    command_name    check_interfaces_status
    command_line    $USER1$/check_interfaces -H $HOSTADDRESS$ -C $ARG1$ --status $ARG2$
}

define command {
    command_name    check_interfaces_targeted
    command_line    $USER1$/check_interfaces -H $HOSTADDRESS$ -C $ARG1$ --ifaces "$ARG2$"
}
```

### Service Definitions

```cfg
define service {
    use                     generic-service
    host_name               switch01
    service_description     Interface Status
    check_command           check_interfaces!public
}

define service {
    use                     generic-service
    host_name               switch01
    service_description     Uplink Speed
    check_command           check_interfaces_status!public!linkspeed
}

define service {
    use                     generic-service
    host_name               switch01
    service_description     Core Uplinks
    check_command           check_interfaces_targeted!public!GigabitEthernet0/1,GigabitEthernet0/2
}
```

---

## 6. NRPE Integration

### On the remote Linux host:
Add to `/etc/nrpe.cfg`:

```cfg
command[check_local_interfaces]=/usr/local/nagios/libexec/check_interfaces -H localhost
```

### On the Nagios server:
```cfg
define service {
    use                     generic-service
    host_name               linux-server01
    service_description     Local Interfaces
    check_command           check_nrpe!check_local_interfaces
}
```

---

## 7. Logging Setup
Logging is **opt‑in**:

```bash
check_interfaces -H switch01 -C public -v --log-dir /var/log/nms_tools
```

Ensure directory exists:
```bash
sudo mkdir -p /var/log/nms_tools
sudo chown nagios:nagios /var/log/nms_tools
```

---

## 8. SELinux Notes (RHEL‑based Systems)

If SELinux blocks execution:
```bash
sudo chcon -t nagios_unconfined_plugin_exec_t /usr/lib64/nagios/plugins/check_*
```

---

## 9. Hostname Resolution Requirement

All NMS_Tools binaries that accept `-H` require the hostname to be resolvable.

If the hostname cannot be resolved:
* The tool fails fast
* No network operations occur
* Nagios mode returns: ```UNKNOWN - Hostname resolution failed for '<host>'```

---

## 10. File Permissions

| Path | Owner | Mode | Purpose |
| --- | --- | --- | --- |
| ``/usr/local/nagios/libexec/check_*`` | nagios:nagios | 755 | Plugin executables |
| ``/var/log/nms_tools/`` | nagios:nagios | 755 | Log directory |

---

## 11. Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| ``UNKNOWN ``- ``Hostname ``resolution ``failed`` | DNS or /etc/hosts issue | Fix hostname resolution |
| ``CRITICAL ``- ``remote ``host ``requires ``SNMP ``community ``string`` | Missing ``-C`` | Add ``-C ``<community>`` |
| No output | Binary not executable | ``chmod ``755 ``check_*`` |
| Permission denied (logs) | Log directory not writable | ``chown ``nagios:nagios ``/var/log/nms_tools`` |
