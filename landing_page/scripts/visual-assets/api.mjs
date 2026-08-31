const assetKeys = new Set([
  "id",
  "metadata",
  "config",
  "commands",
  "lifecycle",
]);
const catalogKeys = new Set(["config", "commands", "assets"]);

/**
 * @typedef {Object} AssetDefinition
 * @property {string} id
 * @property {Record<string, unknown>=} metadata
 * @property {unknown=} config
 * @property {Record<string, Function>=} commands
 * @property {Record<string, Function>=} lifecycle
 */

/**
 * @typedef {Object} CatalogDefinition
 * @property {unknown=} config
 * @property {Record<string, Function>} commands
 * @property {Array<ReturnType<typeof defineAsset>>} assets
 */

function rejectUnknownKeys(value, allowed, label) {
  const unknown = Object.keys(value).filter((key) => !allowed.has(key));
  if (unknown.length > 0) {
    throw new Error(`${label} has unknown keys: ${unknown.join(", ")}`);
  }
}

function validateCallbacks(callbacks, label) {
  for (const [name, callback] of Object.entries(callbacks)) {
    if (typeof callback !== "function") {
      throw new Error(`${label}.${name} must be a function`);
    }
  }
}

/**
 * Define one asset with opaque asset-specific config and explicit executable
 * commands and/or lifecycle callbacks.
 *
 * @param {AssetDefinition} definition
 */
export function defineAsset(definition) {
  rejectUnknownKeys(definition, assetKeys, "Asset");
  if (!definition.id) {
    throw new Error("Asset requires id");
  }

  const commands = definition.commands ?? {};
  const lifecycle = definition.lifecycle ?? {};
  validateCallbacks(commands, `${definition.id}.commands`);
  validateCallbacks(lifecycle, `${definition.id}.lifecycle`);
  if (
    Object.keys(commands).length === 0 &&
    Object.keys(lifecycle).length === 0
  ) {
    throw new Error(
      `${definition.id} requires at least one command or lifecycle callback`,
    );
  }

  const asset = {
    id: definition.id,
    metadata: definition.metadata ?? {},
    config: definition.config,
    commands,
    lifecycle,

    hasCommand(name) {
      return typeof commands[name] === "function";
    },

    hasLifecycle(name) {
      return typeof lifecycle[name] === "function";
    },

    async runCommand(name, context, input) {
      const callback = commands[name];
      if (!callback) {
        throw new Error(`${definition.id} does not support command ${name}`);
      }
      return callback({
        ...context,
        asset,
        config: definition.config,
        metadata: asset.metadata,
        input,
      });
    },

    async runLifecycle(name, context, input) {
      const callback = lifecycle[name];
      if (!callback) {
        throw new Error(
          `${definition.id} does not support lifecycle ${name}`,
        );
      }
      return callback({
        ...context,
        asset,
        config: definition.config,
        metadata: asset.metadata,
        input,
      });
    },
  };

  return asset;
}

/**
 * Define the catalog composition root and its CLI-visible command workflows.
 *
 * @param {CatalogDefinition} definition
 */
export function defineVisualAssets(definition) {
  rejectUnknownKeys(definition, catalogKeys, "Visual asset catalog");
  if (!Array.isArray(definition.assets) || definition.assets.length === 0) {
    throw new Error("Visual asset catalog requires assets");
  }
  if (
    !definition.commands ||
    Object.keys(definition.commands).length === 0
  ) {
    throw new Error("Visual asset catalog requires commands");
  }
  validateCallbacks(definition.commands, "catalog.commands");

  const assetMap = new Map();
  for (const asset of definition.assets) {
    if (!asset?.id || typeof asset.runCommand !== "function") {
      throw new Error("Catalog assets must be created with defineAsset");
    }
    if (assetMap.has(asset.id)) {
      throw new Error(`Duplicate visual asset id: ${asset.id}`);
    }
    assetMap.set(asset.id, asset);
  }

  const catalog = {
    config: definition.config ?? {},
    commands: definition.commands,
    assets: definition.assets,
    assetMap,
    commandNames: Object.keys(definition.commands),

    hasCommand(name) {
      return typeof definition.commands[name] === "function";
    },

    async execute(name, context) {
      const callback = definition.commands[name];
      if (!callback) {
        throw new Error(`Unknown visual-assets command: ${name}`);
      }
      return callback({
        ...context,
        catalog,
        config: catalog.config,
      });
    },
  };

  return catalog;
}

/**
 * @param {{id?: string, run: Function}} definition
 */
export function definePipeline({ id, run }) {
  if (typeof run !== "function") {
    throw new Error(`Pipeline ${id ?? "<anonymous>"} must define run(context)`);
  }
  return { id, run };
}

export function reviewedFile(reviewedPath) {
  return {
    kind: "reviewed-file",
    reviewedPath,
  };
}

export function captureOutput({ candidatePath, capture }) {
  if (!candidatePath || typeof capture !== "function") {
    throw new Error(
      "captureOutput requires candidatePath and capture(context)",
    );
  }
  return {
    kind: "capture-output",
    candidatePath,
    capture,
  };
}

export function capturedSource({ reviewed, candidate }) {
  if (!reviewed || candidate?.kind !== "capture-output") {
    throw new Error(
      "capturedSource requires a reviewed path and captureOutput candidate",
    );
  }
  return {
    kind: "captured-source",
    reviewedPath: reviewed,
    candidate,
  };
}

export function yamlMediaBinding({
  file,
  sectionId,
  collection,
  title,
  mediaField,
  variantFields,
}) {
  return {
    kind: "yaml-media",
    file,
    sectionId,
    collection,
    title,
    mediaField,
    variantFields,
  };
}