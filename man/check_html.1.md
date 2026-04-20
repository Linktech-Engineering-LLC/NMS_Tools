% CHECK_HTML(1) NMS_Tools | HTTP/HTTPS Content and Response Validator
% Linktech Engineering
% April 2026

# NAME
**check_html** — HTTP/HTTPS inspection and content validation tool

# SYNOPSIS
**check_html** -H <host> [-p <port>] [options]

# DESCRIPTION
**check_html** performs deterministic HTTP/HTTPS checks, including status code
validation, redirect chain capture, TLS negotiation details, and optional
content validation.

It is designed for:
- Monitoring web services  
- Detecting regressions  
- Validating expected content  
- Automation pipelines  

# OPTIONS

## Target

**-H, --host <hostname>**  
Target hostname.

**-p, --port <port>**  
Port (default: 80 for HTTP, 443 for HTTPS).

**--path <path>**  
Request path.

## Validation

**--expect-status <code>**  
Require specific HTTP status.

**--expect-contains <string>**  
Require substring in response body.

**--expect-json**  
Validate JSON structure.

## Debugging

**--debug-http**  
Show request/response details.

**--verbose**  
Show redirect chain and timing metrics.

## Output Modes

**--json**  
Emit structured JSON.

**--quiet**  
Suppress human-readable output.

# EXIT CODES
**0** — All checks passed  
**1** — Non-critical deviation  
**2** — Critical failure  
**3** — Unknown error

# EXAMPLES

Check homepage:
```
check_html -H example.com
```

Validate content:
```
check_html -H example.com --expect-contains "Welcome"
```

Debug HTTP:
```
check_html -H api.example.com --debug-http
```

# FUTURE ENHANCEMENTS
- Structured HTML parsing  
- DOM validation rules  
- Content hashing for change detection  
- TLS handshake timing metrics  

# SEE ALSO
**nms_tools(7)**, **check_cert(1)**

# AUTHOR
Linktech Engineering — https://www.linktechengineering.net/projects/nms-tools/
