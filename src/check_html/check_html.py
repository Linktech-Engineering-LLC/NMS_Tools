#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Leon McClatchey, Linktech Engineering LLC
"""
File: check_html.py
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-03-21
 Modified: 2026-08-29
Required: Python 3.8+
Part of: NMS_Tools Monitoring Suite
License: MIT (see LICENSE for details)

Description:
    HTML content checker with status-code enforcement, required-tag checks,
    content-type validation, quiet/verbose modes, and JSON output.
"""

import http.client
import ipaddress
import json
import os
import ssl
import socket
import sys
import time

from pathlib import Path
from urllib.parse import urlparse

from PythonTools.http import (
    HttpFetchError,
    BACKEND_SIGNATURES,
    detect_backend,
    enforce_status_rules,
    enforce_content_type_rules,
    enforce_html_rules
)
from PythonTools.log_helpers.factory import LoggerFactory
from PythonTools.nagios import (
    OK,
    WARNING,
    CRITICAL,
    UNKNOWN,
    BaseNagiosParser,
    nagios_summary,
    start_banner,
    end_banner,
    result_banner,
    html_banner,
    should_output,
    early_exit,
    critical_exit,
    build_result_object,
)
from PythonTools.utils.common import normalize_list
# Root of the suite (two levels up from the tool script)
SUITE_ROOT = Path(__file__).resolve().parent.parent

def load_version() -> str:
    """
    Load the suite VERSION file if present.
    If missing, return a fallback string indicating external execution.
    """
    version_file = SUITE_ROOT / "VERSION"

    try:
        return version_file.read_text(encoding="utf-8").strip()
    except Exception:
        return "External to NMS_TOOLS Suite"

