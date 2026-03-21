#!/usr/bin/env python3
"""
File: check_cert.py
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-03-17
Modified: 2026-03-21
Required: Python 3.6+
Description:
    Certificate checker with SAN, issuer, signature algorithm, wildcard detection,
    perfdata, quiet/verbose modes, and JSON output.
"""

import urllib.request
import urllib.error
import ssl
import socket
import argparse
import sys
import json
import platform

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa, ec, ed25519, ed448
from cryptography.x509.oid import ExtensionOID, NameOID, AuthorityInformationAccessOID
from cryptography.x509.ocsp import load_der_ocsp_response  # optional, see OCSP stub
from cryptography.hazmat.primitives.asymmetric import rsa, ec, ed25519, ed448
from datetime import datetime
from typing import Tuple, Optional, List
# -----------------------------
#  Nagios Exit Codes
# -----------------------------
OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3
# Other Constants
SCRIPT_VERSION = "3.0.0"
TLS_VERSIONS = ["TLSv1", "TLSv1.1", "TLSv1.2", "TLSv1.3"]
# -----------------------------
# ArgParse Custom Formatter
# -----------------------------
class CustomFormatter(
    argparse.ArgumentDefaultsHelpFormatter,
    argparse.RawDescriptionHelpFormatter
):
    """Help formatter that removes argparse's default '(default: ...)' noise
    only when the default is None or False."""

    def _get_help_string(self, action):
        help_text = action.help or ""

        # If the help text already contains %(default), leave it alone
        if "%(default)" in help_text:
            return help_text

        # If argparse would append a default of None or False, suppress it
        if action.default in (None, False):
            return help_text

        # Otherwise, append the meaningful default
        return f"{help_text} (default: {action.default})"
    
class CheckCertArgError(Exception):
    """Raised when CLI arguments are invalid."""
    pass
class CheckCertArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise CheckCertArgError(message)

# -----------------------------
#  CLI Parser
# -----------------------------
def build_parser():
    parser = CheckCertArgumentParser(
        description=(
            "TLS Certificate Inspection Tool\n\n"
            "Performs a full TLS handshake, retrieves the server certificate and chain,\n"
            "evaluates TLS version and cipher, and applies optional enforcement rules.\n"
            "Supports verbose, JSON, and Nagios-compatible output modes."
        ),
        formatter_class=CustomFormatter,
        add_help=True
    )

    # -----------------------------
    # Usage line
    # -----------------------------
    parser.usage = "check_cert.py -H <host> [options]"

    # -----------------------------
    # Connection Options
    # -----------------------------
    conn = parser.add_argument_group("Connection Options")
    conn.add_argument("-H", "--host", required=True,
                      help="Target hostname or IP")
    conn.add_argument("-p", "--port", type=int, default=443,
                      help="Port to connect to")
    conn.add_argument("--sni",
                      help="Override SNI value (default: host)")
    conn.add_argument("--timeout", type=int, default=5,
                      help="Connection timeout in seconds")
    conn.add_argument("--insecure", action="store_true",
                      help="Skip certificate validation during handshake")

    # -----------------------------
    # Output Modes
    # -----------------------------
    out = parser.add_argument_group("Output Modes")
    out.add_argument("-v", "--verbose", action="store_true",
                     help="Detailed certificate output")
    out.add_argument("-j", "--json", action="store_true",
                     help="JSON output for automation")
    out.add_argument("-q", "--quiet", action="store_true",
                     help="Quiet mode: exit code only")
    out.add_argument("-V", "--version", action="version",
                     version=f"check_cert.py {SCRIPT_VERSION} (Python {platform.python_version()})",
                     help="Show script version and Python interpreter version")
    # -----------------------------
    # TLS Requirements
    # -----------------------------
    tls = parser.add_argument_group("TLS Requirements")
    tls.add_argument("--min-tls", choices=TLS_VERSIONS,
                     help="Minimum allowed TLS version")
    tls.add_argument("--require-tls", choices=TLS_VERSIONS,
                     help="Require exact TLS version")
    tls.add_argument("--require-cipher",
                     help="Require exact cipher suite")
    tls.add_argument("--forbid-cipher",
                     help="Forbid exact cipher suite")
    tls.add_argument("--require-aead", action="store_true",
                     help="Require AEAD cipher")
    tls.add_argument("--forbid-cbc", action="store_true",
                     help="Forbid CBC-mode ciphers")
    tls.add_argument("--forbid-rc4", action="store_true",
                     help="Forbid RC4 ciphers")

    # -----------------------------
    # Certificate Requirements
    # -----------------------------
    cert = parser.add_argument_group("Certificate Requirements")
    cert.add_argument("-E", "--enforce-san", action="store_true",
                      help="Require host to appear in SAN list")
    cert.add_argument("-I", "--issuer",
                      help="Require issuer CN to contain substring")
    cert.add_argument("-A", "--sigalg",
                      help="Require signature algorithm")
    cert.add_argument("--min-rsa", type=int,
                      help="Minimum RSA key size in bits")
    cert.add_argument("--require-curve",
                      help="Require ECC curve name")
    cert.add_argument("--require-wildcard", action="store_true",
                      help="Require wildcard certificate")
    cert.add_argument("--forbid-wildcard", action="store_true",
                      help="Forbid wildcard certificate")
    # ----------------------------
    # Nagios Options
    # ----------------------------
    nagios = parser.add_argument_group("Nagios Thresholds")
    nagios.add_argument("--warning", type=int, default=30,
                        help="Warning threshold in days")
    nagios.add_argument("--critical", type=int, default=15,
                        help="Critical threshold in days")

    # -----------------------------
    # OCSP Options
    # -----------------------------
    ocsp = parser.add_argument_group("OCSP Options")
    ocsp.add_argument("--require-ocsp", action="store_true",
                      help="OCSP responder must be reachable")
    ocsp.add_argument("--forbid-ocsp", action="store_true",
                      help="OCSP responder must NOT be reachable")
    ocsp.add_argument("--ocsp-status",
                      choices=["good", "revoked", "unknown", "invalid"],
                      help="Require specific OCSP status")

    # -----------------------------
    # Examples Section
    # -----------------------------
    parser.epilog = (
        "Examples:\n"
        "  check_cert.py -H example.com -v\n"
        "  check_cert.py -H example.com --json\n"
        "  check_cert.py -H example.com --min-tls TLSv1.2\n"
        "  check_cert.py -H example.com --require-aead --require-curve secp256r1\n"
    )

    return parser.parse_args()
