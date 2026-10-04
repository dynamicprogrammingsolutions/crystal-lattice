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
import { commandCapture } from "../scripts/visual-assets/producers/command.mjs";
import {
  runSessionFixtureCatalogCommand,
  sessionFixtureAssetCommands,
} from "../scripts/visual-assets/session-fixture.mjs";
import {
  runRuntimeUiCatalogCommand,
  runtimeUiFixtureAssetCommands,
} from "../scripts/visual-assets/runtime-ui-fixture.mjs";
import {
  centerExtent,
  crop,
  encodeWebp,
  imageMagickPipeline,
  focusCalloutPipeline,
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
    actionsLight:
      "mobile/crystal-lattice-control-rn/artifacts/website-visual/actions-light.png",
    actionsDark:
      "mobile/crystal-lattice-control-rn/artifacts/website-visual/actions-dark.png",
    snapshotsLight:
      "mobile/crystal-lattice-control-rn/artifacts/website-visual/snapshots-light.png",
    snapshotsDark:
      "mobile/crystal-lattice-control-rn/artifacts/website-visual/snapshots-dark.png",
    settingsLight:
      "mobile/crystal-lattice-control-rn/artifacts/website-visual/settings-light.png",
    settingsDark:
      "mobile/crystal-lattice-control-rn/artifacts/website-visual/settings-dark.png",
    usageLight:
      "mobile/crystal-lattice-control-rn/artifacts/website-visual/usage-light.png",
    usageDark:
      "mobile/crystal-lattice-control-rn/artifacts/website-visual/usage-dark.png",
    costLight:
      "mobile/crystal-lattice-control-rn/artifacts/website-visual/cost-light.png",
    costDark:
      "mobile/crystal-lattice-control-rn/artifacts/website-visual/cost-dark.png",
    heroLight:
      "mobile/crystal-lattice-control-rn/artifacts/website-visual/hero-light.png",
    heroDark:
      "mobile/crystal-lattice-control-rn/artifacts/website-visual/hero-dark.png",
    providerSettingsLight:
      "mobile/crystal-lattice-control-rn/artifacts/website-visual/provider-settings-light.png",
    providerSettingsDark:
      "mobile/crystal-lattice-control-rn/artifacts/website-visual/provider-settings-dark.png",
    pluginsLight:
      "mobile/crystal-lattice-control-rn/artifacts/website-visual/plugins-light.png",
    pluginsDark:
      "mobile/crystal-lattice-control-rn/artifacts/website-visual/plugins-dark.png",
    compiledLight:
      "mobile/crystal-lattice-control-rn/artifacts/website-visual/compiled-light.png",
    compiledDark:
      "mobile/crystal-lattice-control-rn/artifacts/website-visual/compiled-dark.png",
    vibeLight:
      "mobile/crystal-lattice-control-rn/artifacts/website-visual/vibe-light.png",
    vibeDark:
      "mobile/crystal-lattice-control-rn/artifacts/website-visual/vibe-dark.png",
    workspacesLight:
      "mobile/crystal-lattice-control-rn/artifacts/website-visual/workspaces-light.png",
    workspacesDark:
      "mobile/crystal-lattice-control-rn/artifacts/website-visual/workspaces-dark.png",
  },
});

