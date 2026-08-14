# GitHub workspace credential lifecycle

Issue a new workspace-specific writable GitHub credential from the source
application's logged-in GitHub CLI and revoke it before destructive workspace
removal.

Parent Task: `tasks/20260806-cloud-workspace-runtime-model/000-main.md`
Depends On:

- `tasks/20260806-cloud-workspace-runtime-model/010-durable-orchestrator-state-and-stable-connections.md`
- `tasks/20260806-cloud-workspace-runtime-model/030-application-workspace-creation-and-complete-transfer.md`
- `tasks/20260806-cloud-workspace-runtime-model/040-full-git-clone-and-remote-sync.md`

Specification:
`plugins/cloud-agent-app/docs/development/specifications/cloud-workspaces/index.md`

Requirements: `CWS-024`, `CWS-025`, `CWS-027`, `CWS-028`, `CWS-029`,
`CWS-030`.

## Requirements checklist

- [ ] The cloud plugin can generate a new per-workspace SSH keypair without copying an existing local private key.
- [ ] A logged-in GitHub CLI can register the public key as a writable deploy key for the primary repository.
- [ ] The private key is stored only in protected cloud workspace state and is excluded from sync, logs, notifications, and connection links.
- [ ] The cloud clone can fetch and push through the issued deploy key.
- [ ] Credential provider, repository, deploy-key ID, fingerprint, and lifecycle state are durably recorded without storing the private key in control metadata.
- [ ] Supported workspace removal revokes or confirms absence of the deploy key before deleting cloud storage.
- [ ] Workspaces without a provider credential can be removed through the same lifecycle with the revocation step treated as not applicable.
- [ ] Failed revocation leaves a retryable deletion state rather than reporting successful removal.
- [ ] Runtime stop/start remains available without the source server, while destructive deletion requires source credential-manager participation.

## Supporting details

Use a provider-neutral credential lifecycle internally, with GitHub as the
first complete adapter. Initial scope is the primary repository only. GitHub
deploy keys have no required expiry in this target, so explicit revocation is
mandatory.

## Execution plan
Status: Draft

### Stage 1 — Provider-neutral credential storage and runtime use

Generate keys, define credential metadata/lifecycle records, install the
private key under protected workspace state, configure instance-local SSH, and
prove that all transfer/export/logging paths exclude it.

Stage completion is testable with a locally controlled SSH Git repository.

### Stage 2 — GitHub issuance and push

Detect/select GitHub remotes, use authenticated `gh api` calls to create a
writable deploy key, record the returned identity, and exercise fetch/push
against an explicitly gated GitHub test repository.

### Stage 3 — Revoke-before-delete workspace removal

Introduce supported destructive workspace deletion as a two-phase operation:
stop runtime, revoke or confirm absent provider credential, remove storage and
durable records, then revoke the cloud connection. Persist and notify retryable
failure states. The same operation removes workspaces with no provider
credential by treating provider revocation as not applicable.

### Implementation decisions and open questions

- Source-server participation is required for guaranteed initial-provider
  revocation; remote mobile clients may stop but not finalize deletion alone.
- Decide whether the keypair is generated in a protected local temporary
  directory or after workspace provisioning, while ensuring only the new
  cloud-specific private key crosses the transfer boundary.
- Protected-branch policy remains provider/repository behavior and is not
  bypassed.

### Documentation

- Document GitHub prerequisites, permission requirements, key location,
  security boundaries, push behavior, and deletion failure recovery.
- Document that primary-repository deploy keys do not cover private submodules
  or secondary repositories.

### Task checklist

- [ ] Finalize provider-neutral credential and deletion state machines.
- [ ] Implement and verify Stage 1.
- [ ] Report local SSH credential isolation procedure.
- [ ] Implement and verify Stage 2.
- [ ] Report gated GitHub creation/fetch/push procedure.
- [ ] Implement and verify Stage 3.
- [ ] Report revoke-before-delete and retry workflow.
- [ ] Update specification requirements and current documentation with evidence.

### Requirement verification

Required automated coverage:

- Add provider-neutral unit tests for key generation, protected placement,
  metadata state transitions, SSH configuration, secret exclusion, deletion
  ordering, and retry behavior using controlled command/API adapters.
- Add local Docker integration with a disposable SSH Git server to prove the
  runtime uses only the generated workspace key across stop/start and that
  transfer/export/log artifacts exclude it.
- Add an explicitly gated real GitHub test-repository suite that uses the
  logged-in `gh` session to create the deploy key, query it by returned ID,
  fetch/push from the cloud runtime, delete the workspace, and verify the key
  is absent through the GitHub API.
- Include forced provider failure/retry cases without leaving test deploy keys.
- Run the relevant local cloud e2e and at least one remote Docker or AWS
  fresh-build credential lifecycle before marking the provider capability
  complete, because protected remote workspace storage and deployed runtime
  SSH behavior are part of the requirement.

If the gated GitHub suite cannot run because credentials or a designated test
repository are unavailable, verification remains not run. Manual inspection of
the provider UI does not replace API assertions.

### Additional implementation verification

- All test-created GitHub deploy keys are cleaned up even after test failure.
- Secret scanning of transfer/export artifacts does not find the private key.
- Provider API errors and insufficient repository permissions produce safe,
  actionable messages without exposing authentication tokens.
- Existing full-clone and remote-sync profile e2e remains green with
  credentials disabled.
