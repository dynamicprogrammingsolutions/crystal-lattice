# Kimi compaction parity technical specification

## Architecture

The compaction feature is a `FeaturePlugin` that contributes a session
action. Execution flows through four cooperating layers:

```text
Feature action (execute_action)
  enablement check, range resolution, preserved-tail scan,
  synthetic message construction, compacted session assembly

AgentCore
  rebuild_native_history, slice_session, add_message,
  send_request_stream for the internal compaction request

ToolGatingFeature
  disable_all_tools: True suppresses tool schemas in the request payload

Provider
  receives [system: generic compactor, user: synthetic message] and
  returns the structured summary text
```

The feature action returns replacement `native_messages` to the application,
which persists the rebuilt session. The compacted session has correct native
history for any provider, not just OpenAI chat-completions.

## Reference sources

All `kimi-cli` paths are relative to `../kimi-cli`, commit `7ba9695`.

- `src/kimi_cli/soul/compaction.py:103-189` — `SimpleCompaction` with
  `prepare` and `compact`.
- `src/kimi_cli/soul/compaction.py:117-122` — `kosong.step` call with
  `system_prompt="You are a helpful assistant that compacts conversation
  context."` and `toolset=EmptyToolset()`.
- `src/kimi_cli/soul/compaction.py:130-139` — output injection with
  `system(...)` prefix and preserved tail.
- `src/kimi_cli/soul/compaction.py:145-189` — `prepare` with backward scan
  for `max_preserved_messages` and `## Message N` block construction.
- `src/kimi_cli/soul/message.py:19-20` — `system(message)` wraps as
  `<system>{message}</system>`.
- `src/kimi_cli/prompts/compact.md:1-74` — exact compaction prompt body.
- `src/kimi_cli/tests/core/test_simple_compaction.py:44-77` — upstream test
  confirming `## Message N` block format and preserved tail.
- `src/kimi_cli/tests/core/test_simple_compaction.py:218-277` — upstream
  tests confirming text-only filtering and media preservation in the tail.

## Request shape

The compaction request session contains exactly two messages:

1. `system`: `"You are a helpful assistant that compacts conversation
   context."`
2. `user`: a single synthetic message built from the compactable range.

The synthetic user message content is the concatenation of, for each
compactable message in order:

```text
## Message N
Role: <role>
Content:
<text-only content of the message>
```

followed by `\n<compaction prompt>` and, if custom instructions are supplied,
the custom-instruction block appended in the same text block.

The generic compactor system prompt is the request session's outer `system`
message. When the selected conversation prefix begins with the agent's normal
system message, that original message is also included as the first numbered
block inside the synthetic `user` message. This matches the upstream
`test_prepare_builds_compact_message_and_preserves_tail` contract.

The original leading system message is not included in `compact_indices`, so
the platform preserves it in the final session. Request inclusion and final
session deletion therefore use distinct index sets.

### Text-only filtering

Only text content is included in the synthetic message:

- `str` content is included verbatim.
- Multipart content: only parts with `type == "text"` are included; their
  `text` field is concatenated.
- Structured tool-call and tool-result fields, media parts
  (image/audio/video URL parts), and think parts are dropped.
- Text content from every message role, including a tool-role message, is
  retained.

This matches `kimi-cli`'s whitelist approach
(`src/kimi_cli/tests/core/test_simple_compaction.py:218-249`).

## Tool suppression

The merged compaction request config applies `settings_overrides` and
`compaction_model`, then sets `disable_all_tools: True`. A
`settings_overrides.disable_all_tools: false` value cannot re-enable tools.

The platform's `ToolGatingFeature`
(`core/python/plugins/tool_gating_feature.py`) honors this flag by returning
an empty tool schema list from `prepare_tools`, so no tools are serialized
into the request payload.

This matches `kimi-cli`'s `toolset=EmptyToolset()` at
`src/kimi_cli/soul/compaction.py:120`.

## Preserved tail

When no explicit `end` is supplied to the action:

1. Read `max_preserved_messages` from `compaction.max_preserved_messages`
   (default `2`).
2. Scan backward from the end of the compactable range for the last
   `max_preserved_messages` messages with role `user` or `assistant`.
3. If fewer than `max_preserved_messages` such messages are found, return a
   no-op result (no compaction performed).
4. If `max_preserved_messages <= 0`, return a no-op result, matching
   `SimpleCompaction.prepare`.
5. Otherwise, compact only messages before the boundary; preserve messages
   from the boundary onward verbatim in the compacted session.

