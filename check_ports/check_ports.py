#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Leon McClatchey, Linktech Engineering LLC
"""
File: check_ports.py
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-04-20
Modified: 2026-04-21
Part of: NMS_Tools Monitoring Suite
License: MIT (see LICENSE for details)

Description:
    Deterministic, multi-port TCP availability checker with Nagios-compatible
    output and optional JSON diagnostics.
"""
import argparse
import json
import os
import platform
import shlex
import shutil
import socket
import sys
import zipfile

from datetime import datetime, timedelta
from enum import IntEnum, auto
from pathlib import Path

# Nagios Exit Codes
OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3
NAGIOS_STATE_NAMES = {
    OK: "OK",
    WARNING: "WARNING",
    CRITICAL: "CRITICAL",
    UNKNOWN: "UNKNOWN",
}
# Other Global Constants
SCRIPT_VERSION = "1.0.0"
SCRIPT_NAME = Path(sys.argv[0]).stem
# Flag Classes
class FlagNames(IntEnum):
    VERBOSE = auto()
    JSON = auto()
    QUIET = auto()

    REQUIRE_ALL = auto()
    REQUIRE_ANY = auto()
    FAIL_ONLY = auto()

    # Provider override is not a boolean flag, so no bit here.
class Flags:
    """
    Operator-grade flag engine for check_weather.
    Backed by a deterministic bitmask.
    """

    def __init__(self):
        self._mask = 0

    # -----------------------------
    # Core bit operations
    # -----------------------------
    def set(self, flag: FlagNames, value: bool = True):
        if value:
            self._mask |= (1 << flag.value)
        else:
            self._mask &= ~(1 << flag.value)

    def get(self, flag: FlagNames) -> bool:
        return bool(self._mask & (1 << flag.value))

    # -----------------------------
    # Convenience accessors
    # -----------------------------
    def __getitem__(self, flag: FlagNames) -> bool:
        return self.get(flag)

    def __setitem__(self, flag: FlagNames, value: bool):
        self.set(flag, value)

    # -----------------------------
    # Introspection
    # -----------------------------
    def active_names(self):
        return [
            name.name
            for name in FlagNames
            if self.get(name)
        ]

    def to_hex(self):
        return f"0x{self._mask:08X}"

    # -----------------------------
    # Build from argparse args
    # -----------------------------
    @classmethod
    def from_args(cls, args):
        f = cls()

        # Output modes
        f[FlagNames.VERBOSE] = args.verbose
        f[FlagNames.JSON] = args.json
        f[FlagNames.QUIET] = args.quiet

        # Filter flags
        f[FlagNames.REQUIRE_ALL] = args.require_all
        f[FlagNames.REQUIRE_ANY] = args.require_any
        f[FlagNames.FAIL_ONLY ] = args.fail_only

        return f
MODE_MAP = {
    FlagNames.JSON:    "json",
    FlagNames.VERBOSE: "verbose",
    FlagNames.QUIET:   "quiet",
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
            "Deterministic, multi-port TCP availability checker with "
            "Nagios-compatible output and optional JSON diagnostics. "
            "Supports verbose, JSON, and Nagios output."
        ),
        formatter_class=CustomFormatter,
        add_help=True
    )

    parser.usage = "%(prog)s -H <host> (--ports <ports> | --service <name>) [options]"

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

    # ------------------------------------------------------------
    # Port / Service Selection
    # ------------------------------------------------------------
    sel = parser.add_argument_group("Port / Service Selection")
    sel.add_argument(
        "-p", "--ports",
        help=(
            "Comma-delimited list of ports or port ranges. "
            "Examples: '22,80,443', '1-1024', or '22,80,1000-1010'. "
            "Hostnames in --ports are not allowed; use -H/--host to specify the target host."
        )
    )
    sel.add_argument(
        "-s", "--service",
        help=(
            "Comma-delimited list of service names to resolve. "
            "Examples: 'http', 'https,ssh', or 'smtp,pop3,imap'. "
            "Each service is resolved using /etc/services and socket.getservbyname()."
        )
    )

    # ------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------
    log = parser.add_argument_group("Logging")
    log.add_argument(
        "--log-dir",
        dest="log_dir",
        metavar="DIR",
        default=None,
        help="Directory to store logs (optional). If omitted, logging is disabled."
    )
    log.add_argument(
        "--log-max-mb",
        dest="log_max_mb",
        metavar="MB",
        type=int,
        default=50,
        help="Maximum log size in MB before rotation."
    )

    # ------------------------------------------------------------
    # Nagios Behavior Filters
    # ------------------------------------------------------------
    filt = parser.add_argument_group("Nagios Behavior Filters")
    filt.add_argument("--require-all", action="store_true",
                      help="Require all ports to be open; if any fail, return CRITICAL.")
    filt.add_argument("--require-any", action="store_true",
                      help="Require at least one port to be open; if all fail, return CRITICAL.")
    filt.add_argument("--fail-only", action="store_true",
                      help="Only report failed ports in verbose or JSON output.")

    # ------------------------------------------------------------
    # Output Modes
    # ------------------------------------------------------------
    out = parser.add_argument_group("Output Modes")
    out.add_argument("-v", "--verbose", action="store_true", help="Detailed output")
    out.add_argument("-j", "--json", action="store_true", help="JSON output for automation")
    out.add_argument("-q", "--quiet", action="store_true", help="Quiet mode: exit code only")
    out.add_argument(
        "-V", "--version",
        action="version",
        version=f"{SCRIPT_NAME} {SCRIPT_VERSION} (Python {platform.python_version()})",
        help="Show script and Python version"
    )

    args = parser.parse_args()

    # Require at least one of --ports or --service
    if not args.ports and not args.service:
        raise CheckArgError("Either --ports or --service must be specified.")

    return args
