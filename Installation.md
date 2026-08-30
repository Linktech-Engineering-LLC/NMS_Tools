# Installation

**Suite:** NMS_Tools Monitoring Suite
**Maintainer:** Leon McClatchey, Linktech Engineering LLC
**Document Type:** Installation Guide
**Last Updated:** 2026‑08‑30

---

## 📘 Table of Contents
1. [Overview](#1-overview)
2. [Installation Locations](#2-installation-locations)
3. [Prerequisites](#3-prerequisites)
4. [Installing the Full Suite](#4-installing-the-full-suite)
  * [DEB Installation](#deb-installation-debianubuntu)
  * [RPM Installation](#rpm-installation-fedorarhelopensuse)
5. [Installing Individual Tools](#5-installing-individual-tools)
6. [Nightly Builds](#6-nightly-builds)
7. [Uninstallation](#7-uninstallation)
  * [DEB Removal](#deb-removal)
  * [RPM Removal](#rpm-removal)
  * [Manual Binary Removal](#manual-binary-removal)
8. [Notes](#8-notes)

---

## 1. Overview

NMS_Tools is distributed as standalone Linux binaries and native system packages (DEB/RPM).  
No Python runtime is required — each tool is a self‑contained executable built with PyInstaller.

You may install the entire suite or individual tools depending on your environment.

---

## 2. Installation Locations

NMS_Tools binaries may be installed in either of two locations:

### **System‑wide path (default)**  
For general CLI usage, automation, cron jobs, and operator workflows:

[/usr/bin/]

### **Nagios plugin directory**  
For monitoring environments (Nagios, Icinga, Naemon, NRPE, NCPA):

[/usr/local/nagios/libexec/]

Or, optionally, to keep the suite organized:

[/usr/local/nagios/libexec/NMS_Tools/]

All tools are fully Nagios‑compatible and can be used as drop‑in plugins.

---

## 3. Prerequisites

* Linux system (x86_64)
* Standard utilities (bash, coreutils)
* Root/sudo access for system‑wide installation (DEB/RPM)

No Python installation is required.

---

## 4. Installing the Full Suite

### DEB Installation (Debian/Ubuntu)

```bash
sudo dpkg -i nms-tools_<version>.deb
```

### RPM Installation (Fedora/RHEL/openSUSE)

```bash
sudo rpm -i nms_tools-<version>-1.noarch.rpm
```

Packages install all tools into standard system paths:

/usr/bin/check_cert
/usr/bin/check_html
/usr/bin/check_interfaces
/usr/bin/check_ports
/usr/bin/check_weather

---

## 5. Installing Individual Tools
Each tool is also available as a standalone binary.

Download from:

* **Stable releases:**  
  https://github.com/Linktech-Engineering-LLC/NMS_Tools/releases

* **Nightly builds:**
  https://linktech-engineering-llc.github.io/NMS_Tools/

Make the binary executable:

```bash
chmod +x check_cert
```

Install to system path:

```bash
sudo mv check_cert /usr/local/bin/
```

Or install as a Nagios plugin:

```bash
sudo mv check_cert /usr/local/nagios/libexec/
```

Or into a dedicated suite folder:

```bash
sudo mkdir -p /usr/local/nagios/libexec/NMS_Tools
sudo mv check_cert /usr/local/nagios/libexec/NMS_Tools/
```

Repeat for any tool you want to install individually.

---

## 6. Nightly Builds

Nightly builds include:

* Latest binaries
* DEB/RPM packages
* Checksums
* Build metadata

Available at:

https://linktech-engineering-llc.github.io/NMS_Tools/

---

## 7. Uninstallation

### DEB Removal

```bash
sudo dpkg -r nms-tools
```

### RPM Removal

```bash
sudo rpm -e nms_tools
```

### Manual binary removal

System‑wide:

```bash
sudo rm /usr/local/bin/check_*
```

Nagios plugin directory:

```bash
sudo rm /usr/local/nagios/libexec/check_*
```

Or:

```bash
sudo rm -r /usr/local/nagios/libexec/NMS_Tools/
```

---

## 8. Notes

* All binaries are deterministic and self‑contained.
* No Python environment or vendor library is required.
* Tools may be installed individually or as a suite.
* Nagios plugin installation is fully supported.