VERSION = load_version()
MIN_MAJOR = 3
MIN_MINOR = 8
# Other Global Constants
SCRIPT_NAME = Path(sys.argv[0]).stem
SCRIPT_VERSION = "1.1.0"
# -----------------------------
# ArgParse Custom Formatter & CLI Parser (Migrated)
# -----------------------------
def build_parser():
    nag = BaseNagiosParser(
        prog=SCRIPT_NAME,
        description=(
            "HTML Content Validation Tool\n\n"
            "Performs HTTP/HTML inspection including status checks, content-type "
            "validation, required/forbidden tags and text, backend fingerprinting, "
            "redirect analysis, and optional security requirements.\n"
            "Supports verbose, JSON, quiet, and Nagios-compatible output modes."
        ),
        script_version=SCRIPT_VERSION,
        suite_version=VERSION,
    )

    # Usage line
    nag.parser.usage = "%(prog)s -H <host> [options]"

    # -----------------------------
    # Core Options
    # -----------------------------
    core = nag.add_group("Core Options")
    core.add_argument("-H", "--host", required=True, help="Target hostname or URL")
    core.add_argument("-p", "--port", type=int, default=80, help="Port to connect to")
    core.add_argument("--timeout", type=int, default=5, help="Connection timeout in seconds")

    # -----------------------------
    # Connection Options
    # -----------------------------
    conn = nag.add_group("Connection Options")
    conn.add_argument("--https", action="store_true", help="Force HTTPS request")
    conn.add_argument("--no-redirect", action="store_true", help="Do not follow redirects")
    conn.add_argument("--max-redirects", type=int, default=5, help="Maximum number of redirects allowed")

    # -----------------------------
    # HTTP Status Requirements
    # -----------------------------
    status = nag.add_group("HTTP Status Requirements")
    status.add_argument("--expect-status", type=int, default=200, help="Expected HTTP status code")
    status.add_argument("--expect-family", help="Expected status code family (e.g., 2xx)")
    status.add_argument("--forbid-status", type=int, help="Fail if this status code is returned")

    # -----------------------------
    # Content-Type Requirements
    # -----------------------------
    ctype = nag.add_group("Content-Type Requirements")
    ctype.add_argument("--require-content-type", default="text/html", help="Required Content-Type header")
    ctype.add_argument("--forbid-content-type", help="Fail if this Content-Type is returned")

    # -----------------------------
    # HTML Content Requirements
    # -----------------------------
    html = nag.add_group("HTML Requirements")
    html.add_argument("--require-tag", action="append", help="Require specific HTML tag (repeatable)")
    html.add_argument("--forbid-tag", action="append", help="Forbid specific HTML tag (repeatable)")
    html.add_argument("--require-text", action="append", help="Require specific text in the page (repeatable)")
    html.add_argument("--forbid-text", action="append", help="Forbid specific text in the page (repeatable)")
    html.add_argument("--max-size", type=int, help="Maximum allowed page size in bytes")

    # -----------------------------
    # Backend Fingerprinting
    # -----------------------------
    backend = nag.add_group("Backend Fingerprinting")

    backend.add_argument("--require-tomcat", action="store_true", help="Require backend to be Apache Tomcat")
    backend.add_argument("--forbid-tomcat", action="store_true", help="Fail if backend is Apache Tomcat")

    backend.add_argument("--require-apache", action="store_true", help="Require backend to be Apache HTTPD")
    backend.add_argument("--forbid-apache", action="store_true", help="Fail if backend is Apache HTTPD")

    backend.add_argument("--require-nginx", action="store_true", help="Require backend to be Nginx")
    backend.add_argument("--forbid-nginx", action="store_true", help="Fail if backend is Nginx")

    backend.add_argument("--require-iis", action="store_true", help="Require backend to be Microsoft IIS")
    backend.add_argument("--forbid-iis", action="store_true", help="Fail if backend is Microsoft IIS")

    backend.add_argument("--require-jetty", action="store_true", help="Require backend to be Jetty")
    backend.add_argument("--forbid-jetty", action="store_true", help="Fail if backend is Jetty")

    backend.add_argument("--require-express", action="store_true", help="Require backend to be Node.js/Express")
    backend.add_argument("--forbid-express", action="store_true", help="Fail if backend is Node.js/Express")

    backend.add_argument("--require-gunicorn", action="store_true", help="Require backend to be Gunicorn")
    backend.add_argument("--forbid-gunicorn", action="store_true", help="Fail if backend is Gunicorn")

    backend.add_argument(
        "--require-backend",
        action="append",
        choices=["tomcat", "apache", "nginx", "iis", "jetty", "express", "gunicorn"],
        help="Require backend to match one of the specified types (repeatable)"
    )

    backend.add_argument(
        "--forbid-backend",
        action="append",
        choices=["tomcat", "apache", "nginx", "iis", "jetty", "express", "gunicorn"],
        help="Fail if backend matches any of the specified types (repeatable)"
    )

    # -----------------------------
    # Security Requirements
    # -----------------------------
    sec = nag.add_group("Security Requirements")
    sec.add_argument("--require-https", action="store_true", help="Fail if HTTPS is not used")
    sec.add_argument("--require-https-redirect", action="store_true", help="Require HTTP to redirect to HTTPS")
    sec.add_argument("--require-hsts", action="store_true", help="Require Strict-Transport-Security header")
    sec.add_argument("--require-header", action="append", help="Require specific header (Header:Value)")

    # -----------------------------
    # Nagios Thresholds
    # -----------------------------
    nagios = nag.add_group("Nagios Thresholds")
    nagios.add_argument("--warning-rt", type=float, default=0.5, help="Warning threshold for response time (seconds)")
    nagios.add_argument("--critical-rt", type=float, default=1.0, help="Critical threshold for response time (seconds)")
    nagios.add_argument("--warning-size", type=int, default=200 * 1024, help="Warning threshold for page size (bytes)")
    nagios.add_argument("--critical-size", type=int, default=500 * 1024, help="Critical threshold for page size (bytes)")

    # -----------------------------
    # Examples
    # -----------------------------
    nag.parser.epilog = (
        "Examples:\n"
        "  %(prog)s -H example.com -v\n"
        "  %(prog)s -H example.com --expect-status 200\n"
        "  %(prog)s -H example.com --require-tomcat\n"
        "  %(prog)s -H example.com --json\n"
    )

    return nag.parse()
def determine_protocol_and_url(args):
    host = args.host.strip()

    # Detect protocol prefix
    if host.startswith("http://"):
        protocol = "http"
        host = host[len("http://"):]
    elif host.startswith("https://"):
        protocol = "https"
        host = host[len("https://"):]
    else:
        protocol = "https" if args.https else "http"

    # Determine port
    port = args.port

    # Build base URL
    url = f"{protocol}://{host}"

    # Include port ONLY if explicitly specified
    if args.port_was_explicit:   # You track this in the parser
        url = f"{url}:{port}"

    # Default path
    if "/" not in host:
        url = f"{url}/"

    return protocol, url
