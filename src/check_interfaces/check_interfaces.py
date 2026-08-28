#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Leon McClatchey, Linktech Engineering LLC
"""
File: check_interfaces.py
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-03-22
Modified: 2026-08-28
Required: Python 3.8+
Part of: NMS_Tools Monitoring Suite
License: MIT (see LICENSE for details)

Description:
        Interface Checker: If the host is local, local libraries are used, otherwise SNMP v2 is used
        Obtains a dictionary of interfaces from the system, which includes the operational
        and configuration information about each interface.
"""
import sys
import os
import json
import re

from pathlib import Path

from PythonTools.log_helpers.factory import LoggerFactory
from PythonTools.nagios import (
    OK,
    WARNING,
    CRITICAL,
    UNKNOWN,
    BaseNagiosParser,
    nagios_summary,
    should_output,
    start_banner,
    result_banner,
    log_interface,
    end_banner,
)
from PythonTools.net import (
    apply_iface_selection,
    evaluate_status,
    fmt_flags,
    fmt_speed,
    gather_local_interfaces,
    gather_snmp_interfaces,
    is_alias,
    is_local,
    is_virtual,
    normalize_interfaces,
    validate_host_local,
)
from PythonTools.utils import (
    matches_ignore
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
            "Interface Inspection Tool\n\n"
            "Determines whether the target host is local or remote. "
            "Local hosts are inspected using kernel interface data. "
            "Remote hosts require SNMPv2c or SNMPv3 and are inspected using IF-MIB. "
            "Supports verbose, JSON, quiet, and Nagios-compatible output modes."
        ),
        script_version=SCRIPT_VERSION,
        suite_version=VERSION,
    )

    nag.parser.usage = "%(prog)s -H <host> [options]"

    # -----------------------------
    # Core Options
    # -----------------------------
    core = nag.add_group("Core Options")
    core.add_argument("-H", "--host", required=True,
                      help="Target hostname or IP address")
    core.add_argument("-t", "--timeout", type=int, default=5,
                      help="Connection timeout in seconds")

    # -----------------------------
    # SNMP Options (v2c)
    # -----------------------------
    snmp = nag.add_group("SNMP Options")
    snmp.add_argument("-C", "--community",
                      help="SNMPv2c community string (required for remote hosts)")
    snmp.add_argument("-p", "--snmp-port", type=int, default=161,
                      help="SNMP port")
    snmp.add_argument("-T", "--snmp-timeout", type=int,
                      help="SNMP timeout in seconds (defaults to --timeout if not set; ignored in local mode)")

    # -----------------------------
    # SNMPv3 Options (future-proofing)
    # -----------------------------
    v3 = nag.add_group("SNMPv3 Options")
    v3.add_argument("--v3-user", help="SNMPv3 security name")
    v3.add_argument("--v3-auth", choices=["MD5", "SHA"], help="SNMPv3 authentication protocol")
    v3.add_argument("--v3-auth-pass", help="SNMPv3 authentication password")
    v3.add_argument("--v3-priv", choices=["DES", "AES"], help="SNMPv3 privacy protocol")
    v3.add_argument("--v3-priv-pass", help="SNMPv3 privacy password")

    # -----------------------------
    # Interface Filtering Options
    # -----------------------------
    filtering = nag.add_group("Interface Filtering Options")
    filtering.add_argument("--include-aliases", action="store_true",
                           help="Include alias interfaces (e.g., eth0:1, br0:backup)")
    filtering.add_argument("--ignore-virtual", action="store_true",
                           help="Ignore virtual interfaces (e.g., vnet*, virbr*, docker0)")
    filtering.add_argument("--exclude-local", action="store_true",
                           help="Exclude local-only interfaces such as 'lo'")
    filtering.add_argument("--ignore", action="append", metavar="PATTERN",
                           help="Ignore interfaces matching this pattern (substring or regex). Repeatable.")

    # -----------------------------
    # Targeting Options
    # -----------------------------
    targeting = nag.add_group("Targeting Options")

    group = targeting.add_mutually_exclusive_group()
    group.add_argument(
        "--status",
        choices=[
            "oper-status",
            "admin-status",
            "linkspeed",
            "duplex",
            "mtu",
            "alias",
            "flags",
            "iftype"
        ],
        default="oper-status",
        help="Interface attribute to evaluate."
    )

    group.add_argument(
        "--perfdata",
        choices=[
            "in_octets",
            "out_octets",
            "in_errors",
            "out_errors",
            "in_discards",
            "out_discards",
            "in_ucast",
            "out_ucast",
            "in_multicast",
            "out_multicast",
            "in_broadcast",
            "out_broadcast"
        ],
        help="Select a perfdata metric to output."
    )

    targeting.add_argument(
        "--ifaces",
        metavar="LIST",
        help="Comma-delimited list or regex pattern of interfaces to evaluate."
    )

    # -----------------------------
    # Examples
    # -----------------------------
    nag.parser.epilog = (
        "Examples:\n"
        "  %(prog)s -H localhost -v\n"
        "  %(prog)s -H 192.168.1.1 --community public\n"
        "  %(prog)s -H router --community mystring --json\n"
    )

    return nag.parse()
