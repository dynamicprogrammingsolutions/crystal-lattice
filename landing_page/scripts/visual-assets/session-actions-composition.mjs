import fs from "node:fs";
import path from "node:path";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { chromium } from "@playwright/test";
import { defineAsset } from "./api.mjs";
import { readSessionActionsRecipe } from "./session-actions-preview.mjs";

const recipe = readSessionActionsRecipe();

const digest = (file) => createHash("sha256").update(fs.readFileSync(file)).digest("hex");
const readJson = (file) => JSON.parse(fs.readFileSync(file, "utf8"));
const escapeHtml = (value) => String(value).replace(/[&<>"']/g, (character) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
})[character]);
const colors = ["#4387ef", "#20a5ad", "#a879ed"];
const markerColor = (color, opacity) => {
  const values = color.slice(1).match(/../g).map(value => parseInt(value, 16));
  return `rgba(${values.join(",")},${opacity})`;
};
const palette = (theme) => theme === "dark"
  ? { background: "#0b0d10", code: "#151b24", text: "#e8edf5", muted: "#a5b2c5", border: "#344255" }
  : { background: "#f3f4f7", code: "#ffffff", text: "#172239", muted: "#64748b", border: "#c8d1df" };

export function validateSessionActionsContract(contract, config) {
  assert.deepEqual(contract.configExcerpt, { plugins: config.plugins });
  assert.equal(contract.mappings.length, 3);
  for (const mapping of contract.mappings) {
    assert.ok(config.plugins.includes(`path:plugins/${mapping.package}`));
    const actual = contract.schema.find((entry) => entry.id === mapping.id);
    assert.equal(actual?.plugin, mapping.plugin);
    assert.equal(actual?.label, mapping.label);
    assert.equal(actual?.action_id, mapping.actionId);
    assert.equal(actual?.ui_type, "session_action");
  }
}

export function focusGeometry(geometry, layout) {
  const top = Math.min(...geometry.rows.map((row) => row.frame.y)) - geometry.popover.y - 8;
  const bottom = Math.max(...geometry.rows.map((row) => row.frame.y + row.frame.height)) - geometry.popover.y + 8;
  const left = layout.focus.labelOnly
    ? geometry.rows[0].frame.x - geometry.popover.x + (layout.focus.labelInset ?? 36)
    : 4;
  const width = layout.focus.labelOnly ? (layout.focus.labelWidth ?? 160) : geometry.popover.width - 8;
  assert.ok(left >= 0 && top >= 0 && left + width <= geometry.popover.width);
  assert.ok(bottom <= geometry.popover.height);
  const zoom = layout.focus.width / width;
  assert.ok(layout.focus.y + (bottom - top) * zoom + 4 <= layout.height,
    "The magnified menu exceeds this canvas; adjust the maintained composition.");
  return { x: left, y: top, width, height: bottom - top, zoom };
}

export function stackedPopupGeometry(geometry, layout) {
  const bodyTop = Math.min(...geometry.rows.map(row => row.frame.y)) - geometry.popover.y - 8;
  const left = layout.focus.outlineInset ?? 0;
  const width = geometry.popover.width - left * 2;
  const bottom = geometry.popover.height - left;
  const zoom = layout.focus.width / width;
  const headerHeight = layout.focus.headerHeight;
  const gapHeight = layout.focus.cropBreakHeight;
  assert.ok(headerHeight > 0 && headerHeight < bodyTop);
  assert.ok(layout.focus.y + (headerHeight + gapHeight + bottom - bodyTop) * zoom <= layout.height);
  return {
    left, width, zoom, headerHeight, gapHeight, bodyTop, bottom,
    bodyHeight: bottom - bodyTop,
    omitted: { y: headerHeight, height: bodyTop - headerHeight },
    rows: geometry.rows.map((row, index) => ({
      id: row.id, color: colors[index],
      x: row.frame.x - geometry.popover.x - 4,
      y: row.frame.y - geometry.popover.y + row.frame.height * 0.16,
      width: geometry.popover.width - 2 * (row.frame.x - geometry.popover.x - 4),
      height: row.frame.height * 0.68,
    })),
  };
}

