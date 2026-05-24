/* ========================================================================
   File: weather.js
   Author: Leon McClatchey
   Company: Linktech Engineering LLC
   Created: 2026-05-06
   Modified: 2026-05-06
   Part of: NMS_Tools Monitoring Suite
   License: MIT (see LICENSE for details)

   Description:
       calls the check_weather.py via a cgi bash script
       reads the resulting json and populates the webpage
       with the results
   ======================================================================== */


document.addEventListener("DOMContentLoaded", () => {

    const form = document.getElementById("weather-form");
    const currentIcon = document.getElementById("current-icon");
    const currentDetails = document.getElementById("current-details");
    const currentContent = document.getElementById("current-content");
    const hourlyContent = document.getElementById("hourly-content");
    const weeklyContent = document.getElementById("weekly-content");
    const spinner = document.getElementById("loading-spinner");
    const ICON_VERSION = "3";

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const location = document.getElementById("location").value.trim();
        const country = document.getElementById("country").value.trim() || "US";
        const units = document.getElementById("units").value;

        spinner.style.display = "flex";
        try {
            const response = await fetch(
                `/api/weather?location=${encodeURIComponent(location)}&country=${encodeURIComponent(country)}&units=${encodeURIComponent(units)}`
            );

            const data = await response.json();

            const current = data.current;
            const hourly = data.hourly;
            const weekly = data.weekly;

            // -------------------------------
            // ICON HELPER
            // -------------------------------
            function iconTag(filename) {
                return `<img src="/images/icons/weather/${filename}?v=${ICON_VERSION}" class="wx-icon">`;
            }

            // -------------------------------
            // UNIT CONVERSION
            // -------------------------------
            function convert(block) {
                let out = {};

                if (units === "metric") {
                    out.temp = `${block.data.temperature_c} °C`;
                    out.feels = `${block.data.apparent_temperature_c} °C`;
                    out.dewpoint = `${block.data.dewpoint_c} °C`;
                    out.wind = `${block.data.wind_kph} kph`;
                    out.gust = `${block.data.wind_gust_kph} kph`;
                    out.precip = `${block.data.precip_mm} mm`;
                    out.visibility = `${block.data.visibility_km} km`;
                    out.pressure = `${block.data.pressure_msl} hPa`;
                    out.plabel = "Sea-Level Pressure";
                } else {
                    out.temp = `${block.data.temperature_f} °F`;
                    out.feels = `${block.data.apparent_temperature_f} °F`;
                    out.dewpoint = `${block.data.dewpoint_f} °F`;
                    out.wind = `${block.data.wind_mph} mph`;
                    out.gust = `${block.data.wind_gust_mph} mph`;
                    out.precip = `${block.data.precip_in} in`;
                    out.visibility = `${block.data.visibility_mi} mi`;
                    out.pressure = `${block.data.pressure_inhg} inHg`;
                    out.plabel = "Barometric Pressure";
                }

                return out;
            }

            const C = convert(current);
            // -------------------------------
            // CURRENT ICON
            // -------------------------------
            currentIcon.innerHTML = iconTag(current.data.icon);

            // -------------------------------
            // CURRENT CONDITIONS
            // -------------------------------
            currentDetails.innerHTML = `
                <h3>Current</h3>
                <p><strong>Temperature:</strong> ${C.temp}</p>
                <p><strong>Feels Like:</strong> ${C.feels}</p>
                <p><strong>Dew Point:</strong> ${C.dewpoint}</p>
                <p><strong>Cloud Cover:</strong> ${current.data.cloudcover} %</p>
                <p><strong>Visibility:</strong> ${C.visibility}</p>
                <p><strong>Precip Prob:</strong> ${current.data.precipitation_probability} %</p>
                <p><strong>Wind:</strong> ${C.wind}</p>
                <p><strong>Wind Gust:</strong> ${C.gust}</p>
                <p><strong>Precip:</strong> ${C.precip}</p>
                <p><strong>Conditions:</strong> ${current.data.context}</p>
                <p><strong>${C.plabel}:</strong> ${C.pressure}</p>
            `;

            // -------------------------------
            // HOURLY FORECAST (ROTATED)
            // -------------------------------
            let hourlyHTML = `<h3>Hourly (Next 24 Hours)</h3><div class="hourly-grid">`;

            const now = new Date();
            const currentHour = now.getHours();

            let startIndex = hourly.data.hours.findIndex(h => {
                const t = new Date(h.time);
                return t.getHours() === (currentHour + 1) % 24;
            });

            if (startIndex === -1) startIndex = 0;

            const rotated = hourly.data.hours.slice(startIndex).concat(
                hourly.data.hours.slice(0, startIndex)
            );

            rotated.slice(0, 24).forEach(h => {
                const temp = units === "metric" ? `${h.temperature_c} °C` : `${h.temperature_f} °F`;
                const precip = h.precipitation_probability;
                const time = new Date(h.time).toLocaleTimeString("en-US", { hour: "numeric" });

                hourlyHTML += `
                    <div class="hourly-cell">
                        <div class="hour">${time}</div>
                        <div class="icon">${iconTag(h.icon)}</div>
                        <div class="temp">${temp}</div>
                        <div class="precip">${precip}%</div>
                    </div>
                `;
            });

            hourlyHTML += `</div>`;
            hourlyContent.innerHTML = hourlyHTML;

            // -------------------------------
            // WEEKLY FORECAST
            // -------------------------------
            let weeklyHTML = `<h3>Weekly Forecast</h3><div class="weekly-grid">`;

            weekly.data.days.forEach(day => {
                const date = new Date(day.date + "T12:00:00");
                const dayName = date.toLocaleDateString("en-US", { weekday: "short" });
                const month = date.getMonth() + 1;
                const dayNum = date.getDate();

                const high = units === "metric" ? `${day.temp_max_c} °C` : `${day.temp_max_f} °F`;
                const low  = units === "metric" ? `${day.temp_min_c} °C` : `${day.temp_min_f} °F`;
                const wind = units === "metric" ? `${day.wind_kph_max} kph` : `${day.wind_mph_max} mph`;

                weeklyHTML += `
                    <div class="weekly-day">
                        <div class="weekly-date">${dayName} ${month}/${dayNum}</div>
                        <div class="weekly-icon">${iconTag(day.icon)}</div>
                        <div class="weekly-temps">${high} / ${low}</div>
                        <div class="weekly-precip">${day.precipitation_probability_max}% rain</div>
                        <div class="weekly-wind">${wind} wind</div>
                    </div>
                `;
            });

            weeklyHTML += `</div>`;
            weeklyContent.innerHTML = weeklyHTML;

            // -------------------------------
            // FADE-IN ANIMATION
            // -------------------------------
            [currentContent, hourlyContent, weeklyContent].forEach(el => {
                el.classList.remove("fade-in");
            });

            // Force reflow so animation restarts cleanly
            void currentContent.offsetWidth;

            [currentContent, hourlyContent, weeklyContent].forEach(el => {
                el.classList.add("fade-in");
            });

        } catch (err) {
            console.error("Weather demo error:", err);
            currentContent.innerHTML = `<p class="error">Error: ${err}</p>`;
        } finally {
            spinner.style.display = "none";
        }

    });
});
