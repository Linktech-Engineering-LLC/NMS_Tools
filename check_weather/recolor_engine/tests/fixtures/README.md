# Recolor Engine – Test Fixtures

This directory contains **synthetic SVG fixtures** used by the recolor engine
test harness (`run_tests.py`). These files are intentionally minimal and are
not artistic icons. Their purpose is to provide **deterministic structural
shapes** that exercise the classifier, analyzer, and recolor logic.

The fixtures allow the test harness to validate:

- Filename → semantic group classification  
- SVG structure → group detection heuristics  
- Recoloring → correct palette application  

Each file is designed to trigger a specific semantic group in the analyzer.

---

## Fixture Overview

### `sun.svg`
A simple `<circle>` element representing the sun.  
A small `L`/`Z` path is included but **not** used for detection.

**Triggers:**  
- `sun`

**Used to test:**  
- Sun detection  
- Sun recoloring (yellow)

---

### `day-sunny.svg`
A standalone `<circle>` icon representing a clear‑sky sun.

**Triggers:**  
- `sun`

**Used to test:**  
- Sun detection  
- Sun recoloring  
- Integration pipeline behavior for sun‑only icons

---

### `cloud.svg`
A cubic‑curve cloud shape using both `C` and `S` commands.

**Triggers:**  
- `cloud`

**Used to test:**  
- Cloud detection  
- Cloud recoloring (rain or snow palette depending on expected groups)

---

### `rain.svg`
A cloud shape plus two short lowercase‑`c` raindrop paths.

**Triggers:**  
- `cloud`  
- `rain`

**Used to test:**  
- Rain detection  
- Rain recoloring (blue)  
- Cloud recoloring (rain cloud palette)

---

### `snow.svg`
A cloud shape plus a small arc (`A`) snowflake.

**Triggers:**  
- `cloud`  
- `snow`

**Used to test:**  
- Snow detection  
- Snow recoloring (white)  
- Cloud recoloring (snow cloud palette)

---

### `sleet.svg`
A single raindrop (`c`) plus a short uppercase‑`C` snowflake curve.

**Triggers:**  
- `rain`  
- `snow`

**Used to test:**  
- Mixed‑condition detection  
- Correct dual‑palette recoloring  
- Ensuring sleet does **not** trigger cloud

---

### `thunder.svg`
A cloud shape plus a zig‑zag lightning bolt using multiple `L` commands.

**Triggers:**  
- `cloud`  
- `thunder`

**Used to test:**  
- Thunder detection  
- Thunder recoloring (gold)  
- Cloud recoloring (storm palette)

---

## Notes

- These fixtures are **not** used in production.  
- They are intentionally small to keep tests fast and deterministic.  
- They avoid VS Code’s binary detector by including an XML header.  
- They are safe to modify as long as the structural commands remain consistent
  with the analyzer heuristics.

---

## Adding New Fixtures

When adding new semantic groups or heuristics:

1. Create a minimal SVG that uses the path commands your analyzer expects.  
2. Add the file to this directory.  
3. Update the integration tests to include detection and recolor checks.  
4. Keep fixtures small and readable.  
