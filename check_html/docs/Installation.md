# check_html.py — Installation Guide

check_html.py is a deterministic HTTP/HTTPS inspection and content‑validation tool.
It requires only a standard Python 3 environment and the requests library.

This document describes how to install and run the tool on Linux systems, including optional Nagios plugin deployment.

## 1. Requirements

- Python **3.6 or newer**
- Linux environment (Ubuntu, Debian, CentOS, RHEL, Rocky, Alma, etc.)
- pip available for installing Python packages
- Optional: Nagios or Icinga for monitoring integration

A virtual environment is not required, but may be used if preferred.

## 2. Install Dependencies

check_html.py uses a single external Python dependency:

```Code 
requests
```

Install it system‑wide or user‑local:

### System‑wide install

```bash
sudo pip3 install requests
```

### User‑local install

```bash
pip3 install --user requests
```

No requirements.txt file is needed for this tool.

## 3. Clone the Repository

```bash
git clone https://github.com/LinktechEngineering/NMS_Tools.git
cd NMS_Tools/check_html
```

## 4. Make the Tool Executable

```bash
chmod +x check_html.py
```

You can now run it directly:

```bash
./check_html.py -H example.com
```

## 5. Optional: Install as a Nagios Plugin

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

## 6. Test the Installation

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