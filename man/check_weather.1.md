% CHECK_WEATHER(1) NMS_Tools | Deterministic Weather Monitoring Tool
% Linktech Engineering
% April 2026

# NAME
**check_weather** — deterministic weather condition evaluator with provider registry and alert engine

# SYNOPSIS
**check_weather** [--city <name>] [--provider <id>] [--json] [--verbose]  
**check_weather** [--debug-cache] [--debug-location]  
**check_weather** [--ttl <seconds>] [--ignore-ttl] [--ignore-cache] [--cache-info]

# DESCRIPTION
**check_weather** retrieves and evaluates current and forecast weather conditions
using deterministic JSON schemas and a unified provider architecture. The tool
supports multiple weather providers, cache handling, slicing normalization,
astronomy fields, index calculations, and NWS alert ingestion.

The tool is designed for monitoring systems, automation pipelines, and
operator‑grade diagnostics.

# OPTIONS

## --city <name>
City or location name to resolve.  
Supports Open‑Meteo geocoding and NWS station lookup.

## --provider <id>
Override provider selection.  
Examples: `openmeteo`, `nws`.

## --json
Emit deterministic JSON output.

## --verbose
Emit human‑readable verbose output.

## --debug-cache
Display cache path, age, TTL, and hit/miss status.

## --debug-location
Display resolved coordinates, station ID, and lookup method.

## --ttl <seconds>
Override cache TTL.

## --ignore-ttl
Bypass TTL check and force API fetch.

## --ignore-cache
Skip cache entirely.

## --cache-info
Display cache metadata without fetching.

## --help
Show help text.

# EXIT CODES
**0** — OK  
**1** — WARNING  
**2** — CRITICAL  
**3** — UNKNOWN

# EXAMPLES

## Basic usage

check_weather --city "Wichita, KS"

## JSON output

check_weather --city "Wichita, KS" --json

## Force API fetch

check_weather --city "Wichita, KS" --ignore-cache

## Debug cache

check_weather --debug-cache --city "Wichita, KS"

# SEE ALSO
**check_ports(1)**, **check_cert(1)**, **check_html(1)**,  
**check_interfaces(1)**, **check_ticker(1)**, **nms_tools(7)**

# AUTHOR
Linktech Engineering — https://www.linktechengineering.net/projects/nms-tools/
