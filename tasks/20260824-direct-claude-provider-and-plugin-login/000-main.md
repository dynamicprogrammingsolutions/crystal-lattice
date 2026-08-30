# Anthropic-Compatible Provider And Plugin-Driven OAuth

Deliver an Anthropic-compatible provider path and plugin-owned OAuth lifecycle
that work consistently from mobile, desktop, top-level CLI, and the interactive
terminal while preserving the existing OpenRouter Claude option.

## Requirements checklist

### Functional requirements

- [ ] The `anthropic` provider can execute ordinary and tool-enabled requests
  against the official Anthropic API and supported Anthropic-compatible
  endpoints without routing through OpenRouter.
- [ ] API-key authentication uses the resolved provider configuration as its
  primary credential input.
- [ ] A separate Anthropic OAuth application plugin exposes login, status,
  cancellation, refresh, and logout actions.
- [ ] Saved OAuth credentials are directly usable by the provider through one
  documented credential contract.
- [ ] Mobile and desktop expose the Anthropic OAuth actions through the
  standard application/session action UI.
- [ ] Anthropic OAuth works through plugin-contributed top-level and
  interactive terminal commands.
- [ ] Missing, expired, revoked, cancelled, and invalid authentication states
  produce actionable plugin-owned results.
- [ ] Existing `claude-tools` work with the direct provider.
- [ ] Existing OpenRouter-based Claude agents remain available and are not
  silently replaced.
- [ ] Provider-specific follow-ups add server web tools, fast mode and service
  tiers, native compaction, files/PDFs, token counting, and advanced server
  tools without bloating the baseline provider.

### Non-functional requirements

- [ ] Credentials use configurable secure persistence and are excluded from
  ordinary logs, notifications, session records, and diagnostics.
- [ ] Direct-provider selection and fallback behavior are explicit and do not
  silently route a failed request through another paid provider.
- [ ] OAuth state, PKCE, refresh, supersession, and cancellation are safe.
- [ ] Anthropic-specific behavior remains in provider/auth plugins rather than
  generic application, terminal, or frontend code.
- [ ] Deterministic provider/auth tests, local Ollama compatibility tests, and
  selective hosted verification cover the supported credential modes and tool
  loop.
- [ ] Public documentation distinguishes direct Anthropic access,
  Anthropic-compatible endpoints, and OpenRouter-hosted Claude access.
- [ ] Batch processing and structured outputs are outside this task group.

## Open requirement questions

1. Should the direct Anthropic provider become a new default agent or remain an
   explicitly selected configuration?
   - Recommendation: keep the existing OpenRouter Claude default until API-key
     and OAuth requests, credential refresh, tool behavior, and hosted smoke
     evidence are complete.

## Subtasks

- [ ] `tasks/20260824-direct-claude-provider-and-plugin-login/010-direct-claude-provider-runtime.md`
- [ ] `tasks/20260824-direct-claude-provider-and-plugin-login/011-anthropic-server-web-tools.md`
- [ ] `tasks/20260824-direct-claude-provider-and-plugin-login/012-anthropic-fast-mode-and-service-tiers.md`
- [ ] `tasks/20260824-direct-claude-provider-and-plugin-login/013-anthropic-native-compaction-and-context-editing.md`
- [ ] `tasks/20260824-direct-claude-provider-and-plugin-login/014-anthropic-files-pdfs-and-citations.md`
- [ ] `tasks/20260824-direct-claude-provider-and-plugin-login/015-anthropic-token-counting.md`
- [ ] `tasks/20260824-direct-claude-provider-and-plugin-login/016-anthropic-advanced-server-tools.md`
- [ ] `tasks/20260824-direct-claude-provider-and-plugin-login/020-claude-authentication-plugin.md`
- [ ] `tasks/20260824-direct-claude-provider-and-plugin-login/030-claude-client-and-terminal-integration.md`

## Workstreams

- Baseline provider delivery: subtask 010.
- Provider-specific follow-ups: subtasks 011 through 016; each depends on 010
  but is not a prerequisite for OAuth.
- OAuth lifecycle: subtask 020.
- Client and terminal integration: subtask 030.

