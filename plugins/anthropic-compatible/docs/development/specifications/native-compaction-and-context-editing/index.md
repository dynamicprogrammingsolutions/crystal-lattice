# Anthropic native compaction and context editing

This package-owned specification refines the
[Anthropic-compatible provider specification](../anthropic-provider/index.md)
for native context management.

It covers:

- automatic request-time compaction through Anthropic Messages;
- independent thinking-retention and tool-use-clearing policies;
- official model-capability and explicit compatible-endpoint gating;
- versioned beta composition;
- compaction blocks, streaming deltas, and continuation;
- applied-edit and iteration-usage reporting;
- cancellation, compatibility, and verification.

It does not define generic prompt summarization, manual visible-prefix
compaction, a separate background compaction process, or managed
`pause_after_compaction: true` continuation.

Specification documents:

- [Product specification](product-spec.md)
- [Technical specification](technical-spec.md)
- [Protocol](protocol.md)
- [Requirements and evidence](requirements.md)

Related portable contract:

- [Portable provider implementation](../../../../../../docs/development/specifications/portable-provider-implementation/index.md)

Active delivery work:

- `tasks/20260824-direct-claude-provider-and-plugin-login/013-anthropic-native-compaction-and-context-editing.md`