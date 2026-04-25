#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Leon McClatchey, Linktech Engineering LLC
"""
File: check_interfaces.py
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-03-22
Modified: 2026-04-20
Required: Python 3.8+
Part of: NMS_Tools Monitoring Suite
License: MIT (see LICENSE for details)

Description:
        Interface Checker: If the host is local, local libraries are used, otherwise SNMP v2 is used
        Obtains a dictionary of interfaces from the system, which includes the operational
        and configuration information about each interface.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "libs"))

import argparse
import platform
import os
import socket
import ipaddress
import psutil
import json
import re
import shutil
import zipfile

from datetime import datetime
from easysnmp import Session

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

# Nagios Exit Codes
OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3
# Other Global Constants
SCRIPT_NAME = Path(sys.argv[0]).stem
SCRIPT_VERSION = "1.1.0"
VIRTUAL_PREFIXES = (
    "vnet", "virbr", "docker", "br-", "tap", "tun", "veth"
)
SPEED_UNITS = {
    "G": 1000,
    "M": 1,
}
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
        prog=SCRIPT_NAME,
        description=(
            "Interface Inspection Tool\n\n"
            "Determines whether the target host is local or remote. "
            "Local hosts are inspected using kernel interface data. "
            "Remote hosts require SNMPv2c and are inspected using IF-MIB. "
            "Supports verbose, JSON, and Nagios output."
        ),
        formatter_class=CustomFormatter,
        add_help=True
    )
    parser.usage = "%(prog)s -H <host> [options]"
    # ------------------------------------------------------------
    # Core Options
    # ------------------------------------------------------------
    core = parser.add_argument_group("Core Options")
    core.add_argument(
        "-H", "--host",
        required=True,
        help="Target hostname or IP address"
    )
    core.add_argument(
        "-t", "--timeout",
        type=int,
        default=5,
        help="Connection timeout in seconds"
    )
    core.add_argument(
        "--log-dir",
        dest="log_dir",
        metavar="DIR",
        default=None,
        help="Directory to store logs (optional). If omitted, logging is disabled."
    )
    core.add_argument(
        "--log-max-mb",
        dest="log_max_mb",
        metavar="MB",
        type=int,
        default=50,
        help="Maximum log size in MB before rotation."
    )
    # ------------------------------------------------------------
    # SNMP Options
    # ------------------------------------------------------------
    snmp = parser.add_argument_group("SNMP Options")

    snmp.add_argument(
        "-C", "--community",
        help="SNMPv2c community string (required for remote hosts)"
    )
    snmp.add_argument(
        "-p", "--snmp-port", type=int, default=161,
        help="SNMP port"
    )
    snmp.add_argument(
        "-T", "--snmp-timeout",
        type=int,
        help="SNMP timeout in seconds (defaults to global --timeout if not set; ignored in local mode)"
    )
    # -------------------------------------------------------------
    # Interface Filtering Options
    # -------------------------------------------------------------
    filtering = parser.add_argument_group("Interface Filtering Options")
    filtering.add_argument(
        "--include-aliases",
        action="store_true",
        help="Include alias interfaces (e.g., eth0:1, br0:backup) in discovery and evaluation"
    )
    filtering.add_argument(
        "--ignore-virtual",
        action="store_true",
        help="Ignore virtual interfaces (e.g., vnet*, virbr*, docker0) during discovery and evaluation"
    )
    filtering.add_argument(
        "--exclude-local",
        action="store_true",
        help="Exclude local-only interfaces such as 'lo' from discovery and evaluation"
    )
    filtering.add_argument(
        "--ignore",
        action="append",
        metavar="PATTERN",
        help="Ignore interfaces matching this pattern (supports substring or regex). Can be used multiple times."
    )
    # -------------------------------------------------------------
    # Targeting Options
    # -------------------------------------------------------------
    targeting = parser.add_argument_group("Targeting Options")
    targeting.add_argument(
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
        help="Interface attribute to evaluate. Defaults to 'oper-status'."
    )
    targeting.add_argument(
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
        help="Select a perfdata metric to output. Only one may be chosen."
    )
    targeting.add_argument(
        "--ifaces",
        metavar="LIST",
        help="Comma-delimited list or regex pattern of interfaces to evaluate."
    )
    # ------------------------------------------------------------
    # Output Modes
    # ------------------------------------------------------------
    out = parser.add_argument_group("Output Modes")
    out.add_argument(
        "-v", "--verbose", action="store_true",
        help="Detailed output"
    )
    out.add_argument(
        "-j", "--json", action="store_true",
        help="JSON output for automation"
    )
    out.add_argument(
        "-q", "--quiet", action="store_true",
        help="Quiet mode: exit code only"
    )
    out.add_argument(
        "-V", "--version",
        action="version",
        version=(
            f"NMS_TOOLS Suite Version: {VERSION}\n"
            f"{SCRIPT_NAME}: {SCRIPT_VERSION}\n"
            f"Python: {platform.python_version()}"
        ),
        help="Show script and Python version"
    )
    # ------------------------------------------------------------
    # Examples
    # ------------------------------------------------------------
    parser.epilog = (
        "Examples:\n"
        "  %(prog)s -H localhost -v\n"
        "  %(prog)s -H 192.168.1.1 --community public\n"
        "  %(prog)s -H router --community mystring --json\n"
    )
    return parser.parse_args()
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
def validate_host_local(host: str):
    """
    Determines whether the supplied host is:
      • invalid (UNKNOWN)
      • local (local mode)
      • remote (SNMP mode)

    Returns:
        {
            "ok": bool,
            "local": bool,
            "ip": str or None,
            "error": str or None
        }
    """

    # Step 1: Basic validation (shared logic)
    rc = validate_host_basic(host)
    if not rc["ok"]:
        return {
            "ok": False,
            "local": False,
            "ip": None,
            "error": rc["error"]
        }

    target_ip = rc["ip"]

    # Step 2: Enumerate local interface IPs
    local_ips = set()
    for iface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family in (socket.AF_INET, socket.AF_INET6):
                local_ips.add(addr.address)
    # Step 3: Compare
    if target_ip in local_ips:
        return {
            "ok": True,
            "local": True,
            "ip": target_ip,
            "error": None
        }

    # Not local → remote SNMP mode
    return {
        "ok": True,
        "local": False,
        "ip": target_ip,
        "error": None
    }
# -----------------------------
# Local Interface Information
# -----------------------------
def gather_local_interfaces(timeout=None):
    """
    Collects local interface information using psutil.
    Returns a deterministic structure suitable for JSON, verbose, and Nagios output.
    """

    interfaces = {}

    # psutil.net_if_addrs() gives addresses
    addrs = psutil.net_if_addrs()

    # psutil.net_if_stats() gives MTU, speed, duplex, flags
    stats = psutil.net_if_stats()

    for iface in sorted(addrs.keys()):

        stats_path = f"/sys/class/net/{iface}/statistics"
        counters = {}
        try:
            counters = {
                "in_octets": int(open(f"{stats_path}/rx_bytes").read()),
                "out_octets": int(open(f"{stats_path}/tx_bytes").read()),
                "in_ucast": int(open(f"{stats_path}/rx_packets").read()),
                "out_ucast": int(open(f"{stats_path}/tx_packets").read()),
                "in_multicast": int(open(f"{stats_path}/multicast").read()),
                "out_multicast": int(open(f"{stats_path}/tx_multicast").read()) if os.path.exists(f"{stats_path}/tx_multicast") else 0,
                "in_broadcast": int(open(f"{stats_path}/broadcast").read()) if os.path.exists(f"{stats_path}/broadcast") else 0,
                "out_broadcast": int(open(f"{stats_path}/tx_broadcast").read()) if os.path.exists(f"{stats_path}/tx_broadcast") else 0,
                "in_discards": int(open(f"{stats_path}/rx_dropped").read()),
                "out_discards": int(open(f"{stats_path}/tx_dropped").read()),
                "in_errors": int(open(f"{stats_path}/rx_errors").read()),
                "out_errors": int(open(f"{stats_path}/tx_errors").read())
            }
        except Exception:
            counters = {}

        iface_info = {
            "name": iface,
            "mac": None,
            "ipv4": [],
            "ipv6": [],
            "mtu": None,
            "speed": None,
            "duplex": None,
            "oper_up": None,
            "running": None,
            "counters": counters,
            "flags": []
        }

        # -----------------------------
        # Address information
        # -----------------------------
        for addr in addrs[iface]:
            if addr.family == socket.AF_INET:
                iface_info["ipv4"].append({
                    "address": addr.address,
                    "netmask": addr.netmask,
                    "broadcast": addr.broadcast
                })
            elif addr.family == socket.AF_INET6:
                iface_info["ipv6"].append({
                    "address": addr.address,
                    "netmask": addr.netmask,
                    "broadcast": addr.broadcast
                })
            elif addr.family == psutil.AF_LINK:
                iface_info["mac"] = addr.address

        # -----------------------------
        # Stats (MTU, speed, duplex, flags)
        # -----------------------------
        if iface in stats:
            st = stats[iface]
            iface_info["mtu"] = st.mtu
            iface_info["speed"] = st.speed  # may be 0 or None
            iface_info["duplex"] = st.duplex  # psutil.NIC_DUPLEX_FULL, etc.
            iface_info["oper_up"] = st.isup

            # psutil doesn't expose flags directly, but we can infer:
            if st.isup:
                iface_info["flags"].append("UP")
            if st.speed not in (0, None):
                iface_info["flags"].append("RUNNING")
        interfaces[iface] = iface_info

    return interfaces
# -----------------------------
# SNMP Interface Information
# -----------------------------

def snmp_walk(host, community, oid, port=161, timeout=3):
    session = Session(
        hostname=host,
        community=community,
        version=2,
        remote_port=port,
        timeout=timeout
    )

    results = session.walk(oid)

    out = {}
    for item in results:
        idx = int(item.oid_index)
        out[idx] = item.value
    return out
def gather_snmp_interfaces(ip, community, port=161, timeout=3):
    ifDescr       = snmp_walk(ip, community, "1.3.6.1.2.1.2.2.1.2", port, timeout)
    ifType        = snmp_walk(ip, community, "1.3.6.1.2.1.2.2.1.3", port, timeout)
    ifMtu         = snmp_walk(ip, community, "1.3.6.1.2.1.2.2.1.4", port, timeout)
    ifSpeed       = snmp_walk(ip, community, "1.3.6.1.2.1.2.2.1.5", port, timeout)
    ifPhysAddress = snmp_walk(ip, community, "1.3.6.1.2.1.2.2.1.6", port, timeout)
    ifAdminStatus = snmp_walk(ip, community, "1.3.6.1.2.1.2.2.1.7", port, timeout)
    ifOperStatus  = snmp_walk(ip, community, "1.3.6.1.2.1.2.2.1.8", port, timeout)
    dot3Duplex    = snmp_walk(ip, community, "1.3.6.1.2.1.10.7.2.1.19", port, timeout)

    interfaces = {}

    for idx in sorted(ifDescr.keys()):
        name = ifDescr[idx]

        iface = {
            "name": name,
            "mac": ifPhysAddress.get(idx),
            "mtu": int(ifMtu.get(idx, 0)),
            "speed": int(ifSpeed.get(idx, 0)),
            "duplex": dot3Duplex.get(idx),
            "up": (str(ifOperStatus.get(idx)) == "1"),
            "running": (str(ifOperStatus.get(idx)) == "1"),
            "flags": []
        }

        if iface["up"]:
            iface["flags"].append("UP")
        if iface["speed"] > 0:
            iface["flags"].append("RUNNING")

        interfaces[name] = iface

    return interfaces
# -----------------------------
# Normalized Interfaces
# -----------------------------
def normalize_interfaces(raw, source):
    normalized = {}

    for name, iface in raw.items():
        mac = iface.get("mac")

        # Normalize MAC (SNMP hex → colon format)
        if mac and mac.startswith("0x"):
            mac = mac[2:]
            mac = ":".join(mac[i:i+2] for i in range(0, len(mac), 2))
        if not mac:
            mac = "00:00:00:00:00:00"

        # Normalize admin/oper
        admin_up = iface.get("admin_up", True)
        oper_up = iface.get("oper_up", False)

        # Normalize flags
        flags = []
        if admin_up:
            flags.append("UP")
        if oper_up:
            flags.append("RUNNING")

        normalized[name] = {
            "name": name,
            "mac": mac,
            "ipv4": iface.get("ipv4", []),
            "ipv6": iface.get("ipv6", []),
            "mtu": iface.get("mtu"),
            "speed": normalize_speed(iface.get("speed")),
            "duplex": normalize_duplex(iface.get("duplex")),
            "admin_up": admin_up,
            "oper_up": oper_up,
            "counters": normalize_counters(iface.get("counters",{})),
            "flags": flags,
            "ifType": iface.get("ifType")
        }

    return normalized
def normalize_counters(raw):
    """
    Normalize interface counters from either local or SNMP collectors.
    Ensures all fields exist, are integers, and follow the canonical schema.
    """

    def to_int(value):
        try:
            return int(value)
        except Exception:
            return 0

    return {
        "in_octets":     to_int(raw.get("in_octets")),
        "out_octets":    to_int(raw.get("out_octets")),
        "in_ucast":      to_int(raw.get("in_ucast")),
        "out_ucast":     to_int(raw.get("out_ucast")),
        "in_multicast":  to_int(raw.get("in_multicast")),
        "out_multicast": to_int(raw.get("out_multicast")),
        "in_broadcast":  to_int(raw.get("in_broadcast")),
        "out_broadcast": to_int(raw.get("out_broadcast")),
        "in_discards":   to_int(raw.get("in_discards")),
        "out_discards":  to_int(raw.get("out_discards")),
        "in_errors":     to_int(raw.get("in_errors")),
        "out_errors":    to_int(raw.get("out_errors"))
    }
def normalize_speed(value):
    """
    Normalize speed to Mbps.
    SNMP reports bits per second.
    psutil reports Mbps.
    """
    try:
        v = int(value)
        if v in (0, None, 4294967295, 4294):
            return None
        if v > 100000:  # SNMP bps threshold
            return v // 1_000_000
        return v
    except Exception:
        return None
def normalize_duplex(value):
    """
    Normalize duplex to 'full', 'half', or 'unknown'.
    SNMP EtherLike-MIB uses integers.
    psutil uses constants.
    """
    if value in (None, "unknown"):
        return "unknown"

    # psutil constants
    if value == psutil.NIC_DUPLEX_FULL:
        return "full"
    if value == psutil.NIC_DUPLEX_HALF:
        return "half"

    # SNMP EtherLike-MIB
    try:
        v = int(value)
        if v == 3:
            return "full"
        if v == 2:
            return "half"
    except Exception:
        pass

    return "unknown"
def fmt_speed(speed):
    if speed is None:
        return "-"
    for suffix, factor in SPEED_UNITS.items():
        if speed >= factor:
            return f"{speed // factor}{suffix}"
    return str(speed)
def fmt_flags(flags):
    return ",".join(flags) if flags else "-"
# -----------------------------
# Filters
# -----------------------------
def is_alias(name):
    return ":" in name
def is_virtual(name):
    return name.startswith(VIRTUAL_PREFIXES)
def is_local(name, iface):
    # Loopback interface
    if name == "lo":
        return True

    # Loopback aliases (rare but possible)
    if name.startswith("lo:"):
        return True

    # IPv4 loopback addresses
    for ip in iface.get("ipv4", []):
        if ip["address"].startswith("127."):
            return True

    return False
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
def matches_ignore(name, patterns) -> bool:
    if not patterns:
        return False

    lname = name.lower()

    for p in patterns:
        p = p.strip()
        if not p:
            continue

        # 1. Substring match (default behavior)
        if p.lower() in lname:
            return True

        # 2. Regex match (if pattern looks like a regex)
        try:
            if re.search(p, name, re.IGNORECASE):
                return True
        except re.error:
            # Invalid regex → ignore and fall back to substring only
            pass

    return False
# --------------------------------
# Enforcement
# --------------------------------
def parse_speed(s):
    s = s.strip().upper()
    for suffix, factor in SPEED_UNITS.items():
        if s.endswith(suffix):
            return int(s[:-1]) * factor
    return int(s)
def extract_required(filtered, args):
    if not args.require:
        return filtered  # no change

    required_only = {}
    for req in args.require:
        if req in filtered:
            required_only[req] = filtered[req]
    return required_only
def apply_iface_selection(interfaces, ifaces_arg) -> tuple:
    """
    Selects interfaces based on --ifaces.
    Supports:
      • comma-delimited lists
      • regex patterns
      • literal matches
    If --ifaces is None → return all interfaces, no unmatched.

    Returns:
        (selected_dict, unmatched_list)
    """

    # No selection → return everything
    if not ifaces_arg:
        return interfaces, []

    selected = {}
    patterns = [p.strip() for p in ifaces_arg.split(",") if p.strip()]
    matched_patterns = set()

    for name, iface in interfaces.items():
        lname = name.lower()

        for p in patterns:
            # Literal match
            if lname == p.lower():
                selected[name] = iface
                matched_patterns.add(p)
                break

            # Substring match
            if p.lower() in lname:
                selected[name] = iface
                matched_patterns.add(p)
                break

            # Regex match
            try:
                if re.search(p, name, re.IGNORECASE):
                    selected[name] = iface
                    matched_patterns.add(p)
                    break
            except re.error:
                # Invalid regex → ignore and fall back to substring only
                pass

    unmatched = [p for p in patterns if p not in matched_patterns]
    return selected, unmatched
def evaluate_status(interfaces, status_target, unmatched=None) -> dict:
    """
    Evaluates the selected interfaces based on the --status target.
    Injects unmatched --ifaces patterns as CRITICAL failures.
    Returns a dict:
        {
            "state": "OK" | "WARNING" | "CRITICAL",
            "failures": [iface names],
            "results": { iface: { "ok": bool, "value": X } }
        }
    """

    if not status_target:
        status_target = "oper-status"

    results = {}
    failures = []

    for name, iface in interfaces.items():

        if status_target == "oper-status":
            ok = iface.get("oper_up", False)
            value = "up" if ok else "down"

        elif status_target == "admin-status":
            ok = iface.get("admin_up", False)
            value = "up" if ok else "down"

        elif status_target == "linkspeed":
            speed = iface.get("speed")
            ok = speed not in (None, 0)
            value = speed

        elif status_target == "duplex":
            if iface.get("name").startswith("br"):
                ok = True
                value = "n/a"
            else:
                ok = iface.get("duplex") == "full"
                value = iface.get("duplex")

        elif status_target == "mtu":
            mtu = iface.get("mtu")
            ok = mtu is not None and mtu > 0
            value = mtu

        elif status_target == "alias":
            ok = not is_alias(name)
            value = "alias" if not ok else "normal"

        else:
            ok = True
            value = None

        results[name] = {
            "ok": ok,
            "value": value
        }

        if not ok:
            failures.append(name)

    # Inject unmatched --ifaces patterns as CRITICAL failures
    if unmatched:
        for name in unmatched:
            results[name] = {"ok": False, "value": "not found"}
            failures.append(name)

    # Determine overall state
    if failures:
        state = "CRITICAL"
    else:
        state = "OK"

    return {
        "state": state,
        "failures": failures,
        "results": results
    }
# -----------------------------
# Display the Information
# -----------------------------
def build_perfdata(interfaces, metric):
    """
    Build perfdata for a single selected metric.
    Returns a string like:
        'in_octets=12345c br0_in_octets=12345c eth0_in_octets=67890c'
    """
    parts = []

    for name, iface in interfaces.items():
        value = iface["counters"].get(metric)
        if value is None:
            continue

        # perfdata label: iface_metric
        label = f"{name}_{metric}"

        # perfdata value: <value>c (counter)
        parts.append(f"{label}={value}c")

    return " ".join(parts)
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
# Logging Functions
# --------------------------------------
def ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
def write_log(meta, message):
    log_dir = meta.get("log_dir")

    try:
        os.makedirs(log_dir, exist_ok=True)
        logfile = os.path.join(log_dir, f"{SCRIPT_NAME}.log")
        with open(logfile, "a") as f:
            f.write(f"{ts()}; {message}\n")
    except Exception as e:
        if not meta.get("_log_warn_emitted"):
            meta["_log_warn_emitted"] = True
            warning = f"[WARN] Unable to write to log directory: {log_dir} — {e}"
            if meta["mode"] == "verbose":
                print(f"[WARN] {warning}")
            meta.setdefault("warnings", []).append(warning)
def rotate_log_if_needed(meta):
    log_dir = meta["log_dir"]
    logfile = os.path.join(log_dir, f"{SCRIPT_NAME}.log")

    if not os.path.exists(logfile):
        return

    max_mb = meta.get("log_max_mb", 50)
    max_bytes = max_mb * 1024 * 1024

    try:
        if os.path.getsize(logfile) < max_bytes:
            return

        archive_path = build_archive_path(meta)
        shutil.move(logfile, archive_path)
        compress_file(archive_path)

        with open(logfile, "w", encoding="utf-8") as f:
            f.write(f"{ts()}; [INFO] log rotated to {os.path.basename(archive_path)}.zip\n")

    except Exception as e:
        if not meta.get("_log_warn_emitted"):
            meta["_log_warn_emitted"] = True
            warn = f"[WARN] Unable to rotate log file '{logfile}': {e}"
            if meta.get("mode") == "verbose":
                print(warn)
            meta.setdefault("warnings", []).append(warn)
def build_archive_path(meta):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(meta["log_dir"], f"{SCRIPT_NAME}_{ts}.log")
def compress_file(path):
    zip_path = path + ".zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(path, os.path.basename(path))
    os.remove(path)
def start_banner(meta):
    return (
        f"[START] {meta['script_name']}.py"
        f" host={meta['host']}"
        f" status={meta.get('status_target')}"
        f" ignore={meta['ignore']}"
        f" exclude_local={meta['exclude_local']}"
        f" include_aliases={meta['include_aliases']}"
    )
def log_interface(iface_name, iface_meta, iface_result):
    fields = [f"{k}={v}" for k, v in iface_meta.items()]
    fields.append(f"ok={iface_result.get('ok')}")
    fields.append(f"value={iface_result.get('value')}")
    return f"[IFACE] {iface_name} " + " ".join(fields)
def log_summary(state, failures):
    return f"[RESULT] state={state} failures={failures}"
def end_banner():
    return "[END]"

# --------------------------------------
# Main Entry Point
# --------------------------------------
def main():
    args = build_parser()
    if args.perfdata and args.status:
        # allowed, but perfdata becomes the primary message
        primary_mode = "perfdata"
    elif args.perfdata:
        primary_mode = "perfdata"
    elif args.status:
        primary_mode = "status"
    else:
        primary_mode = "status"
        args.status = "oper-status"

    # ------------------------------------------------------------
    # Host validation (local vs remote)
    # ------------------------------------------------------------
    rc = validate_host_local(args.host)
    if not rc["ok"]:
        print(f"UNKNOWN - {rc['error']}")
        sys.exit(UNKNOWN)

    # ------------------------------------------------------------
    # Determine Nagios mode
    # ------------------------------------------------------------
    nagios_mode = not args.json and not args.verbose and not args.quiet

    # ------------------------------------------------------------
    # Build initial metadata BEFORE logging
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

    logging_enabled = not nagios_mode and meta["log_dir"]
    # ------------------------------------------------------------
    # Determine effective timeout
    # ------------------------------------------------------------
    if rc["local"]:
        effective_timeout = args.timeout
    else:
        effective_timeout = args.snmp_timeout if args.snmp_timeout else args.timeout

    # ------------------------------------------------------------
    # Interface collection
    # ------------------------------------------------------------
    if rc["local"]:
        raw = gather_local_interfaces(timeout=effective_timeout)
    else:
        if not args.community:
            print("CRITICAL - remote host requires SNMP community string")
            sys.exit(CRITICAL)

        raw = gather_snmp_interfaces(
            rc["ip"],
            args.community,
            port=args.snmp_port,
            timeout=effective_timeout
        )
    data = normalize_interfaces(raw, meta.get("mode"))
    # ------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------
    filtered = apply_filters(data, args)

    # ------------------------------------------------------------
    # Interface selection (--ifaces)
    # ------------------------------------------------------------
    selected, unmatched = apply_iface_selection(filtered, args.ifaces)

    # ------------------------------------------------------------
    # Status target
    # ------------------------------------------------------------
    status_target = args.status or "oper-status"

    # ------------------------------------------------------------
    # Update metadata BEFORE logging
    # ------------------------------------------------------------
    meta["interface_count"] = len(selected)
    meta["status_target"] = status_target

    # ------------------------------------------------------------
    # Logging lifecycle (only if not Nagios)
    # ------------------------------------------------------------
    if logging_enabled:
        rotate_log_if_needed(meta)
        write_log(meta, start_banner(meta))

    # ------------------------------------------------------------
    # Status evaluation (--status)
    # ------------------------------------------------------------
    result = evaluate_status(selected, status_target, unmatched)
    # ------------------------------------------------------------
    # Per-interface logging
    # ------------------------------------------------------------
    if logging_enabled:
        for iface_name in selected:
            iface_meta = data[iface_name]          # full metadata dict
            iface_result = result["results"][iface_name] # ok/value dict
            write_log(meta, log_interface(iface_name, iface_meta, iface_result))

        # Log unmatched --ifaces as missing interfaces
        for name in unmatched:
            iface_result = result["results"][name]
            write_log(meta, log_interface(name, {"name": name}, iface_result))

        write_log(meta, log_summary(result["state"], result["failures"]))
        write_log(meta, end_banner())

    # ------------------------------------------------------------
    # JSON output
    # ------------------------------------------------------------
    if args.json:
        output_json(meta, selected, result)
        sys.exit(0 if result["state"] == "OK" else 2)

    # ------------------------------------------------------------
    # Verbose output
    # ------------------------------------------------------------
    elif args.verbose:
        output_verbose(meta, selected, result)
        sys.exit(0 if result["state"] == "OK" else 2)

    # ------------------------------------------------------------
    # Single-line Nagios output
    # ------------------------------------------------------------
    msg, code = output_single_line(
        meta=meta, 
        interfaces=selected, 
        result=result, 
        primary_mode=primary_mode, 
        perfdata_metric=args.perfdata
        )
    if not args.quiet:
        print(msg)
    sys.exit(code)

if __name__ == "__main__":
    if sys.version_info < (MIN_MAJOR, MIN_MINOR):
        print(f"CRITICAL: Python {MIN_MAJOR}.{MIN_MINOR}+ required, "
            f"but running on {sys.version_info.major}.{sys.version_info.minor}")
        sys.exit(2)
    main()