def fetch_http(url, protocol, args):
    """
    Performs an HTTP or HTTPS request with deterministic behavior.

    Returns:
        {
            "status": int,
            "headers": dict,
            "body": str,
            "response_time": float,
            "final_url": str,
            "redirects": int,
            "tls_error": bool
        }
    """

    parsed = urlparse(url)
    raw_host = parsed.hostname
    if raw_host is None:
        raise HttpFetchError(f"Invalid redirect URL: missing hostname in '{url}'")
    host: str = raw_host
    port = parsed.port or (443 if protocol == "https" else 80)
    path = parsed.path or "/"

    redirects = 0
    tls_error = False
    start_time = time.time()

    while True:
        try:
            # ------------------------------------------------------------
            # Build connection
            # ------------------------------------------------------------
            if protocol == "https":
                context = ssl.create_default_context()
                conn = http.client.HTTPSConnection(
                    host,
                    port,
                    timeout=args.timeout,
                    context=context
                )
            else:
                conn = http.client.HTTPConnection(
                    host,
                    port,
                    timeout=args.timeout
                )

            # ------------------------------------------------------------
            # Send request
            # ------------------------------------------------------------
            conn.request("GET", path, headers={"Host": host})
            resp = conn.getresponse()

        except ssl.SSLError:
            # Build minimal capture object
            return {
                "status": None,
                "headers": {},
                "content_type": None,
                "body": None,
                "response_time": None,
                "final_url": url,
                "redirects": 0,
                "tls_error": True,
            }

        except Exception as e:
            raise HttpFetchError(f"Connection failed: {e}")

        # ------------------------------------------------------------
        # Capture response
        # ------------------------------------------------------------
        status = resp.status
        headers = {k.lower(): v for k, v in resp.getheaders()}
        content_type = headers.get("content-type")
        body = resp.read().decode(errors="replace")

        # ------------------------------------------------------------
        # Handle redirects
        # ------------------------------------------------------------
        if 300 <= status < 400 and not args.no_redirect:
            if redirects >= args.max_redirects:
                raise HttpFetchError("Maximum redirects exceeded")

            location = headers.get("location")
            if not location:
                raise HttpFetchError("Redirect without Location header")

            redirects += 1

            # Absolute or relative redirect
            new_url = location if "://" in location else f"{protocol}://{host}{location}"
            parsed = urlparse(new_url)
            raw_host = parsed.hostname
            if raw_host is None:
                raise HttpFetchError(f"Invalid redirect URL: missing hostname in '{new_url}'")
            host: str = raw_host
            path = parsed.path or "/"
            protocol = parsed.scheme
            port = parsed.port or (443 if protocol == "https" else 80)

            continue  # perform next request

        # ------------------------------------------------------------
        # Done
        # ------------------------------------------------------------
        break

    response_time = time.time() - start_time

    return {
        "status": status,
        "headers": headers,
        "content_type": content_type,
        "body": body,
        "response_time": response_time,
        "final_url": f"{protocol}://{host}:{port}{path}",
        "redirects": redirects,
        "tls_error": tls_error
    }
def capture_http_response(url: str, protocol: str, args):
    """
    Performs the HTTP request and returns a normalized capture object.
    """

    try:
        raw = fetch_http(url, protocol, args)
    except HttpFetchError as e:
        critical_exit(str(e))

    # Normalize status
    raw_status = raw.get("status")
    status = int(raw_status) if isinstance(raw_status, (int, float, str)) else None

    # Normalize content-type
    ctype = raw.get("content_type") or None

    # Normalize response time
    rt = raw.get("response_time")
    response_time = float(rt) if isinstance(rt, (int, float)) else None

    # Normalize headers
    headers = raw.get("headers") or {}

    # Normalize body
    body = raw.get("body") if raw.get("body") is not None else None


    # Normalize and structure the capture
    capture = {
        "status": status,
        "headers": headers,
        "content_type": ctype,
        "body": body,
        "response_time": response_time,
        "final_url": raw.get("final_url"),
        "redirects": raw.get("redirects", 0),
        "tls_error": raw.get("tls_error", False),
    }

    return capture