async function buildStackedPopup(context, popupPath, geometry, layout, theme, scale, output) {
  const focus = stackedPopupGeometry(geometry, layout);
  const overlay = `${output}-marker.png`;
  const marked = `${output}-marked.png`;
  const silhouette = `${output}-silhouette.png`;
  const isolated = `${output}-isolated.png`;
  const popupSize = await dimensions(context, popupPath);
  const args = ["-size", `${popupSize.width}x${popupSize.height}`, "xc:none", "-stroke", "none"];
  for (const row of focus.rows) {
    const x = row.x * scale, y = row.y * scale;
    const width = row.width * scale, height = row.height * scale;
    args.push("-fill", markerColor(row.color, 0.3), "-draw",
      `polygon ${x},${y + 4} ${x + width - 7},${y} ${x + width},${y + height - 4} ${x + 3},${y + height}`);
  }
  args.push(overlay);
  await context.run("magick", args, { stdio: "pipe" });
  await context.run("magick", [
    popupPath, overlay, "-compose", theme === "dark" ? "Screen" : "Multiply", "-composite", marked,
  ], { stdio: "pipe" });
  const edge = focus.left * scale;
  const top = layout.focus.outlineTop * scale;
  const right = popupSize.width - edge;
  const bottom = focus.bottom * scale;
  const radius = layout.focus.cornerRadius * scale;
  const center = popupSize.width / 2;
  await context.run("magick", [
    "-size", `${popupSize.width}x${popupSize.height}`, "xc:black", "-fill", "white", "-stroke", "none",
    "-draw", `roundrectangle ${edge},${top} ${right},${bottom} ${radius},${radius}`,
    "-draw", `polygon ${center - top},${top} ${center},0 ${center + top},${top}`, silhouette,
  ], { stdio: "pipe" });
  await context.run("magick", [
    marked, silhouette, "-alpha", "off", "-compose", "CopyOpacity", "-composite", isolated,
  ], { stdio: "pipe" });
  const cropX = Math.round(focus.left * scale);
  const header = `${Math.round(focus.width * scale)}x${Math.round(focus.headerHeight * scale)}+${cropX}+0`;
  const body = `${Math.round(focus.width * scale)}x${Math.round(focus.bodyHeight * scale)}+${cropX}+${Math.round(focus.bodyTop * scale)}`;
  // A visible interruption preserves the fact that this is an excerpt,
  // instead of depicting a complete menu with the other entries removed.
  const gapHeight = Math.round(focus.gapHeight * scale);
  const sourceWidth = Math.round(focus.width * scale);
  await context.run("magick", [
    "(", isolated, "-crop", header, "+repage", ")",
    "(", "-size", `${sourceWidth}x${gapHeight}`, `xc:${palette(theme).background}`,
    "-fill", "none", "-stroke", palette(theme).muted, "-strokewidth", "1",
    "-draw", `path 'M 24,${gapHeight / 2} L ${sourceWidth / 2 - 8},${gapHeight / 2 - 3} L ${sourceWidth / 2},${gapHeight / 2 + 3} L ${sourceWidth / 2 + 8},${gapHeight / 2 - 3} L ${sourceWidth - 24},${gapHeight / 2}'`, ")",
    "(", isolated, "-crop", body, "+repage", ")",
    "-append", "-resize", `${layout.focus.width}x`, output,
  ], { stdio: "pipe" });
  return focus;
}

async function dimensions(context, file) {
  const result = await context.run("magick", ["identify", "-format", "%w %h", file], { stdio: "pipe" });
  const [width, height] = result.stdout.trim().split(/\s+/).map(Number);
  assert.ok(width > 0 && height > 0);
  return { width, height };
}