const desktopWebsiteCapture = commandCapture({
  id: "desktop-website-visual",
  projectDirectory: "desktop/crystal-lattice-control-desktop-rn",
  command: ["npm", "run", "capture:website-visual:macos"],
  outputs: {
    agentCodexLight:
      "desktop/crystal-lattice-control-desktop-rn/artifacts/website-visual/agent-codex-light.png",
    agentCodexDark:
      "desktop/crystal-lattice-control-desktop-rn/artifacts/website-visual/agent-codex-dark.png",
    agentClaudeLight:
      "desktop/crystal-lattice-control-desktop-rn/artifacts/website-visual/agent-claude-light.png",
    agentClaudeDark:
      "desktop/crystal-lattice-control-desktop-rn/artifacts/website-visual/agent-claude-dark.png",
    crossDeviceLight:
      "desktop/crystal-lattice-control-desktop-rn/artifacts/website-visual/cross-device-light.png",
    crossDeviceDark:
      "desktop/crystal-lattice-control-desktop-rn/artifacts/website-visual/cross-device-dark.png",
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
  cropGeometry,
  resizeTo,
  extent,
  trimEdges = true,
  quality = 80,
}) {
  return imageMagickPipeline({
    id,
    operations: [
      cropGeometry ? crop(cropGeometry) : undefined,
      trimEdges ? trim() : undefined,
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

function workbenchModal(options) {
  return optimizedUiScreenshot({
    id: "workbench-modal",
    trimEdges: false,
    quality: 76,
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

function mobileHeroMedia() {
  return yamlMediaBinding({
    file: "src/content/pages/mobile.yaml",
    sectionId: "mobile-hero",
    mediaField: "image",
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

async function refreshSessionCommand(context) {
  return runSessionFixtureCatalogCommand(context, "refresh-session", {
    runtimeRequired: true,
  });
}

async function promoteSessionCommand(context) {
  return runSessionFixtureCatalogCommand(context, "promote-session", {
    mutate: true,
  });
}

async function refreshRuntimeUiCommand(context) {
  return runRuntimeUiCatalogCommand(context, "refresh-runtime-ui", {
    pythonRequired: true,
  });
}

async function promoteRuntimeUiCommand(context) {
  return runRuntimeUiCatalogCommand(context, "promote-runtime-ui", {
    mutate: true,
  });
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
    "refresh-session": refreshSessionCommand,
    "promote-session": promoteSessionCommand,
    "refresh-runtime-ui": refreshRuntimeUiCommand,
    "promote-runtime-ui": promoteRuntimeUiCommand,
  },

  assets: [
    defineAsset({
      id: "mobile-workbench",
      metadata: {
        claim:
          "The website workbench visuals use UI contracts produced by a canonical application configuration.",
      },
      config: {
        fixtureId: "mobile-workbench",
        config: "visual_assets/runtime/mobile-workbench/config.json",
        agent: "codex-openai",
        sessionFixture:
          "mobile/crystal-lattice-control-rn/src/testing/fixtures/websiteCodingPlanSession.json",
        reviewedFixture:
          "mobile/crystal-lattice-control-rn/src/testing/fixtures/websiteRuntimeUi.json",
      },
      commands: runtimeUiFixtureAssetCommands(),
    }),

    defineAsset({
      id: "coding-plan",
      metadata: {
        claim:
          "A reviewed real coding session supplies deterministic website capture content.",
      },
      config: {
        fixtureId: "coding-plan",
        extendReviewedFixture: true,
        manifest:
          "visual_assets/session_sources/starlette-gzip-responder/manifest.json",
        reviewedFixture:
          "mobile/crystal-lattice-control-rn/src/testing/fixtures/websiteCodingPlanSession.json",
      },
      commands: sessionFixtureAssetCommands(),
    }),

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
          alt: "Session settings with magnified medium reasoning effort and medium verbosity controls.",
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
            source: capturedSource({
              reviewed:
                "visual_assets/sources/provider-reasoning-light.png",
              candidate:
                mobileWebsiteCapture.output("settingsLight"),
            }),
            provenance: importedSource(
              "landing_page/public/provider-reasoning.png",
            ),
            output: "public/provider-reasoning.webp",
            build: focusCalloutPipeline({
              id: "provider-reasoning-focus-light",
              canvas: {
                width: 1000,
                height: 1315,
                background: "#F3F4F7",
              },
              original: {
                crop: "1206x1650+0+420",
                width: 720,
                height: 985,
                gravity: "north",
                geometry: "+0+190",
                dimPercent: 18,
                borderColor: "#D9DDE5",
                borderWidth: 1,
              },
              callout: {
                crop: "1040x410+80+1055",
                width: 920,
                height: 363,
                gravity: "north",
                geometry: "+0+500",
                borderColor: "#FFFFFF",
                borderWidth: 3,
                shadow: {
                  color: "rgba(0,0,0,0.55)",
                  geometry: "45x14+0+12",
                },
              },
              quality: 78,
            }),
            expected: {
              width: 1000,
              height: 1315,
              maxBytes: 60000,
              sha256:
                "1d10ffdb13d405fe9b495a6bf927b92a0a960b1570c8897e77cc4e3879e3725d",
            },
          },
          dark: {
            source: capturedSource({
              reviewed:
                "visual_assets/sources/provider-reasoning-dark.png",
              candidate:
                mobileWebsiteCapture.output("settingsDark"),
            }),
            provenance: importedSource(
              "landing_page/public/provider-reasoning-dark.png",
            ),
            output: "public/provider-reasoning-dark.webp",
            build: focusCalloutPipeline({
              id: "provider-reasoning-focus-dark",
              canvas: {
                width: 1000,
                height: 1315,
                background: "#0B0D10",
              },
              original: {
                crop: "1206x1650+0+420",
                width: 720,
                height: 985,
                gravity: "north",
                geometry: "+0+190",
                dimPercent: 10,
                borderColor: "#2C2F35",
                borderWidth: 1,
              },
              callout: {
                crop: "1040x410+80+1055",
                width: 920,
                height: 363,
                gravity: "north",
                geometry: "+0+500",
                borderColor: "#3A3A3C",
                borderWidth: 3,
                shadow: {
                  color: "rgba(0,0,0,0.78)",
                  geometry: "45x14+0+12",
                },
              },
              quality: 78,
            }),
            expected: {
              width: 1000,
              height: 1315,
              maxBytes: 45000,
              sha256:
                "80b7364913bd58dc359dbe02a013d5434c242abd9a2159287f5868d7ab3b41e5",
            },
          },
        },
      },
      lifecycle: capturedImageLifecycle,
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
          alt: "A completed coding-plan response with magnified input, estimated cached, completion, reasoning-token, and estimated-cost metadata.",
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
            source: capturedSource({
              reviewed:
                "visual_assets/sources/provider-usage-cost-light.png",
              candidate:
                mobileWebsiteCapture.output("usageLight"),
            }),
            provenance: importedSource(
              "landing_page/public/provider-usage-cost.png",
            ),
            output: "public/provider-usage-cost.webp",
            build: focusCalloutPipeline({
              id: "provider-usage-focus-light",
              canvas: {
                width: 940,
                height: 1334,
                background: "#F3F4F7",
              },
              original: {
                crop: "1206x1900+0+450",
                width: 660,
                height: 1040,
                gravity: "north",
                geometry: "+0+160",
                dimPercent: 12,
                borderColor: "#D9DDE5",
                borderWidth: 1,
              },
              callout: {
                crop: "1050x180+75+1795",
                width: 880,
                height: 151,
                gravity: "north",
                geometry: "+0+850",
                borderColor: "#FFFFFF",
                borderWidth: 3,
                shadow: {
                  color: "rgba(0,0,0,0.55)",
                  geometry: "45x14+0+12",
                },
              },
              quality: 78,
            }),
            expected: {
              width: 940,
              height: 1334,
              maxBytes: 100000,
              sha256:
                "527a3494070e8b9a37774e66afcb5e2b38984fa3c8d204201eedf4737d734f0a",
            },
          },
          dark: {
            source: capturedSource({
              reviewed:
                "visual_assets/sources/provider-usage-cost-dark.png",
              candidate:
                mobileWebsiteCapture.output("usageDark"),
            }),
            provenance: importedSource(
              "landing_page/public/provider-usage-cost-dark.png",
            ),
            output: "public/provider-usage-cost-dark.webp",
            build: focusCalloutPipeline({
              id: "provider-usage-focus-dark",
              canvas: {
                width: 940,
                height: 1334,
                background: "#0B0D10",
              },
              original: {
                crop: "1206x1900+0+450",
                width: 660,
                height: 1040,
                gravity: "north",
                geometry: "+0+160",
                dimPercent: 6,
                borderColor: "#2C2F35",
                borderWidth: 1,
              },
              callout: {
                crop: "1050x180+75+1795",
                width: 880,
                height: 151,
                gravity: "north",
                geometry: "+0+850",
                borderColor: "#3A3A3C",
                borderWidth: 3,
                shadow: {
                  color: "rgba(0,0,0,0.78)",
                  geometry: "45x14+0+12",
                },
              },
              quality: 78,
            }),
            expected: {
              width: 940,
              height: 1334,
              maxBytes: 100000,
              sha256:
                "3749a82c6afb16e1af85fe286061c1ffe0c67b5703135670c1b08028b009491e",
            },
          },
        },
      },
      lifecycle: capturedImageLifecycle,
    }),

    defineAsset({
      id: "mobile-active-session",
      metadata: {
        claim:
          "The mobile client can continue a realistic coding-agent session from a phone.",
        freshnessTriggers: [
          "mobile chat header, transcript, composer, or navigation changes",
          "reviewed coding-plan session changes",
          "mobile-page hero layout changes",
        ],
      },
      config: {
        presentation: {
          alt: "Crystal Lattice mobile chat showing a Starlette compatibility plan with turn usage, estimated cost, agent, and session status.",
          width: 1000,
          height: 2025,
        },
        contentBindings: [mobileHeroMedia()],
        variants: {
          light: {
            source: capturedSource({
              reviewed:
                "visual_assets/sources/mobile-active-session-light.png",
              candidate:
                mobileWebsiteCapture.output("heroLight"),
            }),
            provenance: {
              kind: "detox-capture",
              fixture: "coding-plan",
              output: "hero-light.png",
            },
            output: "public/mobile-active-session.webp",
            build: workbenchModal({
              cropGeometry: "1206x2442+0+180",
              resizeTo: "1000x>",
              quality: 54,
            }),
            expected: {
              width: 1000,
              height: 2025,
              maxBytes: 80000,
              sha256:
                "55a4f00c51b57fc355059923a26eab75f96330850b62b70c2f0c48b6be3a4c84",
            },
          },
          dark: {
            source: capturedSource({
              reviewed:
                "visual_assets/sources/mobile-active-session-dark.png",
              candidate:
                mobileWebsiteCapture.output("heroDark"),
            }),
            provenance: {
              kind: "detox-capture",
              fixture: "coding-plan",
              output: "hero-dark.png",
            },
            output: "public/mobile-active-session-dark.webp",
            build: workbenchModal({
              cropGeometry: "1206x2442+0+180",
              resizeTo: "1000x>",
              quality: 30,
            }),
            expected: {
              width: 1000,
              height: 2025,
              maxBytes: 80000,
              sha256:
                "ce0aa2813b683d32068dc03a2b64b146be23ab52269d3cbc929700c357b05ff8",
            },
          },
        },
      },
      lifecycle: capturedImageLifecycle,
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
          alt: "Session actions menu showing plugin-provided copy, title, deletion, summarization, and native compaction controls alongside session settings.",
          width: 1000,
          height: 2025,
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
            source: capturedSource({
              reviewed:
                "visual_assets/sources/chat-actions-workbench-light.png",
              candidate:
                mobileWebsiteCapture.output("actionsLight"),
            }),
            provenance: importedSource(
              "landing_page/public/chat-actions-workbench.png",
            ),
            output: "public/chat-actions-workbench.webp",
            build: workbenchModal({
              cropGeometry: "1206x2442+0+180",
              resizeTo: "1000x>",
            }),
            expected: {
              width: 1000,
              height: 2025,
              maxBytes: 55000,
              sha256:
                "bef7d5cefa6680c6b386f20c22b0c65feef538ec66986c1ff43cbb036ff6644a",
            },
          },
          dark: {
            source: capturedSource({
              reviewed:
                "visual_assets/sources/chat-actions-workbench-dark.png",
              candidate:
                mobileWebsiteCapture.output("actionsDark"),
            }),
            provenance: importedSource(
              "landing_page/public/chat-actions-workbench-dark.png",
            ),
            output: "public/chat-actions-workbench-dark.webp",
            build: workbenchModal({
              cropGeometry: "1206x2442+0+180",
              resizeTo: "1000x>",
            }),
            expected: {
              width: 1000,
              height: 2025,
              maxBytes: 55000,
              sha256:
                "9d476332506e8ec1c42849dbb216c1d394b8d9146599948caa6fb7966ef6aa21",
            },
          },
        },
      },
      lifecycle: capturedImageLifecycle,
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
          alt: "Snapshots dialog showing automatic pre-compaction and pre-deletion recovery points with Select, Restore, and Delete controls.",
          width: 1000,
          height: 2025,
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
            source: capturedSource({
              reviewed:
                "visual_assets/sources/session-snapshots-workbench-light.png",
              candidate:
                mobileWebsiteCapture.output("snapshotsLight"),
            }),
            provenance: importedSource(
              "landing_page/public/session-snapshots-workbench.png",
            ),
            output: "public/session-snapshots-workbench.webp",
            build: workbenchModal({
              cropGeometry: "1206x2442+0+180",
              resizeTo: "1000x>",
            }),
            expected: {
              width: 1000,
              height: 2025,
              maxBytes: 55000,
              sha256:
                "31808b2f74ca0d60dd90955c0327b8d3d4bd57b3216d0fa6813679d244866c7a",
            },
          },
          dark: {
            source: capturedSource({
              reviewed:
                "visual_assets/sources/session-snapshots-workbench-dark.png",
              candidate:
                mobileWebsiteCapture.output("snapshotsDark"),
            }),
            provenance: importedSource(
              "landing_page/public/session-snapshots-workbench-dark.png",
            ),
            output: "public/session-snapshots-workbench-dark.webp",
            build: workbenchModal({
              cropGeometry: "1206x2442+0+180",
              resizeTo: "1000x>",
            }),
            expected: {
              width: 1000,
              height: 2025,
              maxBytes: 55000,
              sha256:
                "865b735fc75522a600503dd8bf607f0ab86feade82d69d50ca0469559fe43478",
            },
          },
        },
      },
      lifecycle: capturedImageLifecycle,
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
          alt: "Session settings showing OpenAI model, reasoning, verbosity, prompt cache, web search, and compaction transcript controls contributed by plugins.",
          width: 1000,
          height: 2025,
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
            build: workbenchModal({
              cropGeometry: "1206x2442+0+180",
              resizeTo: "1000x>",
            }),
            expected: {
              width: 1000,
              height: 2025,
              maxBytes: 60000,
              sha256:
                "a831addcc2865c72b495d4c18f0f14a0f75a1821f1dd4ba2536d2bdc903c3e47",
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
            build: workbenchModal({
              cropGeometry: "1206x2442+0+180",
              resizeTo: "1000x>",
            }),
            expected: {
              width: 1000,
              height: 2025,
              maxBytes: 60000,
              sha256:
                "86d7add2912ded1f843a9ce73f3ffb659225acf1b6272d6ab7d0922f02d35d3d",
            },
          },
        },
      },
      lifecycle: capturedImageLifecycle,
    }),
  ],
});