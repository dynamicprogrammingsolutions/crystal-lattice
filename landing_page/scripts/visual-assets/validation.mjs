import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

import yaml from "js-yaml";

export function resolveWithin(root, relativePath, label) {
  const resolved = path.resolve(root, relativePath);
  const prefix = `${root}${path.sep}`;
  if (resolved !== root && !resolved.startsWith(prefix)) {
    throw new Error(`${label} escapes ${root}: ${relativePath}`);
  }
  return resolved;
}

export function resolveLandingPath(landingRoot, relativePath, label = "Path") {
  return resolveWithin(landingRoot, relativePath, label);
}

export function resolveRepositoryPath(
  repositoryRoot,
  relativePath,
  label = "Path",
) {
  return resolveWithin(repositoryRoot, relativePath, label);
}

export function ensureArtifactPath(repositoryRoot, candidatePath) {
  const relative = path.relative(repositoryRoot, candidatePath);
  if (
    relative.startsWith("..") ||
    path.isAbsolute(relative) ||
    !relative.split(path.sep).includes("artifacts")
  ) {
    throw new Error(
      `Capture candidates must remain under an artifacts directory: ${candidatePath}`,
    );
  }
}

export function sha256(filePath) {
  return crypto
    .createHash("sha256")
    .update(fs.readFileSync(filePath))
    .digest("hex");
}

export function inspectImage(filePath) {
  const result = spawnSync(
    "magick",
    ["identify", "-format", "%w %h", filePath],
    {
      encoding: "utf8",
      maxBuffer: 1024 * 1024,
    },
  );
  if (result.status !== 0) {
    throw new Error(
      `Could not inspect ${filePath}: ${result.stderr || "unknown error"}`,
    );
  }
  const [width, height] = result.stdout.trim().split(/\s+/).map(Number);
  if (!Number.isInteger(width) || !Number.isInteger(height)) {
    throw new Error(`Could not read image dimensions for ${filePath}`);
  }
  return {
    width,
    height,
    bytes: fs.statSync(filePath).size,
    sha256: sha256(filePath),
  };
}

export function publicUrl(outputPath) {
  const normalized = outputPath.replaceAll(path.sep, "/");
  if (!normalized.startsWith("public/")) {
    throw new Error(`Public output must be under public/: ${outputPath}`);
  }
  return `/${normalized.slice("public/".length)}`;
}

function findYamlMediaEntry(document, binding, assetId) {
  const section = document.sections?.find(
    (candidate) => candidate?.id === binding.sectionId,
  );
  if (!section) {
    throw new Error(
      `${assetId}: missing section ${binding.sectionId} in ${binding.file}`,
    );
  }
  if (!binding.collection) {
    return binding.mediaField ? section[binding.mediaField] : section;
  }
  const entries = section[binding.collection];
  if (!Array.isArray(entries)) {
    throw new Error(
      `${assetId}: section ${binding.sectionId} has no ${binding.collection}`,
    );
  }
  const item = entries.find((candidate) => candidate?.title === binding.title);
  if (!item) {
    throw new Error(
      `${assetId}: missing ${binding.title} in ${binding.sectionId}`,
    );
  }
  return binding.mediaField ? item[binding.mediaField] : item;
}

export function validateContentBindings(asset, landingRoot, documentCache) {
  for (const binding of asset.contentBindings ?? []) {
    if (binding.kind !== "yaml-media") {
      throw new Error(`${asset.id}: unknown content binding ${binding.kind}`);
    }
    const contentPath = resolveLandingPath(
      landingRoot,
      binding.file,
      "Content file",
    );
    let document = documentCache.get(contentPath);
    if (!document) {
      document = yaml.load(fs.readFileSync(contentPath, "utf8"));
      documentCache.set(contentPath, document);
    }
    const entry = findYamlMediaEntry(document, binding, asset.id);
    if (!entry) {
      throw new Error(`${asset.id}: content binding has no media entry`);
    }

    for (const [variantName, fieldName] of Object.entries(
      binding.variantFields,
    )) {
      const variant = asset.variants[variantName];
      if (!variant) {
        throw new Error(
          `${asset.id}: binding refers to unknown variant ${variantName}`,
        );
      }
      const expected = publicUrl(variant.output);
      if (entry[fieldName] !== expected) {
        throw new Error(
          `${asset.id}: ${binding.file} ${fieldName}=${JSON.stringify(entry[fieldName])}, expected ${JSON.stringify(expected)}`,
        );
      }
    }

    const presentation = asset.presentation;
    const checks = {
      alt: presentation?.alt,
      width: presentation?.width,
      height: presentation?.height,
    };
    for (const [fieldName, expected] of Object.entries(checks)) {
      if (expected !== undefined && entry[fieldName] !== expected) {
        throw new Error(
          `${asset.id}: ${binding.file} ${fieldName}=${JSON.stringify(entry[fieldName])}, expected ${JSON.stringify(expected)}`,
        );
      }
    }
  }
}