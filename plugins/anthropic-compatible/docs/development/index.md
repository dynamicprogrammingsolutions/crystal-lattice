# Anthropic-compatible provider development documentation

This development documentation covers implementation, maintenance, and the
durable design of the Anthropic-compatible provider package.

## Implementation

- [Implementation](implementation.md): runtime classes, provider/extension
  ownership, streaming sequence, and verification layout.

## Specifications

- [Anthropic provider specification](specifications/anthropic-provider/index.md):
  API-key baseline, provider/extension boundaries, Messages protocol,
  compatibility profiles, security, errors, and verification.
- [Native compaction and context editing](specifications/native-compaction-and-context-editing/index.md):
  automatic request-time compaction, context-editing policy, native
  continuation blocks, usage, and compatibility.

Package-user installation and configuration documentation is maintained in the
package `README.md` and
[Anthropic reasoning controls](../reasoning-controls.md).