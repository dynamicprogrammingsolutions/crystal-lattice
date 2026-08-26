# Visual Assets

The landing package uses an executable JavaScript catalog to produce,
validate, and publish screenshots and other visual files.

Use this guide when adding or changing:

- an asset;
- a build pipeline;
- a direct asset command;
- reusable lifecycle callbacks;
- a captured source;
- a catalog command.

For implementation internals, see
[Visual content and screenshot generation](development/visual-content-and-screenshot-generation.md).

## Locations

```text
landing_page/
├── visual_assets/
│   ├── config.mjs       # Catalog commands, assets, and shared builds
│   └── sources/         # Reviewed, sanitized source masters
├── public/              # Optimized deployed derivatives
├── artifacts/
│   └── visual-assets/   # Ignored candidates, reports, and browser captures
└── scripts/
    └── visual-assets/   # Reusable API and implementations
```

Do not place unreviewed captures in `visual_assets/sources/` or optimized
derivatives. Capture candidates belong under an ignored `artifacts/`
directory.

## Catalog Model

The catalog is created with:

```js
defineVisualAssets({
  config,
  commands,
  assets,
});
```

The common asset shape is:

```js
defineAsset({
  id,
  metadata,
  config,
  commands,
  lifecycle,
});
```

These fields have distinct responsibilities:

| Field | Purpose |
|---|---|
| `id` | Stable asset selector used by the CLI and reports |
| `metadata` | Non-operational claim, provenance, and freshness information |
| `config` | Arbitrary asset-specific data interpreted by its callbacks |
| `commands` | Complete asset implementations for catalog commands |
| `lifecycle` | Smaller reusable stages composed by catalog commands |

An asset may define:

- only direct commands;
- only lifecycle callbacks;
- both direct commands and lifecycle callbacks.

The catalog command decides explicitly which form it uses.

## Current Commands

List assets:

```bash
yarn visual-assets:list
```

Inspect one asset or variant:

```bash
yarn visual-assets:inspect provider-reasoning
yarn visual-assets:inspect provider-reasoning --variant dark
```

Inspect the complete catalog:

```bash
yarn visual-assets:inspect
```

Check one asset or the complete catalog:

```bash
yarn visual-assets:check provider-reasoning
yarn visual-assets:check
```

Update an explicitly selected asset or all assets:

```bash
yarn visual-assets:update provider-reasoning
yarn visual-assets:update provider-reasoning --variant dark
yarn visual-assets:update --all
```

Capture and promote a source when the selected asset supports those
operations:

```bash
yarn visual-assets:capture mobile-hero
yarn visual-assets:promote-source mobile-hero --variant dark
```

Catalog command names are derived from `defineVisualAssets({ commands })`. A
new catalog command can be invoked through the base script without adding a
package shortcut:

```bash
yarn visual-assets <command> [arguments]
```

## Add an Image Using the Current Lifecycle

The current reviewed-image assets share:

```js
const reviewedImageLifecycle = {
  describe: describeImageAsset,
  validateDefinition: validateImageAssetDefinition,
  buildCandidate: buildImageCandidates,
  inspectCandidate: inspectImageCandidates,
  validateCandidate: validateImageCandidates,
  comparePublished: comparePublishedImages,
  preparePublication: prepareImagePublication,
};
```

Add an asset to `visual_assets/config.mjs`:

```js
defineAsset({
  id: "new-provider-control",

  metadata: {
    claim:
      "The provider exposes a visible per-session control.",

    freshnessTriggers: [
      "provider control schema changes",
      "session settings presentation changes",
    ],
  },

  config: {
    presentation: {
      alt:
        "Session settings showing the provider control.",
      width: 1000,
      height: 1315,
    },

    contentBindings: [
      homeMedia({
        sectionId: "native-provider-features",
        collection: "items",
        title: "Provider control",
        mediaField: "media",
      }),
    ],

    variants: {
      light: {
        source: reviewedFile(
          "visual_assets/sources/new-provider-control-light.png",
        ),

        output:
          "public/new-provider-control.webp",

        build: providerCard({
          resizeTo: "1000x1334>",
        }),

        expected: {
          width: 1000,
          height: 1315,
          maxBytes: 60000,
          sha256: "...",
        },
      },

      dark: {
        source: reviewedFile(
          "visual_assets/sources/new-provider-control-dark.png",
        ),

        output:
          "public/new-provider-control-dark.webp",

        build: providerCard({
          resizeTo: "1000x1315^",
          extent: "1000x1315",
        }),

        expected: {
          width: 1000,
          height: 1315,
          maxBytes: 60000,
          sha256: "...",
        },
      },
    },
  },

  lifecycle: reviewedImageLifecycle,
});
```

