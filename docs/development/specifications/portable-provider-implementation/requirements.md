# Portable provider implementation requirements

These requirements track the live implementation of the
[portable provider implementation specification](index.md).

| ID | Requirement | Implementation | Verification | Documentation | Evidence |
|---|---|---|---|---|---|
| PPI-001 | Substantial provider packages expose a transport-focused provider plus independently owned optional provider extensions and package metadata. | In progress | Unverified | Documented | `plugins/docs/provider-implementation-standard/`; existing provider packages; Anthropic subtask 010 |
| PPI-002 | Providers own credential consumption, request transport, native conversion, ordinary/streaming calls, full native history, cancellation, and raw error mapping without interactive login logic. | In progress | Unverified | Documented | public provider standard; `core/python/agent_core/types.py` |
| PPI-003 | Provider-specific extensions own their config, UI, tags, enablement, request shaping, public metadata, tests, and docs even when transport mechanics remain in the provider. | In progress | Unverified | Documented | decision 001; public provider standard |
| PPI-004 | Model discovery preserves authoritative capabilities and uses conservative behavior when capabilities are absent or discovery fails. | Not started | Unverified | Documented | Anthropic subtask 010; public provider standard |
| PPI-005 | Official and compatible endpoints use explicit tested profiles and never silently enable unsupported fields or fall back to another provider. | Not started | Unverified | Documented | Anthropic compatibility specification |
| PPI-006 | Streaming partials are chunk-local, completed native history contains no raw chunks/scratch state, and non-streaming and streaming finals share one contract. | In progress | Unverified | Documented | Core provider protocol; public provider standard |
| PPI-007 | Tool schemas, calls, and results use the request-bound interop registry and preserve provider-native identity and display metadata across reload. | In progress | Unverified | Documented | `plugins/docs/tool-interop.md`; public provider standard |
| PPI-008 | Structured provider errors retain stable categories, retryability, request IDs, and redacted details through application events. | Not started | Unverified | Pending | Anthropic subtask 010 |
| PPI-009 | Provider conformance includes deterministic contracts, public application integration, supported local-compatible profiles, and selective hosted verification with explicit marker/skip rules. | Not started | Unverified | Documented | public conformance standard; Anthropic verification specification |
| PPI-010 | Each substantial provider package documents configuration, credentials, models, extensions, compatibility, errors, cancellation, verification, and limitations. | In progress | Unverified | Documented | public package/documentation standard |

## Current-state note

Existing providers implement portions of this target but are not declared
fully conformant by this requirements file. Package-specific requirements and
tests remain authoritative for delivered behavior until conformance evidence
is recorded.