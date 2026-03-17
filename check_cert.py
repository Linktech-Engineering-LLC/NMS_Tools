#!/usr/bin/env python3
"""
File: check_cert.py
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-03-17
Modified: 2026-03-17
Required: Python 3.6+
Description:
    Certificate checker with SAN, issuer, signature algorithm, wildcard detection,
    perfdata, quiet/verbose modes, and JSON output.
"""

import ssl
import socket
import argparse
import datetime
import sys
import json

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.x509.oid import ExtensionOID, NameOID
from cryptography.x509.ocsp import load_der_ocsp_response  # optional, see OCSP stub
from cryptography.hazmat.primitives.asymmetric import rsa, ec, ed25519, ed448

# -----------------------------
#  Nagios Exit Codes
# -----------------------------
OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3


# -----------------------------
#  Certificate Fetch (SNI)
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
        pem = ssl.DER_cert_to_PEM_cert(der)
        cert = x509.load_pem_x509_certificate(pem.encode(), default_backend())

        tls_version = ssock.version()
        cipher = ssock.cipher()[0] if ssock.cipher() else None

        ocsp_resp = None
        chain = []  # stdlib doesn't expose full chain cleanly

        return cert, chain, ocsp_resp, tls_version, cipher
    except Exception as e:
        raise RuntimeError(f"TLS handshake or certificate retrieval failed: {e}")

# -----------------------------
#  Extractors
# -----------------------------
def get_cert_expiry(cert):
    return cert.not_valid_after

def get_key_info(cert):
    """Return (key_type, rsa_bits, curve_name)"""
    key = cert.public_key()

    # RSA
    if isinstance(key, rsa.RSAPublicKey):
        return ("rsa", key.key_size, None)

    # ECC
    if isinstance(key, ec.EllipticCurvePublicKey):
        return ("ec", None, key.curve.name.lower())

    # EdDSA
    if isinstance(key, ed25519.Ed25519PublicKey):
        return ("eddsa", None, "ed25519")
    if isinstance(key, ed448.Ed448PublicKey):
        return ("eddsa", None, "ed448")

    return ("unknown", None, None)

def get_ocsp_status(ocsp_resp):
    # Using stdlib ssl: no stapled OCSP available
    return (False, "unsupported")

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

def get_signature_algorithm(cert):
    try:
        return cert.signature_hash_algorithm.name.lower()
    except Exception:
        return None

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

# -----------------------------
#  Classification Logic
# -----------------------------
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
    ocsp_supported = data["ocsp_supported"]
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
        print("UNKNOWN - certificate is self-signed (no valid chain)")
        data["chain_warning"] = "self-signed certificate"

    # 2. Missing intermediates (server sent only leaf)
    if not chain and aia_urls:
        print("UNKNOWN - server did not send intermediate certificates (AIA present)")
        data["chain_warning"] = "missing intermediates"

    # 3. Issuer mismatch (rare but important)
    if data["issuer_cn"] is None:
        print("UNKNOWN - certificate issuer could not be determined")
        data["chain_warning"] = "Unknown Issuer"

    # OCSP enforcement
    if args.require_ocsp and not ocsp_supported:
        print("UNKNOWN - server did not staple an OCSP response")
        sys.exit(UNKNOWN)

    if args.forbid_ocsp and ocsp_supported:
        print("UNKNOWN - server stapled an OCSP response but --forbid-ocsp was used")
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
#  Main Orchestrator
# -----------------------------
def main():
    args = parse_args()

    try:
        cert, chain, ocsp_resp, tls_version, cipher = fetch_certificate_and_socket(args.host, args.port)
    except Exception as e:
        print(f"UNKNOWN - failed to retrieve certificate: {e}")
        sys.exit(UNKNOWN)

    ocsp_supported, ocsp_status = get_ocsp_status(ocsp_resp)
    key_type, rsa_bits, curve_name = get_key_info(cert)

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
        "ocsp_supported": ocsp_supported,
        "ocsp_status": ocsp_status,
        "san": san_list,
        "issuer_cn": issuer_cn,
        "signature_algorithm": sigalg,
        "wildcard": wildcard,
        "key_type": key_type,
        "rsa_bits": rsa_bits,
        "ecc_curve": curve_name,
        "aia_urls": aia_urls,
    }

    # JSON mode overrides everything else
    if args.json:
        dta = {
            "host": args.host,
            "port": args.port,
            "expiry": expiry.isoformat(),
            "days_remaining": (expiry - datetime.datetime.utcnow()).days,
            "san": san_list,
            "issuer_cn": issuer_cn,
            "signature_algorithm": sigalg,
            "wildcard": wildcard,
            "ocsp_supported": ocsp_supported,
            "ocsp_status": ocsp_status,
            "tls_version": tls_version,
            "cipher": cipher,
            "key_type": key_type,
            "rsa_bits": rsa_bits,
            "ecc_curve": curve_name,
            "chain_present": len(chain) > 0,
            "aia_issuer_urls": aia_urls,
            "self_signed": is_self_signed(cert),
            "chain_warning" : data.get("chain_warning"),
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
        print(f"RSA Bits: {rsa_bits}")
        print(f"ECC Curve: {curve_name}")
        print(f"Self-Signed: {is_self_signed(cert)}")
        print(f"AIA Issuer URLs: {', '.join(aia_urls) if aia_urls else 'None'}")
        print(f"Chain Present: {len(chain) > 0}")
        print(f"Self-Signed: {is_self_signed(cert)}")
        print(f"AIA Issuer URLs: {', '.join(aia_urls) if aia_urls else 'None'}")
        print(f"Chain Present: {len(chain) > 0}")
        if "chain_warning" in data:
            print(f"Chain Warning: {data['chain_warning']}")

    enforce(args, data)
    

    # Optional SAN display
    if args.show_san:
        print(f"SAN: {', '.join(san_list)}")

    # Expiration logic
    remaining = expiry - datetime.datetime.utcnow()
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
