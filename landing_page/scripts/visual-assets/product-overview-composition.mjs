import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const landingRoot = path.resolve(fileURLToPath(new URL("../../", import.meta.url)));
const repositoryRoot = path.resolve(landingRoot, "..");
const outputDirectory = path.join(landingRoot, "artifacts/product-overview-preview");
const workDirectory = path.join(outputDirectory, ".work");

const themes = {
  light: {
    token: "light",
    suffix: "",
    background: "#f3f4f7",
  },
  dark: {
    token: "dark",
    suffix: "-dark",
    background: "#0b0d10",
  },
};

function runMagick(args) {
  execFileSync("magick", args, {
    cwd: repositoryRoot,
    stdio: "inherit",
  });
}

function requireSource(relativePath) {
  const source = path.join(repositoryRoot, relativePath);
  if (!fs.existsSync(source)) {
    throw new Error(`Missing product overview source: ${relativePath}`);
  }
  return source;
}

function outputFor(id, shape, theme) {
  return path.join(
    outputDirectory,
    `${id}-${shape}${theme.suffix}.webp`,
  );
}

function renderContained({
  source,
  crop,
  width,
  height,
  inset = 40,
  background,
  destination,
  quality = 86,
}) {
  const args = [source];
  if (crop) {
    args.push("-crop", crop, "+repage");
  }
  args.push(
    "-resize", `${width - inset * 2}x${height - inset * 2}`,
    "-gravity", "center",
    "-background", background,
    "-extent", `${width}x${height}`,
    "-strip",
    "-define", "webp:method=6",
    "-quality", String(quality),
    destination,
  );
  runMagick(args);
}

function renderPiece({
  source,
  crop,
  width,
  height,
  background,
  destination,
}) {
  runMagick([
    source,
    "-crop", crop,
    "+repage",
    "-resize", `${width}x${height}`,
    "-gravity", "center",
    "-background", background,
    "-extent", `${width}x${height}`,
    destination,
  ]);
}

function compose({
  width,
  height,
  background,
  pieces,
  destination,
  quality = 86,
}) {
  const args = ["-size", `${width}x${height}`, `xc:${background}`];
  for (const piece of pieces) {
    args.push(
      piece.source,
      "-geometry", `+${piece.x}+${piece.y}`,
      "-composite",
    );
  }
  args.push(
    "-strip",
    "-define", "webp:method=6",
    "-quality", String(quality),
    destination,
  );
  runMagick(args);
}

function renderAgentCompact({ source, theme, destination }) {
  const profiles = path.join(workDirectory, `overview-agent-profiles-${theme.token}.png`);
  const details = path.join(workDirectory, `overview-agent-details-${theme.token}.png`);
  renderPiece({
    source,
    crop: "900x300+20+80",
    width: 900,
    height: 300,
    background: theme.background,
    destination: profiles,
  });
  renderPiece({
    source,
    crop: "450x650+930+80",
    width: 900,
    height: 720,
    background: theme.background,
    destination: details,
  });
  compose({
    width: 1000,
    height: 1120,
    background: theme.background,
    pieces: [
      { source: profiles, x: 50, y: 35 },
      { source: details, x: 50, y: 365 },
    ],
    destination,
  });
}

function renderWorkspaceCompact({ source, theme, destination }) {
  const context = path.join(
    workDirectory,
    `overview-workspace-context-${theme.token}.png`,
  );
  const detail = path.join(
    workDirectory,
    `overview-workspace-detail-${theme.token}.png`,
  );
  renderPiece({
    source,
    crop: "2560x1440+0+0",
    width: 900,
    height: 506,
    background: theme.background,
    destination: context,
  });
  renderPiece({
    source,
    crop: "1500x1050+0+200",
    width: 900,
    height: 630,
    background: theme.background,
    destination: detail,
  });
  compose({
    width: 1000,
    height: 1200,
    background: theme.background,
    pieces: [
      { source: context, x: 50, y: 30 },
      { source: detail, x: 50, y: 550 },
    ],
    destination,
  });
}

