# 230 - Qwen Compaction and Checkpoint Replay

Short description: Implement Qwen-like live chat compaction and checkpoint replay behavior in this platform, using the source findings in this file to reconstruct Qwen's prompt, request shape, checkpoint records, and resume behavior as closely as practical.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`

## Goal

Implement Qwen-like compaction behavior in this platform. The research captured in this file is meant to save rediscovery time for the completing agent.

The intended outcome is that a later agent can:

1. Reconstruct the exact compaction request sent to the model.
2. Reproduce the compaction prompt and token-threshold logic.
3. Mirror how Qwen persists compacted history and rebuilds it on resume.
4. Compare Qwen's simpler one-pass compressor to Gemini and Kimi.

This file intentionally emphasizes source findings and references over design decisions. It should help the completing agent implement the feature without having to rediscover the upstream behavior.

## Scope boundaries

This task culminates in implementation, but this task file currently records research findings rather than a concrete build plan.

It is in scope to implement, with this file documenting:

1. Compaction thresholds and split-point logic.
2. Prompt body and request structure.
3. How Qwen injects the compacted summary into history.
4. How Qwen persists `chat_compression` checkpoints.
5. Resume/replay behavior from those checkpoints.

It is not in scope, at this task-authoring stage, to:

1. Commit to a concrete implementation approach here.
2. Add an execution plan in advance.
3. Omit the upstream behavioral details needed for parity.

## Key source references

All paths are relative to the locally cloned Qwen Code repo at `../qwen-code`, commit `f6a90dd`.

### Live compaction

- Main service:
  - `packages/core/src/services/chatCompressionService.ts`
- Compression prompt body:
  - `packages/core/src/core/prompts.ts:349`
- Main client call site:
  - `packages/core/src/core/client.ts:630`

### Checkpoint persistence and replay

- Chat recording payload type:
  - `packages/core/src/services/chatRecordingService.ts:101`
- Chat compression record writer:
  - `packages/core/src/services/chatRecordingService.ts:398`
- Resume/replay logic:
  - `packages/core/src/services/sessionService.ts:592`
- Prompt-token restoration on resume:
  - `packages/core/src/services/sessionService.ts:681`

## Compaction findings

### Trigger and split-point behavior

1. Default compaction threshold is `0.7` of the configured context window:
   - `packages/core/src/services/chatCompressionService.ts:22`
2. Preserve threshold is `0.3`:
   - `packages/core/src/services/chatCompressionService.ts:28`
3. Split points are chosen on user-turn boundaries using `findCompressSplitPoint(...)`:
   - `packages/core/src/services/chatCompressionService.ts:36`
4. Automatic compaction is skipped if a previous compaction failed and the caller is not forcing compression:
   - `packages/core/src/services/chatCompressionService.ts:92`

### Compression prompt body

The compaction prompt is in:

- `packages/core/src/core/prompts.ts:349`

Important characteristics to preserve in future reconstruction notes:

1. It is a structured XML `<state_snapshot>` prompt.
2. It asks for private `<scratchpad>` reasoning before final output.
3. It emphasizes preservation of plans, errors, and user directives.
4. It is shorter and less defensive than Gemini's current prompt.

The XML structure explicitly includes:

1. `<overall_goal>`
2. `<key_knowledge>`
3. `<file_system_state>`
4. `<recent_actions>`
5. `<current_plan>`

### Exact request shape

The compaction request is assembled in:

- `packages/core/src/services/chatCompressionService.ts:146`

Exact structure to preserve:

1. Request goes through `config.getContentGenerator().generateContent(...)`, not `BaseLlmClient`.
2. `model: model` — the active chat model string is used directly.
3. `contents:`
   - `...historyToCompress`
   - one appended `user` message: `First, reason in your scratchpad. Then, generate the <state_snapshot>.`
4. `config.systemInstruction: getCompressionPrompt()`
5. outer call receives `promptId` as the second argument to `generateContent(...)`

Important differences from Gemini:

1. No dedicated compression model alias mapping.
2. No explicit utility role flag in this call site.
3. No second verification/self-correction pass.
4. No pre-summarization tool-output truncation stage was found in this implementation.

### Injection of compacted summary back into history

If summarization succeeds, Qwen constructs `extraHistory` as:

1. `user(summary)`
2. `model("Got it. Thanks for the additional context!")`
3. `...historyToKeep`

Source:

- `packages/core/src/services/chatCompressionService.ts:188`

### Checkpoint persistence

Unlike the inspected Gemini code, Qwen explicitly persists chat-compression checkpoints.

Relevant structures:

1. `ChatCompressionRecordPayload` contains:
   - `info`
   - `compressedHistory`
   - `packages/core/src/services/chatRecordingService.ts:105`
2. `recordChatCompression(...)` writes a `system` record with subtype `chat_compression`:
   - `packages/core/src/services/chatRecordingService.ts:398`

### Client-side application of compression

The main client calls compression via:

- `packages/core/src/core/client.ts:630`

If compaction succeeds:

1. it records the checkpoint via `chatRecordingService?.recordChatCompression(...)`
2. it restarts chat with the compressed history
3. it updates last-prompt token telemetry

This is the cleanest inspected example of an explicit persisted compaction checkpoint.

### Replay and resume behavior

On resume, Qwen reconstructs API history from the latest checkpoint:

- `packages/core/src/services/sessionService.ts:592`

Replay strategy:

1. scan conversation records for the latest `system/chat_compression`
2. use its `compressedHistory` snapshot as the base model-facing history
3. append all later non-system messages
4. optionally strip `thought` parts

It also restores prompt-token count from the latest checkpoint or the last assistant usage record:

- `packages/core/src/services/sessionService.ts:681`

## Shared-helper opportunities

Qwen is the strongest candidate for shared helpers with Gemini.

Likely shared helpers:

1. History split-point calculation on user-turn boundaries.
2. Threshold gating for auto-compaction.
3. XML-style summarized-prefix compaction request assembly.
4. Post-compaction injection in the form:
   - `user(summary)`
   - assistant acknowledgment
   - preserved tail
5. Persistence abstractions for storing a compacted-history snapshot and later replaying it.

Likely Qwen-only helpers:

1. Direct use of the active model string instead of Gemini's compression-model alias mapping.
2. One-pass compaction with no verification pass.
3. The explicit `chat_compression` checkpoint record and replay behavior as currently implemented.

The completing agent should prefer shared helpers with Gemini where the behavior is genuinely common, but should not force Kimi into the same abstractions if that makes Kimi's compaction shape less accurate.

## Additional findings

1. I did not find a separate Gemini-style prior-session one-line summary feature in the inspected Qwen code.
2. Qwen's compaction is simpler and more linear than Gemini's: one prompt, one model call, one checkpoint write.

## Requirements checklist

- [ ] Implement Qwen-like compaction behavior in this platform, informed by the sources below.
- [ ] Implement Qwen-like checkpoint persistence and replay behavior or clearly document any intentional deviation made during completion.
- [ ] Extract any Gemini/Qwen-shared logic into shared helpers only where parity remains clear.
- [ ] Preserve the exact one-pass request shape used by `config.getContentGenerator().generateContent(...)`.
- [ ] Preserve the XML compaction prompt structure from `core/prompts.ts`.
- [ ] Preserve the injection shape: `user(summary)` then assistant acknowledgment then preserved tail.
- [ ] Preserve the explicit `chat_compression` checkpoint record behavior.
- [ ] Preserve the replay/resume strategy based on latest `compressedHistory`.
- [ ] Preserve the note that no separate prior-session summary feature was confirmed in the inspected Qwen code.
