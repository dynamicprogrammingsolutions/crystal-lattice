# Anthropic-compatible provider

This specification defines the target behavior owned by the planned
`plugins/anthropic-compatible` package.

It covers:

- the `anthropic` provider identity and API-key baseline;
- ordinary and streaming Anthropic Messages requests;
- official capability-based model discovery;
- configurable Anthropic-compatible endpoints;
- provider-native message, content-block, and history contracts;
- separate tools, reasoning, usage, and prompt-caching extensions;
- cancellation, safe generic request errors, redaction, and compatibility
  degradation;
- deterministic, local Ollama, and hosted Anthropic verification.

The baseline does not include OAuth acquisition, server web tools, fast mode,
native compaction, the Files API, PDFs, token counting, advanced server tools,
image attachments, model-price cost estimation, a portable structured provider
request-error contract, batch processing, or structured outputs. OAuth and
selected provider features are tracked by separate tasks and must refine this
package specification before implementation.

Specification documents:

- [Product specification](product-spec.md)
- [Technical specification](technical-spec.md)
- [Messages protocol](protocol.md)
- [Compatible endpoint capabilities](compatibility.md)
- [Security and errors](security-and-errors.md)
- [Verification](verification.md)
- [Requirements and evidence](requirements.md)

Decision records:

- [Package identity and extension boundaries](decisions/001-package-identity-and-extension-boundaries.md)
- [Compatibility and capability discovery](decisions/002-compatibility-and-capability-discovery.md)
- [Anthropic SDK transport](decisions/003-anthropic-sdk-transport.md)

Package feature refinements:

- [Native compaction and context editing](../native-compaction-and-context-editing/index.md)

Related portable contract:

- [Portable provider implementation](../../../../../../docs/development/specifications/portable-provider-implementation/index.md)

Active delivery work:

- `tasks/20260824-direct-claude-provider-and-plugin-login/010-direct-claude-provider-runtime.md`
- `tasks/20260824-direct-claude-provider-and-plugin-login/013-anthropic-native-compaction-and-context-editing.md`
- `tasks/20260824-direct-claude-provider-and-plugin-login/017-anthropic-image-attachments.md`
- `tasks/20260824-direct-claude-provider-and-plugin-login/018-provider-cost-estimation-and-pricing-catalog.md`
- `tasks/20260824-direct-claude-provider-and-plugin-login/019-portable-provider-request-errors.md`