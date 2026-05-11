# Investigate And Implement Claude Compaction

Determine Claude Code's compaction behavior and add Claude-compatible compaction support or a vendor-preset extension to the existing compaction plugins.

## Requirements checklist

- [ ] Investigate Claude Code compaction prompts/output format through behavior, if possible.
- [ ] Decide whether to create separate `claude-compaction-app` / `claude-compaction-feature` packages or generalize existing Gemini compaction plugins to vendor-specific prompt presets.
- [ ] Implement Claude-compatible compaction action support.
- [ ] Add unit and application integration tests for Claude compaction behavior.
- [ ] Wire Claude compaction into default config only when stable and opt-in semantics are clear.

Parent Task: tasks/20260504-claude-tools-parity/000-main.md

Depends On: tasks/20260504-claude-tools-parity/010-investigate-claude-code-behavior.md
Depends On: tasks/20260504-claude-tools-parity/030-implement-claude-system-message-and-config.md

## Existing State

Current compaction support is Gemini-shaped:

- `plugins/gemini-compaction-app`
- `plugins/gemini-compaction-feature`

The app plugin prompt asks for a structured XML `<state_snapshot>` with sections such as:

- `<overall_goal>`
- `<active_constraints>`
- `<key_knowledge>`
- `<artifact_trail>`
- `<file_system_state>`
- `<recent_actions>`
- `<task_state>`

The app plugin is configured per agent under:

```yaml
compaction:
  enabled: false
  type: "gemini"
  agent_id: null
  prompt: null
  settings_overrides: {}
  verification_pass: true
```

The feature plugin mirrors this with feature-level actions.

## Investigation Notes

Claude Code likely has its own compaction behavior, but this was not yet captured. Investigate via real Claude Code behavior because Claude Code is not open source.

Potential approaches:

- Trigger `/compact` in an interactive or scripted Claude Code session and proxy-log the internal request.
- Create a long context in print/stream-json mode and observe whether automatic compaction occurs.
- Search Claude Code local cache/debug logs for compaction-related request markers, but do not rely on code internals.

Capture:

- compaction prompt/system instructions
- output format expected from summarizer
- any acknowledgement message inserted into conversation history
- whether verification/self-critique pass exists
- whether tool outputs receive special handling

## Implementation Options

Option A: New packages

```text
plugins/claude-compaction-app
plugins/claude-compaction-feature
```

Option B: Generalize Gemini compaction packages

- Rename or extend conceptually to support `type: "gemini"` and `type: "claude"`.
- Keep backward compatibility for existing `type: "gemini"` configs.

Prefer the option that is smallest and least disruptive once behavior is known.
