# Visual Content and Screenshot Generation

The landing package maintains approved screenshots as reproducible,
theme-aware derivatives rather than editing production images directly.

The current workflow has four separate boundaries:

```text
source capture or generation
        │
        ▼
reviewed source master
        │
        ▼
optimized public derivative
        │
        ▼
browser presentation verification
```

Capturing a source never automatically changes a reviewed source or public
website file.

## Maintained Files

The executable asset catalog is:

```text
visual_assets/config.mjs
```

It uses ordinary JavaScript functions to define:

- asset and variant IDs;
- current product claims and freshness triggers;
- reviewed source paths;
- source provenance;
- replaceable pipelines;
- public output paths;
- dimensions, byte ceilings, and SHA-256 expectations;
- content-file bindings;
- aggregate budgets.

Reviewed source masters are stored under:

```text
visual_assets/sources/
```

They are sanitized, maintained inputs and are not deployed by Astro.

Optimized website files are stored under:

```text
public/
```

Generated candidates, capture output, reports, Playwright results, and review
screenshots are stored under the ignored directory:

```text
artifacts/visual-assets/
```

## Programmatic Pipeline Contract

Every configured variant provides a pipeline with:

```js
async run(context) {
  // Produce context.candidatePath from context.sourcePath.
}
```

The context provides:

- the asset and variant;
- reviewed source and candidate paths;
- repository, package, and ignored output roots;
- a process runner;
- an ignored-path helper.

The generic runner does not know whether a pipeline uses ImageMagick,
Playwright, a diagram renderer, another program, or unique custom code.

`scripts/visual-assets/operations.mjs` provides the currently reusable
ImageMagick elements:

- trim;
- resize;
- centered extent;
- sRGB normalization;
- metadata removal;
- WebP encoding;
- custom programmatic ImageMagick arguments.

These are JavaScript functions rather than a declarative pipeline language.
A pipeline may use them, define a unique operation, or implement its complete
`run(context)` method directly.

## Source Types

`reviewedFile(path)` identifies a maintained source master.

`capturedSource({ reviewed, candidate })` identifies both:

- the reviewed source used by `inspect`, `update`, and `check`;
- an ignored candidate produced by an explicit `capture` command.

Normal verification never invokes a capture producer. This keeps ordinary
builds and CI independent of simulators, credentials, providers, and expensive
source-generation workflows.

## Current Source Provenance

The current source masters came from the author-preserving imported revision:

```text
e88aa46ee8d6bd0969c63c78f8e152f1fd938974
```

That revision is recorded as provenance in the executable catalog. It is not
needed to run the asset workflow; all maintained source files are present in
the current checkout.

## Requirements

Install package dependencies:

```bash
yarn install
```

Image transformation requires:

- ImageMagick 7 with the `magick` command;
- Node.js supported by the landing package.

Install the Playwright Chromium browser once when no installed browser channel
is selected:

```bash
npx playwright install chromium
```

Set `PLAYWRIGHT_CHANNEL` to use an installed browser channel such as `chrome`
instead.

## List Assets

Show every asset, variant, source type, public output, and pipeline:

```bash
yarn visual-assets:list
```

## Inspect Candidates

Generate ignored candidates without requiring them to match the current
dimensions, hashes, or byte ceilings:

```bash
yarn visual-assets:inspect provider-reasoning
yarn visual-assets:inspect provider-reasoning --variant dark
yarn visual-assets:inspect
```

With no asset selection, `inspect` processes the complete catalog.

The report is written to:

```text
artifacts/visual-assets/reports/inspect.json
```

Use this command when evaluating a changed source or pipeline. Review the
candidate appearance, dimensions, bytes, and SHA-256 before updating the
maintained expectations.

## Update Public Derivatives

Updating is an explicit mutation and requires an asset or `--all`:

```bash
yarn visual-assets:update provider-reasoning
yarn visual-assets:update provider-reasoning --variant dark
yarn visual-assets:update --all
```

The command:

1. reads the reviewed source master;
2. executes the configured programmatic pipeline;
3. checks maintained dimensions, byte ceilings, and SHA-256;
4. validates the corresponding content-file binding;
5. copies the approved candidate to its declared `public/` path.

It does not capture a source, change copy, select a visual, or update
expectations automatically.

## Verify Current Derivatives

Regenerate candidates and compare them byte-for-byte with `public/`:

```bash
yarn visual-assets:check
yarn visual-assets:check provider-reasoning
yarn visual-assets:check provider-reasoning --variant dark
```

With no selection, `check` verifies the complete catalog.

The check fails when:

