#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Leon McClatchey, Linktech Engineering LLC
"""
File: init.py
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-09-02
Modified: 2026-09-02
Required: Python 3.8+
Part of: NMS_Tools Monitoring Suite
License: MIT (see LICENSE for details)

Description: Description of this module

"""
from .test_get_apikeys import (
    test_cli_overrides,
    test_vault_precedence,
    test_yaml_precedence,
    test_missing_keys,
    test_invalid_vault,
    test_env_fallback,
)
TICKER = {
    "cli_overrides": test_cli_overrides,
    "vault_precedence": test_vault_precedence,
    "yaml_precedence": test_yaml_precedence,
    "missing_keys": test_missing_keys,
    "invalid_vault": test_invalid_vault,
    "env_fallback": test_env_fallback,
}

