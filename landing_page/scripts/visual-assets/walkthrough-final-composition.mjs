import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const landingRoot = path.resolve(fileURLToPath(new URL("../../", import.meta.url)));
const repositoryRoot = path.resolve(landingRoot, "..");
const outputDirectory = path.join(landingRoot, "artifacts/walkthrough-final-preview");
const workDirectory = path.join(outputDirectory, ".work");

const themes = {
  light: {
    token: "light",
    outputSuffix: "",
    background: "#f3f4f7",
  },
  dark: {
    token: "dark",
    outputSuffix: "-dark",
    background: "#0b0d10",
  },
};

const sources = {
  conversation:
    "landing_page/artifacts/walkthrough-candidates/mobile/hero-{theme}.png",
  composer:
    "landing_page/artifacts/walkthrough-candidates/mobile/composer-active-{theme}.png",
  messageActions:
    "landing_page/artifacts/walkthrough-candidates/mobile/message-actions-{theme}.png",
  messageFooter:
    "landing_page/artifacts/walkthrough-candidates/message-footer-{theme}.webp",
  sessionActions:
    "landing_page/artifacts/walkthrough-candidates/mobile/actions-{theme}.png",
  agent:
    "landing_page/public/homepage-draft/agent-codex-{theme}.webp",
  providerSettings:
    "landing_page/artifacts/walkthrough-candidates/mobile/provider-settings-{theme}.png",
  plugins:
    "landing_page/artifacts/walkthrough-candidates/mobile/plugins-{theme}.png",
  workspace:
    "landing_page/artifacts/walkthrough-candidates/mobile/workspaces-list-{theme}.png",
  requestStatus:
    "landing_page/artifacts/walkthrough-candidates/request-status-{theme}.webp",
  desktopSessions:
    "desktop/crystal-lattice-control-desktop-rn/artifacts/website-proof-batch/session-list-{theme}-window.png",
  mobileConnections:
    "landing_page/artifacts/walkthrough-candidates/mobile/connections-{theme}.png",
};

const frames = [
  {
    id: "compose-controls",
    source: sources.conversation,
    crop: "1100x1150+53+260",
    compactHeight: 1100,
  },
  {
    id: "compose-running",
    source: sources.composer,
    crop: "1000x1060+100+500",
    compactHeight: 1050,
  },
  {
    id: "message-metadata",
    source: sources.messageFooter,
    crop: "1080x520+60+270",
    compactHeight: 720,
  },
  {
    id: "message-actions",
    source: sources.messageActions,
    crop: "1000x1350+100+480",
    compactHeight: 1100,
  },
  {
    id: "session-controls",
    source: sources.sessionActions,
    crop: "1100x1550+53+190",
    compactHeight: 1160,
  },
  {
    id: "session-pinning",
    source: sources.sessionActions,
    crop: "1100x820+53+250",
    compactHeight: 760,
  },
  {
    id: "agent-profile",
    source: sources.agent,
    crop: "1400x980+0+0",
    compactHeight: 1050,
  },
  {
    id: "provider-settings",
    source: sources.providerSettings,
    crop: "1100x840+53+680",
    compactHeight: 760,
  },
  {
    id: "session-plugins",
    source: sources.plugins,
    crop: "1100x1030+53+500",
    compactHeight: 950,
  },
  {
    id: "workspace-sessions",
    source: sources.workspace,
    crop: "1206x1300+0+250",
    compactHeight: 1050,
  },
  {
    id: "workspace-status",
    source: sources.requestStatus,
    crop: "856x880+172+10",
    compactHeight: 900,
  },
  {
    id: "desktop-connection",
    source: sources.desktopSessions,
    crop: "980x280+0+50",
    compactHeight: 400,
  },
  {
    id: "mobile-connection",
    source: sources.mobileConnections,
    crop: "1100x1700+53+250",
    compactHeight: 1200,
  },
];

function runMagick(args) {
  execFileSync("magick", args, {
    cwd: repositoryRoot,
    stdio: "inherit",
  });
}

function sourceFor(template, theme) {
  const relativePath = template.replace("{theme}", theme.token);
  const source = path.join(repositoryRoot, relativePath);
  if (!fs.existsSync(source)) {
    throw new Error(`Missing walkthrough composition source: ${relativePath}`);
  }
  return source;
}

function outputFor(frame, shape, theme) {
  return path.join(
    outputDirectory,
    `${frame.id}-${shape}${theme.outputSuffix}.webp`,
  );
}

function renderFrame({
  source,
  crop,
  width,
  height,
  theme,
  destination,
}) {
  const horizontalPadding = width >= 1400 ? 80 : 40;
  const verticalPadding = width >= 1400 ? 60 : 36;
  runMagick([
    source,
    "-crop", crop,
    "+repage",
    "-resize", `${width - horizontalPadding}x${height - verticalPadding}`,
    "-gravity", "center",
    "-background", theme.background,
    "-extent", `${width}x${height}`,
    "-strip",
    "-define", "webp:method=6",
    "-quality", "92",
    destination,
  ]);
}

function renderPiece({
  source,
  crop,
  width,
  height,
  theme,
  destination,
}) {
  runMagick([
    source,
    "-crop", crop,
    "+repage",
    "-resize", `${width}x${height}`,
    "-gravity", "center",
    "-background", theme.background,
    "-extent", `${width}x${height}`,
    destination,
  ]);
}