When an explicit `end` is supplied, preserved-tail does not apply; the
selected range is compacted exactly. This includes the `compact_up_to_here`
message action, which supplies an explicit `end`.

This matches `kimi-cli`'s `SimpleCompaction.prepare` backward scan at
`src/kimi_cli/soul/compaction.py:151-159`, with the explicit-range carve-out
documented as a decision below.

## Summary injection shape

The compacted session's summary user message content is:

```text
<system>Previous context has been compacted. Here is the compaction output:</system>
<summary body>
```

where `<summary body>` is the model's structured output (the
`<current_focus>…</important_context>` sections). The compacted session is
then:

```text
[leading system message(s) preserved]
[user: <system>…</system>\n<summary body>]
[preserved tail messages, if any]
```

No assistant acknowledgment message is added. No Claude-style
`local-command-caveat` artifact is added.

This matches `kimi-cli`'s `system(...)` wrapping at
`src/kimi_cli/soul/compaction.py:130-137` and `src/kimi_cli/soul/message.py:19-20`.

## Prompt body

The compaction prompt is the exact content of
`kimi-cli/src/kimi_cli/prompts/compact.md` (lines 1-74). The local
"CRITICAL: TEXT ONLY" preamble and trailing "REMINDER" text are removed;
with `disable_all_tools: True`, those guards are unnecessary.

Custom instructions are appended in the same text block as the prompt,
matching `kimi-cli`'s custom-instruction block at
`src/kimi_cli/soul/compaction.py:181-187`.

## Enablement

The plugin is active only when the agent's `compaction` config has
`enabled: true` and `type: "kimi"`. The enablement check uses the flattened
`base_config` from `build_agent_config()`, so `compaction` is read at the
root level, not nested under `agent`.

When `config` is provided to `get_ui_elements` and compaction is not enabled,
`get_ui_elements` returns `[]`. When `execute_action` is called and
compaction is not enabled, it returns an error with `type: "disabled"`.

When `config` is `None` (global endpoint enumeration), UI elements are
returned unconditionally, matching Gemini's behavior at
`plugins/gemini-compaction-feature/src/gemini_compaction_feature/__init__.py:490`.

## Configuration

```yaml
compaction:
  enabled: true              # required
  type: "kimi"               # required
  max_preserved_messages: 2  # optional, default 2
  compaction_model: null     # optional, overrides the request model
  prompt: null               # optional, overrides the compaction prompt
  settings_overrides: {}     # optional, merged into the compaction request config
```

`max_preserved_messages`, `compaction_model`, `prompt`, and
`settings_overrides` are read from the `compaction` block via a
`_get_compaction_config` helper matching Gemini's pattern.

The configuration UI's `compaction_model` element predates the nested agent
block and stores a top-level per-session override. Execution resolves that
effective request value after reading the agent block, so the UI value takes
precedence without moving the other settings out of `compaction`.

## Decisions

Five material decisions were raised during investigation and resolved on
2026-08-16. They are recorded here because each affects a public contract,
ownership boundary, or user-visible behavior likely to outlive the
implementation task.

### Decision 1: Remove Claude-shaped helpers

**Choice.** Remove `build_compaction_session` and
`build_compaction_request_session` and rewrite tests against a new
`build_kimi_compaction_request_session` builder.

**Alternatives considered.** Keep the Claude-shaped helpers as internal
utilities and only change the request path used by `execute_action`.

**Rationale.** Keeping Claude-shaped helpers in a Kimi plugin invites future
drift. The helpers are internal utilities with no external consumers; the
tests are the only callers besides `execute_action` itself. A single
Kimi-shaped builder is easier to reason about and test.

### Decision 2: Preserved tail applies only when no explicit end

**Choice.** Apply preserved-tail only when no explicit `end` is supplied.
When `end` is supplied (including `compact_up_to_here`), compact exactly the
selected range.

**Alternatives considered.** Always apply preserved-tail, matching
`kimi-cli`'s `/compact` which has no explicit-range selector.

**Rationale.** `kimi-cli`'s `/compact` always preserves the last two
messages, but its CLI does not expose an explicit range selector. Our
`compact_up_to_here` message action is an explicit range that may end before
the last two messages; forcing preserved-tail there would surprise the user
by preserving messages outside the selected range. The full-range
`compact_conversation` action is the path that should match `kimi-cli`
faithfully.

### Decision 3: `max_preserved_messages` lives under `compaction`

**Choice.** Read `max_preserved_messages` from
`compaction.max_preserved_messages` via `_get_compaction_config`, default
`2`.

**Alternatives considered.** Expose it at the top level of the feature
plugin's config schema, separate from the `compaction` block.

