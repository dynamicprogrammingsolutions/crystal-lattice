import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const landingRoot = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "..",
);
const repositoryRoot = path.resolve(landingRoot, "..");
const outputRoot = path.join(
  landingRoot,
  "artifacts",
  "homepage-visual-review",
);
const imagesRoot = path.join(outputRoot, "images");

const source = {
  desktop: path.join(
    repositoryRoot,
    "desktop",
    "crystal-lattice-control-desktop-rn",
    "artifacts",
    "website-visual",
  ),
  mobile: path.join(
    repositoryRoot,
    "mobile",
    "crystal-lattice-control-rn",
    "artifacts",
    "website-visual",
  ),
};

const captures = {
  agentCodex: ["desktop", "agent-codex"],
  agentClaude: ["desktop", "agent-claude"],
  desktopContinuity: ["desktop", "cross-device"],
  providerSettings: ["mobile", "provider-settings"],
  featurePlugins: ["mobile", "plugins"],
  sessionActions: ["mobile", "actions"],
  compiled: ["mobile", "compiled"],
  cost: ["mobile", "cost"],
  mobileContinuity: ["mobile", "hero"],
  vibe: ["mobile", "vibe"],
  workspaces: ["mobile", "workspaces"],
};

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function copyCaptures() {
  fs.rmSync(outputRoot, { recursive: true, force: true });
  fs.mkdirSync(imagesRoot, { recursive: true });
  const copied = {};
  for (const [key, [family, basename]] of Object.entries(captures)) {
    copied[key] = {};
    for (const theme of ["light", "dark"]) {
      const filename = `${basename}-${theme}.png`;
      const input = path.join(source[family], filename);
      if (!fs.existsSync(input)) {
        throw new Error(`Missing capture: ${input}`);
      }
      const outputName = `${key}-${theme}.png`;
      fs.copyFileSync(input, path.join(imagesRoot, outputName));
      copied[key][theme] = `images/${outputName}`;
    }
  }
  return copied;
}

function screenshot(copied, key, theme, alt, className = "") {
  return `<figure class="capture ${className}">
    <img src="${copied[key][theme]}" alt="${escapeHtml(alt)}" />
    <figcaption>Production capture · ${theme}</figcaption>
  </figure>`;
}

function relationBoard({
  copied,
  theme,
  title,
  snippet,
  pluginKey,
  pluginAlt,
  uiKey,
  uiAlt,
  note,
}) {
  return `<article class="relationship">
    <h3>${escapeHtml(title)}</h3>
    <div class="relationship-grid">
      <div class="relationship-node code-node">
        <span class="node-label">1 · Configuration</span>
        <pre>${escapeHtml(snippet)}</pre>
      </div>
      <div class="connector" aria-label="Configuration loads the plugin">
        <strong>1 → 2</strong><span>loads plugin package</span>
      </div>
      <div class="relationship-node">
        <span class="node-label">2 · Plugin surface</span>
        ${screenshot(copied, pluginKey, theme, pluginAlt, "embedded")}
      </div>
      <div class="connector" aria-label="Plugin contributes the user interface">
        <strong>2 → 3</strong><span>contributes UI</span>
      </div>
      <div class="relationship-node">
        <span class="node-label">3 · User interface</span>
        ${screenshot(copied, uiKey, theme, uiAlt, "embedded")}
      </div>
    </div>
    <p class="note">${escapeHtml(note)}</p>
  </article>`;
}

function section(id, title, body) {
  return `<section id="${id}">
    <div class="section-heading">
      <span>${id.replace("highlight-", "Highlight ")}</span>
      <h2>${escapeHtml(title)}</h2>
    </div>
    ${body}
  </section>`;
}

