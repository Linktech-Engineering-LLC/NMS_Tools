# Installation

## Overview

NMS_Tools can be installed as a complete suite using the included `install.sh` script.  
This installer performs environment validation, prepares the Python runtime, builds the vendor library, and deploys all tools consistently across the system.

Tools may also be installed individually if only specific functionality is required.

---

## Prerequisites

- Linux system with standard utilities (bash, coreutils, etc.)
- Python 3.x (minimum version required by the suite)
- Permission to install into system paths (sudo may be required)

---

## Installing the Full Suite

To install all tools at once:

`./install.sh`


The installer will:

- Validate the Python environment using `validate_env.py`
- Ensure the correct Python version is available
- Build the vendor library deterministically
- Bump tool scripts to the correct version
- Deploy all tools to their target locations

The process is deterministic and safe to run multiple times.

---

## Installing Individual Tools

Each tool in the suite may also be installed independently.  
Refer to the README in each tool’s directory for usage and installation details.

---

## Vendor Library

The suite includes a vendor library that is built automatically during installation.  
This ensures:

- Deterministic behavior  
- No external runtime dependencies  
- Reproducible builds  

The vendor library is rebuilt only when required.

---

## Environment Validation

The installer uses `validate_env.py` to confirm:

- Python version compatibility  
- Required modules are available  
- The environment is suitable for deterministic operation  

If validation fails, the installer will exit with a clear diagnostic message.

---

## Notes

- The installer is idempotent and may be re‑run safely.  
- Vendor libraries are rebuilt only when necessary.  
- Individual tools can be deployed without installing the full suite.
