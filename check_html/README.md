# check_html — HTTP/HTTPS Inspection & Content Validation Tool
![Python Version](https://img.shields.io/badge/python-3.6%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-stable-brightgreen)
![Nagios Plugin](https://img.shields.io/badge/Nagios-plugin-success)
![NMS_Tools](https://img.shields.io/badge/NMS_Tools-check__html-blueviolet)

`check_html.py` is a deterministic HTTP/HTTPS inspection tool designed for monitoring environments.  
It performs lightweight endpoint validation, backend fingerprinting, and content checks while producing clean, predictable output across JSON, verbose, and Nagios modes.

---

## Features

- HTTP/HTTPS request pipeline with TLS awareness  
- Status code validation  
- Content-Type validation  
- Optional HTML body presence validation  
- Backend fingerprinting (server header, content type, HTML detection)  
- Deterministic JSON output for automation  
- Clean, noise-free CLI parser  
- Nagios-compatible exit codes and perfdata  
- Fast, dependency-light implementation  

---

## Installation

`check_html.py` requires only:

- Python 3.6+
- `requests` library

Install dependencies:

pip install requests


The tool is standalone and does not require system packages or external binaries.

---

## Usage

Basic usage:

```bash
./check_html.py -H <host>
```


Common options:

-H, --host           Target hostname or IP
-p, --port           Port (default: 80 or 443 based on scheme)
-s, --ssl            Force HTTPS
-j, --json           Output JSON
-v, --verbose        Verbose diagnostic output
--timeout            Connection timeout (default: 5s)
--expect-status      Expected HTTP status code (e.g., 200)
--expect-type        Expected Content-Type (e.g., text/html)
--require-html       Require HTML content in the response body


Nagios mode (default) produces a single deterministic line:

OK - 200 OK (text/html) | time=0.0012s;;;0 size=331B;;;0


---

## Output Modes

### Nagios Mode (default)
- One-line summary  
- Status code + content type  
- Perfdata includes:
  - response time  
  - body size  

### JSON Mode (`-j`)
Machine-readable structured output including:

- status code  
- headers  
- content type  
- HTML detection  
- backend fingerprint  
- timing metrics  
- enforcement results  

### Verbose Mode (`-v`)
Human-readable diagnostic report including:

- connection details  
- TLS session (if HTTPS)  
- headers  
- content type  
- HTML detection  
- enforcement summary  

---

## Enforcement Model

`check_html.py` applies lightweight validation rules:

- **Status Code Check** — validates against `--expect-status`  
- **Content-Type Check** — validates against `--expect-type`  
- **HTML Presence Check** — validates HTML body when `--require-html` is used  
- **Backend Check** — fingerprints server backend and applies optional rules  

Failures are categorized as:

- **CRITICAL** — hard failures  
- **WARNING** — soft failures  
- **OK** — all rules passed  

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | OK |
| 1 | WARNING |
| 2 | CRITICAL |
| 3 | UNKNOWN |

---

## License

This tool is part of the **NMS_Tools** suite.  
See the root project for licensing, documentation, and contributor guidelines.
