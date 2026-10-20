import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const landingRoot = path.resolve(fileURLToPath(new URL("../../", import.meta.url)));
const outputDirectory = path.join(landingRoot, "artifacts/walkthrough-final-preview");
const workDirectory = path.join(outputDirectory, ".work");

const sources = {
  compose: "artifacts/walkthrough-candidates/mobile/composer-active",
  messages: "artifacts/walkthrough-candidates/mobile/message-actions",
  footer: "artifacts/walkthrough-candidates/message-footer",
  actions: "artifacts/walkthrough-candidates/mobile/actions",
  providerSettings: "artifacts/walkthrough-candidates/mobile/provider-settings",
  plugins: "artifacts/walkthrough-candidates/mobile/plugins",
  workspace: "artifacts/walkthrough-candidates/mobile/workspaces-list",
  agent: "public/homepage-draft/agent-codex",
};

const themes = {
  light: {
    suffix: "light",
    outputSuffix: "",
    background: "#f3f4f7",
    card: "#ffffff",
    border: "#c7c7cc",
    focus: "#0a84ff",
    secondary: "#30b956",
    provider: "#af52de",
    plugin: "#ff9500",
  },
  dark: {
    suffix: "dark",
    outputSuffix: "-dark",
    background: "#0b0d10",
    card: "#1c1c1e",
    border: "#55555a",
    focus: "#409cff",
    secondary: "#30d158",
    provider: "#bf5af2",
    plugin: "#ff9f0a",
  },
};

function runMagick(args) {
  execFileSync("magick", args, { cwd: landingRoot, stdio: "inherit" });
}

function sourceFor(prefix, theme, extension = "png") {
  const filename = `${prefix}-${theme.suffix}.${extension}`;
  const source = path.join(landingRoot, filename);
  if (!fs.existsSync(source)) {
    throw new Error(`Missing walkthrough composition source: ${filename}`);
  }
  return source;
}

function resolveColor(theme, color) {
  return theme[color] ?? color;
}

function card({
  name,
  source,
  crop,
  width,
  height,
  theme,
  focusBoxes = [],
  accent,
}) {
  const destination = path.join(workDirectory, `${name}.png`);
  const resizeGeometry = accent ? `${width}x${height}` : `${width}x${height}>`;
  const args = [
    source,
    "-crop", crop,
    "+repage",
    "-resize", resizeGeometry,
    "-gravity", "center",
    "-background", theme.card,
    "-extent", `${width}x${height}`,
  ];

  for (const box of focusBoxes) {
    args.push(
      "-fill", "none",
      "-stroke", resolveColor(theme, box.color ?? "focus"),
      "-strokewidth", String(box.strokeWidth ?? 8),
      "-draw",
      `roundrectangle ${box.x1},${box.y1} ${box.x2},${box.y2} ${box.radius ?? 18},${box.radius ?? 18}`,
    );
  }

  if (accent) {
    args.push(
      "-fill", resolveColor(theme, accent),
      "-stroke", "none",
      "-draw", `rectangle 0,0 ${width},10`,
    );
  }

  args.push(
    "-fill", "none",
    "-stroke", theme.border,
    "-strokewidth", "4",
    "-draw", `rectangle 2,2 ${width - 3},${height - 3}`,
    destination,
  );
  runMagick(args);
  return destination;
}

function connector({
  x1,
  y1,
  x2,
  y2,
  color = "focus",
  arrow = "down",
}) {
  const triangle = arrow === "right"
    ? `polygon ${x2 - 18},${y2 - 13} ${x2 - 18},${y2 + 13} ${x2},${y2}`
    : `polygon ${x2 - 13},${y2 - 18} ${x2 + 13},${y2 - 18} ${x2},${y2}`;
  return [
    {
      fill: "none",
      stroke: color,
      strokeWidth: 7,
      command: `line ${x1},${y1} ${x2},${y2}`,
    },
    {
      fill: color,
      stroke: color,
      strokeWidth: 1,
      command: triangle,
    },
  ];
}

function ellipsis({ x, y, color = "border", radius = 4 }) {
  return [-12, 0, 12].map(offset => ({
    fill: color,
    stroke: "none",
    strokeWidth: 0,
    command: `circle ${x + offset},${y} ${x + offset + radius},${y}`,
  }));
}