async function renderCode(browser, contract, layout, theme, output) {
  const page = await browser.newPage({ viewport: { width: layout.code.width, height: layout.code.height }, deviceScaleFactor: 1 });
  try {
    const tones = palette(theme);
    const rows = contract.configExcerpt.plugins.map((value, index) => {
      const name = contract.mappings[index].package;
      const quoted = JSON.stringify(value);
      const start = quoted.indexOf(name);
      assert.ok(start >= 0);
      const highlight = layout.code.highlightRows
        ? ` style="--marker:${markerColor(colors[index], theme === "dark" ? 0.3 : 0.22)}"` : "";
      return `<span class="entry"${highlight}>  ${escapeHtml(quoted.slice(0, start))}<span class="value-tail"><span class="package" data-plugin="${name}" style="color:${layout.code.highlightRows ? tones.text : colors[index]}">${escapeHtml(name)}</span><span class="suffix">${escapeHtml(quoted.slice(start + name.length))}${index < 2 ? "," : ""}</span></span></span>`;
    });
    await page.setContent(`<!doctype html><html><head><meta charset="utf-8"><style>
      *{box-sizing:border-box}body{margin:0;background:transparent}
      pre{margin:0;padding:36px ${layout.code.paddingHorizontal ?? 24}px;border:2px solid ${tones.border};border-radius:22px;
        color:${tones.muted};background:${tones.code};font:${layout.code.fontSize}px/${layout.code.lineHeight}px Menlo,monospace;
        white-space:pre-wrap;overflow-wrap:anywhere}
      .entry{display:block;margin:${layout.code.entryGap}px 0}.package{font-weight:650}
      .value-tail{display:inline-block;white-space:nowrap}.suffix{font-size:${layout.code.suffixScale ?? 1}em}
      .key{color:${tones.text}}
      ${layout.code.highlightRows ? ".entry{position:relative;isolation:isolate}.entry::before{content:'';position:absolute;inset:5px -6px;background:var(--marker);z-index:-1;clip-path:polygon(0% 8%,99% 0%,100% 91%,1% 100%)}" : ""}
    </style></head><body><pre>{\n  <span class="key">"plugins"</span>: [${rows.join("")}  ]\n}</pre></body></html>`);
    await page.evaluate(() => document.fonts.ready);
    assert.deepEqual(JSON.parse(await page.locator("pre").textContent()), contract.configExcerpt);
    const codeBounds = await page.locator("pre").boundingBox();
    assert.ok(codeBounds.height <= layout.code.height,
      `Configuration text is ${codeBounds.height}px high for the ${layout.width}px ${theme} canvas; allocated ${layout.code.height}px.`);
    const anchors = await page.locator("[data-plugin]").evaluateAll((elements) => elements.map((element) => {
      const rect = element.closest(".entry").getBoundingClientRect();
      const label = element.getBoundingClientRect();
      return {
        package: element.getAttribute("data-plugin"),
        x: rect.right + 12, y: rect.top + rect.height / 2,
        row: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
        label: { x: label.x, y: label.y, width: label.width, height: label.height },
      };
    }));
    for (const anchor of anchors) {
      assert.ok(anchor.label.x >= 0 && anchor.label.x + anchor.label.width <= layout.code.width,
        `${anchor.package} extends beyond the configuration canvas.`);
      assert.ok(anchor.label.y >= 0 && anchor.label.y + anchor.label.height <= layout.code.height,
        `${anchor.package} is vertically clipped.`);
    }
    await page.screenshot({ path: output, omitBackground: true });
    return anchors;
  } finally {
    await page.close();
  }
}

