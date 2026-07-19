#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Leon McClatchey, Linktech Engineering LLC
"""
File: check_ports.py
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-04-20
Modified: 2026-05-06
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
# -----------------------------
# CLI Parser
# -----------------------------
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
def build_enforcement_object(args, service_ports, explicit_ports, ports, results):
    services_requested = args.service.split(",") if args.service else []

    # service → port
    service_map = {
        svc: port
        for svc, port in zip(services_requested, service_ports)
    }

    # port → service (string keys for JSON)
    port_to_service = {
        str(port): svc
        for svc, port in zip(services_requested, service_ports)
    }

    # Helper for labeling service ports
    def svc_label(port):
        return f"{port_to_service[str(port)]}({port})" if str(port) in port_to_service else str(port)

    # Grouped buckets
    open_ports = [r["port"] for r in results if r["status"] == "open"]
    closed_ports = [r["port"] for r in results if r["status"] == "closed"]
    timeout_ports = [r["port"] for r in results if r["status"] == "timeout"]
    unreachable_ports = [r["port"] for r in results if r["status"] == "unreachable"]

    service_open = sorted([svc_label(p) for p in service_ports if p in open_ports])
    service_closed = sorted([svc_label(p) for p in service_ports if p in closed_ports])

    explicit_open = sorted([str(p) for p in explicit_ports if p in open_ports])
    explicit_closed = sorted([str(p) for p in explicit_ports if p in closed_ports])

    # status_by_port
    status_by_port = {str(r["port"]): r["status"] for r in results}

    # status_by_service
    status_by_service = {
        svc: status_by_port.get(str(port), "unknown")
        for svc, port in service_map.items()
    }

    return {
        "host": args.host,

        "services_requested": services_requested,
        "service_ports": service_ports,
        "explicit_ports": explicit_ports,
        "all_ports": ports,

        "service_map": service_map,
        "port_to_service": port_to_service,

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
    
def main():
    args, flags, mode = build_parser()
    logger = initialize_logger(args, mode)
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
        if logger and logging_enabled:
            logger.info(meta, start_banner_ports(meta))

    except CheckArgError as e:
        msg = f"UNKNOWN - {e}"
        if logger and logging_enabled:
            # No START banner was written → write a minimal START
            logger.info(meta, f"[START] {SCRIPT_NAME}.py host={meta['host']} cmd=\"{meta['command']}\"")
            logger.info(meta, log_summary_ports("UNKNOWN", msg))
            logger.info(meta, end_banner())
        print(msg)
        os._exit(3)

    # ------------------------------------------------------------
    # Execute connection tests
    # ------------------------------------------------------------
    results = []
    for port in ports:
        status = check_port(args.host, port, args.timeout)
        results.append({"port": port, "status": status})

        services_requested = args.service.split(",") if args.service else []
        service_map = dict(zip(services_requested, service_ports))
        port_to_service = {str(port): svc for svc, port in service_map.items()}

        if logger and logging_enabled:
            # Determine service-aware label
            svc = port_to_service.get(str(port))
            label = f"{svc}({port})" if svc else port
            logger.info(meta, log_port_result(args.host, label, status))

    enf = build_enforcement_object(
        args,
        service_ports,
        explicit_ports,
        ports,
        results
    )
    # ------------------------------------------------------------
    # Compute Nagios exit code
    # ------------------------------------------------------------
    code = compute_nagios_code(enf, args)

    # ------------------------------------------------------------
    # Output modes
    # ------------------------------------------------------------
    if args.json:
        print(json.dumps(enf, indent=2))
        if logger and logging_enabled:
            logger.info(meta, log_summary_ports(nagios_state_string(code), "json output", enf))
            logger.info(meta, end_banner())
        os._exit(code)

    if args.verbose:
        print(f"Host: {args.host}")
        print(f"Services requested: {', '.join(args.service.split(',')) if args.service else 'None'}")

        # Show service ports with service names
        if service_ports:
            svc_labels = [
                f"{svc}({port})"
                for svc, port in zip(args.service.split(","), service_ports)
            ]
            print(f"Service ports:      {', '.join(svc_labels)}")
        else:
            print("Service ports:      None")

        print(f"Explicit ports:     {', '.join(str(p) for p in explicit_ports) if explicit_ports else 'None'}")
        print(f"All ports:          {', '.join(str(p) for p in ports)}")
        print()

        # Per-port results with service names when applicable
        for r in results:
            port = r["port"]
            svc = enf["port_to_service"].get(str(port))
            label = f"{svc}({port})" if svc else str(port)
            print(f"{args.host}:{label} = {r['status']}")

        if logger and logging_enabled:
            logger.info(meta, log_summary_ports(nagios_state_string(code), "verbose output", enf))
            logger.info(meta, end_banner())
        os._exit(code)

    if args.quiet:
        if logger and logging_enabled:
            logger.info(meta, log_summary_ports(nagios_state_string(code), "quiet output", enf))
            logger.info(meta, end_banner())
        os._exit(code)

    # ------------------------------------------------------------
    # Default Nagios single-line output
    # ------------------------------------------------------------
    msg = build_nagios_message(enf, code)
    print(msg)

    if logger and logging_enabled:
        logger.info(meta, log_summary_ports(nagios_state_string(code), msg))
        logger.info(meta, end_banner())

    os._exit(code)

if __name__ == "__main__":
    main()
