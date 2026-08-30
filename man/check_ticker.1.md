% CHECK_TICKER(1) NMS_Tools | Deterministic Ticker Movement Monitoring
% Linktech Engineering
% April 2026

# NAME
**check_ticker** — deterministic ticker ingestion and movement analysis tool

# SYNOPSIS
**check_ticker** --symbol <ticker> [--json] [--verbose] [--quiet]  
**check_ticker** [--debug-ticker] [--timeout <seconds>]

# DESCRIPTION
**check_ticker** retrieves ticker movement data from a backend source and
evaluates deterministic movement thresholds, volatility scoring, and trend
indicators. The tool is designed for dashboards, monitoring systems, and
backend ingestion validation.

Movement calculations are deterministic and consistent across executions.

# OPTIONS

## --symbol <ticker>
Ticker symbol to evaluate.  
Examples: `AAPL`, `MSFT`, `TSLA`.

## --json
Emit deterministic JSON output.

## --verbose
Emit human‑readable verbose output.

## --quiet
Emit minimal Nagios‑style output.

## --debug-ticker
Display backend fetch lifecycle, timing, and normalization details.

## --timeout <seconds>
Set execution timeout.

## --help
Show help text.

# EXIT CODES
**0** — OK  
**1** — WARNING  
**2** — CRITICAL  
**3** — UNKNOWN

# EXAMPLES

## Basic usage

check_ticker --symbol AAPL

## JSON output

check_ticker --symbol AAPL --json

## Debug backend

check_ticker --symbol AAPL --debug-ticker

# SEE ALSO
**check_ports(1)**, **check_weather(1)**, **check_cert(1)**,  
**check_html(1)**, **check_interfaces(1)**, **nms_tools(7)**

# AUTHOR
Linktech Engineering — https://www.linktechengineering.net/projects/nms-tools/
