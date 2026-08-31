# check_html.py — Installation Guide

**Part of:** NMS_Tools Monitoring Suite  
**Document:** Installation Guide  
**Author:** Leon McClatchey, Linktech Engineering LLC  
**License:** MIT  
**Requires:** Python 3.12+  
**Last Updated:** 2026‑08‑17

## Table of Contents

1. [Overview](#1-overview)
2. [Requirements](#2-requirements)
3. [Install Dependencies](#3-install-dependencies)
4. [Clone the Repository](#4-clone-the-repository)
5. [Make the Tool Executable](#5-make-the-tool-executable)
6. [Nagios Plugin Installation](#6-nagios-plugin-installation)
7. [Test the Installation](#7-test-the-installation)

---

## 1. Overview

check_html.py is a deterministic HTTP/HTTPS inspection and content‑validation tool.
It requires only a standard Python 3 environment and the requests library.

This document describes how to install and run the tool on Linux systems, including optional Nagios plugin deployment.

## 2. Requirements

- Python **3.6 or newer**
- Linux environment (Ubuntu, Debian, CentOS, RHEL, Rocky, Alma, etc.)
- pip available for installing Python packages
- Optional: Nagios or Icinga for monitoring integration

A virtual environment is not required, but may be used if preferred.

## 3. Install Dependencies

check_html.py uses only Python standard library modules.

There are no external dependencies and no requirements.txt for this tool.

Nothing needs to be installed via pip.

## 4. Clone the Repository

```bash
git clone https://github.com/Linktech-Engineering-LLC/NMS_Tools.git
cd NMS_Tools/check_html
```

## 5. Make the Tool Executable

```bash
chmod +x check_html.py
```

You can now run it directly:

```bash
./check_html.py -H example.com
```

## 6. Nagios Plugin Installation

Copy the tool into your Nagios plugin directory:

```bash
sudo cp check_html.py /usr/local/nagios/libexec/
sudo chmod 755 /usr/local/nagios/libexec/check_html.py
```

Define a Nagios command:

```Code
define command {
    command_name    check_html
    command_line    /usr/local/nagios/libexec/check_html.py -H $ARG1$
}
```

Example service definition:

```Code
define service {
    use                 generic-service
    host_name           example.com
    service_description HTML Check
    check_command       check_html!example.com
}
```

## 7. Test the Installation

### Basic HTTP check

```bash
./check_html.py -H example.com
```

### HTTPS check

```bash
./check_html.py -H example.com --https
```

### Verbose mode

```bash
./check_html.py -H example.com -v
```

### JSON mode

```bash
./check_html.py -H example.com -j
```

A successful run should produce output similar to:

```Code
OK - 200 OK (text/html)
```

Your installation is complete.