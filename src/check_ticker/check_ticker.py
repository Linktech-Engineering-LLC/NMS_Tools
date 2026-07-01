#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Leon McClatchey, Linktech Engineering LLC
"""
File: check_ticker.py
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-06-17
Modified: 2026-06-17
Required: Python 3.8+
Part of: NMS_Tools Monitoring Suite
License: MIT (see LICENSE for details)
Description:
            Command‑line interface for querying market data and producing Nagios‑compatible
            output, verbose diagnostic output, or structured JSON. Integrates with
            MarketObjectEngine to retrieve provider data, compute trend and history
            information, and emit logs containing full provider payloads. Designed for use
            in monitoring environments and automated dashboards.
"""

import os
import sys
import yaml
from pathlib import Path

from PythonTools.ansible.vault import VaultLoader, VaultError
from PythonTools.finance.api_keys import resolve_api_key, ApiKeyError, resolve_apikey_file
from PythonTools.log_helpers.factory import LoggerFactory
from PythonTools.market.router import MarketObjectEngine
from PythonTools.market.trend import (
    compute_trend_and_slope,
    compute_volatility,
    compute_trend_strength,
    detect_reversal,
    compute_multi_window_trend
)
from PythonTools.nagios import (
    OK,
    WARNING,
    CRITICAL,
    UNKNOWN,
    nagios_summary,
    start_banner,
    end_banner,
)
from PythonTools.nagios.helpers import should_output
from PythonTools.nagios.parser import BaseNagiosParser
from PythonTools.utils.common import normalize_path, json_output

# -------------------------------------------------------------------
# Suite metadata
# -------------------------------------------------------------------
SUITE_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_NAME = Path(sys.argv[0]).stem
SCRIPT_VERSION = "1.0.0"

def load_version() -> str:
    version_file = SUITE_ROOT.parent / "VERSION"
    try:
        return version_file.read_text(encoding="utf-8").strip()
    except Exception:
        return "External to NMS_TOOLS Suite"

VERSION = load_version()

# -------------------------------------------------------------------
# Argument parser
# -------------------------------------------------------------------
def build_parser() -> BaseNagiosParser:
    parser = BaseNagiosParser(
        prog=SCRIPT_NAME,
        description=(
            "Checks history, prices, and trends on Market Objects. "
            "Supports verbose, JSON, quiet, and Nagios-compatible output."
        ),
        script_version=SCRIPT_VERSION,
        suite_version=VERSION,
    )

    parser.add_argument(
        "ticker",
        help="Ticker symbol (e.g., AAPL, BTC, GOLD, US10Y)",
    )

    core = parser.add_group("Core Options")
    core.add_argument("--history", type=int, metavar="DAYS", help="Fetch N days of historical data")
    core.add_argument("--trend", action="store_true", help="Enable trend analysis (direction + slope)")
    core.add_argument("--trend-volatility", action="store_true",help="Include volatility (standard deviation of history)")
    core.add_argument("--trend-strength", action="store_true", help="Include trend strength (slope normalized by volatility)")
    core.add_argument("--trend-reversal", action="store_true", help="Detect mid‑window trend reversals")
    core.add_argument("--trend-windows", action="store_true", help="Compute short/medium/long window trends")

    filt = parser.add_group("Nagios Behavior Filters")
    filt.add_argument("--require-up", action="store_true", help="Require upward trend → CRITICAL if not")
    filt.add_argument("--require-flat", action="store_true", help="Require flat trend → WARNING if not")
    filt.add_argument("--require-down", action="store_true", help="Require downward trend → CRITICAL if not")

    vault = parser.add_group("Vault Options")
    vault.add_argument("--vault-path", dest="vault_path", help="Path to vault file")
    vault.add_argument("--vault-password-file", dest="vault_password_file", help="Path to vault password file")

    apikeys = parser.add_group("API Key Options")
    apikeys.add_argument("--apikey-file", dest="apikey_file", help="YAML file containing provider API keys")
    apikeys.add_argument("--coingecko-key", dest="coingecko_key", help="Override Coingecko key")
    apikeys.add_argument("--finnhub-key", dest="finnhub_key", help="Override Finnhub key")

    return parser

# -------------------------------------------------------------------
# API key resolution
# -------------------------------------------------------------------
def get_apikeys(args) -> dict:
    vault_path = normalize_path(args.vault_path or os.getenv("CT_VAULT_PATH"))
    vault_password_file = normalize_path(args.vault_password_file or os.getenv("CT_VAULT_PASSWORD_FILE"))
    apikey_file = normalize_path(args.apikey_file or os.getenv("CT_APIKEY_FILE"))

    cli_keys = {
        "coingecko": args.coingecko_key,
        "finnhub": args.finnhub_key,
    }

    # Vault
    if vault_path and vault_password_file:
        try:
            loader = VaultLoader(
                vault_file=vault_path,
                password_source=vault_password_file,
                program_name="check_ticker",
            )
            vault_data = loader.decrypt_yaml()
        except VaultError as exc:
            raise ApiKeyError(f"Vault error: {exc}") from exc
    else:
        vault_data = None

    # Config file
    if apikey_file:
        apikey_file = resolve_apikey_file(apikey_file, SCRIPT_NAME)
        try:
            with open(apikey_file, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f) or {}
        except Exception as exc:
            raise ApiKeyError(f"Failed to load API key file: {exc}") from exc
    else:
        config_data = None

    resolved = {}
    required = ("coingecko", "finnhub")

    for provider in required:
        key = resolve_api_key(provider, cli_keys, vault_data, config_data)
        if key is None:
            raise ApiKeyError(f"Missing API key for provider '{provider}'")
        resolved[provider] = key

    return resolved

