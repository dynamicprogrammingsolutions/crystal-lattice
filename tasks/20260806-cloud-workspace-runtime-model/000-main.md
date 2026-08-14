# Cloud workspace and runtime model

Evolve the existing cloud-agent plugin and cloud orchestrator from a
session-owned, container-lifetime model into a durable workspace model with a
separately controlled runtime, stable cloud connections, complete application
transfer, Git-native synchronization, and revocable provider-issued Git
credentials.

## Requirements checklist

- [ ] Saved cloud connections remain authenticated and usable until explicitly revoked, including after the local source server is unavailable.
- [ ] Orchestrator restart preserves and recovers cloud connections, routes, workspace records, and managed Docker runtimes.
- [ ] A cloud workspace remains durably available while its runtime is stopped.
- [ ] Connection settings, runtime controls, status, and notifications remain available while the runtime is stopped.
- [ ] Users can create a cloud workspace without selecting a session.
- [ ] Workspace creation transfers all configured agents, all live sessions, and session-owned assets.
- [ ] The default repository transfer produces a complete Git clone and syncs cloud refs back through a stable remote-style workflow.
- [ ] Individual sessions and their assets can be sent to or imported from an existing cloud workspace.
- [ ] GitHub and GitLab workspaces can receive newly issued, workspace-specific writable credentials without transferring existing local private keys.
- [ ] Supported workspace removal revokes provider-issued Git access before deleting cloud storage and revoking the cloud connection.
- [ ] Existing project transfer/setup/install/validation script contracts and legacy transfer profiles remain usable.
- [ ] Existing session-start behavior remains available as a compatibility wrapper during migration.

## Scope and workstreams

The target is intentionally evolutionary:

- existing `connection_id` and `instance_id` identifiers remain compatible;
- the existing instance directory becomes the durable workspace storage;
- the Docker container becomes a separately controlled runtime;
- the cloud plugin remains the owner of repository, session, credential, and
  user-workflow semantics;
- the orchestrator owns durable records, connection authorization, runner
  lifecycle, reconciliation, and the always-on control surface.

The first target remains single-node and Docker-backed. Multi-node scheduling,
automatic request-triggered wake, general credential brokers, and storage
quotas are deferred.

Specification:
`plugins/cloud-agent-app/docs/development/specifications/cloud-workspaces/index.md`

Requirements: `CWS-001` through `CWS-032`.

## Subtasks

- [ ] `tasks/20260806-cloud-workspace-runtime-model/010-durable-orchestrator-state-and-stable-connections.md`
- [ ] `tasks/20260806-cloud-workspace-runtime-model/020-workspace-runtime-lifecycle-and-control.md`
- [ ] `tasks/20260806-cloud-workspace-runtime-model/030-application-workspace-creation-and-complete-transfer.md`
- [ ] `tasks/20260806-cloud-workspace-runtime-model/040-full-git-clone-and-remote-sync.md`
- [ ] `tasks/20260806-cloud-workspace-runtime-model/050-single-session-exchange.md`
- [ ] `tasks/20260806-cloud-workspace-runtime-model/060-github-workspace-credential-lifecycle.md`
- [ ] `tasks/20260806-cloud-workspace-runtime-model/070-gitlab-workspace-credential-support.md`

## Supporting details

- Current cloud bearer tokens expire after 24 hours while frontend connection
  records persist the expired token.
- Current connection, route, transfer, and instance registries are in-memory.
- Workspace bytes already live below the configured orchestrator data
  directory and can be preserved by the existing host mount.
- Current cloud transport proxies server settings, application actions, and
  health checks into the runtime, making them unavailable when the container
  is stopped.
- Current workspace creation exports one session and optimizes the portable
  config to one selected agent.
- Current bundled transfer scripts preserve current worktree content but do
  not transfer the complete clone as a durable remote-style workflow.
- The approved target uses provider-issued deploy keys as the common GitHub
  and GitLab credential model. Source-server participation is required for
  guaranteed provider revocation in the initial target.

## Execution plan
Status: Draft

Execute subtasks in dependency order. Tasks 040 and 050 may proceed in
parallel after task 030. Every task owns its implementation, automated
verification, current documentation, specification/requirements updates, and
stage handoff. There is no separate testing, documentation, or final-check
subtask.

Each stage ends with a report describing:

- user-visible behavior now available;
- requirement IDs and live evidence status;
- compatibility and migration effects;
- automated unit, integration, Docker end-to-end, remote/AWS, and gated
  provider verification performed or explicitly blocked;
- a concise procedure the user can run against the application;
- remaining limitations assigned to later work.

The user procedure is a stage handoff, not a substitute for automated
acceptance evidence.