# -----------------------------
# Port Scanning 
# -----------------------------
def parse_ports(port_string):
    """
    Parse a comma-delimited list of ports or port ranges.
    Rejects host:port, host:service, and service names.
    Returns a sorted, deduped list of integer ports.
    """
    if not port_string:
        return []

    tokens = [t.strip() for t in port_string.split(",") if t.strip()]
    ports = []

    for token in tokens:
        # Reject host:port or host:service
        if ":" in token:
            raise CheckArgError(
                f"Invalid port token '{token}'. Hostnames or service names are not "
                "allowed in --ports; use -H/--host for hosts and -s/--service for services."
            )

        # Reject service names (alphabetic tokens)
        if token.isalpha():
            raise CheckArgError(
                f"Invalid port token '{token}'. Service names belong in --service, not --ports."
            )

        # Handle ranges
        if "-" in token:
            try:
                start, end = token.split("-", 1)
                start = int(start)
                end = int(end)
            except ValueError:
                raise CheckArgError(f"Invalid port range '{token}'.")

            if start < 1 or end < 1 or start > 65535 or end > 65535:
                raise CheckArgError(f"Port range '{token}' is out of valid TCP range.")

            if start > end:
                raise CheckArgError(f"Invalid port range '{token}': start > end.")

            ports.extend(range(start, end + 1))
            continue

        # Handle single numeric ports
        try:
            port = int(token)
        except ValueError:
            raise CheckArgError(f"Invalid port token '{token}'.")

        if port < 1 or port > 65535:
            raise CheckArgError(f"Port '{port}' is out of valid TCP range.")

        ports.append(port)

    return sorted(set(ports))
def resolve_services(service_string):
    """
    Resolve one or more service names into a list of TCP ports.
    Supports comma-delimited service names.
    Rejects numeric ports in --service.
    """
    if not service_string:
        return []

    services = [s.strip() for s in service_string.split(",") if s.strip()]
    resolved_ports = []

    for svc in services:
        # Reject numeric ports in --service
        if svc.isdigit():
            raise CheckArgError(
                f"Invalid service '{svc}'. Numeric ports belong in --ports, not --service."
            )

        ports_for_service = []

        # Primary resolution: socket.getservbyname()
        try:
            port = socket.getservbyname(svc, "tcp")
            ports_for_service.append(port)
        except OSError:
            # Fallback: manual scan of /etc/services
            try:
                with open("/etc/services", "r") as f:
                    for line in f:
                        if line.startswith("#") or not line.strip():
                            continue
                        parts = line.split()
                        if len(parts) >= 2 and parts[0] == svc:
                            port_proto = parts[1]
                            if "/tcp" in port_proto:
                                port_num = int(port_proto.split("/")[0])
                                ports_for_service.append(port_num)
            except FileNotFoundError:
                pass

        if not ports_for_service:
            raise CheckArgError(f"Service '{svc}' not found in /etc/services")

        if len(ports_for_service) > 1:
            print(f"WARNING: Service '{svc}' has multiple TCP entries; using all.")

        resolved_ports.extend(ports_for_service)

    return sorted(set(resolved_ports))
def build_port_list(args):
    """
    Combine ports from --ports and --service into a single deduped list.
    """
    explicit_ports = parse_ports(args.ports) if args.ports else []
    service_ports = resolve_services(args.service) if args.service else []

    all_ports = sorted(set(explicit_ports + service_ports))

    if not all_ports:
        raise CheckArgError("No ports resolved from --ports or --service.")

    return all_ports
def check_port(host, port, timeout):
    """
    Attempt a single TCP connection to host:port with a strict timeout.

    Returns one of:
        "open"
        "closed"
        "timeout"
        "unreachable"
    """

    try:
        with socket.create_connection((host, port), timeout):
            return "open"

    except socket.timeout:
        return "timeout"

    except ConnectionRefusedError:
        return "closed"

    except OSError:
        # Includes: network unreachable, no route to host, DNS issues, etc.
        return "unreachable"
