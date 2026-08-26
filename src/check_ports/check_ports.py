#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Leon McClatchey, Linktech Engineering LLC
"""
File: check_ports.py
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-04-20
Modified: 2026-08-26
Part of: NMS_Tools Monitoring Suite
License: MIT (see LICENSE for details)

Description:
    Deterministic, multi-port TCP availability checker with Nagios-compatible
    output and optional JSON diagnostics.
"""
import json
import os
import shlex
import socket
import sys

from pathlib import Path

from PythonTools.log_helpers.factory import LoggerFactory
from PythonTools.nagios import (
    OK,
    WARNING,
    CRITICAL,
    UNKNOWN,
    STATE_NAMES,
    Flags,
    MODE_MAP,
    BaseNagiosParser,
    CheckArgError,
    should_output,
    nagios_summary,
)
from PythonTools.net import check_port
from PythonTools.parsing import parse_ports, resolve_services

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
# Other Global Constants
SCRIPT_VERSION = "1.1.0"
SCRIPT_NAME = Path(sys.argv[0]).stem

def build_parser():
    nag = BaseNagiosParser(
        prog=SCRIPT_NAME,
        description=(
            "Deterministic, multi-port TCP availability checker with "
            "Nagios-compatible output and optional JSON diagnostics.\n\n"
            "Supports verbose, JSON, and Nagios output."
        ),
        script_version=SCRIPT_VERSION,
        suite_version=VERSION,
    )

    # Usage line
    nag.parser.usage = "%(prog)s -H <host> (--ports <ports> | --service <name>) [options]"

    # ------------------------------------------------------------
    # Core Options
    # ------------------------------------------------------------
    core = nag.add_group("Core Options")
    core.add_argument(
        "-H", "--host",
        required=True,
        help="Target hostname or IP address",
    )
    core.add_argument(
        "-t", "--timeout",
        type=int,
        default=5,
        help="Connection timeout in seconds",
    )

    # ------------------------------------------------------------
    # Port / Service Selection
    # ------------------------------------------------------------
    sel = nag.add_group("Port / Service Selection")
    sel.add_argument(
        "-p", "--ports",
        help=(
            "Comma-delimited list of ports or port ranges. "
            "Examples: '22,80,443', '1-1024', or '22,80,1000-1010'. "
            "Hostnames in --ports are not allowed; use -H/--host to specify the target host."
        ),
    )
    sel.add_argument(
        "-s", "--service",
        help=(
            "Comma-delimited list of service names to resolve. "
            "Examples: 'http', 'https,ssh', or 'smtp,pop3,imap'. "
            "Each service is resolved using /etc/services and socket.getservbyname()."
        ),
    )
   # ------------------------------------------------------------
    # Nagios Behavior Filters
    # ------------------------------------------------------------
    filt = nag.add_group("Nagios Behavior Filters")
    filt.add_argument(
        "--require-all",
        action="store_true",
        help="Require all ports to be open; if any fail, return CRITICAL.",
    )
    filt.add_argument(
        "--require-any",
        action="store_true",
        help="Require at least one port to be open; if all fail, return CRITICAL.",
    )
    filt.add_argument(
        "--fail-only",
        action="store_true",
        help="Only report failed ports in verbose or JSON output.",
    )
    nag.parser.epilog = (
        "Examples:\n"
        "  %(prog)s -H example.com --ports 22,80,443 -v\n"
        "  %(prog)s -H example.com --service http,https --json\n"
        "  %(prog)s -H example.com --ports 1-1024 --require-all\n"
    )

    args, flags, mode = nag.parse()
    # Require at least one of --ports or --service
    if not args.ports and not args.service:
        nag.exit_unknown("Either --ports or --service must be specified.")

    return args, flags, mode
