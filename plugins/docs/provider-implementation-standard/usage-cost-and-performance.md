# Provider usage, cost, and performance

## Usage extension

Implement provider usage in a provider extension when the API returns token or
unit counts.

The extension owns:

- configuration and UI;
- native usage normalization;
- formatted message metadata;
- turn and session cumulative totals;
- persistence/rebuild;
- performance-extension interoperability;
- cost-estimation integration.

Keep the raw provider usage available alongside normalized fields.

## Normalized usage

Expose available values for:

- input tokens;
- output tokens;
- total tokens;
- reasoning/thinking tokens;
- cached input/read tokens;
- cache-write/creation tokens;
- formatted variants;
- turn cumulative input/output tokens;
- session cumulative usage.

Do not synthesize a provider-reported field when the value is estimated.

## Duration and TPS

Usage extensions provide stable internal turn-cumulative input and output token
fields. `DurationExtension` uses output tokens for turn TPS and may fall back
to input tokens when output totals are unavailable.

Verify:

- ordinary responses;
- streamed responses;
- multi-generation tool turns;
- reasoning responses;
- persistence/reload;
- extension execution order.

## Cost terminology

Call a monetary value:

- `reported` only when the provider returns a request-level cost;
- `estimated` when calculated from token/unit counts and configured or
  maintained rates.

Do not relabel organization-level aggregate billing reports as request-level
reported cost.

## Cost precedence

Use this order:

1. provider-reported request cost;
2. provider-reported token classes with model rates;
3. estimated cache/token classes with model rates;
4. no cost when required usage or rates are unavailable.

Preserve cost provenance in per-message, turn, and session totals. A cumulative
value containing estimated components is not wholly reported.

## Pricing catalogs

A maintained catalog:

- is checked into the owning/shared package;
- records source and refresh time;
- uses deterministic validated data;
- maps documented model aliases;
- supports ordinary input, cached input, cache writes where applicable, and
  output rates;
- may include provider-specific classes such as cache-write TTL rates;
- is refreshed through an explicit command;
- is never fetched live during an ordinary provider request.

Unknown models and incomplete rates produce no estimate.

## Cached-token estimation

Some compatible providers omit cache counts. An optional estimator may infer a
conservative reusable prefix from prior usage-bearing history.

Rules:

- disabled by default unless the provider package documents otherwise;
- reported cache counts always win;
- estimates remain separate from raw usage;
- prefix invalidation resets the estimate;
- estimates may contribute to local cost estimates;
- estimates are labeled and never treated as billing-grade usage.

## Shared implementation

Reuse shared helpers for:

- token formatting;
- cost formatting;
- turn/session accumulation;
- cached-token estimation;
- rate-bucket calculation;
- provenance propagation.

Provider extensions remain responsible for mapping their native usage and
provider-specific rate classes into the portable inputs.