# Cloud workspaces product specification

## Problem

The current cloud-agent workflow treats a selected session and a newly started
container as the center of the cloud lifecycle. Starting the runtime is
expensive because repository, config, and runtime material are transferred for
one session even when the user later wants another existing session or a new
one. The resulting connection is short-lived, and orchestrator restart can
leave running containers and durable bytes that are no longer manageable.

Users need a cloud workspace that remains accessible independently of:

- which session they initially want to use;
- whether the runtime container is currently running;
- whether the local source server is reachable;
- whether the orchestrator process has restarted.

## Product model

A cloud workspace is a durable server-side directory and identity containing:

- a complete repository clone and current working state;
- portable application configuration for all transferred agents;
- all transferred live sessions and session-owned assets;
- runtime setup state and project-specific hook results;
- workspace-specific Git credentials when explicitly requested.

A runtime is a replaceable process attached to that workspace. Stopping the
runtime preserves the workspace and connection. Starting it makes agent and
session APIs available again.

A cloud connection is the stable app-side identity and authorization channel
for one logical cloud connection. It remains usable for control even when no
runtime process exists.

## Primary user workflows

### Create a workspace

From the local application, the user starts a connection-level action without
selecting a session. Creation runs in the background and reports phases through
an application notification.

The resulting workspace contains all configured agents, all live sessions,
session-owned assets, and the complete default Git clone transfer. The user
saves or opens the cloud connection and may use any transferred session or
create a new one.

### Leave and reconnect

The user may leave the local source server unavailable for days. A previously
saved mobile or desktop cloud connection remains authenticated until it is
explicitly revoked. Orchestrator restart does not lose the workspace,
connection, routes, or managed runtime identity.

### Stop and start runtime

The user may disable the connection setting **Run cloud workspace** or execute
**Stop runtime**. Sessions and agents become temporarily unavailable, but
connection settings, actions, status, and notifications remain available.

Enabling the setting or executing **Start runtime** starts a new runtime
against the same workspace. Readiness progress is visible, and session/agent
views refresh when ready.

### Work with Git

The cloud workspace starts from a complete clone containing reachable history,
branches, and tags, plus the current local worktree state. The original
upstream remains `origin`.

Sync-down exports cloud refs and updates a stable local remote. The product
does not automatically merge, rebase, reset, or checkout branches.

When explicitly enabled, the plugin creates a new workspace-specific writable
credential for the primary GitHub or GitLab repository. Existing local private
keys are not transferred.

### Exchange one session

The user can add a local session to an existing running workspace or import a
cloud-created session locally. Directional sync explicitly replaces the
destination copy after confirmation. Repository transfer does not run for
session-only exchange.

### Remove a workspace

Supported deletion stops the runtime, revokes provider-issued Git access,
removes durable workspace and orchestrator records, and revokes the cloud
connection. Provider revocation failure leaves a visible retryable deletion
state instead of reporting success.

In the first target, guaranteed provider revocation requires the source server
that owns the logged-in GitHub or GitLab CLI session.

## Goals

- Make cloud workspace creation independent of session selection.
- Amortize repository/runtime transfer across all sessions used in a workspace.
- Preserve access through local-server absence and orchestrator restart.
- Make stopped runtime a normal, controllable connection state.
- Keep repository-specific behavior in replaceable default/project scripts.
- Use normal Git concepts for cloud work rather than an opaque patch-only
  round trip.
- Avoid transferring existing user Git private keys.
- Keep the orchestrator narrow enough for future runner replacement.
- Preserve useful current flows and project overrides during migration.

## Non-goals

- Distributed workspace scheduling or multi-node failover.
- Multiple concurrently writing runtimes for one workspace.
- Automatic runtime wake for arbitrary proxied requests.
- General-purpose GitHub App, GitLab OAuth, or cloud secret broker services.
- Immediate deletion from a remote app when the source credential manager is
  unavailable.
- Transfer of snapshot history, transient event history, linked worktrees,
  ignored build trees, or every private dependency.
- Automatic Git integration decisions.
- Automatic session merging.

## Acceptance examples

### Reconnect after time away

A user creates a workspace, saves the connection on a phone, turns off the
local source server, and reconnects more than 24 hours later. The connection
still loads control state and, if the runtime is running, sessions.

### Recover after orchestrator restart

The orchestrator process restarts while the Docker runtime and host storage
remain. It reloads manifests, rediscovers the labeled container, restores
proxy routing, and the saved app reconnects without a new link.

### Use a stopped workspace

The runtime is stopped. Server settings still show **Run cloud workspace** as
disabled, runtime status reports `stopped`, and **Start runtime** is available.
Session requests report runtime unavailability without removing the saved
connection. Enabling the setting starts the runtime and reloads sessions after
readiness.

### Use all agents and sessions

An application with multiple agents and asset-bearing sessions creates one
workspace. The cloud connection lists all transferred sessions, can use each
configured agent, and can create new cloud sessions.

### Synchronize a cloud branch

The user creates and commits a branch in cloud. Sync-down updates a stable
local cloud remote. The local current branch and worktree remain unchanged,
and the user may inspect, merge, or cherry-pick the cloud branch.

### Revoke cloud Git access

The plugin creates a new writable deploy key for the primary repository. The
runtime pushes a branch. Workspace removal deletes the provider key before
deleting the private key and workspace. If provider deletion fails, the
workspace remains in a retryable deletion state.
