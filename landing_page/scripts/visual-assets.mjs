import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

import yaml from "js-yaml";

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const landingRoot = path.resolve(scriptDirectory, "..");
const repositoryRoot = path.resolve(landingRoot, "..");
const manifestPath = path.join(
  landingRoot,
  "research",
  "025-current-visual-baseline-and-asset-pipeline",
  "visual-manifest.yaml",
);
const generationRoot = path.join(
  landingRoot,
  "artifacts",
  "research",
  "025-current-visual-baseline-and-asset-pipeline",
  "asset-generation",
);

const command = process.argv[2] ?? "check";
if (!["check", "inspect", "update"].includes(command)) {
  throw new Error(
    "Usage: node scripts/visual-assets.mjs <check|inspect|update>",
  );
}

function run(commandName, args, options = {}) {
  const result = spawnSync(commandName, args, {
    cwd: options.cwd ?? repositoryRoot,
    encoding: options.binary ? null : "utf8",
    maxBuffer: 64 * 1024 * 1024,
  });
  if (result.status !== 0) {
    const stderr = Buffer.isBuffer(result.stderr)
      ? result.stderr.toString("utf8")
      : result.stderr;
    throw new Error(
      `${commandName} ${args.join(" ")} failed: ${stderr || "unknown error"}`,
    );
  }
  return result.stdout;
}

function resolveLandingPath(relativePath) {
  const resolved = path.resolve(landingRoot, relativePath);
  const prefix = `${landingRoot}${path.sep}`;
  if (resolved !== landingRoot && !resolved.startsWith(prefix)) {
    throw new Error(`Path escapes landing_page: ${relativePath}`);
  }
  return resolved;
}

function sha256(filePath) {
  return crypto
    .createHash("sha256")
    .update(fs.readFileSync(filePath))
    .digest("hex");
}

function imageDimensions(filePath) {
  const value = run("magick", [
    "identify",
    "-format",
    "%w %h",
    filePath,
  ]).trim();
  const [width, height] = value.split(/\s+/).map(Number);
  if (!Number.isInteger(width) || !Number.isInteger(height)) {
    throw new Error(`Could not read image dimensions for ${filePath}`);
  }
  return { width, height };
}

function sourceExtension(sourcePath) {
  const extension = path.extname(sourcePath);
  return extension || ".bin";
}

function publicUrl(outputPath) {
  const normalized = outputPath.replaceAll(path.sep, "/");
  if (!normalized.startsWith("public/")) {
    throw new Error(`Visual output must live under public/: ${outputPath}`);
  }
  return `/${normalized.slice("public/".length)}`;
}

function loadHomeContent() {
  const contentPath = path.join(
    landingRoot,
    "src",
    "content",
    "pages",
    "home.yaml",
  );
  return yaml.load(fs.readFileSync(contentPath, "utf8"));
}

function findContentEntry(homeContent, asset) {
  const section = homeContent.sections?.find(
    (candidate) => candidate?.id === asset.content.section_id,
  );
  if (!section) {
    throw new Error(
      `${asset.id}: missing section ${asset.content.section_id} in home.yaml`,
    );
  }
  const entries = section[asset.content.collection];
  if (!Array.isArray(entries)) {
    throw new Error(
      `${asset.id}: section ${asset.content.section_id} has no ${asset.content.collection}`,
    );
  }
  const item = entries.find(
    (candidate) => candidate?.title === asset.content.title,
  );
  if (!item) {
    throw new Error(
      `${asset.id}: missing ${asset.content.title} in ${asset.content.section_id}`,
    );
  }
  return asset.content.collection === "items" ? item.media : item;
}

function verifyContentEntry(homeContent, asset) {
  const entry = findContentEntry(homeContent, asset);
  const lightUrl = publicUrl(asset.variants.light.output);
  const darkUrl = publicUrl(asset.variants.dark.output);
  const checks = {
    src: lightUrl,
    srcDark: darkUrl,
    alt: asset.alt,
    width: asset.width,
    height: asset.height,
  };
  for (const [key, expected] of Object.entries(checks)) {
    if (entry?.[key] !== expected) {
      throw new Error(
        `${asset.id}: home.yaml ${key}=${JSON.stringify(entry?.[key])}, expected ${JSON.stringify(expected)}`,
      );
    }
  }
}

function extractSource(revision, sourcePath, destination) {
  const payload = run(
    "git",
    ["show", `${revision}:${sourcePath}`],
    { binary: true },
  );
  fs.mkdirSync(path.dirname(destination), { recursive: true });
  fs.writeFileSync(destination, payload);
}