Then:

1. add the reviewed source masters;
2. add the corresponding content fields;
3. run `visual-assets:inspect`;
4. review the candidates and record their expectations;
5. run `visual-assets:update` for the asset;
6. run `visual-assets:check`.

## Define a Reusable Build

A build receives a source path and must create the requested candidate path.

The current ImageMagick helper accepts ordinary JavaScript operations:

```js
function desktopScreenshot({
  resizeTo,
  extent,
}) {
  return imageMagickPipeline({
    id: "desktop-screenshot",

    operations: [
      trim(),
      resize(resizeTo),
      extent
        ? centerExtent(extent)
        : undefined,
      normalizeSrgb(),
      stripMetadata(),
      encodeWebp({
        quality: 82,
        method: 6,
      }),
    ],
  });
}
```

Use it in an asset:

```js
build: desktopScreenshot({
  resizeTo: "1400x1000>",
}),
```

An ImageMagick-specific operation can be added programmatically:

```js
const removeCaptureBorder =
  imageMagickArguments(
    "remove-capture-border",
    () => [
      "-shave",
      "3x4",
    ],
  );
```

A build does not need to use ImageMagick. Implement the `run(context)` contract
directly:

```js
const customBuild = definePipeline({
  id: "custom-build",

  async run(context) {
    await renderCustomVisual({
      source: context.sourcePath,
      output: context.candidatePath,
    });
  },
});
```

## Define a Direct-Command Asset

Use direct commands when an asset owns a complete process that does not benefit
from shared lifecycle composition:

```js
defineAsset({
  id: "generated-diagram",

  config: {
    model:
      "visual_assets/sources/diagram-model.json",
    output:
      "public/generated-diagram.svg",
  },

  commands: {
    inspect: inspectGeneratedDiagram,
    check: checkGeneratedDiagram,
    update: prepareGeneratedDiagramUpdate,
  },
});
```

The command callback receives:

```js
{
  asset,
  metadata,
  config,
  repositoryRoot,
  landingRoot,
  artifactRoot,
  variantName,
  run,
  artifactPath,
  input,
}
```

Read-only command callbacks return report entries.

A durable mutating command such as `update` returns one or more prepared
effects:

```js
async function prepareGeneratedDiagramUpdate(
  context,
) {
  const candidate = await buildAndValidateDiagram(
    context,
  );

  return {
    report: candidate.report,

    async apply() {
      await publishDiagram(candidate);
    },
  };
}
```

The catalog prepares every selected asset before calling any `apply()`
function.

## Define Lifecycle Callbacks

Lifecycle callbacks are named stages interpreted by catalog commands:

```js
defineAsset({
  id: "lifecycle-asset",

  config: {
    // Asset-specific configuration.
  },

  lifecycle: {
    validateDefinition,
    buildCandidate,
    inspectCandidate,
    validateCandidate,
    comparePublished,
    preparePublication,
  },
});
```

Lifecycle names are not hardcoded in the runner. They become meaningful when a
catalog command calls them:

```js
const candidate = await assetContext.runLifecycle(
  "buildCandidate",
);
```

Changing or introducing lifecycle stages requires changing the catalog command
and affected assets, not the runner or CLI.

## Combine Commands and Lifecycle

A captured image may own `capture` directly while using the shared image
lifecycle for inspection, checking, and publication:

