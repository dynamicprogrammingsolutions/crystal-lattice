# Kimi compaction parity product specification

## Purpose

A long Kimi-style conversation accumulates many user/assistant turns, tool
calls, and tool results. Compaction reduces the active history to a structured
summary while preserving the most recent turns verbatim, so the agent can
continue without losing the current task state, errors and solutions, code
evolution, system context, design decisions, and TODO items.

The `kimi-tools` plugin exposes manual compaction through two session actions:
`compact_conversation` (full or selected range) and `compact_up_to_here`
(message-anchored prefix). The compaction must match `kimi-cli`'s
`SimpleCompaction` closely enough that the same prompt, the same synthetic
single-message request shape, the same generic compactor system prompt, the
same tool suppression, and the same preserved-tail behavior are used.

## Users

### Package users

Package users need to:

- compact conversation history or a selected range into a summary;
- preserve the most recent user/assistant turns verbatim when compacting the
  full range;
- continue the conversation after compaction from the compacted session;
- override the compaction model when needed;
- supply custom focus instructions to the compaction prompt;
- see clear disabled, no-op, and error outcomes when compaction is not
  available or not applicable.

### Application clients

Application clients need one stable session action surface and do not need to
know that the compaction request is a single synthetic user message rather
than a normal multi-turn request.

## Target behavior

### Manual compaction invocation

The plugin exposes two session actions:

| Action | Selection | Preserved tail |
|---|---|---|
| `compact_conversation` | Full range or explicit `start`/`end` | Applied when no explicit `end` is supplied |
| `compact_up_to_here` | Prefix ending at an anchor message | Not applied (explicit `end`) |

When compaction is disabled for the agent, both actions are unavailable: UI
elements are omitted and execution returns an error with `type: "disabled"`.

### Compaction request

The compaction request is a single synthetic user message sent to the current
runtime LLM with a generic compactor system prompt and no tools. The
synthetic message flattens the compactable range into numbered blocks:

```text
## Message 1
Role: <role>
Content:
<text-only content>

## Message 2
Role: <role>
Content:
<text-only content>

...

<compaction prompt>
```

When the selected prefix begins with the agent's system message, that message
is included in the numbered transcript, matching `SimpleCompaction.prepare`.
It is still preserved as the leading system message in the platform's final
session.

Only text content is included. Structured tool-call and tool-result payloads,
media parts, and think parts are dropped. Text content is retained from every
message role, including textual tool messages.

### Compacted session

The compacted session replaces the compacted range with one user message
whose content is:

```text
<system>Previous context has been compacted. Here is the compaction output:</system>
<structured summary body>
```

The prompt requests `kimi-cli`'s required XML-style sections:
`<current_focus>`, `<environment>`, `<completed_tasks>`, `<active_issues>`,
`<code_state>`, and `<important_context>`. A non-empty response that does not
contain all sections is retained rather than rejected, matching `kimi-cli`.

No assistant acknowledgment message is added. No Claude-style
`local-command-caveat` artifact is added. Preserved-tail messages, if any,
follow the summary user message unchanged.

### Preserved tail

When no explicit `end` is supplied, the last `max_preserved_messages`
user/assistant messages (default 2) are preserved verbatim. If fewer than
`max_preserved_messages` user/assistant messages exist in the compactable
range, the action returns a no-op result instead of forcing compaction with
no preserved tail. `max_preserved_messages <= 0` also produces a no-op.

### Enablement

The plugin is active only when the agent's `compaction` config has:

```yaml
compaction:
  enabled: true
  type: "kimi"
```

When `config` is `None` (global endpoint enumeration), UI elements are
returned unconditionally so the action remains discoverable.

## Compatibility

### Previous plugin behavior

Earlier plugin versions sent the compaction prompt as a normal multi-turn
request with the agent's normal system message and normal tool schemas. The
compaction prompt included a "CRITICAL: TEXT ONLY" preamble and a trailing
"REMINDER" to discourage tool use. The compacted session used a plain-text
prefix without `<system>…</system>` wrapping.

Current target behavior replaces that with the `kimi-cli`-faithful shape: a
single synthetic user message, a generic compactor system prompt, no tools,
the exact `compact.md` prompt body, and `<system>…</system>`-wrapped summary
injection.

### Preserved behavior

- `compaction_model` continues to override the normal request model only for
  compaction. Agent configuration reads it from the `compaction` block; the
  existing session settings UI writes a top-level per-session
  `compaction_model` override that takes precedence.
- `settings_overrides` continues to merge into the compaction request config.
  It cannot override `disable_all_tools: true`.
- `prompt` continues to override the default compaction prompt body.
- Custom instructions continue to be appended to the compaction prompt.
- The `compact_up_to_here` message action continues to compact exactly the
  prefix up to the anchor message.

## Non-goals

- Auto-compaction triggered by token thresholds. This is tracked by task
  `20260315-gemini-qwen-grok-tool-packages/222-lifecycle-auto-compaction.md`.
- Checkpoint creation, context clear/rewrite, or D-Mail checkpoint-revert
  behavior. These are tracked by the checkpoint/D-Mail portion of task 240.
- A Claude-style pre-compaction transcript snapshot. The platform has no
  checkpoint mechanism and this correction does not add one.
- Cross-vendor shared compaction helpers. Task 250 addresses shared helpers.
- Redefining the platform's `disable_all_tools` tool-gating contract, the
  feature-plugin lifecycle, or session persistence.