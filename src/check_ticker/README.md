# check_ticker

Deterministic market/ticker inspection tool for equities, crypto, commodities, and indices.

`check_ticker` is part of the **NMS_Tools** suite and uses the unified, deterministic market provider architecture from **PythonTools**. It retrieves normalized price data, historical closing prices, and multi‑window trend analysis suitable for monitoring systems, dashboards, and automation pipelines.

## Features

* Unified provider architecture (Yahoo, Finnhub, Coingecko, AlphaVantage)
* Deterministic symbol normalization (equities, crypto, commodities, indices)
* Full‑precision JSON output for automation
* Verbose YAML output for inspection and debugging
* Nagios‑style single‑line status output (default)
* Quiet mode for monitoring systems that only need exit codes
* Trend analysis (short / medium / long windows)
* Raw provider payload logging for diagnostics
* Frozen standalone binary (PyInstaller) for production use

## Usage

```bash
check_ticker.py <symbol> [options]
```

Example:

```bash
check_ticker.py BTC --history 5 --trend -j
```

## Output Modes

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

## Logging

Console logging is suppressed unless verbose mode is enabled.
File logging is enabled when `--log-dir` is provided.

Logged fields include:

* START / END banners
* TICKER summary
* RAW provider payload (JSON)

## Options

| Option | Description |
| --- | --- |
| ``--history N`` | Include N days of historical closing prices |
| ``--trend`` | Compute trend analysis |
| ``--require-up`` / ``--require-flat`` / ``--require-down`` | Enforce trend direction |
| ``--json``, ``-j`` | JSON output mode |
| ``--verbose``, ``-v`` | Verbose YAML output |
| ``--quiet`` | Suppress console output |
| ``--log-dir DIR`` | Write logs to DIR |

## Exit Codes

| Code | Meaning |
| --- | --- |
| ``0`` | Success |
| ``1`` | Provider error |
| ``2`` | Trend requirement not met |
| ``3`` | Invalid symbol or unsupported provider |

## Provider Architecture

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

## Raw Payload

Raw provider data is logged (not printed) to assist with debugging and trend analysis.

## Runtime Requirements

### Running from source

To run check_ticker.py directly from source, the following must be installed in the active virtual environment:

```text
PythonTools (main branch)
```

PythonTools provides:
* unified market data providers
* symbol normalization
* trend analysis
* shared market object models
* deterministic logging and exception modeling

### Frozen Mode (Standalone Executable)

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

## Current Status

* ✔ Fully compatible with PythonTools
* ✔ Deterministic provider routing
* ✔ JSON / YAML / Nagios / Quiet modes finalized
* ✔ Logging architecture stable
* ✔ Frozen mode enabled via scripts/build.py
* ✔ Included in NMS_Tools packaging
* ✔ Suitable for production monitoring environments