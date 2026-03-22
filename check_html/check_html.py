#!/usr/bin/env python3
"""
File: check_html.py
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-03-21
Modified: 2026-03-22
Required: Python 3.6+
Description:
    HTML content checker with status-code enforcement, required-tag checks,
    content-type validation, quiet/verbose modes, and JSON output.
"""

import sys
import socket
import ipaddress
import argparse
import platform
import time
import ssl
import json
import http.client

from typing import Optional
from urllib.parse import urlparse

# Nagios Exit Codes
OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3
# Other Global Constants
SCRIPT_VERSION = "1.0.1"
BACKEND_SIGNATURES = {
    "tomcat": {
        "headers": [
            "apache-coyote",
            "tomcat",
            "coyote"
        ],
        "html": [
            "apache tomcat",
            "org.apache.catalina",
            "tomcat manager"
        ],
        "ports": [8080]  # weak heuristic
    },

    "apache": {
        "headers": ["apache"],
        "html": ["apache server at"],
        "ports": [80, 8080]
    },

    "nginx": {
        "headers": ["nginx"],
        "html": ["nginx"],
        "ports": [80]
    },

    "iis": {
        "headers": ["microsoft-iis"],
        "html": ["iis", "microsoft"],
        "ports": [80, 443]
    },

    "jetty": {
        "headers": ["jetty"],
        "html": ["powered by jetty"],
        "ports": [8080]
    },

    "express": {
        "headers": ["express"],
        "html": [],
        "ports": []
    },

    "gunicorn": {
        "headers": ["gunicorn"],
        "html": [],
        "ports": []
    }
}
# -----------------------------
# Custom Error Classes
# -----------------------------
class HttpFetchError(Exception):
    pass
# -----------------------------
# Custom Formatter
# -----------------------------
class CustomFormatter(
    argparse.ArgumentDefaultsHelpFormatter,
    argparse.RawDescriptionHelpFormatter
):
    def _get_help_string(self, action):
        help_text = action.help or ""
        if "%(default)" in help_text:
            return help_text
        if action.default in (None, False):
            return help_text
        return f"{help_text} (default: {action.default})"
class CheckArgError(Exception):
    pass
class CheckArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        print(f"ERROR: {message}\n")
        self.print_help()
        sys.exit(UNKNOWN)
