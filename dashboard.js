async function loadDashboard() {
  // Determine whether we are in /nightly/ or /stable/
  const path = window.location.pathname;
  const isNightly = path.includes("/nightly/");
  const isStable = path.includes("/stable/");

  const metaUrl = "metadata.json";

  let meta;
  try {
    const response = await fetch(metaUrl);
    meta = await response.json();
  } catch (err) {
    document.getElementById("build-info").innerHTML =
      "<p style='color:red'>Failed to load metadata.json</p>";
    return;
  }

  // Metadata v2 required for NMS_Tools
  const build = meta.build;
  const toolchain = meta.toolchain;
  const artifacts = meta.artifacts;

  // -----------------------------
  // ⭐ Badges
  // -----------------------------
  const shortCommit = build.commit.substring(0, 7);
  const shortDate = build.date.split("T")[0].replace(/-/g, "_");

  document.getElementById("version-badge").src =
    `https://img.shields.io/badge/version-${shortCommit}-blue`;

  document.getElementById("date-badge").src =
    `https://img.shields.io/badge/date-${shortDate}-lightgrey`;

  document.getElementById("python-badge").src =
    `https://img.shields.io/badge/python-${toolchain.python}-yellow`;

  document.getElementById("pyi-badge").src =
    `https://img.shields.io/badge/pyinstaller-${toolchain.pyinstaller}-orange`;

  // -----------------------------
  // ⭐ Build Info Table
  // -----------------------------
  document.getElementById("build-info").innerHTML = `
    <table>
      <tr><th>Field</th><th>Value</th></tr>
      <tr><td>Date</td><td>${build.date}</td></tr>
      <tr><td>Commit</td><td>${build.commit}</td></tr>
      <tr><td>Branch</td><td>${build.branch}</td></tr>
      <tr><td>Workflow Run</td><td>${build.workflow_run_id}</td></tr>
    </table>
  `;

  // -----------------------------
  // ⭐ Artifact Table
  // -----------------------------
  let rows = "";
  for (const a of artifacts) {
    const downloadUrl = isNightly
      ? `https://github.com/Linktech-Engineering-LLC/NMS_Tools/releases/download/nightly/${a.name}`
      : `https://github.com/Linktech-Engineering-LLC/NMS_Tools/releases/download/${build.version}/${a.name}`;

    rows += `
      <tr>
        <td>${a.name}</td>
        <td>${a.size}</td>
        <td>${a.sha256}</td>
        <td>${a.crc32}</td>
        <td>${a.type}</td>
        <td>${a.os}</td>
        <td>${a.arch}</td>
        <td><a href="${downloadUrl}">Download</a></td>
      </tr>
    `;
  }

  document.getElementById("artifact-table").innerHTML = `
    <table>
      <tr>
        <th>Name</th>
        <th>Size</th>
        <th>SHA‑256</th>
        <th>CRC‑32</th>
        <th>Type</th>
        <th>OS</th>
        <th>Arch</th>
        <th>Download</th>
      </tr>
      ${rows}
    </table>
  `;
}

window.onload = loadDashboard;
