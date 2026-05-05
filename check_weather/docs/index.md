# check_weather Documentation Index  
**Updated 2026‑05**

This directory contains all documentation for the `check_weather` tool, including usage, operation, classification, recoloring, and integration details.

---

## Overview

`check_weather` is the backend engine used by the weather CGI script and the web demo.  
It performs:

- provider queries  
- data normalization  
- forecast slicing  
- icon classification  
- SVG recoloring  
- structured output generation  

This index links to all documentation relevant to development, maintenance, and integration.

---

## Documentation

### Core Docs
- **[Usage](Usage.md)**  
  Command‑line flags, examples, dry‑run mode, logging behavior.

- **[Operation](Operation.md)**  
  Internal flow, provider handling, forecast slicing, error handling.

- **[Metadata Schema](Metadata_Schema.md)**  
  Field definitions for all JSON output structures.

- **[Enforcement](Enforcement.md)**  
  Rules, invariants, and validation logic enforced by the tool.

- **[Classification](Classification.md)** *(New)*  
  Hybrid filename + geometry classification engine used for icon recoloring.

- **[Examples](Examples.md)**  
  Sample outputs, verbose mode examples, and CGI integration samples.

- **[Troubleshooting](Troubleshooting.md)**  
  Common issues, log interpretation, provider failures, icon mismatches.

- **[CHANGELOG](../CHANGELOG.md)**  
  Version history for the entire NMS_Tools suite.

- **[Tool‑Specific CHANGELOG](../check_weather/CHANGELOG.md)** *(New)*  
  Detailed history of changes specific to the `check_weather` tool.

---

## Related Components

### Recolor Engine
The recoloring logic is implemented in:

check_weather/recolor.py


See **Classification.md** for how groups are assigned, and **Operation.md** for how recoloring fits into the pipeline.

### Weather Demo (Web UI)
Documentation for the web UI lives in:

web/docs/

This includes HTML/JS integration, icon usage, and CGI endpoint behavior.

---

## Pipeline Overview

provider query
→ normalization
→ forecast slicing
→ icon classification
→ recoloring
→ output (JSON / CGI)


The classification and recoloring stages are documented in detail in `Classification.md`.

---

## Contributing

Contributions should follow:

- consistent logging format  
- deterministic output rules  
- stable classification behavior  
- documented changes in the tool‑specific CHANGELOG  

Pull requests should reference the relevant documentation sections.

---

**End of index.md**