def enforce_backend_rules(detected_obj, args):
    # TLS failure overrides backend detection
    if detected_obj["reason"] == "TLS handshake failed":
        return (2, "TLS handshake failed")
    backend = detected_obj["detected"]   # may be None

    # ------------------------------------------------------------
    # Explicit selectors (highest precedence)
    # ------------------------------------------------------------
    explicit_require = []
    explicit_forbid = []

    if args.require_tomcat: explicit_require.append("tomcat")
    if args.require_apache: explicit_require.append("apache")
    if args.require_nginx: explicit_require.append("nginx")
    if args.require_iis: explicit_require.append("iis")
    if args.require_jetty: explicit_require.append("jetty")
    if args.require_express: explicit_require.append("express")
    if args.require_gunicorn: explicit_require.append("gunicorn")

    if args.forbid_tomcat: explicit_forbid.append("tomcat")
    if args.forbid_apache: explicit_forbid.append("apache")
    if args.forbid_nginx: explicit_forbid.append("nginx")
    if args.forbid_iis: explicit_forbid.append("iis")
    if args.forbid_jetty: explicit_forbid.append("jetty")
    if args.forbid_express: explicit_forbid.append("express")
    if args.forbid_gunicorn: explicit_forbid.append("gunicorn")

    # ------------------------------------------------------------
    # Generic selectors (only used if no explicit selectors)
    # ------------------------------------------------------------
    require = explicit_require or normalize_list(args.require_backend)
    forbid  = explicit_forbid  or normalize_list(args.forbid_backend)

    # ------------------------------------------------------------
    # Enforcement
    # ------------------------------------------------------------
    if require:
        if backend is None:
            return CRITICAL, f"No backend detected but required {require}"
        if backend not in require:
            return CRITICAL, f"Backend '{backend}' does not match required {require}"

    if forbid:
        if backend in forbid:
            return CRITICAL, f"Backend '{backend}' is forbidden"

    return OK, None
# ============================================================
#  Metadata Builder for check_html.py
#  (Aligned with current main() and logging module)
# ============================================================
def build_html_meta(capture, backend, args):
    """
    Deterministic metadata enrichment for check_html.
    Mirrors the structure used in check_cert.py:
    - base metadata is created in main()
    - this function adds HTML-specific operational metadata
    """

    return {
        # Normalized target URL + protocol
        "url": capture.get("url"),
        "protocol": capture.get("protocol"),

        # Connection behavior
        "https": args.https,
        "max_redirects": args.max_redirects,
        "timeout": args.timeout,

        # Expected behavior (for banners + enforcement)
        "expect_status": args.expect_status,
        "expect_family": args.expect_family,

        # Capture-derived fields
        "status": capture.get("status"),
        "content_type": capture.get("content_type"),
        "redirects": capture.get("redirects"),
        "backend_detected": backend.get("detected"),
    }
# -------------------------------------
# Displays
# ------------------------------------
def print_verbose(result):
    """
    Render verbose, human-readable output for check_html.
    """

    cap = result["capture"]
    backend = result["backend"]

    print("=== HTTP Capture ===")

    status = cap["status"] if cap["status"] is not None else "N/A"
    print(f"Status:          {status}")

    ctype = cap["content_type"] if cap["content_type"] else "N/A"
    print(f"Content-Type:    {ctype}")

    rt = cap["response_time"]
    rt_str = f"{rt:.4f}s" if isinstance(rt, (int, float)) else "N/A"
    print(f"Response Time:   {rt_str}")

    print(f"Final URL:       {cap['final_url']}")
    print(f"Redirects:       {cap['redirects']}")
    print(f"TLS Error:       {cap['tls_error']}")
    print()

    print("=== Backend Detection ===")
    print(f"Detected:        {backend['detected']}")
    print(f"Candidates:      {', '.join(backend['candidates'])}")
    print(f"Confidence:      {backend['confidence']}")
    print(f"Reason:          {backend['reason']}")
    print(f"Backend Status:  {nagios_label(backend['status'])}")
    print()

    print("=== Status Check ===")
    print(f"Status:          {nagios_label(result['status_check']['status'])}")
    if result["status_check"]["message"]:
        print(f"Message:         {result['status_check']['message']}")
    print()

    print("=== Content-Type Check ===")
    print(f"Status:          {nagios_label(result['content_type_check']['status'])}")
    if result["content_type_check"]["message"]:
        print(f"Message:         {result['content_type_check']['message']}")
    print()

    print("=== HTML Check ===")
    print(f"Status:          {nagios_label(result['html_check']['status'])}")
    if result["html_check"]["message"]:
        print(f"Message:         {result['html_check']['message']}")
    print()

    print("=== Overall ===")
    print(f"Final Status:    {nagios_label(result['overall']['status'])}")
    print(f"Message:         {result['overall']['message']}")