def compute_nagios_code(enf, args):
    # require-all: all ports must be open
    if args.require_all:
        return 0 if len(enf["closed_ports"]) == 0 \
                   and len(enf["timeout_ports"]) == 0 \
                   and len(enf["unreachable_ports"]) == 0 else 2

    # require-any: at least one port must be open
    if args.require_any:
        return 0 if len(enf["open_ports"]) > 0 else 2

    # default behavior
    if len(enf["unreachable_ports"]) > 0:
        return 2  # CRITICAL
    if len(enf["timeout_ports"]) > 0:
        return 2  # CRITICAL
    if len(enf["closed_ports"]) > 0:
        return 1  # WARNING
    return 0      # OK
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
def start_banner_ports(meta):
    return (
        f"[START]"
        f" cmd=\"{meta['command']}\""
        f" host={meta['host']}"
        f" ports_explicit={meta['explicit_ports']}"
        f" ports_service={meta['service_ports']}"
        f" ports_all={meta['all_ports']}"
        f" timeout={meta['timeout']}"
        f" require_all={meta['require_all']}"
        f" require_any={meta['require_any']}"
        f" fail_only={meta['fail_only']}"
    )
def log_port_result(host, port, status):
    return f"[PORT] host={host} port={port} status={status}"
def log_summary_ports(state, message):
    return f"[RESULT] state={state} message=\"{message}\""
def end_banner():
    return "[END]"
def detect_mode(flags):
    for flag, mode in MODE_MAP.items():
        if flags[flag]:
            return mode
    return "nagios"
# -------------------------------------
# Nagios Functions
# -------------------------------------
def nagios_state_string(code):
    return NAGIOS_STATE_NAMES.get(code, "UNKNOWN")
def build_nagios_message(enf, code):
    """
    Build the single-line Nagios output message.
    Adds service-name awareness for single-service checks
    and port-aware messages for single explicit-port checks.
    """

    services = enf.get("services_requested", [])
    service_ports = enf.get("service_ports", [])
    explicit_ports = enf.get("explicit_ports", [])
    all_ports = enf.get("all_ports", [])

    # ------------------------------------------------------------
    # Case 1: Single-service, single-port check
    # ------------------------------------------------------------
    single_service = (
        len(services) == 1
        and len(service_ports) == 1
        and len(explicit_ports) == 0
        and len(all_ports) == 1
    )

    if single_service:
        svc = services[0]
        port = all_ports[0]

        if port in enf["open_ports"]:
            return f"OK - {svc} ({port}) is open"
        if port in enf["closed_ports"]:
            return f"WARNING - {svc} ({port}) is closed"
        if port in enf["timeout_ports"]:
            return f"CRITICAL - {svc} ({port}) timed out"
        if port in enf["unreachable_ports"]:
            return f"CRITICAL - {svc} ({port}) is unreachable"

        return f"UNKNOWN - {svc} ({port}) unexpected state"

    # ------------------------------------------------------------
    # Case 2: Single explicit port (no services)
    # ------------------------------------------------------------
    single_explicit = (
        len(explicit_ports) == 1
        and len(services) == 0
        and len(all_ports) == 1
    )

    if single_explicit:
        port = explicit_ports[0]

        if port in enf["open_ports"]:
            return f"OK - Port {port} is open"
        if port in enf["closed_ports"]:
            return f"WARNING - Port {port} is closed"
        if port in enf["timeout_ports"]:
            return f"CRITICAL - Port {port} timed out"
        if port in enf["unreachable_ports"]:
            return f"CRITICAL - Port {port} is unreachable"

        return f"UNKNOWN - Port {port} unexpected state"

    # ------------------------------------------------------------
    # Case 3: Fallback to original multi-port behavior
    # ------------------------------------------------------------
    if code == OK:
        return (
            "OK - All ports open: "
            + ", ".join(map(str, enf["open_ports"]))
            if enf["open_ports"]
            else "OK - No ports specified"
        )

    if code == WARNING:
        return (
            "WARNING - Closed ports: "
            + ", ".join(map(str, enf["closed_ports"]))
            if enf["closed_ports"]
            else "WARNING - No closed ports"
        )

    if code == CRITICAL:
        bad = (
            enf["unreachable_ports"]
            + enf["timeout_ports"]
            + enf["closed_ports"]
        )
        return (
            "CRITICAL - Problem ports: "
            + ", ".join(map(str, bad))
            if bad
            else "CRITICAL - No ports responded"
        )

    return "UNKNOWN - Unexpected state"

