# check_ticker — Enforcement Model

**Part of:** NMS_Tools Monitoring Suite  
**Document:** Enforcement Model  
**Author:** Leon McClatchey, Linktech Engineering LLC  
**License:** MIT  
**Requires:** Python 3.12+  (development only; not required for frozen binary)
**Last Updated:** 2026‑09-04

## Table of Contents
1. [Overview](#1-overview)
2. [Deterministic Behavior Guarantees](#2-deterministic-behavior-guarantees)
3. [Trend Enforcement](#3-trend-enforcement)
4. [Provider Enforcement](#4-provider-enforcement)
5. [History Enforcement](#5-history-enforcement)
6. [Exit Code Mapping](#6-exit-code-mapping)
7. [Failure Modes](#7-failure-modes)
8. [Examples](#8-examples)
9. [Documents](#9-documents)

---

## 1. Overview

`check_ticker` enforces deterministic behavior across market data retrieval, historical analysis, and trend evaluation.
The enforcement model ensures:
* consistent exit codes
* predictable trend direction evaluation
* deterministic provider selection
* stable JSON/YAML output fields
* reproducible behavior across environments (source or frozen binary)

The enforcement engine is intentionally strict. Any deviation in provider behavior, symbol normalization, or trend computation results in deterministic failure modes.

---

## 2. Deterministic Behavior Guarantees

`check_ticker` guarantees the following:

### 2.1 Deterministic Provider Routing

Provider selection is based on:
* asset type
* provider capability
* provider priority
* availability

The same symbol always resolves to the same provider unless the provider is unavailable.

### 2.2 Deterministic Trend Output

Trend direction, slope, volatility, strength, and reversal detection are computed using fixed algorithms with no randomness.

### 2.3 Deterministic History Retrieval

Historical closing prices are normalized to:
* consistent date ordering
* consistent precision
* consistent JSON/YAML structure

### 2.4 Deterministic Exit Codes

Exit codes never vary based on output mode or logging mode.

### 2.5 Deterministic Failure Behavior

Any provider error, normalization error, or trend mismatch produces a predictable exit code and message.

---

## 3. Trend Enforcement

Trend enforcement is controlled by:
* `--require-up`
* `--require-flat`
* `--require-down`

### 3.1 Upward Trend Enforcement

If `--require-up` is set:
* Trend direction must be **UP**
* Otherwise → **CRITICAL (exit 2)**

### 3.2 Flat Trend Enforcement

If `--require-flat` is set:
* Trend direction must be **FLAT**
* Otherwise → **WARNING (exit 1)**

### 3.3 Downward Trend Enforcement

If `--require-down` is set:
* Trend direction must be **DOWN**
* Otherwise → **CRITICAL (exit 2)**

### 3.4 Multi‑Window Trend Enforcement

If `--trend-windows` is enabled:
* Short, medium, and long windows must all be computed
* Enforcement applies to the **primary window** (short)
* Secondary windows are informational unless a provider error occurs

### 3.5 Volatility / Strength / Reversal Enforcement

If these flags are enabled:
* Volatility must be computable
* Strength must be computable
* Reversal detection must complete
* Any failure → CRITICAL (exit 1)

---

## 4. Provider Enforcement

Provider enforcement ensures that:

### 4.1 Provider Must Support Requested Features

If the provider cannot supply:
* history
* OHLC
* trend windows
* volatility
* strength

Then:
* The provider is rejected
* Fallback provider is attempted
* If no provider supports the requested feature → **CRITICAL (exit 1)**

### 4.2 Provider Payload Must Be Valid

Raw provider payload must:
* parse correctly
* contain required fields
* match expected schema
* Invalid payload → **CRITICAL (exit 1)**

### 4.3 API Key Enforcement

If API keys are required:
* `--apikey-file` must exist
* Vault password must decrypt vault file
* Provider keys must be present
* Missing or invalid keys → **CRITICAL (exit 1)**

---

## 5. History Enforcement

History enforcement applies when:
* `--history N` is used
* trend analysis requires historical data
* volatility or strength require history

### 5.1 Minimum History Requirements

If N days of history cannot be retrieved:
* provider fallback is attempted
* if no provider can supply history → **CRITICAL (exit 1)**

### 5.2 History Ordering

History must be:
* chronological
* normalized
* complete

Missing or unordered history → **CRITICAL (exit 1)**

### 5.3 Precision Enforcement

Closing prices must be:
* numeric
* non-null
* normalized to full precision

Invalid precision → **CRITICAL (exit 1)**

---

## 6. Exit Code Mapping
| Exit Code | Meaning |
| --- | --- |
| **0** | Success |
| **1** | Provider error, history error, or trend computation failure |
| **2** | Trend requirement not met (``--require-up``, ``--require-down``) |
| **3** | Invalid symbol or unsupported provider |

---

## 7. Failure Modes

### 7.1 Provider Failure
* network error
* invalid payload
* missing fields
**→ exit 1**

### 7.2 Trend Failure
* slope cannot be computed
* volatility cannot be computed
* reversal detection fails
**→ exit 1**

### 7.3 Trend Requirement Failure
* trend direction mismatch
**→ exit 2**

### 7.4 Symbol Normalization Failure
* unknown symbol
* unsupported asset type
**→ exit 3**

### 7.5 Vault / API Key Failure
* vault cannot be decrypted
* missing API keys
**→ exit 1**

---

## 8. Examples

### 8.1 Require Upward Trend
```bash
check_ticker AAPL --trend --require-up
```

### 8.2 Require Downward Trend
```bash
check_ticker BTC --trend --require-down
```

### 8.3 Require Flat Trend
```bash
check_ticker GOLD --trend --require-flat
```

### 8.4 History + Trend Enforcement
```bash
check_ticker ETH --history 10 --trend --require-up -j
```

---

## 9. Documents
* [Metadata_schema.md](Metadata_schema.md)
* [Operation.md](Operation.md)
* [Usage.md](Usage.md)
* [Installation.md](Installation.md)
* [FLAGS.md](../../../docs/FLAGS.md)
