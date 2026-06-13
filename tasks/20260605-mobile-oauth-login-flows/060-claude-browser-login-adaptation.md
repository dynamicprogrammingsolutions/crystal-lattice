# Claude Browser Login Adaptation
Reuse the Codex redirect-based browser-login architecture for Claude once the provider implementation exists in this repo.

## Requirements checklist

- [ ] Confirm the Claude OAuth provider behavior against the `pi` implementation and identify any provider-specific deviations.
- [ ] Reuse the Codex browser-login architecture wherever the protocol shape matches.
- [ ] Keep the Claude work aligned with the shared login-type selection UX and CLI command surface.
- [ ] Document any places where Claude must diverge from Codex.

Parent Task: `tasks/20260605-mobile-oauth-login-flows/000-main.md`
Depends On: Provider implementation work for Claude in this repo (no concrete task file assigned yet), `tasks/20260605-mobile-oauth-login-flows/050-complete-codex-browser-login-flow.md`

## Working reference in `pi`

Treat these files as source of truth for Claude behavior:

- `../pi/packages/ai/src/utils/oauth/anthropic.ts`
- `../pi/packages/ai/test/anthropic-oauth.test.ts`

High-level flow already discovered:

- Browser OAuth with PKCE.
- Local callback server in the CLI implementation.
- Manual pasted redirect fallback.
- Token exchange at Anthropic's token endpoint.

## Expected reuse from Codex work

- Same frontend redirect handling pattern if Claude accepts mobile-friendly redirects.
- Same start/complete action pattern.
- Same preference and selection UX pattern.
- Same CLI command-to-action pattern.

## Questions to answer during implementation

- Are Claude scopes or redirect restrictions materially different from Codex?
- Does Claude need different frontend copy or status handling?
- Can the same generic action payload shape be reused, or should provider-specific fields be isolated?