# -----------------------------
#  Certificate Fetch/Parse
# -----------------------------

def fetch_certificate_and_socket(hostname: str, port: int = 443, timeout: int = 10, insecure: bool = False):
    """Perform TLS handshake using stdlib ssl and return:
       - leaf certificate (cryptography.x509)
       - empty chain (list)
       - ocsp_resp = None (OCSP unsupported)
       - TLS info (version, cipher)
    """
    try:
        if insecure:
            ctx = ssl._create_unverified_context()
        else:
            ctx = ssl.create_default_context()

        # If insecure, hostname checking is already disabled
        # If secure, we want hostname checking ON
        if insecure:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
        sock = socket.create_connection((hostname, port), timeout)
        ssock = ctx.wrap_socket(sock, server_hostname=hostname)

        der = ssock.getpeercert(binary_form=True)
        if der is None:
            raise RuntimeError("No certificate received from peer")

        pem = ssl.DER_cert_to_PEM_cert(der)
        cert = x509.load_pem_x509_certificate(pem.encode(), default_backend())

        tls_version, cipher = get_tls_info(ssock)
        cipher_info = ssock.cipher()
        cipher = cipher_info[0] if cipher_info is not None else None

        ocsp_resp = None
        chain = []  # stdlib doesn't expose full chain cleanly

        return cert, chain, tls_version, cipher
    except Exception as e:
        raise RuntimeError(f"TLS handshake or certificate retrieval failed: {e}")

def fetch_aia_certificate(url, timeout=5):
    """
    Fetch an intermediate certificate from an AIA URL.
    Returns raw certificate bytes (DER or PEM).
    Returns None on failure.
    """

    # Deterministic user-agent
    headers = {
        "User-Agent": "NMS_Tools/1.0 (AIA Fetcher)"
    }

    req = urllib.request.Request(url, headers=headers)

    try:
        # AIA URLs are HTTP, not HTTPS — but we still set a context for consistency
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.read()

    except urllib.error.HTTPError as e:
        # 404, 403, etc.
        return None

    except urllib.error.URLError as e:
        # DNS failure, timeout, refused connection
        return None

    except Exception:
        # Any other unexpected failure
        return None
def parse_cert_bytes(raw):
    try:
        # PEM
        if raw.startswith(b"-----BEGIN CERTIFICATE-----"):
            return x509.load_pem_x509_certificate(raw, default_backend())
        # DER
        else:
            return x509.load_der_x509_certificate(raw, default_backend())
    except Exception:
        return None    
def parse_intermediate_cert(url, raw_bytes):
    """
    Parse an intermediate certificate fetched via AIA.
    Returns a dict with parsed fields or an error entry.
    """

    entry = {"url": url}

    if raw_bytes is None:
        entry["error"] = "fetch_failed"
        return entry

    cert_obj = parse_cert_bytes(raw_bytes)
    if cert_obj is None:
        entry["error"] = "parse_failed"
        return entry

    # Extract fields
    subject_cn = get_subject_cn(cert_obj)
    issuer_cn = get_issuer_cn(cert_obj)
    algo = cert_obj.signature_hash_algorithm
    sigalg = algo.name if algo is not None else cert_obj.signature_algorithm_oid._name
    key_type, key_bits, curve = get_key_info(cert_obj)

    # Extract OCSP URLs
    ocsp_urls = get_ocsp_urls(cert_obj)

    entry.update({
        "subject_cn": subject_cn,
        "issuer_cn": issuer_cn,
        "signature_algorithm": sigalg,
        "key_type": key_type,
        "ocsp_urls": ocsp_urls,
    })

    return entry

# -----------------------------
#  Extractors
# -----------------------------
def get_cert_expiry(cert):
    return cert.not_valid_after

def get_cn(cert_obj):
    try:
        return cert_obj.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
    except Exception:
        return None

