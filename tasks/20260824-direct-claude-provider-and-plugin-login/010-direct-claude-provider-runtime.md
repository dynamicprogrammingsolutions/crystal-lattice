# Direct Claude Provider Runtime

Implement the direct Claude provider and its stable credential-consumption,
request, streaming, tool, and error contracts.

## Requirements checklist

### Functional requirements

- [ ] The provider supports ordinary message requests and streaming through
  the standard provider plugin interfaces.
- [ ] The provider consumes the approved Claude credential contract without
  reading frontend-specific state.
- [ ] Claude-compatible tool schemas, calls, results, reasoning, usage, and
  cancellation are mapped through existing application/core contracts.
- [ ] Provider configuration distinguishes direct Claude access from
  OpenRouter access.
- [ ] Authentication, rate-limit, provider, validation, and cancellation
  failures map to stable application-facing outcomes.

### Non-functional requirements

- [ ] Provider code does not embed login UI or credential-acquisition logic.
- [ ] Credential and authorization values are redacted from logs and errors.
- [ ] Direct-provider failures never silently fall back to OpenRouter.
- [ ] Provider behavior without optional tools/extensions remains compatible
  with the generic core pipeline.
- [ ] Deterministic unit/contract coverage precedes selective hosted tests.

Parent Task:
`tasks/20260824-direct-claude-provider-and-plugin-login/000-main.md`

## Open requirement questions

1. Which official API/transport surface is the authority for subscription
   OAuth requests if that credential mode is approved?
   - Resolve from verified provider behavior during planning; do not infer a
     private or unstable endpoint from UI traffic.

## Supporting facts

- No direct Anthropic/Claude provider plugin currently exists in the
  repository.
- Existing provider projects demonstrate streaming-first provider packaging,
  provider extensions, hosted test markers, and credential redaction.
- Claude-compatible tools currently run through OpenRouter and provider-neutral
  tool-loop interop.

## Execution plan

Status: Draft

Create a first-party provider project under `plugins/` using the current
provider-plugin package conventions. Define the minimal credential input and
configuration shape selected by the parent task, then implement native message
conversion, streaming, finalization, tool-call/result mapping, cancellation,
and error normalization.

Verify generic application usage before enabling Claude-specific extensions.
Run the existing Claude tool package through the direct provider and fix only
provider-boundary incompatibilities demonstrated by realistic tests.

### Implementation decisions and open questions

- Decision: the provider owns request transport and native mapping; the auth
  plugin owns obtaining and persisting credentials.
- Decision: provider identity is explicit in agent configuration.
- Open: choose official provider surface and supported initial models after
  credential-mode approval.

### Documentation

- Add provider README and user docs for installation, configuration, models,
  credentials, tools, errors, and hosted tests.
- Add provider development documentation for native mapping and test seams
  only if package complexity justifies it.

### Task checklist

- [ ] Confirm provider surface, models, and credential input.
- [ ] Create provider package and plugin metadata.
- [ ] Implement request, streaming, finalization, and cancellation.
- [ ] Implement native history and tool mapping.
- [ ] Add error and usage normalization.
- [ ] Add deterministic provider and application tests.
- [ ] Run selective hosted ordinary/tool request smokes.
- [ ] Document delivered behavior and limitations.

### Requirement verification

- Provider contract tests prove native conversion and streamed finalization.
- Application integration proves an ordinary and tool-enabled request.
- Cancellation and authentication failures produce expected events/results.
- Hosted smoke verifies the selected official provider surface.

### Additional implementation verification

- Multi-turn native history survives application persistence/reload.
- Tool-result payloads do not lose display or provider-native metadata.
- Rate-limit and usage data degrade safely when provider fields are absent.