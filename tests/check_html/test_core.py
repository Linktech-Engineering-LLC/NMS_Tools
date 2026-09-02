#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Leon McClatchey, Linktech Engineering LLC
"""
File: test_core.py
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-09-02
Modified: 2026-09-02
Required: Python 3.8+
Part of: NMS_Tools Monitoring Suite
License: MIT (see LICENSE for details)

Description: Description of this module

"""

from src.check_html.check_html import (
    validate_host_basic,
    determine_protocol_and_url,
    enforce_backend_rules,
    build_html_meta,
    nagios_label,
    build_perfdata,
    single_line,
)

class DummyArgs:
    def __init__(self):
        self.https = False
        self.max_redirects = 5
        self.timeout = 5
        self.expect_status = 200
        self.expect_family = None
        self.warning_rt = 0.5
        self.critical_rt = 1.0
        self.warning_size = 200_000
        self.critical_size = 500_000

def test_validate_host_basic_ip():
    rc = validate_host_basic("127.0.0.1")
    assert rc["ok"] is True
    assert rc["ip"] == "127.0.0.1"

def test_validate_host_basic_invalid():
    rc = validate_host_basic("invalid.host.name")
    assert rc["ok"] is False

def test_determine_protocol_default():
    args = DummyArgs()
    args.host = "example.com"
    args.port = None
    args.port_was_explicit = False
    protocol, url = determine_protocol_and_url(args)
    assert protocol == "http"
    assert url == "http://example.com/"

def test_backend_rules_require_match():
    detected = {"detected": "nginx", "reason": "header match"}
    args = DummyArgs()
    args.require_backend = ["nginx"]
    args.forbid_backend = None
    args.require_tomcat = False
    args.require_apache = False
    args.require_nginx = False
    args.require_iis = False
    args.require_jetty = False
    args.require_express = False
    args.require_gunicorn = False
    args.forbid_tomcat = False
    args.forbid_apache = False
    args.forbid_nginx = False
    args.forbid_iis = False
    args.forbid_jetty = False
    args.forbid_express = False
    args.forbid_gunicorn = False

    status, msg = enforce_backend_rules(detected, args)
    assert status == 0  # OK

def test_nagios_label():
    assert nagios_label(0) == "OK"
    assert nagios_label(2) == "CRITICAL"

def test_perfdata():
    args = DummyArgs()
    capture = {"response_time": 0.1234, "body": "hello world"}
    perf = build_perfdata(args, capture)
    assert "time=0.1234s" in perf
    assert "size=11B" in perf

def test_single_line_ok():
    args = DummyArgs()
    result = {
        "overall": {"status": 0, "message": "OK"},
        "capture": {"status": 200, "content_type": "text/html", "response_time": 0.1, "body": "hi"},
    }
    line = single_line(result, args)
    assert line.startswith("OK - 200 OK")
