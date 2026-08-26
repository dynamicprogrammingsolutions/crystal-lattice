# Visual Content and Screenshot Generation

The landing package maintains approved screenshots as reproducible,
theme-aware derivatives rather than editing production images directly.

This page documents the current asset manifest, generation, validation, and
browser-review workflow. It does not select the final website visual set or
define product claims; authored content and its owning product sources remain
authoritative for those decisions.

## Maintained Inputs and Outputs

The current visual manifest is:

```text
research/025-current-visual-baseline-and-asset-pipeline/visual-manifest.yaml
```

It records, for every accepted visual:

- the public claim and content entry it supports;
- alternative text and display dimensions;
- light and dark source paths at a pinned Git revision;
- deterministic ImageMagick transformations;
- public output paths;
- byte ceilings and expected SHA-256 values;
- freshness triggers.

Raw source images are recovered from the pinned Git revision into:

```text
artifacts/research/025-current-visual-baseline-and-asset-pipeline/
```

That directory also receives generated candidates, reports, Playwright output,
and review captures. It is ignored.

Only manifest-approved optimized files are copied to `public/`.

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

Content types that accept a themed image use `src` and optional `srcDark`
fields plus explicit `width`, `height`, and `alt` values.

## Requirements

Install package dependencies:

```bash
yarn install
```

Asset generation requires:

- Git with the manifest's source revision available;
- ImageMagick 7 with the `magick` command;
- Node.js supported by the landing package.

Install the Playwright Chromium browser once when no installed browser channel
is selected:

```bash
npx playwright install chromium
```

Set `PLAYWRIGHT_CHANNEL` to use an installed browser channel such as `chrome`
instead.

## Inspect Candidates

Generate ignored candidates and a report without requiring the candidate
hashes to match the current manifest:

```bash
yarn visual-assets:inspect
```

The report is written to:

```text
artifacts/research/025-current-visual-baseline-and-asset-pipeline/
  asset-generation/asset-check-report.json
```

Use this mode when evaluating a changed source or transformation. Review the
candidate dimensions, byte sizes, and SHA-256 values before changing maintained
expectations.

## Update Public Derivatives

After reviewing candidates and updating their expected dimensions and hashes
in the manifest:

```bash
yarn visual-assets:update
```

The command:

1. extracts each pinned source image into ignored output;
2. applies the declared ImageMagick transformation;
3. checks dimensions, byte ceilings, and expected hashes;
4. validates the corresponding YAML content entry;
5. copies the approved derivative to its declared `public/` path.

It does not change page copy, visual selection, or alternative text
automatically.

## Verify Public Derivatives

Regenerate every candidate and compare it byte-for-byte with `public/`:

```bash
yarn visual-assets:check
```

The check fails when:

- a source revision or source path is unavailable;
- ImageMagick produces unexpected dimensions or bytes;
- a derivative exceeds its byte ceiling;
- a generated or public SHA-256 differs from the manifest;
- the public file is missing;
- `home.yaml` no longer matches the manifest's source paths, alternative text,
  or dimensions;
- an active theme exceeds the manifest's aggregate byte budget.

## Browser Verification and Captures

Run the visual contracts headlessly:

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

Full-page and focused section captures are written below:

```text
artifacts/research/025-current-visual-baseline-and-asset-pipeline/
  playwright/captures/
```

Run the asset and browser checks together:

```bash
yarn verify:visual
```

## Changing a Visual

1. Confirm the current product claim and the need for visual proof.
2. Prepare a sanitized source capture in ignored output.
3. Commit the reviewed source or identify another stable source revision.
4. Update the visual manifest's claim, content location, source, transform,
   dimensions, byte ceiling, freshness triggers, and alternative text.
5. Run `yarn visual-assets:inspect`.
6. Review the candidate and update its expected SHA-256.
7. Run `yarn visual-assets:update`.
8. Run `yarn verify:visual`.
9. Complete human review at the actual page presentation size.

Do not use generated image editing to change proof-bearing product text,
controls, connection state, citations, notifications, or other behavior.
Recapture the real product state instead.

## Retained Review Records

The manifest is accompanied by:

- `asset-review.csv`, including accepted and omitted contribution decisions;
- `performance-baseline.json`, including the imported and current loading
  measurements;
- `accessibility-and-alt-text-review.md`, including current alternative-text
  and presentation review.

These records preserve current review inputs. Disposable screenshots and
browser traces remain under `artifacts/`.