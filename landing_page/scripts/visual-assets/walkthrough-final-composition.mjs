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
    border: "#d1d1d6",
    focus: "#0a84ff",
  },
  dark: {
    suffix: "dark",
    outputSuffix: "-dark",
    background: "#0b0d10",
    card: "#1c1c1e",
    border: "#48484a",
    focus: "#409cff",
  },
};

function runMagick(args) {
  execFileSync("magick", args, { cwd: landingRoot, stdio: "inherit" });
}

function sourceFor(prefix, theme, extension = "png") {
  const filename = prefix === sources.agent
    ? `${prefix}-${theme.suffix}.${extension}`
    : `${prefix}-${theme.suffix}.${extension}`;
  const source = path.join(landingRoot, filename);
  if (!fs.existsSync(source)) {
    throw new Error(`Missing walkthrough composition source: ${filename}`);
  }
  return source;
}

function card({
  name,
  source,
  crop,
  width,
  height,
  theme,
  focus = false,
}) {
  const destination = path.join(workDirectory, `${name}.png`);
  runMagick([
    source,
    "-crop", crop,
    "+repage",
    "-resize", `${width}x${height}>`,
    "-gravity", "center",
    "-background", theme.card,
    "-extent", `${width}x${height}`,
    "-bordercolor", focus ? theme.focus : theme.border,
    "-border", "2",
    destination,
  ]);
  return destination;
}

function compose({ width, height, theme, parts, destination }) {
  const args = ["-size", `${width}x${height}`, `xc:${theme.background}`];
  for (const part of parts) {
    args.push(part.source, "-geometry", `+${part.x}+${part.y}`, "-composite");
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
    crop: "1206x1480+0+260",
    width: 470,
    height: 650,
    theme,
  });
  const widePopup = card({
    name: `compose-${theme.suffix}-wide-popup`,
    source,
    crop: "860x1260+173+720",
    width: 650,
    height: 820,
    theme,
    focus: true,
  });
  const wideComposer = card({
    name: `compose-${theme.suffix}-wide-composer`,
    source,
    crop: "1120x360+43+2200",
    width: 720,
    height: 340,
    theme,
    focus: true,
  });
  compose({
    width: 1800,
    height: 1013,
    theme,
    parts: [
      { source: wideContext, x: 45, y: 180 },
      { source: widePopup, x: 485, y: 70 },
      { source: wideComposer, x: 1035, y: 575 },
    ],
    destination: output("compose", "wide", theme),
  });

  const compactPopup = card({
    name: `compose-${theme.suffix}-compact-popup`,
    source,
    crop: "1000x1320+103+670",
    width: 900,
    height: 760,
    theme,
    focus: true,
  });
  const compactComposer = card({
    name: `compose-${theme.suffix}-compact-composer`,
    source,
    crop: "1120x380+43+2170",
    width: 900,
    height: 370,
    theme,
    focus: true,
  });
  compose({
    width: 1000,
    height: 1250,
    theme,
    parts: [
      { source: compactPopup, x: 50, y: 35 },
      { source: compactComposer, x: 50, y: 835 },
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
    crop: "1206x1520+0+300",
    width: 660,
    height: 900,
    theme,
  });
  const wideActions = card({
    name: `messages-${theme.suffix}-wide-actions`,
    source,
    crop: "1040x1370+83+620",
    width: 750,
    height: 860,
    theme,
    focus: true,
  });
  const wideFooter = card({
    name: `messages-${theme.suffix}-wide-footer`,
    source: footer,
    crop: "1200x610+0+290",
    width: 750,
    height: 380,
    theme,
    focus: true,
  });
  compose({
    width: 1800,
    height: 1013,
    theme,
    parts: [
      { source: wideContext, x: 45, y: 55 },
      { source: wideActions, x: 620, y: 35 },
      { source: wideFooter, x: 1015, y: 600 },
    ],
    destination: output("messages", "wide", theme),
  });

  const compactActions = card({
    name: `messages-${theme.suffix}-compact-actions`,
    source,
    crop: "1040x1370+83+620",
    width: 900,
    height: 745,
    theme,
    focus: true,
  });
  const compactFooter = card({
    name: `messages-${theme.suffix}-compact-footer`,
    source: footer,
    crop: "1200x610+0+290",
    width: 900,
    height: 420,
    theme,
    focus: true,
  });
  compose({
    width: 1000,
    height: 1250,
    theme,
    parts: [
      { source: compactActions, x: 50, y: 35 },
      { source: compactFooter, x: 50, y: 790 },
    ],
    destination: output("messages", "compact", theme),
  });
}

