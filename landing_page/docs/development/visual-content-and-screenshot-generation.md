# Visual Content and Screenshot Generation Architecture

This page describes the current implementation of the landing package visual
asset system.

Developers adding assets, builds, commands, lifecycle callbacks, or captures
should start with the consumer guide:

- [Visual assets](../visual-assets.md)

This page focuses on ownership, execution, extension, and safety boundaries.

## Responsibilities

The visual asset system owns:

- executable asset registration;
- CLI command registration;
- asset selection;
- direct asset-command execution;
- lifecycle composition;
- process and ignored-path services;
- prepared durable mutations;
- reports;
- reviewed-source and public-derivative generation;
- website content bindings;
- browser presentation checks.

It does not own:

- product truth for the represented feature;
- mobile or desktop production UI behavior;
- native fixture implementation;
- provider credentials;
- final page briefs or visual selection;
- deployment.

## Module Layout

```text
landing_page/
├── visual_assets/
│   ├── config.mjs
│   └── sources/
├── scripts/
│   └── visual-assets/
│       ├── api.mjs
│       ├── cli.mjs
│       ├── runner.mjs
│       ├── selection.mjs
│       ├── validation.mjs
│       ├── operations.mjs
│       ├── runtime-ui-fixture.mjs
│       ├── session-fixture.mjs
│       ├── refresh_runtime_ui_fixture.py
│       ├── refresh_session_fixture.py
│       ├── lifecycle/
│       │   └── image.mjs
│       └── producers/
│           └── detox.mjs
├── tests/
│   ├── visual-assets/
│   └── visual/
└── artifacts/
    └── visual-assets/
```

`visual_assets/config.mjs` is the composition root. It defines the supported
commands and assets.

`scripts/visual-assets/` provides reusable infrastructure and implementations.
It does not register specific website assets.

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
- requires at least one asset;
- requires at least one command;
- validates command callbacks;
- validates unique asset IDs;
- builds the asset index;
- exposes command names to the CLI;
- dispatches catalog commands.

The CLI does not maintain a separate command list. It reads:

```js
catalog.commandNames
```

Adding a catalog command therefore does not require a CLI or runner change.

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
- requires `id`;
- validates command and lifecycle callbacks;
- requires at least one command or lifecycle callback;
- provides `hasCommand` and `runCommand`;
- provides `hasLifecycle` and `runLifecycle`;
- injects the asset, metadata, and opaque config into callbacks.

`config` is intentionally opaque to the API and runner. Its structure belongs
to the assigned callbacks.

`metadata` is non-operational. Catalog commands may include it in reports, but
the runner does not interpret claims, provenance, or freshness triggers.

## CLI Dispatch

The CLI performs only three architecture-specific operations:

1. import the catalog;
2. verify that the requested command exists;
3. pass the command and raw arguments to the runner.

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

Argument meaning belongs to the selected catalog command. Current selection
helpers understand asset IDs, `--all`, and `--variant`; a custom command may
interpret other raw arguments without changing CLI dispatch.

## Runner Boundary

The runner creates a command context and invokes:

```js
await catalog.execute(command, commandContext);
```

It does not interpret:

- image variants;
- sources;
- build pipelines;
- public outputs;
- dimensions;
- hashes;
- capture producers;
- content bindings;
- asset-specific configuration keys.

Those concepts are implemented by catalog commands and asset callbacks.

## Command Context

Catalog commands receive services for:

- raw command arguments;
- asset selection;
- sequential selected-asset iteration;
- asset description;
- prepared-effect application;
- report writing;
- repository, package, and ignored output roots;
- a command-local cache.

The current selection helper supports:

```text
<asset-id> ...
--all
--variant <name>
```

Catalog commands decide whether:

- no selection means all assets;
- explicit selection is required;
- extra arguments are allowed;
- unsupported assets are skipped or rejected.

## Asset Context

Selected assets receive:

- the defined asset;
- opaque asset config;
- metadata;
- selected variant name;
- whether `--all` was used;
- repository, package, and ignored output roots;
- process execution;
- ignored-path construction;
- command-local cache;
- direct-command and lifecycle helpers.

Important helpers include:

```js
assetContext.hasCommand(name)
assetContext.runCommand(name, input)

assetContext.hasLifecycle(name)
assetContext.runLifecycle(name, input)

assetContext.requireLifecycles(names)
assetContext.unsupported(name)
```

`unsupported(name)` skips the asset for an `--all` operation and rejects an
explicitly selected unsupported asset.

## Catalog Commands

Catalog commands are complete CLI-visible workflows.

The current catalog defines:

- `list`;
- `inspect`;
- `check`;
- `update`;
- `capture`;
- `promote-source`;
- `refresh-session`;
- `promote-session`;
- `refresh-runtime-ui`;
- `promote-runtime-ui`.

Each command explicitly chooses:

- direct asset command;
- composed lifecycle stages;
- unsupported behavior.

There is no runner-level precedence rule between direct commands and
lifecycle callbacks.

For example, `check`:

