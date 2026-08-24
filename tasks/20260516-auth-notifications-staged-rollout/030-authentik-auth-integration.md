# Stage 3: Authentik Authentication Integration

Add authentik-based login and identity-aware authorization on top of the existing pairing-first notification and bridge design, without forcing a redesign of notification delivery.

SUPERSEDED BY:
`tasks/20260824-os-level-notification-delivery/020-community-authentik-bridge-identity.md`
and its public modular bridge dependencies.

## Requirements checklist

- [ ] Define the authentik deployment and subdomain layout.
- [ ] Define mobile and terminal/login clients, token lifetimes, and validation strategy.
- [ ] Add authentik-backed login to the mobile app and server-side flows.
- [ ] Update bridge and cloud authorization to validate authentik-issued tokens.
- [ ] Keep notification delivery decoupled from auth so pairing-based delivery can coexist during migration.
- [ ] Document required secrets, keys, Google social-login setup, and deployment steps.
- [ ] Keep authentik integration optional so pairing-only and self-hosted minimal deployments remain supported.

Parent Task: `tasks/20260516-auth-notifications-staged-rollout/000-main.md`
Depends On: `tasks/20260516-auth-notifications-staged-rollout/010-local-notification-polling.md`
Depends On: `tasks/20260516-auth-notifications-staged-rollout/020-bridge-push-delivery.md`

## Stage intent

This stage adds a real identity layer using authentik while preserving the notification model built earlier. Notification storage and push delivery should already work before login is introduced.

This stage must remain additive:

- bridge deployments without authentik should still be possible
- pairing-only operation should still work unless a self-hoster explicitly opts into auth-required behavior
- missing authentik configuration should disable auth features gracefully rather than breaking the base bridge path

## Decisions captured from research

- Authentik is the preferred self-hosted auth choice for this repo because it provides a full self-hosted IdP, social login support, OIDC/OAuth2 flows, and an admin UI with less custom auth work than a code-first auth core.
- Google should be the upstream login source for users, but the apps and services should trust authentik tokens, not Google tokens directly.
- Mobile and terminal/server should use OIDC Authorization Code + PKCE as public clients.
- Bridge and cloud should validate authentik-issued JWTs statelessly using OIDC discovery and JWKS.
- Auth should become an additional verification and authorization model on top of pairing, not a prerequisite for delivering notifications.

## Current code references

- Bridge pairing/session behavior today:
  - `bridge-elixir/lib/bridge/app_channel.ex:64-180`
  - `bridge-elixir/lib/bridge/server_channel.ex:11-42`
- Cloud orchestrator current auth model:
  - `cloud-orchestrator/lib/cloud_orchestrator/router.ex:18-209`
- Mobile bridge connection persistence still revolves around `pairingToken` today:
  - `mobile/crystal-lattice-control-rn/App.tsx:114-130`
  - `mobile/crystal-lattice-control-rn/App.tsx:740-760`
  - `mobile/crystal-lattice-control-rn/App.tsx:1187-1210`

## Recommended deployment shape

Suggested subdomains:

- `auth.example.com`
- `bridge.example.com`
- `cloud.example.com`

Suggested authentik deployment components:

- authentik server
- authentik worker
- PostgreSQL
- Redis
- reverse proxy / TLS

Suggested future trust relationships:

- Mobile app trusts authentik as OIDC provider.
- Terminal/server trusts authentik as OIDC provider.
- Bridge validates authentik JWTs using JWKS.
- Cloud orchestrator validates authentik JWTs using JWKS.
- Google only acts as the upstream social-login provider for authentik.

## Ordered implementation steps

1. Deploy authentik in a test environment.
2. Configure Google as a social-login source in authentik.
3. Create authentik applications/providers for:
   - mobile app
   - terminal/server login
   - optional future machine-to-machine or admin clients
4. Add login flows to mobile and terminal/server.
5. Add JWT validation to bridge and cloud.
6. Introduce identity-aware server ownership and visibility rules.
7. Migrate pairing-only flows into pairing-plus-identity flows where helpful.

## Manual vs CLI / agent steps

### Authentik infrastructure deployment

- [Manual or CLI] Provision a host or Kubernetes environment for authentik.
- [Agent/CLI] Deploy authentik with Docker Compose or Helm once the target environment is chosen.
- [Agent/CLI] Deploy PostgreSQL and Redis or point authentik at managed instances.
- [Manual] Create DNS records and TLS certificates for `auth.example.com`.
- [Agent/CLI] Wire environment variables and secrets into the deployment.

### Google social-login setup for authentik

- [Manual-preferred] Create a Google OAuth client for authentik in Google Cloud Console.
- [Manual] Set the Google OAuth redirect URI expected by authentik.
- [Manual] Copy Google OAuth client ID and client secret into authentik.
- [Agent/CLI] Document and, where practical, script the resulting authentik configuration after the credentials exist.

### Authentik application/provider setup

- [Manual or CLI] Create public OIDC clients for the mobile app and terminal/server.
- [Manual] Choose redirect URIs:
  - mobile custom URI scheme or universal/app link
  - terminal/server loopback callback
- [Manual or CLI] Configure token lifetimes, scopes, refresh tokens, and signing keys.
- [Agent/CLI] Export deployment configuration or infra code if the team wants the setup reproducible.

### Bridge and cloud integration

- [Agent/CLI] Add OIDC discovery and JWKS-based JWT validation.
- [Agent/CLI] Bind bridge server visibility and cloud access to claims such as `sub`, `email`, and groups if used.
- [Manual] Decide policy semantics:
  - user-owned servers only
  - optional sharing
  - optional organization/group visibility

### Secret placement

- [Manual] Store authentik secret material in secure secret storage.
- [Manual] Store Google client secret only on authentik, not on bridge or cloud.
- [Manual] Store TLS private keys on the hosts that terminate TLS.
- [Agent/CLI] Configure bridge and cloud with issuer/JWKS settings rather than sharing authentik private keys.

## Specific secret and key inventory

### On authentik hosts

- `AUTHENTIK_SECRET_KEY`
- PostgreSQL credentials
- Redis credentials
- authentik signing keys / certificates
- Google OAuth client ID
- Google OAuth client secret
- TLS cert/private key if terminating TLS there

### On bridge hosts

- issuer / discovery URL for authentik
- JWKS cache or fetch configuration
- no Google secret
- preferably no authentik client secret for routine JWT validation
- FCM credentials from Stage 2 if push is enabled

### On cloud hosts

- issuer / discovery URL for authentik
- JWKS cache or fetch configuration
- no Google secret
- internal orchestrator token-signing secret if that remains part of the design

### On mobile / terminal clients

- public `client_id`
- no client secret for PKCE public clients
- secure local storage for refresh tokens and app session state

## Migration notes

- Keep pairing available at first for continuity.
- Add identity-aware ownership gradually.
- Avoid rewriting the notification model when auth lands.
- Push-token registration should evolve from pairing-scoped to identity-scoped or hybrid-scoped records over time.
- Treat authentik as an optional enhancement path, not a mandatory prerequisite for using the open source bridge.

## Recommended human docs for this stage

- `tasks/20260516-auth-notifications-staged-rollout/docs/authentik-auth-concepts.md`