def get_key_info(cert: x509.Certificate) -> Tuple[str, Optional[int], Optional[str]]:
    """
    Returns (key_type, key_bits, curve) in a deterministic format.
    - RSA: ('rsa', bits, None)
    - EC: ('ecdsa', None, curve_name)
    - Ed25519/Ed448: ('ed25519'/'ed448', None, None)
    - Fallback: ('unknown', None, None)
    """
    pub = cert.public_key()

    # RSA
    if isinstance(pub, rsa.RSAPublicKey):
        return ("rsa", pub.key_size, None)

    # Elliptic Curve (ECDSA)
    if isinstance(pub, ec.EllipticCurvePublicKey):
        curve_name = pub.curve.name.lower()
        return ("ecdsa", None, curve_name)

    # Ed25519
    if isinstance(pub, ed25519.Ed25519PublicKey):
        return ("ed25519", None, None)

    # Ed448
    if isinstance(pub, ed448.Ed448PublicKey):
        return ("ed448", None, None)

    # Fallback
    return ("unknown", None, None)

def get_ocsp_status(cert: x509.Certificate, timeout: float = 1.0) -> str:
    """
    Returns OCSP reachability status:
    - 'reachable' if TCP connect to OCSP responder succeeds
    - 'unreachable' if connect fails
    - 'none' if no OCSP URL is present
    """
    # Extract OCSP URL from AIA
    try:
        aia = cert.extensions.get_extension_for_oid(ExtensionOID.AUTHORITY_INFORMATION_ACCESS).value
    except x509.ExtensionNotFound:
        return "none"

    ocsp_urls = [
        desc.access_location.value
        for desc in aia
        if desc.access_method == AuthorityInformationAccessOID.OCSP
    ]

    if not ocsp_urls:
        return "none"

    ocsp_url = ocsp_urls[0]

    # Parse host/port from URL
    try:
        # Example: http://ocsp.int-x3.letsencrypt.org
        host = ocsp_url.split("://", 1)[1].split("/", 1)[0]
        if ":" in host:
            hostname, port = host.split(":", 1)
            port = int(port)
        else:
            hostname, port = host, 80
    except Exception:
        return "unreachable"

    # Attempt TCP connection
    try:
        with socket.create_connection((hostname, port), timeout=timeout):
            return "reachable"
    except Exception:
        return "unreachable"
    
def get_san_list(cert):
    try:
        san = cert.extensions.get_extension_for_oid(ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
        return san.value.get_values_for_type(x509.DNSName)
    except x509.ExtensionNotFound:
        return []

def get_issuer_cn(cert):
    try:
        for attr in cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME):
            return attr.value
    except Exception:
        return None
    return None

def get_subject_cn(cert):
    try:
        for attr in cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME):
            return attr.value
    except Exception:
        return None
    return None

def get_signature_algorithm(cert: x509.Certificate) -> str:
    """
    Returns a deterministic signature algorithm name for any certificate.
    - RSA/ECDSA: returns the hash name (e.g., 'sha256')
    - Ed25519/Ed448: returns the algorithm name (e.g., 'ed25519')
    - Fallback: OID name
    """
    # Case 1: Algorithms with a hash (RSA, ECDSA)
    algo = cert.signature_hash_algorithm
    if algo is not None:
        return algo.name.lower()

    # Case 2: Algorithms without a hash (Ed25519, Ed448)
    oid_name = cert.signature_algorithm_oid._name
    if oid_name:
        return oid_name.lower()

    # Case 3: Absolute fallback (should never happen)
    return cert.signature_algorithm_oid.dotted_string

def get_ocsp_urls(cert_obj):
    urls = []
    try:
        aia = cert_obj.extensions.get_extension_for_oid(
            AuthorityInformationAccessOID.AUTHORITY_INFORMATION_ACCESS
        ).value

        for desc in aia:
            if desc.access_method == AuthorityInformationAccessOID.OCSP:
                urls.append(desc.access_location.value)
    except Exception:
        pass

    return urls

def get_tls_info(ssock) -> Tuple[str, Optional[str]]:
    """
    Returns (tls_version, cipher) in a normalized, deterministic format.
    - tls_version: 'tls1.3', 'tls1.2', etc.
    - cipher: canonical OpenSSL cipher name or None
    """
    # Normalize TLS version
    version = ssock.version()
    tls_version = version.lower() if version else "unknown"

    # Normalize cipher
    cipher_info = ssock.cipher()
    cipher = cipher_info[0] if cipher_info else None

    return tls_version, cipher


def is_wildcard_cert(cert):
    san_list = get_san_list(cert)
    if any(name.startswith("*.") for name in san_list):
        return True

    try:
        for attr in cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME):
            if attr.value.startswith("*."):
                return True
    except Exception:
        pass

    return False

# --------------------------------------
#  Classification/Enforcement/Validation
# --------------------------------------
def classify(days: int, warn: int, crit: int) -> str:
    if days < 0:
        return "expired"
    if days <= crit:
        return "critical"
    if days <= warn:
        return "warning"
    return "ok"

