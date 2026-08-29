/* ========================================================================
   File: global.js
   Author: Leon McClatchey
   Company: Linktech Engineering LLC
   Created: 2026-08-29
   Part of: NMS_Tools Monitoring Suite
   Description:
       Global pure helper functions shared across all frontend modules.
       Safe to load in <head> because it contains no DOM references
       and no event handlers.
   ======================================================================== */

/* ------------------------------------------------------------
   Number Helpers
------------------------------------------------------------ */

/**
 * Safely formats a number to fixed decimals.
 * Returns "" if the value is null/undefined.
 */
function safeFixed(value, decimals = 2) {
    if (value === null || value === undefined) return "";
    return Number(value).toFixed(decimals);
}

/**
 * Returns the last element of an array safely.
 */
function last(arr) {
    if (!arr || arr.length === 0) return null;
    return arr[arr.length - 1];
}

/* ------------------------------------------------------------
   Ticker Helpers
------------------------------------------------------------ */

/**
 * Extracts the latest OHLC values from the raw ticker block.
 * Returns an object with formatted values.
 */
function extractOHLC(raw) {
    if (!raw) return {};

    return {
        open: safeFixed(last(raw.open)),
        close: safeFixed(last(raw.close)),
        high: safeFixed(last(raw.high)),
        low: safeFixed(last(raw.low))
    };
}

/**
 * Converts a history array into chart-friendly labels.
 */
function historyLabels(history) {
    return history ? history.map((_, i) => i) : [];
}
/**
 * Convert a backend timestamp (ISO string, epoch seconds, or null)
 * into a clean localtime string.
 *
 * Returns "N/A" if timestamp is null or invalid.
 */
function toLocalTime(ts) {
    if (!ts) return "N/A";

    let dt;

    // Case 1: epoch seconds (FastAPI sometimes returns numeric timestamps)
    if (typeof ts === "number") {
        dt = new Date(ts * 1000);
    }
    // Case 2: ISO string
    else if (typeof ts === "string") {
        dt = new Date(ts);
    }
    else {
        return "N/A";
    }

    if (isNaN(dt.getTime())) return "N/A";

    // Format: YYYY-MM-DD HH:MM:SS (localtime)
    const yyyy = dt.getFullYear();
    const mm = String(dt.getMonth() + 1).padStart(2, "0");
    const dd = String(dt.getDate()).padStart(2, "0");

    const hh = String(dt.getHours()).padStart(2, "0");
    const mi = String(dt.getMinutes()).padStart(2, "0");
    const ss = String(dt.getSeconds()).padStart(2, "0");

    return `${yyyy}-${mm}-${dd} ${hh}:${mi}:${ss}`;
}
