# Using the Visual Asset Framework

The landing package provides an executable framework for defining,
generating, validating, reviewing, and publishing visual files.

Use this guide when you need to:

- add an asset;
- add a new asset configuration shape;
- create a processing pipeline;
- define a direct asset command;
- compose lifecycle callbacks;
- add custom validation or publication rules;
- expose a new catalog command.

For the processing implementations currently available to asset authors, see
[Visual Asset Processing Pipelines](visual-assets.md).

For framework internals and maintainer boundaries, see
[Visual Asset Framework Architecture](development/visual-content-and-screenshot-generation.md).

## Framework Entry Points

The executable catalog is owned by:

```text
landing_page/visual_assets/config.mjs
```

Reusable framework code is under:

```text
landing_page/scripts/visual-assets/
```

The catalog is created with:

```js
defineVisualAssets({
  config,
  commands,
  assets,
});
```

Each asset is created with:

```js
defineAsset({
  id,
  metadata,
  config,
  commands,
  lifecycle,
});
```

## First Asset

A direct-command asset can implement a complete operation itself:

```js
const exampleAsset = defineAsset({
  id: "example-report",

  metadata: {
    claim:
      "The generated visual communicates one current product fact.",
  },

  config: {
    input:
      "visual_assets/example/input.json",
    output:
      "public/example-report.svg",
  },

  commands: {
    inspect: inspectExampleReport,
    check: checkExampleReport,
    update: prepareExampleReportUpdate,
  },
});
```

Register it in the catalog:

```js
defineVisualAssets({
  config,
  commands,
  assets: [
    exampleAsset,
  ],
});
```

Invoke a command through the generic CLI:

```bash
yarn visual-assets inspect example-report
yarn visual-assets check example-report
yarn visual-assets update example-report
```

Catalog command names come from `defineVisualAssets({ commands })`. The CLI
does not maintain another command registry.

## Asset Fields

The common asset fields have distinct responsibilities:

| Field | Responsibility |
|---|---|
| `id` | Stable selector used by commands, reports, and tests |
| `metadata` | Non-operational claim, provenance, and freshness information |
| `config` | Arbitrary asset-specific data interpreted by assigned callbacks |
| `commands` | Complete asset-local implementations of catalog commands |
| `lifecycle` | Smaller named callbacks composed by catalog commands |

The framework validates only the common shape. It intentionally does not
interpret asset-specific `config` keys.

This means a new asset type can introduce its own configuration without
changing the CLI, runner, or framework API:

```js
defineAsset({
  id: "example-sequence",

  config: {
    frames: 12,
    viewport: {
      width: 1440,
      height: 900,
    },
    renderer: "custom",
  },

  commands: {
    inspect: inspectSequence,
  },
});
```

The assigned command owns the meaning and validation of `frames`, `viewport`,
and `renderer`.

## Direct Asset Commands

A direct asset command owns the complete asset-local part of one catalog
command:

```js
async function inspectExample({
  config,
  artifactPath,
}) {
  const candidatePath =
    artifactPath("example/candidate.svg");

  await buildCandidate({
    config,
    candidatePath,
  });

  return {
    candidate: candidatePath,
  };
}
```

The callback receives an asset context containing:

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

Use direct commands when the process is complete and asset-specific, or when
it does not benefit from shared lifecycle composition.

## Lifecycle Callbacks

Lifecycle callbacks are smaller named stages:

```js
defineAsset({
  id: "example-lifecycle-asset",

  config: {
    // Interpreted by the callbacks below.
  },

  lifecycle: {
    validateDefinition,
    buildCandidate,
    inspectCandidate,
    validateCandidate,
    preparePublication,
  },
});
```

Lifecycle names are not registered globally. They become meaningful when a
catalog command calls them:

```js
const candidate = await assetContext.runLifecycle(
  "buildCandidate",
);
```

A catalog command can require a set of stages:

```js
assetContext.requireLifecycles([
  "validateDefinition",
  "buildCandidate",
  "validateCandidate",
]);
```

Lifecycle composition is useful when several catalog commands need different
sequences over the same asset behavior. For example, inspection may use
non-strict validation, while publication may add public-output comparison and
prepared mutation.

## Combine Commands and Lifecycle

An asset can define both:

```js
defineAsset({
  id: "example-mixed-asset",

  commands: {
    capture: captureExample,
  },

  lifecycle: {
    inspectCandidate,
    validateCandidate,
    preparePublication,
  },
});
```

The catalog command explicitly decides whether to call a direct command,
compose lifecycle callbacks, or reject the asset as unsupported.

There is no framework-level precedence rule between the two forms.

## Define a Processing Pipeline

A processing pipeline receives a context and produces the requested
candidate:

```js
const examplePipeline = {
  id: "example-pipeline",

  async run(context) {
    await renderExample({
      source: context.sourcePath,
      output: context.candidatePath,
      config: context.config,
    });
  },
};
```

Store the pipeline object in the asset's opaque configuration:

```js
defineAsset({
  id: "example-pipeline-asset",

  config: {
    source:
      "visual_assets/example/source.dat",
    output:
      "public/example-output.dat",
    build: examplePipeline,
  },

  lifecycle: {
    buildCandidate,
    validateCandidate,
    preparePublication,
  },
});
```