# -----------------------------
# Filters
# -----------------------------
def apply_filters(interfaces, args) -> dict:
    filtered = {}

    for name, iface in interfaces.items():

        # Alias filtering
        if args.status == "alias":
            pass
        elif is_alias(name) and not args.include_aliases:
            continue

        # Virtual filtering
        if args.ignore_virtual and is_virtual(name):
            continue

        # Local-only filtering (lo, loopback, etc.)
        if args.exclude_local and is_local(name, iface):
            continue

        # Pattern ignore (substring or regex)
        if matches_ignore(name, args.ignore):
            continue

        filtered[name] = iface

    return filtered
# --------------------------------
# Enforcement
# --------------------------------
def extract_required(filtered, args):
    if not args.require:
        return filtered  # no change

    required_only = {}
    for req in args.require:
        if req in filtered:
            required_only[req] = filtered[req]
    return required_only
# -----------------------------
# Display the Information
# -----------------------------
def output_json(meta, interfaces, exit_code):
    """
    JSON output mode.
    meta: dictionary with host info, mode, errors, etc.
    interfaces: normalized interface dictionary
    exit_code: Nagios exit code
    """

    payload = {
        "meta": meta,
        "interfaces": interfaces,
        "status": exit_code
    }
    meta.pop("_log_warn_emitted", None)
    
    print(json.dumps(payload, indent=2, sort_keys=True))
    return exit_code
def output_verbose(meta, interfaces, result):
    print(f"Interface Summary ({meta['mode']})")
    print(f"Host: {meta['host']} ({meta['ip']})")
    print(f"Interfaces: {meta['interface_count']}")
    print(f"Status Target: {meta['status_target']}\n")

    for name, iface in interfaces.items():
        print(f"Interface: {name}")

        # Basic metadata
        print(f"  MAC: {iface['mac'] or '-'}")
        print(f"  MTU: {iface['mtu'] if iface['mtu'] is not None else '-'}")
        print(f"  Speed: {fmt_speed(iface['speed'])}")
        print(f"  Duplex: {iface['duplex']}")
        print(f"  Admin: {'up' if iface['admin_up'] else 'down'}")
        print(f"  Oper: {'up' if iface['oper_up'] else 'down'}")
        print(f"  Flags: {fmt_flags(iface['flags'])}")

        # Evaluation result
        eval_ok = result["results"][name]["ok"]
        eval_val = result["results"][name]["value"]
        eval_str = "OK" if eval_ok else str(eval_val)
        print(f"  Eval: {eval_str} ({meta['status_target']})")

        # IP addresses
        if iface["ipv4"]:
            ipv4_list = [f"{ip['address']}/{ip['netmask']}" for ip in iface["ipv4"]]
            print(f"  IPv4: {', '.join(ipv4_list)}")
        else:
            print("  IPv4: none")

        if iface["ipv6"]:
            ipv6_list = [ip["address"] for ip in iface["ipv6"]]
            print(f"  IPv6: {', '.join(ipv6_list)}")
        else:
            print("  IPv6: none")

        # Counters
        c = iface["counters"]
        print("  Counters:")
        print(f"    Octets:     In={c['in_octets']}  Out={c['out_octets']}")
        print(f"    Ucast:      In={c['in_ucast']}   Out={c['out_ucast']}")
        print(f"    Multicast:  In={c['in_multicast']} Out={c['out_multicast']}")
        print(f"    Broadcast:  In={c['in_broadcast']} Out={c['out_broadcast']}")
        print(f"    Discards:   In={c['in_discards']} Out={c['out_discards']}")
        print(f"    Errors:     In={c['in_errors']}   Out={c['out_errors']}")
        print(f"    Unknown:    {c.get('in_unknown', 0)}")

        print()  # blank line between interfaces

    # Warnings (log failures, etc.)
    if meta.get("warnings"):
        for w in meta["warnings"]:
            print(w)
def output_single_line(meta, interfaces, result, primary_mode, perfdata_metric):
    """
    Build a Nagios-compatible single-line output with optional perfdata.
    Returns: (message, exit_code)
    """

    state = result["state"]
    failures = result["failures"]
    status_target = meta["status_target"]

    # -----------------------------
    # Build human-readable message
    # -----------------------------
    if primary_mode == "perfdata":
        # Perfdata-centric message
        msg = f"{state}: {perfdata_metric} perfdata"

    else:
        # Status-centric message
        if state == "OK":
            msg = f"OK: all interfaces {status_target}"
        else:
            failed_list = ", ".join(failures)
            msg = f"{state}: {failed_list} failed {status_target}"

    # -----------------------------
    # Build perfdata (always included)
    # -----------------------------
    if perfdata_metric:
        # Only the selected metric
        perf = []
        for name, iface in interfaces.items():
            val = iface["counters"].get(perfdata_metric)
            if val is not None:
                perf.append(f"{name}_{perfdata_metric}={val}c")
        perfdata = " ".join(perf)

    else:
        # Emit all counters
        perf = []
        for name, iface in interfaces.items():
            for metric, val in iface["counters"].items():
                if val is not None:
                    perf.append(f"{name}_{metric}={val}c")
        perfdata = " ".join(perf)

    # -----------------------------
    # Final output
    # -----------------------------
    line = f"{msg} | {perfdata}"

    exit_code = {
        "OK": 0,
        "WARNING": 1,
        "CRITICAL": 2,
        "UNKNOWN": 3
    }.get(state, 3)

    return line, exit_code
