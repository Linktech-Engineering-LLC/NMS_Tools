# NMS_Tools

A collection of deterministic, audit‑transparent network management and monitoring tools used across Linktech Engineering infrastructure.  
Each tool is designed with:

- Predictable, reproducible behavior  
- Strict output contracts  
- Clear operational modes  
- Minimal external dependencies  
- Compatibility with Nagios/Icinga and standalone system use  

---

## Tools

### `check_cert.py`
A deterministic TLS certificate inspection and policy enforcement tool with:

- JSON, verbose, and Nagios output modes  
- TLS version and cipher extraction  
- SAN, issuer, signature algorithm, and key metadata  
- AIA chain reconstruction  
- OCSP reachability detection  
- Expiration thresholds and policy enforcement  
- Deterministic JSON schema for automation  

Documentation:

- **Installation:** `docs/Installation.md`  
- **Operation:** `docs/Operation.md`  
- **Usage Examples:** `docs/Usage.md`  
- **Roadmap:** `docs/roadmap.md`  

---

## Philosophy

NMS_Tools follows Linktech Engineering’s deterministic engineering principles:

- No hidden state  
- No ambiguous output  
- No silent failures  
- Audit‑transparent behavior  
- Predictable exit codes  
- Clean separation between human and machine output modes  

Each tool is built to be reliable in both interactive and automated environments.

---

## Status

Active development.  
See `docs/roadmap.md` for planned enhancements and upcoming tools in the suite.

