#!/usr/bin/env python3.12
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Leon McClatchey, Linktech Engineering LLC
"""
File: check_cert.py
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-03-17
Modified: 2026-08-26
Required: Python 3.8+
Part of: NMS_Tools Monitoring Suite
License: MIT (see LICENSE for details)

Description:
    Certificate checker with SAN, issuer, signature algorithm, wildcard detection,
    perfdata, quiet/verbose modes, and JSON output.
"""
import json
import os
import sys

from pathlib import Path

from PythonTools.certs import (
    fetch_certificate_and_socket,
    TLS_VERSIONS,
    validate_host_basic,
    build_certificate_meta,
    run_enforcement_checks,
    run_monitoring_checks,
    merge_enforcement,
)
from PythonTools.log_helpers.factory import LoggerFactory
from PythonTools.nagios import (
    OK,
    WARNING,
    CRITICAL,
    UNKNOWN,
    nagios_summary,
    start_banner,
    end_banner,
    cert_banner,
    result_banner,
    should_output,
    BaseNagiosParser,
    early_exit,
)

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
# Other Constants
SCRIPT_NAME = Path(sys.argv[0]).stem
SCRIPT_VERSION = "3.1.0"
# -----------------------------
# ArgParse Custom Formatter & CLI Parser
# -----------------------------
def build_parser():
    nag = BaseNagiosParser(
        prog="check_cert.py",
        description=(
            "TLS Certificate Inspection Tool\n\n"
            "Performs a full TLS handshake, retrieves the server certificate and chain,\n"
            "evaluates TLS version and cipher, and applies optional enforcement rules.\n"
            "Supports verbose, JSON, and Nagios-compatible output modes."
        ),
        script_version=SCRIPT_VERSION,
        suite_version=VERSION,
    )

    # Usage line
    nag.parser.usage = "%(prog)s -H <host> [options]"

    # -----------------------------
    # Connection Options
    # -----------------------------
    core = nag.add_group("Core Options")
    core.add_argument("-H", "--host", required=True, help="Target hostname or IP")
    core.add_argument("-p", "--port", type=int, default=443, help="Port to connect to")
    core.add_argument("--sni", help="Override SNI value (default: host)")
    core.add_argument("--timeout", type=int, default=5, help="Connection timeout in seconds")
    core.add_argument("--insecure", action="store_true", help="Skip certificate validation during handshake")

    # -----------------------------
    # TLS Requirements
    # -----------------------------
    tls = nag.add_group("TLS Requirements")
    tls.add_argument("--min-tls", choices=TLS_VERSIONS, help="Minimum allowed TLS version")
    tls.add_argument("--require-tls", choices=TLS_VERSIONS, help="Require exact TLS version")
    tls.add_argument("--require-cipher", help="Require exact cipher suite")
    tls.add_argument("--forbid-cipher", help="Forbid exact cipher suite")
    tls.add_argument("--require-aead", action="store_true", help="Require AEAD cipher")
    tls.add_argument("--forbid-cbc", action="store_true", help="Forbid CBC-mode ciphers")
    tls.add_argument("--forbid-rc4", action="store_true", help="Forbid RC4 ciphers")

    # -----------------------------
    # Certificate Requirements
    # -----------------------------
    cert = nag.add_group("Certificate Requirements")
    cert.add_argument("-E", "--enforce-san", action="store_true", help="Require host to appear in SAN list")
    cert.add_argument("-I", "--issuer", help="Require issuer CN to contain substring")
    cert.add_argument("-A", "--sigalg", help="Require signature algorithm")
    cert.add_argument("--min-rsa", type=int, help="Minimum RSA key size in bits")
    cert.add_argument("--require-curve", help="Require ECC curve name")
    cert.add_argument("--require-wildcard", action="store_true", help="Require wildcard certificate")
    cert.add_argument("--forbid-wildcard", action="store_true", help="Forbid wildcard certificate")

    # -----------------------------
    # Monitoring Checks
    # -----------------------------
    monitoring = nag.add_group("Monitoring Checks")
    monitoring.add_argument("--no-check-expiration", dest="check_expiration", action="store_false", default=True)
    monitoring.add_argument("--no-check-chain", dest="check_chain", action="store_false", default=True)
    monitoring.add_argument("--no-check-hostname", dest="check_hostname", action="store_false", default=True)
    monitoring.add_argument("--no-check-san", dest="check_san", action="store_false", default=True)
    monitoring.add_argument("--no-check-self-signed", dest="check_self_signed", action="store_false", default=True)
    monitoring.add_argument("--check-ocsp", dest="check_ocsp", action="store_true", default=False)

    # -----------------------------
    # Nagios Thresholds
    # -----------------------------
    nagios = nag.add_group("Nagios Thresholds")
    nagios.add_argument("-w", "--warning", type=int, default=30, help="Warning threshold in days")
    nagios.add_argument("-c", "--critical", type=int, default=15, help="Critical threshold in days")

    # -----------------------------
    # OCSP Options
    # -----------------------------
    ocsp = nag.add_group("OCSP Options")
    ocsp.add_argument("--require-ocsp", action="store_true", help="OCSP responder must be reachable")
    ocsp.add_argument("--forbid-ocsp", action="store_true", help="OCSP responder must NOT be reachable")
    ocsp.add_argument("--ocsp-status", choices=["good", "revoked", "unknown", "invalid"], help="Require specific OCSP status")

    # Examples
    nag.parser.epilog = (
        "Examples:\n"
        "  %(prog)s -H example.com -v\n"
        "  %(prog)s -H example.com --json\n"
        "  %(prog)s -H example.com --min-tls TLSv1.2\n"
        "  %(prog)s -H example.com --require-aead --require-curve secp256r1\n"
    )

    return nag.parse()