function buildHtml(copied) {
  const providerSnippet = `{
  "providers": {
    "openai": {
      "plugins": [
        "path:\${BUILTIN_PLUGINS}/openai-responses"
      ]
    }
  },
  "agents": {
    "codex-openai": {
      "provider": "openai",
      "auth_mode": "auto",
      "enable_flex_processing": true
    }
  }
}`;
  const applicationSnippet = `{
  "plugins": [
    "path:\${BUILTIN_PLUGINS}/session-status-app",
    "path:\${BUILTIN_PLUGINS}/session-pinned-app",
    "path:\${BUILTIN_PLUGINS}/session-title-app"
  ]
}`;

  const themes = ["light", "dark"].map(theme => `<div class="theme-block">
    <h3>${theme === "light" ? "Light" : "Dark"}</h3>
    <div class="capture-grid two">
      ${screenshot(
        copied,
        "agentCodex",
        theme,
        "Two-pane Crystal Lattice Desktop agent picker with Codex selected and effective default tools visible.",
        "desktop-frame",
      )}
      ${screenshot(
        copied,
        "agentClaude",
        theme,
        "Two-pane Crystal Lattice Desktop agent picker with Claude selected and Claude-oriented tools visible.",
        "desktop-frame",
      )}
    </div>
  </div>`).join("");

  const relationshipThemes = ["light", "dark"].map(theme => `<div class="theme-block">
    <h3>${theme === "light" ? "Light" : "Dark"}</h3>
    ${relationBoard({
      copied,
      theme,
      title: "Provider configuration → provider features → settings",
      snippet: providerSnippet,
      pluginKey: "featurePlugins",
      pluginAlt: "Production session plugins modal showing independently selectable OpenAI Responses features.",
      uiKey: "providerSettings",
      uiAlt: "Production session settings showing authentication mode, flex processing, and reasoning effort.",
      note:
        "The red connectors and numbered labels are illustrative website annotations. The screenshots inside the nodes are production UI.",
    })}
    ${relationBoard({
      copied,
      theme,
      title: "Application-plugin configuration → actions → workflow state",
      snippet: applicationSnippet,
      pluginKey: "sessionActions",
      pluginAlt: "Production session actions menu containing plugin-contributed session actions.",
      uiKey: "workspaces",
      uiAlt: "Production session list with plugin-driven title, subtitle, pin, and status controls.",
      note:
        "This candidate uses the production action row as the visible plugin surface. Review whether a separate application-plugin registry proof is still required.",
    })}
  </div>`).join("");

  const transparencyThemes = ["light", "dark"].map(theme => `<div class="theme-block">
    <h3>${theme === "light" ? "Light" : "Dark"}</h3>
    <div class="capture-grid two">
      ${screenshot(
        copied,
        "compiled",
        theme,
        "Production action-display modal containing the compiled system message generated through the real feature action.",
        "phone-frame",
      )}
      ${screenshot(
        copied,
        "cost",
        theme,
        "Production Cost report action-display modal generated from generic synthetic records, with provider usage visible behind it.",
        "phone-frame",
      )}
    </div>
    <p class="note">Cost values are illustrative fixture data, not company spending or provider invoices.</p>
  </div>`).join("");

  const continuityThemes = ["light", "dark"].map(theme => `<div class="theme-block">
    <h3>${theme === "light" ? "Light" : "Dark"}</h3>
    <div class="continuity-board">
      <div class="device desktop-device">
        <span>Desktop</span>
        <img src="${copied.desktopContinuity[theme]}" alt="Desktop client showing the shared compatibility-fix session." />
      </div>
      <div class="continuity-link">
        <strong>Same session</strong>
        <span>title · status · agent · latest prompt · answer</span>
      </div>
      <div class="device phone-device">
        <span>Mobile</span>
        <img src="${copied.mobileContinuity[theme]}" alt="Mobile client showing the same compatibility-fix session." />
      </div>
    </div>
  </div>`).join("");

  const vibeThemes = ["light", "dark"].map(theme => `<div class="theme-block">
    <h3>${theme === "light" ? "Light" : "Dark"}</h3>
    ${screenshot(
      copied,
      "vibe",
      theme,
      "GLM-5.3 Flash through Z.ai handling a non-development research workflow with attached files and expanded reasoning before tool calls.",
      "phone-frame single",
    )}
  </div>`).join("");

  const workspaceThemes = ["light", "dark"].map(theme => `<div class="theme-block">
    <h3>${theme === "light" ? "Light" : "Dark"}</h3>
    ${screenshot(
      copied,
      "workspaces",
      theme,
      "Session list with todo, in-progress, and done sessions, descriptive titles and subtitles, header-only pin state, and the plugin-driven status list open.",
      "phone-frame single",
    )}
  </div>`).join("");

  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Crystal Lattice homepage visual review</title>
  <style>
    :root { color-scheme: light dark; font-family: Inter, ui-sans-serif, system-ui, sans-serif; }
    * { box-sizing: border-box; }
    body { margin: 0; background: #0c0f14; color: #f6f7f9; }
    header { max-width: 1500px; margin: 0 auto; padding: 48px 28px 22px; }
    header p, .note { color: #aeb7c5; line-height: 1.55; }
    main { max-width: 1500px; margin: 0 auto; padding: 0 28px 80px; }
    section { border-top: 1px solid #2a303a; padding: 42px 0; }
    .section-heading span, .node-label { color: #79b5ff; font-size: 12px; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }
    h1 { font-size: clamp(34px, 5vw, 66px); margin: 0 0 14px; }
    h2 { font-size: clamp(26px, 3vw, 44px); margin: 6px 0 26px; }
    h3 { margin: 0 0 16px; }
    .theme-block { background: #141922; border: 1px solid #2a303a; border-radius: 20px; padding: 22px; margin: 20px 0; }
    .capture-grid { display: grid; gap: 20px; }
    .capture-grid.two { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    figure { margin: 0; }
    .capture img { display: block; width: 100%; max-height: 760px; object-fit: contain; background: #080a0d; }
    .capture figcaption { color: #8f9bad; font-size: 12px; margin-top: 8px; }
    .desktop-frame img { border: 10px solid #252b35; border-top-width: 28px; border-radius: 14px; }
    .phone-frame img { width: min(100%, 520px); margin: 0 auto; border: 10px solid #252b35; border-radius: 34px; }
    .single { max-width: 620px; margin: 0 auto; }
    .relationship { margin: 20px 0 34px; }
    .relationship-grid { display: grid; grid-template-columns: 1fr 130px 1fr 130px 1fr; align-items: center; gap: 12px; }
    .relationship-node { min-width: 0; background: #0d1118; border: 1px solid #343b48; border-radius: 14px; padding: 14px; }
    .relationship-node pre { overflow: auto; white-space: pre-wrap; color: #dce9ff; font: 12px/1.5 ui-monospace, SFMono-Regular, Menlo, monospace; }
    .embedded img { max-height: 560px; }
    .embedded figcaption { display: none; }
    .connector { color: #ff5a5f; text-align: center; display: grid; gap: 5px; }
    .connector strong { font-size: 24px; }
    .connector span { color: #f2b4b6; font-size: 11px; }
    .continuity-board { display: grid; grid-template-columns: 1.8fr 180px .72fr; gap: 20px; align-items: center; }
    .device { background: #090c11; border: 1px solid #343b48; padding: 12px; }
    .device > span { display: inline-block; margin-bottom: 8px; color: #79b5ff; font-weight: 800; }
    .device img { display: block; width: 100%; max-height: 720px; object-fit: contain; }
    .desktop-device { border-radius: 16px; border-top-width: 26px; }
    .phone-device { border-radius: 34px; border-width: 10px; }
    .continuity-link { color: #ff5a5f; text-align: center; display: grid; gap: 6px; }
    .continuity-link span { color: #aeb7c5; font-size: 12px; }
    @media (max-width: 1000px) {
      .capture-grid.two, .continuity-board { grid-template-columns: 1fr; }
      .relationship-grid { grid-template-columns: 1fr; }
      .connector strong { transform: rotate(90deg); }
    }
  </style>
</head>
<body>
  <header>
    <h1>Homepage visual review</h1>
    <p>Revised light and dark candidates. No source is promoted, optimized, or bound to the public website by this gallery.</p>
    <p>Model-family profiles are Crystal Lattice compatibility implementations, not official upstream applications or sessions.</p>
  </header>
  <main>
    ${section("highlight-1", "One workspace for every model family.", themes)}
    ${section("highlight-2", "Replace the parts you disagree with.", relationshipThemes)}
    ${section("highlight-3", "Transparency by design.", transparencyThemes)}
    ${section("highlight-4", "Work from anywhere.", continuityThemes)}
    ${section("highlight-5", "Vibe code—or vibe anything.", vibeThemes)}
    ${section("highlight-6", "Sessions become workspaces.", workspaceThemes)}
  </main>
</body>
</html>`;
}

const copied = copyCaptures();
fs.writeFileSync(path.join(outputRoot, "index.html"), buildHtml(copied));
console.log(path.join(outputRoot, "index.html"));