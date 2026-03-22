#!/usr/bin/env python3
"""
File: check_interfaces.py
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-03-22
Modified: 2026-03-22
Required: Python 3.6+
Description:
        Interface Checker: If the host is local, local libraries are used, otherwise SNMP v2 is used
        Obtains a dictionary of interfaces from the system, which includes the operational
        and configuration information about each interface.
"""

import argparse
import platform
import sys
import socket
import ipaddress
import psutil
import json

from pysnmp.hlapi import (
    SnmpEngine, CommunityData, UdpTransportTarget,
    ContextData, ObjectType, ObjectIdentity, nextCmd
)

# Nagios Exit Codes
OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3
# Other Global Constants
SCRIPT_VERSION = "1.0.0"
VIRTUAL_PREFIXES = (
    "vnet", "virbr", "docker", "br-", "tap", "tun", "veth"
)
SPEED_UNITS = {
    "G": 1_000_000_000,
    "M": 1_000_000,
    "K": 1000,
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

    parser.usage = "check_interfaces.py -H <host> [options]"

    # ------------------------------------------------------------
    # Connection Options
    # ------------------------------------------------------------
    conn = parser.add_argument_group("Connection Options")
    conn.add_argument(
        "-H", "--host", required=True,
        help="Target hostname or IP address"
    )

    # SNMP options (only required for remote hosts)
    conn.add_argument(
        "-C", "--community",
        help="SNMPv2c community string (required for remote hosts)"
    )
    conn.add_argument(
        "-p", "--snmp-port", type=int, default=161,
        help="SNMP port"
    )
    conn.add_argument(
        "-t", "--snmp-timeout", type=int, default=3,
        help="SNMP timeout in seconds"
    )
    # -------------------------------------------------------------
    # Filtering Group
    # -------------------------------------------------------------
    filtering = parser.add_argument_group("Interface Filtering Options")

    filtering.add_argument(
        "--include-aliases",
        action="store_true",
        help="Include alias interfaces (e.g., eth0:1, br0:backup) in output and status evaluation"
    )
    filtering.add_argument(
        "--ignore-virtual",
        action="store_true",
        help="Ignore virtual interfaces (e.g., vnet*, virbr*, docker0) in output and status evaluation"
    )
    filtering.add_argument(
        "--exclude-local",
        action="store_true",
        help="Exclude local-only interfaces such as 'lo' from output and status evaluation"
    )
    filtering.add_argument(
        "--ignore",
        action="append",
        metavar="PATTERN",
        help="Ignore interfaces matching this pattern (supports substring match). Can be used multiple times."
    )
    filtering.add_argument(
        "--require",
        action="append",
        metavar="IFACE",
        help="Require this interface to exist and be UP. Can be used multiple times."
    )
    filtering.add_argument(
        "--require-speed",
        metavar="SPEED",
        help="Require interfaces to have at least this speed (e.g., 1G, 100M, 10G)."
    )
    filtering.add_argument(
        "--ignore-iftype",
        action="append",
        metavar="TYPE",
        help="Ignore interfaces with this SNMP ifType (numeric). Can be used multiple times."
    )
    filtering.add_argument(
        "--require-iftype",
        action="append",
        metavar="TYPE",
        help="Require at least one interface of this SNMP ifType to be UP. Can be used multiple times."
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
        "-V", "--version", action="version",
        version=f"check_interfaces.py {SCRIPT_VERSION} (Python {platform.python_version()})",
        help="Show script and Python version"
    )

    # ------------------------------------------------------------
    # Examples
    # ------------------------------------------------------------
    parser.epilog = (
        "Examples:\n"
        "  check_interfaces.py -H localhost -v\n"
        "  check_interfaces.py -H 192.168.1.1 --community public\n"
        "  check_interfaces.py -H router --community mystring --json\n"
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
def gather_local_interfaces():
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
        iface_info = {
            "name": iface,
            "mac": None,
            "ipv4": [],
            "ipv6": [],
            "mtu": None,
            "speed": None,
            "duplex": None,
            "up": None,
            "running": None,
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
            iface_info["up"] = st.isup

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
def snmp_walk(ip, community, oid, port=161, timeout=3):
    """
    Deterministic SNMP walk helper.
    Returns a dict {index: value}.
    """
    results = {}

    for (errorIndication,
         errorStatus,
         errorIndex,
         varBinds) in nextCmd(
            SnmpEngine(),
            CommunityData(community, mpModel=1),  # SNMPv2c
            UdpTransportTarget((ip, port), timeout=timeout, retries=1),
            ContextData(),
            ObjectType(ObjectIdentity(oid)),
            lexicographicMode=False
    ):
        if errorIndication:
            raise Exception(f"SNMP error: {errorIndication}")
        if errorStatus:
            raise Exception(
                f"SNMP error: {errorStatus.prettyPrint()} at {errorIndex}"
            )

        for oid_obj, value in varBinds:
            # Extract the interface index from the OID
            idx = int(oid_obj.prettyPrint().split('.')[-1])
            results[idx] = value.prettyPrint()

    return results
def gather_snmp_interfaces(ip, community, port=161, timeout=3):
    """
    Collect interface information from a remote host using SNMPv2c.
    Returns a structure identical to gather_local_interfaces().
    """

    # -----------------------------
    # IF-MIB walks
    # -----------------------------
    ifDescr       = snmp_walk(ip, community, "1.3.6.1.2.1.2.2.1.2", port, timeout)
    ifType        = snmp_walk(ip, community, "1.3.6.1.2.1.2.2.1.3", port, timeout)
    ifMtu         = snmp_walk(ip, community, "1.3.6.1.2.1.2.2.1.4", port, timeout)
    ifSpeed       = snmp_walk(ip, community, "1.3.6.1.2.1.2.2.1.5", port, timeout)
    ifPhysAddress = snmp_walk(ip, community, "1.3.6.1.2.1.2.2.1.6", port, timeout)
    ifAdminStatus = snmp_walk(ip, community, "1.3.6.1.2.1.2.2.1.7", port, timeout)
    ifOperStatus  = snmp_walk(ip, community, "1.3.6.1.2.1.2.2.1.8", port, timeout)

    # -----------------------------
    # EtherLike-MIB (optional)
    # -----------------------------
    try:
        dot3Duplex = snmp_walk(ip, community, "1.3.6.1.2.1.10.7.2.1.19", port, timeout)
    except Exception:
        dot3Duplex = {}

    # -----------------------------
    # Build deterministic structure
    # -----------------------------
    interfaces = {}

    for idx in sorted(ifDescr.keys()):
        name = ifDescr[idx]

        iface = {
            "name": name,
            "mac": ifPhysAddress.get(idx),
            "ipv4": [],
            "ipv6": [],
            "mtu": int(ifMtu.get(idx, 0)),
            "speed": int(ifSpeed.get(idx, 0)),
            "duplex": dot3Duplex.get(idx),
            "admin_up": (int(ifAdminStatus.get(idx, 0)) == 1),
            "oper_up": (int(ifOperStatus.get(idx, 0)) == 1),
            "flags": [],
            "ifType": int(ifType.get(idx, 0))   # <-- ADD THIS
        }
        # Flags
        if iface["oper_up"]:
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

        # Normalize duplex
        duplex = iface.get("duplex")
        if source == "local":
            if duplex is None:
                duplex = "unknown"
            else:
                duplex = {
                    0: "unknown",
                    1: "half",
                    2: "full"
                }.get(int(duplex.value), "unknown")
        else:  # SNMP
            duplex = {
                "1": "unknown",
                "2": "half",
                "3": "full"
            }.get(str(duplex), "unknown")

        # Normalize speed
        speed = iface.get("speed")
        if speed in (0, None, 4294967295):
            speed = None

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
            "speed": speed,
            "duplex": duplex,
            "admin_up": admin_up,
            "oper_up": oper_up,
            "flags": flags,
            "ifType": iface.get("ifType")
        }

    return normalized
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
def apply_filters(interfaces, args):
    filtered = {}

    for name, iface in interfaces.items():

        # Alias filtering
        if is_alias(name) and not args.include_aliases:
            continue

        # Virtual filtering
        if args.ignore_virtual and is_virtual(name):
            continue

        # Local filtering
        if args.exclude_local and is_local(name, iface):
            continue

        # Pattern ignore
        if matches_ignore(name, args.ignore):
            continue

        # SNMP ifType filtering
        if args.ignore_iftype:
            if iface.get("ifType") in [int(t) for t in args.ignore_iftype]:
                continue

        filtered[name] = iface

    return filtered
def matches_ignore(name, patterns):
    if not patterns:
        return False
    lname = name.lower()
    for p in patterns:
        if p.lower() in lname:
            return True
    return False
# --------------------------------
# Enforcement
# --------------------------------
def enforce_require_interfaces(filtered, args):
    if not args.require:
        return None  # no error

    missing = []
    down = []

    for req in args.require:
        if req not in filtered:
            missing.append(req)
            continue

        iface = filtered[req]

        # Only enforce oper_up if the interface is intended to be up
        if iface["admin_up"] and not iface["oper_up"]:
            down.append(req)

    if missing:
        return f"CRITICAL - required interfaces missing: {', '.join(missing)}", CRITICAL

    if down:
        return f"CRITICAL - required interfaces down: {', '.join(down)}", CRITICAL

    return None
def parse_speed(s):
    s = s.strip().upper()
    for suffix, factor in SPEED_UNITS.items():
        if s.endswith(suffix):
            return int(s[:-1]) * factor
    return int(s)
def enforce_speed(filtered, args):
    if not args.require_speed:
        return None  # no enforcement requested

    min_speed = parse_speed(args.require_speed)
    slow = []

    for name, iface in filtered.items():
        speed = iface.get("speed")

        # Unknown speeds are allowed unless you want stricter rules later
        if speed is None:
            continue

        if speed < min_speed:
            slow.append(f"{name}({fmt_speed(speed)})")

    if slow:
        return (
            f"WARNING - interfaces below required speed {args.require_speed}: "
            f"{', '.join(slow)}",
            WARNING
        )

    return None
def extract_required(filtered, args):
    if not args.require:
        return filtered  # no change

    required_only = {}
    for req in args.require:
        if req in filtered:
            required_only[req] = filtered[req]
    return required_only
def enforce_iftype(filtered, args):
    if not args.require_iftype:
        return None

    required_types = [int(t) for t in args.require_iftype]

    for t in required_types:
        found_up = any(
            iface.get("ifType") == t and iface.get("admin_up") and iface.get("oper_up")
            for iface in filtered.values()
        )

        if not found_up:
            return (
                f"CRITICAL - no interfaces of required ifType {t} are UP",
                CRITICAL
            )

    return None

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

    print(json.dumps(payload, indent=2, sort_keys=True))
    return exit_code
def output_verbose(meta, interfaces):
    print(f"Interface Summary ({meta['mode']})")
    print(f"Host: {meta['host']} ({meta['ip']})")
    print(f"Interfaces: {meta['interface_count']}\n")

    header = (
        f"{'Name':<10} {'MAC':<20} {'MTU':<6} {'Speed':<7} "
        f"{'Duplex':<8} {'Admin':<6} {'Oper':<6} Flags"
    )
    print(header)
    print("-" * len(header))

    for name, iface in interfaces.items():
        mac = iface["mac"] or "-"
        mtu = iface["mtu"] if iface["mtu"] is not None else "-"
        speed = fmt_speed(iface["speed"])
        duplex = iface["duplex"]
        admin = "up" if iface["admin_up"] else "down"
        oper = "up" if iface["oper_up"] else "down"
        flags = fmt_flags(iface["flags"])

        print(
            f"{name:<10} {mac:<20} {mtu:<6} {speed:<7} "
            f"{duplex:<8} {admin:<6} {oper:<6} {flags}"
        )
def output_single_line(interfaces):
    # Filter out alias interfaces first
    filtered = {
        name: iface
        for name, iface in interfaces.items()
        if ":" not in name
    }

    if not filtered:
        return ("UNKNOWN - no interfaces detected", UNKNOWN)

    parts = []
    down_found = False

    for name, iface in filtered.items():
        if iface["oper_up"]:
            parts.append(f"{name} UP")
        else:
            parts.append(f"{name} DOWN")
            down_found = True

    if down_found:
        status = "CRITICAL"
        exit_code = CRITICAL
    else:
        status = "OK"
        exit_code = OK

    summary = ", ".join(parts)
    msg = f"{status} - {len(filtered)} interfaces: {summary}"
    return (msg, exit_code)

# --------------------------------------
# Main Entry Point
# --------------------------------------
def main():
    args = build_parser()
        
    rc = validate_host_local(args.host)
    if not rc["ok"]:
        print(f"UNKNOWN - {rc['error']}")
        sys.exit(UNKNOWN)
    data = {}
    if rc["local"]:
        # LOCAL MODE
        data = normalize_interfaces(gather_local_interfaces(),"local")
    else:
        # REMOTE MODE
        if not args.community:
            print("CRITICAL - remote host requires SNMP community string")
            sys.exit(CRITICAL)
        data = normalize_interfaces(gather_snmp_interfaces(rc["ip"], args.community),"snmp")
    filtered = apply_filters(data, args)
    # Enforcement: required interfaces
    err = enforce_require_interfaces(filtered, args)
    if err:
        msg, code = err
        print(msg)
        sys.exit(code)

    # Enforcement: speed
    err = enforce_speed(filtered, args)
    if err:
        msg, code = err
        print(msg)
        sys.exit(code)

    # Required ifType
    err = enforce_iftype(filtered, args)
    if err:
        msg, code = err
        print(msg)
        sys.exit(code)
    meta = {
        "host": args.host,
        "ip": rc["ip"],
        "mode": "local" if rc["local"] else "snmp",
        "error": None,
        "interface_count": len(filtered)
    }
    if args.json:
        sys.exit(output_json(meta, filtered, OK))
    elif args.verbose:
        output_verbose(meta, filtered)
        sys.exit(OK)
    display_set = extract_required(filtered, args) if args.require else filtered
    msg, code = output_single_line(display_set)
    print(msg)
    sys.exit(code)

if __name__ == "__main__":
    main()
