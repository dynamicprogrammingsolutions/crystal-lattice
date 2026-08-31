# Visual Asset Framework Architecture

This page describes the current architecture of the landing package visual
asset framework.

Developers using the supported framework contract should start with:

- [Using the Visual Asset Framework](../visual-asset-framework.md)

Developers selecting or changing processing implementations should use:

- [Visual Asset Processing Pipelines](../visual-assets.md)

This page focuses on framework ownership, execution, extension, safety, and
testing. It does not define processing-pipeline behavior.

## Responsibilities

The framework owns:

- executable catalog construction;
- asset construction;
- catalog command registration;
- CLI command discovery;
- asset selection;
- command and lifecycle dispatch;
- command and asset contexts;
- process and ignored-path services;
- command-local caching;
- prepared durable mutation;
- report writing;
- common framework validation;
- unsupported-operation behavior.

It does not own:

- the meaning of asset-specific configuration;
- product truth represented by a visual;
- processing algorithms;
- capture implementation;
- source-fixture behavior;
- image composition;
- native application behavior;
- website content selection;
- final visual approval.

Processing implementations use the framework through commands, lifecycle
callbacks, opaque configuration, and context services.

## Framework Layout

```text
landing_page/
├── visual_assets/
│   └── config.mjs
├── scripts/
│   └── visual-assets/
│       ├── api.mjs
│       ├── cli.mjs
│       ├── runner.mjs
│       ├── selection.mjs
│       └── validation.mjs
├── tests/
│   └── visual-assets/
└── artifacts/
    └── visual-assets/
```

`visual_assets/config.mjs` is the composition root. It registers commands and
assets.

`scripts/visual-assets/` owns reusable framework code. Processing modules may
exist beside it, but they are consumers of this architecture rather than part
of its common contract.

## Catalog Construction

`defineVisualAssets` accepts:

```js
defineVisualAssets({
  config,
  commands,
  assets,
});
```

It:

- rejects unknown common keys;
- requires at least one command;
- requires at least one asset;
- validates command callbacks;
- validates unique asset IDs;
- creates the asset index;
- exposes command names;
- dispatches catalog commands.

The catalog owns:

```js
catalog.commandNames
catalog.hasCommand(name)
catalog.execute(name, context)
catalog.assetMap
catalog.assets
```

The CLI and runner do not maintain separate command or asset registries.

## Asset Construction

`defineAsset` accepts:

```js
defineAsset({
  id,
  metadata,
  config,
  commands,
  lifecycle,
});
```

It:

- rejects unknown common keys;
- requires a stable asset ID;
- validates direct-command callbacks;
- validates lifecycle callbacks;
- requires at least one command or lifecycle callback;
- provides command and lifecycle lookup;
- injects asset data into callback contexts.

The constructed asset exposes:

```js
asset.hasCommand(name)
asset.runCommand(name, context)
asset.hasLifecycle(name)
asset.runLifecycle(name, context)
```

## Opaque Asset Configuration

Asset `config` is opaque to:

- the framework API;
- the CLI;
- the runner;
- selection;
- generic dispatch.

Its shape belongs to the callbacks assigned to the asset.

This boundary allows independently designed asset types to coexist in one
catalog:

```js
defineAsset({
  id: "example",

  config: {
    arbitrary:
      "interpreted by the callback",
  },

  commands: {
    inspect,
  },
});
```

A new asset-specific key does not justify a framework change.

A framework change is justified only when callbacks require a new common
contract or cross-cutting service that cannot be expressed through existing
contexts.

## Metadata Boundary

Asset `metadata` is non-operational.

The framework may carry it into contexts and reports, but it does not interpret
claims, provenance, freshness information, or review status.

Operational behavior belongs under `config`, direct commands, or lifecycle
callbacks.

This prevents descriptive metadata from silently changing execution.

## CLI Dispatch

The CLI performs a small fixed set of operations:

1. import the catalog;
2. verify the requested command exists;
3. pass the command name and raw arguments to the runner.

Conceptually:

```js
if (!catalog.hasCommand(command)) {
  throw new Error(catalogUsage());
}

await executeVisualAssets({
  catalog,
  command,
  args,
  repositoryRoot,
  landingRoot,
});
```

The CLI derives its available commands from the catalog.

Adding a catalog command does not require adding another dispatch branch to the
CLI.

## Runner Boundary

The runner creates a command context and invokes:

