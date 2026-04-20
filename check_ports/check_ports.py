#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Leon McClatchey, Linktech Engineering LLC
"""
File: check_ports.py
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-04-20
Modified: 2026-04-20
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
            "Deterministic, multi-port TCP availability checker with Nagios-compatible"
            "output and optional JSON diagnostics."
            "Supports verbose, JSON, and Nagios output."
        ),
        formatter_class=CustomFormatter,
        add_help=True
    )
    # -----------------------------
    # Usage line
    # -----------------------------
    parser.usage = "%(prog)s -H <host> -p <ports> [options]"
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
        "-p", "--ports",
        required=True,
        help=(
            "Comma-delimited list of ports or port ranges."
            "Examples: '22,80,443', '1-1024', or '22,80,1000-1010'."
            "Hostnames in --ports are not allowed; use -H/--host to specify the target host."
        )
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
    # Nagios Behavior Filters
    # ------------------------------------------------------------
    filt = parser.add_argument_group("Nagios Behavior Filters")
    filt.add_argument(
        "--require-all",
        action="store_true",
        help="Require all ports to be open; if any fail, return CRITICAL."
    )
    filt.add_argument(
        "--require-any",
        action="store_true",
        help="Require at least one port to be open; if all fail, return CRITICAL."
    )
    filt.add_argument(
        "--fail-only",
        action="store_true",
        help="Only report failed ports in verbose or JSON output."
    )
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
    out.add_argument(
        "-V", "--version",
        action="version",
        version=f"{SCRIPT_NAME} {SCRIPT_VERSION} (Python {platform.python_version()})",
        help="Show script and Python version")

    return parser.parse_args()
# -----------------------------
# Port Scanning 
# -----------------------------
def parse_ports(port_string):
    """
    Parse a comma-delimited list of ports and ranges into a sorted list of ints.

    Allowed:
        "22"
        "22,80,443"
        "1-1024"
        "22,80,1000-1010"

    Disallowed:
        "host:22"
        "192.168.1.1:22"
        "example.com:443"
        "22,tcp"

    Returns:
        List[int] - sorted, deduplicated list of ports

    Raises:
        ValueError - if any token is invalid
    """

    ports = set()

    # Split on commas
    tokens = [t.strip() for t in port_string.split(",") if t.strip()]

    if not tokens:
        raise ValueError("No ports specified.")

    for token in tokens:

        # ------------------------------------------------------------
        # 1. Reject host:port patterns (out of scope for this tool)
        # ------------------------------------------------------------
        if ":" in token:
            raise ValueError(
                f"Invalid port token '{token}': hostnames are not allowed in --ports. "
                "Use -H/--host to specify the target host."
            )

        # ------------------------------------------------------------
        # 2. Range: "start-end"
        # ------------------------------------------------------------
        if "-" in token:
            try:
                start_str, end_str = token.split("-", 1)
                start = int(start_str)
                end = int(end_str)
            except ValueError:
                raise ValueError(f"Invalid port range '{token}'.")

            if start < 1 or end > 65535 or start > end:
                raise ValueError(f"Invalid port range '{token}' (must be 1–65535 and start <= end).")

            for p in range(start, end + 1):
                ports.add(p)

            continue

        # ------------------------------------------------------------
        # 3. Single integer port
        # ------------------------------------------------------------
        try:
            p = int(token)
        except ValueError:
            raise ValueError(f"Invalid port '{token}' (must be an integer).")

        if p < 1 or p > 65535:
            raise ValueError(f"Invalid port '{token}' (must be between 1 and 65535).")

        ports.add(p)

    # Return sorted list
    return sorted(ports)
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
        f"[START] {SCRIPT_NAME}.py"
        f" host={meta['host']}"
        f" ports={meta['ports_input']}"
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
    Deterministic, operator-grade, and consistent with NMS_Tools.
    """

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

    # ------------------------------------------------------------
    # Build metadata for logging
    # ------------------------------------------------------------
    meta = {
        "log_dir": args.log_dir,
        "log_max_mb": args.log_max_mb,
        "mode": "verbose" if args.verbose else "normal",
        "_log_warn_emitted": False,

        # tool-specific fields
        "host": args.host,
        "ports_input": args.ports,
        "timeout": args.timeout,
        "require_all": args.require_all,
        "require_any": args.require_any,
        "fail_only": args.fail_only,
    }
    flags = Flags.from_args(args)
    mode = detect_mode(flags)
    logging_enabled = (mode != "nagios") and bool(args.log_dir)

    # ------------------------------------------------------------
    # Rotate log and write start banner
    # ------------------------------------------------------------
    if logging_enabled:
        rotate_log_if_needed(meta)
        write_log(meta, start_banner_ports(meta))

    # ------------------------------------------------------------
    # Parse ports
    # ------------------------------------------------------------
    try:
        ports = parse_ports(args.ports)
    except ValueError as e:
        msg = f"UNKNOWN - {e}"
        if logging_enabled:
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
