# Kimi compaction parity

This specification defines the manual `compact_conversation` and
`compact_up_to_here` session actions owned by the `kimi-tools` plugin package.
It targets parity with `kimi-cli`'s `SimpleCompaction` for the compaction
request shape, system prompt, tool suppression, preserved-tail behavior,
summary injection format, prompt body, and enablement enforcement.

It covers:

- the single synthetic user message built from `## Message N` blocks,
  including a selected leading agent system message;
- the generic compactor system prompt used only for the compaction request;
- unconditional tool suppression via `disable_all_tools`, after configurable
  request overrides;
- preserved-tail behavior for full-range compaction;
- the `<system>…</system>`-wrapped summary injection in one user message;
- the exact `kimi-cli` compaction prompt body;
- agent-level enablement through `compaction.enabled` and `compaction.type`;
- the top-level per-session `compaction_model` override emitted by the
  configuration UI;
- intentional deviations from `kimi-cli` (auto-compaction, checkpoint/context
  rewrite, D-Mail).

It does not redefine general feature-plugin lifecycle, session persistence,
native-history rebuilding, or the platform's `disable_all_tools` tool-gating
contract. It applies those package and framework capabilities to Kimi-style
compaction.

Artifacts:

- [Product specification](product-spec.md)
- [Technical specification](technical-spec.md)
- [Requirements and evidence](requirements.md)

Approval and execution are tracked by
[Kimi compaction parity correction task](../../../../../../tasks/20260816-kimi-compaction-parity.md).

The historical research task
[Kimi compaction and checkpoints](../../../../../../tasks/20260315-gemini-qwen-grok-tool-packages/240-kimi-compaction-and-checkpoints.md)
is superseded for the manual-compaction portion by this specification and its
approval task. The checkpoint/D-Mail portion of the historical task remains
open and separate.