import fs from "node:fs";
import path from "node:path";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { defineAsset } from "./api.mjs";
import { buildComposition } from "./session-actions-composition.mjs";
import { proofBatchRecipes } from "../../visual_assets/proof-batch-recipes.mjs";

const hash = file => createHash("sha256").update(fs.readFileSync(file)).digest("hex");
const read = file => JSON.parse(fs.readFileSync(file, "utf8"));
const palette = theme => theme === "dark" ? "#0b0d10" : "#f3f4f7";

export function nativeExcerptGeometry(native, crop, destination, canvas) {
  const scale = native.size.width / native.geometry.width;
  assert.ok(crop.x >= 0 && crop.y >= 0 && crop.width > 0 && crop.height > 0);
  assert.ok((crop.x + crop.width) * scale <= native.size.width);
  assert.ok((crop.y + crop.height) * scale <= native.size.height);
  const placed = {
    ...destination, height: crop.height * destination.width / crop.width,
  };
  assert.ok(placed.x >= 0 && placed.x + placed.width <= canvas.width);
  assert.ok(placed.y >= 0 && placed.y + placed.height <= canvas.height);
  return {
    crop: `${Math.round(crop.width * scale)}x${Math.round(crop.height * scale)}+${Math.round(crop.x * scale)}+${Math.round(crop.y * scale)}`,
    destination: placed,
  };
}

async function metrics(context, file) {
  const { stdout } = await context.run("magick", ["identify", "-format", "%w %h", file], { stdio: "pipe" });
  const [width, height] = stdout.trim().split(/\s+/).map(Number);
  return { width, height };
}

