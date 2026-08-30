# Anthropic-compatible provider

This specification defines the target behavior owned by the planned
`plugins/anthropic-compatible` package.

It covers:

- the `anthropic` provider identity and API-key baseline;
- ordinary and streaming Anthropic Messages requests;
- official capability-based model discovery;
- configurable Anthropic-compatible endpoints;
- provider-native message, content-block, and history contracts;
- separate tools, reasoning, usage, prompt-caching, and attachment extensions;
- cancellation, stable errors, redaction, and compatibility degradation;
- deterministic, local Ollama, and hosted Anthropic verification.

The baseline does not include OAuth acquisition, server web tools, fast mode,
native compaction, the Files API, PDFs, token counting, advanced server tools,
batch processing, or structured outputs. OAuth and selected provider features
are tracked by separate tasks and must refine this package specification before
implementation.

Specification documents:

- [Product specification](product-spec.md)
- [Technical specification](technical-spec.md)
- [Messages protocol](protocol.md)
- [Compatibility profiles](compatibility.md)
- [Security and errors](security-and-errors.md)
- [Verification](verification.md)
- [Requirements and evidence](requirements.md)

Decision records:

- [Package identity and extension boundaries](decisions/001-package-identity-and-extension-boundaries.md)
- [Compatibility and capability discovery](decisions/002-compatibility-and-capability-discovery.md)

Related portable contract:

- [Portable provider implementation](../../../../../../docs/development/specifications/portable-provider-implementation/index.md)

Active delivery work:

- `tasks/20260824-direct-claude-provider-and-plugin-login/010-direct-claude-provider-runtime.md`