1. runs `commands.check` when present;
2. otherwise requires the image-check lifecycle;
3. validates the asset definition;
4. builds candidates;
5. inspects candidates;
6. validates candidates strictly;
7. compares public derivatives;
8. applies catalog-level budgets;
9. writes the report.

The complete ordering is visible in `visual_assets/config.mjs`.

## Direct Asset Commands

A direct asset command implements the complete asset-local part of a catalog
command:

```js
commands: {
  check: checkGeneratedDiagram,
}
```

The callback receives the asset context plus:

```js
{
  asset,
  metadata,
  config,
  input,
}
```

The catalog command determines how the returned value participates in global
budgets, reports, or durable mutation.

Direct commands are appropriate for:

- unique generators;
- external tools with their own lifecycle;
- formats that do not use image inspection;
- command-specific behavior that cannot reuse shared stages.

## Lifecycle Composition

Lifecycle callbacks are smaller asset-local stages:

```js
lifecycle: {
  validateDefinition,
  buildCandidate,
  inspectCandidate,
  validateCandidate,
  comparePublished,
  preparePublication,
}
```

Lifecycle names are not registered in the runner or API. A name is meaningful
because a catalog command calls it.

This allows catalog commands to define more than one lifecycle sequence:

- inspection uses non-strict validation;
- checking adds public comparison;
- update replaces comparison with prepared publication;
- capture and source promotion use separate optional stages.

An asset can define both direct commands and lifecycle callbacks. The catalog
command explicitly decides which path to use.

## Current Image Lifecycle

`lifecycle/image.mjs` owns the current reviewed-image configuration shape:

```js
config: {
  presentation,
  contentBindings,
  variants,
}
```

Each variant currently contains:

```js
{
  source,
  provenance,
  output,
  build,
  expected,
}
```

The image lifecycle implements:

- `describe`;
- `validateDefinition`;
- `buildCandidate`;
- `inspectCandidate`;
- `validateCandidate`;
- `comparePublished`;
- `preparePublication`;
- optional `capture`;
- optional `prepareSourcePromotion`.

The generic runner never reads this configuration.

## Programmatic Builds

`operations.mjs` provides ordinary JavaScript functions for building an
ImageMagick command:

- trim;
- resize;
- centered extent;
- sRGB normalization;
- metadata removal;
- WebP encoding;
- custom argument callbacks.

`imageMagickPipeline` returns the common:

```js
{
  id,
  async run(context) {},
}
```

An asset may provide any other object implementing this build contract.

`focusCalloutPipeline` is a programmatic build assembled from the same
operations. The asset owns all source rectangles, contextual-image placement,
callout placement, border, shadow, dimming, and encoding values. The pipeline
keeps the contextual screenshot narrower than the final canvas and places the
enlarged square-corner callout above the source region it magnifies. This is an
image composition of one reviewed source, not a native UI mutation.

## Prepared Durable Mutations

Durable changes are represented as prepared effects:

```js
{
  report,
  async apply() {},
}
```

Asset callbacks perform generation and validation before returning the effect.

Catalog commands:

1. prepare every selected effect;
2. perform global validation such as budgets;
3. call `context.applyAll(prepared)`.

If preparation of any selected asset fails, no `apply()` function is called.

This model is used for:

- public derivative update;
- reviewed-source promotion;
- future durable asset operations.

Capture output is disposable and may be produced before this boundary, but it
must remain under an ignored `artifacts/` directory.

## Source Lifecycle

`reviewedFile(path)` identifies a maintained source.

`capturedSource({ reviewed, candidate })` identifies:

- the maintained source used by build/check/update;
- an ignored candidate available to capture and promotion.

Source promotion and public publication are intentionally separate prepared
mutations.

Normal checking does not invoke a source producer.

## Detox Producer

`producers/detox.mjs` adapts a package-owned Detox command to one or more named
capture outputs.

The adapter:

- runs the command in the owning package;
- memoizes the run for the current CLI process;
- verifies the requested named output exists;
- returns its repository path.

The owning mobile package remains responsible for native UI interaction and
fixture correctness.

The landing package remains responsible for source review, promotion,
derivative production, and website presentation.

The producer captures application pixels without a hardware frame. The image
lifecycle applies the maintained crop and encoding to those pixels. A phone
frame, when required by a mobile-specific page, is presentation owned by the
website CSS and is not part of the reviewed raster source.

## Reviewed session fixture producer

`session-fixture.mjs` adapts the `coding-plan` direct-command asset to
`refresh_session_fixture.py`.

The producer receives all environment-dependent inputs explicitly:

- Python executable;
- agent ID;
- credential-directory path.

The tracked source manifest owns:

- repository URL and immutable revision;
- sparse checkout paths;
- checkout byte and time budgets;
- generation config;
- initial and follow-up prompts;
- reviewed-prefix length;
- presentation identity.

The Python producer:

1. creates an operating-system temporary directory;
2. performs the bounded sparse checkout and verifies its exact revision;
3. copies the tracked generation config;
4. reads only the expected ChatGPT credential file from the supplied config
   directory;
5. creates `TerminalApplication` with explicit runtime paths and overrides;
6. either runs the initial investigation or seeds the approved reviewed
   prefix and runs only its replacement follow-up;