def build_metadata(args, mode):
    """
    Build the initial metadata dictionary for check_ports.
    Pure function: no logging, no side-effects.
    """
    command_string = " ".join(shlex.quote(arg) for arg in sys.argv)

    return {
        "log_dir": args.log_dir,
        "log_max_mb": args.log_max_mb,
        "mode": mode,
        "_log_warn_emitted": False,
        "command": command_string,
        "logging_enabled": (mode != "nagios") and bool(args.log_dir),

        # tool-specific fields
        "host": args.host,
        "timeout": args.timeout,
        "require_all": args.require_all,
        "require_any": args.require_any,
        "fail_only": args.fail_only,

        # dynamic fields (populated later)
        "service_requested": [],
        "explicit_ports": [],
        "service_ports": [],
        "all_ports": [],
    }
def resolve_all_ports(args, meta, logger=None ):
    """
    Resolve explicit ports and service ports, merge them, update metadata,
    emit warnings, and write the start banner. Handles CheckArgError cleanly.
    Returns (ports, explicit_ports, service_ports).
    """
    logging_enabled = meta["logging_enabled"]

    try:
        # Parse explicit ports
        explicit_ports = parse_ports(args.ports) if args.ports else []

        # Resolve service ports
        services_requested = args.service.split(",") if args.service else []
        meta["service_requested"] = services_requested
        service_ports = []
        for svc in services_requested:
            srv_ports = []
            srv_ports = resolve_services(svc)
            # Warn if a service maps to multiple ports
            if len(srv_ports) > 1:
                msg = f"Service '{svc}' maps to multiple TCP ports: {srv_ports}"
                if logger and logging_enabled:
                    logger.warning(msg)
                else:
                    print(msg)
            service_ports.extend(srv_ports)


        # Merge ports
        ports = sorted(set(explicit_ports + service_ports))

        if not ports:
            raise CheckArgError("No ports resolved from --ports or --service.")

        # Update metadata
        meta["explicit_ports"] = explicit_ports
        meta["service_ports"]  = service_ports
        meta["all_ports"]      = ports

        # Write start banner
        if logger and logging_enabled:
            logger.info(start_banner_ports(meta))

        return 

    except CheckArgError as e:
        # UNKNOWN state handling
        msg = f"UNKNOWN - {e}"

        if logger and logging_enabled:
            # No START banner was written → write a minimal START
            logger.info(meta, f"[START] {SCRIPT_NAME}.py host={meta['host']} cmd=\"{meta['command']}\"")
            logger.info(meta, log_summary_ports("UNKNOWN", msg))
            logger.info(meta, end_banner())

        print(msg)
        os._exit(UNKNOWN)
