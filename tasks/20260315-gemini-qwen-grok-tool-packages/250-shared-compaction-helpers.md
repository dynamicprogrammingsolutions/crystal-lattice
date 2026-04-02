# 250 - Shared Compaction Helpers and Cross-Vendor Notes

Short description: Implement shared compaction helpers for the common behavior across Gemini-like, Qwen-like, and Kimi-like compaction while preserving vendor-specific request shapes, prompts, and history-management differences.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`

Depends On:
- `tasks/20260315-gemini-qwen-grok-tool-packages/220-gemini-compaction-and-session-summary.md`
- `tasks/20260315-gemini-qwen-grok-tool-packages/230-qwen-compaction-and-checkpoint-replay.md`
- `tasks/20260315-gemini-qwen-grok-tool-packages/240-kimi-compaction-and-checkpoints.md`

## Goal

Support the implementation of compaction in this platform by identifying and extracting the behavior that is actually shared across the vendor implementations into shared helpers, without flattening away the vendor-specific semantics that matter for parity.

This task exists because the other compatibility subtasks already rely on shared non-plugin code. Compaction work should follow the same pattern where it is sensible.

The intended outcome is that a later agent can:

1. implement Gemini-like, Qwen-like, and Kimi-like compaction with thinner vendor wrappers
2. keep the shared logic in one place where the behavior is genuinely common
3. avoid forcing all vendors into one abstraction when their semantics differ too much

This file is implementation-supporting. It intentionally focuses on shared-behavior findings and source-backed notes rather than a concrete execution plan.

## Scope boundaries

This task supports implementation, but this task file currently focuses on shared-behavior findings rather than a concrete build plan.

It is in scope to implement or inform implementation, with this file documenting:

1. which compaction behaviors appear shared enough to extract
2. which behaviors should stay vendor-specific
3. where a shared helper likely belongs in the codebase
4. the Grok gap, so it is not mistakenly treated as a fourth compaction pattern

It is not in scope, at this task-authoring stage, to:

1. choose the final module layout here
2. define the final public plugin API here
3. write an execution plan in advance

## Source references

### Gemini

- `../gemini-cli/packages/core/src/services/chatCompressionService.ts`
- `../gemini-cli/packages/core/src/services/sessionSummaryService.ts`
- `../gemini-cli/packages/core/src/prompts/snippets.ts`
- `../gemini-cli/packages/core/src/core/client.ts`

### Qwen

- `../qwen-code/packages/core/src/services/chatCompressionService.ts`
- `../qwen-code/packages/core/src/services/chatRecordingService.ts`
- `../qwen-code/packages/core/src/services/sessionService.ts`
- `../qwen-code/packages/core/src/core/prompts.ts`
- `../qwen-code/packages/core/src/core/client.ts`

### Kimi

- `../kimi-cli/src/kimi_cli/soul/compaction.py`
- `../kimi-cli/src/kimi_cli/prompts/compact.md`
- `../kimi-cli/src/kimi_cli/soul/kimisoul.py`
- `../kimi-cli/src/kimi_cli/soul/context.py`
- `../kimi-cli/src/kimi_cli/config.py`

### Grok gap note

- `../grok-cli/src/agent/grok-agent.ts`

## Shared behavior worth considering for helper extraction

### 1. Trigger gating

All three implemented vendors have a distinct decision point for whether compaction should run.

Potentially shareable helper responsibilities:

1. compare current token count against thresholds
2. support more than one trigger style
3. return a structured "should compact" decision rather than a raw boolean if that proves useful

Vendor differences to preserve:

1. Gemini: threshold against active model token limit
2. Qwen: threshold against configured context window
3. Kimi: ratio trigger OR reserved-context trigger

### 2. Preserved-tail selection

All three implementations keep a recent slice of history uncompressed.

Potentially shareable helper responsibilities:

1. compute the preserved suffix boundary
2. return `to_compact` and `to_keep` / `to_preserve`

Vendor differences to preserve:

1. Gemini/Qwen: user-turn split point plus percentage-based preserved tail
2. Kimi: last `N` `user`/`assistant` messages

### 3. Compaction result structures

All three implementations return or work with:

1. new history/messages after compaction
2. token-count or usage data
3. status/failure information

Potentially shareable helper responsibilities:

1. result dataclasses / typed dicts
2. token-estimate helpers
3. status enums or status normalization

### 4. Post-compaction history replacement

All three implementations replace or rewrite model-facing history after summarization.

Potentially shareable helper responsibilities:

1. apply/replace history with compacted output
2. preserve the retained suffix
3. update token estimates or telemetry state

Vendor differences to preserve:

1. Gemini/Qwen: summary-injected history shape
2. Kimi: clear/rewrite/checkpoint/appended-summary flow

## Behavior that should remain vendor-specific

### Gemini-only or mostly Gemini-only

1. compression-model alias mapping
2. reverse-budget truncation of tool outputs before summarization
3. verification/self-correction compaction pass
4. separate prior-session one-line summary feature

### Qwen-only or mostly Qwen-only

1. explicit `chat_compression` persistence format as inspected
2. resume/replay reconstruction from latest `compressedHistory`
3. direct active-model use with the current `ContentGenerator` call shape

### Kimi-only or mostly Kimi-only

1. synthetic single-message input format with numbered historical messages
2. markdown prompt with handoff-like sections
3. `EmptyToolset()` compaction call
4. context-file clear/rewrite/checkpoint behavior
5. D-Mail-adjacent checkpoint rollback semantics

## Gemini/Qwen shared pattern to preserve

Gemini and Qwen are close enough that a later implementation should actively look for a shared helper layer for these behaviors:

1. split-point selection on user-turn boundaries
2. summarized-prefix compaction request assembly
3. summary injection back into history as:
   - `user(summary)`
   - assistant acknowledgment
   - preserved tail

Important caution:

1. Gemini's verification pass should stay optional/vendor-specific.
2. Gemini's tool-output truncation before summarization should not be assumed for Qwen.

## Kimi compatibility note

Kimi should not be forced into the Gemini/Qwen snapshot abstraction if that reduces parity. Shared helpers should be narrower for Kimi.

The best Kimi candidates for sharing are likely:

1. threshold evaluation
2. compaction result/status structures
3. maybe preserved-tail utility code if it remains parameter-driven and readable

## Grok gap note

In the inspected Grok CLI repo, I did not find a comparable session compaction subsystem. That means:

1. Grok should not drive the shared helper design here.
2. There is no fourth parity target for compaction from the inspected Grok repo.

Relevant source:

- `../grok-cli/src/agent/grok-agent.ts`

## Suggested placement notes for future implementation

These are placement notes, not a concrete implementation plan.

1. Shared logic should live in a shared non-plugin package, consistent with the other vendor-compat subtasks.
2. If compaction requires session/history ownership beyond ordinary tool behavior, some helpers may belong in application/core code rather than in a pure tool package.
3. Vendor-specific wrappers should remain thin and should own:
   - prompt text
   - request-shape differences
   - verification pass differences
   - persistence/replay differences
   - history-injection shape differences

## Requirements checklist

- [ ] Extract shared helpers only where the upstream behavior is genuinely common.
- [ ] Keep vendor-specific semantics explicit where the implementations materially diverge.
- [ ] Preserve the Gemini/Qwen shared pattern without forcing Kimi into the same abstraction.
- [ ] Preserve the note that Grok does not provide a comparable compaction subsystem in the inspected repo.