```js
await catalog.execute(
  command,
  commandContext,
);
```

The runner does not interpret:

- asset-specific configuration;
- variants;
- sources;
- outputs;
- processing stages;
- dimensions;
- hashes;
- capture semantics;
- publication semantics;
- content bindings.

Those concepts belong to catalog commands and asset callbacks.

The runner remains stable as new asset types and processing workflows are
introduced.

## Command Context

Catalog commands receive services for:

- raw command arguments;
- asset selection;
- sequential selected-asset iteration;
- prepared-effect application;
- report writing;
- repository and package roots;
- ignored output paths;
- process execution;
- command-local caching.

The command context coordinates behavior spanning selected assets.

It is the correct owner for:

- selection requirements;
- unsupported-operation policy;
- combined budgets or constraints;
- all-or-nothing prepared application;
- command reports.

## Asset Context

Each selected asset receives an asset context containing:

- the constructed asset;
- asset ID;
- metadata;
- opaque config;
- selected variant name;
- whether `--all` was used;
- repository, package, and ignored output roots;
- process execution;
- command-local cache;
- direct-command helpers;
- lifecycle helpers.

Important helpers include:

```js
assetContext.hasCommand(name)
assetContext.runCommand(name, input)

assetContext.hasLifecycle(name)
assetContext.runLifecycle(name, input)

assetContext.requireLifecycles(names)
assetContext.unsupported(name)
```

Asset contexts do not add meaning to callback names or configuration keys.

## Asset Selection

The shared selection layer understands:

```text
<asset-id> ...
--all
--variant <name>
```

It:

- resolves asset IDs through the catalog index;
- rejects unknown IDs;
- prevents contradictory selection;
- returns selected assets and raw variant selection.

The catalog command decides:

- whether no selector defaults to all assets;
- whether explicit selection is required;
- whether variants apply;
- whether extra arguments are allowed;
- whether an unsupported asset is skipped or rejected.

Selection does not inspect asset configuration.

## Catalog Commands

A catalog command is a complete CLI-visible workflow.

It can:

- run a direct asset command;
- compose lifecycle callbacks;
- use both forms for different assets;
- perform cross-asset validation;
- prepare durable effects;
- apply effects;
- write a report.

Example:

```js
async function exampleCommand(
  context,
) {
  const results =
    await context.forEachSelected(
      async (assetContext) => {
        if (
          assetContext.hasCommand(
            "example",
          )
        ) {
          return assetContext.runCommand(
            "example",
          );
        }

        if (
          assetContext.hasLifecycle(
            "exampleStage",
          )
        ) {
          return assetContext.runLifecycle(
            "exampleStage",
          );
        }

        return assetContext.unsupported(
          "example",
        );
      },
      {
        requireSelection: true,
      },
    );

  return context.writeReport("example", {
    results,
  });
}
```

There is no runner-level precedence rule between direct commands and lifecycle
callbacks.

## Direct Commands

A direct command implements the complete asset-local part of one catalog
command:

```js
commands: {
  inspect: inspectAsset,
}
```

The callback receives the asset context and command-specific input.

Direct commands are appropriate when:

- an operation is complete and asset-specific;
- lifecycle decomposition would not create useful reuse;
- an external system already owns the operation sequence;
- the asset needs command-specific argument handling.

The framework does not constrain the callback's internal processing.

## Lifecycle Callbacks

Lifecycle callbacks are smaller named stages:

```js
lifecycle: {
  validateDefinition,
  buildCandidate,
  inspectCandidate,
  validateCandidate,
  preparePublication,
}
```

Lifecycle names are local conventions between an asset type and the catalog
commands composing it.

They are not registered in:

- the API;
- the CLI;
- the runner;
- a global lifecycle enum.

This allows different catalog commands to compose different stage sequences
without changing framework dispatch.

## Commands and Lifecycle Together

An asset may expose both:

```js
defineAsset({
  id: "mixed",

  commands: {
    capture,
  },

  lifecycle: {
    validateCandidate,
    preparePublication,
  },
});
```

The catalog command explicitly selects the path it needs.

This supports:

- one-off operations beside reusable stages;
- asset types that participate only in some commands;
- gradual extraction of shared behavior;
- replacement of one processing workflow without framework changes.

## Unsupported Operations

`assetContext.unsupported(name)` applies selection-aware behavior.

An explicitly selected unsupported asset should fail because the user asked
for that asset.