async function buildReport(context, recipe) {
  const source = path.join(context.repositoryRoot, recipe.captureDirectory);
  const destination = path.join(context.landingRoot, recipe.candidateDirectory);
  const contractPath = path.join(source, "contract.json");
  const contract = read(contractPath);
  assert.ok(contract.response.result.display.body);
  const sources = { ...contract.sourceHashes, [path.relative(context.repositoryRoot, contractPath)]: hash(contractPath) };
  for (const [file, expected] of Object.entries(sources)) {
    assert.equal(hash(path.join(context.repositoryRoot, file)), expected, `Changed native source: ${file}`);
  }
  fs.mkdirSync(destination, { recursive: true });
  const results = [];
  for (const theme of ["light", "dark"]) {
    const report = path.join(source, `${theme}-report.png`);
    const compact = path.join(source, `${theme}-report-compact.png`);
    const geometryFile = path.join(source, `${theme}-geometry.json`);
    const compactGeometryFile = path.join(source, `${theme}-geometry-compact.json`);
    const geometry = read(geometryFile);
    const compactGeometry = read(compactGeometryFile);
    const conversation = path.join(source, `${theme}-conversation.png`);
    for (const file of [conversation, report, compact, geometryFile, compactGeometryFile]) {
      sources[path.relative(context.repositoryRoot, file)] = hash(file);
    }
    const nativeConversation = {
      file: conversation, geometry: geometry.window, size: await metrics(context, conversation),
    };
    const nativeReports = {
      report: { file: report, geometry: geometry.report, size: await metrics(context, report) },
      "report-compact": { file: compact, geometry: compactGeometry.report, size: await metrics(context, compact) },
    };
    for (const shape of ["wide", "compact"]) {
      const width = shape === "wide" ? 2400 : 1200;
      const height = shape === "wide" ? 1350 : 1600;
      const filename = `${shape}${theme === "dark" ? "-dark" : ""}.webp`;
      const file = path.join(destination, filename);
      const args = ["-size", `${width}x${height}`, `xc:${palette(theme)}`];
      const excerpts = [];
      let reportContext;
      let metadataCorrespondence;
      if (shape === "wide") {
        // A screenshot taken after opening the report already contains that
        // window. Use the earlier unobscured conversation as the context.
        const contextWidth = 1060;
        const contextHeight = nativeConversation.size.height * contextWidth / nativeConversation.size.width;
        const contextPlacement = { x: 60, y: Math.round((height - contextHeight) / 2), width: contextWidth, height: contextHeight };
        if (!recipe.reportOnly) {
          args.push("(", conversation, "-resize", `${contextWidth}x`, ")",
            "-geometry", `+${contextPlacement.x}+${contextPlacement.y}`, "-composite");
          reportContext = {
            source: path.relative(context.repositoryRoot, conversation),
            destination: contextPlacement,
          };
        }
        const crop = {
          x: 0, y: 0, width: geometry.report.width, height: recipe.wideReportHeight,
        };
        const reportWidth = recipe.reportOnly ? 1800 : 1440;
        const reportX = recipe.reportOnly ? 300 : 900;
        const destinationY = Math.round((height - crop.height * reportWidth / crop.width) / 2);
        const excerpt = nativeExcerptGeometry(nativeReports.report, crop,
          { x: reportX, y: destinationY, width: reportWidth }, { width, height });
        args.push("(", report, "-crop", excerpt.crop, "+repage", "-resize", `${reportWidth}x`, ")",
          "-geometry", `+${excerpt.destination.x}+${excerpt.destination.y}`, "-composite");
        excerpts.push({
          kind: "report",
          source: { file: path.relative(context.repositoryRoot, report), ...crop },
          destination: excerpt.destination,
        });
        const bottom = excerpt.destination.y + excerpt.destination.height;
        args.push("-fill", "none", "-stroke", theme === "dark" ? "#a5b2c5" : "#64748b",
          "-strokewidth", "2",
          "-draw", `path 'M ${reportX + 20},${bottom} L ${reportX + reportWidth / 2 - 15},${bottom - 4} L ${reportX + reportWidth / 2},${bottom + 4} L ${reportX + reportWidth / 2 + 15},${bottom - 4} L ${reportX + reportWidth - 20},${bottom}'`);
        if (recipe.metadataExcerpt) {
          const crop = recipe.metadataExcerpt;
          const { crop: region, destination } = nativeExcerptGeometry(
            nativeConversation, crop, crop.destination, { width, height },
          );
          const scale = contextWidth / geometry.window.width;
          const origin = {
            x: contextPlacement.x + crop.x * scale, y: contextPlacement.y + crop.y * scale,
            width: crop.width * scale, height: crop.height * scale,
          };
          metadataCorrespondence = { source: origin, detail: destination };
          const startY = origin.y + origin.height / 2;
          const endY = destination.y + destination.height / 2;
          args.push("-fill", "none", "-stroke", "#4387ef", "-strokewidth", "3",
            "-draw", `rectangle ${origin.x},${origin.y} ${origin.x + origin.width},${origin.y + origin.height}`,
            "-draw", `path 'M ${origin.x},${startY} L 38,${startY} L 38,${endY} L ${destination.x},${endY}'`,
            "(", conversation, "-crop", region, "+repage", "-resize", `${destination.width}x`, ")",
            "-geometry", `+${destination.x}+${destination.y}`, "-composite",
            "-draw", `rectangle ${destination.x},${destination.y} ${destination.x + destination.width},${destination.y + destination.height}`);
          excerpts.push({
            kind: "message-metadata",
            source: { file: path.relative(context.repositoryRoot, conversation),
              x: crop.x, y: crop.y, width: crop.width, height: crop.height },
            destination,
          });
        }
      } else {
        for (const crop of recipe.compactExcerpts) {
          const native = nativeReports[crop.source];
          const nativeScale = native.size.width / native.geometry.width;
          assert.ok(crop.x >= 0 && crop.y >= 0);
          assert.ok((crop.x + crop.width) * nativeScale <= native.size.width);
          assert.ok((crop.y + crop.height) * nativeScale <= native.size.height);
          const destination = {
            ...crop.destination,
            height: crop.height * crop.destination.width / crop.width,
          };
          assert.ok(destination.x >= 0 && destination.x + destination.width <= width);
          assert.ok(destination.y >= 0 && destination.y + destination.height <= height);
          const cropGeometry = `${Math.round(crop.width * nativeScale)}x${Math.round(crop.height * nativeScale)}+${Math.round(crop.x * nativeScale)}+${Math.round(crop.y * nativeScale)}`;
          args.push("(", native.file, "-crop", cropGeometry, "+repage", "-resize", `${destination.width}x`, ")",
            "-geometry", `+${destination.x}+${destination.y}`, "-composite");
          excerpts.push({
            source: { file: path.relative(context.repositoryRoot, native.file),
              x: crop.x, y: crop.y, width: crop.width, height: crop.height },
            destination,
          });
        }
        // Visible interruptions distinguish genuine magnifications from a
        // fabricated shortened report. No report labels or values are redrawn.
        args.push("-fill", "none", "-stroke", theme === "dark" ? "#a5b2c5" : "#64748b", "-strokewidth", "2");
        for (const [index, excerpt] of excerpts.entries()) {
          const { destination, source: crop } = excerpt;
          if (index + 1 < excerpts.length) {
            const y = (destination.y + destination.height + excerpts[index + 1].destination.y) / 2;
            args.push("-draw", `path 'M 90,${y} L 585,${y - 4} L 600,${y + 4} L 615,${y - 4} L 1110,${y}'`);
          }
          if (crop.width < nativeReports[recipe.compactExcerpts[index].source].geometry.width) {
            const x = destination.x + destination.width;
            const mid = destination.y + destination.height / 2;
            args.push("-draw", `path 'M ${x},${destination.y + 8} L ${x},${mid - 8} L ${x - 5},${mid} L ${x},${mid + 8} L ${x},${destination.y + destination.height - 8}'`);
          }
        }
      }
      args.push("-colorspace", "sRGB", "-strip", "-quality", "88", "-define", "webp:method=6", file);
      await context.run("magick", args, { stdio: "pipe" });
      const imageMetrics = await metrics(context, file);
      assert.deepEqual(imageMetrics, { width, height });
      const bytes = fs.statSync(file).size;
      assert.ok(bytes <= recipe.maxBytes, `${filename} exceeds its budget.`);
      results.push({
        asset_id: recipe.id, variant: `${shape}-${theme}`, file: filename, width, height, bytes,
        sha256: hash(file), presentation: "native-report", excerpts,
        actionId: contract.reportAction.actionId, nativeGeometry: geometry,
        reportContext, metadataCorrespondence,
      });
    }
  }
  fs.writeFileSync(path.join(destination, "manifest.json"), JSON.stringify({
    reviewState: "candidate", sourceHashes: sources, results,
    recipeSha256: hash(path.join(context.landingRoot, recipe.recipeFile)),
    actualReport: contract.response.result, sampleData: recipe.sampleData ?? false,
  }, null, 2));
  return results;
}

