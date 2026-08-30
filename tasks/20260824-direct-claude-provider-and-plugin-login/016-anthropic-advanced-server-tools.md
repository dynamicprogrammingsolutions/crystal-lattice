# Anthropic Advanced Server Tools

Add selected Anthropic code execution, tool search, and programmatic
tool-calling capabilities through explicit provider extensions and application
boundaries.

## Requirements checklist

### Functional requirements

- [ ] Code execution can be enabled through an extension with explicit sandbox,
  file, result, and cancellation behavior.
- [ ] Tool search can expose large tool catalogs without injecting every schema
  into the initial prompt.
- [ ] Programmatic tool calling can execute supported multi-tool workflows
  while preserving tool results and application visibility.
- [ ] Server-tool content blocks and lifecycle events map into stable core
  metadata and displays.
- [ ] Capability discovery and compatible profiles control feature
  availability.

### Non-functional requirements

- [ ] Server-side execution is clearly distinguished from local Crystal
  Lattice tools.
- [ ] Remote sandbox files and results have explicit ownership, retention, and
  download policies.
- [ ] Provider-specific configuration, UI, enablement, and public metadata live
  in extensions.
- [ ] Compatible endpoints without the capabilities remain unaffected.
- [ ] Structured outputs are outside this task.

Parent Task:
`tasks/20260824-direct-claude-provider-and-plugin-login/000-main.md`

Depends On:

- `tasks/20260824-direct-claude-provider-and-plugin-login/010-direct-claude-provider-runtime.md`

Specification:

- `plugins/anthropic-compatible/docs/development/specifications/anthropic-provider/index.md`

## Execution plan

Status: Draft

Select and specify each advanced server capability before implementation.
Prefer separate extensions with shared provider-native server-tool event
mapping. Do not make remote execution appear equivalent to the local shell,
filesystem, or tool host.

### Implementation decisions and open questions

- Decision: web search and web fetch belong to subtask 011, not this task.
- Decision: structured outputs are not planned.
- Open: split code execution, tool search, and programmatic calling into
  separate subtasks if their security or lifecycle specifications diverge.

### Documentation

- Document execution location, data flow, retention, costs, capability gates,
  local-tool distinctions, and compatible-endpoint limitations.

### Task checklist

- [ ] Select the first advanced capability and extend the specification.
- [ ] Implement capability-specific extension/config/UI.
- [ ] Implement provider-native server-tool mapping.
- [ ] Add security, cancellation, and persistence tests.
- [ ] Add selective hosted tests.
- [ ] Document delivered behavior.

### Requirement verification

- Enabled server tools complete through real hosted requests with visible
  lifecycle and results.
- Disabled or unsupported profiles send no feature-specific fields.
- Local tools remain independently selectable and retain their established
  security boundaries.

### Additional implementation verification

- Remote files/results do not leak into unrelated sessions.
- Long-running server operations respect request cancellation.