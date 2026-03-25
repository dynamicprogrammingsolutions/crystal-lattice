# 220 - Gemini Compaction and Session Summary

Short description: Implement Gemini-like live chat compaction and the separate previous-session summary behavior in this platform, using the source findings in this file to reconstruct Gemini's request shapes, prompts, and history-injection behavior as closely as practical.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`

## Goal

Implement Gemini-like compaction and session-summary behavior in this platform. The research captured in this file is meant to save rediscovery time for the completing agent.

The intended outcome is that a later agent can:

1. Reconstruct the exact request shapes sent to the model.
2. Reproduce the compaction prompts and model-selection logic.
3. Mirror how Gemini injects compacted state back into chat history.
4. Decide which parts belong in a future `gemini-tools` compaction plugin versus host/runtime support.

This file intentionally emphasizes source findings and references over design decisions. It should help the completing agent implement the feature without having to rediscover the upstream behavior.

## Scope boundaries

This task culminates in implementation, but this task file currently records research findings rather than a concrete build plan.

It is in scope to implement, with this file documenting:

1. Prompt text and prompt builders.
2. Request contents and parameters.
3. Trigger thresholds and split-point logic.
4. How tool outputs are truncated before summarization.
5. How the compacted summary is injected back into history.
6. The separate prior-session summary feature.

It is not in scope, at this task-authoring stage, to:

1. Commit to a concrete implementation approach here.
2. Add an execution plan in advance.
3. Omit the upstream behavioral details needed for parity.

## Key source references

All paths are relative to the locally cloned Gemini CLI repo at `../gemini-cli`, commit `020da58`.

### Live compaction

- Main service:
  - `packages/core/src/services/chatCompressionService.ts`
- Compression prompt entrypoint:
  - `packages/core/src/core/prompts.ts:38`
- Compression prompt body:
  - `packages/core/src/prompts/snippets.ts:695`
- Main client call site:
  - `packages/core/src/core/client.ts:1049`
- Local executor call site:
  - `packages/core/src/agents/local-executor.ts:668`

### Separate previous-session summary

- Summary service:
  - `packages/core/src/services/sessionSummaryService.ts`
- Background/session-list helper:
  - `packages/core/src/services/sessionSummaryUtils.ts`
- Startup trigger:
  - `packages/cli/src/ui/AppContainer.tsx:482`
- Session-list trigger:
  - `packages/cli/src/utils/sessions.ts:20`

## Live compaction findings

### Trigger and split-point behavior

1. Default auto-compaction threshold is `0.5` of the active model's token limit:
   - `packages/core/src/services/chatCompressionService.ts:40`
2. Preserve threshold is `0.3`, meaning roughly the newest 30% of history is retained uncompressed:
   - `packages/core/src/services/chatCompressionService.ts:46`
3. Split-point selection is based on user-turn boundaries, not arbitrary message indices:
   - `packages/core/src/services/chatCompressionService.ts:59`
4. If the newest message is a model message with no pending function call, Gemini may compress all prior history.

### Tool-output truncation before summarization

1. Gemini first applies a reverse-budget truncation pass across tool responses before it asks the model to summarize:
   - `packages/core/src/services/chatCompressionService.ts:132`
2. Function/tool-response token budget is `50_000`:
   - `packages/core/src/services/chatCompressionService.ts:51`
3. Older oversized tool outputs are replaced with a truncated placeholder produced via:
   - `saveTruncatedToolOutput(...)`
   - `formatTruncatedToolOutput(...)`
   - both referenced in `packages/core/src/services/chatCompressionService.ts:16`
4. If truncation fails, Gemini keeps the original part rather than dropping it.

### Model selection for compaction

Gemini does not use the active chat model string directly for the compaction call. It maps the active model to a dedicated compression model config alias via:

- `modelStringToModelConfigAlias(...)` in `packages/core/src/services/chatCompressionService.ts:101`

Known mappings include:

1. `gemini-3-pro-preview` / `gemini-3.1` style models -> `chat-compression-3-pro`
2. preview flash models -> `chat-compression-3-flash`
3. `gemini-2.5-pro` -> `chat-compression-2.5-pro`
4. `gemini-2.5-flash` -> `chat-compression-2.5-flash`
5. `gemini-2.5-flash-lite` -> `chat-compression-2.5-flash-lite`
6. fallback -> `chat-compression-default`

### Compression prompt body

The prompt comes from `getCompressionPrompt(config)` and the current modern body is in:

- `packages/core/src/prompts/snippets.ts:695`

Important characteristics to preserve in future reconstruction notes:

1. It explicitly treats the summarizer as a specialized system component.
2. It has a strong prompt-injection defense section.
3. It requires output to stay inside a structured XML `<state_snapshot>`.
4. It asks for a private `<scratchpad>` reasoning phase.
5. It requires dense retention of goal, constraints, discoveries, file/system state, recent actions, and immediate task state.

The XML structure includes these named sections:

1. `<overall_goal>`
2. `<active_constraints>`
3. `<key_knowledge>`
4. `<artifact_trail>`
5. `<file_system_state>`
6. `<recent_actions>`
7. `<task_state>`

### First compaction request shape

The main summarization request is assembled in:

- `packages/core/src/services/chatCompressionService.ts:353`

Exact structure to preserve:

1. `modelConfigKey: { model: modelStringToModelConfigAlias(model) }`
2. `contents:`
   - `...historyForSummarizer`
   - one extra `user` message whose text is:
     - either an anchor instruction saying a previous `<state_snapshot>` exists and must be integrated
     - or an instruction to generate a new snapshot
     - followed by `First, reason in your scratchpad. Then, generate the updated <state_snapshot>.`
3. `systemInstruction: { text: getCompressionPrompt(config) }`
4. `promptId: promptId`
5. `role: LlmRole.UTILITY_COMPRESSOR`
6. `abortSignal: abortSignal ?? new AbortController().signal`

Important input-shaping rule:

1. Gemini chooses between original history and truncated history before summarization.
2. It prefers the original prefix if that prefix fits within the summarizer model's token limit.
3. Otherwise it summarizes the truncated prefix.

Relevant code:

- `packages/core/src/services/chatCompressionService.ts:334`

### Verification request shape

Gemini performs a second self-correction pass after the first summary:

- `packages/core/src/services/chatCompressionService.ts:374`

Exact structure to preserve:

1. Same `modelConfigKey`
2. Same `systemInstruction`
3. `contents:`
   - `...historyForSummarizer`
   - a `model` turn containing the first generated summary
   - a final `user` turn asking the model to critically evaluate whether it omitted technical details, file paths, tool results, or user constraints, and to output a FINAL improved `<state_snapshot>` if needed
4. `promptId: ${promptId}-verify`
5. `role: LlmRole.UTILITY_COMPRESSOR`

This verification pass is a major Gemini-specific behavior difference from Qwen and Kimi.

### Injection of compacted summary back into chat history

After verification, Gemini constructs the new history as:

1. `user(finalSummary)`
2. `model("Got it. Thanks for the additional context!")`
3. `...historyToKeepTruncated`

Source:

- `packages/core/src/services/chatCompressionService.ts:423`

Important note:

1. In the inspected Gemini code, I did not confirm a Qwen-style persisted `chat_compression` checkpoint record.
2. The main client resets/restarts chat with the compressed history and preserved resumed-session data instead:
   - `packages/core/src/core/client.ts:1074`
3. The local executor variant updates in-memory history directly:
   - `packages/core/src/agents/local-executor.ts:688`

### Failure and fallback behaviors worth preserving in notes

1. If prior summarization failed and compression is retried automatically, Gemini may skip a new summarizer call and rely only on tool-output truncation.
2. Empty summary is treated as failure.
3. If calculated new token count inflates history, compression is rejected.
4. If truncation alone meaningfully reduces tokens, Gemini can return `CONTENT_TRUNCATED` rather than full summarized compression.