# -----------------------------
# Display Options
# -----------------------------
def display_verbose(meta):
    """Pretty, operator-grade verbose output."""

    # -----------------------------
    # Connection
    # -----------------------------
    print("=== Connection ===")
    print(f"Host: {meta.get('host')}")
    print(f"Port: {meta.get('port')}")
    print(f"SNI: {meta.get('sni')}")
    print(f"Timeout: {meta.get('timeout')}")
    print(f"Insecure: {meta.get('insecure')}")
    print()

    # -----------------------------
    # TLS Session
    # -----------------------------
    print("=== TLS Session ===")
    print(f"TLS Version: {meta.get('tls_version')}")
    print(f"Cipher: {meta.get('cipher')}")
    print(f"tls_state: {meta.get('tls_state')}")
    print(f"tls_messages: {meta.get('tls_messages')}")
    print(f"tls_handshake_state: {meta.get('tls_handshake_state')}")
    print(f"tls_handshake_message: {meta.get('tls_handshake_message')}")
    print(f"  AEAD: {meta.get('cipher_is_aead')}")
    print(f"  CBC: {meta.get('cipher_is_cbc')}")
    print(f"  RC4: {meta.get('cipher_is_rc4')}")
    print()

    # -----------------------------
    # Certificate
    # -----------------------------
    print("=== Certificate ===")
    print(f"Subject CN: {meta.get('subject_cn')}")
    print(f"Issuer CN: {meta.get('issuer_cn')}")
    print(f"Signature Algorithm: {meta.get('signature_algorithm')}")
    print(f"Signature Algorithm State: {meta.get('signature_algorithm_state')}")
    print(f"Signature Algorithm Message: {meta.get('signature_algorithm_message')}")
    print(f"Wildcard: {meta.get('wildcard')}")
    print(f"Self-Signed: {meta.get('self_signed')}")
    print(f"Hostname Matches: {meta.get('hostname_matches')}")
    print()

    print("SAN:")
    san_list = meta.get("san", [])
    if san_list:
        for entry in san_list:
            print(f"  - {entry}")
    else:
        print("  (none)")
    print()

    print(f"Expires: {meta.get('expires')}")
    print(f"Expiration Days: {meta.get('expiration_days')}")
    print()

    # -----------------------------
    # Key Metadata
    # -----------------------------
    print("=== Key Metadata ===")
    print(f"Key Type: {meta.get('key_type')}")
    print(f"RSA Bits: {meta.get('rsa_bits') or '—'}")
    print(f"ECC Curve: {meta.get('ecc_curve') or '—'}")
    print(f"Key State: {meta.get('key_state')}")
    print(f"Key Message: {meta.get('key_message')}")
    print()

    # -----------------------------
    # AIA
    # -----------------------------
    print("=== AIA ===")
    print("Issuer URLs:")
    aia_urls = meta.get("aia_issuer_urls", [])
    if aia_urls:
        for url in aia_urls:
            print(f"  - {url}")
    else:
        print("  (none)")
    print()

    print("Chain:")
    aia_chain = meta.get("aia_chain", [])
    if aia_chain:
        for entry in aia_chain:
            print(f"  - {entry.get('subject_cn')}")
            print(f"      Issuer: {entry.get('issuer_cn')}")
            print(f"      Algorithm: {entry.get('signature_algorithm')}")
            print(f"      Key Type: {entry.get('key_type')}")
    else:
        print("  (none)")
    print(f"Chain State: {meta.get('chain_state')}")
    print(f"Chain Message: {meta.get('chain_message')}")
    print()

    # -----------------------------
    # OCSP
    # -----------------------------
    print("=== OCSP ===")
    print("Responder URLs:")
    ocsp_urls = meta.get("ocsp_urls", [])
    if ocsp_urls:
        for url in ocsp_urls:
            print(f"  - {url}")
    else:
        print("  (none)")
    print(f"Status: {meta.get('ocsp_status')}")
    print(f"Reachable: {meta.get('ocsp_reachable')}")
    print()

    # -----------------------------
    # Chain Validation
    # -----------------------------
    print("=== Chain Validation ===")
    print(f"Server-Sent Chain: {meta.get('chain_present')}")
    print(f"Reconstructed: {meta.get('chain_reconstructed')}")
    print(f"Valid: {meta.get('chain_valid')}")
    print()

    chain_errors = meta.get("chain_errors", [])
    if chain_errors:
        print("Errors:")
        for err in chain_errors:
            print(f"  - {err}")
    else:
        print("Errors: None")
    print()

    # -----------------------------
    # General Warnings / Errors
    # -----------------------------
    print("=== General Warnings ===")
    warnings = meta.get("warnings", [])
    if warnings:
        for w in warnings:
            print(f"  - {w}")
    else:
        print("  None")
    print()

    print("=== General Errors ===")
    errors = meta.get("errors", [])
    if errors:
        for e in errors:
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
def nagios_exit(enf, meta):
    days = meta["expiration_days"]
    date = meta["expiration_date"]
    perf = f"days_remaining={days};{meta['warning_days']};{meta['critical_days']}"

    # Hard failures (CRITICAL)
    hard_failures = [f for f in enf["failed"] if not f.endswith("_warning")]
    warnings = [f for f in enf["failed"] if f.endswith("_warning")]

    # 1. Certificate expired (days < 0)
    if days < 0:
        print(f"CRITICAL - certificate expired on {date} | {perf}")
        os._exit(CRITICAL)

    # 2. Hard enforcement failures
    if hard_failures:
        print(f"CRITICAL - certificate valid but {', '.join(hard_failures)}, expires on {date} | {perf}")
        os._exit(CRITICAL)

    # 3. Warning enforcement failures
    if warnings:
        print(f"WARNING - certificate valid but {', '.join(warnings)}, expires on {date} | {perf}")
        os._exit(WARNING)

    # 4. Fully OK
    print(f"OK - certificate valid, expires on {date} | {perf}")
    os._exit(OK)
