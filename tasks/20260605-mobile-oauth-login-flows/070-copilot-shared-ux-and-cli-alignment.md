# Copilot Shared UX And CLI Alignment
Apply the shared login selection, status, and CLI/action patterns to Copilot where appropriate, while keeping Copilot's provider-specific device-code flow intact.

## Requirements checklist

- [ ] Confirm Copilot's provider behavior against the `pi` implementation and preserve its device-code nature.
- [ ] Reuse the shared login selection UX where it makes sense without forcing a redirect-based callback flow.
- [ ] Reuse the CLI command and action architecture from the Codex work.
- [ ] Document the UX and implementation differences between redirect-based providers and device-code providers.

Parent Task: `tasks/20260605-mobile-oauth-login-flows/000-main.md`
Depends On: Provider implementation work for Copilot in this repo (no concrete task file assigned yet), `tasks/20260605-mobile-oauth-login-flows/020-auth-ux-and-framework-capability-audit.md`, `tasks/20260605-mobile-oauth-login-flows/030-cli-login-commands-via-plugin-actions.md`

## Working reference in `pi`

Treat these files as source of truth for Copilot behavior:

- `../pi/packages/ai/src/utils/oauth/github-copilot.ts`
- `../pi/packages/ai/test/github-copilot-oauth.test.ts`

High-level flow already discovered:

- Copilot uses GitHub device-code auth.
- There is no mobile app redirect callback to capture.
- After GitHub device auth succeeds, Copilot-specific token retrieval and model-enablement steps continue.

## Scope note

This task is intentionally not "make Copilot look identical to Codex/Claude internally."

The reusable parts are:

- action-driven auth surface
- login-type selection UX if more than one provider path exists
- status/check/cancel/logout conventions
- CLI command bindings to plugin actions

The non-reusable part is the redirect-based mobile callback path.

## Expected output

- Copilot integrated into the shared auth UX model where appropriate.
- A clear, explicit distinction between:
  - redirect-based browser OAuth providers
  - device-code providers