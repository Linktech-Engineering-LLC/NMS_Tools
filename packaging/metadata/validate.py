#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Leon McClatchey, Linktech Engineering LLC
"""
File: validate.py
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-06-16
Modified: 2026-06-16
Required: Python 3.8+
Part of: NMS_Tools Monitoring Suite
License: MIT (see LICENSE for details)

Description: Description of this module

"""


import json
import sys
from jsonschema import validate, ValidationError

SCHEMA_PATH = "packaging/metadata/schema.json"

def main():
    if len(sys.argv) != 2:
        print("Usage: validate.py <metadata.json>")
        sys.exit(1)

    metadata_path = sys.argv[1]

    try:
        with open(SCHEMA_PATH, "r") as f:
            schema = json.load(f)
    except Exception as e:
        print(f"Error loading schema: {e}")
        sys.exit(1)

    try:
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
    except Exception as e:
        print(f"Error loading metadata: {e}")
        sys.exit(1)

    try:
        validate(instance=metadata, schema=schema)
        print("metadata.json is valid")
    except ValidationError as e:
        print("metadata.json is INVALID")
        print(e.message)
        sys.exit(1)

if __name__ == "__main__":
    main()
