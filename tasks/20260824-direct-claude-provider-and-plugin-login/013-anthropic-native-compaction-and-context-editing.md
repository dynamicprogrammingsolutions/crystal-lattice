# Anthropic Native Compaction And Context Editing

Add provider-native compaction and context editing without replacing generic
prompt-based summarization in other providers.

## Requirements checklist

### Functional requirements

- [ ] `AnthropicCompactionExtension` owns compaction configuration, UI,
  enablement, native block mapping, and session actions.
- [ ] Server-side compaction blocks are preserved in canonical native history
  and reused on subsequent requests.
- [ ] Users can compact full history or a supported visible prefix and continue
  the conversation.
- [ ] Context editing can clear supported stale tool results or other eligible
  context according to explicit policy.
- [ ] Background compaction supports progress, cancellation, conflict
  detection, and reconciled persistence where operation duration justifies it.

### Non-functional requirements

- [ ] Native compaction does not redefine or replace provider-independent
  prompt summarization.
- [ ] A late or cancelled result cannot overwrite newer session history.
- [ ] Visible transcript projections do not become the canonical continuation
  state.
- [ ] Compatible endpoints without compaction support omit the feature.

Parent Task:
`tasks/20260824-direct-claude-provider-and-plugin-login/000-main.md`

Depends On:

- `tasks/20260824-direct-claude-provider-and-plugin-login/010-direct-claude-provider-runtime.md`

Specification:

- `plugins/anthropic-compatible/docs/development/specifications/anthropic-provider/index.md`

## Execution plan

Status: Draft

Create a package-specification refinement before implementation. Reuse the
application operation, notification, cancellation, and reconciled persistence
contracts proven by OpenAI Responses native compaction, while keeping the
Anthropic native protocol and transcript projection package-owned.

### Implementation decisions and open questions

- Decision: provider-native history remains canonical.
- Decision: compaction and context editing are opt-in.
- Open: determine whether synchronous compatibility actions are useful or
  whether only an application-owned background action should ship.

### Documentation

- Document trigger thresholds, selection, context-editing policies, transcript
  projections, cancellation, compatibility, and failure behavior.
- Add a dedicated package specification refinement if implementation scope
  exceeds the baseline specification cleanly.

### Task checklist

- [ ] Define the compaction/context-editing specification refinement.
- [ ] Implement native compaction request and stream mapping.
- [ ] Implement context-editing policies.
- [ ] Implement session action and background lifecycle.
- [ ] Add cancellation, conflict, and reload behavior.
- [ ] Add deterministic and hosted continuation tests.
- [ ] Document delivered behavior.

### Requirement verification

- A compacted session continues through a real follow-up request.
- Cancellation and concurrent changes prevent stale compaction commits.
- Compatible endpoints without support remain unaffected.

### Additional implementation verification

- Native compaction blocks survive persistence/reload.
- Tool IDs, thinking signatures, and cache state remain valid after compaction.