function generateVariant(manifest, asset, theme, variant) {
  const rawPath = path.join(
    generationRoot,
    "raw",
    `${asset.id}-${theme}${sourceExtension(variant.source)}`,
  );
  const candidatePath = path.join(
    generationRoot,
    "generated",
    variant.output.slice("public/".length),
  );
  extractSource(manifest.source_revision, variant.source, rawPath);
  fs.mkdirSync(path.dirname(candidatePath), { recursive: true });

  const transform = variant.transform ?? {};
  const args = [rawPath];
  if (transform.trim) {
    args.push("-trim", "+repage");
  }
  if (transform.resize) {
    args.push("-resize", String(transform.resize));
  }
  if (transform.extent) {
    args.push(
      "-gravity",
      String(transform.gravity ?? "center"),
      "-extent",
      String(transform.extent),
    );
  }
  args.push(
    "-colorspace",
    "sRGB",
    "-strip",
    "-quality",
    String(transform.quality ?? 80),
    "-define",
    `webp:method=${transform.webp_method ?? 6}`,
    candidatePath,
  );
  run("magick", args);

  const dimensions = imageDimensions(candidatePath);
  const bytes = fs.statSync(candidatePath).size;
  const digest = sha256(candidatePath);
  const expected = variant.expected;
  if (
    dimensions.width !== expected.width ||
    dimensions.height !== expected.height
  ) {
    throw new Error(
      `${asset.id}/${theme}: generated ${dimensions.width}x${dimensions.height}, expected ${expected.width}x${expected.height}`,
    );
  }
  if (bytes > expected.max_bytes) {
    throw new Error(
      `${asset.id}/${theme}: ${bytes} bytes exceeds ${expected.max_bytes}`,
    );
  }
  const matchesExpectedHash = digest === expected.sha256;
  if (command !== "inspect" && !matchesExpectedHash) {
    throw new Error(
      `${asset.id}/${theme}: generated sha256 ${digest}, expected ${expected.sha256}`,
    );
  }

  const publicPath = resolveLandingPath(variant.output);
  if (command === "update") {
    fs.mkdirSync(path.dirname(publicPath), { recursive: true });
    fs.copyFileSync(candidatePath, publicPath);
  }
  if (command !== "inspect") {
    if (!fs.existsSync(publicPath)) {
      throw new Error(`${asset.id}/${theme}: missing ${variant.output}`);
    }
    const publicDigest = sha256(publicPath);
    if (publicDigest !== digest) {
      throw new Error(
        `${asset.id}/${theme}: ${variant.output} differs; run yarn visual-assets:update`,
      );
    }
  }

  return {
    theme,
    source: variant.source,
    output: variant.output,
    width: dimensions.width,
    height: dimensions.height,
    bytes,
    sha256: digest,
    expected_sha256: expected.sha256,
    matches_expected_sha256: matchesExpectedHash,
  };
}

const manifest = yaml.load(fs.readFileSync(manifestPath, "utf8"));
if (manifest.schema_version !== 1) {
  throw new Error(`Unsupported manifest schema: ${manifest.schema_version}`);
}
if (!Array.isArray(manifest.assets) || manifest.assets.length === 0) {
  throw new Error("Visual manifest has no assets");
}

fs.rmSync(generationRoot, { recursive: true, force: true });
fs.mkdirSync(generationRoot, { recursive: true });

const homeContent = loadHomeContent();
const themeTotals = { light: 0, dark: 0 };
const reportAssets = [];
const seenIds = new Set();

for (const asset of manifest.assets) {
  if (!asset.id || seenIds.has(asset.id)) {
    throw new Error(`Invalid or duplicate asset id: ${asset.id}`);
  }
  seenIds.add(asset.id);
  verifyContentEntry(homeContent, asset);

  const variants = [];
  for (const theme of ["light", "dark"]) {
    const variant = asset.variants?.[theme];
    if (!variant) {
      throw new Error(`${asset.id}: missing ${theme} variant`);
    }
    const result = generateVariant(manifest, asset, theme, variant);
    themeTotals[theme] += result.bytes;
    variants.push(result);
  }
  reportAssets.push({
    id: asset.id,
    claim: asset.claim,
    content: asset.content,
    variants,
  });
}

for (const theme of ["light", "dark"]) {
  if (themeTotals[theme] > manifest.budgets.active_theme_max_bytes) {
    throw new Error(
      `${theme} visual set is ${themeTotals[theme]} bytes; budget is ${manifest.budgets.active_theme_max_bytes}`,
    );
  }
}

const report = {
  schema_version: 1,
  generated_at: new Date().toISOString(),
  command,
  manifest: path.relative(landingRoot, manifestPath),
  source_revision: manifest.source_revision,
  transformation_version: manifest.transformation_version,
  tool_versions: {
    node: process.version,
    imagemagick: run("magick", ["-version"]).split("\n")[0],
  },
  theme_totals: themeTotals,
  budgets: manifest.budgets,
  assets: reportAssets,
};
fs.writeFileSync(
  path.join(generationRoot, "asset-check-report.json"),
  `${JSON.stringify(report, null, 2)}\n`,
);

console.log(
  `${command} verified ${reportAssets.length} visual assets: light=${themeTotals.light} bytes dark=${themeTotals.dark} bytes`,
);