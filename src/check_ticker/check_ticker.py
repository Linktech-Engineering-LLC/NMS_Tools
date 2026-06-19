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
    Nagios-compatible check for market tickers.
    Uses PythonTools.market.MarketObjectEngine to retrieve price, percent
    change, and trend for a given ticker symbol.
"""

import os
import sys
import yaml
from pathlib import Path
from typing import Optional

from PythonTools.ansible.vault import VaultLoader, VaultError
from PythonTools.finance.api_keys import resolve_api_key, ApiKeyError, resolve_apikey_file
from PythonTools.log_helpers.factory import LoggerFactory
from PythonTools.market.router import MarketObjectEngine
from PythonTools.nagios import (
    OK,
    WARNING,
    CRITICAL,
    UNKNOWN,
    nagios_summary,
    start_banner,
    end_banner,
    Flags,
    FlagNames,
    detect_mode,
)
from PythonTools.nagios.helpers import should_output
from PythonTools.nagios.parser import BaseNagiosParser
from PythonTools.utils.common import normalize_path

# -------------------------------------------------------------------
# Suite metadata
# -------------------------------------------------------------------
SUITE_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_NAME = Path(sys.argv[0]).stem
SCRIPT_VERSION = "1.0.0"
def load_version() -> str:
    """
    Load the suite VERSION file if present.
    If missing, return a fallback string indicating external execution.
    """
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
            "Market Objects include Stocks, Bonds, Crypto, and Commodities. "
            "Supports verbose, JSON, and Nagios-compatible output."
        ),
        script_version = SCRIPT_VERSION,
        suite_version = VERSION
    )

    # Core options
    parser.add_argument(
        "ticker",
        help="Ticker symbol (e.g., AAPL, BTC, GOLD, US10Y)",
    )

    core = parser.add_group("Core Options")
    core.add_argument(
        "--history",
        type=int,
        metavar="DAYS",
        help="Fetch N days of historical data (if supported by provider)",
    )
    core.add_argument(
        "--trend",
        action="store_true",
        help="Perform trend analysis on historical data (if supported)",
    )

    # Nagios behavior filters (reserved for future logic)
    filt = parser.add_group("Nagios Behavior Filters")
    filt.add_argument(
        "--require-up",
        action="store_true",
        help="Require the ticker to be trending upward; otherwise return CRITICAL.",
    )
    filt.add_argument(
        "--require-flat",
        action="store_true",
        help="Require the ticker to be stable/flat; otherwise return WARNING.",
    )
    filt.add_argument(
        "--require-down",
        action="store_true",
        help="Require the ticker to be trending downward; otherwise return CRITICAL.",
    )
    # --------------------------------------------------------
    # Vault Options
    # --------------------------------------------------------
    vault = parser.add_group("Vault Options")

    vault.add_argument(
        "--vault-path",
        dest="vault_path",
        required=False,
        help="Path to vault file containing credentials"
    )

    vault.add_argument(
        "--vault-password-file",
        dest="vault_password_file",
        required=False,
        help="Path to file containing vault password"
    )
    # --------------------------------------------------------
    # API Key Options
    # --------------------------------------------------------
    apikeys = parser.add_group("API Key Options")

    # Unified YAML file containing all provider keys
    apikeys.add_argument(
        "--apikey-file",
        dest="apikey_file",
        required=False,
        help="Path to YAML file containing provider API keys"
    )

    # Individual provider keys (override everything else)
    apikeys.add_argument(
        "--coingecko-key",
        dest="coingecko_key",
        required=False,
        help="Coingecko API key (overrides vault/config/env)"
    )

    apikeys.add_argument(
        "--alphavantage-key",
        dest="alphavantage_key",
        required=False,
        help="AlphaVantage API key (overrides vault/config/env)"
    )

    apikeys.add_argument(
        "--finnhub-key",
        dest="finnhub_key",
        required=False,
        help="Finnhub key (overrides vault/config/env)"
    )

    return parser
def get_apikeys(args) -> dict:
    """
    Resolve all provider API keys using the priority chain:
    CLI > Vault > Config > Environment
    Raises ApiKeyError on failure.
    """

    # Normalize paths
    vault_path = normalize_path(args.vault_path or os.getenv("CT_VAULT_PATH"))
    vault_password_file = normalize_path(args.vault_password_file or os.getenv("CT_VAULT_PASSWORD_FILE"))
    apikey_file = normalize_path(args.apikey_file or os.getenv("CT_APIKEY_FILE"))

    # CLI overrides
    cli_keys = {
        "coingecko": args.coingecko_key,
        "alphavantage": args.alphavantage_key,
        "finnhub": args.finnhub_key,
    }

    # Vault (optional)
    if vault_path and vault_password_file:
        try:
            loader = VaultLoader(
                vault_file=vault_path,
                password_source=vault_password_file,
                program_name="check_ticker"
            )
            vault_data = loader.decrypt_yaml()
        except VaultError as exc:
            raise ApiKeyError(f"Vault error: {exc}") from exc
    else:
        vault_data = None

    # Config file (optional)
    if apikey_file:
        apikey_file = resolve_apikey_file(apikey_file, SCRIPT_NAME)
        try:
            with open(apikey_file, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f) or {}
        except Exception as exc:
            raise ApiKeyError(f"Failed to load API key file: {exc}") from exc
    else:
        config_data = None

    # Resolve each provider independently
    resolved = {}
    required_providers = ("coingecko", "alphavantage", "finnhub")

    for provider in required_providers:
        key = resolve_api_key(provider, cli_keys, vault_data, config_data)

        if key is None:
            raise ApiKeyError(f"Missing API key for provider '{provider}'")

        resolved[provider] = key

    return resolved

# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------
def main() -> int:
    parser = build_parser()
    args, flags, mode = parser.parse()
    api_keys = get_apikeys(args)
    ticker = args.ticker.upper()

    # Initialize logger only if not in Nagios mode and log-dir is provided
    logger = None
    if mode != "nagios" and args.log_dir:
        try:
            os.makedirs(args.log_dir, exist_ok=True)

            log_cfg = {
                "path": os.path.join(args.log_dir, "check_ticker.log"),
                "log_level": "INFO",
                "log_max_mb": args.log_max_mb,
                "archive_mode": "zip",
                "backup_count": 7,

                # Quiet mode suppresses console logging
                "console_enabled": not args.quiet,

                # Nagios checks should not use color
                "color": False,
            }

            logger_factory = LoggerFactory(log_cfg, "check_ticker")
            logger = logger_factory.get_logger("main")
            logger.info(f"LoggerFactory initialized (mode={mode})")

        except Exception as e:
            if should_output(mode):
                print(nagios_summary(UNKNOWN, f"Failed to initialize LoggerFactory: {e}"))
            return UNKNOWN

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

    price = result.price
    pct = result.pct * 100
    trend = getattr(result, "trend", "unknown")

    if logger:
        logger.info(
            f"[TICKER] ticker={ticker} price={price} pct={pct:.2f} trend={trend}"
        )

    # TODO: apply require_up/require_flat/require_down once trend semantics are finalized
    state = OK
    message = f"{ticker} ${price:.2f} ({pct:+.2f}%) trend={trend}"

    if should_output(mode):
        print(nagios_summary(state, message))

    if logger:
        logger.info(end_banner("check_ticker", "OK"))

    return state


if __name__ == "__main__":
    raise SystemExit(main())