def main():
    args = build_parser()
    command_string = " ".join(shlex.quote(arg) for arg in sys.argv)
    # ------------------------------------------------------------
    # Build metadata for logging
    # ------------------------------------------------------------
    meta = {
        "log_dir": args.log_dir,
        "log_max_mb": args.log_max_mb,
        "mode": "verbose" if args.verbose else "normal",
        "_log_warn_emitted": False,
        "command": command_string,
        
        # tool-specific fields
        "host": args.host,
        "timeout": args.timeout,
        "require_all": args.require_all,
        "require_any": args.require_any,
        "fail_only": args.fail_only,
    }
    flags = Flags.from_args(args)
    mode = detect_mode(flags)
    logging_enabled = (mode != "nagios") and bool(args.log_dir)

    # ------------------------------------------------------------
    # Resolve and combine ports
    # ------------------------------------------------------------
    try:
        explicit_ports = parse_ports(args.ports) if args.ports else []
        service_ports  = resolve_services(args.service) if args.service else []
        ports = sorted(set(explicit_ports + service_ports))

        if not ports:
            raise CheckArgError("No ports resolved from --ports or --service.")

        # ------------------------------------------------------------
        # Update metadata with dynamic fields
        # ------------------------------------------------------------
        meta["explicit_ports"] = explicit_ports
        meta["service_ports"]  = service_ports
        meta["all_ports"]      = ports

        # ------------------------------------------------------------
        # Rotate log and write start banner (NOW SAFE)
        # ------------------------------------------------------------
        if logging_enabled:
            rotate_log_if_needed(meta)
            write_log(meta, start_banner_ports(meta))

    except CheckArgError as e:
        msg = f"UNKNOWN - {e}"
        if logging_enabled:
            # No START banner was written → write a minimal START
            rotate_log_if_needed(meta)
            write_log(meta, f"[START] {SCRIPT_NAME}.py host={meta['host']} cmd=\"{meta['command']}\"")
            write_log(meta, log_summary_ports("UNKNOWN", msg))
            write_log(meta, end_banner())
        print(msg)
        sys.exit(3)

    # ------------------------------------------------------------
    # Execute connection tests
    # ------------------------------------------------------------
    results = []
    for port in ports:
        status = check_port(args.host, port, args.timeout)
        results.append({"port": port, "status": status})

        if logging_enabled:
            write_log(meta, log_port_result(args.host, port, status))

    # ------------------------------------------------------------
    # Build enforcement object
    # ------------------------------------------------------------
    enf = {
        "host": args.host,
        "services_requested": args.service.split(",") if args.service else [],
        "service_ports": service_ports,          # ports resolved from services
        "explicit_ports": explicit_ports,        # ports from --ports
        "all_ports": ports,                      # final combined list
        "service_map": dict(zip(
            "services_requested",
            "service_ports"
        )),

        "results": results,

        "open_ports":        [r["port"] for r in results if r["status"] == "open"],
        "closed_ports":      [r["port"] for r in results if r["status"] == "closed"],
        "timeout_ports":     [r["port"] for r in results if r["status"] == "timeout"],
        "unreachable_ports": [r["port"] for r in results if r["status"] == "unreachable"],
    }

    # ------------------------------------------------------------
    # Compute Nagios exit code
    # ------------------------------------------------------------
    code = compute_nagios_code(enf, args)

    # ------------------------------------------------------------
    # Output modes
    # ------------------------------------------------------------
    if args.json:
        print(json.dumps(enf, indent=2))
        if logging_enabled:
            write_log(meta, log_summary_ports(nagios_state_string(code), "json output"))
            write_log(meta, end_banner())
        sys.exit(code)

    if args.verbose:
        print(f"Host: {args.host}")
        print(f"Services requested: {', '.join(args.service.split(',')) if args.service else 'None'}")
        print(f"Service ports:      {', '.join(str(p) for p in service_ports) if service_ports else 'None'}")
        print(f"Explicit ports:     {', '.join(str(p) for p in explicit_ports) if explicit_ports else 'None'}")
        print(f"All ports:          {', '.join(str(p) for p in ports)}")
        print()

        for r in results:
            print(f"{args.host}:{r['port']} = {r['status']}")

        if logging_enabled:
            write_log(meta, log_summary_ports(nagios_state_string(code), "verbose output"))
            write_log(meta, end_banner())
        sys.exit(code)

    if args.quiet:
        if logging_enabled:
            write_log(meta, log_summary_ports(nagios_state_string(code), "quiet output"))
            write_log(meta, end_banner())
        sys.exit(code)

    # ------------------------------------------------------------
    # Default Nagios single-line output
    # ------------------------------------------------------------
    msg = build_nagios_message(enf, code)
    print(msg)

    if logging_enabled:
        write_log(meta, log_summary_ports(nagios_state_string(code), msg))
        write_log(meta, end_banner())

    sys.exit(code)

if __name__ == "__main__":
    main()
