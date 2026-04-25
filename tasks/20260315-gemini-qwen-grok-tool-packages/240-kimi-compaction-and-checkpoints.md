# 240 - Kimi Compaction and Checkpoints

Short description: Implement Kimi-like context compaction in this platform, using the source findings in this file to reconstruct Kimi's markdown prompt, single-message summarization request, preserved-tail behavior, and checkpoint-adjacent context management as closely as practical.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`

## Goal

Implement Kimi-like compaction behavior in this platform. The research captured in this file is meant to save rediscovery time for the completing agent.

The intended outcome is that a later agent can:

1. Reconstruct the exact compaction prompt and single-message request shape.
2. Preserve Kimi's threshold logic and preserved-tail behavior.
3. Mirror how Kimi rewrites context after compaction.
4. Separate true compaction from Kimi's checkpoint/D-Mail "time travel" mechanism.

This file intentionally emphasizes source findings and references over design decisions. It should help the completing agent implement the feature without having to rediscover the upstream behavior.

## Scope boundaries

This task culminates in implementation, but this task file currently records research findings rather than a concrete build plan.

It is in scope to implement, with this file documenting:

1. Compaction thresholds and preserved-message logic.
2. The exact compaction markdown prompt.
3. The request shape sent to the current runtime LLM.
4. The output injection shape after compaction.
5. The context clear/rewrite/checkpoint sequence.
6. The related checkpoint and D-Mail mechanisms as adjacent capabilities.

It is not in scope, at this task-authoring stage, to:

1. Commit to a concrete implementation approach here.
2. Add an execution plan in advance.
3. Omit the upstream behavioral details needed for parity.

## Key source references

All paths are relative to the locally cloned Kimi CLI repo at `../kimi-cli`, commit `7ba9695`.

### Compaction engine

- Main compaction logic:
  - `src/kimi_cli/soul/compaction.py`
- Compaction prompt template:
  - `src/kimi_cli/prompts/compact.md`
- Prompt export module:
  - `src/kimi_cli/prompts/__init__.py`

### Runtime application of compaction

- Auto-compaction trigger and compaction orchestration:
  - `src/kimi_cli/soul/kimisoul.py:550`
- `compact_context(...)` application flow:
  - `src/kimi_cli/soul/kimisoul.py:732`

### Context, checkpoints, and D-Mail-adjacent behavior

- Context persistence and checkpoint records:
  - `src/kimi_cli/soul/context.py`
- D-Mail tool description:
  - `src/kimi_cli/tools/dmail/dmail.md`

### Trigger configuration

- Reserved-context and ratio config:
  - `src/kimi_cli/config.py:81`

## Compaction findings

### Trigger behavior

Kimi auto-compacts when either of these is true:

1. `token_count >= max_context_size * compaction_trigger_ratio`
2. `token_count + reserved_context_size >= max_context_size`

Source:

- `src/kimi_cli/soul/compaction.py:56`

Default config values:

1. `reserved_context_size = 50000`
2. `compaction_trigger_ratio = 0.85`

Source:

- `src/kimi_cli/config.py:81`

### Preserved-tail logic

Kimi's `SimpleCompaction` preserves the last two `user`/`assistant` messages by default:

- `src/kimi_cli/soul/compaction.py:103`

More precisely:

1. It scans backward for the last `max_preserved_messages` messages whose role is `user` or `assistant`.
2. Everything before that boundary becomes `to_compact`.
3. Everything from that boundary onward becomes `to_preserve`.

This is structurally simpler than Gemini and Qwen's percentage-based preserved tail.

### Compaction prompt body

The prompt text is in:

- `src/kimi_cli/prompts/compact.md:1`

Important characteristics to preserve:

1. Markdown prompt, not XML.
2. Explicit priority ordering:
   - current task state
   - errors and solutions
   - code evolution
   - system context
   - design decisions
   - TODO items
3. Explicit compression rules for what to keep, merge, remove, and condense.
4. Required structured output sections:
   - `<current_focus>`
   - `<environment>`
   - `<completed_tasks>`
   - `<active_issues>`
   - `<code_state>`
   - `<important_context>`

### Exact request shape

Kimi does not send the original conversation as a normal multi-turn chat history.

Instead, it builds a single synthetic `user` message in:

- `src/kimi_cli/soul/compaction.py:171`

That message contains:

1. a sequence of blocks like:
   - `## Message N`
   - `Role: <role>`
   - `Content:`
2. only `TextPart` content from each compacted message
3. the full compaction prompt text appended at the end
4. optionally a custom instruction block if the user ran `/compact <focus>`

