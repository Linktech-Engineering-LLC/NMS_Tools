# Installation.md — Deployment & Nagios Integration

## Prerequisites

**Resolvable hostname** — All NMS_Tools scripts require the -H target to be resolvable via DNS or /etc/hosts.

| Requirement |	Details |
| :--- | :--- |
| Python |	3.6 or later |
| pysnmp |	Required for remote SNMP interface inspection |
| psutil |	Required for local interface inspection |
| SNMP access |	SNMPv2c community string for each remote target device |
| Nagios |	Nagios, Icinga, or compatible monitoring platform (optional) |

**Note:** pysnmp and psutil are both required because the tool imports them at startup. Even if you only use local mode or only use SNMP mode, both packages must be installed.
---

## Download

`check_interfaces.py` is distributed as part of the **NMS_Tools** suite.

### Clone the Repository

```bash
git clone https://github.com/Linktech-Engineering-LLC/NMS_Tools.git
cd NMS_Tools/check_interfaces
```

### Download a Single Tool

If you only need `check_interfaces`, you can download the `check_interfaces/` directory from the repository without cloning the full suite.

---

## Install Dependencies

check_interfaces.py requires two external Python packages:

* pysnmp — for SNMP interface polling
* psutil — for local host interface inspection

Install both:

```bash
pip install pysnmp psutil
```

Or, if your environment requires a user‑level install:

```bash
pip install --user pysnmp psutil
```

Optional: Install using the provided requirements.txt
If you cloned the full NMS_Tools repository, you may install dependencies using the tool‑level requirements file:

```bash
pip install -r requirements.txt
```

Verify installation

```bash
python3 -c "import pysnmp, psutil; print('pysnmp:', pysnmp.__version__, 'psutil:', psutil.__version__)"
```

---

## Deployment

### Standalone

Run directly from the cloned repository or any directory:

```bash
chmod +x check_interfaces.py
./check_interfaces.py -H localhost -v
```

### Nagios Plugin Directory

Copy or symlink the tool into your Nagios plugin directory:

```bash
# Copy
cp check_interfaces.py /usr/local/nagios/libexec/

# Or symlink
ln -s /path/to/NMS_Tools/check_interfaces/check_interfaces.py /usr/local/nagios/libexec/check_interfaces.py
```

Ensure the file is executable and owned by the Nagios user:

```bash
chmod +x /usr/local/nagios/libexec/check_interfaces.py
chown nagios:nagios /usr/local/nagios/libexec/check_interfaces.py
```

> **Note:** Your plugin directory may differ depending on distribution and installation method (e.g., `/usr/lib64/nagios/plugins/` on RHEL‑based systems).

---

## Verify Installation

### Local Host

```bash
./check_interfaces.py -H localhost -v
```

Expected: verbose output listing all local interfaces with operational status.

### Remote Host

```bash
./check_interfaces.py -H switch01.example.com -C public -v
```

Expected: verbose output listing all SNMP‑discovered interfaces on the remote device.

### Version Check

```bash
./check_interfaces.py -V
```

---

## Nagios Integration

### Command Definition

Add the following command definition to your Nagios configuration (typically `commands.cfg` or an equivalent object file):

```cfg
# Basic interface check
define command {
    command_name    check_interfaces
    command_line    $USER1$/check_interfaces.py -H $HOSTADDRESS$ -C $ARG1$
}

# Interface check with attribute selection
define command {
    command_name    check_interfaces_status
    command_line    $USER1$/check_interfaces.py -H $HOSTADDRESS$ -C $ARG1$ --status $ARG2$
}

# Interface check with specific interfaces
define command {
    command_name    check_interfaces_targeted
    command_line    $USER1$/check_interfaces.py -H $HOSTADDRESS$ -C $ARG1$ --ifaces "$ARG2$"
}
```

### Service Definition Examples

```cfg
# Monitor all interfaces on a switch
define service {
    use                     generic-service
    host_name               switch01
    service_description     Interface Status
    check_command           check_interfaces!public
}

# Monitor link speed on uplinks
define service {
    use                     generic-service
    host_name               switch01
    service_description     Uplink Speed
    check_command           check_interfaces_status!public!linkspeed
}

# Monitor specific interfaces
define service {
    use                     generic-service
    host_name               switch01
    service_description     Core Uplinks
    check_command           check_interfaces_targeted!public!GigabitEthernet0/1,GigabitEthernet0/2
}
```

### NRPE (Remote Execution)

For monitoring the local interfaces of a remote Linux host via NRPE, add the following to the NRPE configuration on the target host:

```cfg
command[check_local_interfaces]=/usr/local/nagios/libexec/check_interfaces.py -H localhost
```

Then define the service on the Nagios server:

```cfg
define service {
    use                     generic-service
    host_name               linux-server01
    service_description     Local Interfaces
    check_command           check_nrpe!check_local_interfaces
}
```

---

## Logging Setup

Logging is **opt‑in** and **disabled in default (Nagios) mode**. To enable logging for verbose or JSON output modes, specify a log directory:

```bash
./check_interfaces.py -H switch01 -C public -v --log-dir /var/log/nms_tools
```

Ensure the log directory exists and is writable by the executing user:

```bash
mkdir -p /var/log/nms_tools
chown nagios:nagios /var/log/nms_tools
```

Log rotation is handled internally via `--log-max-mb` (default: 50 MB).

---

## File Permissions Summary

| Path                                         | Owner         | Mode  | Purpose                        |
|----------------------------------------------|---------------|-------|--------------------------------|
| `check_interfaces.py`                        | `nagios:nagios`| `755` | Plugin executable              |
| `/var/log/nms_tools/` (if logging enabled)   | `nagios:nagios`| `755` | Log output directory           |

---

## Troubleshooting

| Symptom                                      | Cause                                          | Fix                                           |
|----------------------------------------------|-------------------------------------------------|-----------------------------------------------|
| `ModuleNotFoundError: No module named 'pysnmp'` | pysnmp not installed                          | `pip install pysnmp`                          |
| `CRITICAL - remote host requires SNMP community string` | Missing `-C` flag for remote host    | Add `-C <community>`                         |
| `UNKNOWN - ...`                              | Host unreachable, DNS failure, or invalid args  | Verify hostname, network path, and arguments  |
| Permission denied on log directory           | Log directory not writable by executing user    | `chown nagios:nagios /var/log/nms_tools`      |
