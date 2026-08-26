import {
  defineAsset,
  defineVisualAssets,
  reviewedFile,
  yamlMediaBinding,
} from "../scripts/visual-assets/api.mjs";
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

export default defineVisualAssets({
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

  assets: [
    defineAsset({
      id: "provider-reasoning",
      claim:
        "Provider plugins can expose reasoning effort and verbosity as visible session settings.",
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
      freshnessTriggers: [
        "provider settings UI changes",
        "reasoning or verbosity schema changes",
        "mobile message/settings presentation changes",
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
          pipeline: providerCard({
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
          pipeline: providerCard({
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
    }),

    defineAsset({
      id: "provider-usage-cost",
      claim:
        "Provider metadata can make token, cache, duration, and cost information visible in a session.",
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
      freshnessTriggers: [
        "message footer or metadata presentation changes",
        "provider usage or cost schema changes",
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
          pipeline: providerCard({
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
          pipeline: providerCard({
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
    }),

    defineAsset({
      id: "chat-actions-workbench",
      claim:
        "Plugins can expose session and message actions through the mobile workbench.",
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
      freshnessTriggers: [
        "session action menu changes",
        "application action contract changes",
        "mobile action presentation changes",
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
          pipeline: workbenchPhone({
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
          pipeline: workbenchPhone({
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
    }),

    defineAsset({
      id: "session-snapshots-workbench",
      claim:
        "A session can expose checkpoint creation, selection, restoration, and deletion controls.",
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
      freshnessTriggers: [
        "snapshot action or dialog changes",
        "snapshot contract changes",
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
          pipeline: workbenchPhone({
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
          pipeline: workbenchPhone({
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
    }),

    defineAsset({
      id: "session-settings-plugins",
      claim:
        "Plugin UI schemas can contribute model and provider controls to per-session settings.",
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
      freshnessTriggers: [
        "session settings UI changes",
        "plugin UI schema changes",
        "provider option changes",
      ],
      variants: {
        light: {
          source: reviewedFile(
            "visual_assets/sources/session-settings-plugins-light.png",
          ),
          provenance: importedSource(
            "landing_page/public/session-settings-plugins.png",
          ),
          output: "public/session-settings-plugins.webp",
          pipeline: workbenchPhone({
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
          source: reviewedFile(
            "visual_assets/sources/session-settings-plugins-dark.png",
          ),
          provenance: importedSource(
            "landing_page/public/session-settings-plugins-dark.png",
          ),
          output: "public/session-settings-plugins-dark.webp",
          pipeline: workbenchPhone({
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
    }),
  ],
});