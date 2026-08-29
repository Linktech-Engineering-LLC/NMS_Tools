/* ========================================================================
   File: ticker.js
   Author: Leon McClatchey
   Company: Linktech Engineering LLC
   Created: 2026-08-29
   Modified: 2026-08-29
   Part of: NMS_Tools Monitoring Suite
   License: MIT (see LICENSE for details)
   ======================================================================== */

document.addEventListener("DOMContentLoaded", () => {

    const form = document.getElementById("ticker-form");
    const spinner = document.getElementById("loading-spinner");

    const tickerContent = document.getElementById("ticker-content");
    const trendContent = document.getElementById("trend-content");
    const historyContent = document.getElementById("history-content");

    let historyChart = null;

    // ------------------------------------------------------------
    // MAIN FUNCTION: event handler
    // ------------------------------------------------------------
    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const symbol = document.getElementById("ticker").value.trim();
        if (!symbol) return;

        spinner.style.display = "flex";
        console.log(symbol);
        lookupTicker(symbol);
        spinner.style.display = "none";
    });
});
// ------------------------------------------------------------
// RENDER META
// -----------------------------------------------------------
function renderMeta(data){
    document.getElementById("ticker-meta").innerHTML = `
        <div class="meta-header">
            <strong>Ticker: ${data.ticker}, Provider: ${data.provider}, Last Updated: ${toLocalTime(data.timestamp)}</strong>
        </div>

    `;
}
// ------------------------------------------------------------
// RENDER CURRENT PRICE
// ------------------------------------------------------------
function renderTicker(data) {
    const ohlc = extractOHLC(data.raw);

    const html = `
        <div class="quote-grid">

            <!-- COLUMN 1 -->
            <div class="quote-col">
                <div class="quote-price">
                    <strong>Price:</strong> $${safeFixed(data.price)}
                </div>

                <div class="quote-change ${data.pct >= 0 ? "positive" : "negative"}">
                    <strong>PCT:</strong> ${safeFixed(data.pct)}%
                </div>
                <div><strong>Open:</strong> ${ohlc.open}</div>
                <div><strong>High:</strong> ${ohlc.high}</div>
                <div><strong>Low:</strong> ${ohlc.low}</div>
                <div><strong>Close:</strong> ${ohlc.close}</div>
            </div>

            <!-- COLUMN 2 -->
            <div class="quote-col">
                <div><strong>Trend:</strong> ${data.trend.trend}</div>
                <div><strong>Slope:</strong> ${safeFixed(data.trend.slope)}</div>
                <div><strong>Volatility:</strong> ${safeFixed(data.trend.volatility)}</div>
                <div><strong>Strength:</strong> ${safeFixed(data.trend.strength)}</div>
                <div><strong>Reversal:</strong> ${data.trend.reversal}</div>
                <div><strong>History Points:</strong> ${data.history?.length ?? 0}</div>
            </div>

        </div>
    `;

    document.getElementById("quote-content").innerHTML = html;
}
// ------------------------------------------------------------
// RENDER TREND BLOCK
// ------------------------------------------------------------
function renderTrend(trend) {
    document.getElementById("sparkline-content").innerHTML =
        `Trend: ${trend.trend} (slope ${trend.slope.toFixed(2)})`;
}

// ------------------------------------------------------------
// RENDER HISTORY GRAPH (Chart.js)
// ------------------------------------------------------------
function renderHistory(history) {
    if (!history || history.length === 0) {
        historyContent.innerHTML = `<p>No history available.</p>`;
        return;
    }

    historyContent.innerHTML = `<canvas id="history-chart"></canvas>`;
    const ctx = document.getElementById("history-chart").getContext("2d");

    if (historyChart) {
        historyChart.destroy();
    }

    historyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: history.map((_, i) => i),
            datasets: [{
                label: "History",
                data: history,
                borderColor: "#0077ff",
                backgroundColor: "rgba(0, 119, 255, 0.1)",
                tension: 0.2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { display: false }
            }
        }
    });
}
async function lookupTicker(symbol) {
    // Always clear previous content
    clearTickerUI();

    try {
        const response = await fetch(`/api/ticker?symbol=${encodeURIComponent(symbol)}`);
        const data = await response.json();
        console.log(data);

        if (!data || data.error) {
            showTickerError(data?.error || "No data available");
            return;
        }

        renderMeta(data);
        renderTicker(data);
        //renderTrend(data.trend);

    } catch (err) {
        showTickerError("Lookup failed");
    }
}
function clearTickerUI() {
    document.getElementById("ticker-meta").innerHTML = "";
    document.getElementById("quote-content").innerHTML = "";
    document.getElementById("sparkline-content").innerHTML = "";
}

function showTickerError(msg) {
    // Meta bar shows the failure message
    document.getElementById("ticker-meta").innerHTML =
        `<div class="meta-error"><strong>Lookup Failed</strong></div>`;

    // Collapse the detail sections
    document.getElementById("quote-content").innerHTML = "";
    document.getElementById("sparkline-content").innerHTML = "";

    // Optional: visually indicate the error
    const quoteBox = document.getElementById("quote-content");
    quoteBox.style.display = "none"; // hides the card entirely
}