# --------------------------------------
# Logging Initialization (PythonTools Unified)
# --------------------------------------
def initialize_logger(args, mode):
    """
    Unified LoggerFactory initialization for check_interfaces.
    Matches the model used by check_html, check_cert, and check_ticker.
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

# --------------------------------------
# Main Entry Point
# --------------------------------------
def main():
    # ------------------------------------------------------------
    # Parse arguments and determine mode
    # ------------------------------------------------------------
    args, flags, mode = build_parser()
    primary_mode = "perfdata" if args.perfdata else "status"

    # ------------------------------------------------------------
    # Host validation
    # ------------------------------------------------------------
    rc = validate_host_local(args.host)
    if not rc["ok"]:
        print(f"UNKNOWN - {rc['error']}")
        os._exit(UNKNOWN)

    # ------------------------------------------------------------
    # Build metadata (single pass)
    # ------------------------------------------------------------
    meta = {
        "host": args.host,
        "ip": rc["ip"],
        "mode": "local" if rc["local"] else "snmp",
        "ignore": args.ignore,
        "exclude_local": args.exclude_local,
        "include_aliases": args.include_aliases,
        "log_dir": str(Path(args.log_dir).expanduser()) if args.log_dir else None,
        "log_max_mb": args.log_max_mb,
    }

    # ------------------------------------------------------------
    # Logging setup
    # ------------------------------------------------------------
    logger = initialize_logger(args, meta["mode"])
    logging_enabled = logger and mode != "nagios" and meta["log_dir"]

    if logger and logging_enabled:
        logger.info(start_banner(SCRIPT_NAME, meta))

    # ------------------------------------------------------------
    # Determine timeout
    # ------------------------------------------------------------
    effective_timeout = (
        args.timeout if rc["local"]
        else args.snmp_timeout or args.timeout
    )

    # ------------------------------------------------------------
    # Interface collection
    # ------------------------------------------------------------
    if rc["local"]:
        raw = gather_local_interfaces(timeout=effective_timeout)
    else:
        if not args.community:
            print("CRITICAL - remote host requires SNMP community string")
            os._exit(CRITICAL)

        raw = gather_snmp_interfaces(
            rc["ip"],
            args.community,
            port=args.snmp_port,
            timeout=effective_timeout
        )

    data = normalize_interfaces(raw, meta["mode"])

    # ------------------------------------------------------------
    # Filtering + selection
    # ------------------------------------------------------------
    filtered = apply_filters(data, args)
    selected, unmatched = apply_iface_selection(filtered, args.ifaces)

    # ------------------------------------------------------------
    # Status evaluation
    # ------------------------------------------------------------
    status_target = args.status or "oper-status"
    meta["interface_count"] = len(selected)
    meta["status_target"] = status_target

    result = evaluate_status(selected, status_target, unmatched)

    # ------------------------------------------------------------
    # Logging (per-interface + summary)
    # ------------------------------------------------------------
    if logger and logging_enabled:
        for iface_name in selected:
            logger.info(log_interface(
                iface_name,
                data[iface_name],
                result["results"][iface_name]
            ))

        for name in unmatched:
            logger.info(log_interface(
                name,
                {"name": name},
                result["results"][name]
            ))

        logger.info(result_banner(result["state"], result["failures"]))
        logger.info(end_banner(SCRIPT_NAME, result["state"]))

    # ------------------------------------------------------------
    # Output routing
    # ------------------------------------------------------------
    if args.json:
        output_json(meta, selected, result)
        os._exit(0 if result["state"] == "OK" else 2)

    if args.verbose:
        output_verbose(meta, selected, result)
        os._exit(0 if result["state"] == "OK" else 2)

    msg, code = output_single_line(
        meta=meta,
        interfaces=selected,
        result=result,
        primary_mode=primary_mode,
        perfdata_metric=args.perfdata
    )

    if not args.quiet:
        print(msg)

    os._exit(code)

if __name__ == "__main__":
    if sys.version_info < (MIN_MAJOR, MIN_MINOR):
        print(f"CRITICAL: Python {MIN_MAJOR}.{MIN_MINOR}+ required, "
            f"but running on {sys.version_info.major}.{sys.version_info.minor}")
        os._exit(2)
    main()