def run_port_checks(args, meta, logger=None):
    results = []

    ports = meta["all_ports"]
    service_ports = meta["service_ports"]
    logging_enabled = meta["logging_enabled"]

    # Build service → port mapping
    services_requested = meta["service_requested"]
    service_map = dict(zip(services_requested, service_ports))
    port_to_service = {str(port): svc for svc, port in service_map.items()}

    for port in ports:
        status = check_port(args.host, port, args.timeout)
        results.append({"port": port, "status": status})

        if logger and logging_enabled:
            svc = port_to_service.get(str(port))
            label = f"{svc}({port})" if svc else port
            logger.info(log_port_result(args.host, label, status))

    return results, port_to_service

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
def initialize_logger(args, mode):
    """
    Unified LoggerFactory initialization for check_ports.
    Matches the model used by check_cert and check_ticker.
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
def log_summary_ports(state, message, enf=None):
    """
    Build the RESULT line for the log.

    If enf is provided, include grouped service/explicit info so logs
    show which services/ports were open/closed.
    """
    base = f"[RESULT] state={state} message=\"{message}\""

    if not enf:
        return base

    segments = []

    service_open = enf.get("service_open", [])
    service_closed = enf.get("service_closed", [])
    explicit_open = enf.get("explicit_open", [])
    explicit_closed = enf.get("explicit_closed", [])

    if service_open:
        segments.append("service_open=" + ",".join(service_open))
    if service_closed:
        segments.append("service_closed=" + ",".join(service_closed))
    if explicit_open:
        segments.append("explicit_open=" + ",".join(explicit_open))
    if explicit_closed:
        segments.append("explicit_closed=" + ",".join(explicit_closed))

    if segments:
        return base + " " + " ".join(segments)
    return base
def end_banner():
    return "[END]"
def detect_mode(flags):
    for flag, mode in MODE_MAP.items():
        if flags[flag]:
            return mode
    return "nagios"
# -------------------------------------
# Display Functions
# -------------------------------------
def nagios_state_string(code):
    return STATE_NAMES.get(code, "UNKNOWN")
def build_nagios_message(enf, code):
    """
    Build the single-line Nagios output message.
    - Preserves special cases for single-service and single-explicit checks
    - Adds grouped, operator-grade output for multi-port checks
    - Only displays non-empty categories
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
    # Case 3: Multi-port grouped output (new behavior with service names)
    # ------------------------------------------------------------

    # Build mapping: port -> service name
    port_to_service = {}
    for svc, port in zip(services, service_ports):
        port_to_service[port] = svc

    # Build the four buckets with service names where applicable
    def svc_label(port):
        return f"{port_to_service[port]}({port})" if port in port_to_service else str(port)

    service_open = sorted([svc_label(p) for p in service_ports if p in enf["open_ports"]])
    service_closed = sorted([svc_label(p) for p in service_ports if p in enf["closed_ports"]])

    explicit_open = sorted([str(p) for p in explicit_ports if p in enf["open_ports"]])
    explicit_closed = sorted([str(p) for p in explicit_ports if p in enf["closed_ports"]])

    # Helper to format non-empty categories
    def fmt(label, items):
        if not items:
            return None
        return f"{label}: {','.join(items)}"

    segments = []
    for label, items in [
        ("service_open", service_open),
        ("service_closed", service_closed),
        ("explicit_open", explicit_open),
        ("explicit_closed", explicit_closed),
    ]:
        seg = fmt(label, items)
        if seg:
            segments.append(seg)

    # Determine summary
    if code == OK:
        summary = "All ports open" if not service_closed and not explicit_closed else "Ports OK"
    elif code == WARNING:
        summary = "Some ports closed"
    elif code == CRITICAL:
        if service_open or explicit_open:
            summary = "Closed ports detected"
        else:
            summary = "All ports closed"
    else:
        summary = "Port status"

    segment_str = "; ".join(segments)

    perf_open = len(service_open) + len(explicit_open)
    perf_closed = len(service_closed) + len(explicit_closed)
    perfdata = f"ports_open={perf_open} ports_closed={perf_closed}"

    if segment_str:
        return f"{code} - {summary} ({segment_str}) | {perfdata}"
    else:
        return f"{code} - {summary} | {perfdata}"
def build_enforcement_object(meta, results, port_to_service):
    services_requested = meta["service_requested"]
    service_ports      = meta["service_ports"]
    explicit_ports     = meta["explicit_ports"]
    ports              = meta["all_ports"]

    # service → port
    service_map = {
        svc: port
        for svc, port in zip(services_requested, service_ports)
    }

    # Helper for labeling service ports
    def svc_label(port):
        svc = port_to_service.get(str(port))
        return f"{svc}({port})" if svc else str(port)

    open_ports        = [r["port"] for r in results if r["status"] == "open"]
    closed_ports      = [r["port"] for r in results if r["status"] == "closed"]
    timeout_ports     = [r["port"] for r in results if r["status"] == "timeout"]
    unreachable_ports = [r["port"] for r in results if r["status"] == "unreachable"]

    service_open   = sorted([svc_label(p) for p in service_ports if p in open_ports])
    service_closed = sorted([svc_label(p) for p in service_ports if p in closed_ports])

    explicit_open   = sorted([str(p) for p in explicit_ports if p in open_ports])
    explicit_closed = sorted([str(p) for p in explicit_ports if p in closed_ports])

    status_by_port = {str(r["port"]): r["status"] for r in results}

    status_by_service = {
        svc: status_by_port.get(str(port), "unknown")
        for svc, port in service_map.items()
    }

    return {
        "host": meta["host"],

        "services_requested": services_requested,
        "service_ports": service_ports,
        "explicit_ports": explicit_ports,
        "all_ports": ports,

        "service_map": service_map,
        "port_to_service": port_to_service,   # ← FIXED

        "service_open": service_open,
        "service_closed": service_closed,
        "explicit_open": explicit_open,
        "explicit_closed": explicit_closed,

        "results": results,
        "status_by_port": status_by_port,
        "status_by_service": status_by_service,

        "open_ports": open_ports,
        "closed_ports": closed_ports,
        "timeout_ports": timeout_ports,
        "unreachable_ports": unreachable_ports,
    }
