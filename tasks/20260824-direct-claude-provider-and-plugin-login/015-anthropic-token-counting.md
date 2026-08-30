# Anthropic Token Counting

Add provider-authoritative token counting for request preflight, context
management, and user-visible estimates.

## Requirements checklist

### Functional requirements

- [ ] A provider or application action can count tokens for the effective
  system prompt, messages, tools, and supported attachments before generation.
- [ ] Token counts can inform context-window validation and compaction
  recommendations without sending a generation request.
- [ ] Count results distinguish authoritative provider values from local
  estimates.
- [ ] Model discovery supplies the applicable input-token limit when available.
- [ ] Compatible endpoints without token counting report the feature as
  unavailable and may use a clearly labeled local estimate.

### Non-functional requirements

- [ ] Token counting never mutates session history.
- [ ] Counting reuses normal request preparation so rendered system messages,
  tools, and attachments are represented consistently.
- [ ] Counts and estimates do not expose message or attachment content in logs.
- [ ] The feature remains independent from batch processing.

Parent Task:
`tasks/20260824-direct-claude-provider-and-plugin-login/000-main.md`

Depends On:

- `tasks/20260824-direct-claude-provider-and-plugin-login/010-direct-claude-provider-runtime.md`

Specification:

- `plugins/anthropic-compatible/docs/development/specifications/anthropic-provider/index.md`

## Execution plan

Status: Draft

Extend the package specification with token-count request preparation,
authority, and estimate-labeling rules. Prefer a reusable provider/application
action over embedding token-count side effects into ordinary requests.

### Implementation decisions and open questions

- Decision: batch processing is not a dependency or companion feature.
- Decision: provider counts are authoritative; estimates are visibly labeled.
- Open: decide which generic application surfaces should consume preflight
  counts for warnings or automatic compaction.

### Documentation

- Document supported endpoints, count inputs, authority, estimates, limits,
  cost, and compatible-endpoint behavior.

### Task checklist

- [ ] Extend the package specification and requirements.
- [ ] Implement effective-request token-count preparation.
- [ ] Implement token-count action and result contract.
- [ ] Add context-window warning/compaction integration as approved.
- [ ] Add deterministic and hosted tests.
- [ ] Add compatible-endpoint unavailable/estimate tests.
- [ ] Document delivered behavior.

### Requirement verification

- Hosted counts match the effective request structure.
- Count actions do not generate assistant messages or mutate history.
- Ollama reports token counting unavailable without breaking normal requests.

### Additional implementation verification

- Tool and attachment changes invalidate stale count displays.
- Context-limit comparisons use the selected discovered model.