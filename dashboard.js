//
// dashboard.js — NMS_Tools Dashboard Renderer
//

async function loadMetadata() {
    try {
        const response = await fetch("metadata.json");
        if (!response.ok) throw new Error("metadata.json not found");
        return await response.json();
    } catch (err) {
        console.error("Failed to load metadata.json:", err);
        return null;
    }
}

function setBadge(id, label, value, color) {
    const el = document.getElementById(id);
    if (el) {
        el.src = `https://img.shields.io/badge/${label}-${value}-${color}`;
    }
}

function renderBuildInfo(meta) {
    const div = document.getElementById("build-info");
    if (!div) return;

    const b = meta.build;
    const t = meta.toolchain;

    div.innerHTML = `
        <table>
            <tr><th>Date</th><td>${b.date}</td></tr>
            <tr><th>Commit</th><td>${b.commit}</td></tr>
            <tr><th>Branch</th><td>${b.branch}</td></tr>
            <tr><th>Workflow Run</th><td>${b.workflow_run_id}</td></tr>
            <tr><th>Python</th><td>${t.python}</td></tr>
            <tr><th>PyInstaller</th><td>${t.pyinstaller}</td></tr>
        </table>
    `;
}

function renderArtifacts(meta) {
    const div = document.getElementById("artifact-table");
    if (!div) return;

    const nightlyURL =
        "https://github.com/Linktech-Engineering-LLC/NMS_Tools/releases/download/nightly";

    let html = `
        <table>
            <tr>
                <th>Name</th>
                <th>Type</th>
                <th>OS</th>
                <th>Arch</th>
                <th>Size</th>
                <th>SHA-256</th>
                <th>CRC32</th>
                <th>Download</th>
            </tr>
    `;

    for (const a of meta.artifacts) {
        const dl = `${nightlyURL}/${a.name}`;
        html += `
            <tr>
                <td>${a.name}</td>
                <td>${a.type}</td>
                <td>${a.os}</td>
                <td>${a.arch}</td>
                <td>${a.size.toLocaleString()} bytes</td>
                <td><code>${a.sha256}</code></td>
                <td><code>${a.crc32}</code></td>
                <td><a class="download-btn" href="${dl}">Download</a></td>
            </tr>
        `;
    }

    html += "</table>";
    div.innerHTML = html;
}

async function main() {
    const meta = await loadMetadata();
    if (!meta) return;

    // Badges
    setBadge("version-badge", "version", meta.build.commit.substring(0, 7), "blue");
    setBadge("date-badge", "date", meta.build.date.split("T")[0], "lightgrey");
    setBadge("python-badge", "python", meta.toolchain.python, "yellow");
    setBadge("pyi-badge", "pyinstaller", meta.toolchain.pyinstaller, "orange");

    // Sections
    renderBuildInfo(meta);
    renderArtifacts(meta);
}

main();