def run_enforcement_checks(args, meta):
    """
    Evaluate all enforcement rules and return raw results.
    meta = extracted certificate metadata.
    """

    results: dict[str, bool | None | list[str]] = {
        "min_tls": None,
        "require_tls": None,
        "require_cipher": None,
        "forbid_cipher": None,
        "require_aead": None,
        "forbid_cbc": None,
        "forbid_rc4": None,
        "enforce_san": None,
        "issuer": None,
        "sigalg": None,
        "min_rsa": None,
        "require_curve": None,
        "require_wildcard": None,
        "forbid_wildcard": None,
        "require_ocsp": None,
        "forbid_ocsp": None,
        "ocsp_status": None,
        "errors": [],   # this one is a list
    }

    # --- TLS Requirements ---
    results["min_tls"] = (
        None if not args.min_tls
        else tls_version_rank(meta["tls_version"]) >= tls_version_rank(args.min_tls)
    )

    results["require_tls"] = (
        None if not args.require_tls
        else meta["tls_version"] == args.require_tls
    )

    results["require_cipher"] = (
        None if not args.require_cipher
        else meta["cipher"] == args.require_cipher
    )

    results["forbid_cipher"] = (
        None if not args.forbid_cipher
        else meta["cipher"] != args.forbid_cipher
    )

    results["require_aead"] = (
        None if not args.require_aead
        else meta["cipher_is_aead"]
    )

    results["forbid_cbc"] = (
        None if not args.forbid_cbc
        else not meta["cipher_is_cbc"]
    )

    results["forbid_rc4"] = (
        None if not args.forbid_rc4
        else not meta["cipher_is_rc4"]
    )

    # --- Certificate Requirements ---
    results["enforce_san"] = (
        None if not args.enforce_san
        else meta["hostname_in_san"]
    )

    results["issuer"] = (
        None if not args.issuer
        else args.issuer.lower() in meta["issuer_cn"].lower()
    )

    results["sigalg"] = (
        None if not args.sigalg
        else meta["signature_algorithm"].lower() == args.sigalg.lower()
    )

    results["min_rsa"] = (
        None if not args.min_rsa
        else (meta["key_type"] == "rsa" and meta["rsa_bits"] >= args.min_rsa)
    )

    results["require_curve"] = (
        None if not args.require_curve
        else (meta["key_type"] == "ecdsa" and meta["ecc_curve"] == args.require_curve)
    )

    results["require_wildcard"] = (
        None if not args.require_wildcard
        else meta["wildcard"]
    )

    results["forbid_wildcard"] = (
        None if not args.forbid_wildcard
        else not meta["wildcard"]
    )

    # --- OCSP Requirements ---
    results["require_ocsp"] = (
        None if not args.require_ocsp
        else meta["ocsp_reachable"]
    )

    results["forbid_ocsp"] = (
        None if not args.forbid_ocsp
        else not meta["ocsp_reachable"]
    )

    results["ocsp_status"] = (
        None if not args.ocsp_status
        else meta["ocsp_status"] == args.ocsp_status
    )

    return results

def validate_chain(cert: x509.Certificate, chain: List[x509.Certificate]) -> Tuple[bool, List[str]]:
    """
    Validates certificate chain structure.
    Returns (chain_ok, warnings).
    """
    warnings = []

    # Case 1: Self-signed certificate
    if cert.issuer == cert.subject:
        warnings.append("self_signed")
        return (False, warnings)

    # Case 2: No intermediates provided
    if not chain:
        warnings.append("missing_intermediate")
        return (False, warnings)

    # Case 3: Check ordering and issuer/subject linkage
    full_chain = [cert] + chain
    for i in range(len(full_chain) - 1):
        child = full_chain[i]
        parent = full_chain[i + 1]

        if child.issuer != parent.subject:
            warnings.append("issuer_mismatch")

    # Case 4: If chain is out of order
    # (simple heuristic: if issuer of leaf matches neither subject of first intermediate nor leaf itself)
    if cert.issuer != chain[0].subject:
        warnings.append("chain_out_of_order")

    chain_ok = len(warnings) == 0
    return (chain_ok, warnings)

def check_ocsp_reachability(url, timeout=5):
    """
    Returns:
        "reachable"   – HTTP 200/301/302
        "unreachable" – DNS failure, TCP failure, timeout, non-200
        "none"        – no OCSP URL provided
    """

    if not url:
        return "none"

    try:
        parsed = urllib.parse.urlparse(url)
        host = parsed.hostname
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        path = parsed.path or "/"

        # DNS resolution
        try:
            socket.gethostbyname(host)
        except Exception:
            return "unreachable"

        # TCP connect
        s = socket.create_connection((host, port), timeout=timeout)

        # Minimal HTTP GET
        req = f"GET {path} HTTP/1.0\r\nHost: {host}\r\n\r\n"
        s.send(req.encode("ascii"))
        resp = s.recv(1024).decode("latin1", errors="ignore")
        s.close()

        if resp.startswith("HTTP/1.1 200") or resp.startswith("HTTP/1.0 200"):
            return "reachable"
        if resp.startswith("HTTP/1.1 301") or resp.startswith("HTTP/1.1 302"):
            return "reachable"

        return "unreachable"

    except Exception:
        return "unreachable"

