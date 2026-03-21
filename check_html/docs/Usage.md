# check_html.py — Usage Guide

check_html.py is a deterministic HTTP/HTTPS inspection and content‑validation tool.
It supports JSON, verbose, and Nagios output modes, and is designed for operators, automation systems, and monitoring platforms.

This guide describes the command‑line interface, output modes, examples, and Nagios integration.

## 1. Basic Usage

### HTTP check

```bash
./check_html.py -H example.com
```
### HTTPS check

```bash
./check_html.py -H example.com --https
```

### Explicit port

```bash
./check_html.py -H example.com -p 8080
```

## 2. Output Modes
check_html.py supports three deterministic output modes.

### 2.1 JSON Mode (-j/--json)
Structured output for automation:

```bash
./check_html.py -H example.com --json
```

Produces a canonical JSON object containing:

- capture metadata
- backend detection
- enforcement results
- final status and message

### 2.2 Verbose Mode (-v/--verbose)

Human‑readable, multi‑section output:

```bash
./check_html.py -H example.com -v
```

Sections include:

- Request summary
- Capture details
- Backend detection
- Status enforcement
- Content‑type enforcement
- HTML enforcement
- Final result

### 2.3 Default Mode (Nagios Single‑Line)

No flags required:

```bash
./check_html.py -H example.com
```

Example OK:

```Code
OK - 200 OK (text/html)
```

Example failure:

```Code
CRITICAL - TLS handshake failed
```

This mode is used for Nagios/Icinga integration.

## 3. Protocol Selection

### Force HTTPS

```bash
./check_html.py -H example.com --https
```

### Force HTTP

```bash
./check_html.py -H example.com --http
```
### Auto‑detect (default)

If neither flag is provided:

- HTTPS is used if port is 443
- Otherwise HTTP is used

## 4. Enforcement Options

### Expected HTTP status

```bash
./check_html.py -H example.com --expect-status 200
```

### Require HTML body

```bash
./check_html.py -H example.com --require-html
```

### Require specific content‑type

```bash
./check_html.py -H example.com --require-type text/html
```

### Backend enforcement

```bash
./check_html.py -H example.com --require-backend nginx
```

## 5. Timeout and Redirects

### Set timeout (seconds)

```bash
./check_html.py -H example.com -t 5
```

### Limit redirects

```bash
./check_html.py -H example.com --max-redirects 3
```

## 6. Examples

### Check a normal website

```bash
./check_html.py -H example.com
```

### Check an HTTPS site with verbose output

```bash
./check_html.py -H example.com --https -v
```

### Enforce HTML and content‑type

```bash
./check_html.py -H example.com --require-html --require-type text/html
```

### Enforce backend fingerprint

```bash
./check_html.py -H example.com --require-backend nginx
```

### JSON output for automation

```bash
./check_html.py -H api.example.com --json
```

## 7. Nagios Integration

### Command definition

```Code
define command {
    command_name    check_html
    command_line    /usr/local/nagios/libexec/check_html.py -H $ARG1$
}
```

### Service definition

```Code
define service {
    use                 generic-service
    host_name           example.com
    service_description HTML Check
    check_command       check_html!example.com
}
```

### Example Nagios output

```Code
OK - 200 OK (text/html)
```

## 8. Exit Codes

check_html.py uses standard Nagios exit codes:

| Code | Meaning |
|------|---------|
| 0	| OK |
| 1 | WARNING |
| 2 | CRITICAL |
| 3 | UNKNOWN |

Exit codes are determined by the enforcement subsystem using Nagios‑aware severity merging:

**CRITICAL > WARNING > UNKNOWN > OK**

## 9. Help Output

View all flags:

```bash
./check_html.py --help
```

The CLI parser is noise‑free, grouped, and deterministic.