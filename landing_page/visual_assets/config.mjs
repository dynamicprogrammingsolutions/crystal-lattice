import {
  capturedSource,
  defineAsset,
  defineVisualAssets,
  reviewedFile,
  yamlMediaBinding,
} from "../scripts/visual-assets/api.mjs";
import {
  buildImageCandidates,
  captureImageSources,
  comparePublishedImages,
  describeImageAsset,
  inspectImageCandidates,
  prepareImagePublication,
  prepareImageSourcePromotion,
  validateImageAssetDefinition,
  validateImageCandidates,
} from "../scripts/visual-assets/lifecycle/image.mjs";
import { detoxCapture } from "../scripts/visual-assets/producers/detox.mjs";
import {
  centerExtent,
  encodeWebp,
  imageMagickPipeline,
  normalizeSrgb,
  resize,
  stripMetadata,
  trim,
} from "../scripts/visual-assets/operations.mjs";

const importedRevision = "e88aa46ee8d6bd0969c63c78f8e152f1fd938974";

const mobileWebsiteCapture = detoxCapture({
  id: "mobile-website-visual",
  projectDirectory: "mobile/crystal-lattice-control-rn",
  command: [
    "npm",
    "run",
    "detox:capture:website-visual:ios",
  ],
  outputs: {
    settingsLight:
      "mobile/crystal-lattice-control-rn/artifacts/website-visual/session-settings-light.png",
    settingsDark:
      "mobile/crystal-lattice-control-rn/artifacts/website-visual/session-settings-dark.png",
  },
});

const reviewedImageLifecycle = {
  describe: describeImageAsset,
  validateDefinition: validateImageAssetDefinition,
  buildCandidate: buildImageCandidates,
  inspectCandidate: inspectImageCandidates,
  validateCandidate: validateImageCandidates,
  comparePublished: comparePublishedImages,
  preparePublication: prepareImagePublication,
};

const capturedImageLifecycle = {
  ...reviewedImageLifecycle,
  capture: captureImageSources,
  prepareSourcePromotion:
    prepareImageSourcePromotion,
};

function optimizedUiScreenshot({
  id,
  resizeTo,
  extent,
  quality = 80,
}) {
  return imageMagickPipeline({
    id,
    operations: [
      trim(),
      resize(resizeTo),
      extent ? centerExtent(extent) : undefined,
      normalizeSrgb(),
      stripMetadata(),
      encodeWebp({ quality, method: 6 }),
    ],
  });
}

function providerCard(options) {
  return optimizedUiScreenshot({
    id: "provider-card",
    ...options,
  });
}

function workbenchPhone(options) {
  return optimizedUiScreenshot({
    id: "workbench-phone",
    ...options,
  });
}

function homeMedia({ sectionId, collection, title, mediaField }) {
  return yamlMediaBinding({
    file: "src/content/pages/home.yaml",
    sectionId,
    collection,
    title,
    mediaField,
    variantFields: {
      light: "src",
      dark: "srcDark",
    },
  });
}

function importedSource(originalPath) {
  return {
    revision: importedRevision,
    originalPath,
  };
}

function evaluateBudgets(budgets, results, strict) {
  return budgets.map((budget) => {
    const applicable = results.filter((result) =>
      budget.select({
        assetId: result.asset_id,
        variantName: result.variant,
      }),
    );
    const bytes = applicable.reduce(
      (sum, result) => sum + (result.bytes ?? 0),
      0,
    );
    const withinBudget = bytes <= budget.maxBytes;
    if (strict && !withinBudget) {
      throw new Error(
        `${budget.id}: ${bytes} bytes exceeds ${budget.maxBytes}`,
      );
    }
    return {
      id: budget.id,
      max_bytes: budget.maxBytes,
      selected_assets: applicable.length,
      bytes,
      within_budget: withinBudget,
    };
  });
}

async function listCommand(context) {
  return {
    kind: "list",
    assets: await context.describeAssets(),
  };
}

async function inspectCommand(context) {
  const results = await context.forEachSelected(
    async (assetContext) => {
      if (assetContext.hasCommand("inspect")) {
        return assetContext.runCommand("inspect");
      }

      assetContext.requireLifecycles([
        "validateDefinition",
        "buildCandidate",
        "inspectCandidate",
        "validateCandidate",
      ]);
      await assetContext.runLifecycle("validateDefinition");
      const candidates = await assetContext.runLifecycle(
        "buildCandidate",
      );
      const inspected = await assetContext.runLifecycle(
        "inspectCandidate",
        { candidates },
      );
      const validated = await assetContext.runLifecycle(
        "validateCandidate",
        {
          candidates: inspected,
          strict: false,
        },
      );
      return validated.map((candidate) => candidate.result);
    },
    { defaultAll: true },
  );
  return context.writeReport("inspect", {
    results,
    budgets: evaluateBudgets(context.config.budgets, results, false),
  });
}