## Supporting facts

- The current default `claude` agent uses the OpenRouter provider with an
  Anthropic model slug.
- `plugins/claude-tools` provides Claude-compatible tools and compaction but
  does not implement a direct Anthropic provider or Anthropic OAuth.
- The existing ChatGPT auth application plugin demonstrates background login,
  saved credentials, status, cancellation, logout, and provider consumption.
- The local `../pi` repository contains an Anthropic Messages implementation,
  compatibility controls, and an OAuth flow that will be used as a protocol
  and behavior reference.
- Generic action deep links and action-dialog selection already exist.
- Plugin-driven terminal commands are tracked separately so the provider task
  does not add another command framework.

## Execution plan

Status: Draft

Implement the work through independently reviewable provider, feature, OAuth,
and client stages. Establish the API-key provider and compatibility contract
first. Add provider-specific features as separate subtasks. Implement OAuth
against the provider credential contract, then expose the shared actions
through terminal and React Native frontends.

Do not change the default Claude agent until the direct provider, OAuth
refresh, tool behavior, and hosted smoke evidence are complete. Stop for user
review if the inspected OAuth behavior requires undocumented credential
extraction, imitation of private clients beyond the approved `pi` reference,
or materially different security boundaries.

### Implementation decisions and open questions

- Decision: the baseline credential mode is API-key authentication from
  resolved config, normally `${env:ANTHROPIC_API_KEY}`.
- Decision: subscription OAuth is implemented by subtask 020 using the local
  `../pi` implementation as the primary behavior reference and verified
  provider behavior as the protocol authority.
- Decision: provider transport and authentication UI are separate plugins
  joined by a documented credential contract.
- Decision: the package is named Anthropic-compatible, while runtime provider
  and class names use the shorter `anthropic` form.
- Decision: `claude-tools` remains provider-independent where its current
  interop contract permits.
- Decision: OpenRouter remains a supported explicit alternative.
- Decision: batch processing and structured outputs are not planned.
- Open: decide whether and when direct Anthropic becomes a default agent.

### Documentation

- Maintain the package-owned Anthropic provider specification under
  `plugins/anthropic-compatible/docs/development/specifications/anthropic-provider/`.
- Maintain the portable provider target under
  `docs/development/specifications/portable-provider-implementation/`.
- Maintain the current public authoring standard under
  `plugins/docs/provider-implementation-standard/`.
- Add provider installation, configuration, credential, model, compatibility,
  tool, and troubleshooting documentation when implementation is delivered.
- Add Anthropic OAuth login, status, logout, storage, and callback
  documentation with subtask 020.
- Update default-agent and terminal/mobile guidance only when behavior is
  delivered.

### Task checklist

- [x] Resolve the baseline credential mode and provider/package naming.
- [x] Define the package-owned and portable specification structures.
- [ ] Execute and verify direct provider runtime subtask 010.
- [ ] Execute selected provider-feature subtasks 011 through 016.
- [ ] Execute and verify OAuth authentication subtask 020.
- [ ] Execute and verify frontend/terminal integration subtask 030.
- [ ] Run selective local-compatible, real-provider, and saved-login smoke
  tests.
- [ ] Reconcile documentation and requirement evidence.
- [ ] Record whether and when the default Claude agent should change.

### Requirement verification

- A direct Anthropic request and a tool-enabled request complete using API-key
  configuration.
- The same baseline provider supports the documented subset through local
  Ollama's Anthropic-compatible API.
- OAuth login/status/logout and credential refresh behave consistently across
  application actions and terminal bindings.
- Mobile and desktop can complete the supported OAuth flow and use the saved
  credential on a subsequent provider request.
- OpenRouter Claude behavior remains available and unchanged unless explicitly
  selected otherwise.

### Additional implementation verification

- Revoked or expired credentials cannot fall through to an unintended
  provider.
- Concurrent login attempts and provider requests have deterministic
  supersession behavior.
- Credential files and diagnostics contain no unnecessary provider response or
  account data.
- Unsupported compatible-endpoint features are omitted or reported explicitly
  rather than inferred from model names or silently ignored.