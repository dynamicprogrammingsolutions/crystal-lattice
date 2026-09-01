# Portable provider implementation requirements

These requirements track the live implementation of the
[portable provider implementation specification](index.md).

| ID | Requirement | Implementation | Verification | Documentation | Evidence |
|---|---|---|---|---|---|
| PPI-001 | Substantial provider packages expose a transport-focused provider plus independently owned optional provider extensions and package metadata. | In progress | Automated | Documented | Anthropic provider/tools/reasoning/usage implementation; caching remains |
| PPI-002 | Providers own credential consumption, request transport, native conversion, ordinary/streaming calls, full native history, cancellation, and raw error mapping without interactive login logic. | Implemented | Automated | Documented | Anthropic provider unit, stack, Ollama, and application tests |
| PPI-003 | Provider-specific extensions own interpretation, native history, metadata, tests, and docs; config/UI/request shaping may use the generic request-options contract when the feature maps directly to versioned provider request keys. | Implemented | Automated | Documented | Anthropic tools/usage own feature config; Anthropic reasoning is interpretation-only with raw request options |
| PPI-004 | Model discovery preserves authoritative capabilities and uses conservative behavior when capabilities are absent or discovery fails. | In progress | Automated | Documented | Anthropic discovery preserves raw capabilities and returns `[]` on failure; capability policy remains |
| PPI-005 | Compatible endpoints share explicit tested baseline protocol tags, reserve boolean capabilities for non-baseline optional extension tags, and use ordinary inspectable configuration presets without silently falling back to another provider or requiring hidden request filtering. | Not started | Unverified | Documented | Anthropic compatibility specification |
| PPI-006 | Streaming partials are chunk-local, completed native history contains no raw chunks/scratch state, and non-streaming and streaming finals share one contract. | Implemented | Automated | Documented | Anthropic reducer, stack, and Ollama streaming tests |
| PPI-007 | Tool schemas, calls, and results use the request-bound interop registry and preserve provider-native identity and display metadata across reload. | Implemented | Automated | Documented | Anthropic extension unit, stack, and Ollama tool tests |
| PPI-008 | Structured provider errors retain stable categories, retryability, request IDs, and redacted details through application events while provider retries and auth lifecycle remain plugin-owned. | Not started | Unverified | Pending | `tasks/20260824-direct-claude-provider-and-plugin-login/019-portable-provider-request-errors.md` |
| PPI-009 | Provider conformance includes deterministic contracts, public application integration, supported local-compatible configurations, and selective hosted verification with explicit marker/skip rules. | In progress | Automated | Documented | Anthropic deterministic, default-config application, Ollama, and selective hosted Stage 1 tests pass |
| PPI-010 | Each substantial provider package documents configuration, credentials, models, extensions, compatibility, errors, cancellation, verification, and limitations. | Implemented | Inspected | Documented | Anthropic README and development implementation guide |
| PPI-011 | Providers with token usage expose normalized formatted per-message, turn-cumulative, and session-cumulative usage that survives reload and interoperates with duration/TPS calculation. | In progress | Automated | Documented | Anthropic usage and reload tests pass; duration/TPS consumer verification remains Stage 2 |
| PPI-012 | Provider cost estimation uses maintained public model-pricing catalogs, explicit reported-versus-estimated provenance, conservative cached-token estimation, and shared calculation helpers without inventing values for unknown models. | Not started | Unverified | Documented | `tasks/20260824-direct-claude-provider-and-plugin-login/018-provider-cost-estimation-and-pricing-catalog.md`; public usage/cost/performance standard |
| PPI-013 | Providers claiming reasoning and tools pass the canonical bank-file continuity test in ordinary and streaming modes; profiles claiming cross-request reasoning preservation also satisfy the interrupted-user reasoning-size contract or record an explicit negative profile. | In progress | Automated | Documented | direct Anthropic Haiku ordinary/streaming and Sonnet keep-all hosted tests pass; Anthropic latest-turn-only reports cleared reasoning and OpenRouter Claude interrupted-user is a strict expected failure |

## Current-state note

Existing providers implement portions of this target but are not declared
fully conformant by this requirements file. Package-specific requirements and
tests remain authoritative for delivered behavior until conformance evidence
is recorded.