function buildSessionActions(theme) {
  const source = sourceFor(sources.actions, theme);
  const wideContext = card({
    name: `session-actions-${theme.suffix}-wide-context`,
    source,
    crop: "1206x2250+0+250",
    width: 470,
    height: 900,
    theme,
  });
  const wideActions = card({
    name: `session-actions-${theme.suffix}-wide-actions`,
    source,
    crop: "1040x1700+83+280",
    width: 980,
    height: 900,
    theme,
    focus: true,
  });
  compose({
    width: 1800,
    height: 1013,
    theme,
    parts: [
      { source: wideContext, x: 80, y: 55 },
      { source: wideActions, x: 600, y: 35 },
    ],
    destination: output("session-actions", "wide", theme),
  });

  const compactContext = card({
    name: `session-actions-${theme.suffix}-compact-context`,
    source,
    crop: "1206x2050+0+330",
    width: 470,
    height: 1050,
    theme,
  });
  const compactActions = card({
    name: `session-actions-${theme.suffix}-compact-actions`,
    source,
    crop: "1040x1600+83+280",
    width: 900,
    height: 1150,
    theme,
    focus: true,
  });
  compose({
    width: 1000,
    height: 1250,
    theme,
    parts: [
      { source: compactContext, x: 20, y: 115 },
      { source: compactActions, x: 75, y: 35 },
    ],
    destination: output("session-actions", "compact", theme),
  });
}

function buildSettings(theme) {
  const agent = sourceFor(sources.agent, theme, "webp");
  const provider = sourceFor(sources.providerSettings, theme);
  const plugins = sourceFor(sources.plugins, theme);
  const wideAgent = card({
    name: `settings-${theme.suffix}-wide-agent`,
    source: agent,
    crop: "1400x980+0+0",
    width: 1080,
    height: 760,
    theme,
  });
  const wideProvider = card({
    name: `settings-${theme.suffix}-wide-provider`,
    source: provider,
    crop: "1120x900+43+800",
    width: 650,
    height: 410,
    theme,
    focus: true,
  });
  const widePlugins = card({
    name: `settings-${theme.suffix}-wide-plugins`,
    source: plugins,
    crop: "1120x1000+43+680",
    width: 650,
    height: 440,
    theme,
    focus: true,
  });
  compose({
    width: 1800,
    height: 1013,
    theme,
    parts: [
      { source: wideAgent, x: 35, y: 125 },
      { source: wideProvider, x: 1100, y: 35 },
      { source: widePlugins, x: 1100, y: 525 },
    ],
    destination: output("session-settings", "wide", theme),
  });

  const compactAgent = card({
    name: `settings-${theme.suffix}-compact-agent`,
    source: agent,
    crop: "600x110+20+120",
    width: 900,
    height: 230,
    theme,
  });
  const compactProvider = card({
    name: `settings-${theme.suffix}-compact-provider`,
    source: provider,
    crop: "1120x900+43+800",
    width: 900,
    height: 430,
    theme,
    focus: true,
  });
  const compactPlugins = card({
    name: `settings-${theme.suffix}-compact-plugins`,
    source: plugins,
    crop: "1120x1000+43+680",
    width: 900,
    height: 480,
    theme,
    focus: true,
  });
  compose({
    width: 1000,
    height: 1250,
    theme,
    parts: [
      { source: compactAgent, x: 50, y: 25 },
      { source: compactProvider, x: 50, y: 300 },
      { source: compactPlugins, x: 50, y: 750 },
    ],
    destination: output("session-settings", "compact", theme),
  });
}

function buildWorkspace(theme) {
  const source = sourceFor(sources.workspace, theme);
  const wideContext = card({
    name: `workspace-${theme.suffix}-wide-context`,
    source,
    crop: "1206x1900+0+240",
    width: 650,
    height: 900,
    theme,
  });
  const wideRows = card({
    name: `workspace-${theme.suffix}-wide-rows`,
    source,
    crop: "1120x1500+43+350",
    width: 1020,
    height: 900,
    theme,
    focus: true,
  });
  compose({
    width: 1800,
    height: 1013,
    theme,
    parts: [
      { source: wideContext, x: 45, y: 55 },
      { source: wideRows, x: 710, y: 35 },
    ],
    destination: output("workspace", "wide", theme),
  });

  const compactRows = card({
    name: `workspace-${theme.suffix}-compact-rows`,
    source,
    crop: "1206x1650+0+260",
    width: 900,
    height: 1120,
    theme,
    focus: true,
  });
  compose({
    width: 1000,
    height: 1250,
    theme,
    parts: [
      { source: compactRows, x: 50, y: 65 },
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