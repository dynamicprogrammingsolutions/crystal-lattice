# Cloud Agent Orchestrator
Plan and implement cloud agent orchestration for the terminal/server application. The feature should let a local server start a remote cloud agent for a session, transfer project files and session state, connect through a cloud-specific transport, and later bring changes and session history back.

## Task checklist

### 0100 MVP and follow-ups

- [x] `tasks/20260429-cloud-agent-orchestrator/0100-remote-docker-orchestrator-mvp.md`
- [x] `tasks/20260429-cloud-agent-orchestrator/0101-agentapplication-cloud-runtime.md`
- [x] `tasks/20260429-cloud-agent-orchestrator/0102-explicit-transfer-script-contract.md`
- [x] `tasks/20260429-cloud-agent-orchestrator/0103-async-runtime-readiness-observability.md`
- [x] `tasks/20260429-cloud-agent-orchestrator/0104-cloud-runtime-startup-optimizations.md`
- [x] `tasks/20260429-cloud-agent-orchestrator/0110-connection-scoped-cloud-routing.md`
- [x] `tasks/20260429-cloud-agent-orchestrator/0111-clean-up-e2e-test-realism.md`
- [x] `tasks/20260429-cloud-agent-orchestrator/0112-cloud-runtime-working-directory.md`
- [x] `tasks/20260429-cloud-agent-orchestrator/0113-connection-created-session-routing.md`
- [x] `tasks/20260429-cloud-agent-orchestrator/0114-cloud-transfer-endpoint-configuration.md`
- [x] `tasks/20260429-cloud-agent-orchestrator/0115-real-tool-sync-back-e2e.md`
- [x] `tasks/20260429-cloud-agent-orchestrator/0120-cloud-profile-config-no-behavior-change.md`
- [x] `tasks/20260429-cloud-agent-orchestrator/0121-default-cloud-profile-scripts.md`
- [x] `tasks/20260429-cloud-agent-orchestrator/0121.1-cloud-profile-schema-and-script-conventions.md`
- [ ] `tasks/20260429-cloud-agent-orchestrator/0121.2-cloud-validation-command-and-bundled-runtime-assets.md`
- [ ] `tasks/20260429-cloud-agent-orchestrator/0121.3-cloud-agent-config-reference-audit-and-typing.md`
- [ ] `tasks/20260429-cloud-agent-orchestrator/0121.4-cloud-validation-runtime-image-build-cleanup.md`
- [ ] `tasks/20260429-cloud-agent-orchestrator/0122-sync-profile-selection-ui.md`
- [ ] `tasks/20260429-cloud-agent-orchestrator/0123-cloud-profile-user-docs.md`
- [ ] `tasks/20260429-cloud-agent-orchestrator/0124-dockerfile-container-profiles.md`
- [ ] `tasks/20260429-cloud-agent-orchestrator/0125-explicit-ssh-transfer-adapter-script.md`
- [ ] `tasks/20260429-cloud-agent-orchestrator/0126-script-driven-cloud-layout.md`
- [ ] `tasks/20260429-cloud-agent-orchestrator/0127-cloud-specific-config-overrides.md`

### Later phases

- [ ] `tasks/20260429-cloud-agent-orchestrator/0200-linked-readonly-session-ux.md`
  - START AFTER the remaining `0100` through `0199` MVP follow-ups are complete.
- [ ] `tasks/20260429-cloud-agent-orchestrator/0300-native-cloud-connection-ux.md`
- [ ] `tasks/20260429-cloud-agent-orchestrator/0400-reuse-multi-session-and-sync-polish.md`
- [ ] `tasks/20260429-cloud-agent-orchestrator/0500-provider-and-deployment-expansion.md`

## Goals

- Add an orchestrator service that is independent from the bridge and independent from the architecture used to run cloud agents.
- Keep the orchestrator always reachable. First support a Dockerized service deployable on a remote Docker host with a stable secure address. A custom subdomain is useful but optional; a generated CloudFront HTTPS domain is acceptable for automated AWS deployment/testing.
- Add a cloud-specific transport and connection type rather than forcing cloud routing through bridge.
- Start with a deployable, usable end-to-end implementation, not a localhost-only prototype.
- Let project-specific scripts define workspace transfer behavior instead of hardcoding git or rsync assumptions.
- Make application actions the replaceable operation layer, while adding native frontend support where generic action rendering is not enough.
- Support a clean return path: transferred changes can be brought back to the original directory, and closing the remote session can overwrite the local session with the cloud session state.

## Architecture Direction

Main layers:

- Local terminal/server application:
  - owns local sessions, project/workspace context, and user-triggered cloud actions
  - receives orchestrator URL/access configuration at startup
  - packages workspace/session data and calls the orchestrator