def output_results(mode, args, meta, results, port_to_service, enf, code, logger=None):
    """
    Handle all output modes:
        • json
        • verbose
        • quiet
        • default (Nagios single-line)
    """

    logging_enabled = meta["logging_enabled"]

    match mode:

        # ------------------------------------------------------------
        # JSON output
        # ------------------------------------------------------------
        case "json":
            print(json.dumps(enf, indent=2))

            if logger and logging_enabled:
                logger.info(log_summary_ports(nagios_state_string(code), "json output", enf))
                logger.info(end_banner())

            os._exit(code)

        # ------------------------------------------------------------
        # Verbose output
        # ------------------------------------------------------------
        case "verbose":
            print(f"Host: {meta['host']}")
            print(f"Services requested: {', '.join(meta['service_requested']) or 'None'}")

            # Show service ports with service names
            if meta["service_ports"]:
                svc_labels = [
                    f"{svc}({port})"
                    for svc, port in zip(meta["service_requested"], meta["service_ports"])
                ]
                print(f"Service ports:      {', '.join(svc_labels)}")
            else:
                print("Service ports:      None")

            print(f"Explicit ports:     {', '.join(str(p) for p in meta['explicit_ports']) or 'None'}")
            print(f"All ports:          {', '.join(str(p) for p in meta['all_ports'])}")
            print()

            # Per-port results with service names when applicable
            for r in results:
                if meta["fail_only"] and r["status"] == "open":
                    continue                
                port = r["port"]
                svc = port_to_service.get(str(port))
                label = f"{svc}({port})" if svc else str(port)
                print(f"{meta['host']}:{label} = {r['status']}")

            if logger and logging_enabled:
                logger.info(log_summary_ports(nagios_state_string(code), "verbose output", enf))
                logger.info(end_banner())

            os._exit(code)

        # ------------------------------------------------------------
        # Quiet output
        # ------------------------------------------------------------
        case "quiet":
            if logger and logging_enabled:
                logger.info(log_summary_ports(nagios_state_string(code), "quiet output", enf))
                logger.info(end_banner())

            os._exit(code)

        # ------------------------------------------------------------
        # Default Nagios single-line output
        # ------------------------------------------------------------
        case _:
            msg = build_nagios_message(enf, code)
            print(msg)

            if logger and logging_enabled:
                logger.info(log_summary_ports(nagios_state_string(code), msg))
                logger.info(end_banner())

            os._exit(code)
    
def main():
    args, flags, mode = build_parser()
    logger = initialize_logger(args, mode)
    meta = build_metadata(args, mode)
    resolve_all_ports(args, meta, logger)
    results, port_to_service = run_port_checks(args, meta, logger)
    enf = build_enforcement_object(meta, results, port_to_service)
    # ------------------------------------------------------------
    # Compute Nagios exit code
    # ------------------------------------------------------------
    code = compute_nagios_code(enf, args)
    output_results(mode, args, meta, results, port_to_service, enf, code, logger)

if __name__ == "__main__":
    main()
