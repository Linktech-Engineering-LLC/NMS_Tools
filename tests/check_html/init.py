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

from .test_core import (
    test_validate_host_basic_ip,
    test_validate_host_basic_invalid,
    test_determine_protocol_default,
    test_backend_rules_require_match,
    test_nagios_label,
    test_perfdata,
    test_single_line_ok,
)

HTML = {
    "validate_host_basic_ip": test_validate_host_basic_ip,
    "validate_host_basic_invalid": test_validate_host_basic_invalid,
    "determine_protocol_default": test_determine_protocol_default,
    "backend_rules_require_match": test_backend_rules_require_match,
    "nagios_label": test_nagios_label,
    "perfdata": test_perfdata,
    "single_line_ok": test_single_line_ok,
}