def build_enforcement_dict(args, results) -> dict:
    """
    Build a deterministic enforcement dictionary for verbose, JSON, and Nagios modes.

    `args`    = argparse Namespace
    `results` = dict of individual enforcement check results, e.g.:
        {
            "min_tls": True/False/None,
            "require_tls": True/False/None,
            "require_cipher": True/False/None,
            "forbid_cipher": True/False/None,
            "require_aead": True/False/None,
            "forbid_cbc": True/False/None,
            "forbid_rc4": True/False/None,
            "enforce_san": True/False/None,
            "issuer": True/False/None,
            "sigalg": True/False/None,
            "min_rsa": True/False/None,
            "require_curve": True/False/None,
            "require_wildcard": True/False/None,
            "forbid_wildcard": True/False/None,
            "require_ocsp": True/False/None,
            "forbid_ocsp": True/False/None,
            "ocsp_status": True/False/None,
            "errors": [ ... ]
        }
    """

    applied = []
    passed = []
    failed = []
    errors = []

    # Map CLI flags to human-readable rule names
    rule_map = {
        "min_tls":          args.min_tls,
        "require_tls":      args.require_tls,
        "require_cipher":   args.require_cipher,
        "forbid_cipher":    args.forbid_cipher,
        "require_aead":     args.require_aead,
        "forbid_cbc":       args.forbid_cbc,
        "forbid_rc4":       args.forbid_rc4,
        "enforce_san":      args.enforce_san,
        "issuer":           args.issuer,
        "sigalg":           args.sigalg,
        "min_rsa":          args.min_rsa,
        "require_curve":    args.require_curve,
        "require_wildcard": args.require_wildcard,
        "forbid_wildcard":  args.forbid_wildcard,
        "require_ocsp":     args.require_ocsp,
        "forbid_ocsp":      args.forbid_ocsp,
        "ocsp_status":      args.ocsp_status,
    }

    # Build applied/passed/failed lists
    for rule, value in rule_map.items():
        if value is None or value is False:
            continue  # rule not requested

        applied.append(f"{rule}={value}" if value not in (True, False) else rule)

        result = results.get(rule)
        if result is True:
            passed.append(f"{rule}={value}" if value not in (True, False) else rule)
        elif result is False:
            failed.append(f"{rule}={value}" if value not in (True, False) else rule)

    # Collect enforcement errors
    if "errors" in results and results["errors"]:
        errors.extend(results["errors"])

    return {
        "applied": applied,
        "passed": passed,
        "failed": failed,
        "errors": errors,
    }

# -----------------------------
#  Status Dispatcher + Perfdata
# -----------------------------
def handle_status(status, days, expiry, warn, crit, quiet=False):
    handlers = {
        "expired": lambda: (f"CRITICAL - certificate expired {abs(days)} days ago ({expiry} UTC)", CRITICAL),
        "critical": lambda: (f"CRITICAL - {days} days remaining ({expiry} UTC)", CRITICAL),
        "warning": lambda: (f"WARNING - {days} days remaining ({expiry} UTC)", WARNING),
        "ok":       lambda: (f"OK - {days} days remaining ({expiry} UTC)", OK),
    }

    message, code = handlers[status]()

    perfdata = f"days_remaining={days};{warn};{crit};0;"

    if quiet:
        print(f"{code}")
    else:
        print(f"{message} | {perfdata}")

    sys.exit(code)

def is_aead_cipher(cipher: Optional[str]) -> bool:
    if not cipher:
        return False
    return cipher.startswith("TLS_") and ("GCM" in cipher or "CHACHA20" in cipher)

def is_cbc_cipher(cipher: Optional[str]) -> bool:
    if not cipher:
        return False
    return "CBC" in cipher

def is_rc4_cipher(cipher: Optional[str]) -> bool:
    if not cipher:
        return False
    return "RC4" in cipher

def is_self_signed(cert):
    return cert.issuer == cert.subject

def get_aia_issuer_urls(cert):
    try:
        aia = cert.extensions.get_extension_for_oid(ExtensionOID.AUTHORITY_INFORMATION_ACCESS)
        urls = []
        for desc in aia.value:
            if desc.access_method.dotted_string == "1.3.6.1.5.5.7.48.2":  # caIssuers
                urls.append(desc.access_location.value)
        return urls
    except Exception:
        return []

TLS_ORDER = {
    "TLSv1": 1,
    "TLSv1.1": 2,
    "TLSv1.2": 3,
    "TLSv1.3": 4,
}

def tls_version_rank(version: str):
    return TLS_ORDER.get(version, 0)

# -----------------------------
# Populate Warnings/Errors
# -----------------------------
def populate_warnings(data: dict) -> list:
    warnings = []
    expiration_days = data.get("expiration_days", 0)
    sigalg = data.get("sigalg")
    tls_version = data.get("tls_version")
    if expiration_days < 30:
        warnings.append(f"certificate_expires_soon: {expiration_days} days")
    key_type = data.get("key_type")
    key_bits = data.get("key_bits")

    if key_type == "rsa" and isinstance(key_bits, int) and key_bits < 2048:
        warnings.append(f"weak_rsa_key: {key_bits} bits")

    if sigalg in ("sha1", "md5"):
        warnings.append(f"deprecated_signature_algorithm: {sigalg}")
    if tls_version in ("tls1", "tls1.1"):
        warnings.append(f"weak_tls_version: {tls_version}")
    if data.get("cipher") is None:
        warnings.append("no_cipher_negotiated")
    if data.get("ocsp_status") == "unreachable":
        warnings.append("ocsp_unreachable")
    return warnings
