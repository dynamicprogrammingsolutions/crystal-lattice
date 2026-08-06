# Decision: issue workspace-specific provider deploy keys

## Context

Cloud Git push needs provider authentication. Copying existing local SSH keys,
credential-helper stores, or broad personal tokens would expose credentials
with unrelated scope and unclear revocation.

GitHub and GitLab both support repository deploy keys that can be created and
removed through authenticated provider APIs. GitLab also supports expiration.

## Decision

- Credential transfer is explicit and opt-in.
- Generate a new Ed25519 keypair for each cloud workspace.
- Never read or transfer an existing local user private key.
- Register the public key as a writable deploy key for the primary repository
  through the source server's logged-in `gh` or `glab` session.
- Store the private key only in protected cloud workspace state.
- Track provider credential identity and lifecycle metadata without storing the
  private key in control records.
- Revoke or confirm absence/expiry of provider access before deleting cloud
  storage and revoking the connection.
- Preserve a stopped retryable deletion state when revocation fails.
- Require source credential-manager participation for guaranteed deletion in
  the first target.

## Consequences

Positive:

- Cloud access is isolated from existing local keys.
- Provider access has explicit workspace ownership and deletion semantics.
- Runtime restart can reuse the workspace credential.
- GitHub and GitLab share one provider-neutral lifecycle.

Costs:

- Initial support covers only the primary repository.
- Source-server availability is required for guaranteed revocation.
- GitHub deploy keys need explicit deletion because the initial target has no
  provider expiry backstop.
- Repository administration permission and protected-branch policy still
  apply.

Deferred alternatives:

- GitHub App installation tokens.
- GitLab project access tokens or OAuth credential brokers.
- Cloud-side deletion independent of the source credential manager.
- Credentials for private submodules and multiple repositories.
