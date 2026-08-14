# Cloud workspaces

This package-owned specification defines the target cloud workspace model for
the Cloud Agent App plugin and the narrow orchestrator/runtime contracts needed
to support it.

The plugin owns the high-level workspace, transfer, session, Git, credential,
and user-workflow semantics. The cloud orchestrator remains a replaceable
control plane for durable records, connection authorization, runner lifecycle,
runtime reconciliation, and proxy/control routing.

- [Product specification](product-spec.md)
- [Technical specification](technical-spec.md)
- [Requirements and evidence](requirements.md)
- [Durable workspace, runtime, and connection decision](decisions/001-durable-workspace-runtime-and-connection.md)
- [Git transfer and remote synchronization decision](decisions/002-git-bundle-and-remote-sync.md)
- [Provider-issued Git credential decision](decisions/003-provider-issued-deploy-keys.md)

## Ownership and relationships

Owner:

- `plugins/cloud-agent-app`

Implementing and consuming packages:

- `cloud-orchestrator`
- `application/python/agent_terminal_app`
- `packages/frontend-sdk`
- `packages/frontend-sdk-react`
- `mobile/crystal-lattice-control-rn`
- `desktop/crystal-lattice-control-desktop-rn`

Related portable contracts:

- `docs/development/specifications/notifications/`
- `docs/development/specifications/action-display/`
- `plugins/docs/application-plugins.md`
- `plugins/docs/notifications-and-action-displays.md`

Active work:

- `tasks/20260806-cloud-workspace-runtime-model/000-main.md`

## Target and current state

The target is not yet implemented.

Current behavior is session-oriented: cloud startup transfers one session,
creates a runtime container, and stores connection details on that local
session. Connection tokens expire after 24 hours, orchestrator registries are
process-local, and control requests are proxied into the runtime. Workspace
bytes may survive in the configured host data directory, but the orchestrator
cannot reliably recover their identity or managed containers after restart.

Live implementation, verification, documentation, and evidence status is
tracked in [requirements.md](requirements.md).

## Scope

The first target includes:

- stable saved cloud connections;
- durable single-node orchestrator state and Docker reconciliation;
- durable workspace storage with a separately startable/stoppable runtime;
- always-on connection settings, actions, status, health, and notifications;
- application-level workspace creation;
- complete agent, live-session, and session-asset transfer;
- full-clone Git transfer and remote-style sync;
- single-session add/import/directional sync;
- GitHub and GitLab workspace-specific deploy-key lifecycle;
- revoke-before-delete workspace removal;
- compatibility for existing script phases, profiles, identifiers, and the
  legacy session-start action.

Deferred:

- multi-node or distributed orchestration;
- automatic request-triggered wake;
- runtime pools and idle scheduling;
- storage quotas and automated retention;
- one-time invitations and per-device cloud credentials;
- cloud-side provider credential brokers;
- destructive deletion while the source credential manager is unavailable;
- linked worktree, private-submodule, and multi-repository credential support;
- session merge or conflict-free synchronization.