### Verification baseline

Automated verification is the default. Detailed subtask planning may refine
exact test names and fixtures, but must preserve these existing boundaries:

- package and protocol tests:
  - `pytest plugins/cloud-agent-app/tests -q`;
  - `(cd cloud-orchestrator && mix test)`;
  - focused `application/python/tests` for runtime, HTTP, notifications, and
    installed-bundle behavior;
  - `npm --workspace @crystal-lattice/frontend-sdk test`;
  - `npm --workspace @crystal-lattice/frontend-sdk-react test`;
  - `npm --workspace @crystal-lattice/frontend-rn-components test`;
  - package-local mobile and desktop Jest/integration suites when those
    frontends change;
- real local application integration through public FastAPI and frontend SDK
  adapters;
- local Docker cloud end-to-end through
  `npm --workspace @crystal-lattice/frontend-sdk run integration:cloud` and
  `integration:cloud:profiles`;
- gated remote deployment coverage through
  `integration:cloud:remote-docker` and AWS EC2 + CloudFront coverage through
  `integration:cloud:aws:fresh` for behavior involving persistence,
  reconciliation, runtime lifecycle, default images/config, or deployment
  storage;
- gated real GitHub/GitLab repository tests for credential issuance, push,
  lookup, revocation, and cleanup.

New acceptance scenarios extend the existing realistic
frontend SDK → local app action → orchestrator → runtime → sync-back harness.
They must not bypass public HTTP, production transports, deployment scripts, or
normal workspace transfer/runtime behavior.

Manual verification is required only for a material native presentation or
external-provider observation that cannot be asserted through the available
automated suites. A skipped gated test is reported as not run, not passed.

### Implementation decisions and open questions

Decided:

- Keep current public identifiers and evolve their semantics rather than add a
  parallel `/workspaces` API in the first target.
- Model runtime settings as desired state and runtime status as observed state.
- Keep project script phases and profile overrides as the repository-specific
  extension mechanism.
- Transfer all live sessions and session-owned assets, but not snapshot or
  transient event history.
- Preserve IDs during session exchange and require explicit overwrite.
- Use full Git bundles and stable remote-tracking refs rather than copying raw
  `.git` internals.
- Use newly generated per-workspace deploy keys for GitHub and GitLab.

Open during subtask planning:

- Exact legacy connection-token migration and rotation response shape.
- Exact stopped-runtime representation for `GET /sessions` while preserving
  frontend usability and avoiding a false empty-state interpretation.
- Exact secure-at-rest handling for cloud connection and deploy-key metadata
  on each supported frontend/runtime host.

### Documentation

- Create and maintain the package-owned specification at
  `plugins/cloud-agent-app/docs/development/specifications/cloud-workspaces/`.
- Update `plugins/cloud-agent-app/README.md` and
  `plugins/cloud-agent-app/docs/cloud-script-authoring.md` only as behavior
  becomes implemented.
- Update cloud-orchestrator current behavior and deployment documentation with
  durable-state, reconciliation, runtime lifecycle, and control-plane details.
- Update frontend connection/settings documentation for stopped-runtime
  behavior.

### Task checklist

- [ ] Create the target specification and live requirements before implementation.
- [ ] Complete task 010 and verify restart recovery with current cloud creation.
- [ ] Complete task 020 and verify stopped-runtime connection control.
- [ ] Complete task 030 and verify application-level complete workspace creation.
- [ ] Complete tasks 040 and 050 in either order or in parallel.
- [ ] Complete task 060 and verify GitHub credential issuance and revocation.
- [ ] Complete task 070 and verify GitLab parity.
- [ ] Keep requirement evidence and parent/subtask state synchronized after every stage.

### Requirement verification

The parent requirements are complete only when their owning subtasks record
concrete automated or human evidence and the package specification
requirements table links that evidence. The final user-relevant boundary is a
saved mobile or desktop cloud connection controlling a durable workspace
through orchestrator restart, runtime stop/start, complete workspace transfer,
session exchange, Git synchronization, and provider credential deletion.

At minimum, completion requires the fast package suites, the relevant real
backend integration suites, local Docker cloud end-to-end, standard-profile
end-to-end, and every task-designated remote/AWS or provider-gated scenario.
Detailed planning chooses focused commands and test names; it may not reduce
the required behavior boundaries.

### Additional implementation verification

- Realistic integration must preserve the public
  local-app → orchestrator → runtime → sync-back path.
- Restart verification must actually restart the orchestrator process or
  container rather than reconstructing registries directly in a test.
- Provider credential verification should use explicitly gated test
  repositories/projects and must clean up created keys.