# -------------------------------------------------------------------
# Logger
# -------------------------------------------------------------------
def initialize_logger(args, mode):
    if mode == "nagios" or not args.log_dir:
        return None

    try:
        os.makedirs(args.log_dir, exist_ok=True)
        log_cfg = {
            "path": os.path.join(args.log_dir, "check_ticker.log"),
            "log_level": "INFO",
            "log_max_mb": args.log_max_mb,
            "archive_mode": "zip",
            "backup_count": 7,
            "console_stream": sys.stderr,
            "console_enabled": not args.quiet,
            "color": False if mode == "nagios" else args.color,
        }
        logger_factory = LoggerFactory(log_cfg, "check_ticker")
        return logger_factory.get_logger("main")
    except Exception as e:
        if should_output(mode):
            print(nagios_summary(UNKNOWN, f"Failed to initialize LoggerFactory: {e}"))
        return None

# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------
def main() -> int:
    parser = build_parser()
    args, flags, mode = parser.parse()

    # Resolve API keys
    try:
        api_keys = get_apikeys(args)
    except ApiKeyError as exc:
        if should_output(mode):
            print(nagios_summary(UNKNOWN, str(exc)))
        return UNKNOWN

    ticker = args.ticker.upper()
    logger = initialize_logger(args, mode)

    meta = {
        "ticker": ticker,
        "mode": mode,
        "history_days": args.history,
        "trend": args.trend,
        "require_up": args.require_up,
        "require_flat": args.require_flat,
        "require_down": args.require_down,
    }

    if logger:
        logger.info(start_banner("check_ticker", meta))

    # Query market engine
    engine = MarketObjectEngine(api_keys)
    result = engine.get_quote(ticker)

    if result.is_error():
        msg = result.error
        if logger:
            logger.error(msg)
            logger.info(end_banner("check_ticker", "UNKNOWN"))
        if should_output(mode):
            print(nagios_summary(UNKNOWN, msg))
        return UNKNOWN

    # Full-precision payload
    payload = {
        "ticker": ticker,
        "provider": result.provider,
        "timestamp": result.timestamp,
        "price": result.price,
        "pct": result.pct * 100,
        "history": result.history,     # <-- ADD THIS
        "raw": result.raw,
    }
    payload.update(result.trend_result.to_json())
    # Rounded values for human/Nagios output
    rounded_price = round(payload["price"], 3)
    rounded_pct = round(payload["pct"], 2)

    # Perfdata (rounded)
    perfdata = f"price={rounded_price:.3f} pct={rounded_pct:.2f}"
    nagios_msg = f"{ticker} ${rounded_price:.3f} ({rounded_pct:+.2f}%)"
    state = OK
  
    # --- Trend Analysis ---
    tr = result.trend_result
    if args.trend:
        tr.trend, tr.slope = compute_trend_and_slope(result.history)
        nagios_msg += f" trend={tr.trend} slope={tr.slope:.3f}"
        if args.require_up and tr.slope != "up":
            state = CRITICAL
        if args.require_flat and tr.slope != "flat":
            state = WARNING
        if args.require_down and tr.slope != "down":
            state = CRITICAL

    if args.trend_volatility:
        tr.volatility = compute_volatility(result.history)
        nagios_msg += f" vol={tr.volatility:.3f}"
        
    if args.trend_strength:
        tr.strength = compute_trend_strength(result.history)
        nagios_msg += f" strength={tr.strength:.3f}"
        
    if args.trend_reversal:
        tr.reversal = detect_reversal(result.history)
        nagios_msg += f" reversal={tr.reversal}"
        
    if args.trend_windows:
        tr.windows = compute_multi_window_trend(result.history)

    # JSON mode → full precision
    if args.json and should_output(mode):
        print(json_output(payload, args.color))

    # Verbose mode → full precision
    if args.verbose and should_output(mode):
        print("--- VERBOSE MODE ---")
        print(yaml.safe_dump(payload, sort_keys=False))

    # Nagios output
    if mode == "nagios" and should_output(mode):
        print(nagios_summary(state, nagios_msg))

    if logger:
        logger.info(
            f"[TICKER] ticker={ticker} price={payload['price']} "
            f"pct={payload['pct']:.6f} trend={result.trend_result.trend}"
        )

        # NEW: log full raw provider payload
        try:
            import json
            raw_json = json.dumps(payload["raw"], indent=2, sort_keys=True)
            logger.info(f"[RAW] provider={payload['provider']} data=\n{raw_json}")
        except Exception as exc:
            logger.error(f"[RAW] failed to serialize raw provider data: {exc}")
        logger.info(end_banner("check_ticker", state))

    return state


if __name__ == "__main__":
    raise SystemExit(main())
