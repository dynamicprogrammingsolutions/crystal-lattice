# Provider Cost Estimation And Pricing Catalog

Define and implement a portable provider cost-estimation contract backed by
maintained public model-pricing catalogs and normalized usage metadata.

## Requirements checklist

### Functional requirements

- [ ] Provider usage extensions expose consistent reported-token, formatted,
  turn-cumulative, and session-cumulative metadata.
- [ ] A maintained pricing catalog supplies public per-model input, cached
  input, cache-write where applicable, and output rates.
- [ ] Cost estimation uses provider-reported token counts when available and
  clearly labels monetary values as estimated.
- [ ] A conservative cached-token estimator is available when a compatible
  provider omits cache counts.
- [ ] Reported request cost, when a provider supplies one, takes precedence
  over local estimation without changing the reported/estimated distinction.
- [ ] Anthropic cost estimation supports ordinary input, cache reads, cache
  creation with applicable TTL pricing, and output tokens.
- [ ] Per-message, per-turn, and session-cumulative estimated costs survive
  persistence/reload.

### Non-functional requirements

- [ ] The feature does not use the Anthropic Admin Cost API.
- [ ] Pricing refresh is reproducible, reviewed, and does not depend on live
  network access during normal request execution.
- [ ] Estimated cached tokens remain separate from provider-reported usage.
- [ ] Unknown models or incomplete rates produce no monetary estimate rather
  than a misleading partial total.
- [ ] Generic calculation behavior is shared rather than copied into each
  provider package.

Parent Task:
`tasks/20260824-direct-claude-provider-and-plugin-login/000-main.md`

Depends On:

- `tasks/20260824-direct-claude-provider-and-plugin-login/010-direct-claude-provider-runtime.md`

Specification:

- `docs/development/specifications/portable-provider-implementation/index.md`
- `plugins/anthropic-compatible/docs/development/specifications/anthropic-provider/index.md`

Primary requirement IDs:

- `PPI-012`
- `ANTH-016`

## Supporting facts

- OpenAI Responses already uses a maintained checked-in pricing snapshot.
- The reference OpenAI-compatible usage extension already implements
  provider-cost precedence, configured token rates, cached-token estimation,
  formatted cost, and turn/session cumulative totals.
- Ordinary Anthropic Messages usage reports token classes rather than an exact
  per-request USD charge.

## Execution plan

Status: Draft

Extract or generalize the proven usage/cost helpers behind a portable contract.
Define a maintained pricing-catalog schema and Anthropic catalog refresh
workflow. Keep provider-native usage mapping in each provider's usage extension
while sharing estimation, formatting, provenance, and cumulative calculations.

### Implementation decisions and open questions

- Decision: all locally calculated monetary values are called cost estimates.
- Decision: no Anthropic Admin API integration is included.
- Decision: pricing catalogs are checked-in runtime inputs refreshed by an
  explicit maintainer command.
- Decision: reported request cost wins when present.
- Open: choose the owning shared package/module for reusable usage and cost
  helpers.
- Open: finalize canonical cache-read/cache-write rate names while preserving
  existing `token_rates.cached` compatibility.

### Documentation

- Extend the portable provider specification and public authoring standard.
- Document pricing source, snapshot date, refresh command, model aliases,
  unsupported models, estimation provenance, and cache-rate semantics.

### Task checklist

- [ ] Finalize portable usage/cost metadata and rate-bucket names.
- [ ] Select the shared implementation owner.
- [ ] Extract reusable formatting, cumulative, cached-token, and cost helpers.
- [ ] Define pricing catalog schema and validation.
- [ ] Add maintained Anthropic pricing catalog and refresh process.
- [ ] Integrate Anthropic usage with cost estimation.
- [ ] Verify an existing OpenAI-compatible consumer after extraction.
- [ ] Add deterministic pricing, alias, cache, provenance, and reload tests.
- [ ] Document delivered behavior and update requirements.

### Requirement verification

- Known Anthropic models produce deterministic estimates from reported token
  classes and the checked-in catalog.
- Unknown models or incomplete rates produce no estimate.
- Reported cost remains authoritative when present.
- Existing OpenAI-compatible usage/cost behavior remains compatible.

### Additional implementation verification

- Pricing snapshot refresh produces reviewable deterministic changes.
- Cache-read and cache-write rates cannot be accidentally interchanged.