function renderCrossDevice({ desktop, mobile, theme, compact, destination }) {
  const desktopPiece = path.join(
    workDirectory,
    `overview-continuity-desktop-${theme.token}-${compact ? "compact" : "wide"}.png`,
  );
  const mobilePiece = path.join(
    workDirectory,
    `overview-continuity-mobile-${theme.token}-${compact ? "compact" : "wide"}.png`,
  );

  if (compact) {
    renderPiece({
      source: desktop,
      crop: "2560x1440+0+0",
      width: 920,
      height: 518,
      background: theme.background,
      destination: desktopPiece,
    });
    renderPiece({
      source: mobile,
      crop: "1000x1750+103+200",
      width: 390,
      height: 728,
      background: theme.background,
      destination: mobilePiece,
    });
    compose({
      width: 1000,
      height: 1250,
      background: theme.background,
      pieces: [
        { source: desktopPiece, x: 40, y: 35 },
        { source: mobilePiece, x: 305, y: 500 },
      ],
      destination,
    });
    return;
  }

  renderPiece({
    source: desktop,
    crop: "2560x1440+0+0",
    width: 1180,
    height: 664,
    background: theme.background,
    destination: desktopPiece,
  });
  renderPiece({
    source: mobile,
    crop: "1000x1750+103+200",
    width: 330,
    height: 616,
    background: theme.background,
    destination: mobilePiece,
  });
  compose({
    width: 1600,
    height: 1000,
    background: theme.background,
    pieces: [
      { source: desktopPiece, x: 40, y: 168 },
      { source: mobilePiece, x: 1230, y: 190 },
    ],
    destination,
  });
}

fs.rmSync(outputDirectory, { recursive: true, force: true });
fs.mkdirSync(outputDirectory, { recursive: true });
fs.mkdirSync(workDirectory, { recursive: true });

for (const theme of Object.values(themes)) {
  const composer = requireSource(
    `mobile/crystal-lattice-control-rn/artifacts/website-visual/composer-overview-${theme.token}.png`,
  );
  const workspace = requireSource(
    `desktop/crystal-lattice-control-desktop-rn/artifacts/website-visual/workspace-${theme.token}.png`,
  );
  const agent = requireSource(
    `landing_page/public/homepage-draft/agent-codex-${theme.token}.webp`,
  );
  const provider = requireSource(
    `landing_page/public/provider-reasoning${theme.suffix}.webp`,
  );
  const desktopContinuity = requireSource(
    `desktop/crystal-lattice-control-desktop-rn/artifacts/website-visual/cross-device-${theme.token}.png`,
  );
  const mobileContinuity = requireSource(
    `mobile/crystal-lattice-control-rn/artifacts/website-visual/hero-${theme.token}.png`,
  );

  for (const shape of ["wide", "compact"]) {
    renderContained({
      source: composer,
      crop: "1206x1447+0+1175",
      width: 1000,
      height: 1200,
      inset: 35,
      background: theme.background,
      destination: outputFor("session-composer", shape, theme),
    });
  }

  renderContained({
    source: workspace,
    width: 1600,
    height: 960,
    inset: 30,
    background: theme.background,
    destination: outputFor("workspace", "wide", theme),
  });
  renderWorkspaceCompact({
    source: workspace,
    theme,
    destination: outputFor("workspace", "compact", theme),
  });

  renderContained({
    source: agent,
    width: 1400,
    height: 980,
    inset: 0,
    background: theme.background,
    destination: outputFor("agent-profile", "wide", theme),
  });
  renderAgentCompact({
    source: agent,
    theme,
    destination: outputFor("agent-profile", "compact", theme),
  });

  for (const shape of ["wide", "compact"]) {
    renderContained({
      source: provider,
      width: 1000,
      height: 1315,
      inset: 0,
      background: theme.background,
      destination: outputFor("provider-controls", shape, theme),
    });
  }

  renderCrossDevice({
    desktop: desktopContinuity,
    mobile: mobileContinuity,
    theme,
    compact: false,
    destination: outputFor("cross-device", "wide", theme),
  });
  renderCrossDevice({
    desktop: desktopContinuity,
    mobile: mobileContinuity,
    theme,
    compact: true,
    destination: outputFor("cross-device", "compact", theme),
  });
}

fs.rmSync(workDirectory, { recursive: true, force: true });

fs.writeFileSync(
  path.join(outputDirectory, "manifest.json"),
  `${JSON.stringify({
    generatedAt: new Date().toISOString(),
    assets: [
      { id: "session-composer", wide: [1000, 1200], compact: [1000, 1200] },
      { id: "workspace", wide: [1600, 960], compact: [1000, 1200] },
      { id: "agent-profile", wide: [1400, 980], compact: [1000, 1120] },
      { id: "provider-controls", wide: [1000, 1315], compact: [1000, 1315] },
      { id: "cross-device", wide: [1600, 1000], compact: [1000, 1250] },
    ],
  }, null, 2)}\n`,
);

console.log(`Generated product overview candidates in ${outputDirectory}`);