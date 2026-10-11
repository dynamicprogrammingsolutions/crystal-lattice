# Visual Asset Processing Pipelines

The landing package includes processing implementations for reviewed images,
native captures, generated UI fixtures, and website presentation.

Use this page when selecting, configuring, or changing one of those processing
workflows.

For the framework used to define assets, commands, lifecycle callbacks,
custom rules, and new pipeline types, see
[Using the Visual Asset Framework](visual-asset-framework.md).

For framework internals and maintainer boundaries, see
[Visual Asset Framework Architecture](development/visual-content-and-screenshot-generation.md).

## Find Current Assets

The executable catalog is the source of truth for current asset membership,
configuration, sources, outputs, expectations, and freshness metadata:

```text
landing_page/visual_assets/config.mjs
```

Inspect it through the catalog:

```bash
yarn visual-assets:list
yarn visual-assets:inspect
yarn visual-assets:inspect <asset-id>
yarn visual-assets:inspect <asset-id> \
  --variant dark
```

This page documents processing behavior and operational constraints. It is not
the current asset registry.

## Processing Locations

```text
landing_page/
├── visual_assets/
│   ├── config.mjs
│   ├── runtime/
│   ├── session_sources/
│   └── sources/
├── scripts/
│   └── visual-assets/
│       ├── lifecycle/
│       ├── producers/
│       ├── operations.mjs
│       ├── runtime-ui-fixture.mjs
│       ├── session-fixture.mjs
│       ├── refresh_runtime_ui_fixture.py
│       └── refresh_session_fixture.py
├── artifacts/
│   └── visual-assets/
└── public/
```

The maintained boundaries are:

- ignored candidates and reports under `artifacts/visual-assets/`;
- reviewed, sanitized processing inputs under `visual_assets/`;
- optimized website files under `public/`.

## Reviewed Image Lifecycle

### Session actions relationship candidate

The `homepage-session-actions` catalog asset owns the first plugin
configuration-to-menu composition. Its configuration is maintained in
`visual_assets/session-actions-composition.json`; its native source config is
`visual_assets/runtime/session-actions/config.json`.

From `landing_page/`:

```bash
PYTHON=/path/to/configured/python yarn visual-assets capture homepage-session-actions
yarn visual-assets inspect homepage-session-actions
yarn visual-assets check homepage-session-actions
```

Capture runs the Desktop package's real-backend/native producer. Inspect
renders the loaded JSON excerpt with Playwright, combines the native owner and
popover screenshots at their measured positions, magnifies the relevant menu
region, and uses ImageMagick to bake Desktop connections or portrait marker
annotations for the three real action rows.
The resulting light/dark wide (2400 × 1350) and compact (1200 × 1600)
derivatives stay under `artifacts/visual-assets/homepage-session-actions/`.

Desktop keeps code left/UI right with connectors. The portrait derivative
stacks full-width code above a magnified native popup excerpt. Its three code
declarations and actual action rows use matching translucent marker bands;
the popup's real header, close control, and edges identify its origin.
A crop break marks omitted unrelated menu entries. The accepted pre-icon
hashes remain in the recipe as a comparison baseline. Correcting the actual
Generate title glyph requires native recapture and new derivative hashes;
the layout and relationship treatment remain the accepted baseline.

The manifest records source hashes, actual package/action mappings,
configuration row/name bounds, native crop geometry, desktop connector
endpoints, portrait highlight correspondence, popup source segments and
omission bounds,
dimensions, and derivative hashes. Each derivative has a 240,000-byte limit.
Check requires those sources and the recipe to remain current. Re-capture
after changes to the plugin schema or the captured UI; rerun inspect after a
composition change. Code soft-wrapping preserves valid JSON and whole plugin
names. Captures use a fixed blue palette and contain only the seeded session.