This is a major difference from Gemini and Qwen.

### Model / call parameters

Kimi uses the current runtime LLM/provider rather than a dedicated summarizer model.

The compaction call is:

- `src/kimi_cli/soul/compaction.py:117`

Exact structure to preserve:

1. `chat_provider=llm.chat_provider`
2. `system_prompt="You are a helpful assistant that compacts conversation context."`
3. `toolset=EmptyToolset()`
4. `history=[compact_message]`

Important notes:

1. No tools are available during compaction.
2. There is no separate tool loop.
3. No dedicated summarizer model is selected.
4. There is a TODO comment about max completion tokens, but no max completion parameter is currently set.

### Output injection shape

After the model returns a compacted result:

1. Kimi creates a single new `user` message.
2. Its first content part is a system-style notice: `Previous context has been compacted. Here is the compaction output:`
3. It then appends the compacted result content, excluding any `ThinkPart` items.
4. It then appends the preserved tail messages after that single compacted message.

Source:

- `src/kimi_cli/soul/compaction.py:130`

This means Kimi injects compaction output as one synthesized `user` turn, not as `user(summary)` + assistant acknowledgment like Gemini/Qwen.

### How compaction is applied to context

Kimi rewrites context more aggressively than Gemini/Qwen.

`compact_context(...)` does the following:

1. emits `CompactionBegin()` over the wire
2. runs compaction with retry
3. clears the context file/history
4. rewrites the system prompt as the first record again
5. creates a checkpoint
6. appends the compacted messages
7. updates estimated token count
8. emits `CompactionEnd()`

Source:

- `src/kimi_cli/soul/kimisoul.py:732`

### Checkpoints and D-Mail-adjacent behavior

Kimi's context subsystem has an explicit checkpoint mechanism:

- `src/kimi_cli/soul/context.py:95`

Relevant capabilities:

1. `_checkpoint` records are appended to the session context file.
2. Optional user-visible `CHECKPOINT <id>` messages can be injected.
3. Context can be reverted to an earlier checkpoint via `revert_to(...)`.

Kimi also has a D-Mail tool that lets the agent revert to a previous checkpoint and append a message from its future self.

Important distinction to preserve:

1. D-Mail is not the same as compaction.
2. It is a checkpoint rollback + handoff mechanism.
3. It is still relevant context-management behavior for future compatibility work.

Relevant D-Mail description:

- `src/kimi_cli/tools/dmail/dmail.md`

## Shared-helper opportunities

Kimi should share helper code only where the behavior is truly common. Its compaction shape is materially different from Gemini and Qwen.

Likely shared helpers:

1. Threshold-check helpers for deciding whether compaction should trigger.
2. Utility/result structures for compaction outcomes and token estimates.
3. Maybe a small preserved-tail helper if it can be parameterized cleanly by retention strategy.

Likely Kimi-only helpers:

1. Flattening a history prefix into one synthetic `user` message.
2. Markdown compaction prompt handling.
3. `EmptyToolset()` compaction invocation against the current runtime LLM.
4. Context clear/rewrite/checkpoint flow.
5. D-Mail- and checkpoint-adjacent context operations.

The completing agent should avoid over-generalizing Gemini/Qwen snapshot abstractions into Kimi if that would hide Kimi's distinctive request shape and context rewrite behavior.

## Additional findings

1. I did not find a separate Gemini-style previous-session summary feature in the inspected Kimi code.
2. Kimi's compaction is text-only in terms of the generated compact message input: it serializes only `TextPart` content from prior messages.
3. Kimi's compaction shape is the most handoff-like of the inspected systems.

## Requirements checklist

- [ ] Implement Kimi-like compaction behavior in this platform, informed by the sources below.
- [ ] Implement Kimi-like context rewrite/checkpoint behavior where applicable, or clearly document any intentional deviation made during completion.
- [ ] Extract only the truly shared parts into shared helpers and keep Kimi-specific flow distinct where needed.
- [ ] Preserve the exact markdown compaction prompt and required output sections.
- [ ] Preserve the single-synthetic-user-message request shape built from numbered prior messages.
- [ ] Preserve the fact that compaction uses the current runtime LLM with `EmptyToolset()` and a simple generic system prompt.
- [ ] Preserve the exact output injection shape: one synthesized `user` message plus preserved tail.
- [ ] Preserve the clear/rewrite/checkpoint/appended-summary flow in `compact_context(...)`.
- [ ] Preserve the distinction between compaction and the D-Mail checkpoint-revert mechanism.