- Cloud orchestrator service:
  - always-reachable control plane
  - manages cloud agent instances, tokens, routing, archive upload/download, status, and lifecycle
  - first implementation runs as a Dockerized service on a Docker-capable host; local Docker is used for testing
  - first AWS-testable deployment should provision an EC2 Docker host rather than Fargate, because the MVP cloud-agent backend needs to start/manage Docker containers
- Cloud agent runtime:
  - Docker container in the first version
  - runs an API-compatible agent server/runtime for imported sessions
  - receives transferred workspace archive and runs project-defined setup scripts
- Frontend/mobile cloud transport:
  - new transport type backed by the orchestrator
  - can connect using a copied link/token in the MVP
  - later supports automatic add/open flows and linked-session navigation

## Workspace Script Model

The transfer model should be script-based and project-defined.

Local packaging script environment:

- `AGENT_WORKSPACE_DIR`: the local project/current working directory.
- `AGENT_TRANSFER_DIR`: an empty temporary directory where the script places files to send.

Cloud setup script environment:

- `AGENT_TRANSFER_DIR`: the unpacked transferred archive directory on the cloud agent.
- `AGENT_WORKSPACE_DIR`: the cloud working directory where the project should be prepared.

The script may use any project-appropriate mechanism: `rsync`, `git archive`, generated files, monorepo filtering, raw copy, or no git at all.

## Existing Relevant System Notes

- Application-level plugins and actions already exist:
  - `core/python/agent_app/app_plugins.py`
  - `core/python/agent_app/application_future.py`
  - `application/python/agent_terminal_app/server.py` endpoints: `/application/actions`, `/application/ui-schema`, `/actions`
- Mobile/frontend action displays already support copy actions:
  - `packages/frontend-sdk/src/types/plugins.ts` defines `ActionDisplayCopyTextAction`.
  - `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx` and `mobile/crystal-lattice-control-rn/src/SessionsScreen.tsx` handle `copy_text`.
  - `plugins/chatgpt-auth-app/src/chatgpt_auth_app/__init__.py` is a useful example of returning action display payloads with `copy_text`, `open_url`, and `run_action`.
- Existing connection records are manual/discovery/bridge:
  - `packages/frontend-sdk/src/connections/types.ts`
  - `packages/frontend-sdk/src/connections/store.ts`
  - `mobile/crystal-lattice-control-rn/App.tsx`
  - `mobile/crystal-lattice-control-rn/src/ConnectionsScreen.tsx`
- Bridge deployment docs are a useful template for the orchestrator deployment docs:
  - `bridge-elixir/PRODUCTION_DEPLOYMENT.md`
  - `bridge-elixir/docker-compose.single-node-v2.yml`
  - `bridge-elixir/deploy/aws-fargate/README.md`

## Deployment Notes From Current Bridge Investigation

The current private bridge deployment was inspected only to understand the deployment pattern; do not commit concrete private hostnames, domains, usernames, or deploy commands.

Generic pattern to support for the orchestrator MVP:

- Source is copied to a remote Docker host, commonly with `rsync` excluding build/dependency directories.
- The remote host builds and starts a single-node Docker Compose service.
- The service exposes a local HTTP port.
- Nginx on the same host may proxy a public subdomain to `127.0.0.1:<service-port>`.
- TLS may be terminated by Nginx/Certbot when a custom domain is available.
- A `/health` endpoint supports smoke tests.

The first implementation task should add enough generic documentation and script structure so an environment-specific deploy command can be created from SSH access details without committing those private details.

## AWS Deployment Direction For The MVP

The orchestrator should have a bridge-like automated deployment/testing story: with AWS CLI credentials and sufficient permissions, an integration/e2e script can create the resources, run smoke tests, and destroy the resources.

For the first version, use EC2 as a Docker host rather than Fargate for the cloud-agent backend:

- provision an EC2 instance
- install Docker and Docker Compose through cloud-init/user-data or an equivalent bootstrap
- deploy the orchestrator service, and optionally the bridge service, as Docker Compose services
- expose the services through a stable secure address
- prefer a generated CloudFront HTTPS domain for automated tests so no custom DNS is required
- optionally support a custom domain path later through Route53/ACM or a remote-host Nginx/Certbot setup

This is distinct from a future Fargate cloud-agent backend. A single Fargate task can host an orchestrator-like service, but it is not enough for the MVP Docker-agent runtime model because it cannot act as a normal Docker host for per-session containers.

## High-Level Acceptance

- A user can start a cloud agent for a local session and connect to it through the new cloud transport.
- The remote orchestrator can be deployed as a Dockerized service with a stable secure address; a generated CloudFront HTTPS domain is acceptable and a custom subdomain is optional.
- Local Docker can test the same core flow.
- Project-defined scripts control workspace transfer.
- Changes can be transferred back to the original local directory.
- Closing a remote session can overwrite/update the local session with remote session state.
- Later subtasks add native UX, reuse/multi-session flows, additional cloud backends, and deployment hardening without replacing the MVP architecture.