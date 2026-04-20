% CHECK_CERT(1) NMS_Tools | TLS Certificate Inspection Tool
% Linktech Engineering
% April 2026

# NAME
**check_cert** — TLS certificate inspection and policy enforcement tool

# SYNOPSIS
**check_cert** -H <host> [-p <port>] [options]

# DESCRIPTION
**check_cert** performs deterministic TLS certificate inspection, extracting
metadata, validating chains, enforcing hostname rules, and evaluating OCSP and
algorithm strength policies.

It is suitable for:
- Monitoring certificate expiration  
- Enforcing TLS policy  
- Detecting misconfigurations  
- Automation pipelines  

# OPTIONS

## Target

**-H, --host <hostname>**  
Target hostname.

**-p, --port <port>**  
TLS port (default: 443).

## Validation

**--require-hostname-match**  
Fail if certificate CN/SAN does not match host.

**--require-ocsp-good**  
Require OCSP status `good`.

**--require-tls13-only**  
Fail if TLS < 1.3 is negotiated.

## Metadata Extraction

Extracts:
- Expiration  
- Issuer  
- SAN entries  
- Key usage  
- Extended key usage  
- Signature algorithm  
- SCTs  
- HSTS preload status  

## Output Modes

**--json**  
Emit structured JSON.

**--quiet-json**  
Compact JSON.

**--output <file>**  
Write JSON to file.

**--verbose**  
Show chain details and negotiation metadata.

# EXIT CODES
**0** — Certificate valid  
**1** — Non-critical issue  
**2** — Critical issue  
**3** — Unknown error

# EXAMPLES

Check expiration:
```
check_cert -H example.com
```

Require hostname match:
```
check_cert -H api.example.com --require-hostname-match
```

Require OCSP good:
```
check_cert -H secure.example.com --require-ocsp-good
```

# FUTURE ENHANCEMENTS
- Intermediate expiration checks  
- Root trust validation  
- Signature algorithm strength enforcement  
- Pattern-based cipher forbidding  

# SEE ALSO
**nms_tools(7)**, **check_ports(1)**

# AUTHOR
Linktech Engineering — https://www.linktechengineering.net/projects/nms-tools/