def output_json(meta, enf):
    """
    Produce deterministic, complete JSON output for monitoring and automation.
    Mirrors the canonical metadata builder and includes all enforcement results.
    """

    out = {
        # -----------------------------
        # Connection
        # -----------------------------
        "host": meta.get("host"),
        "port": meta.get("port"),
        "sni": meta.get("sni"),
        "timeout": meta.get("timeout"),
        "insecure": meta.get("insecure"),

        # -----------------------------
        # TLS Session
        # -----------------------------
        "tls": {
            "version": meta.get("tls_version"),
            "cipher": meta.get("cipher"),
            "tls_state": meta.get("tls_state"),
            "tls_messages":meta.get("tls_messages"),
            "tls_handshake_state":meta.get("tls_handshake_state"),
            "tls_handshake_message":meta.get("tls_handshake_message"),
            "cipher_is_aead": meta.get("cipher_is_aead"),
            "cipher_is_cbc": meta.get("cipher_is_cbc"),
            "cipher_is_rc4": meta.get("cipher_is_rc4"),
        },

        # -----------------------------
        # Certificate
        # -----------------------------
        "certificate": {
            "subject_cn": meta.get("subject_cn"),
            "issuer_cn": meta.get("issuer_cn"),
            "signature_algorithm": meta.get("signature_algorithm"),
            "signature_algorithm_state": meta.get("signature_algorithm_state"),
            "signature_algorithm_message": meta.get("signature_algorithm_message"),
            "wildcard": meta.get("wildcard"),
            "self_signed": meta.get("self_signed"),
            "hostname_matches": meta.get("hostname_matches"),
            "san": meta.get("san", []),
            "expires": meta.get("expires"),
            "expiration_days": meta.get("expiration_days"),
            "warning_days": meta.get("warning_days"),
            "critical_days": meta.get("critical_days"),
        },

        # -----------------------------
        # Key Metadata
        # -----------------------------
        "key": {
            "type": meta.get("key_type"),
            "rsa_bits": meta.get("rsa_bits"),
            "ecc_curve": meta.get("ecc_curve"),
            "key_state": meta.get("key_state"),
            "key_message": meta.get("key_message")
        },

        # -----------------------------
        # AIA
        # -----------------------------
        "aia": {
            "issuer_urls": meta.get("aia_issuer_urls", []),
            "chain": meta.get("aia_chain", []),
        },

        # -----------------------------
        # OCSP
        # -----------------------------
        "ocsp": {
            "urls": meta.get("ocsp_urls", []),
            "status": meta.get("ocsp_status"),
            "reachable": meta.get("ocsp_reachable"),
        },

        # -----------------------------
        # Chain Validation
        # -----------------------------
        "chain": {
            "server_sent": meta.get("chain_present"),
            "reconstructed": meta.get("chain_reconstructed"),
            "valid": meta.get("chain_valid"),
            "errors": meta.get("chain_errors", []),
            "chain_state": meta.get("chain_state"),
            "chain_message": meta.get("chain_message"),
        },

        # -----------------------------
        # General Warnings / Errors
        # -----------------------------
        "warnings": meta.get("warnings", []),
        "errors": meta.get("errors", []),

        # -----------------------------
        # Enforcement
        # -----------------------------
        "enforcement": {
            "applied": enf.get("applied", []),
            "passed": enf.get("passed", []),
            "failed": enf.get("failed", []),
            "errors": enf.get("errors", []),
            "state": compute_nagios_code(enf),
        }
    }

    print(json.dumps(out, indent=2))