def populate_errors(data: dict) -> list:
    errors = []
    expiration_days = data.get("expiration_days", 0)
    if expiration_days < 0:
        errors.append("certificate_expired")
    if not data.get("chain_ok"):
        errors.append("chain_invalid")
    if data.get('tls_version') is None:
        errors.append("tls_handshake_failed")
    if data.get("cert") is None:
        errors.append("no_certificate_present")
    return errors
# -----------------------------
# Display Verbose
# -----------------------------
def display_verbose(data):
    """Pretty, operator-grade verbose output."""

    host = data.get("host")
    port = data.get("port")
    sni = data.get("sni") or host
    timeout = data.get("timeout")
    insecure = data.get("insecure")

    tls_version = data.get("tls_version")
    cipher = data.get("cipher")

    issuer_cn = data.get("issuer_cn")
    sigalg = data.get("signature_algorithm")
    wildcard = data.get("wildcard")
    san_list = data.get("san", [])

    expires = data.get("expires")
    key_type = data.get("key_type")
    rsa_bits = data.get("rsa_bits")
    ecc_curve = data.get("ecc_curve")
    self_signed = data.get("self_signed")

    chain_present = data.get("chain_present")
    aia_issuer_urls = data.get("aia_issuer_urls", [])
    aia_chain = data.get("aia_chain", [])

    ocsp_urls = data.get("ocsp_urls", [])

    chain_reconstructed = data.get("chain_reconstructed")
    chain_valid = data.get("chain_valid")
    chain_errors = data.get("chain_errors", [])

    # -----------------------------
    # Connection
    # -----------------------------
    print("=== Connection ===")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"SNI: {sni}")
    print(f"Timeout: {timeout}")
    print(f"Insecure: {insecure}")
    print()

    # -----------------------------
    # TLS Session
    # -----------------------------
    print("=== TLS Session ===")
    print(f"TLS Version: {tls_version}")
    print(f"Cipher: {cipher}")
    print()

    # -----------------------------
    # Certificate
    # -----------------------------
    print("=== Certificate ===")
    print(f"Issuer CN: {issuer_cn}")
    print(f"Signature Algorithm: {sigalg}")
    print(f"Wildcard: {wildcard}")

    print("SAN:")
    if san_list:
        for entry in san_list:
            print(f"  - {entry}")
    else:
        print("  (none)")

    print(f"Expires: {expires}")
    print()

    # -----------------------------
    # Key Metadata
    # -----------------------------
    print("=== Key Metadata ===")
    print(f"Key Type: {key_type}")
    print(f"RSA Bits: {rsa_bits if rsa_bits else '—'}")
    print(f"ECC Curve: {ecc_curve if ecc_curve else '—'}")
    print(f"Self-Signed: {self_signed}")
    print()

    # -----------------------------
    # AIA
    # -----------------------------
    print("=== AIA ===")
    print("Issuer URLs:")
    if aia_issuer_urls:
        for url in aia_issuer_urls:
            print(f"  - {url}")
    else:
        print("  (none)")

    print("Chain:")
    if aia_chain:
        for entry in aia_chain:
            print(f"  - {entry.get('subject_cn')}")
            print(f"      Issuer: {entry.get('issuer_cn')}")
            print(f"      Algorithm: {entry.get('signature_algorithm')}")
            print(f"      Key Type: {entry.get('key_type')}")
    else:
        print("  (none)")
    print()

    # -----------------------------
    # OCSP
    # -----------------------------
    print("=== OCSP ===")
    print("Responder URLs:")
    if ocsp_urls:
        for url in ocsp_urls:
            print(f"  - {url}")
    else:
        print("  (none)")
    print()

    # -----------------------------
    # Chain Validation
    # -----------------------------
    print("=== Chain Validation ===")

    if chain_reconstructed is None:
        print("Reconstructed: Not Performed")
    else:
        print(f"Reconstructed: {'Yes' if chain_reconstructed else 'No'}")

    if chain_valid is None:
        print("Valid: Not Performed")
    else:
        print(f"Valid: {'Yes' if chain_valid else 'No'}")

    if chain_errors:
        print("Errors:")
        for err in chain_errors:
            print(f"  - {err}")
    else:
        print("Errors: None")

    print("=== General Warnings ===")
    if data.get("warnings"):
        for w in data.get("warnings"):
            print(f"  - {w}")
    else:
        print("  None")

    print("\n=== General Errors ===")
    if data.get("errors"):
        for e in data.get("errors"):
            print(f"  - {e}")
    else:
        print("  None")

        