# -----------------------------
# CLI Parser
# -----------------------------
def build_parser():
    parser = CheckArgumentParser(
        description=(
            "HTTP/HTML Inspection Tool\n\n"
            "Fetches a webpage, validates status code, content-type, required tags,\n"
            "backend fingerprinting (Tomcat/Apache/Nginx), redirect behavior, and\n"
            "optional enforcement rules. Supports verbose, JSON, and Nagios output."
        ),
        formatter_class=CustomFormatter,
        add_help=True
    )

    parser.usage = "check_http.py -H <host> [options]"

    # ------------------------------------------------------------
    # Connection Options
    # ------------------------------------------------------------
    conn = parser.add_argument_group("Connection Options")
    conn.add_argument("-H", "--host", required=True,
                      help="Target hostname or URL")
    conn.add_argument("-p", "--port", type=int, default=80,
                      help="Port to connect to")
    conn.add_argument("--https", action="store_true",
                      help="Force HTTPS request")
    conn.add_argument("--timeout", type=int, default=5,
                      help="Connection timeout in seconds")
    conn.add_argument("--no-redirect", action="store_true",
                      help="Do not follow redirects")
    conn.add_argument("--max-redirects", type=int, default=5,
                      help="Maximum number of redirects allowed")

    # ------------------------------------------------------------
    # Output Modes
    # ------------------------------------------------------------
    out = parser.add_argument_group("Output Modes")
    out.add_argument("-v", "--verbose", action="store_true",
                     help="Detailed output")
    out.add_argument("-j", "--json", action="store_true",
                     help="JSON output for automation")
    out.add_argument("-q", "--quiet", action="store_true",
                     help="Quiet mode: exit code only")
    out.add_argument("-V", "--version", action="version",
                     version=f"check_http.py {SCRIPT_VERSION} (Python {platform.python_version()})",
                     help="Show script and Python version")

    # ------------------------------------------------------------
    # HTTP Status Requirements
    # ------------------------------------------------------------
    status = parser.add_argument_group("HTTP Status")
    status.add_argument("--expect-status", type=int, default=200,
                        help="Expected HTTP status code")
    status.add_argument("--expect-family", type=str,
                        help="Expected status code family (e.g., 2xx)")
    status.add_argument("--forbid-status", type=int,
                        help="Fail if this status code is returned")

    # ------------------------------------------------------------
    # Content-Type Requirements
    # ------------------------------------------------------------
    ctype = parser.add_argument_group("Content-Type Requirements")
    ctype.add_argument("--require-content-type", default="text/html",
                       help="Required Content-Type header")
    ctype.add_argument("--forbid-content-type",
                       help="Fail if this Content-Type is returned")

    # ------------------------------------------------------------
    # HTML Content Requirements
    # ------------------------------------------------------------
    html = parser.add_argument_group("HTML Requirements")
    html.add_argument("--require-tag", action="append",
                      help="Require specific HTML tag (repeatable)")
    html.add_argument("--forbid-tag", action="append",
                      help="Forbid specific HTML tag (repeatable)")
    html.add_argument("--require-text", action="append",
                      help="Require specific text in the page (repeatable)")
    html.add_argument("--forbid-text", action="append",
                      help="Forbid specific text in the page (repeatable)")
    html.add_argument("--max-size", type=int,
                      help="Maximum allowed page size in bytes")

    # ------------------------------------------------------------
    # Backend Fingerprinting
    # ------------------------------------------------------------
    backend = parser.add_argument_group("Backend Fingerprinting")

    # Individual backend enforcement flags (Nagios-style)
    backend.add_argument("--require-tomcat", action="store_true",
                        help="Require backend to be Apache Tomcat")
    backend.add_argument("--forbid-tomcat", action="store_true",
                        help="Fail if backend is Apache Tomcat")

    backend.add_argument("--require-apache", action="store_true",
                        help="Require backend to be Apache HTTPD")
    backend.add_argument("--forbid-apache", action="store_true",
                        help="Fail if backend is Apache HTTPD")

    backend.add_argument("--require-nginx", action="store_true",
                        help="Require backend to be Nginx")
    backend.add_argument("--forbid-nginx", action="store_true",
                        help="Fail if backend is Nginx")

    backend.add_argument("--require-iis", action="store_true",
                        help="Require backend to be Microsoft IIS")
    backend.add_argument("--forbid-iis", action="store_true",
                        help="Fail if backend is Microsoft IIS")

    backend.add_argument("--require-jetty", action="store_true",
                        help="Require backend to be Jetty")
    backend.add_argument("--forbid-jetty", action="store_true",
                        help="Fail if backend is Jetty")

    backend.add_argument("--require-express", action="store_true",
                        help="Require backend to be Node.js/Express")
    backend.add_argument("--forbid-express", action="store_true",
                        help="Fail if backend is Node.js/Express")

    backend.add_argument("--require-gunicorn", action="store_true",
                        help="Require backend to be Gunicorn")
    backend.add_argument("--forbid-gunicorn", action="store_true",
                        help="Fail if backend is Gunicorn")

    # Generic backend selector (BotScanner-style)
    backend.add_argument(
        "--require-backend",
        action="append",
        choices=[
            "tomcat", "apache", "nginx", "iis",
            "jetty", "express", "gunicorn"
        ],
        help="Require backend to match one of the specified types (repeatable)"
    )

    backend.add_argument(
        "--forbid-backend",
        action="append",
        choices=[
            "tomcat", "apache", "nginx", "iis",
            "jetty", "express", "gunicorn"
        ],
        help="Fail if backend matches any of the specified types (repeatable)"
    )

    # ------------------------------------------------------------
    # HTTPS / Security Requirements
    # ------------------------------------------------------------
    sec = parser.add_argument_group("Security Requirements")
    sec.add_argument("--require-https", action="store_true",
                     help="Fail if HTTPS is not used")
    sec.add_argument("--require-https-redirect", action="store_true",
                     help="Require HTTP to redirect to HTTPS")
    sec.add_argument("--require-hsts", action="store_true",
                     help="Require Strict-Transport-Security header")
    sec.add_argument("--require-header", action="append",
                     help="Require specific header (Header:Value)")

    # ------------------------------------------------------------
    # Nagios Thresholds
    # ------------------------------------------------------------
    nagios = parser.add_argument_group("Nagios Thresholds")
    nagios.add_argument("--warning-rt", type=float,
                        help="Warning threshold for response time (seconds)")
    nagios.add_argument("--critical-rt", type=float,
                        help="Critical threshold for response time (seconds)")
    nagios.add_argument("--warning-size", type=int,
                        help="Warning threshold for page size (bytes)")
    nagios.add_argument("--critical-size", type=int,
                        help="Critical threshold for page size (bytes)")

    # ------------------------------------------------------------
    # Examples
    # ------------------------------------------------------------
    parser.epilog = (
        "Examples:\n"
        "  check_http.py -H example.com -v\n"
        "  check_http.py -H example.com --expect-status 200\n"
        "  check_http.py -H example.com --require-tomcat\n"
        "  check_http.py -H example.com --json\n"
    )

    return parser.parse_args()
