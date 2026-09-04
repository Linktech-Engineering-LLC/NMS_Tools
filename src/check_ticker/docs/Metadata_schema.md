# check_ticker — Metadata Schema

**Part of:** NMS_Tools Monitoring Suite  
**Document:** Metadata Schema  
**Author:** Leon McClatchey, Linktech Engineering LLC  
**License:** MIT  
**Requires:** Python 3.12+  (development only; not required for frozen binary)
**Last Updated:** 2026‑09-04

## Table of Contents
1. [Overview](#1-overview)
2. [Market Object Schema](#2-market-object-schema)
3. [History Schema](#3-history-schema)
4. [Trend Schema](#4-trend-schema)
5. [Provider Metadata](#5-provider-metadata)
6. [Error Schema](#6-error-schema)
7. [Examples](#7-examples)
8. [Documents](#8-documents)

---

## 1. Overview
`check_ticker` produces deterministic metadata describing:
* the resolved market object
* normalized symbol information
* historical closing prices
* multi‑window trend analysis
* provider selection and diagnostics
* error conditions and failure metadata

All metadata is emitted in **JSON mode** (`-j`/`--json`) and included in verbose **YAML mode** (`-v`/'--verbose`).
Nagios mode emits only a single‑line summary, but the underlying metadata is still generated internally.

The schema defined in this document is stable across:
* source execution
* frozen binary execution
* all supported providers
* all supported asset types (equities, crypto, commodities, indices)

---

## 2. Market Object Schema

The Market Object represents the normalized ticker and its resolved provider.

### 2.1 Fields
| Field | Type | Description |
| --- | --- | --- |
| ``symbol`` | string | User‑provided ticker symbol (e.g., ``AAPL``, ``BTC``, ``GOLD``) |
| ``normalized_symbol`` | string | Deterministically normalized symbol used internally |
| ``asset_type`` | string | One of: ``equity``, ``crypto``, ``commodity``, ``index`` |
| ``provider`` | string | Selected provider (e.g., ``yahoo``, ``coingecko``, ``finnhub``, ``alphavantage``) |
| ``price`` | float | Latest resolved price (full precision) |
| ``timestamp`` | string (ISO‑8601) | Provider timestamp for the resolved price |
| ``currency`` | string | Currency code (e.g., ``USD``) |
| ``market_status`` | string | ``open``, ``closed``, or ``unknown`` |

### 2.2 Deterministic Rules
* `normalized_symbol` is always lowercase and provider‑compatible.
* `asset_type` is derived deterministically from symbol classification.
* `provider` is selected using the provider routing rules in Operation.md.
* `price` is always full‑precision (no rounding).
* `timestamp` is always normalized to ISO‑8601.

---

## 3. History Schema

Historical closing prices are included when:
* `--history N` is used
* trend analysis requires history
* volatility or strength require history

### 3.1 Fields
| Field | Type | Description |
| --- | --- | --- |
| ``history`` | array | Chronological list of historical entries |
| ``history[].date`` | string (YYYY‑MM‑DD) | Trading date |
| ``history[].close`` | float | Closing price (full precision) |
| ``history[].provider_timestamp`` | string (ISO‑8601) | Raw provider timestamp for the historical entry |

### 3.2 Deterministic Rules
* History is always sorted oldest → newest.
* All dates are normalized to `YYYY‑MM‑DD`.
* All closing prices retain full precision.
* Missing or malformed entries are never included.
* Provider fallback is attempted if history is incomplete.

---

## 4. Trend Schema

Trend metadata is included when:
* `--trend` is used
* `--trend-windows` is used
* volatility/strength/reversal flags are used

### 4.1 Primary Trend Fields
| Field | Type | Description |
| --- | --- | --- |
| ``trend.direction`` | string | ``up``, ``down``, ``flat``, or ``unknown`` |
| ``trend.slope`` | float | Linear regression slope over the selected window |
| ``trend.volatility`` | float | Standard deviation of historical prices |
| ``trend.strength`` | float | Normalized slope (``slope ``/ ``volatility``) |
| ``trend.reversal`` | boolean | Whether a mid‑window reversal was detected |

### 4.2 Multi‑Window Trend Fields
Included when `--trend-windows` is enabled.
| Field | Type | Description |
| --- | --- | --- |
| ``trend.windows.short.direction`` | string | Short‑window trend direction |
| ``trend.windows.short.slope`` | float | Short‑window slope |
| ``trend.windows.medium.direction`` | string | Medium‑window trend direction |
| ``trend.windows.medium.slope`` | float | Medium‑window slope |
| ``trend.windows.long.direction`` | string | Long‑window trend direction |
| ``trend.windows.long.slope`` | float | Long‑window slope |

### 4.3 Deterministic Rules
* Trend direction is derived from slope thresholds.
* Volatility is computed using deterministic standard deviation.
* Strength is computed only when volatility > 0.
* Reversal detection uses fixed mid‑window heuristics.
* Multi‑window trends never affect primary trend enforcement.

---

## 5. Provider Metadata

Provider metadata describes the selected provider and diagnostic information.

### 5.1 Fields
| Field | Type | Description |
| --- | --- | --- |
| ``provider.name`` | string | Provider identifier |
| ``provider.latency_ms`` | integer | Measured provider latency |
| ``provider.payload_size`` | integer | Raw payload size in bytes |
| ``provider.fallback_used`` | boolean | Whether fallback provider was used |
| ``provider.api_source`` | string | ``vault``, ``apikey-file``, or ``direct`` |

### 5.2 Deterministic Rules
* Latency is always measured using monotonic time.
* Payload size is always the raw JSON byte length.
* Fallback is only true if primary provider fails.
* API source reflects the actual key resolution path.

---

## 6. Error Schema

Errors are normalized into a deterministic structure.

### 6.1 Fields
| Field | Type | Description |
| --- | --- | --- |
| ``error`` | boolean | Whether an error occurred |
| ``error_type`` | string | ``provider``, ``history``, ``trend``, ``symbol``, ``api``, or ``unknown`` |
| ``error_message`` | string | Human‑readable error description |
| ``provider_error`` | string | Raw provider error (if applicable) |
| ``normalization_error`` | string | Symbol normalization error (if applicable) |

### 6.2 Deterministic Rules
* Only one error_type is ever emitted.
* error_message is always concise and stable.
* provider_error is included only when provider fails.
* normalization_error is included only when symbol resolution fails.

---

## 7. Examples

### 7.1 JSON Example (abbreviated)
```json
{
  "symbol": "AAPL",
  "normalized_symbol": "aapl",
  "asset_type": "equity",
  "provider": "yahoo",
  "price": 227.14,
  "timestamp": "2026-09-04T13:45:00Z",
  "history": [
    { "date": "2026-08-30", "close": 224.11 },
    { "date": "2026-08-31", "close": 225.02 }
  ],
  "trend": {
    "direction": "up",
    "slope": 0.91,
    "volatility": 0.44,
    "strength": 2.06,
    "reversal": false
  },
  "provider_metadata": {
    "name": "yahoo",
    "latency_ms": 118,
    "payload_size": 8421,
    "fallback_used": false
  },
  "error": false
}
```

---

## 8. Documents
* [Installation.md](Installation.md)
* [FLAGS.md](../../../docs/FLAGS.md)
* [Enforcement.md](Enforcement.md)
* [Operation.md](Operation.md)
* [Usage.md](Usage.md)