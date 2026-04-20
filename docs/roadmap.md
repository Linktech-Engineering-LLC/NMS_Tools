# NMS_Tools Roadmap

This document tracks planned enhancements and future tools within the NMS_Tools suite.

---

## check_ports.py — Planned Enhancements

### Port Parsing & Resolution
- **Named port support** (e.g., `https` → 443 via `/etc/services`)
- Strict validation for unknown port names
- Deterministic expansion of mixed numeric + named ports

### Output & Evaluation
- JSON schema versioning
- Optional perfdata block for Nagios
- Additional evaluation modes (e.g., require-open-count=N)

### Logging & Diagnostics
- Structured diagnostic mode (`--debug`)
- Per‑port timing metrics
- Connection lifecycle tracing (SYN, timeout, refusal)

### UX Improvements
- Help text refinements
- Port parsing preview (`--explain-ports`)

---

## check_weather.py — Planned for v2.1.0

### Provider Architecture
- NOAA/NWS as a second weather provider with station-based and coordinate-based lookups
- Provider registry pattern for uniform declaration, discovery, and dispatch
- `--provider` override for explicit provider selection

### Debug and Diagnostic Flags
- `--debug-cache` — cache-hit/miss status, file path, cache age, and TTL comparison
- `--debug-location` — resolved coordinates, station ID, lookup method, and geocoding source

### Validation and Configuration
- Strict schema validator against a versioned internal schema
- `--ttl` override for user-configurable cache TTL
- `--ignore-ttl` — bypass TTL check and force an API fetch
- `--ignore-cache` — skip cache entirely
- `--cache-info` — display cache status and metadata without fetching

### Documentation
- Full documentation update for v2.1.0 covering all new flags, provider registry usage,
  NOAA/NWS examples, schema validation flow, and TTL logic

---

## check_cert.py — Planned Enhancements

### Chain & Trust Validation
- Chain status field (`ok`, `self_signed`, `missing_intermediate`, `issuer_unknown`)
- Intermediate expiration checks
- Root trust validation (system trust store or custom CA bundle)

### Hostname & SAN Enforcement
- Explicit hostname mismatch detection
- `--require-hostname-match` flag

### OCSP Enhancements
- OCSP response timestamp parsing (`thisUpdate`, `nextUpdate`)
- `--require-ocsp-good` enforcement

### Key & Algorithm Strength
- Minimum ECC curve strength enforcement
- Signature algorithm strength enforcement

### TLS & Cipher Policy
- `--require-tls13-only` convenience flag
- Pattern‑based cipher forbidding

### Metadata Extraction
- SCT extraction
- HSTS preload detection
- keyUsage / extendedKeyUsage extraction

### Operational / UX Improvements
- `--output <file>` for JSON logging
- `--quiet-json` compact mode
- `--perfdata-json` for Nagios perfdata
- Help text refinements
- Verbose output polishers

---

## check_html.py — Planned Enhancements

### HTTP/TLS Pipeline
- TLS handshake timing metrics
- Redirect chain capture
- Backend fingerprinting improvements

### Content Validation
- Structured HTML parsing mode
- Optional DOM validation rules
- Content hashing for change detection

### Output & Diagnostics
- JSON schema versioning
- `--debug-http` for request/response tracing
- Response timing metrics

---

## check_interfaces.py — Planned Enhancements

### SNMP & Interface State
- Improved SNMP error classification (timeout vs auth vs unreachable)
- Deterministic UNKNOWN vs CRITICAL mapping
- Interface speed and duplex extraction

### Output & Diagnostics
- JSON schema versioning
- Per‑interface timing metrics
- `--debug-snmp` diagnostic mode

### UX Improvements
- Help text refinements
- Interface filtering (`--match`, `--exclude`)

---

## Suite‑Level Roadmap

### Documentation & Architecture
- Unified documentation style across all tools
- Suite‑level navigation improvements
- Versioned JSON schemas for all tools

### Logging & Determinism
- Unified logging lifecycle across the suite
- Standardized log rotation and retention policy
- Optional structured logs (JSONL)

### Future Tools (Concept Stage)
- `check_tls.py` — TLS handshake policy enforcement  
- `check_ocsp.py` — OCSP responder health checks  
- `check_dnssec.py` — DNSSEC validation  
- `check_renewal.py` — Certificate renewal pipeline validation  

---

## Notes

Additional items will be added as development continues.