7. uses the shared application request path;
8. rejects install, build, simulator, and source-writing commands;
9. sanitizes private metadata, paths, account identifiers, credentials, raw
   responses, and request identifiers;
10. validates repository-inspection activity, a no-tool follow-up, and visible
    reasoning metadata;
11. writes an ignored candidate plus generation provenance.

Provider reconstruction omits an empty assistant message whose only purpose is
to carry a tool call. Seed validation therefore compares the semantic runtime
prefix while candidate construction restores the exact reviewed message
objects before appending the new follow-up pair.

`promote-session` is the only command that replaces the tracked reviewed
session fixture. The ordinary `check` path never runs a model request or
repository checkout.

## Runtime UI fixture producer

`runtime-ui-fixture.mjs` is a direct-command asset adapter for deterministic
application UI contracts. It invokes
`refresh_runtime_ui_fixture.py`, which:

1. loads the canonical visual runtime configuration;
2. adds the owning plugin source roots to the isolated Python import path;
3. instantiates `AgentApplication` in a temporary session store;
4. imports the reviewed coding-session messages;
5. asks the real core and application plugins for their UI and config schemas;
6. selects the configured presentation keys from those real schemas;
7. emits deterministic source hashes, action/settings contracts, and snapshot
   presentation data.

`refresh-runtime-ui` writes an ignored candidate.
`promote-runtime-ui` is the only command that updates the tracked fixture.
The asset's `check` command regenerates the candidate locally and compares it
byte-for-byte with the promoted file.

The native harness consumes the promoted file in process. This isolates
visual rendering from server startup, event polling, ports, credentials, and
plugin-cache state. It does not replace transport coverage:
`backend.website-runtime-ui.integration.test.ts` starts the public FastAPI
boundary and verifies the canonical actions and selected settings through the
production frontend transport and backend adapter.

The runtime fixture keeps several presentation projections from one reviewed
session. Provider usage proof remains attached to the accepted investigation
response, while the mobile hero uses the consecutive follow-up exchange.
`metadata.display` may carry a bounded exact excerpt for a website proof while
the reviewed fixture retains the complete response content.

## Validation

`validation.mjs` owns reusable file-level concerns:

- root-bound path resolution;
- ignored capture-path enforcement;
- image dimensions;
- SHA-256;
- public URL conversion;
- YAML media binding validation.

Format- or asset-specific validation belongs in lifecycle or direct command
callbacks.

## Reports and Ignored Output

Reports are written under:

```text
artifacts/visual-assets/reports/
```

Generated candidates are written under:

```text
artifacts/visual-assets/generated/
```

Playwright output is written under:

```text
artifacts/visual-assets/playwright/
```

Reviewed source masters remain under `visual_assets/sources/`, and optimized
derivatives remain under `public/`.

## Browser Presentation

The website uses `ThemedImage.astro` so one image element carries light and dark
source metadata. Theme restoration assigns only the active source.

The mobile-page hero wraps the same unframed source in a generic CSS phone
frame. Homepage and other consumers can therefore reuse the proof without a
device bezel.

Playwright verifies:

- desktop and phone routes;
- light and dark themes;
- active source selection;
- lazy loading;
- image semantics;
- card layout;
- theme toggling;
- client-navigation persistence.

These tests validate website presentation, not native application behavior or
source-capture correctness.

## Testing Boundaries

Programmatic tests cover:

- catalog and asset construction;
- command and lifecycle coexistence;
- generic selection;
- unknown common keys;
- programmatic build operations;
- capture and promotion separation;
- Detox output memoization;
- preparation failure preventing durable application.

Python fixture tests cover:

- sanitization and forbidden-command rejection;
- two-request shared application execution;
- reviewed-prefix preservation across provider normalization;
- no-tool, reasoning-bearing follow-up validation;
- deterministic runtime UI-schema generation.

The complete catalog check exercises every current source, build, expectation,
content binding, budget, and public derivative.

Playwright exercises the production website adapter and generated static site.

Native capture scenarios remain package-owned and require their own native
tests and human presentation review.

## Extension Rules

Adding the following should not require a CLI, runner, or API change:

- a new asset config shape;
- a direct-command-only asset;
- a lifecycle-only asset;
- a mixed asset;
- a new direct command implementation for an existing catalog command;
- a new lifecycle stage used by catalog code;
- a different lifecycle sequence;
- an asset that omits capture or promotion;
- a new catalog command.

A shared runtime change is justified only when callbacks require a new
cross-cutting service that cannot be expressed through current process, path,
cache, selection, report, or prepared-mutation services.

## Invariants

Preserve these invariants:

- catalog command ordering is visible in the catalog;
- the runner does not interpret asset config;
- the CLI derives commands from the catalog;
- unsupported explicit selections fail;
- unsupported `--all` operations may skip;
- durable effects are prepared before any apply;
- capture candidates stay ignored;
- reviewed source promotion is explicit;
- normal checking never runs capture producers;
- public proof is generated from reviewed source masters;
- proof-bearing UI is never fabricated through image editing.