A pipeline may call external processes, package APIs, renderers, browser
automation, native automation, or ordinary JavaScript. The framework requires
only the contract expected by the lifecycle or command using it.

## Add Custom Rules

Put asset-specific rules in the callback that owns the corresponding
configuration:

```js
function validateExampleDefinition({
  config,
}) {
  if (!Number.isInteger(config.frameCount)) {
    throw new Error(
      "frameCount must be an integer",
    );
  }

  if (config.frameCount < 1) {
    throw new Error(
      "frameCount must be positive",
    );
  }
}
```

Use catalog-level validation for constraints involving several selected
assets:

```js
async function updateCommand(context) {
  const prepared =
    await context.forEachSelected(
      prepareAssetUpdate,
      {
        requireSelection: true,
      },
    );

  validateCombinedBudget(prepared);
  await context.applyAll(prepared);

  return context.writeReport("update", {
    results:
      prepared.map((item) => item.report),
  });
}
```

This keeps local rules with the asset type and cross-asset rules with the
catalog command coordinating them.

## Prepared Durable Mutations

A mutating callback should complete generation and validation before exposing
the durable write:

```js
async function prepareExampleUpdate(
  context,
) {
  const candidate =
    await buildAndValidate(context);

  return {
    report: candidate.report,

    async apply() {
      await publishCandidate(candidate);
    },
  };
}
```

Catalog commands prepare all selected effects before calling any `apply()`
function. If one selected asset fails during preparation, no prepared durable
write is applied.

Use prepared effects for changes such as:

- publishing a generated derivative;
- promoting a reviewed source;
- replacing a maintained generated file;
- updating a set of related outputs after combined validation.

Disposable candidate generation does not need a prepared effect, but it must
remain under an ignored output path.

## Candidate, Reviewed, and Published States

Many visual workflows have three distinct states:

```text
candidate
  -> review
  -> maintained source
  -> processing
  -> published output
```

The framework does not require every asset type to use all three states.
Define only the states the asset needs.

Preserve these boundaries when they apply:

- candidates are disposable and ignored;
- review or promotion is explicit;
- maintained sources are stable build inputs;
- published files are derived outputs;
- ordinary checking does not silently launch an expensive or non-deterministic
  producer.

## Add a Catalog Command

A catalog command is the CLI-visible workflow:

```js
async function customCommand(context) {
  const results =
    await context.forEachSelected(
      async (assetContext) => {
        if (
          assetContext.hasCommand("custom")
        ) {
          return assetContext.runCommand(
            "custom",
          );
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

        return assetContext.unsupported(
          "custom",
        );
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
defineVisualAssets({
  config,
  commands: {
    ...commands,
    custom: customCommand,
  },
  assets,
});
```

Invoke it without changing the CLI or runner:

```bash
yarn visual-assets custom <asset-id>
```

## Selection and Variants

The shared selection helper supports:

```text
<asset-id> ...
--all
--variant <name>
```

The catalog command decides:

- whether no selector means all assets;
- whether explicit selection is required;
- whether variants are meaningful;
- whether additional command-specific arguments are allowed;
- whether unsupported assets are skipped or rejected.

An explicitly selected unsupported asset should fail. An unsupported asset in
an `--all` operation may be skipped when the command defines that behavior.

## Reports and Ignored Output

Use the command context to create ignored paths and reports:

```js
const candidate =
  context.artifactPath(
    "example/candidate.json",
  );

return context.writeReport("inspect", {
  results,
});
```

Framework-managed ignored output belongs under:

```text
landing_page/artifacts/visual-assets/
```

Reports should contain enough information to review and reproduce the command
outcome without making the report a maintained source of truth.

## Testing Framework Extensions

Add focused tests when introducing:

- a new common asset key;
- a catalog command;
- selection behavior;
- a new prepared-mutation rule;
- a new cross-cutting context service;
- a new direct-command/lifecycle interaction;
- a new asset configuration validator.

Test the extension through at least one real catalog consumer. Do not replace
the shared helper with a duplicate implementation in the test fixture.

From `landing_page/`:

```bash
yarn test:visual-assets
```

Run the complete configured validation when an extension affects existing
assets:

```bash
yarn visual-assets:check
```

## Troubleshooting

### Unknown command

The requested name is not present in `defineVisualAssets({ commands })`.
Register the catalog command or use an existing command.

### Unsupported asset

The selected asset does not define the direct command or lifecycle stage
required by the catalog command. Add the applicable callback or select an
asset that supports the workflow.

### Unknown common key

`defineAsset` and `defineVisualAssets` reject unknown framework-level keys.
Place asset-specific data under `config`.

### Candidate generation changed a maintained file

Candidate generation is crossing the durable-mutation boundary. Write the
candidate under ignored output and expose the maintained write through a
prepared `apply()` function.

### A custom asset needs a new configuration shape

Add the keys under the asset's opaque `config` and validate them in the
assigned callback. A framework change is needed only when the asset requires a
new cross-cutting service or common contract.