async function checkCommand(context) {
  const results = await context.forEachSelected(
    async (assetContext) => {
      if (assetContext.hasCommand("check")) {
        return assetContext.runCommand("check");
      }

      assetContext.requireLifecycles([
        "validateDefinition",
        "buildCandidate",
        "inspectCandidate",
        "validateCandidate",
        "comparePublished",
      ]);
      await assetContext.runLifecycle("validateDefinition");
      const candidates = await assetContext.runLifecycle(
        "buildCandidate",
      );
      const inspected = await assetContext.runLifecycle(
        "inspectCandidate",
        { candidates },
      );
      const validated = await assetContext.runLifecycle(
        "validateCandidate",
        {
          candidates: inspected,
          strict: true,
        },
      );
      await assetContext.runLifecycle("comparePublished", {
        candidates: validated,
      });
      return validated.map((candidate) => candidate.result);
    },
    { defaultAll: true },
  );
  return context.writeReport("check", {
    results,
    budgets: evaluateBudgets(context.config.budgets, results, true),
  });
}

async function updateCommand(context) {
  const prepared = await context.forEachSelected(
    async (assetContext) => {
      if (assetContext.hasCommand("update")) {
        return assetContext.runCommand("update");
      }

      assetContext.requireLifecycles([
        "validateDefinition",
        "buildCandidate",
        "inspectCandidate",
        "validateCandidate",
        "preparePublication",
      ]);
      await assetContext.runLifecycle("validateDefinition");
      const candidates = await assetContext.runLifecycle(
        "buildCandidate",
      );
      const inspected = await assetContext.runLifecycle(
        "inspectCandidate",
        { candidates },
      );
      const validated = await assetContext.runLifecycle(
        "validateCandidate",
        {
          candidates: inspected,
          strict: true,
        },
      );
      return assetContext.runLifecycle("preparePublication", {
        candidates: validated,
      });
    },
    { requireSelection: true },
  );
  const results = prepared
    .map((effect) => effect.report)
    .filter(Boolean);
  const budgets = evaluateBudgets(
    context.config.budgets,
    results,
    true,
  );
  await context.applyAll(prepared);
  return context.writeReport("update", {
    results,
    budgets,
  });
}

async function captureCommand(context) {
  const results = await context.forEachSelected(
    async (assetContext) => {
      if (assetContext.hasCommand("capture")) {
        return assetContext.runCommand("capture");
      }
      if (assetContext.hasLifecycle("capture")) {
        return assetContext.runLifecycle("capture");
      }
      return assetContext.unsupported("capture");
    },
    { requireSelection: true },
  );
  return context.writeReport("capture", { results });
}

async function promoteSourceCommand(context) {
  const prepared = await context.forEachSelected(
    async (assetContext) => {
      if (assetContext.hasCommand("promote-source")) {
        return assetContext.runCommand("promote-source");
      }
      if (assetContext.hasLifecycle("prepareSourcePromotion")) {
        return assetContext.runLifecycle(
          "prepareSourcePromotion",
        );
      }
      return assetContext.unsupported("promote-source");
    },
    { requireSelection: true },
  );
  const results = prepared
    .map((effect) => effect.report)
    .filter(Boolean);
  await context.applyAll(prepared);
  return context.writeReport("promote-source", { results });
}

