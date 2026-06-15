//
// dashboard.js — Unified NMS_Tools Dashboard Renderer
//

async function loadMetadata() {
  try {
    const response = await fetch("metadata.json");
    if (!response.ok) throw new Error("metadata.json not found");
    return await response.json();
  } catch (err) {
    document.getElementById("build-info").innerHTML =
      "<p style='color:red'>Failed to load metadata.json</p>";
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
      <tr><th>Field</th><th>Value</th></tr>
      <tr><td>Date</td><td>${b.date}</td></tr>
      <tr><td>Commit</td><td>${b.commit}</td></tr>
      <tr><td>Branch</td><td>${b.branch}</td></tr>
      <tr><td>Workflow Run</td><td>${b.workflow_run_id}</td></tr>
      <tr><td>Python</td><td>${t.python}</td></tr>
      <tr><td>PyInstaller</td><td>${t.pyinstaller}</td></tr>
    </table>
  `;
}

function renderArtifacts(meta) {
  const div = document.getElementById("artifact-table");
  if (!div) return;

  const nightlyURL =
    "https://github.com/Linktech-Engineering-LLC/NMS_Tools/releases/download/nightly";

  let rows = "";

  for (const a of meta.artifacts) {
    const dl = `${nightlyURL}/${a.name}`;
    rows += `
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

  div.innerHTML = `
    <table>
      <tr>
        <th>Name</th>
        <th>Type</th>
        <th>OS</th>
        <th>Arch</th>
        <th>Size</th>
        <th>SHA‑256</th>
        <th>CRC‑32</th>
        <th>Download</th>
      </tr>
      ${rows}
    </table>
  `;
}

async function main() {
  const meta = await loadMetadata();
  if (!meta) return;

  const build = meta.build;
  const toolchain = meta.toolchain;

  // -----------------------------
  // ⭐ Badges (RunUpdates‑aligned)
  // -----------------------------

  // Commit badge
  const shortCommit = build.commit.substring(0, 7);
  setBadge("version-badge", "version", shortCommit, "blue");

  // Date badge (underscore fix)
  const shortDate = build.date.split("T")[0].replace(/-/g, "_");
  setBadge("date-badge", "date", shortDate, "lightgrey");

  // Python badge
  setBadge("python-badge", "python", toolchain.python, "yellow");

  // PyInstaller badge
  setBadge("pyi-badge", "pyinstaller", toolchain.pyinstaller, "orange");

  // -----------------------------
  // ⭐ Sections
  // -----------------------------
  renderBuildInfo(meta);
  renderArtifacts(meta);
}

main();