**Rationale.** The class docstring already documents it under `compaction`.
Co-locating it with `compaction.enabled`, `compaction.type`,
`compaction.prompt`, and `compaction.settings_overrides` keeps all
compaction configuration in one block, matching Gemini's pattern.

### Decision 4: Auto-compaction is out of scope

**Choice.** Leave auto-compaction to task 222. This correction is
manual-action parity only.

**Alternatives considered.** Implement Kimi-only auto-compaction in this
correction, using `kimi-cli`'s `should_auto_compact` threshold logic
(`trigger_ratio=0.85`, `reserved_context_size=50_000`).

**Rationale.** Task 222 is the cross-vendor lifecycle auto-compaction task.
Implementing Kimi-only auto-compaction here would create a second
implementation pattern that task 222 would then have to reconcile. The
manual action is the parity gap that matters now; auto-compaction is a
separate concern with its own threshold logic, token accounting, and
lifecycle hooks.

### Decision 5: Checkpoint/context rewrite is an intentional deviation

**Choice.** Document the deviation. Do not add a checkpoint mechanism or a
Claude-style pre-compaction transcript snapshot in this correction.

**Alternatives considered.** Replicate `kimi-cli`'s
clear/rewrite/checkpoint/append flow, or add a Claude-style pre-compaction
transcript snapshot.

**Rationale.** The platform has no checkpoint mechanism, and adding one is a
cross-vendor concern that belongs with task 240's checkpoint/D-Mail portion,
not with this manual-compaction correction. The platform's existing
`core.slice_session` + `core.add_message` path produces a correct compacted
session with rebuilt native history; it just does not create a checkpoint or
rewrite the system prompt the way `kimi-cli` does. The user-visible
compaction result is equivalent; the internal context-management mechanics
differ.

## Deviations from kimi-cli

### Checkpoint and context rewrite

`kimi-cli`'s `compact_context` (`src/kimi_cli/soul/kimisoul.py:732-774`)
clears the context, rewrites the system prompt, creates a checkpoint,
appends the compacted messages, and updates the estimated token count. The
local implementation does not replicate this. It uses the platform's
`core.slice_session` + `core.add_message` APIs to produce a compacted
session with rebuilt native history, which the application then persists.
There is no checkpoint creation, no context clear, and no system prompt
rewrite beyond the compaction request itself.

This is an intentional deviation (Decision 5). The platform has no
checkpoint mechanism, and adding one is out of scope for this correction.

### Auto-compaction

`kimi-cli` auto-compacts at 85% context usage or when only 50,000 tokens
remain (`src/kimi_cli/soul/compaction.py:56-72`,
`src/kimi_cli/config.py:81,85`). The local implementation does not
auto-compact. This is an intentional deviation (Decision 4) tracked by task
222.

### D-Mail and checkpoint revert

`kimi-cli` has a D-Mail tool that reverts to a previous checkpoint and
appends a message from the agent's future self. The local implementation
does not replicate this. It is out of scope and tracked by task 240's
checkpoint/D-Mail portion.

## Verification

### Unit tests

`plugins/kimi-tools/tests/test_kimi_compaction_feature.py` must cover:

- Synthetic single-user-message format with `## Message N\nRole: …\nContent:`
  blocks.
- Text-only filtering (multipart content with text + image + think).
- Leading agent system message included in the numbered synthetic transcript
  while remaining preserved in the final platform session.
- Textual tool-message content retained while structured tool-result data is
  omitted.
- Generic compactor system prompt as the leading request message.
- `disable_all_tools: True` in the merged request config.
- `settings_overrides` cannot re-enable tools.
- Preserved-tail boundary with default `max_preserved_messages=2`.
- No-op result when fewer than `max_preserved_messages` user/assistant
  messages exist.
- No-op result when `max_preserved_messages <= 0`.
- `<system>…</system>` prefix wrap in `build_compact_summary_text`.
- Exact prompt body match against `compact.md`.
- Custom-instruction append in the same text block as the prompt.
- Enablement UI gating (empty elements when disabled).
- Enablement execute gating (`error.type == "disabled"`).
- Config reading from the `compaction` block.
- Top-level per-session `compaction_model` UI override precedence.

### Integration tests

`plugins/kimi-tools/tests/test_kimi_compaction_feature_ollama_integration.py`
must continue to pass with the new request shape and enablement enforcement.

### Lint and format

`ruff check plugins/kimi-tools/src plugins/kimi-tools/tests` and
`black plugins/kimi-tools/src plugins/kimi-tools/tests` must pass clean.