#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Leon McClatchey, Linktech Engineering LLC
"""
File: validate.py
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-07-15
Modified: 2026-08-26
Required: Python 3.8+
Part of: NMS_Tools Monitoring Suite
License: MIT (see LICENSE for details)

Description: Description of this module

"""

import json, sys
from pathlib import Path
from jsonschema import validate, ValidationError

SCHEMA_PATH = Path(__file__).parent / "schema.json"

def main():
    with open(SCHEMA_PATH) as s, open(sys.argv[1]) as f:
        schema = json.load(s)
        data = json.load(f)
    try:
        validate(instance=data, schema=schema)
        print("[+] metadata.json validated successfully")
    except ValidationError as e:
        print(f"[!] Validation failed: {e.message}")
        sys.exit(1)

if __name__ == "__main__":
    main()