async function buildComposition(context) {
  const source = path.join(context.repositoryRoot, recipe.captureDirectory);
  const output = path.join(context.landingRoot, recipe.candidateDirectory);
  const configPath = path.join(context.landingRoot, "visual_assets/runtime/session-actions/config.json");
  const contractPath = path.join(source, "contract.json");
  const contract = readJson(contractPath);
  validateSessionActionsContract(contract, readJson(configPath));
  assert.equal(digest(configPath), contract.configSha256, "Capture configuration changed; recapture first.");
  fs.mkdirSync(output, { recursive: true });
  assert.ok(contract.sourceHashes, "Capture lacks source fingerprints; recapture first.");
  const sourceHashes = {
    ...contract.sourceHashes,
    [path.relative(context.repositoryRoot, contractPath)]: digest(contractPath),
    [path.relative(context.repositoryRoot, configPath)]: digest(configPath),
  };
  for (const [file, expected] of Object.entries(sourceHashes)) {
    assert.equal(digest(path.join(context.repositoryRoot, file)), expected, `Capture source changed: ${file}`);
  }
  const browser = await chromium.launch({ headless: true });
  const results = [];
  try {
    for (const theme of ["light", "dark"]) {
      const geometryPath = path.join(source, `${theme}-geometry.json`);
      const windowPath = path.join(source, `${theme}-window.png`);
      const popupPath = path.join(source, `${theme}-popover.png`);
      const geometry = readJson(geometryPath);
      assert.deepEqual(geometry.rows.map((row) => ({ id: row.id, label: row.label })),
        contract.mappings.map((row) => ({ id: row.id, label: row.label })));
      for (const file of [geometryPath, windowPath, popupPath]) {
        sourceHashes[path.relative(context.repositoryRoot, file)] = digest(file);
      }
      const windowSize = await dimensions(context, windowPath);
      const popupSize = await dimensions(context, popupPath);
      const windowScale = windowSize.width / geometry.window.width;
      const popupScale = popupSize.width / geometry.popover.width;
      assert.ok(Math.abs(windowScale - popupScale) < 0.05, "Native window capture scales differ.");
      const origin = {
        x: Math.min(geometry.window.x, geometry.popover.x),
        y: Math.min(geometry.window.y, geometry.popover.y),
      };
      const union = {
        width: Math.ceil((Math.max(geometry.window.x + geometry.window.width, geometry.popover.x + geometry.popover.width) - origin.x) * windowScale),
        height: Math.ceil((Math.max(geometry.window.y + geometry.window.height, geometry.popover.y + geometry.popover.height) - origin.y) * windowScale),
      };
      const nativePath = path.join(output, `${theme}-native-context.png`);
      const offset = (frame) => `+${Math.round((frame.x - origin.x) * windowScale)}+${Math.round((frame.y - origin.y) * windowScale)}`;
      await context.run("magick", [
        "-size", `${union.width}x${union.height}`, "xc:none",
        windowPath, "-geometry", offset(geometry.window), "-composite",
        popupPath, "-geometry", offset(geometry.popover), "-composite", nativePath,
      ], { stdio: "pipe" });
      for (const [shape, layout] of Object.entries(recipe.layouts)) {
        const filename = `${shape}${theme === "dark" ? "-dark" : ""}.webp`;
        const codePath = path.join(output, `${shape}-${theme}-code.png`);
        const anchors = await renderCode(browser, contract, layout, theme, codePath);
        if (layout.presentation === "stacked-highlights") {
          const popupOutput = path.join(output, `${shape}-${theme}-popup.png`);
          const excerpt = await buildStackedPopup(context, popupPath, geometry, layout, theme, popupScale, popupOutput);
          const correspondences = contract.mappings.map((mapping, index) => ({
            package: mapping.package, actionId: mapping.id, color: colors[index],
            configRow: anchors[index].row,
            configLabel: {
              x: layout.code.x + anchors[index].label.x, y: layout.code.y + anchors[index].label.y,
              width: anchors[index].label.width, height: anchors[index].label.height,
            },
            actionRow: {
              x: layout.focus.x + (excerpt.rows[index].x - excerpt.left) * excerpt.zoom,
              y: layout.focus.y + (excerpt.headerHeight + excerpt.gapHeight + excerpt.rows[index].y - excerpt.bodyTop) * excerpt.zoom,
              width: excerpt.rows[index].width * excerpt.zoom,
              height: excerpt.rows[index].height * excerpt.zoom,
            },
          }));
          const file = path.join(output, filename);
          await context.run("magick", [
            "-size", `${layout.width}x${layout.height}`, `xc:${palette(theme).background}`,
            codePath, "-geometry", `+${layout.code.x}+${layout.code.y}`, "-composite",
            popupOutput, "-geometry", `+${layout.focus.x}+${layout.focus.y}`, "-composite",
            "-colorspace", "sRGB", "-strip", "-quality", "88", "-define", "webp:method=6", file,
          ], { stdio: "pipe" });
          const metrics = await dimensions(context, file);
          assert.deepEqual(metrics, { width: layout.width, height: layout.height });
          assert.ok(fs.statSync(file).size <= recipe.maxBytes);
          results.push({
            asset_id: recipe.id, variant: `${shape}-${theme}`, file: filename, ...metrics,
            bytes: fs.statSync(file).size, sha256: digest(file),
            presentation: layout.presentation, popupExcerpt: excerpt,
            endpoints: [], correspondences,
          });
          continue;
        }
        const focus = focusGeometry(geometry, layout);
        const focusPath = path.join(output, `${shape}-${theme}-focus.png`);
        const crop = `${Math.round(focus.width * popupScale)}x${Math.round(focus.height * popupScale)}+${Math.round(focus.x * popupScale)}+${Math.round(focus.y * popupScale)}`;
        await context.run("magick", [
          popupPath, "-crop", crop, "+repage", "-resize", `${layout.focus.width}x`,
          "-bordercolor", palette(theme).border, "-border", "2", focusPath,
        ], { stdio: "pipe" });
        const endpoints = contract.mappings.map((mapping, index) => ({
          package: mapping.package, actionId: mapping.id,
          configRow: anchors[index].row,
          configLabel: {
            x: layout.code.x + anchors[index].label.x,
            y: layout.code.y + anchors[index].label.y,
            width: anchors[index].label.width, height: anchors[index].label.height,
          },
          from: { x: layout.code.x + anchors[index].x, y: layout.code.y + anchors[index].y },
          to: {
            x: layout.focus.x + 2 + Math.max(
              geometry.rows[index].frame.x + 2 - geometry.popover.x - focus.x, 2,
            ) * focus.zoom,
            y: layout.focus.y + 2 + (geometry.rows[index].frame.y + geometry.rows[index].frame.height / 2 - geometry.popover.y - focus.y) * focus.zoom,
          },
        }));
        const args = [
          "-size", `${layout.width}x${layout.height}`, `xc:${palette(theme).background}`,
          "(", nativePath, "-resize", `${layout.context.width}x`, ")",
          "-geometry", `+${layout.context.x}+${layout.context.y}`, "-composite",
          codePath, "-geometry", `+${layout.code.x}+${layout.code.y}`, "-composite",
          focusPath, "-geometry", `+${layout.focus.x}+${layout.focus.y}`, "-composite",
        ];
        for (const [index, point] of endpoints.entries()) {
          for (const endpoint of [point.from, point.to]) {
            assert.ok(endpoint.x >= 0 && endpoint.x < layout.width && endpoint.y >= 0 && endpoint.y < layout.height);
          }
          const { from, to } = point;
          const gap = to.x - from.x;
          assert.ok(gap > 0, "Configuration and action columns overlap.");
          args.push("-fill", "none", "-stroke", colors[index], "-strokewidth", shape === "wide" ? "5" : "4",
            "-draw", `path 'M ${from.x},${from.y} C ${from.x + gap * 0.45},${from.y} ${to.x - gap * 0.45},${to.y} ${to.x},${to.y}'`,
            "-fill", colors[index], "-stroke", "none", "-draw", `circle ${to.x},${to.y} ${to.x + 6},${to.y}`);
        }
        const file = path.join(output, filename);
        args.push("-colorspace", "sRGB", "-strip", "-quality", "88", "-define", "webp:method=6", file);
        await context.run("magick", args, { stdio: "pipe" });
        const metrics = await dimensions(context, file);
        assert.deepEqual(metrics, { width: layout.width, height: layout.height });
        assert.ok(fs.statSync(file).size <= recipe.maxBytes, `${filename} exceeds its byte budget.`);
        if (shape === "wide") {
          assert.equal(digest(file), recipe.preserveWideHashes[theme], "The reviewed Desktop composition changed.");
        }
        results.push({
          asset_id: recipe.id, variant: `${shape}-${theme}`, file: filename, ...metrics,
          bytes: fs.statSync(file).size, sha256: digest(file), focus, endpoints,
        });
      }
    }
  } finally {
    await browser.close();
  }
  fs.writeFileSync(path.join(output, "manifest.json"), JSON.stringify({
    reviewState: "candidate",
    recipeSha256: digest(path.join(context.landingRoot, "visual_assets/session-actions-composition.json")),
    configSha256: contract.configSha256,
    sourceHashes, results,
  }, null, 2));
  return results;
}

