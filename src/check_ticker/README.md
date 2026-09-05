# check_ticker
Deterministic market/ticker inspection tool for equities, crypto, commodities, and indices.

**Part of:** NMS_Tools Monitoring Suite  
**Script:** `check_ticker.py`  
**Author:** Leon McClatchey, Linktech Engineering LLC  
**License:** MIT  
**Requires:** Python 3.12+  (development only; not required for frozen binary)
**Last Updated:** 2026‑09‑04

## Table of Contents
1. [Overview](#1-overview)
2. [Features](#2-features)
3. [Usage](#3-usage)
4. [Output Modes](#4-output-modes)
5. [Logging](#5-logging)
6. [Options](#6-options)
    1. [6.1 Output Modes](#61-output-modes)
    2. [6.2 Logging Options](#62-logging-options)
    3. [6.3 Core Options](#63-core-options)
    4. [6.4 Trend Options](#64-trend-options)
    5. [6.5 Nagios Behavior Filters](#65-nagios-behavior-filters)
    6. [6.6 Vault Options](#66-vault-options)
    7. [6.7 API Key Options](#67-api-key-options)
7. [Exit Codes](#7-exit-codes)
8. [Provider Architecture](#8-provider-architecture)
9. [Raw Payload](#9-raw-payload)
10. [Runtime Requirements](#10-runtime-requirements)
    1. [10.1 Running from Source ](#101-running-from-source) 
    2. [10.2 Frozen Mode Standalone Executable](#102-frozen-mode-standalone-executable)
11. [Current Status](#11-current-status)
12. [Documents](#12-documents)
13. [Tools in this Suite](#13-tools-in-this-suite)
14. [License](#14-license)

## 1. Overview

`check_ticker` is part of the **NMS_Tools** suite and uses the unified, deterministic market provider architecture from **PythonTools**. It retrieves normalized price data, historical closing prices, and multi‑window trend analysis suitable for monitoring systems, dashboards, and automation pipelines.

## 2. Features

* Unified provider architecture (Yahoo, Finnhub, Coingecko, AlphaVantage)
* Deterministic symbol normalization (equities, crypto, commodities, indices)
* Full‑precision JSON output for automation
* Verbose YAML output for inspection and debugging
* Nagios‑style single‑line status output (default)
* Quiet mode for monitoring systems that only need exit codes
* Trend analysis (short / medium / long windows)
* Raw provider payload logging for diagnostics
* Frozen standalone binary (PyInstaller) for production use

## 3. Usage

```bash
check_ticker.py <symbol> [options]
```

Example:

```bash
check_ticker.py BTC --history 5 --trend -j
```

## 4. Output Modes

Only one output mode is active at a time.

### JSON Mode (`-j`)
Machine‑readable output with full precision.

```bash
check_ticker.py BTC -j
```

### Verbose Mode (`-v`)
Human‑readable YAML dump including history, trend, and raw provider data.

```bash
check_ticker.py BTC -v
```

### Quiet Mode (`--quiet`)
Suppresses all console output. Only the exit code is returned.
File logging still occurs if `--log-dir` is set.

```bash
check_ticker.py BTC --quiet
```

### Nagios Mode (default)
Single‑line status output suitable for monitoring systems.

```bash
check_ticker.py BTC
```

## 5. Logging

Console logging is suppressed unless verbose mode is enabled.
File logging is enabled when `--log-dir` is provided.

Logged fields include:

* START / END banners
* TICKER summary
* RAW provider payload (JSON)

## 6. Options

### 6.1 Output Modes
| Flag | Description |
| --- | --- |
| ``-v``, ``--verbose`` | Verbose YAML output |
| ``-j``, ``--json`` | JSON output mode |
| ``-q``, ``--quiet`` | Quiet mode (exit code only) |
| ``--color`` | Colorize terminal output (verbose/JSON) |
| ``--output ``FILE`` | Write output to FILE instead of stdout |

### 6.2 Logging Options
| Flag | Description |
| --- | --- |
| ``--log-dir ``DIR`` | Directory to store logs |
| ``--log-max-mb ``SIZE`` | Maximum log size before rotation (default: 50 MB) |

### 6.3 Core Options
| Flag | Description |
| --- | --- |
| ``--history ``DAYS`` | Fetch N days of historical closing prices |
| ``--trend`` | Enable trend analysis (direction + slope) |

### 6.4 Trend Options
| Flag | Description |
| --- | --- |
| ``--trend-volatility`` | Include volatility (standard deviation of history) |
| ``--trend-strength`` | Include trend strength (slope normalized by volatility) |
| ``--trend-reversal`` | Detect mid‑window trend reversals |
| ``--trend-windows`` | Compute short/medium/long window trends |

### 6.5 Nagios Behavior Filters
| Flag | Description |
| --- | --- |
| ``--require-up`` | Require upward trend → CRITICAL if not |
| ``--require-flat`` | Require flat trend → WARNING if not |
| ``--require-down`` | Require downward trend → CRITICAL if not |

### 6.6 Vault Options
| Flag | Description |
| --- | --- |
| ``--vault-path ``PATH`` | Path to vault file |
| ``--vault-password-file ``FILE`` | Path to vault password file |

### 6.7 API Key Options
| Flag | Description |
| --- | --- |
| ``--apikey-file ``FILE`` | YAML file containing provider API keys |
| ``--coingecko-key ``KEY`` | Override Coingecko key |
| ``--finnhub-key ``KEY`` | Override Finnhub key |

#### Internal Flags
Internal bitmask flags used by the enforcement engine (JSON/VERBOSE/QUIET priority, FAIL_ONLY behavior, REQUIRE_ALL/REQUIRE_ANY semantics, etc.) are documented globally:

See: [FLAGS](../../docs/FLAGS.md)


## 7. Exit Codes

| Code | Meaning |
| --- | --- |
| ``0`` | Success |
| ``1`` | Provider error |
| ``2`` | Trend requirement not met |
| ``3`` | Invalid symbol or unsupported provider |

## 8. Provider Architecture

`check_ticker` uses the provider registry from **PythonTools**:

* `finance.providers.yahoo_provider`
* `finance.providers.coingecko_provider`
* `finance.providers.finnhub_provider`
* `finance.providers.alphavantage_provider`

The registry selects the appropriate provider based on:

* asset type (equity, crypto, commodity, index)
* provider capability (history, OHLC, trend compatibility)
* provider priority
* provider availability

Provider selection is deterministic and logged for diagnostics.

## 9. Raw Payload

Raw provider data is logged (not printed) to assist with debugging and trend analysis.

## 10. Runtime Requirements

### 10.1 Running from source

To run `check_ticker.py` directly from source, the following must be installed in the active virtual environment:

```text
PythonTools (main branch)
```

PythonTools provides:
* unified market data providers
* symbol normalization
* trend analysis
* shared market object models
* deterministic logging and exception modeling

### 10.2 Frozen Mode (Standalone Executable)

`check_ticker` **supports frozen operation** via PyInstaller.

Frozen mode is enabled through:

```bash
./scripts/build.py
```

This produces a standalone binary in:

```bash
dist/check_ticker
```

Frozen mode is fully operational and used by:

* NMS_Tools packaging (DEB, RPM, TGZ, ZIP)
* monitoring environments
* automation pipelines
* Nagios/Icinga/Sensu/Zabbix integrations

## 11. Current Status

* ✔ Fully compatible with PythonTools
* ✔ Deterministic provider routing
* ✔ JSON / YAML / Nagios / Quiet modes finalized
* ✔ Logging architecture stable
* ✔ Frozen mode enabled via scripts/build.py
* ✔ Included in NMS_Tools packaging
* ✔ Suitable for production monitoring environments

## 12. Documents

| Document | Description |
|----------|-------------|
| [Installation.md](docs/Installation.md) | Installation and environment setup |
| [Usage.md](docs/Usage.md)        | Full CLI reference and examples |
| [Operation.md](docs/Operation.md)    | Discovery, normalization, and output pipeline |
| [Enforcement.md](docs/Enforcement.md)  | Status evaluation and filtering logic |
| [Metadata_schema.md](docs/Metadata_schema.md) | Normalized interface schema |

## 13. Tools in This Suite

| Tool | Description | Documentation |
|------|-------------|---------------|
| **check_cert** | TLS certificate inspection and expiration validation | [../check_cert/README.md](../check_cert/README.md) |
| **check_html** | HTTP/HTTPS content validation and deterministic HTML checks | [../check_html/README.md](../check_html/README.md) |
| **check_interfaces** | Network interface inspection and operational state reporting | [../check_interfaces/README.md](../check_interfaces/README.md) |
| **check_ports** | Port and service availability inspection | [../check_ports/README.md](../check_ports/README.md) |
| **check_weather** | Deterministic weather client for monitoring pipelines | [../check_weather/README.md](../check_weather/README.md) |
| **check_ticker** | Deterministic market/ticker client using PythonTools finance providers | - |

## 14. License
* Source code: MIT [LICENSE](../../LICENSE) for details.
* Frozen binary: Proprietary [LICENSE_BINARY](../../LICENSE_BINARY.txt)
