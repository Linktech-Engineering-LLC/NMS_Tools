#!/usr/bin/env python3
"""
File: check_cert.py
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-03-17
Modified: 2026-03-19
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

# -----------------------------
#  Certificate Fetch/Parse
# -----------------------------

def fetch_certificate_and_socket(hostname: str, port: int = 443):
    """Perform TLS handshake using stdlib ssl and return:
       - leaf certificate (cryptography.x509)
       - empty chain (list)
       - ocsp_resp = None (OCSP unsupported)
       - TLS info (version, cipher)
    """
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        sock = socket.create_connection((hostname, port), timeout=10)
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

        return cert, chain, ocsp_resp, tls_version, cipher
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

def enforce(args, data):
    # Unpack for readability
    chain = data.get("chain", [])
    tls_version = data["tls_version"]
    cipher = data["cipher"]
    ocsp_status = data["ocsp_status"]
    san_list = data["san"]
    issuer_cn = data["issuer_cn"]
    sigalg = data["signature_algorithm"]
    wildcard = data["wildcard"]
    key_type = data["key_type"]
    rsa_bits = data["rsa_bits"]
    curve_name = data["ecc_curve"]
    aia_urls = data["aia_urls"]

    # -----------------------------
    # Chain validation
    # -----------------------------

    # 1. Self-signed detection
    if is_self_signed(data["cert"]):
        data["chain_warning"] = "self-signed certificate"

    # 2. Missing intermediates (server sent only leaf)
    if not chain and aia_urls:
        data["chain_warning"] = "missing intermediates"

    # 3. Issuer mismatch (rare but important)
    if data["issuer_cn"] is None:
        data["chain_warning"] = "Unknown Issuer"

    # OCSP enforcement
    ocsp_status = data["ocsp_status"]

    # --require-ocsp means: OCSP must be reachable
    if args.require_ocsp:
        if ocsp_status != "reachable":
            print("UNKNOWN - OCSP responder not reachable")
            sys.exit(UNKNOWN)

    # --forbid-ocsp means: OCSP must NOT be reachable
    if args.forbid_ocsp:
        if ocsp_status == "reachable":
            print("UNKNOWN - OCSP responder reachable but --forbid-ocsp was used")
            sys.exit(UNKNOWN)

    if args.ocsp_status and ocsp_status != args.ocsp_status:
        print(f"UNKNOWN - OCSP status '{ocsp_status}' does not match required '{args.ocsp_status}'")
        sys.exit(UNKNOWN)

    # TLS version enforcement
    if args.require_tls:
        if tls_version != args.require_tls:
            print(f"UNKNOWN - TLS version '{tls_version}' does not match required '{args.require_tls}'")
            sys.exit(UNKNOWN)

    if args.min_tls:
        if tls_version is None:
            print("UNKNOWN - TLS version could not be determined")
            sys.exit(UNKNOWN)

        if tls_version_rank(tls_version) < tls_version_rank(args.min_tls):
            print(f"UNKNOWN - TLS version '{tls_version}' is below minimum '{args.min_tls}'")
            sys.exit(UNKNOWN)

    # Cipher suite enforcement
    if args.require_cipher:
        if cipher != args.require_cipher:
            print(f"UNKNOWN - cipher '{cipher}' does not match required '{args.require_cipher}'")
            sys.exit(UNKNOWN)

    if args.forbid_cipher:
        if cipher == args.forbid_cipher:
            print(f"UNKNOWN - cipher '{cipher}' is explicitly forbidden")
            sys.exit(UNKNOWN)

    if args.require_aead:
        if not is_aead_cipher(cipher):
            print(f"UNKNOWN - cipher '{cipher}' is not AEAD (GCM/CHACHA20-POLY1305 required)")
            sys.exit(UNKNOWN)

    if args.forbid_cbc:
        if is_cbc_cipher(cipher):
            print(f"UNKNOWN - CBC cipher '{cipher}' is forbidden")
            sys.exit(UNKNOWN)

    if args.forbid_rc4:
        if is_rc4_cipher(cipher):
            print(f"UNKNOWN - RC4 cipher '{cipher}' is forbidden")
            sys.exit(UNKNOWN)

    # SAN enforcement
    if args.enforce_san and args.host not in san_list:
        print(f"UNKNOWN - {args.host} not present in SAN list")
        sys.exit(UNKNOWN)

    # Issuer check
    if args.issuer and (not issuer_cn or args.issuer.lower() not in issuer_cn.lower()):
        print(f"UNKNOWN - issuer '{issuer_cn}' does not match '{args.issuer}'")
        sys.exit(UNKNOWN)

    # RSA minimum size
    if args.min_rsa and key_type == "rsa":
        if rsa_bits is None or rsa_bits < args.min_rsa:
            print(f"UNKNOWN - RSA key size {rsa_bits} < required {args.min_rsa}")
            sys.exit(UNKNOWN)

    # ECC curve requirement
    if args.require_curve and key_type == "ec":
        if not curve_name or curve_name.lower() != args.require_curve.lower():
            print(f"UNKNOWN - ECC curve '{curve_name}' does not match required '{args.require_curve}'")
            sys.exit(UNKNOWN)

    # Signature algorithm check
    if args.sigalg and (not sigalg or args.sigalg.lower() != sigalg.lower()):
        print(f"UNKNOWN - signature algorithm '{sigalg}' does not match '{args.sigalg}'")
        sys.exit(UNKNOWN)

    # Wildcard checks
    if args.require_wildcard and not wildcard:
        print("UNKNOWN - certificate is not wildcard")
        sys.exit(UNKNOWN)

    if args.forbid_wildcard and wildcard:
        print("UNKNOWN - certificate is wildcard")
        sys.exit(UNKNOWN)

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

def is_aead_cipher(cipher: str) -> bool:
    if not cipher:
        return False
    c = cipher.upper()
    return "GCM" in c or "CHACHA20" in c or "POLY1305" in c

def is_cbc_cipher(cipher: str) -> bool:
    if not cipher:
        return False
    return "CBC" in cipher.upper()

def is_rc4_cipher(cipher: str) -> bool:
    if not cipher:
        return False
    return "RC4" in cipher.upper()

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
#  CLI Parser
# -----------------------------
def parse_args():
    parser = argparse.ArgumentParser(description="Nagios TLS certificate checker")

    parser.add_argument("-H", "--host", required=True)
    parser.add_argument("-p", "--port", type=int, default=443)
    parser.add_argument("-w", "--warning", type=int, default=30)
    parser.add_argument("-c", "--critical", type=int, default=15)

    parser.add_argument("-S", "--show-san", action="store_true")
    parser.add_argument("-E", "--enforce-san", action="store_true")

    parser.add_argument("-I", "--issuer", help="Require issuer CN to contain substring")
    parser.add_argument("-A", "--sigalg", help="Require signature hash algorithm")

    parser.add_argument("--require-wildcard", action="store_true")
    parser.add_argument("--forbid-wildcard", action="store_true")

    parser.add_argument("-q", "--quiet", action="store_true",
                        help="Quiet mode: output only exit code")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Verbose mode: print detailed certificate info")

    parser.add_argument("--json", action="store_true",
                        help="Output full certificate info in JSON")

    parser.add_argument("--require-ocsp", action="store_true",
                        help="Fail if server does not staple an OCSP response")

    parser.add_argument("--forbid-ocsp", action="store_true",
                        help="Fail if server staples an OCSP response")

    parser.add_argument("--ocsp-status", choices=["good", "revoked", "unknown", "invalid"],
                        help="Require a specific OCSP status")

    parser.add_argument("--min-rsa", type=int,
                        help="Minimum RSA key size in bits (e.g. 2048, 3072, 4096)")
    parser.add_argument("--require-curve",
                        help="Require ECC curve name (e.g. secp256r1, secp384r1, x25519)")
    parser.add_argument("--min-tls",
                        choices=["TLSv1", "TLSv1.1", "TLSv1.2", "TLSv1.3"],
                        help="Minimum allowed TLS version")

    parser.add_argument("--require-tls",
                        choices=["TLSv1", "TLSv1.1", "TLSv1.2", "TLSv1.3"],
                        help="Require an exact TLS version")
    parser.add_argument("--require-cipher",
                        help="Require exact cipher suite name (e.g. ECDHE-RSA-AES256-GCM-SHA384)")

    parser.add_argument("--forbid-cipher",
                        help="Forbid exact cipher suite name")

    parser.add_argument("--require-aead", action="store_true",
                        help="Require AEAD cipher (GCM or CHACHA20-POLY1305)")

    parser.add_argument("--forbid-cbc", action="store_true",
                        help="Forbid CBC-mode ciphers")

    parser.add_argument("--forbid-rc4", action="store_true",
                        help="Forbid RC4 ciphers")

    return parser.parse_args()

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
    errors.append("tls_handshake_failed")
    if data.get("cert_obj") is None:
        errors.append("no_certificate_present")
    return errors

# -----------------------------
#  Main Orchestrator
# -----------------------------
def main():
    args = parse_args()

    try:
        cert, chain, ocsp_resp, tls_version, cipher = fetch_certificate_and_socket(args.host, args.port)
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
    warnings = populate_warnings(data)

    # JSON mode overrides everything else
    if args.json:
        dta = {
            "subject_cn": get_subject_cn(cert),
            "issuer_cn": issuer_cn,
            "sigalg": sigalg,
            "key_type": key_type,
            "key_bits": key_bits,
            "curve": curve,
            "tls_version": tls_version,
            "cipher": cipher,
            "ocsp_status": ocsp_status,
            "chain_ok": chain_ok,
            "chain_warnings": chain_warnings,
            "expiration_days": expiration_days,
            "expiration_date": expiration_date,
            "warnings": populate_warnings(data),     # your existing general warnings
            "errors": populate_errors(data),          # your existing general errors
        }

        print(json.dumps(dta, indent=2))

    # Verbose mode
    elif args.verbose:
        print(f"Host: {args.host}")
        print(f"Port: {args.port}")
        print(f"TLS Version: {tls_version}")
        print(f"Cipher: {cipher}")
        print(f"Issuer CN: {issuer_cn}")
        print(f"Signature Algorithm: {sigalg}")
        print(f"Wildcard: {wildcard}")
        print(f"SAN: {', '.join(san_list)}")
        print(f"Expires: {expiry} UTC")
        print(f"Key Type: {key_type}")
        print(f"RSA Bits: {key_bits}")
        print(f"ECC Curve: {curve}")
        print(f"Self-Signed: {is_self_signed(cert)}")
        print(f"Chain Present: {len(chain) > 0}")

        # AIA URLs
        print("AIA Issuer URLs:")
        if aia_urls:
            for url in aia_urls:
                print(f"  - {url}")
        else:
            print("  None")

        # AIA Chain Details
        print("AIA Chain:")
        if data.get("aia_chain"):
            for entry in data["aia_chain"]:
                print(f"  - {entry['url']}")
                if "error" in entry:
                    print(f"      ERROR: {entry['error']}")
                else:
                    print(f"      Subject CN: {entry['subject_cn']}")
                    print(f"      Issuer CN: {entry['issuer_cn']}")
                    print(f"      Signature Algorithm: {entry['signature_algorithm']}")
                    print(f"      Key Type: {entry['key_type']}")
        else:
            print("  None")
            print("Chain Validation:")
            print(f"  Reconstructed: {data['chain_reconstructed']}")
            print(f"  Valid: {data['chain_valid']}")
            if data["chain_errors"]:
                print("  Errors:")
                for e in data["chain_errors"]:
                    print(f"    - {e}")
            else:
                print("  No errors detected")
            print("OCSP Responder URLs:")
            if entry.get("ocsp_urls"):
                for url in entry["ocsp_urls"]:
                    print(f"  - {url}")
            else:
                print("  None")


        # Chain warning (if any)
        if data.get("chain_warning"):
            print(f"Chain Warning: {data['chain_warning']}")

    enforce(args, data)
    

    # Optional SAN display
    if args.show_san:
        print(f"SAN: {', '.join(san_list)}")

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