def nagios_label(code):
    return {
        0: "OK",
        1: "WARNING",
        2: "CRITICAL",
        3: "UNKNOWN"
    }.get(code, "UNKNOWN")
def single_line(result, args):
    code = result["overall"]["status"]
    message = result["overall"]["message"]

    # Determine prefix
    if code == 0:
        prefix = "OK"
    elif code == 1:
        prefix = "WARNING"
    elif code == 2:
        prefix = "CRITICAL"
    else:
        prefix = "UNKNOWN"

    # ------------------------------------------------------------
    # Enhance OK output with HTTP status + content-type
    # ------------------------------------------------------------
    perfdata = None

    if code == 0:
        capture = result.get("capture", {})
        http_status = capture.get("status")
        ctype = capture.get("content_type")
        rt = capture.get("response_time") or 0
        body = capture.get("body") or ""
        size = len(body.encode("utf-8"))

        # Build perfdata deterministically
        # perfdata = f"time={rt:.4f}s;;;0 size={size}B;;;0"
        perfdata = build_perfdata(args, capture)

        # Build human-readable message
        if http_status is not None:
            if ctype:
                message = f"{http_status} OK ({ctype})"
            else:
                message = f"{http_status} OK (no content-type)"

    # ------------------------------------------------------------
    # Build final line
    # ------------------------------------------------------------
    if perfdata:
        return f"{prefix} - {message} | {perfdata}"
    elif message:
        return f"{prefix} - {message}"
    else:
        return f"{prefix}"
def build_perfdata(args, capture):
    latency = capture["response_time"]
    size = len(capture["body"]) if capture["body"] else 0

    return (
        f"time={latency:.4f}s;"
        f"{args.warning_rt};"
        f"{args.critical_rt};0; "
        f"size={size}B;"
        f"{args.warning_size};"
        f"{args.critical_size};0;"
    )
# -----------------------------
# Host Validation
# -----------------------------
def validate_host_basic(host: str):
    """
    Deterministic hostname validation used by all NMS_Tools plugins.

    Rules:
      • If the user supplies an IP → treat it as authoritative (no reverse DNS).
      • If the user supplies the system hostname → resolve it once.
      • Otherwise → attempt forward resolution only.
      • Never perform reverse lookups.
      • Never replace an IP with a hostname.
      • All failures return UNKNOWN-level errors (caller decides exit).

    Returns:
        {
            "ok": bool,
            "ip": str or None,
            "error": str or None
        }
    """

    host = host.strip()

    # ------------------------------------------------------------
    # 1. IP address case (authoritative)
    # ------------------------------------------------------------
    try:
        ip_obj = ipaddress.ip_address(host)
        return {
            "ok": True,
            "ip": str(ip_obj),   # return IP exactly as supplied
            "error": None
        }
    except ValueError:
        pass  # Not an IP, continue

    # ------------------------------------------------------------
    # 2. Local hostname case (special deterministic rule)
    # ------------------------------------------------------------
    system_hostname = socket.gethostname()

    if host.lower() == system_hostname.lower():
        try:
            resolved = socket.gethostbyname(system_hostname)
            return {
                "ok": True,
                "ip": resolved,
                "error": None
            }
        except Exception:
            return {
                "ok": False,
                "ip": None,
                "error": (
                    f"Hostname '{host}' matches local hostname but "
                    f"cannot be resolved by the system resolver"
                )
            }

    # ------------------------------------------------------------
    # 3. Normal hostname → forward resolution only
    # ------------------------------------------------------------
    try:
        resolved = socket.gethostbyname(host)
        return {
            "ok": True,
            "ip": resolved,
            "error": None
        }
    except Exception:
        return {
            "ok": False,
            "ip": None,
            "error": f"Hostname resolution failed for '{host}'"
        }