```js
defineAsset({
  id: "mobile-hero",

  config: {
    // Capture and image configuration.
  },

  commands: {
    capture: captureMobileHero,
  },

  lifecycle: {
    prepareSourcePromotion:
      prepareImageSourcePromotion,

    validateDefinition:
      validateImageAssetDefinition,

    buildCandidate:
      buildImageCandidates,

    inspectCandidate:
      inspectImageCandidates,

    validateCandidate:
      validateImageCandidates,

    comparePublished:
      comparePublishedImages,

    preparePublication:
      prepareImagePublication,
  },
});
```

The catalog command explicitly decides whether to run a direct command or
compose lifecycle stages.

## Add Capture and Source Promotion

A captured source keeps an ignored candidate separate from the reviewed
source:

```js
source: capturedSource({
  reviewed:
    "visual_assets/sources/mobile-hero-dark.png",

  candidate:
    mobileCapture.output("heroDark"),
}),
```

Attach the source callbacks:

```js
lifecycle: {
  capture: captureImageSources,
  prepareSourcePromotion:
    prepareImageSourcePromotion,

  // Build and validation lifecycle...
},
```

The lifecycle is:

```text
capture
  -> ignored candidate
  -> human review
  -> promote-source
  -> reviewed source master
  -> inspect/update/check
  -> public derivative
```

`check` and `update` always read the reviewed source. They do not invoke the
capture producer.

## Add a Detox Producer

Define one producer:

```js
const mobileCapture = detoxCapture({
  id: "mobile-showcase",

  projectDirectory:
    "mobile/crystal-lattice-control-rn",

  command: [
    "yarn",
    "detox",
    "test",
    "e2e/website-visual-capture.e2e.ts",
    "--configuration",
    "ios.sim.release",
  ],

  outputs: {
    heroLight:
      "mobile/crystal-lattice-control-rn/artifacts/website/hero-light.png",

    heroDark:
      "mobile/crystal-lattice-control-rn/artifacts/website/hero-dark.png",
  },
});
```

Several assets may consume named outputs from the same producer. The producer
runs its command once per CLI process.

The owning application package remains responsible for:

- production UI interaction;
- fixture state;
- stable identifiers;
- simulator configuration;
- native behavior verification.

The landing package owns review, source promotion, derivative generation, and
website presentation.

## Add a Catalog Command

Catalog commands are defined in:

```js
defineVisualAssets({
  commands: {
    // ...
  },
});
```

A command can run direct asset commands, compose lifecycle callbacks, or use
both:

```js
async function customCommand(context) {
  const results = await context.forEachSelected(
    async (assetContext) => {
      if (
        assetContext.hasCommand("custom")
      ) {
        return assetContext.runCommand("custom");
      }

      if (
        assetContext.hasLifecycle(
          "customStage",
        )
      ) {
        return assetContext.runLifecycle(
          "customStage",
        );
      }

      return assetContext.unsupported("custom");
    },
    {
      requireSelection: true,
    },
  );

  return context.writeReport("custom", {
    results,
  });
}
```

Register it:

```js
commands: {
  // ...
  custom: customCommand,
},
```

Invoke it:

```bash
yarn visual-assets custom <asset>
```

No CLI or runner edit is required.

## Verification

Run the programmatic asset tests:

```bash
yarn test:visual-assets
```

Check all configured assets:

```bash
yarn visual-assets:check
```

Run website visual contracts:

```bash
yarn test:visual
```

Run all visual verification:

```bash
yarn verify:visual
```

Use headed browser verification when judging visual presentation:

```bash
yarn test:visual:headed
```

## Troubleshooting

### Unsupported command

An explicitly selected asset must define the direct command or lifecycle stages
used by the catalog command. Add the applicable callback or select another
asset.

### Unknown configuration key

Only the common `defineAsset` keys are validated by the API. Asset-specific
keys belong under `config` and are interpreted by the assigned callbacks.

### Candidate differs from expectations

Run `visual-assets:inspect`, review the candidate, and update expectations only
after the visual is accepted.

### Captured source is missing

Run `visual-assets:capture` first. Promotion never launches the capture
producer automatically.

### Public derivative differs

Run `visual-assets:update` for the explicitly reviewed asset, then run
`visual-assets:check`.