def normalize_backend_list(values):
    """
    Takes a list of strings (possibly comma-separated) and returns
    a clean, lowercase, deduplicated list of backend names.
    """
    if not values:
        return []

    out = []
    for item in values:
        for part in item.split(","):
            name = part.strip().lower()
            if name:
                out.append(name)

    # Deduplicate while preserving order
    return list(dict.fromkeys(out))


def ok_exit(message):
    print(f"OK - {message}")
    sys.exit(OK)
def warning_exit(message):
    print(f"WARNING - {message}")
    sys.exit(WARNING)
def critical_exit(message):
    print(f"CRITICAL - {message}")
    sys.exit(CRITICAL)
def unknown_exit(message):
    print(f"UNKNOWN - {message}")
    sys.exit(UNKNOWN)
def nagios_priority(code):
    # Higher number = higher severity
    if code == 2:  # CRITICAL
        return 4
    if code == 1:  # WARNING
        return 3
    if code == 3:  # UNKNOWN
        return 2
    if code == 0:  # OK
        return 1
    return 0

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
def parse_url_or_fail(url: str, original_url: Optional[str]):
    """
    Parses a URL and returns a validated, deterministic structure.

    Returns:
        {
            "host": str,
            "path": str,
            "protocol": str,
            "port": int
        }

    Raises:
        HttpFetchError if hostname is missing or URL is malformed.
    """

    parsed = urlparse(url)

    raw_host = parsed.hostname
    if raw_host is None:
        bad = original_url or url
        raise HttpFetchError(f"Invalid URL: missing hostname in '{bad}'")

    host: str = raw_host
    protocol = parsed.scheme or "http"
    path = parsed.path or "/"
    port = parsed.port or (443 if protocol == "https" else 80)

    return {
        "host": host,
        "path": path,
        "protocol": protocol,
        "port": port
    }