def display_chain_summary(data):
    """High-level, operator-grade summary of certificate chain status."""

    chain_present = data.get("chain_present")
    aia_chain = data.get("aia_chain") or []
    chain_reconstructed = data.get("chain_reconstructed")
    chain_valid = data.get("chain_valid")
    chain_errors = data.get("chain_errors") or []

    print("=== Chain Summary ===")

    # 1. Did the server send a chain?
    if chain_present:
        print("Server Chain: Provided")
    else:
        print("Server Chain: Not Provided")

    # 2. Was an AIA chain fetched?
    if aia_chain:
        print("AIA Chain: Retrieved")
    else:
        print("AIA Chain: Not Retrieved")

    # 3. Was reconstruction attempted?
    if chain_reconstructed is None:
        print("Reconstruction: Not Performed")
    else:
        print(f"Reconstruction: {'Successful' if chain_reconstructed else 'Failed'}")

    # 4. Was validation attempted?
    if chain_valid is None:
        print("Validation: Not Performed")
    else:
        print(f"Validation: {'Valid' if chain_valid else 'Invalid'}")

    # 5. Errors, if any
    if chain_errors:
        print("Errors:")
        for err in chain_errors:
            print(f"  - {err}")
    else:
        print("Errors: None")

    print()
def display_enforcement_summary(enf):
    """
    High-level, operator-grade summary of enforcement results.
    `enf` should contain:
        - applied: list of enforcement rule names that were checked
        - passed: list of rule names that passed
        - failed: list of rule names that failed
        - errors: list of error strings (if any)
    """

    applied = enf.get("applied", [])
    passed = enf.get("passed", [])
    failed = enf.get("failed", [])
    errors = enf.get("errors", [])

    print("=== Enforcement Summary ===")

    # No enforcement flags used
    if not applied:
        print("No enforcement rules applied")
        print()
        return

    # Applied rules
    print("Applied Rules:")
    for rule in applied:
        print(f"  - {rule}")

    # Passed rules
    if passed:
        print("Passed:")
        for rule in passed:
            print(f"  - {rule}")
    else:
        print("Passed:")
        print("  (none)")

    # Failed rules
    if failed:
        print("Failed:")
        for rule in failed:
            print(f"  - {rule}")
    else:
        print("Failed:")
        print("  (none)")

    # Errors (if any)
    if errors:
        print("Errors:")
        for err in errors:
            print(f"  - {err}")
    else:
        print("Errors: None")

    print()

def nagios_exit(days_remaining, expiration_date, enf, args):
    # 1. Enforcement failures override everything
    if enf["failed"]:
        print(f"CRITICAL - {', '.join(enf['failed'])}")
        sys.exit(CRITICAL)

    # 2. Critical expiration threshold
    if args.critical is not None and days_remaining <= args.critical:
        print(f"CRITICAL - certificate expires in {days_remaining} days on {expiration_date}")
        sys.exit(CRITICAL)

    # 3. Warning expiration threshold
    if args.warning is not None and days_remaining <= args.warning:
        print(f"WARNING - certificate expires in {days_remaining} days on {expiration_date}")
        sys.exit(WARNING)

    # 4. OK
    print(f"OK - certificate valid, expires in {days_remaining} days on {expiration_date} UTC")
    sys.exit(OK)

def output_json(meta, enf):
    """
    Produce deterministic JSON output for monitoring and automation.
    Includes certificate metadata, chain info, OCSP, and enforcement results.
    """

    out = {
        "subject_cn": meta.get("subject_cn"),
        "issuer_cn": meta.get("issuer_cn"),
        "signature_algorithm": meta.get("signature_algorithm"),
        "key_type": meta.get("key_type"),
        "rsa_bits": meta.get("rsa_bits"),
        "ecc_curve": meta.get("ecc_curve"),
        "wildcard": meta.get("wildcard"),
        "warnings": meta.get("warnings", []),
        "errors": meta.get("errors", []),

        "san": meta.get("san", []),

        "tls_version": meta.get("tls_version"),
        "cipher": meta.get("cipher"),

        "expiration_date": meta.get("expires").split(" ")[0],
        "expiration_days": meta.get("days_remaining"),

        "ocsp": {
            "urls": meta.get("ocsp_urls", []),
            "status": meta.get("ocsp_status"),
            "reachable": meta.get("ocsp_reachable"),
        },

        "chain": {
            "server_sent": meta.get("chain_present"),
            "aia_urls": meta.get("aia_issuer_urls", []),
            "aia_chain": meta.get("aia_chain", []),
            "reconstructed": meta.get("chain_reconstructed"),
            "valid": meta.get("chain_valid"),
            "errors": meta.get("chain_errors", []),
        },

        "enforcement": {
            "applied": enf.get("applied", []),
            "passed": enf.get("passed", []),
            "failed": enf.get("failed", []),
            "errors": enf.get("errors", []),
        }
    }

    print(json.dumps(out, indent=2))