def compute_nagios_code(enf):
    hard_failures = [f for f in enf["failed"] if not f.endswith("_warning")]
    warnings = [f for f in enf["failed"] if f.endswith("_warning")]

    if hard_failures:
        return CRITICAL
    if warnings:
        return WARNING
    return OK
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
#  Main Orchestrator
# -----------------------------
def main():
    # ------------------------------------------------------------
    # 1. Parse arguments
    # ------------------------------------------------------------
    args, flags, mode = build_parser()

    # Base metadata (script name, mode, log_dir)
    meta = {
        "host": args.host,
        "log_dir": str(Path(args.log_dir).expanduser()) if args.log_dir else None,
        "flags": flags,
        "mode": mode,
    }
    logger = initialize_logger(args, meta["mode"])

    # ------------------------------------------------------------
    # 2. Basic hostname validation (suite-wide deterministic rule)
    # ------------------------------------------------------------
    rc = validate_host_basic(args.host)
    if not rc["ok"]:
        early_exit(meta, f"UNKNOWN - {rc['error']}", UNKNOWN, logger)

    # ------------------------------------------------------------
    # 3. Fetch certificate + chain + TLS session
    # ------------------------------------------------------------
    try:
        cert, chain, tls_version, cipher = fetch_certificate_and_socket(
            args.sni or args.host,
            args.port,
            args.timeout,
            args.insecure
        )
    except Exception as e:
        early_exit(meta, f"UNKNOWN - failed to retrieve certificate: {e}", UNKNOWN, logger)

    # ------------------------------------------------------------
    # 4. Build full deterministic metadata
    # ------------------------------------------------------------
    # NOTE: build_certificate_meta() now performs:
    # - expiration parsing
    # - SAN parsing
    # - hostname matching
    # - key metadata
    # - signature algorithm
    # - wildcard detection
    # - OCSP URL extraction + reachability
    # - AIA fetching + parsing
    # - chain validation
    # - warnings + errors
    # - TLS session info (via fetch_tls_session_info)
    meta.update(build_certificate_meta(cert, chain, args))

    # ------------------------------------------------------------
    # 5. Determine Nagios mode + logging
    # ------------------------------------------------------------
    logging_enabled = mode != "nagios" and meta["log_dir"]

    # ------------------------------------------------------------
    # 6. Enforcement (policy + monitoring)
    # ------------------------------------------------------------
    policy = run_enforcement_checks(args, meta)
    monitoring = run_monitoring_checks(args, meta)
    enf = merge_enforcement(policy, monitoring)
    for field, rule in [
        ("sigalg_state", "signature_algorithm"),
        ("key_state", "key_strength"),
        ("chain_state", "chain_completeness"),
    ]:
        state = meta.get(field)
        if state == "CRITICAL":
            enf["failed"].append(rule)
        elif state == "WARNING":
            enf["failed"].append(f"{rule}_warning")

    # ------------------------------------------------------------
    # 7. Logging (if enabled)
    # ------------------------------------------------------------
    if logger and logging_enabled:
        logger.info(start_banner(SCRIPT_NAME, meta))
        logger.info(cert_banner(meta))
        logger.info(result_banner(compute_nagios_code(enf), enf["failed"]))
        logger.info(end_banner(SCRIPT_NAME, compute_nagios_code(enf)))

    match mode:
        case "verbose":
            display_verbose(meta)
            display_chain_summary(meta)
            display_enforcement_summary(enf)
            early_exit(meta, logger, "", compute_nagios_code(enf))

        case "json":
            output_json(meta, enf)
            early_exit(meta, logger, "", compute_nagios_code(enf))

        case "nagios":
            nagios_exit(enf, meta)

        case "quiet":
            early_exit(meta, logger, "", compute_nagios_code(enf))

        case _:
            # Fallback for unexpected modes
            nagios_exit(enf, meta)


if __name__ == "__main__":
    if sys.version_info < (MIN_MAJOR, MIN_MINOR):
        print(f"CRITICAL: Python {MIN_MAJOR}.{MIN_MINOR}+ required, "
            f"but running on {sys.version_info.major}.{sys.version_info.minor}")
        os._exit(2)
    main()