def detect_backend(capture):
    # If TLS failed, backend detection is impossible
    if capture.get("tls_error"):
        return {
            "detected": None,
            "candidates": [],
            "confidence": "none",
            "reason": "TLS handshake failed"
        }
    headers = capture["headers"]      # already normalized
    html = capture["body"]
    port = extract_port(capture["final_url"])

    html_lower = html.lower() if html else ""

    candidates = []
    reasons = []

    # ------------------------------------------------------------
    # Header-based detection (strongest)
    # ------------------------------------------------------------
    for backend, sigs in BACKEND_SIGNATURES.items():
        for hsig in sigs["headers"]:
            for header_name, header_value in headers.items():
                if isinstance(header_value, str) and hsig in header_value.lower():
                    candidates.append(backend)
                    reasons.append(f"Header '{header_name}' contains '{hsig}'")

    # ------------------------------------------------------------
    # HTML-based detection (medium)
    # ------------------------------------------------------------
    for backend, sigs in BACKEND_SIGNATURES.items():
        for hsig in sigs["html"]:
            if hsig in html_lower:
                candidates.append(backend)
                reasons.append(f"HTML contains '{hsig}'")

    # ------------------------------------------------------------
    # Port heuristics (weak)
    # ------------------------------------------------------------
    for backend, sigs in BACKEND_SIGNATURES.items():
        if port in sigs["ports"]:
            candidates.append(backend)
            reasons.append(f"Port {port} commonly used by {backend}")

    # Deduplicate
    candidates = list(dict.fromkeys(candidates))

    # Confidence logic unchanged...

    # ------------------------------------------------------------
    # Determine confidence
    # ------------------------------------------------------------
    if not candidates:
        return {
            "detected": None,
            "candidates": [],
            "confidence": "low",
            "reason": "No backend signatures detected"
        }

    # Strongest signal: header match
    for backend in candidates:
        for hsig in BACKEND_SIGNATURES[backend]["headers"]:
            for header_value in headers.values():
                if isinstance(header_value, str) and hsig in header_value.lower():
                    return {
                        "detected": backend,
                        "candidates": candidates,
                        "confidence": "high",
                        "reason": f"Header contains '{hsig}'"
                    }

    # Medium signal: HTML match
    for backend in candidates:
        for hsig in BACKEND_SIGNATURES[backend]["html"]:
            if hsig in html_lower:
                return {
                    "detected": backend,
                    "candidates": candidates,
                    "confidence": "medium",
                    "reason": f"HTML contains '{hsig}'"
                }

    # Weak signal: port only
    return {
        "detected": candidates[0],
        "candidates": candidates,
        "confidence": "low",
        "reason": f"Only port-based heuristic matched ({port})"
    }
def extract_port(final_url: str) -> int:
    parsed = urlparse(final_url)

    # If the URL explicitly contains a port, use it
    if parsed.port is not None:
        return parsed.port

    # Otherwise infer from scheme
    return 443 if parsed.scheme == "https" else 80
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
    require = explicit_require or normalize_backend_list(args.require_backend)
    forbid  = explicit_forbid  or normalize_backend_list(args.forbid_backend)

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
def enforce_status_rules(capture, args):
    """
    Enforce HTTP status code rules.
    Returns (status_code, message) in Nagios format.
    """

    code = capture.get("status")

    # If no HTTP status exists (TLS failure, connection failure, etc.)
    if code is None:
        return (CRITICAL, "No HTTP status (TLS or connection failure)")

    # 1. Explicit OK range (200–299)
    if 200 <= code <= 299:
        return (OK, None)

    # 2. Redirects (300–399)
    if 300 <= code <= 399:
        return (WARNING, f"Redirect ({code})")

    # 3. Client errors (400–499)
    if 400 <= code <= 499:
        return (CRITICAL, f"Client error ({code})")

    # 4. Server errors (500–599)
    if 500 <= code <= 599:
        return (CRITICAL, f"Server error ({code})")

    # 5. Anything else is UNKNOWN
    return (UNKNOWN, f"Unexpected HTTP status ({code})")