# --------------------------------------
# Logging Functions
# --------------------------------------
def initialize_logger(args, mode):
    """
    Unified LoggerFactory initialization for check_cert.
    Matches the model used by check_ticker.
    """

    # Nagios mode never writes logs
    if mode == "nagios" or not args.log_dir:
        return None

    try:
        os.makedirs(args.log_dir, exist_ok=True)

        log_cfg = {
            "path": os.path.join(args.log_dir, f"{SCRIPT_NAME}.log"),
            "log_level": "INFO",
            "log_max_mb": args.log_max_mb,
            "archive_mode": "zip",
            "backup_count": 7,

            # Console output only when verbose AND not quiet
            "console_stream": sys.stderr,
            "console_enabled": not args.quiet and args.verbose,

            # Nagios mode never uses color
            "color": False if mode == "nagios" else args.color,
        }

        logger_factory = LoggerFactory(log_cfg, SCRIPT_NAME)
        return logger_factory.get_logger("main")

    except Exception as e:
        if should_output(mode):
            print(nagios_summary(UNKNOWN, f"Failed to initialize LoggerFactory: {e}"))
        return None
# -----------------------------
# Main Function
# -----------------------------
def main():
    args, flags, mode = build_parser()
    # Base metadata (script name, mode, log_dir)
    meta = {
        "host": args.host,
        "log_dir": str(Path(args.log_dir).expanduser()) if args.log_dir else None,
        "flags": flags,
        "mode": mode,
    }
    logger = initialize_logger(args, meta["mode"])
    logging_enabled = mode != "nagios" and meta["log_dir"]

    # ------------------------------------------------------------
    # Hostname validation (suite-wide deterministic rule)
    # ------------------------------------------------------------
    rc = validate_host_basic(args.host)
    if not rc["ok"]:
        early_exit(meta, f"UNKNOWN - {rc['error']}", UNKNOWN)


    # Track whether the operator explicitly set -p/--port
    args.port_was_explicit = args.port is not None

    # Normalize port based on protocol
    if args.port is None:
        args.port = 443 if args.https else 80

    protocol, url = determine_protocol_and_url(args)
    capture = capture_http_response(url, protocol, args)    
    backend = detect_backend(capture)
    meta.update(build_html_meta(capture, backend, args))
    backend_status, backend_message = enforce_backend_rules(backend, args)
    status_status, status_message = enforce_status_rules(capture)
    ct_status, ct_message = enforce_content_type_rules(capture)
    html_status, html_message = enforce_html_rules(capture)

    failure_map = {
        "backend": backend_status,
        "status": status_status,
        "content_type": ct_status,
        "html": html_status,
    }

    failures = [name for name, code in failure_map.items() if code != OK]
    checks = {
        "backend": {"status": backend_status, "message": backend_message},
        "status": {"status": status_status, "message": status_message},
        "content_type": {"status": ct_status, "message": ct_message},
        "html": {"status": html_status, "message": html_message},
    }
   
    result = build_result_object(capture, backend, checks, failures)
    # -------------------------------------------------
    # Add perfdata to metadata (for logging only)
    # -------------------------------------------------
    capture = result.get("capture", {})
    rt = capture.get("response_time") or 0
    body = capture.get("body") or ""
    size = len(body.encode("utf-8"))

    perf = {
        "latency": rt,
        "size": size,
        "warning_rt": args.warning_rt,
        "critical_rt": args.critical_rt,
        "warning_size": args.warning_size,
        "critical_size": args.critical_size,
        "string": build_perfdata(args, capture)
    }
    # Add to result (for JSON)
    result["perfdata"] = perf

    # Add to meta (for logging)
    meta["perfdata"] = perf

    # -------------------------------------------------
    # Logging if not Nagios mode and log-dir specified
    # -------------------------------------------------
    if logger and logging_enabled:
        logger.info(start_banner(SCRIPT_NAME, meta))
        logger.info(html_banner(meta, result))
        logger.info(result_banner(result["overall"]["status"], result["failures"]))
        logger.info(end_banner(SCRIPT_NAME, result["overall"]["status"]))
    
    match mode:
        case "verbose":
            print_verbose(result)
            os._exit(result["overall"]["status"])
        case "json":
            print(json.dumps(result, indent=2))
            os._exit(result["overall"]["status"])
        case "nagios":
            print(single_line(result, args))
            os._exit(result["overall"]["status"])
        case "quiet":
            early_exit(meta, logger, "", result["overall"]["status"])
        case _:
            print(single_line(result, args))
            os._exit(result["overall"]["status"])

if __name__ == "__main__":
    if sys.version_info < (MIN_MAJOR, MIN_MINOR):
        print(f"CRITICAL: Python {MIN_MAJOR}.{MIN_MINOR}+ required, "
            f"but running on {sys.version_info.major}.{sys.version_info.minor}")
        sys.exit(2)
    main()