function compose({ width, height, theme, parts, draws = [], destination }) {
  const args = ["-size", `${width}x${height}`, `xc:${theme.background}`];
  for (const part of parts) {
    args.push(part.source, "-geometry", `+${part.x}+${part.y}`, "-composite");
  }
  for (const draw of draws) {
    args.push(
      "-fill", draw.fill === "none" ? "none" : resolveColor(theme, draw.fill),
      "-stroke", draw.stroke === "none" ? "none" : resolveColor(theme, draw.stroke),
      "-strokewidth", String(draw.strokeWidth ?? 1),
      "-draw", draw.command,
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

function output(name, shape, theme) {
  return path.join(
    outputDirectory,
    `${name}-${shape}${theme.outputSuffix}.webp`,
  );
}

function buildCompose(theme) {
  const source = sourceFor(sources.compose, theme);

  const wideContext = card({
    name: `compose-${theme.suffix}-wide-context`,
    source,
    crop: "1206x1750+0+250",
    width: 500,
    height: 900,
    theme,
    focusBoxes: [
      { x1: 50, y1: 255, x2: 450, y2: 800, color: "focus" },
    ],
  });
  const widePopup = card({
    name: `compose-${theme.suffix}-wide-popup`,
    source,
    crop: "966x780+120+1200",
    width: 820,
    height: 662,
    theme,
    accent: "focus",
  });
  const wideComposer = card({
    name: `compose-${theme.suffix}-wide-composer`,
    source,
    crop: "1120x400+43+2180",
    width: 820,
    height: 293,
    theme,
    accent: "secondary",
  });
  compose({
    width: 1800,
    height: 1013,
    theme,
    parts: [
      { source: wideContext, x: 35, y: 55 },
      { source: widePopup, x: 625, y: 45 },
      { source: wideComposer, x: 625, y: 690 },
    ],
    draws: [
      ...connector({
        x1: 485,
        y1: 470,
        x2: 625,
        y2: 470,
        color: "focus",
        arrow: "right",
      }),
    ],
    destination: output("compose", "wide", theme),
  });

  const compactContext = card({
    name: `compose-${theme.suffix}-compact-context`,
    source,
    crop: "1206x720+0+400",
    width: 900,
    height: 280,
    theme,
    focusBoxes: [
      { x1: 275, y1: 92, x2: 625, y2: 273, color: "focus" },
    ],
  });
  const compactPopup = card({
    name: `compose-${theme.suffix}-compact-popup`,
    source,
    crop: "966x780+120+1200",
    width: 900,
    height: 727,
    theme,
    accent: "focus",
  });
  const compactComposer = card({
    name: `compose-${theme.suffix}-compact-composer`,
    source,
    crop: "1120x400+43+2180",
    width: 900,
    height: 322,
    theme,
    accent: "secondary",
  });
  compose({
    width: 1000,
    height: 1500,
    theme,
    parts: [
      { source: compactContext, x: 50, y: 35 },
      { source: compactPopup, x: 50, y: 375 },
      { source: compactComposer, x: 50, y: 1140 },
    ],
    draws: [
      ...connector({
        x1: 500,
        y1: 308,
        x2: 500,
        y2: 375,
        color: "focus",
      }),
    ],
    destination: output("compose", "compact", theme),
  });
}

function buildMessages(theme) {
  const source = sourceFor(sources.messages, theme);
  const footer = sourceFor(sources.footer, theme, "webp");

  const wideContext = card({
    name: `messages-${theme.suffix}-wide-context`,
    source,
    crop: "1206x1730+0+250",
    width: 400,
    height: 900,
    theme,
    focusBoxes: [
      { x1: 40, y1: 250, x2: 360, y2: 805, color: "focus" },
    ],
  });
  const wideActions = card({
    name: `messages-${theme.suffix}-wide-actions`,
    source,
    crop: "966x1370+120+620",
    width: 650,
    height: 922,
    theme,
    accent: "focus",
  });
  const wideUsage = card({
    name: `messages-${theme.suffix}-wide-usage`,
    source: footer,
    crop: "680x105+60+450",
    width: 620,
    height: 96,
    theme,
    accent: "secondary",
  });
  const wideCost = card({
    name: `messages-${theme.suffix}-wide-cost`,
    source: footer,
    crop: "530x48+60+565",
    width: 620,
    height: 80,
    theme,
    accent: "secondary",
  });
  const wideOutput = card({
    name: `messages-${theme.suffix}-wide-output`,
    source: footer,
    crop: "500x55+460+655",
    width: 620,
    height: 90,
    theme,
    accent: "secondary",
  });
  compose({
    width: 1800,
    height: 1013,
    theme,
    parts: [
      { source: wideContext, x: 20, y: 55 },
      { source: wideActions, x: 500, y: 45 },
      { source: wideUsage, x: 1170, y: 335 },
      { source: wideCost, x: 1170, y: 465 },
      { source: wideOutput, x: 1170, y: 575 },
    ],
    draws: [
      ...connector({
        x1: 385,
        y1: 500,
        x2: 500,
        y2: 500,
        color: "focus",
        arrow: "right",
      }),
    ],
    destination: output("messages", "wide", theme),
  });

  const compactContext = card({
    name: `messages-${theme.suffix}-compact-context`,
    source,
    crop: "1206x720+0+400",
    width: 900,
    height: 260,
    theme,
    focusBoxes: [
      { x1: 275, y1: 87, x2: 625, y2: 253, color: "focus" },
    ],
  });
  const compactModify = card({
    name: `messages-${theme.suffix}-compact-modify`,
    source,
    crop: "966x130+120+820",
    width: 900,
    height: 121,
    theme,
  });
  const compactFork = card({
    name: `messages-${theme.suffix}-compact-fork`,
    source,
    crop: "966x140+120+1230",
    width: 900,
    height: 130,
    theme,
  });
  const compactSummarize = card({
    name: `messages-${theme.suffix}-compact-summarize`,
    source,
    crop: "966x170+120+1365",
    width: 900,
    height: 158,
    theme,
  });
  const compactCompaction = card({
    name: `messages-${theme.suffix}-compact-compaction`,
    source,
    crop: "966x145+120+1525",
    width: 900,
    height: 135,
    theme,
  });
  const compactDeleteFrom = card({
    name: `messages-${theme.suffix}-compact-delete-from`,
    source,
    crop: "966x145+120+1810",
    width: 900,
    height: 135,
    theme,
  });
  const compactUsage = card({
    name: `messages-${theme.suffix}-compact-usage`,
    source: footer,
    crop: "680x105+60+450",
    width: 900,
    height: 139,
    theme,
    accent: "secondary",
  });
  const compactCost = card({
    name: `messages-${theme.suffix}-compact-cost`,
    source: footer,
    crop: "530x50+60+555",
    width: 900,
    height: 100,
    theme,
    accent: "secondary",
  });
  const compactOutput = card({
    name: `messages-${theme.suffix}-compact-output`,
    source: footer,
    crop: "500x55+460+655",
    width: 900,
    height: 115,
    theme,
    accent: "secondary",
  });
  compose({
    width: 1000,
    height: 1570,
    theme,
    parts: [
      { source: compactContext, x: 50, y: 35 },
      { source: compactModify, x: 50, y: 360 },
      { source: compactFork, x: 50, y: 495 },
      { source: compactSummarize, x: 50, y: 640 },
      { source: compactCompaction, x: 50, y: 813 },
      { source: compactDeleteFrom, x: 50, y: 963 },
      { source: compactUsage, x: 50, y: 1140 },
      { source: compactCost, x: 50, y: 1310 },
      { source: compactOutput, x: 50, y: 1425 },
    ],
    draws: [
      ...connector({
        x1: 500,
        y1: 288,
        x2: 500,
        y2: 360,
        color: "focus",
      }),
      ...ellipsis({ x: 500, y: 488 }),
      ...ellipsis({ x: 500, y: 632 }),
      ...ellipsis({ x: 500, y: 805 }),
      ...ellipsis({ x: 500, y: 955 }),
    ],
    destination: output("messages", "compact", theme),
  });
}

function buildSessionActions(theme) {
  const source = sourceFor(sources.actions, theme);

  const wideContext = card({
    name: `session-actions-${theme.suffix}-wide-context`,
    source,
    crop: "1096x2080+50+250",
    width: 450,
    height: 900,
    theme,
    focusBoxes: [
      { x1: 20, y1: 20, x2: 430, y2: 880, color: "focus" },
    ],
  });
  const wideAgent = card({
    name: `session-actions-${theme.suffix}-wide-agent`,
    source,
    crop: "1040x190+83+700",
    width: 800,
    height: 146,
    theme,
    accent: "focus",
  });
  const wideSettings = card({
    name: `session-actions-${theme.suffix}-wide-settings`,
    source,
    crop: "1040x400+83+1370",
    width: 800,
    height: 308,
    theme,
    accent: "focus",
  });
  const wideTitles = card({
    name: `session-actions-${theme.suffix}-wide-titles`,
    source,
    crop: "1040x440+83+1900",
    width: 800,
    height: 338,
    theme,
    accent: "focus",
  });
  compose({
    width: 1800,
    height: 1013,
    theme,
    parts: [
      { source: wideContext, x: 35, y: 55 },
      { source: wideAgent, x: 650, y: 35 },
      { source: wideSettings, x: 650, y: 240 },
      { source: wideTitles, x: 650, y: 610 },
    ],
    draws: [
      ...connector({
        x1: 450,
        y1: 500,
        x2: 650,
        y2: 500,
        color: "focus",
        arrow: "right",
      }),
    ],
    destination: output("session-actions", "wide", theme),
  });

  const compactContext = card({
    name: `session-actions-${theme.suffix}-compact-context`,
    source,
    crop: "1096x900+50+250",
    width: 900,
    height: 260,
    theme,
    focusBoxes: [
      { x1: 293, y1: 5, x2: 607, y2: 253, color: "focus" },
    ],
  });
  const compactAgent = card({
    name: `session-actions-${theme.suffix}-compact-agent`,
    source,
    crop: "1040x190+83+700",
    width: 900,
    height: 164,
    theme,
    accent: "focus",
  });
  const compactActions = card({
    name: `session-actions-${theme.suffix}-compact-actions`,
    source,
    crop: "1040x980+83+1365",
    width: 900,
    height: 848,
    theme,
    accent: "focus",
  });
  compose({
    width: 1000,
    height: 1450,
    theme,
    parts: [
      { source: compactContext, x: 50, y: 35 },
      { source: compactAgent, x: 50, y: 365 },
      { source: compactActions, x: 50, y: 560 },
    ],
    draws: [
      ...connector({
        x1: 500,
        y1: 288,
        x2: 500,
        y2: 365,
        color: "focus",
      }),
      ...ellipsis({ x: 500, y: 544 }),
    ],
    destination: output("session-actions", "compact", theme),
  });
}

function buildSettings(theme) {
  const agent = sourceFor(sources.agent, theme, "webp");
  const provider = sourceFor(sources.providerSettings, theme);
  const plugins = sourceFor(sources.plugins, theme);

  const wideContext = card({
    name: `settings-${theme.suffix}-wide-context`,
    source: agent,
    crop: "1400x760+0+50",
    width: 550,
    height: 700,
    theme,
    focusBoxes: [
      { x1: 18, y1: 218, x2: 365, y2: 270, color: "focus", strokeWidth: 6 },
      { x1: 370, y1: 310, x2: 535, y2: 440, color: "secondary", strokeWidth: 6 },
    ],
  });
  const wideProfile = card({
    name: `settings-${theme.suffix}-wide-profile`,
    source: agent,
    crop: "440x570+930+90",
    width: 500,
    height: 648,
    theme,
    accent: "secondary",
  });
  const wideProvider = card({
    name: `settings-${theme.suffix}-wide-provider`,
    source: provider,
    crop: "1040x790+83+930",
    width: 550,
    height: 407,
    theme,
    accent: "provider",
  });
  const widePlugins = card({
    name: `settings-${theme.suffix}-wide-plugins`,
    source: plugins,
    crop: "1040x1050+83+680",
    width: 550,
    height: 555,
    theme,
    accent: "plugin",
  });
  compose({
    width: 1800,
    height: 1013,
    theme,
    parts: [
      { source: wideContext, x: 25, y: 155 },
      { source: wideProfile, x: 620, y: 180 },
      { source: wideProvider, x: 1200, y: 25 },
      { source: widePlugins, x: 1200, y: 450 },
    ],
    destination: output("session-settings", "wide", theme),
  });

  const compactProfile = card({
    name: `settings-${theme.suffix}-compact-profile`,
    source: agent,
    crop: "720x120+20+100",
    width: 900,
    height: 150,
    theme,
    accent: "focus",
  });
  const compactTools = card({
    name: `settings-${theme.suffix}-compact-tools`,
    source: agent,
    crop: "700x260+700+390",
    width: 900,
    height: 334,
    theme,
    accent: "secondary",
  });
  const compactProvider = card({
    name: `settings-${theme.suffix}-compact-provider`,
    source: provider,
    crop: "1040x400+83+1050",
    width: 900,
    height: 346,
    theme,
    accent: "provider",
  });
  const compactPlugins = card({
    name: `settings-${theme.suffix}-compact-plugins`,
    source: plugins,
    crop: "1040x510+83+1040",
    width: 900,
    height: 441,
    theme,
    accent: "plugin",
  });
  compose({
    width: 1000,
    height: 1450,
    theme,
    parts: [
      { source: compactProfile, x: 50, y: 35 },
      { source: compactTools, x: 50, y: 220 },
      { source: compactProvider, x: 50, y: 590 },
      { source: compactPlugins, x: 50, y: 970 },
    ],
    destination: output("session-settings", "compact", theme),
  });
}

function buildWorkspace(theme) {
  const source = sourceFor(sources.workspace, theme);

  const wideContext = card({
    name: `workspace-${theme.suffix}-wide-context`,
    source,
    crop: "1206x1780+0+320",
    width: 600,
    height: 900,
    theme,
    focusBoxes: [
      { x1: 5, y1: 5, x2: 595, y2: 290, color: "focus", strokeWidth: 7 },
    ],
  });
  const wideRow = card({
    name: `workspace-${theme.suffix}-wide-row`,
    source,
    crop: "1206x590+0+320",
    width: 900,
    height: 440,
    theme,
    accent: "focus",
  });
  compose({
    width: 1800,
    height: 1013,
    theme,
    parts: [
      { source: wideContext, x: 40, y: 55 },
      { source: wideRow, x: 820, y: 285 },
    ],
    draws: [
      ...connector({
        x1: 610,
        y1: 360,
        x2: 820,
        y2: 360,
        color: "focus",
        arrow: "right",
      }),
    ],
    destination: output("workspace", "wide", theme),
  });

  const compactContext = card({
    name: `workspace-${theme.suffix}-compact-context`,
    source,
    crop: "1206x1780+0+320",
    width: 900,
    height: 650,
    theme,
    focusBoxes: [
      { x1: 235, y1: 5, x2: 665, y2: 215, color: "focus", strokeWidth: 7 },
    ],
  });
  const compactTitle = card({
    name: `workspace-${theme.suffix}-compact-title`,
    source,
    crop: "1206x180+0+340",
    width: 900,
    height: 134,
    theme,
    accent: "focus",
  });
  const compactStatus = card({
    name: `workspace-${theme.suffix}-compact-status`,
    source,
    crop: "850x340+0+540",
    width: 900,
    height: 360,
    theme,
    accent: "focus",
  });
  compose({
    width: 1000,
    height: 1370,
    theme,
    parts: [
      { source: compactContext, x: 50, y: 35 },
      { source: compactTitle, x: 50, y: 790 },
      { source: compactStatus, x: 50, y: 950 },
    ],
    draws: [
      ...connector({
        x1: 500,
        y1: 678,
        x2: 500,
        y2: 790,
        color: "focus",
      }),
    ],
    destination: output("workspace", "compact", theme),
  });
}

fs.rmSync(workDirectory, { recursive: true, force: true });
fs.mkdirSync(workDirectory, { recursive: true });

for (const theme of Object.values(themes)) {
  buildCompose(theme);
  buildMessages(theme);
  buildSessionActions(theme);
  buildSettings(theme);
  buildWorkspace(theme);
}

fs.rmSync(workDirectory, { recursive: true, force: true });
console.log(`Generated final walkthrough review assets in ${outputDirectory}`);