function composePieces({
  width,
  height,
  theme,
  pieces,
  destination,
}) {
  const args = ["-size", `${width}x${height}`, `xc:${theme.background}`];
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
    "-quality", "92",
    destination,
  );
  runMagick(args);
}

function renderAgentCompact({ source, theme, destination }) {
  const profile = path.join(workDirectory, `agent-profile-${theme.token}.png`);
  const details = path.join(workDirectory, `agent-details-${theme.token}.png`);
  renderPiece({
    source,
    crop: "900x360+20+80",
    width: 900,
    height: 330,
    theme,
    destination: profile,
  });
  renderPiece({
    source,
    crop: "450x650+930+80",
    width: 900,
    height: 650,
    theme,
    destination: details,
  });
  composePieces({
    width: 1000,
    height: 1050,
    theme,
    pieces: [
      { source: profile, x: 50, y: 35 },
      { source: details, x: 50, y: 385 },
    ],
    destination,
  });
}

function renderComposeFrame({ source, theme, destination, compact }) {
  const context = path.join(
    workDirectory,
    `compose-context-${theme.token}-${compact ? "compact" : "wide"}.png`,
  );
  const composer = path.join(
    workDirectory,
    `compose-field-${theme.token}-${compact ? "compact" : "wide"}.png`,
  );
  if (compact) {
    renderPiece({
      source,
      crop: "1100x1150+53+260",
      width: 900,
      height: 680,
      theme,
      destination: context,
    });
    renderPiece({
      source,
      crop: "1100x430+53+2160",
      width: 900,
      height: 350,
      theme,
      destination: composer,
    });
    composePieces({
      width: 1000,
      height: 1100,
      theme,
      pieces: [
        { source: context, x: 50, y: 35 },
        { source: composer, x: 50, y: 735 },
      ],
      destination,
    });
    return;
  }

  renderPiece({
    source,
    crop: "1100x1150+53+260",
    width: 720,
    height: 900,
    theme,
    destination: context,
  });
  renderPiece({
    source,
    crop: "1100x430+53+2160",
    width: 760,
    height: 400,
    theme,
    destination: composer,
  });
  composePieces({
    width: 1600,
    height: 1000,
    theme,
    pieces: [
      { source: context, x: 40, y: 50 },
      { source: composer, x: 800, y: 300 },
    ],
    destination,
  });
}

function renderMetadataCompact({ source, theme, destination }) {
  const response = path.join(workDirectory, `metadata-response-${theme.token}.png`);
  const usage = path.join(workDirectory, `metadata-usage-${theme.token}.png`);
  const cost = path.join(workDirectory, `metadata-cost-${theme.token}.png`);
  const output = path.join(workDirectory, `metadata-output-${theme.token}.png`);
  renderPiece({
    source,
    crop: "1040x220+80+230",
    width: 900,
    height: 190,
    theme,
    destination: response,
  });
  renderPiece({
    source,
    crop: "680x105+60+450",
    width: 900,
    height: 139,
    theme,
    destination: usage,
  });
  renderPiece({
    source,
    crop: "530x50+60+555",
    width: 900,
    height: 90,
    theme,
    destination: cost,
  });
  renderPiece({
    source,
    crop: "500x55+460+655",
    width: 900,
    height: 100,
    theme,
    destination: output,
  });
  composePieces({
    width: 1000,
    height: 720,
    theme,
    pieces: [
      { source: response, x: 50, y: 35 },
      { source: usage, x: 50, y: 260 },
      { source: cost, x: 50, y: 435 },
      { source: output, x: 50, y: 560 },
    ],
    destination,
  });
}

fs.rmSync(outputDirectory, { recursive: true, force: true });
fs.mkdirSync(outputDirectory, { recursive: true });
fs.mkdirSync(workDirectory, { recursive: true });

for (const theme of Object.values(themes)) {
  for (const frame of frames) {
    const source = sourceFor(frame.source, theme);
    const wideDestination = outputFor(frame, "wide", theme);
    if (frame.id === "compose-controls") {
      renderComposeFrame({
        source,
        theme,
        destination: wideDestination,
        compact: false,
      });
    } else {
      renderFrame({
        source,
        crop: frame.crop,
        width: 1600,
        height: 1000,
        theme,
        destination: wideDestination,
      });
    }
    const compactDestination = outputFor(frame, "compact", theme);
    if (frame.id === "compose-controls") {
      renderComposeFrame({
        source,
        theme,
        destination: compactDestination,
        compact: true,
      });
    } else if (frame.id === "agent-profile") {
      renderAgentCompact({
        source,
        theme,
        destination: compactDestination,
      });
    } else if (frame.id === "message-metadata") {
      renderMetadataCompact({
        source,
        theme,
        destination: compactDestination,
      });
    } else {
      renderFrame({
        source,
        crop: frame.crop,
        width: 1000,
        height: frame.compactHeight,
        theme,
        destination: compactDestination,
      });
    }
  }
}

fs.rmSync(workDirectory, { recursive: true, force: true });

fs.writeFileSync(
  path.join(outputDirectory, "manifest.json"),
  `${JSON.stringify({
    generatedAt: new Date().toISOString(),
    frames: frames.map(frame => ({
      id: frame.id,
      width: 1600,
      height: 1000,
      widthCompact: 1000,
      heightCompact: frame.compactHeight,
    })),
  }, null, 2)}\n`,
);

console.log(
  `Generated ${frames.length} responsive walkthrough frames in ${outputDirectory}`,
);