Relevant anchors:

- `packages/core/src/services/chatCompressionService.ts:255`
- `packages/core/src/services/chatCompressionService.ts:405`

## Shared-helper opportunities

While Gemini has several vendor-specific behaviors, the implementation should look for shared helpers that can also serve Qwen and, where reasonable, Kimi.

Likely shared helpers:

1. History split-point selection on user-turn boundaries.
2. Threshold checks that decide whether compaction should run.
3. A request-assembly helper for:
   - base history prefix to summarize
   - appended compaction instruction turn
   - optional system prompt
4. A post-compaction injection helper for the Gemini/Qwen pattern:
   - `user(summary)`
   - assistant acknowledgment
   - preserved tail
5. Result/status structures for compaction outcomes and token counts.

Likely Gemini-only helpers:

1. Compression-model alias mapping.
2. Reverse-budget tool-output truncation before summarization.
3. Verification/self-correction pass.
4. Separate prior-session one-line summary flow.

The completing agent should prefer shared helpers only where they do not blur Gemini-specific behavior.

## Separate previous-session summary findings

Gemini also has a distinct feature for generating a short summary of the previous session. This is not the same as live chat compaction.

### Summary prompt

The exact prompt text is in:

- `packages/core/src/services/sessionSummaryService.ts:19`

It asks for:

1. The user's primary intent or goal.
2. One sentence only.
3. Maximum 80 characters.
4. Several example summaries.

### Input shaping

Before making the summary request, Gemini:

1. filters to `user` and `gemini` messages only
2. drops empty/system-style records
3. uses a sliding window of first `N/2` and last `N/2` messages if there are more than `maxMessages`
4. truncates each message to `500` chars

Defaults:

1. `DEFAULT_MAX_MESSAGES = 20`
2. `DEFAULT_TIMEOUT_MS = 5000`

Source:

- `packages/core/src/services/sessionSummaryService.ts:15`

### Session-summary request shape

The request is a single-turn summarizer call:

1. `contents = [{ role: 'user', parts: [{ text: prompt }] }]`
2. `modelConfigKey: { model: 'summarizer-default' }`
3. `abortSignal: abortController.signal`
4. `promptId: 'session-summary-generation'`
5. `role: LlmRole.UTILITY_SUMMARIZER`

Source:

- `packages/core/src/services/sessionSummaryService.ts:115`

Notable differences from live compaction:

1. No special compaction XML prompt.
2. No tool outputs or tool loop.
3. No verification pass.
4. Output is not injected into chat history.

### Where the session summary goes

The cleaned summary is written to `conversation.summary` in the session file, not added to model-visible history:

- `packages/core/src/services/sessionSummaryUtils.ts:20`

Trigger points:

1. background fire-and-forget on app startup:
   - `packages/cli/src/ui/AppContainer.tsx:482`
2. explicitly before listing sessions:
   - `packages/cli/src/utils/sessions.ts:20`

## Requirements checklist

- [ ] Implement Gemini-like live compaction behavior in this platform, informed by the sources below.
- [ ] Implement the separate previous-session one-line summary behavior or clearly document any intentional omission made during completion.
- [ ] Extract any Gemini/Qwen-shared logic into shared helpers only where parity remains clear.
- [ ] Preserve in documentation the exact separation between live compaction and prior-session summary.
- [ ] Preserve the compression prompt structure and the verification-pass request shape.
- [ ] Preserve the model-alias mapping behavior for live compaction.
- [ ] Preserve the distinct session-summary prompt and its `summarizer-default` model selection.
- [ ] Preserve the exact injection shape for live compaction: `user(summary)` then assistant acknowledgment then preserved tail.
- [ ] Preserve the note that no explicit persisted `chat_compression` checkpoint was confirmed in the inspected Gemini code.