- a reviewed source is missing;
- a pipeline does not create its candidate;
- dimensions, bytes, or SHA-256 differ from expectations;
- an active-theme budget is exceeded;
- a public derivative is missing or differs from its candidate;
- a configured content binding has stale paths, alternative text, or
  dimensions.

`check` never invokes Detox or another capture producer.

## Capture and Promote a Source

Assets with `capturedSource` support an explicit two-step source update.

Generate ignored candidates:

```bash
yarn visual-assets:capture mobile-hero
yarn visual-assets:capture mobile-hero --variant dark
```

The candidate remains under an `artifacts/` directory. It does not replace the
reviewed source.

After human review, promote the candidate:

```bash
yarn visual-assets:promote-source mobile-hero --variant dark
```

Promotion copies the already-generated candidate to the configured reviewed
source path. It does not generate or update the public derivative. Run
`visual-assets:inspect` and `visual-assets:update` afterward.

Both capture and promotion require an explicit asset or `--all`.

## Detox Producers

`scripts/visual-assets/producers/detox.mjs` provides a reusable source producer.
It runs a package-owned Detox scenario and exposes one or more named output
files:

```js
const mobileCapture = detoxCapture({
  id: "mobile-showcase",
  projectDirectory: "mobile/crystal-lattice-control-rn",
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

An asset can consume a named output:

```js
source: capturedSource({
  reviewed: "visual_assets/sources/mobile-hero-dark.png",
  candidate: mobileCapture.output("heroDark"),
}),
```

Multiple selected assets can consume outputs from one producer run. The
producer memoizes the command for the current CLI process, so one Detox scenario
does not start separately for each output.

The mobile package owns the Detox interaction scenario, fixture state, stable
selectors, simulator configuration, and native behavior. The landing package
owns source review, optimization, publication, and website presentation.

## Adding or Changing Assets

### Existing source and pipeline

1. Add a reviewed source under `visual_assets/sources/`.
2. Add the asset to `visual_assets/config.mjs`.
3. Add or update its website content binding.
4. Run `visual-assets:inspect`.
5. Record reviewed dimensions, byte ceiling, and SHA-256.
6. Run `visual-assets:update` for the selected asset.
7. Run `visual-assets:check` and browser verification.

### New reusable pipeline

Define an ordinary JavaScript pipeline factory in `visual_assets/config.mjs`,
or extract it to a focused module when reuse or testing justifies a separate
file. The generic runner and CLI do not change.

### Unique pipeline

Define the pipeline beside its only asset. It may:

- compose current ImageMagick operation functions;
- add a custom ImageMagick argument function;
- provide a complete `run(context)` implementation.

The generic runner and CLI do not change.

### New source producer

Define a producer that returns `captureOutput`. Keep the capture implementation
with the package that owns the behavior when it needs package-specific fixtures
or tests. The landing configuration consumes its candidate output.

## Themed Images

`src/components/ThemedImage.astro` renders one image element with light and
dark source metadata. The theme initialization in `src/layouts/Layout.astro`
assigns only the source matching the restored `data-theme` value.

The behavior is:

- the inactive theme is not requested on initial page load;
- below-the-fold proof images remain lazy-loaded;
- changing themes updates the same image elements and requests the alternate
  files once;
- Astro client navigation restores the selected theme and source paths;
- a light-image fallback is available when scripting is disabled.

## Browser Verification and Captures

Run visual contracts headlessly:

```bash
yarn test:visual
```

Run the same contracts with visible browser windows:

```bash
yarn test:visual:headed
```

The Playwright configuration builds and previews the static site, then checks:

- home and mobile routes;
- desktop and phone viewports;
- light and dark themes;
- image source selection and successful loading;
- alternative text and dimensions;
- provider and workbench column counts;
- lazy active-theme loading;
- theme toggling without duplicate image elements;
- saved-theme behavior across Astro client navigation.

Captures are written to:

```text
artifacts/visual-assets/playwright/captures/
```

Run the programmatic asset tests, complete asset check, and browser contracts
together:

```bash
yarn verify:visual
```

## Proof Integrity

Do not use generated image editing to change proof-bearing product text,
controls, connection state, citations, notifications, or other behavior.
Recapture the real product state instead.

Decorative generation must remain visibly separate from product-proof
screenshots.

## Retained Review Records

The current baseline review records are under:

```text
research/025-current-visual-baseline-and-asset-pipeline/
```

They include:

- accepted and omitted contribution decisions;
- the imported and current loading measurements;
- current alternative-text and presentation review.

These records preserve review evidence. Active build configuration belongs in
`visual_assets/config.mjs`, and disposable output remains under `artifacts/`.