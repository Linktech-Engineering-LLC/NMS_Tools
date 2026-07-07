# check_ticker

`check_ticker` is a command‑line market data tool used to retrieve price, history, and trend information for equities and cryptocurrencies. It is part of the NMS_Tools suite and uses the unified provider architecture from PythonTools.

## Features

- Unified market data providers (Yahoo, Finnhub, Coingecko, AlphaVantage)
- Full‑precision JSON output for automation
- Verbose YAML output for inspection and debugging
- Nagios‑style single‑line status output (default)
- Quiet mode for monitoring systems that only need exit codes
- Trend analysis (short/medium/long windows)
- Raw provider payload logging for diagnostics

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

`check_ticker` uses the provider registry from PythonTools:

* `finance.providers.yahoo_provider`
* `finance.providers.coingecko_provider`
* `finance.providers.finnhub_provider`
* `finance.providers.alphavantage_provider`

The registry selects the appropriate provider based on symbol type.

## Raw Payload

Raw provider data is logged (not printed) to assist with debugging and trend analysis.

## Runtime Requirements and Frozen Mode

`check_ticker.py` is fully operational and ready for use in development environments.
However, it currently **depends on the PythonTools package** for:

* unified market data providers
* symbol normalization
* trend analysis
* shared market object models

### Runtime Requirement

To run check_ticker.py directly from source, you must have:

```Code
PythonTools (main branch)
```

installed or available in your environment.

### Frozen Mode (Standalone Executable)

Although `check_ticker.py` supports frozen operation via PyInstaller,
**frozen mode is not yet enabled.** It will be activated only after:

* the remaining NMS_Tools modules are migrated to PythonTools
* the provider registry is fully stable
* the shared market object model is finalized

This ensures the frozen build contains the correct provider architecture and avoids breaking changes during the migration phase.

### Current Status

* ✔ Ready for use in development
* ✔ Fully compatible with PythonTools
* ✔ Output modes finalized (JSON, verbose, quiet, Nagios)
* ✔ Logging architecture stable
* ✖ Frozen mode disabled until migration is complete