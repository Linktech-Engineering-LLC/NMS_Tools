# check_ticker — Usage Guide

**Part of:** NMS_Tools Monitoring Suite  
**Document:** Usage Guide
**Author:** Leon McClatchey, Linktech Engineering LLC  
**License:** MIT  
**Requires:** Python 3.12+  (development only; not required for frozen binary)
**Last Updated:** 2026‑09-04

## Table of Contents
1. [Overview](#1-overview)
2. [Basic Invocation](#2-basic-invocation)
3. [Output Modes](#3-output-modes)
4. [Common Patterns](#4-common-patterns)
5. [Trend Analysis Examples](#5-trend-analysis-examples)
6. [Nagios/Icinga Examples](#6-nagiosicinga-examples)
7. [Logging Examples](#7-logging-examples)
8. [Vault and API Key Examples](#8-vault-and-api-key-examples)
10. [Documents](#9-documents)

---

## 1. Overview

`check_ticker` is a deterministic market inspection tool for equities, crypto, commodities, and indices.
It retrieves:
* normalized market metadata
* historical closing prices
* multi‑window trend analysis
* provider diagnostics
* Nagios‑compatible status output

The tool supports JSON, verbose YAML, quiet mode, and single‑line Nagios output.
It is suitable for monitoring systems, dashboards, and automation pipelines.

---

## 2. Basic Invocation

The simplest invocation checks the latest price and trend direction:
```bash
check_ticker BTC
```

Specify a symbol directly:
```bash
check_ticker AAPL
check_ticker GOLD
check_ticker ETH
```

Include history:
```bash
check_ticker BTC --history 5
```

Enable trend analysis:
```bash
check_ticker AAPL --trend
```

Combine history + trend:
```bash
check_ticker ETH --history 10 --trend
```

---

## 3. Output Modes

Only one output mode is active at a time.

### 3.1 JSON Mode (-j)
Machine‑readable output with full precision.
```bash
check_ticker BTC -j
```

### 3.2 Verbose Mode (-v)
Human‑readable YAML dump including:
* market metadata
* history
* trend analysis
* provider diagnostics
* raw provider payload

```bash
check_ticker AAPL -v
```

### 3.3 Quiet Mode (--quiet)
Suppresses all console output.
Exit code only.

```bash
check_ticker ETH --quiet
```

### 3.4 Nagios Mode (default)
Single‑line status output:

```bash
check_ticker GOLD
```

### 3.5 Colorized Output
Enable ANSI color:

```bash
check_ticker BTC --color
```

### 3.6 Write Output to File
Redirect output to a file:

```bash
check_ticker BTC --output /tmp/ticker.json
```

---

## 4. Common Patterns

### 4.1 Price‑Only Check
```bash
check_ticker AAPL
```

### 4.2 History‑Only Check
```bash
check_ticker BTC --history 7
```

### 4.3 Trend‑Only Check
```bash
check_ticker ETH --trend
```

### 4.4 History + Trend
```bash
check_ticker GOLD --history 14 --trend
```

### 4.5 Multi‑Window Trend
```bash
check_ticker AAPL --trend-windows
```

###4.6 Enforce Trend Direction
```bash
check_ticker BTC --trend --require-up
check_ticker BTC --trend --require-flat
check_ticker BTC --trend --require-down
```

### 4.7 JSON for Automation
```bash
check_ticker ETH --history 5 --trend -j
```

### 4.8 Verbose Diagnostics
```bash
check_ticker AAPL -v --trend-windows
```

---

## 5. Trend Analysis Examples

### 5.1 Upward Trend
```bash
check_ticker AAPL --trend --require-up
```

### 5.2 Downward Trend
```bash
check_ticker BTC --trend --require-down
```

### 5.3 Flat Trend
```bash
check_ticker GOLD --trend --require-flat
```

### 5.4 Multi‑Window Trend
```bash
check_ticker ETH --trend-windows -v
```

### 5.5 Volatility + Strength
```bash
check_ticker BTC --trend --trend-volatility --trend-strength
```

### 5.6 Reversal Detection
```bash
check_ticker AAPL --trend --trend-reversal
```

---

## 6. Nagios/Icinga Examples

### 6.1 Basic Nagios Output
```bash
check_ticker BTC
```

### 6.2 Critical on Downward Trend
```bash
check_ticker AAPL --trend --require-up
```

### 6.3 Warning on Flat Trend
```bash
check_ticker GOLD --trend --require-flat
```

### 6.4 JSON for NRDP / NSCA
```bash
check_ticker ETH -j
```

### 6.5 Quiet Mode for Exit‑Code‑Only Checks
```bash
check_ticker BTC --quiet
```

---

## 7. Logging Examples

### 7.1 Enable File Logging
```bash
check_ticker BTC --log-dir /var/log/check_ticker
```

### 7.2 Enable Log Rotation
```bash
check_ticker AAPL --log-dir /var/log/check_ticker --log-max-mb 25
```

### 7.3 Verbose Console Logging
```bash
check_ticker ETH -v
```

### 7.4 Verbose + File Logging
```bash
check_ticker GOLD -v --log-dir /var/log/check_ticker
```

---

## 8. Vault and API Key Examples

### 8.1 Use Vault File
```bash
check_ticker BTC --vault-path /etc/keys/vault.yaml --vault-password-file /etc/keys/vault.pass
```

### 8.2 Use API Key File
```bash
check_ticker AAPL --apikey-file /etc/keys/providers.yaml
```

### 8.3 Override Coingecko Key
```bash
check_ticker ETH --coingecko-key $CG_KEY
```

### 8.4 Override Finnhub Key
```bash
check_ticker AAPL --finnhub-key $FINNHUB_KEY
```

---

## 9. Documents
* [Installation.md](Installation.md)
* [FLAGS.md](../../../docs/FLAGS.md)
* [Enforcement.md](Enforcement.md)
* [Metadata_schema.md](Metadata_schema.md)
* [Operation.md](Operation.md)