# Installation

`check_weather.py` is part of the NMS_Tools suite and follows the same deterministic, operator‑grade installation pattern as the other plugins. The tool is intentionally lightweight: one Python file, one dependency, and no hidden runtime requirements.

---

## 1. Platform Requirements

- Python **3.6 or newer**
- Linux server used for Nagios/Icinga plugin execution
- Outbound HTTPS allowed to:
  - `https://api.open-meteo.com` (forecast provider)
  - `https://geocoding-api.open-meteo.com` (location resolver)
  - `https://api.zippopotam.us` (ZIP code resolver)

The plugin performs no local caching and writes no files.

---

## 2. Install the Only Dependency

The plugin uses the `requests` library for HTTP calls.

### Install via pip (recommended)

```bash
pip install requests
```

### Install via OS package manager
*RHEL / CentOS Stream / Fedora*

```bash
dnf install python3-requests
```

### openSUSE Leap / Tumbleweed / SLES

```bash
zypper install python3-requests
```

### Install via RPM (offline or controlled environments)
If your environment uses RPM‑based artifact deployment:

```bash
rpm -ivh python3-requests-*.rpm
```

(Ensure the package matches your distribution’s Python version.)

## 3. Deploy the Script
Copy the plugin into your monitoring plugins directory:

```bash
cp check_weather.py /usr/lib/nagios/plugins/
chmod 755 /usr/lib/nagios/plugins/check_weather.py
```

For Icinga 2 on RHEL‑based systems:

```bash
install -m 755 check_weather.py /usr/lib64/nagios/plugins/
```

For SUSE‑based systems (Leap / SLES):

```bash
install -m 755 check_weather.py /usr/lib/nagios/plugins/
```

## 4. SELinux Considerations

If SELinux is enforcing, ensure the monitoring engine can make outbound HTTPS requests.

Depending on your environment’s restrictions, you may need to:

* Allow outbound network access for the Nagios/Icinga process
* Create a targeted policy module if your security baseline requires it

No SELinux changes are required on permissive systems.

## 5. Validate the Installation

Run a simple test:

```bash
check_weather.py -l "St John, KS"
```

Expected behavior:

* A single‑line Nagios/Icinga status output
* Clean perfdata fields
* No verbose output unless -v is used

Verbose mode (-v) includes resolver details, provider metadata, and JSON output.

## 6. Additional Documentation

* Usage.md — CLI usage, examples, and threshold configuration
* Operation.md — resolver logic, provider behavior, and error handling
* Metadata_Schema.md — JSON schema for verbose mode output