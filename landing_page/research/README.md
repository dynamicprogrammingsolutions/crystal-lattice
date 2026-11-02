# Landing Website Research Evidence

This directory stores durable normalized evidence, manifests, datasets, and
human review records for Crystal Lattice product-website research.

Human-readable findings and research interpretation belong under:

```text
landing_page/docs/development/research/
```

Disposable raw output belongs under the ignored directory:

```text
landing_page/artifacts/
```

Reviewed, sanitized source masters used by the executable website visual
workflow belong under:

```text
landing_page/visual_assets/sources/
```

Those files are maintained build inputs rather than research evidence or
publicly deployed files.

## Directory Creation

Create subdirectories only when they contain substantive retained evidence.
Expected categories include:

```text
manifests/
evidence/
datasets/
reviews/
```

Do not add empty directory placeholders.

Current retained packages include:

- `current-product-and-compatibility-baseline/` — accepted exhaustive product
  and compatibility evidence;
- `release-safe-early-user-website/` — version-two public compatibility
  projection and focused current-source drift review.

## Retained Evidence

A retained record should preserve, where applicable:

- stable record ID;
- source type and source ID;
- source URL;
- publication date and precision;
- observation date;
- query, discovery route, or experiment ID;
- bounded excerpt or normalized source facts;
- user problem or job;
- workaround or current product;
- requested outcome;
- supporting, contradictory, ambiguous, or irrelevant direction;
- source-provided facts;
- separately labeled inferred classifications and confidence;
- review state;
- collection and transformation version.

Source-specific fields are allowed. Keep a small shared base so evidence can be
traced and compared.

## Excluded Material

Do not commit:

- credentials or secrets;
- private browser state;
- full downloaded pages;
- full discussion threads;
- raw API caches;
- personal profiles;
- private interview recordings;
- full interview transcripts without an explicitly approved and consented
  retention need;
- unnecessary personal identifiers;
- disposable screenshots and browser traces.

Use bounded excerpts and anonymized findings. Keep raw responses, caches,
browser output, generated comparisons, and temporary captures under
`landing_page/artifacts/`.

## Review and Lineage

- Keep source facts separate from classifications.
- Preserve manual review decisions separately from automated predictions.
- Record the input manifest and transformation version for derived datasets.
- Do not silently overwrite accepted evidence. Create a corrected package or
  preserve the prior state through version control when conclusions materially
  change.
- Research counts describe the bounded collection, not market size, adoption,
  or conversion.