# -----------------------------
#  Main Orchestrator
# -----------------------------
def main():
    try:
        args = build_parser()
    except CheckCertArgError as e:
        print(f"UNKNOWN - invalid arguments: {e}")
        sys.exit(UNKNOWN)

    # If version was requested, argparse already printed it and exited.
    # If help was requested, argparse already printed it and exited.
    # So at this point, args is guaranteed to exist and contain required fields.

    # Now it is safe to reference args.host, args.sni, args.timeout, etc.
    try:
        cert, chain, tls_version, cipher = fetch_certificate_and_socket(
            args.sni if args.sni else args.host,
            args.port,
            args.timeout,
            args.insecure
        )
    except Exception as e:
        print(f"UNKNOWN - failed to retrieve certificate: {e}")
        sys.exit(UNKNOWN)

    ocsp_status = get_ocsp_status(cert)
    key_type, key_bits, curve = get_key_info(cert)

    expiry = get_cert_expiry(cert)
    san_list = get_san_list(cert)
    issuer_cn = get_issuer_cn(cert)
    sigalg = get_signature_algorithm(cert)
    wildcard = is_wildcard_cert(cert)
    aia_urls = get_aia_issuer_urls(cert)

    # Build data dict for enforcement
    data = {
        "cert": cert,                 # <-- REQUIRED
        "chain": chain,
        "tls_version": tls_version,
        "cipher": cipher,
        "ocsp_status": ocsp_status,
        "san": san_list,
        "issuer_cn": issuer_cn,
        "signature_algorithm": sigalg,
        "wildcard": wildcard,
        "key_type": key_type,
        "rsa_bits": key_bits,
        "ecc_curve": curve,
        "aia_urls": aia_urls,
    }
    # Fetch intermediates via AIA
    aia_chain_raw = []
    data["aia_chain"] = []

    for url in aia_urls:
        raw = fetch_aia_certificate(url)

        # Parse raw cert object for validation
        if isinstance(raw, bytes):
            try:
                cert_obj = x509.load_der_x509_certificate(raw, default_backend())
                aia_chain_raw.append(cert_obj)
            except Exception:
                pass

        # Parse JSON-safe entry for output
        entry = parse_intermediate_cert(url, raw)
        data["aia_chain"].append(entry)

    chain_ok, chain_warnings = validate_chain(cert, aia_chain_raw)

    data["chain_ok"] = chain_ok
    data["chain_warnings"] = chain_warnings
    data["oscp_urls"] = get_ocsp_urls(cert)

    not_after = cert.not_valid_after
    expiration_date = not_after.strftime("%Y-%m-%d")
    expiration_days = (not_after - datetime.utcnow()).days
    data["expiration_days"] = expiration_days

    ocsp_urls = data.get("ocsp_urls", [])

    # Pick the first OCSP URL (leaf)
    ocsp_url = ocsp_urls[0] if ocsp_urls else None

    ocsp_status = check_ocsp_reachability(ocsp_url)

    # 1. Extract metadata
    meta = {
        # Connection
        "host": args.host,
        "port": args.port,
        "sni": args.sni or args.host,
        "timeout": args.timeout,
        "insecure": args.insecure,

        # TLS
        "tls_version": tls_version,
        "cipher": cipher,
        "cipher_is_aead": is_aead_cipher(cipher),
        "cipher_is_cbc": is_cbc_cipher(cipher),
        "cipher_is_rc4": is_rc4_cipher(cipher),

        # Certificate
        "subject_cn": get_subject_cn(cert),
        "issuer_cn": issuer_cn,
        "signature_algorithm": sigalg,
        "wildcard": wildcard,
        "san": san_list,
        "expires": expiry.strftime("%Y-%m-%d %H:%M:%S"),
        "expiration_date": expiry.strftime("%Y-%m-%d"),
        "days_remaining": expiration_days,

        # Key Metadata
        "key_type": key_type,
        "rsa_bits": key_bits,
        "ecc_curve": curve,
        "self_signed": is_self_signed(cert),

        # AIA
        "aia_issuer_urls": aia_urls,
        "aia_chain": data.get("aia_chain"),

        # OCSP
        "ocsp_urls": data.get("ocsp_urls", []),
        "ocsp_status": ocsp_status,
        "ocsp_reachable": (ocsp_status == "reachable"),

        # Chain Validation
        "chain_present": len(chain) > 0,
        "chain_reconstructed": data.get("chain_reconstructed"),
        "chain_valid": data.get("chain_valid"),
        "chain_errors": data.get("chain_errors", []),
        
        # Warnings/Errors
        "warnings": populate_warnings(data),
        "errors": populate_errors(data),
    }
    # 2. Run enforcement checks
    results = run_enforcement_checks(args, meta)

    # 3. Build enforcement dictionary
    enf = build_enforcement_dict(args, results)

    # 4. Verbose mode
    if args.verbose:
        display_verbose(meta)
        display_chain_summary(meta)
        display_enforcement_summary(enf)
        return
 
    # 5. JSON mode
    if args.json:
        output_json(meta, enf)
        return

    # 6. Nagios mode
    nagios_exit(meta.get("days_remaining"), meta.get("expiration_date"), enf, args)





    
    # Expiration logic
    remaining = expiry - datetime.utcnow()
    days = remaining.days

    status = classify(days, args.warning, args.critical)
    if args.json or args.verbose:
        # JSON mode: exit with correct code, but print nothing else
        sys.exit({
            "expired": CRITICAL,
            "critical": CRITICAL,
            "warning": WARNING,
            "ok": OK,
        }[status])
    
    handle_status(status, days, expiry, args.warning, args.critical, quiet=args.quiet)


if __name__ == "__main__":
    main()