def enforce_content_type_rules(capture, args):
    if capture.get("tls_error"):
        return (3, "No Content-Type (TLS failure)")
    """
    Enforce Content-Type rules.
    Currently minimal: only checks that Content-Type exists.
    Returns (status_code, message) in Nagios format.
    """

    headers = capture.get("headers", {})
    ctype = headers.get("content-type")

    # No Content-Type header at all → UNKNOWN
    if not ctype:
        return (UNKNOWN, "Missing Content-Type header")

    # Otherwise OK
    return (OK, None)
def enforce_html_rules(capture, args):
    # TLS failure means no HTML is possible
    if capture.get("tls_error"):
        return (3, "No HTML body (TLS failure)")
    """
    Enforce HTML content rules.
    Currently minimal: only checks that HTML body exists.
    Returns (status_code, message) in Nagios format.
    """

    body = capture.get("body")

    # If body is None → UNKNOWN (unexpected)
    if body is None:
        return (UNKNOWN, "Missing HTML body")

    # If body is empty → WARNING (page exists but has no content)
    if body.strip() == "":
        return (WARNING, "Empty HTML body")

    # Otherwise OK
    return (OK, None)
def build_result_object(
    capture,
    backend_info,
    backend_status,
    backend_message,
    status_status,
    status_message,
    ct_status,
    ct_message,
    html_status,
    html_message
):
    final_status = max(
        [status_status, ct_status, html_status, backend_status],
        key=nagios_priority
    )

    final_message = (
        backend_message
        or html_message
        or ct_message
        or status_message
        or "OK"
    )

    return {
        "capture": {
            "status": capture["status"],
            "headers": capture["headers"],
            "content_type": capture["headers"].get("content-type"),
            "body": capture["body"],
            "response_time": capture["response_time"],
            "final_url": capture["final_url"],
            "redirects": capture["redirects"],
            "tls_error": capture["tls_error"],
        },

        "backend": {
            "detected": backend_info["detected"],
            "candidates": backend_info["candidates"],
            "confidence": backend_info["confidence"],
            "reason": backend_info["reason"],
            "status": backend_status,
            "message": backend_message,
        },

        "content_type_check": {
            "status": ct_status,
            "message": ct_message,
        },

        "html_check": {
            "status": html_status,
            "message": html_message,
        },

        "status_check": {
            "status": status_status,
            "message": status_message,
        },

        "overall": {
            "status": final_status,
            "message": final_message,
        }
    }
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
def single_line(result):
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
        perfdata = f"time={rt:.4f}s;;;0 size={size}B;;;0"

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
# -----------------------------
# Main Function
# -----------------------------
def main():
    args = build_parser()
    # ------------------------------------------------------------
    # Hostname validation (suite-wide deterministic rule)
    # ------------------------------------------------------------
    rc = validate_host_basic(args.host)
    if not rc["ok"]:
        print(f"UNKNOWN - {rc['error']}")
        sys.exit(UNKNOWN)


    # Track whether the operator explicitly set -p/--port
    args.port_was_explicit = args.port is not None

    # Normalize port based on protocol
    if args.port is None:
        args.port = 443 if args.https else 80

    protocol, url = determine_protocol_and_url(args)
    capture = capture_http_response(url, protocol, args)    
    backend = detect_backend(capture)
    backend_status, backend_message = enforce_backend_rules(backend, args)
    status_status, status_message = enforce_status_rules(capture, args)
    ct_status, ct_message = enforce_content_type_rules(capture, args)
    html_status, html_message = enforce_html_rules(capture, args)
    
    result = build_result_object(
        capture,
        backend,
        backend_status,
        backend_message,
        status_status,
        status_message,
        ct_status,
        ct_message,
        html_status,
        html_message
    )

    # JSON mode
    if args.json:
        print(json.dumps(result, indent=2))
        sys.exit(result["overall"]["status"])

    # Verbose mode
    if args.verbose:
        print_verbose(result)
        sys.exit(result["overall"]["status"])

    # Default: Nagios single-line output
    print(single_line(result))
    sys.exit(result["overall"]["status"])

if __name__ == "__main__":
    main()
