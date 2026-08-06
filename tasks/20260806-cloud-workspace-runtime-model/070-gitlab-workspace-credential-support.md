# GitLab workspace credential support

Extend the provider-neutral workspace credential and deletion lifecycle to
GitLab with writable, expiring deploy keys.

Parent Task: `tasks/20260806-cloud-workspace-runtime-model/000-main.md`
Depends On: `tasks/20260806-cloud-workspace-runtime-model/060-github-workspace-credential-lifecycle.md`

Specification:
`plugins/cloud-agent-app/docs/development/specifications/cloud-workspaces/index.md`

Requirements: `CWS-026`, `CWS-027`, `CWS-028`, `CWS-029`, `CWS-030`.

## Requirements checklist

- [ ] The cloud plugin recognizes supported GitLab remote forms or accepts explicit GitLab provider selection.
- [ ] A logged-in GitLab CLI can register the workspace public key as a writable deploy key.
- [ ] GitLab deploy keys receive a configurable expiration safety backstop.
- [ ] The cloud clone can fetch and push through the GitLab deploy key.
- [ ] Workspace removal revokes, or confirms expiration/absence of, the GitLab deploy key before deleting cloud state.
- [ ] GitLab API failures preserve retryable deletion state and do not expose CLI credentials.
- [ ] GitHub behavior remains unchanged through the shared provider-neutral lifecycle.

## Supporting details

Reuse the key generation, protected storage, SSH configuration, metadata,
deletion state machine, and exclusion guarantees completed in task 060. This
task adds provider parity rather than a second lifecycle.

## Execution plan
Status: Draft

### Stage 1 — GitLab issuance, expiration, and push

Implement provider detection/configuration, authenticated `glab` API use,
writable deploy-key registration with expiration, and gated fetch/push
verification against a GitLab test project.

### Stage 2 — GitLab revocation and recovery

Integrate GitLab deletion, already-expired/already-absent success handling,
temporary API failure retries, and provider-parity documentation.

### Implementation decisions and open questions

- Define the default and maximum deploy-key lifetime during detailed planning.
- Support common GitLab.com and self-managed SSH/HTTPS remote forms where the
  authenticated `glab` host is unambiguous.
- Require explicit provider/host selection when remote inference is ambiguous.

### Documentation

- Document GitLab host/login prerequisites, expiry behavior, permissions,
  fetch/push, removal, and self-managed-host configuration.
- Keep shared credential lifecycle documentation provider-neutral and place
  GitLab-only differences in a focused section.

### Task checklist

- [ ] Finalize GitLab host and expiration contracts.
- [ ] Implement and verify Stage 1.
- [ ] Report gated GitLab issue/fetch/push procedure.
- [ ] Implement and verify Stage 2.
- [ ] Report revoke/expiry/retry procedure.
- [ ] Re-run shared GitHub credential lifecycle verification.
- [ ] Update specification requirements and current documentation with evidence.

### Requirement verification

Required automated coverage:

- Extend provider-neutral unit tests with GitLab host detection, explicit host
  selection, expiration, API error normalization, absent/expired deletion, and
  self-managed-host isolation.
- Add an explicitly gated real GitLab test-project suite that uses the logged-in
  `glab` session to create a writable expiring deploy key, query and assert its
  expiration, fetch/push from the cloud runtime, delete the workspace, and
  verify the key is absent or expired through the GitLab API.
- Exercise temporary API failure and retry without recreating deleted
  workspace/runtime state.
- Re-run the shared local Docker credential lifecycle and the gated GitHub
  provider suite to prove the provider-neutral abstraction remains compatible.
- Run an external/AWS credential scenario if task 060 did not already cover the
  shared deployed credential path after the final GitLab changes.

Unavailable provider credentials or test projects leave the gated verification
not run. Manual provider-page inspection is optional corroboration, not
acceptance evidence.

### Additional implementation verification

- Self-managed host routing never sends credentials to a different host.
- Provider API and CLI output is bounded and secret-safe.
- Test-created GitLab keys are cleaned up after success or failure.
- GitHub and credential-disabled Git profile end-to-end suites remain green.
