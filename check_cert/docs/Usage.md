# Usage Guide — `check_cert.py`

This guide explains how to invoke `check_cert.py`, what each flag does, and how
to combine modes, thresholds, and enforcement rules.

---

## 1. Basic Checks

```bash
check_cert -H example.com
```
This emits a single Nagios-style line:

`OK - certificate valid, expires in 85 days on 2026-06-13`

This is the default mode for:

- Monitoring systems
- Cron jobs
- Shell scripts

## 2. Verbose Output

check_cert -H example.com -v

- Connection details
- TLS version and cipher
- Certificate metadata
- SAN list
- Key information  
- AIA URLs and intermediate chain
- OCSP metadata
- Chain validation summary
- General warnings and errors
- Enforcement summary

Verbose mode is "grouped, noise-free, deterministic"
Chain warnings appear **only** in verbose/JSON, never Nagios

## 3. JSON Output

check_cert -H example.com --json

Outputs a stable, deterministic JSON object containing:

- Certificate metadata
- Key metadata  
- SAN list
- TLS session details
- Expiration timestamp and days remaining
- OCSP metadata
- Chain metadata
- General warnings and errors
- Enforcement results

Ideal for:

- Automation
- Log ingestion
- Pipelines
- Programmatic inspection 

## 4. Expiration Thresholds

Set Nagios thresholds:

-w DAYS   Warning threshold
-c DAYS   Critical threshold

Example: 
`check_cert -H example.com -w 30 -c 10`

Behavior:

- days_remaining <= critical → CRITICAL
- days_remaining <= warning → WARNING
- otherwise → OK

Thresholds apply only to expiration unless enforcement rules are used.
Enforcement failures always produce CRITICAL.

## 5. Enforcement Rules

Enforcement rules validate certificate, TLS, and OCSP properties.

Failures appear in:

- JSON: enforcement.failed
- Verbose: “Enforcement Summary”
- Nagios: CRITICAL

### OCSP Enforcement
--require-ocsp
--forbid-ocsp
--ocsp-status {good,revoked,unknown,invalid}

**Note:**
OCSP support is currently limited to:

- Extracting OCSP URLs
- Reporting presence/absence
- Placeholder status

Full OCSP reachability and response parsing are planned.

### TLS Requirements
--min-tls VERSION
--require-tls VERSION
--require-cipher CIPHER
--forbid-cipher CIPHER
--require-aead
--forbid-cbc
--forbid-rc4

### Key Requirements
--min-rsa BITS
--require-curve CURVE

### Certificate Requirements
--require-wildcard
--forbid-wildcard
-I, --issuer ISSUER
-A, --sigalg ALGORITHM

## 6. Port, Timeout, and SNI
**Port**
check_cert -H mail.example.com -p 587

**Timeout**
--timeout SECONDS

**Disable SNI**
--no-sni

## 7. Insecure Mode
Skip certificate validation during the TLS handshake:

Code
--insecure

This does not affect certificate parsing or enforcement rules.

## 8. Nagios Integration

**Command Definition**
define command {
    command_name    check_cert
    command_line    /usr/lib/nagios/plugins/check_cert -H $HOSTADDRESS$ -w 30 -c 10
}

**Service Definition**
define service {
    use                 generic-service
    host_name           myserver
    service_description TLS Certificate
    check_command       check_cert
}

## 9. Example Outputs

**Default**
OK - 60 days remaining (2026-05-18 18:19:55 UTC);

**Verbose (truncated)**
Host: example.com
Port: 443
TLS Version: tlsv1.3
Cipher: TLS_AES_256_GCM_SHA384
Issuer CN: Example CA
...

**JSON**
{
  "subject_cn": "example.com",
  "issuer_cn": "Example CA",
  "signature_algorithm": "sha256",
  "key_type": "ecdsa",
  "tls_version": "tlsv1.3",
  "cipher": "TLS_AES_256_GCM_SHA384",
  "expiration_days": 60,
  "warnings": [],
  "errors": []
}

## 10. Troubleshooting

### “tls_handshake_failed”
- Port blocked  
- TLS version mismatch  
- SNI mismatch  

### “no_certificate_present”
- Host does not serve TLS on the given port  
- Missing `-p` for non‑443 services  

### OCSP unreachable
- Firewall blocking outbound HTTP  
- OCSP responder offline  

### Chain validation warnings
- Missing intermediates  
- Mismatched issuer/subject  
- Non‑standard chain structure  

## 11. Network Requirements

- Outbound TCP to target host
- Outbound HTTP for AIA retrieval 
- Outbound HTTP for OCSP (future retrieval)  

## 12. Hostname Resolution

All NMS_Tools plugins that accept `-H` require the hostname to be resolvable
via the system resolver (DNS, /etc/hosts, or equivalent).

If the hostname cannot be resolved:

- The tool fails fast with a deterministic error message.
- No network operations are attempted.
- In Nagios mode, the tool exits `UNKNOWN` with a single clean line.

### Deterministic Error Example

If the hostname is unresolvable:

    UNKNOWN - Hostname resolution failed for 'badhost.example'

This behavior is consistent across all tools in the suite and is required for
operator‑grade determinism and Nagios/Icinga compatibility.