This asset is still a candidate. Aggregate inspect/check commands report it as
not run unless its ID is selected explicitly. It has no source-promotion or
publication callback yet; candidate checks are not visual approval. The
existing reviewed image lifecycle remains in force for approved assets.
Use the explicit homepage preview described in the
[content-system guide](development/content-system.md#responsive-proof-sources-and-local-candidates)
to review it in context; there is no separate review-gallery page.

### Complete plugin and transparency candidates

The active October 8 transparency set contains
`homepage-compiled-instructions` and `homepage-usage-overview`. The latter is one
focused native report, reading three days of claude/zai costs and ChatGPT
since-reset estimates/percentage change from a maintained capture-only plugin's
JSON fixture. Its approximately $550 weekly equivalence is illustrative.
Money uses two decimal places only in that fixture.

`homepage-vibe-workflow` processes selected fresh iOS `vibe` captures. The
native capture checks System → User → initial reasoning in one viewport and
retains actual screen-coordinate geometry. The recipe crops the real transcript
and header, removing the status bar/composer without rewriting any UI text.
Both themes produce 1200 × 1600 candidates through `inspect`/`check`, overlaid
only by the explicit homepage preview. Use `CLC_WEBSITE_VISUAL_KINDS=vibe` with
the mobile package's existing capture test to select this scene.

`visual_assets/proof-batch-recipes.mjs` owns the current Message actions,
compiled-instructions, and combined-usage recipes, along with the retained
session-list and separate financial alternatives. Run the Desktop
[batch producer](../../desktop/crystal-lattice-control-desktop-rn/docs/development/website-visual-capture.md)
from its package. Capture Vibe from the mobile package separately, then from
`landing_page/` process the selected homepage candidates:

```bash
yarn visual-assets inspect homepage-session-actions homepage-message-actions homepage-compiled-instructions homepage-usage-overview homepage-vibe-workflow
yarn visual-assets check homepage-session-actions homepage-message-actions homepage-compiled-instructions homepage-usage-overview homepage-vibe-workflow
```

The session-list candidate is retained for later consideration; the user
removed it from the plugin highlight. The current homepage preview selects
Session actions, Message actions, the two transparency images, and Vibe.
`homepage-cost-report` and `homepage-chatgpt-usage` retain their older recipes
and sources for comparison. The current Desktop producer does not refresh
those separate financial scenes; their previous captures are not current
verification of the new batch.

Each Desktop candidate has four WebP derivatives with the same dimensions and
240,000-byte budget as the first image; Vibe has two portrait derivatives.
Their manifests retain native sources,
actual report responses, hashes, crops, and correspondence geometry. Source
fingerprints include the capture test, native harness, real plugin sources,
backend adapter, and effective config. Candidate inspect/check requires an
explicit selection; it does not accept or promote the images.

Message actions use three declarations and four genuine rows; both export
rows share the export package's color. A visible interruption marks unrelated
rows omitted from the portrait enlargement. Session-list connections end at
the actual pin star and archive/status bar controls. The phone uses the same
marker colors on the enlarged real row and preserves list/menu context.

Reports are native window pixels, not reconstructed HTML or painted text.
The compiled Desktop image uses unobscured `*-conversation.png` context. The later
`*-window.png` already contains the open report and must not be combined with
another report-window enlargement. Each Desktop image therefore has one
report excerpt, with its native title/chrome and useful content enlarged.
The combined financial image contains only its focused native report.
Scene-specific crop heights remove blank window canvas; a visible break marks
the Desktop crop. Both current phone images use genuine narrow native windows,
showing complete paragraphs or all three days and the full usage summary.
The combined report's display Markdown is produced by the authorized fixture
plugin; no screenshot labels or values are repainted.

The retained older cost metadata enlargement has a matching outline and
connection to its genuine conversation row. Those cost and usage
portraits magnify bounded crops from wider native reports to preserve unwrapped
numbers and complete history lines. Visible breaks mark separated excerpts
and cropped table columns. Cost phones emphasize totals and daily totals;
Desktop retains project/provider columns and a separate crop of real input,
cached, and completion metadata. The original report payloads and full windows
remain available for verification.
The cost table is still the actual application's scrolling viewport excerpt;
the bounded display caps its body at 420 pixels. It does not show the entire
seven-day table or full report. Capturing a later scrolled portion is a retained
option, rather than drawing missing rows or changing production UI for a photo.

Financial examples use **Sample data** captions. The current combined example
uses the JSON's stipulated weekly equivalence, with the assumption visible
above the image. It is not a provider invoice or a pricing statement.
In the retained separate-report alternative, the cost store includes
recorded OpenAI costs and estimated OpenRouter costs; the usage report's token
and cost totals remain explicitly estimated. These are independently labelled
sample reports, not evidence of an account invoice.

### Reviewed image processing

The image lifecycle under `scripts/visual-assets/lifecycle/image.mjs` processes
light and dark reviewed image variants.

Its callbacks cover:

- definition validation;
- candidate generation;
- image inspection;
- strict or non-strict candidate validation;
- public derivative comparison;
- prepared public-file publication;
- optional source capture;
- optional reviewed-source promotion.

A typical image configuration contains:

```js
config: {
  presentation: {
    alt:
      "Description of the visible product state.",
    width: 1000,
    height: 1400,
  },

  contentBindings: [
    // Website YAML binding.
  ],

  variants: {
    light: {
      source,
      output,
      build,
      expected,
    },

    dark: {
      source,
      output,
      build,
      expected,
    },
  },
}
```

Each expected result records:

```js
expected: {
  width,
  height,
  maxBytes,
  sha256,
}
```

Run inspection while tuning a build:

```bash
yarn visual-assets inspect <asset-id>
```

After review, update the public derivative and verify it:

```bash
yarn visual-assets update <asset-id>
yarn visual-assets check <asset-id>
```

Do not update a hash merely because generation changed. Review the source,
crop, presentation, output dimensions, and website rendering first.

## Programmatic ImageMagick Builds

`scripts/visual-assets/operations.mjs` supplies JavaScript operations for
assembling ImageMagick processing:

- `trim`;
- `crop`;
- `resize`;
- `centerExtent`;
- `normalizeSrgb`;
- `stripMetadata`;
- `encodeWebp`;
- `imageMagickArguments`.

Create a reusable build with `imageMagickPipeline`:

```js
function exampleScreenshot({
  cropGeometry,
  resizeTo,
  quality = 82,
}) {
  return imageMagickPipeline({
    id: "example-screenshot",

    operations: [
      crop(cropGeometry),
      resize(resizeTo),
      normalizeSrgb(),
      stripMetadata(),
      encodeWebp({
        quality,
        method: 6,
      }),
    ],
  });
}
```

Asset-local configuration decides the source rectangle, final size, and
encoding values:

```js
build: exampleScreenshot({
  cropGeometry: "1200x1800+0+160",
  resizeTo: "1000x>",
  quality: 76,
}),
```

Keep unique geometry with the asset definition. Extract a shared build only
when several assets use the same processing semantics.

### Custom ImageMagick operation

Use `imageMagickArguments` for an operation not covered by a maintained
helper:

```js
const removeEdge =
  imageMagickArguments(
    "remove-edge",
    () => [
      "-shave",
      "3x4",
    ],
  );
```

The callback returns arguments only. Process execution, source and output
paths, and error handling remain owned by the pipeline.

## Unframed Native Screen Crops

The current workbench-style processing uses a maintained crop over a native
production-screen capture:

```js
function workbenchModal({
  cropGeometry,
  resizeTo = "1000x>",
  quality = 76,
}) {
  return imageMagickPipeline({
    id: "workbench-modal",

    operations: [
      crop(cropGeometry),
      resize(resizeTo),
      normalizeSrgb(),
      stripMetadata(),
      encodeWebp({
        quality,
        method: 6,
      }),
    ],
  });
}
```

The source should retain application context such as:

- application header;
- session title or identity;
- relevant controls;
- composer or footer when it establishes the screen boundary.

The processing crop removes only irrelevant simulator or capture framing. It
does not add a phone bezel or fabricate missing application UI.

If a page needs a device frame, apply it in website presentation so the same
reviewed raster can remain useful to unframed consumers.

## Focus Callout Pipeline

`focusCalloutPipeline` builds a contextual screenshot and a magnified view from
one reviewed source.

It is appropriate when a full product screen establishes context but the
claimed control or footer would be too small at website presentation size.

The asset controls:

- final canvas;
- context crop;
- context size and placement;
- context dimming;
- focus crop;
- focus size and placement;
- border;
- square corners;
- shadow geometry and clearance;
- encoding.

Example:

```js
build: focusCalloutPipeline({
  id: "example-focus",

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
  },

  callout: {
    crop: "960x280+120+720",
    width: 900,
    gravity: "north",
    geometry: "+50+45",
    borderColor: "#D9DDE5",
    shadow: {
      geometry: "45x14+0+12",
    },
  },

  quality: 78,
}),
```

Important controls are deliberately asset-local. Different UI regions often
need different:

- background crops;
- vertical placement;
- focus dimensions;
- shadow clearance;
- relationship between the callout and its original location.

Common mistakes:

- leaving rounded corners on the focus crop;
- placing the callout over the wrong source region;
- making the contextual screenshot as wide as the final canvas;
- clipping the shadow;
- showing the original focus region at nearly the same prominence as the
  callout;
- using image editing to change product text or controls.

The pipeline may enlarge existing pixels, crop, dim, frame, and add a shadow.
It must not fabricate proof-bearing UI.

## Captured Source Lifecycle

Use `capturedSource` when a maintained reviewed source is produced by an
expensive or non-deterministic process:

```js
source: capturedSource({
  reviewed:
    "visual_assets/sources/example-dark.png",

  candidate:
    producer.output("exampleDark"),
}),
```

The lifecycle is:

```text
capture
  -> ignored candidate
  -> human review
  -> promote-source
  -> reviewed source
  -> inspect/update/check
  -> public derivative
```

Capture and source promotion remain separate:

```bash
yarn visual-assets capture <asset-id>
yarn visual-assets promote-source <asset-id>
```

`check` and `update` read the reviewed source. They do not invoke the capture
producer.

Review candidate sources for:

- correct product state;
- sensitive or private information;
- stale labels or controls;
- light and dark theme consistency;
- clipping;
- platform framing;
- capture size;
- reproducible fixture state.

## Shared Detox Capture

`detoxCapture` adapts a package-owned native capture command to named outputs:

```js
const nativeCapture = detoxCapture({
  id: "native-website-capture",

  projectDirectory:
    "mobile/crystal-lattice-control-rn",

  command: [
    "npm",
    "run",
    "detox:capture:website-visual:ios",
  ],

  outputs: {
    exampleLight:
      "mobile/crystal-lattice-control-rn/artifacts/website/example-light.png",
    exampleDark:
      "mobile/crystal-lattice-control-rn/artifacts/website/example-dark.png",
  },
});
```

Several assets can consume different named outputs from one producer. The
adapter memoizes the producer run for the current CLI process.

The owning application package is responsible for:

- launching production screens;
- fixture correctness;
- stable test identifiers;
- simulator configuration;
- native behavior assertions;
- writing candidate screenshots to ignored package output.

The landing package is responsible for:

- selecting named outputs;
- source review;
- source promotion;
- derivative processing;
- content binding;
- browser presentation.

Changing only a crop or WebP quality does not require a new native capture.
Changing visible application state does.

## Reviewed Session Generation

The session-fixture processing workflow creates a sanitized reviewed
conversation for deterministic native rendering.

The direct-command adapter is:

```text
scripts/visual-assets/session-fixture.mjs
```

The Python producer is:

```text
scripts/visual-assets/refresh_session_fixture.py
```

A session source directory can provide:

```text
config.json
manifest.json
prompt.md
follow-up-prompt.md
```

The manifest owns:

- public repository URL;
- immutable revision;
- sparse checkout paths;
- checkout time and byte budgets;
- generation config;
- initial prompt;
- optional follow-up prompt;
- presentation identity;
- reviewed-prefix length when replacing a follow-up.

Refresh a session candidate:

```bash
yarn visual-assets refresh-session \
  <session-asset-id> \
  --config-dir "$HOME/.crystal" \
  --agent <agent-id> \
  --python <python-executable>
```

The tracked generation config supplies application and plugin configuration.
The supplied config directory contributes the expected credential file only.

The producer:

1. creates a temporary sparse checkout;
2. verifies the pinned revision and resource budgets;
3. creates `TerminalApplication` with explicit paths;
4. runs the request through the shared application request path;
5. rejects install, build, simulator, and source-writing commands;
6. sanitizes private metadata and paths;
7. validates required tool activity and follow-up shape;
8. writes an ignored candidate and provenance record.

When replacing a reviewed follow-up, the producer seeds an approved prefix.
Provider reconstruction may collapse an empty assistant message that only
carries a tool call. Prefix validation compares the semantic runtime sequence,
then restores the exact reviewed message objects before appending the new
follow-up pair.

Review the candidate and provenance under:

```text
artifacts/visual-assets/session-fixtures/
```

Promote only after content, privacy, tool-use, and reasoning review:

```bash
yarn visual-assets promote-session \
  <session-asset-id>
yarn visual-assets check \
  <session-asset-id>
```

Live model access is a source-refresh operation. Routine native capture and
website verification consume the promoted reviewed fixture.

## Runtime UI Fixture Generation

The runtime UI fixture pipeline produces deterministic frontend contracts from
a tracked application configuration and reviewed session.

The adapter is:

```text
scripts/visual-assets/runtime-ui-fixture.mjs
```

The Python producer is:

```text
scripts/visual-assets/refresh_runtime_ui_fixture.py
```

The tracked configuration can select:

- one configured agent;
- provider and application plugins;
- relevant setting keys;
- compact or full message-footer presentation;
- snapshot presentation;
- application and message actions;
- reviewed session projections.

Refresh an ignored candidate:

```bash
yarn visual-assets refresh-runtime-ui \
  <runtime-ui-asset-id> \
  --python <python-executable>
```

Review:

- configured plugins;
- action labels and ordering;
- selected setting keys and options;
- snapshot descriptions;
- message and status presentation;
- source hashes;
- absence of private configuration values.

Promote and check:

```bash
yarn visual-assets promote-runtime-ui \
  <runtime-ui-asset-id>
yarn visual-assets check \
  <runtime-ui-asset-id>
```

The native harness reads the promoted fixture in process. It does not need a
server, credentials, plugin installation, port allocation, or event polling.

A separate frontend integration test should exercise the corresponding real
server, transport, and backend adapter contract.

## Reviewed Message Projections

A runtime fixture may derive more than one proof from a reviewed message:

- complete source content for retained review;
- a provider-focused response for metadata proof;
- a consecutive user/assistant exchange for an active-session proof;
- a bounded exact display excerpt for constrained website presentation.

Use the maintained message display contract for a bounded projection:

```js
metadata: {
  display: {
    type: "text",
    content:
      "Exact excerpt retained from the full message.",
  },
}
```

The full reviewed message remains unchanged. The projection affects
presentation only.

Do not paraphrase a proof-bearing response into a different product claim.

## Theme-Aware Website Presentation

`ThemedImage.astro` stores light and dark source metadata on one image element.
Theme initialization assigns the active source.

This avoids loading two ordinary image elements when only one theme is
visible.

Content bindings should provide:

- light source;
- dark source;
- width;
- height;
- useful alternative text;
- eager or lazy loading appropriate to page position.

Playwright verifies:

- active source selection;
- theme switching;
- client-navigation persistence;
- image dimensions;
- alt text;
- loading behavior;
- responsive layout;
- broken-image absence.

### CSS device framing

A page can add a generic device frame around an unframed reviewed source.

Keep the frame in website presentation when:

- the page specifically communicates mobile use;
- the same screenshot may be reused without a frame elsewhere;
- the frame does not imply a platform different from the captured UI.

Do not bake the frame into the reviewed source unless the hardware itself is
part of the claim.

## Refresh Decision Guide

Use the smallest workflow that reaches the changed boundary.

### Only derivative processing changed

Examples:

- crop;
- resize;
- focus placement;
- shadow;
- encoding quality;
- byte budget.

Run:

```bash
yarn visual-assets inspect <asset-id>
yarn visual-assets update <asset-id>
yarn visual-assets check <asset-id>
```

Do not run native capture.

### Visible native UI changed

Run:

```bash
yarn visual-assets capture <asset-id>
yarn visual-assets promote-source <asset-id>
yarn visual-assets update <asset-id>
yarn visual-assets check <asset-id>
```

### Plugin UI schema or fixture projection changed

Refresh and promote the runtime UI fixture before native capture:

```bash
yarn visual-assets refresh-runtime-ui \
  <runtime-ui-asset-id> \
  --python <python-executable>
yarn visual-assets promote-runtime-ui \
  <runtime-ui-asset-id>
```

Then capture affected sources.

### Reviewed conversation changed

Refresh and promote the reviewed session first, then refresh runtime UI and
capture affected sources.

### Website layout only changed

Do not regenerate sources automatically. Run the website build and browser
visual checks first.

## Verification

Programmatic processing tests:

```bash
yarn test:visual-assets
```

Complete catalog verification:

```bash
yarn visual-assets:check
```

Website build:

```bash
yarn build
```

Responsive and theme presentation:

```bash
yarn test:visual
```

Headed human review:

```bash
yarn test:visual:headed
```

Native capture tests remain owned by the application package supplying the
producer.

## Troubleshooting

### Captured source is missing

Run `capture` before `promote-source`. Promotion does not invoke the producer.

### Candidate differs from expectations

Inspect and review the candidate. Update expected hashes or dimensions only
after accepting the new processing result.

### Source promotion changed the public file unexpectedly

Source promotion changes the reviewed input only. Run `inspect`, then
explicitly run `update` to publish a new derivative.

### Session refresh requires personal application configuration

The session workflow should use a tracked generation config. The explicit
credential directory supplies authentication, not the caller's personal
application settings.

### Runtime fixture and native capture disagree

Promote the refreshed runtime fixture, verify the harness reads it, and run the
real backend/frontend integration boundary before weakening the native test.

### Focus callout is difficult to align

Keep context crop, focus crop, context placement, focus placement, and shadow
clearance independently configurable. Do not force unrelated assets through
one fixed geometry.