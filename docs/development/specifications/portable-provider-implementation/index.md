# Portable provider implementation

This cross-package specification defines the target contract for implementing
and verifying provider plugin bundles consistently across Core, the application
layer, provider packages, and shared plugin-authoring documentation.

It covers:

- provider transport and native-message responsibilities;
- provider extension ownership;
- model discovery and capability tags;
- official and compatible endpoint profiles;
- normalized usage, cost-estimation, cache-estimation, and duration/TPS
  interoperability;
- streaming, native history, cancellation, and error contracts;
- deterministic, local-compatible, and hosted conformance tests;
- package and documentation requirements.

It does not define one provider's wire protocol or require every provider to
implement the same optional features. Package-owned specifications refine this
contract for their protocol and supported endpoints.

Specification documents:

- [Technical specification](technical-spec.md)
- [Requirements and evidence](requirements.md)

Decision records:

- [Provider feature ownership](decisions/001-provider-feature-ownership.md)

Public provider-authoring guidance:

- `plugins/docs/provider-implementation-standard/index.md`

Package refinement:

- `plugins/anthropic-compatible/docs/development/specifications/anthropic-provider/index.md`

Active delivery work:

- `tasks/20260824-direct-claude-provider-and-plugin-login/010-direct-claude-provider-runtime.md`
- `tasks/20260824-direct-claude-provider-and-plugin-login/018-provider-cost-estimation-and-pricing-catalog.md`
- `tasks/20260824-direct-claude-provider-and-plugin-login/019-portable-provider-request-errors.md`