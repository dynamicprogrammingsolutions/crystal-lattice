# Anthropic Fast Mode And Service Tiers

Add extension-owned Anthropic speed and service-tier controls with explicit
cost, retry, cache, and compatibility behavior.

## Requirements checklist

### Functional requirements

- [ ] `AnthropicFastModeExtension` owns fast-mode configuration, UI,
  enablement, request shaping, and public speed metadata.
- [ ] A service-tier extension or coherent fast-mode companion owns supported
  service-tier configuration, UI, request shaping, and public tier metadata.
- [ ] Model capabilities gate fast mode and exposed options.
- [ ] Usage metadata reports effective speed and service tier when returned.
- [ ] Fast-mode retries, fallback, timeout, and rate-limit behavior are
  deterministic and user-configurable through extension-owned settings.

### Non-functional requirements

- [ ] The feature is not called flex processing and does not imply an Anthropic
  equivalent to OpenAI synchronous Flex.
- [ ] Provider transport executes inseparable retry mechanics only from
  normalized extension state.
- [ ] Changing speed or tier does not reuse incompatible prompt-cache state.
- [ ] Compatible endpoints without the feature receive no speed or tier
  fields.

Parent Task:
`tasks/20260824-direct-claude-provider-and-plugin-login/000-main.md`

Depends On:

- `tasks/20260824-direct-claude-provider-and-plugin-login/010-direct-claude-provider-runtime.md`

Specification:

- `plugins/anthropic-compatible/docs/development/specifications/anthropic-provider/index.md`

## Execution plan

Status: Draft

Extend the package specification with explicit fast-mode and service-tier
contracts. Keep all user-facing configuration and public metadata in
extensions while exposing only the narrow provider request/retry hooks needed
by the active transport.

### Implementation decisions and open questions

- Decision: fast mode and service tiers are separate concepts even if one
  package refinement covers both.
- Decision: unsupported options are hidden or rejected before transport.
- Open: decide whether service-tier configuration needs a separate extension
  class after inspecting the final API and usage overlap.

### Documentation

- Document cost, eligibility, compatibility, fallback, retry, cache, and usage
  behavior.
- Update the package specification and requirements before implementation.

### Task checklist

- [ ] Extend the package specification and requirements.
- [ ] Implement capability-gated fast-mode configuration and UI.
- [ ] Implement service-tier configuration and UI.
- [ ] Add provider transport hooks for retry/fallback behavior.
- [ ] Add usage speed/tier metadata.
- [ ] Add deterministic and hosted tests.
- [ ] Document delivered behavior.

### Requirement verification

- Supported hosted models report effective speed/tier metadata.
- Disabled or unsupported configurations send no feature-specific fields.
- Retry/fallback tests prove extension settings control provider mechanics.

### Additional implementation verification

- Cache behavior remains correct when speed changes.
- Rate-limit failures retain stable retryability and request identifiers.