export const sessionActionsComposition = defineAsset({
  id: recipe.id,
  metadata: {
    reviewState: "candidate",
    claim: "The configured title and summarization plugins contribute the shown native Session actions.",
    freshness: ["plugin action schema", "Desktop menu rendering", "capture theme", "composition recipe"],
  },
  config: recipe,
  commands: {
    list: () => ({ id: recipe.id, commands: ["capture", "inspect", "check"] }),
    capture: async (context) => {
      await context.run("npm", ["run", "capture:session-actions:macos"], {
        cwd: path.join(context.repositoryRoot, "desktop/crystal-lattice-control-desktop-rn"),
      });
      return { asset_id: recipe.id, source: recipe.captureDirectory };
    },
    inspect: (context) => context.input?.explicitAsset
      ? buildComposition(context)
      : { asset_id: recipe.id, skipped: true, reason: "Select this unreviewed candidate explicitly." },
    check: async (context) => {
      if (!context.input?.explicitAsset) {
        return { asset_id: recipe.id, skipped: true, reason: "Select this unreviewed candidate explicitly." };
      }
      const root = path.join(context.landingRoot, recipe.candidateDirectory);
      const manifest = readJson(path.join(root, "manifest.json"));
      assert.equal(manifest.recipeSha256, digest(path.join(context.landingRoot, "visual_assets/session-actions-composition.json")));
      for (const [file, expected] of Object.entries(manifest.sourceHashes)) {
        assert.equal(digest(path.join(context.repositoryRoot, file)), expected, `Changed source: ${file}`);
      }
      for (const result of manifest.results) {
        assert.equal(digest(path.join(root, result.file)), result.sha256);
        assert.ok(result.bytes <= recipe.maxBytes);
      }
      return manifest.results;
    },
  },
});