export default defineVisualAssets({
  config: {
    budgets: [
      {
        id: "light-active-theme",
        maxBytes: 300000,
        select: ({ variantName }) => variantName === "light",
      },
      {
        id: "dark-active-theme",
        maxBytes: 300000,
        select: ({ variantName }) => variantName === "dark",
      },
    ],
  },

  commands: {
    list: listCommand,
    inspect: inspectCommand,
    check: checkCommand,
    update: updateCommand,
    capture: captureCommand,
    "promote-source": promoteSourceCommand,
  },

  assets: [
    defineAsset({
      id: "provider-reasoning",
      metadata: {
        claim:
          "Provider plugins can expose reasoning effort and verbosity as visible session settings.",
        freshnessTriggers: [
          "provider settings UI changes",
          "reasoning or verbosity schema changes",
          "mobile message/settings presentation changes",
        ],
      },
      config: {
        presentation: {
          alt: "Session settings showing reasoning enabled, medium reasoning effort, and medium verbosity.",
          width: 1000,
          height: 1315,
        },
        contentBindings: [
          homeMedia({
            sectionId: "native-provider-features",
            collection: "items",
            title: "Reasoning and verbosity",
            mediaField: "media",
          }),
        ],
        variants: {
          light: {
            source: reviewedFile(
              "visual_assets/sources/provider-reasoning-light.png",
            ),
            provenance: importedSource(
              "landing_page/public/provider-reasoning.png",
            ),
            output: "public/provider-reasoning.webp",
            build: providerCard({
              resizeTo: "1000x1334>",
            }),
            expected: {
              width: 1000,
              height: 1315,
              maxBytes: 60000,
              sha256:
                "a47b68b60e814595ee62199c5caebbbc6e39cd23dae061cbece7fb4a3d5deea8",
            },
          },
          dark: {
            source: reviewedFile(
              "visual_assets/sources/provider-reasoning-dark.png",
            ),
            provenance: importedSource(
              "landing_page/public/provider-reasoning-dark.png",
            ),
            output: "public/provider-reasoning-dark.webp",
            build: providerCard({
              resizeTo: "1000x1315^",
              extent: "1000x1315",
            }),
            expected: {
              width: 1000,
              height: 1315,
              maxBytes: 45000,
              sha256:
                "158ce46b1320a01edd52f60fcd5868ddfdf01303878ba707ef3290c4a406815d",
            },
          },
        },
      },
      lifecycle: reviewedImageLifecycle,
    }),

    defineAsset({
      id: "provider-usage-cost",
      metadata: {
        claim:
          "Provider metadata can make token, cache, duration, and cost information visible in a session.",
        freshnessTriggers: [
          "message footer or metadata presentation changes",
          "provider usage or cost schema changes",
        ],
      },
      config: {
        presentation: {
          alt: "A session message with visible input, cached, output, cost, and duration metadata.",
          width: 940,
          height: 1334,
        },
        contentBindings: [
          homeMedia({
            sectionId: "native-provider-features",
            collection: "items",
            title: "Usage and cost transparency",
            mediaField: "media",
          }),
        ],
        variants: {
          light: {
            source: reviewedFile(
              "visual_assets/sources/provider-usage-cost-light.png",
            ),
            provenance: importedSource(
              "landing_page/public/provider-usage-cost.png",
            ),
            output: "public/provider-usage-cost.webp",
            build: providerCard({
              resizeTo: "1000x1334>",
            }),
            expected: {
              width: 940,
              height: 1334,
              maxBytes: 100000,
              sha256:
                "9d4570663cbb38f477afe18423442e421e4962972aa5f3104c54dfe0875d6e34",
            },
          },
          dark: {
            source: reviewedFile(
              "visual_assets/sources/provider-usage-cost-dark.png",
            ),
            provenance: importedSource(
              "landing_page/public/provider-usage-cost-dark.png",
            ),
            output: "public/provider-usage-cost-dark.webp",
            build: providerCard({
              resizeTo: "940x1334^",
              extent: "940x1334",
            }),
            expected: {
              width: 940,
              height: 1334,
              maxBytes: 100000,
              sha256:
                "8a8ad4b107e577483cd9e2bde6772735a193eb3b907f7d6556cab2137bcad96d",
            },
          },
        },
      },
      lifecycle: reviewedImageLifecycle,
    }),

    defineAsset({
      id: "chat-actions-workbench",
      metadata: {
        claim:
          "Plugins can expose session and message actions through the mobile workbench.",
        freshnessTriggers: [
          "session action menu changes",
          "application action contract changes",
          "mobile action presentation changes",
        ],
      },
      config: {
        presentation: {
          alt: "Session actions menu listing settings, plugins, snapshots, copy, delete, title, and other plugin-provided actions.",
          width: 693,
          height: 1400,
        },
        contentBindings: [
          homeMedia({
            sectionId: "session-workbench",
            collection: "gallery",
            title: "Chat actions",
          }),
        ],
        variants: {
          light: {
            source: reviewedFile(
              "visual_assets/sources/chat-actions-workbench-light.png",
            ),
            provenance: importedSource(
              "landing_page/public/chat-actions-workbench.png",
            ),
            output: "public/chat-actions-workbench.webp",
            build: workbenchPhone({
              resizeTo: "700x1400>",
            }),
            expected: {
              width: 693,
              height: 1400,
              maxBytes: 45000,
              sha256:
                "547f2c71815fbe499cf4d3c8e125f76821658ef2f0a8fcbef1c9578b8c228f48",
            },
          },
          dark: {
            source: reviewedFile(
              "visual_assets/sources/chat-actions-workbench-dark.png",
            ),
            provenance: importedSource(
              "landing_page/public/chat-actions-workbench-dark.png",
            ),
            output: "public/chat-actions-workbench-dark.webp",
            build: workbenchPhone({
              resizeTo: "693x1400^",
              extent: "693x1400",
            }),
            expected: {
              width: 693,
              height: 1400,
              maxBytes: 40000,
              sha256:
                "5e4d0d12a6968089cd4a6ccc7f3dc023eef5d3edd678921ebb6c150cdce3c2c3",
            },
          },
        },
      },
      lifecycle: reviewedImageLifecycle,
    }),

    defineAsset({
      id: "session-snapshots-workbench",
      metadata: {
        claim:
          "A session can expose checkpoint creation, selection, restoration, and deletion controls.",
        freshnessTriggers: [
          "snapshot action or dialog changes",
          "snapshot contract changes",
        ],
      },
      config: {
        presentation: {
          alt: "Snapshots dialog with Create, Select, Restore, and Delete controls over a session.",
          width: 693,
          height: 1400,
        },
        contentBindings: [
          homeMedia({
            sectionId: "session-workbench",
            collection: "gallery",
            title: "Snapshots",
          }),
        ],
        variants: {
          light: {
            source: reviewedFile(
              "visual_assets/sources/session-snapshots-workbench-light.png",
            ),
            provenance: importedSource(
              "landing_page/public/session-snapshots-workbench.png",
            ),
            output: "public/session-snapshots-workbench.webp",
            build: workbenchPhone({
              resizeTo: "700x1400>",
            }),
            expected: {
              width: 693,
              height: 1400,
              maxBytes: 50000,
              sha256:
                "0756a2e3f65777e1ae6e411502fd7e47426b71616627c7b02cfbdb8e5f05e3d2",
            },
          },
          dark: {
            source: reviewedFile(
              "visual_assets/sources/session-snapshots-workbench-dark.png",
            ),
            provenance: importedSource(
              "landing_page/public/session-snapshots-workbench-dark.png",
            ),
            output: "public/session-snapshots-workbench-dark.webp",
            build: workbenchPhone({
              resizeTo: "693x1400^",
              extent: "693x1400",
            }),
            expected: {
              width: 693,
              height: 1400,
              maxBytes: 45000,
              sha256:
                "c9b5f60717cab797dd83ebf7dc6d5a6205b2b4864bb5b348ff0f0d16cb8235f6",
            },
          },
        },
      },
      lifecycle: reviewedImageLifecycle,
    }),

    defineAsset({
      id: "session-settings-plugins",
      metadata: {
        claim:
          "Plugin UI schemas can contribute model and provider controls to per-session settings.",
        freshnessTriggers: [
          "session settings UI changes",
          "plugin UI schema changes",
          "provider option changes",
        ],
      },
      config: {
        presentation: {
          alt: "Session settings showing model, reasoning, verbosity, caching, web-search, and format controls contributed by plugins.",
          width: 693,
          height: 1400,
        },
        contentBindings: [
          homeMedia({
            sectionId: "session-workbench",
            collection: "gallery",
            title: "Settings and plugins",
          }),
        ],
        variants: {
          light: {
            source: capturedSource({
              reviewed:
                "visual_assets/sources/session-settings-plugins-light.png",
              candidate:
                mobileWebsiteCapture.output("settingsLight"),
            }),
            provenance: importedSource(
              "landing_page/public/session-settings-plugins.png",
            ),
            output: "public/session-settings-plugins.webp",
            build: workbenchPhone({
              resizeTo: "700x1400>",
            }),
            expected: {
              width: 693,
              height: 1400,
              maxBytes: 55000,
              sha256:
                "cdb0579b45b5cd9de9af98ff82720c8ad12b231b37b3adbe9623efcdbc3d6435",
            },
          },
          dark: {
            source: capturedSource({
              reviewed:
                "visual_assets/sources/session-settings-plugins-dark.png",
              candidate:
                mobileWebsiteCapture.output("settingsDark"),
            }),
            provenance: importedSource(
              "landing_page/public/session-settings-plugins-dark.png",
            ),
            output: "public/session-settings-plugins-dark.webp",
            build: workbenchPhone({
              resizeTo: "693x1400^",
              extent: "693x1400",
            }),
            expected: {
              width: 693,
              height: 1400,
              maxBytes: 50000,
              sha256:
                "239f18bb2fd43010e63348205b04ed9f96bb1b2546b7964ca658df6a9eeb2fbd",
            },
          },
        },
      },
      lifecycle: capturedImageLifecycle,
    }),
  ],
});