export const proofBatchAssets = proofBatchRecipes.map(recipe => defineAsset({
  id: recipe.id,
  metadata: { reviewState: "candidate", claim: recipe.alt },
  config: recipe,
  commands: {
    list: () => ({ id: recipe.id, commands: ["inspect", "check"] }),
    inspect: context => !context.input?.explicitAsset
      ? { asset_id: recipe.id, skipped: true, reason: "Select this candidate explicitly." }
      : recipe.type === "report" ? buildReport(context, recipe) : buildComposition(context, recipe),
    check: context => {
      if (!context.input?.explicitAsset) return { asset_id: recipe.id, skipped: true, reason: "Select this candidate explicitly." };
      const directory = path.join(context.landingRoot, recipe.candidateDirectory);
      const manifest = read(path.join(directory, "manifest.json"));
      assert.equal(manifest.recipeSha256, hash(path.join(context.landingRoot, recipe.recipeFile)));
      for (const [file, expected] of Object.entries(manifest.sourceHashes)) {
        assert.equal(hash(path.join(context.repositoryRoot, file)), expected, `Changed source: ${file}`);
      }
      for (const result of manifest.results) {
        assert.equal(hash(path.join(directory, result.file)), result.sha256);
        assert.ok(result.bytes <= recipe.maxBytes);
      }
      return manifest.results;
    },
  },
}));