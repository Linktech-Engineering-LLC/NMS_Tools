# check_ticker — Operation Model

**Part of:** NMS_Tools Monitoring Suite  
**Document:** Operation Model  
**Author:** Leon McClatchey, Linktech Engineering LLC  
**License:** MIT  
**Requires:** Python 3.12+  (development only; not required for frozen binary)
**Last Updated:** 2026‑09-04

## Table of Contents
1. [Overview](#1-overview)
2. [Provider Routing](#2-provider-routing)
3. [Symbol Normalization](#3-symbol-normalization)
4. [History Retrieval](#4-history-retrieval)
5. [Trend Engine](#5-trend-engine)
6. [Logging Architecture](#6-logging-architecture)
7. [Frozen Mode Behavior](#7-frozen-mode-behavior)
8. [Failure Handling](#8-failure-handling)
9. [See Also](#9-see-also)

---

## 1. Overview

`check_ticker` operates as a deterministic market inspection tool built on the unified provider architecture from PythonTools.
Its operation model ensures:
* deterministic provider selection
* stable symbol normalization
* reproducible history retrieval
* consistent trend computation
* predictable logging behavior
* identical execution semantics between source and frozen mode

The tool is designed for monitoring environments where deterministic output and strict failure handling are required.

---

## 2. Provider Routing

Provider routing determines which market data provider is used for:
* price retrieval
* history retrieval
* trend computation
* volatility and strength analysis

### 2.1 Provider Registry

`check_ticker` uses the PythonTools provider registry, which includes:
* Yahoo — equities, indices
* Coingecko — crypto
* Finnhub — equities, indices
* AlphaVantage — equities, FX, commodities

### 2.2 Routing Rules

Provider selection follows deterministic rules:
1. Asset Type Matching
    * Crypto → Coingecko
    * Equity → Yahoo → Finnhub → AlphaVantage
    * Commodity → AlphaVantage
    * Index → Yahoo → Finnhub
2. Capability Matching  
   Providers must support:
    * history retrieval (if --history or trend flags are used)
    * OHLC data (if trend is enabled)
    * multi‑window trend (if --trend-windows is used)
3. Priority Ordering  
   Providers are attempted in deterministic order based on:
    * reliability
    * latency
    * completeness of metadata
4. Fallback Behavior  
   If the primary provider fails:
    * fallback provider is attempted
    * fallback is logged
    * failure to find a compatible provider → CRITICAL

### 2.3 Deterministic Guarantees
* The same symbol always resolves to the same provider unless the provider is unavailable.
* Provider selection never depends on randomness or environment state.
* Frozen mode uses the same routing logic as source mode.

---

## 3. Symbol Normalization

Symbol normalization ensures that user‑provided symbols are converted into deterministic internal representations.

### 3.1 Normalization Rules
* Symbols are lowercased.
* Whitespace is removed.
* Provider‑specific suffixes are applied (e.g., .NS, .AX, .TO).
* Crypto symbols are normalized to Coingecko’s canonical form.
* Index symbols are mapped to provider‑specific identifiers.

### 3.2 Asset Type Detection

Asset type is determined using:
* symbol heuristics
* provider metadata
* known symbol lists
* deterministic classification rules

### 3.3 Failure Modes

Normalization fails when:
* symbol is unknown
* asset type cannot be determined
* provider cannot support the symbol
Normalization failure → **exit 3**.

--- 

## 4. History Retrieval

History retrieval is required for:
* `--history N`
* `--trend`
* `--trend-windows`
* volatility and strength computation

### 4.1 Retrieval Rules
* History is retrieved from the selected provider.
* If the provider cannot supply history, fallback is attempted.
* History must contain at least N entries if --history N is used.
* Trend analysis requires at least 3 entries.

### 4.2 Normalization Rules
* Dates are normalized to `YYYY‑MM‑DD`.
* Entries are sorted oldest → newest.
* Closing prices retain full precision.
* Missing or malformed entries are discarded.

### 4.3 Deterministic Guarantees
* History ordering is always stable.
* Provider fallback is deterministic.
* History precision is never reduced.

---

## 5. Trend Engine

The trend engine computes:
* direction
* slope
* volatility
* strength
* reversal detection
* multi‑window trends

### 5.1 Slope Computation

Slope is computed using linear regression over:
* history window
* short/medium/long windows (if enabled)

Slope is deterministic and uses fixed regression coefficients.

### 5.2 Volatility

Volatility is computed using:
* standard deviation of closing prices
* deterministic floating‑point operations
* no randomness or sampling

### 5.3 Strength

Strength is computed as:
`strength = slope / volatility`
Strength is only computed when volatility > 0.

### 5.4 Reversal Detection

Reversal detection uses:
* mid‑window slope comparison
* deterministic thresholds
* no probabilistic heuristics

### 5.5 Multi‑Window Trends

If `--trend-windows` is enabled:
* short window (default: 3 days)
* medium window (default: 7 days)
* long window (default: 14 days)

Each window is computed independently.

### 5.6 Deterministic Guarantees
* Trend direction is derived from fixed slope thresholds.
* Volatility and strength use deterministic math.
* Reversal detection uses fixed heuristics.
* Multi‑window trends never affect primary trend enforcement.

---

## 6. Logging Architecture

Logging is deterministic and consistent across all execution modes.

### 6.1 Log Structure

Logs include:
* START banner
* normalized symbol
* provider selection
* history retrieval diagnostics
* trend computation diagnostics
* raw provider payload (JSON)
* END banner

### 6.2 Log Destinations
* Console (verbose mode only)
* File (when --log-dir is used)

### 6.3 Rotation Rules

If `--log-max-mb` is used:
* logs rotate when exceeding the size limit
* rotation uses deterministic naming
* rotation never deletes active logs

### 6.4 Frozen Mode Logging

Frozen mode uses:
* deterministic log paths
* identical log structure
* identical rotation behavior

---

## 7. Frozen Mode Behavior

Frozen mode is enabled via PyInstaller and behaves identically to source mode.

### 7.1 Deterministic Behavior

Frozen mode preserves:
* provider routing
* symbol normalization
* history retrieval
* trend computation
* logging architecture
* exit codes
* JSON/YAML output structure

#### 7.2 Environment Independence

Frozen mode does not require:
* PythonTools installation
* Python 3.12 runtime
* virtual environments

All dependencies are bundled.

### 7.3 Failure Handling

Frozen mode handles failures identically to source mode.

---

## 8. Failure Handling

Failure handling is deterministic and maps directly to exit codes.

### 8.1 Provider Failure
* network error
* invalid payload
* missing fields
**→ exit 1**

### 8.2 Trend Failure
* slope cannot be computed
* volatility cannot be computed
* reversal detection fails
**→ exit 1**

### 8.3 Trend Requirement Failure
* trend direction mismatch
**→ exit 2**

### 8.4 Symbol Normalization Failure
* unknown symbol
* unsupported asset type
**→ exit 3**

### 8.5 API Key / Vault Failure
* vault cannot be decrypted
* missing API keys
**→ exit 1**

---

## 9. See Also
* [Installation.md](Installation.md)
* [FLAGS.md](../../../docs/FLAGS.md)
* [Metadata_schema.md](Metadata_schema.md)
* [Enforcement.md](Enforcement.md)
* [Usage.md](Usage.md)