An unsupported asset reached through `--all` may be skipped when the command
defines that behavior.

This distinction belongs to command coordination, not processing callbacks.

## Prepared Durable Mutations

Durable changes are represented as prepared effects:

```js
{
  report,

  async apply() {
    // Durable mutation.
  },
}
```

The callback performs generation and validation before returning the effect.

The catalog command:

1. prepares every selected effect;
2. performs cross-asset validation;
3. calls `context.applyAll(prepared)`.

If preparation fails, no prepared `apply()` function is called.

This protects multi-asset commands from partial durable updates caused by a
later validation failure.

Disposable work may occur before this boundary only under ignored output.

## Process Service

Callbacks use the context process service rather than creating inconsistent
subprocess conventions.

The service centralizes:

- working directory;
- argument handling;
- process failure reporting;
- output collection;
- command context.

The framework does not interpret the external process being executed.

## Ignored Path Service

Callbacks request disposable output through the context:

```js
const candidate =
  context.artifactPath(
    "example/candidate.dat",
  );
```

The framework roots this output under the package's ignored visual output
directory.

This keeps temporary generation, reports, and review output separate from
maintained source and published files.

## Command-Local Cache

The command context provides one cache shared by all selected assets during a
single CLI invocation.

Processing adapters can use it to memoize expensive shared work:

```js
let result =
  context.commandCache.get(cacheKey);

if (!context.commandCache.has(cacheKey)) {
  result = await produceOnce();
  context.commandCache.set(
    cacheKey,
    result,
  );
}
```

The cache is not persistent state. It exists only for one command execution.

The framework does not assign meaning to cache keys.

## Reports

Catalog commands write structured reports through:

```js
context.writeReport(name, payload)
```

Reports belong under ignored output.

They provide:

- selected asset results;
- candidate or output information;
- validation findings;
- command summary;
- review support.

Reports are command output, not maintained behavioral contracts.

## Common Validation

Framework-level validation covers common contracts such as:

- known common keys;
- callback shape;
- unique asset IDs;
- registered command names;
- valid selection;
- root-bound paths where a framework service owns resolution.

Asset-specific validation belongs to the callback interpreting that asset's
opaque configuration.

Cross-asset validation belongs to the catalog command coordinating the
selection.

## Error Ownership

Errors should be raised at the narrowest owner:

- API construction errors for invalid common definitions;
- selection errors for invalid selectors;
- command errors for unsupported or invalid command usage;
- asset callback errors for asset-specific configuration;
- catalog command errors for combined validation;
- process-service errors for failed external execution.

Avoid moving asset-specific validation into the runner merely to centralize
error text.

## Extension Boundaries

The following should not require a CLI, runner, or common API change:

- a new asset configuration shape;
- a direct-command-only asset;
- a lifecycle-only asset;
- an asset combining both forms;
- a new lifecycle callback name interpreted by catalog code;
- a different lifecycle sequence;
- a new processing pipeline;
- a new producer adapter;
- an asset that omits optional operations;
- a new catalog command.

A shared framework change is justified when consumers need a new common
service or contract that cannot be expressed through:

- opaque config;
- commands;
- lifecycle callbacks;
- process execution;
- ignored paths;
- command-local cache;
- selection;
- reports;
- prepared mutations.

## Testing Architecture

Framework tests cover:

- catalog construction;
- asset construction;
- unknown common keys;
- unique IDs;
- command registration;
- command and lifecycle coexistence;
- selection behavior;
- unsupported explicit selection;
- unsupported `--all` behavior;
- prepared mutation ordering;
- failure preventing durable application;
- command-local service reuse.

Processing tests belong with the processing implementation using the framework.

At least one real catalog consumer should exercise a changed shared helper.

From `landing_page/`:

```bash
yarn test:visual-assets
```

## Invariants

Preserve these framework invariants:

- the catalog is the only command and asset registry;
- command ordering is visible in catalog code;
- the CLI derives commands from the catalog;
- the runner does not interpret asset config;
- asset config remains opaque;
- metadata remains non-operational;
- lifecycle names are defined by their consumers;
- direct commands and lifecycle callbacks may coexist;
- unsupported explicit selections fail;
- unsupported `--all` operations may skip only when the command allows it;
- durable effects are prepared before any apply;
- disposable output remains under ignored paths;
- reports remain command output;
- processing-specific behavior does not migrate into common dispatch without a
  cross-cutting need.