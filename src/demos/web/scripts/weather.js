/* ========================================================================
   File: weather.js
   Author: Leon McClatchey
   Company: Linktech Engineering LLC
   Created: 2026-05-06
   Modified: 2026-08-28
   Part of: NMS_Tools Monitoring Suite
   License: MIT (see LICENSE for details)

   Description:
       FastAPI version — consumes unified JSON:
       {
         status,
         message,
         location,
         data: {
           current: {...},
           hourly: { hours: [...] },
           weekly: { days: [...] }
         }
       }
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
        console.log(location);
        try {
            const response = await fetch(
                `/api/weather?location=${encodeURIComponent(location)}&country=${encodeURIComponent(country)}&units=${encodeURIComponent(units)}`
            );
            const data = await response.json();
            console.log("FULL:", data);
            // Unified JSON structure
            const root = data.data || data;
            const current = root.current;
            const hourly = root.hourly;
            const weekly = root.weekly;
            const alerts = root.alerts?.active || [];
            const resolvedLocation = data.location;
            document.getElementById("weather-meta").innerHTML = `
                <p><strong>Location:</strong> ${resolvedLocation}</p>
            `;

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

                const hasMetricPressure = block.pressure_msl !== undefined && block.pressure_msl !== null;
                const hasImperialPressure = block.pressure_inhg !== undefined && block.pressure_inhg !== null;
                const hasMetricVisibility = block.visibility_km !== undefined && block.visibility_km !== null;
                const hasImperialVisibility = block.visibility_mi !== undefined && block.visibility_mi !==null;

                if (units === "metric") {
                    out.temp = `${block.temperature_c} °C`;
                    out.feels = `${block.feels_like_c} °C`;
                    out.dewpoint = `${block.dewpoint_c} °C`;
                    out.wind = `${block.wind_kph} kph`;
                    out.gust = `${block.wind_gust_kph ?? ""} kph`;
                    out.precip = `${block.precip_mm} mm`;

                    if (hasMetricVisibility) {
                        out.visibility = `${block.visibility_km} km`;
                        out.vlabel = "Visibility";
                    } else {
                        out.visibility = "";
                        out.vlabel = "";
                    }

                    if (hasMetricPressure) {
                        out.pressure = `${block.pressure_msl} hPa`;
                        out.plabel = "Sea-Level Pressure";
                    } else {
                        out.pressure = "";
                        out.plabel = "";
                    }

                } else {
                    out.temp = `${block.temperature_f} °F`;
                    out.feels = `${block.feels_like_f} °F`;
                    out.dewpoint = `${block.dewpoint_f} °F`;
                    out.wind = `${block.wind_mph} mph`;
                    out.gust = `${block.wind_gust_mph ?? ""} mph`;
                    out.precip = `${block.precip_in} in`;

                    if (hasImperialVisibility) {
                        out.visibility = `${block.visibility_mi} mi`;
                        out.vlabel = "Visibility";
                    } else {
                        out.visibility = "";
                        out.vlabel = "";
                    }

                    if (hasImperialPressure) {
                        out.pressure = `${block.pressure_inhg} inHg`;
                        out.plabel = "Barometric Pressure";
                    } else {
                        out.pressure = "";
                        out.plabel = "";
                    }
                }

                return out;
            }
            // --------------------------------
            // Date String Timezone Formatter
            // --------------------------------
            function formatWithEmbeddedOffset(dateString) {
                const d = new Date(dateString);

                // Extract the offset from the original string
                const offset = dateString.match(/([+-]\d{2}:\d{2})$/)?.[1] || "";

                // Format the date WITHOUT converting timezone
                const parts = dateString.split(/[-+]\d{2}:\d{2}$/)[0]; // strip offset
                const local = new Date(parts + "Z"); // interpret as UTC

                return local.toLocaleString("en-US", {
                    weekday: "short",
                    month: "short",
                    day: "numeric",
                    hour: "numeric",
                    minute: "2-digit"
                }) + " " + offset;
            }
            const tzMap = {
            "-07:00": "PDT",
            "-08:00": "PST",
            "-06:00": "MDT",
            "-05:00": "CDT"
            };

            function formatWithZone(dateString) {
            const offset = dateString.match(/([+-]\d{2}:\d{2})$/)?.[1] || "";
            const zone = tzMap[offset] || offset;
            const d = new Date(dateString);
            return d.toLocaleString("en-US", {
                weekday: "short",
                month: "short",
                day: "numeric",
                hour: "numeric",
                minute: "2-digit"
            }) + " " + zone;
            }
            function formatLocalTime(isoString) {
                const d = new Date(isoString);
                return d.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
            }

            const C = convert(current);
            const heatIndex = current.index?.heat_index;
            const windChill = current.index?.wind_chill;
            const airDensity = current.index?.air_density;
            const humidex = current.index?.humidex;
            const wetBulb = current.index?.wet_bulb;
            let feelsExtras = "";

            if (airDensity !== null && airDensity !== undefined) {
                feelsExtras += `<p><strong>Air Density:</strong> ${airDensity.toFixed(1)}°</p>`;
            }
            if (heatIndex !== null && heatIndex !== undefined) {
                feelsExtras += `<p><strong>Heat Index:</strong> ${heatIndex.toFixed(1)}°</p>`;
            }
            if (humidex !== null && humidex !== undefined) {
                feelsExtras += `<p><strong>Humidex:</strong> ${humidex.toFixed(1)}°</p>`;
            }
            if (wetBulb !== null && wetBulb !== undefined) {
                feelsExtras += `<p><strong>Wet Bulb:</strong> ${wetBulb.toFixed(1)}°</p>`;
            }

            if (windChill !== null && windChill !== undefined) {
                feelsExtras += `<p><strong>Wind Chill:</strong> ${windChill.toFixed(1)}°</p>`;
            }
            let pressureLine = "";
            if (C.pressure && C.plabel) {
                pressureLine = `<p><strong>${C.plabel}:</strong> ${C.pressure}</p>`;
            }
            let visibilityLine = "";
            if (C.visibility && C.vlabel) {
                visibilityLine = `<p><strong>${C.vlabel}:</strong> ${C.visibility}</p>`
            }
            // -------------------------------
            // CURRENT ICON
            // -------------------------------
            currentIcon.innerHTML = iconTag(current.icon);

            // -------------------------------
            // CURRENT CONDITIONS
            // -------------------------------
            currentDetails.innerHTML = `
                <h3>Current</h3>
                <p><strong>Sunrise:</strong> ${formatLocalTime(current.sunrise)}</p>
                <p><strong>Sunset:</strong> ${formatLocalTime(current.sunset)}</p>
                <p><strong>Temperature:</strong> ${C.temp}</p>
                <p><strong>Feels Like:</strong> ${C.feels}</p>
                <p><strong>Dew Point:</strong> ${C.dewpoint}</p>
                <p><strong>Humidity:</strong> ${current.humidity}%</p>
                ${visibilityLine}
                <p><strong>Precip Prob:</strong> ${current.precip_probability}%</p>
                <p><strong>Wind:</strong> ${C.wind}</p>
                <p><strong>Wind Gust:</strong> ${C.gust}</p>
                <p><strong>Precip:</strong> ${C.precip}</p>
                <p><strong>Conditions:</strong> ${current.context}</p>
                ${pressureLine}
                ${feelsExtras}
            `;

            // -------------------------------
            // HOURLY FORECAST (ROTATED)
            // -------------------------------
            let hourlyHTML = `<h3>Hourly (Next 24 Hours)</h3><div class="hourly-grid">`;

            const now = new Date();
            const currentHour = now.getHours();

            let startIndex = hourly.hours.findIndex(h => {
                const t = new Date(h.time);
                return t.getHours() === (currentHour + 1) % 24;
            });

            if (startIndex === -1) startIndex = 0;

            const rotated = hourly.hours.slice(startIndex).concat(
                hourly.hours.slice(0, startIndex)
            );

            rotated.slice(0, 24).forEach(h => {
                const temp = units === "metric" ? `${h.temperature_c} °C` : `${h.temperature_f} °F`;
                const precip = h.precip_probability;
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

            weekly.days.forEach(day => {
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
            // ALERTS
            // -------------------------------
            const alertsContent = document.getElementById("alerts-content");

            if (alerts.length > 0) {

                let html = `<h3><img src="images/icons/weather/alert.svg" alt="Alert" class="alert-icon"> Alerts</h3>`;

                alerts.forEach(alert => {
                    html += `
                        <div class="alert-box" style="border-left: 6px solid ${alert.color};">
                            <p>
                                <img src="images/icons/weather/${alert.icon}" alt="Alert" class="alert-icon">
                                <strong>${alert.event}</strong>
                            </p>
                            <p>${alert.headline ?? ""}</p>
                            <p>${alert.description ?? ""}</p>
                            <p><strong>Effective:</strong> ${formatWithZone(alert.effective)}</p>
                            <p><strong>Expires:</strong> ${formatWithZone(alert.expires)}</p>
                        </div>
                    `;
                });

                alertsContent.innerHTML = html;

            } else {
                alertsContent.innerHTML = `<p>No active alerts.</p>`;
            }
            // -------------------------------
            // FADE-IN ANIMATION
            // -------------------------------
            [currentContent, hourlyContent, weeklyContent].forEach(el => {
                el.classList.remove("fade-in");
            });

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
