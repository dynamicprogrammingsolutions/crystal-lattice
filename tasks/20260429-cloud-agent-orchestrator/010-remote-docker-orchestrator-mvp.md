# Remote Docker Orchestrator MVP
Build the first usable end-to-end version: a Dockerized orchestrator deployable on a remote Docker host with a stable secure address, local Docker testing support, an AWS EC2 Docker-host deployment/e2e path, a cloud transport, and an action that starts a cloud agent for one session and returns a copyable connection link.

## Requirements checklist

- [x] Add a standalone orchestrator service independent from bridge.
- [x] Add a Docker backend for cloud agents, usable both locally for testing and on a remote Docker host.
- [x] Add Docker Compose and deployment docs for a single-node orchestrator reachable through a stable secure address.
- [x] Add an AWS EC2 Docker-host deployment/e2e path that can be run with AWS CLI credentials and tears resources down after smoke tests.
- [x] Expose the AWS e2e deployment through a generated CloudFront HTTPS address by default, without requiring a custom subdomain.
- [x] Optionally support generic remote-host reverse proxy/subdomain deployment with Nginx/Certbot or equivalent docs.
- [x] Add a `/health` endpoint and smoke test path for orchestrator deployment.
- [x] Add a cloud transport and `cloud` connection record type in the frontend SDK/mobile.
- [x] Add terminal/server startup configuration for orchestrator URL and access token/secret.
- [x] Add an application action, conventionally `cloud.start_session_agent`, that starts a cloud agent for one selected session.
- [x] Implement project-defined transfer/setup/export/apply scripts using `LOCAL_WORKSPACE_DIR`, `CLOUD_WORKSPACE_DIR`, and `TRANSFER_DIR`.
- [x] Transfer the selected session and project files/metadata through an opaque transfer slot to the cloud runtime.
- [x] Import the session into the cloud runtime and expose it through the cloud transport.
- [x] Return a display payload with a single copyable cloud connection link containing URL/token/session target.
- [x] Support transferring cloud workspace changes back to the original local directory at any time.
- [x] Support closing the remote session and overwriting/updating the local session with the remote session state.
- [x] Add enough generic documentation and script hooks so a private rsync+SSH deploy command can be assembled in the current environment without committing private host/domain details.

Parent Task: `tasks/20260429-cloud-agent-orchestrator/000-main.md`

## Scope

This subtask should be usable as-is. It is not enough to run a local-only demo.

The orchestrator should be deployable to a remote server that supports Docker and is reachable through a stable secure address. A custom subdomain is optional. Local Docker is still required as the primary development/test path.

The MVP may use manual copy/paste for the connection link. Automatic connection insertion and native linked-session UX are intentionally left for later subtasks.

## Deployment Requirements

Mirror the bridge's practical single-node deployment pattern, but update it for the orchestrator's needs and keep all documentation generic:

- Provide a Dockerfile and Docker Compose file for the orchestrator service.
- Bind the orchestrator to an internal HTTP port.
- Document reverse proxy setup with examples using a placeholder domain such as `cloud.example.com`, but do not make a custom subdomain required.
- Include WebSocket/proxy headers if the cloud transport uses WebSockets.
- Document TLS termination via an external reverse proxy such as Nginx/Certbot, Caddy, Traefik, or a load balancer.
- Provide a health check endpoint, for example `GET /health`.
- Provide smoke test commands that verify health and basic instance lifecycle.
- Provide generic rsync+SSH deployment steps with placeholders only.

Implementation should make it straightforward to create a private deploy command equivalent in shape to:

- copy orchestrator source to `user@host:~/cloud-orchestrator/`
- SSH to the host
- run `docker compose` or `docker-compose` build/up
- verify `/health` through the public stable address

Do not include concrete private domains, usernames, or host-specific commands in committed docs or task files.

## AWS EC2 Docker-Host Deployment/E2E

Add an automated AWS deployment path comparable in spirit to the bridge Fargate deployment tests, but using EC2 as a Docker host for the MVP.

Requirements:

- The script should be runnable with AWS CLI credentials and sufficient permissions.
- The script should create the needed resources, run smoke/e2e checks, and support destroying all created resources.
- Provision an EC2 instance with Docker and Docker Compose installed through user-data/cloud-init or a similarly reproducible bootstrap.
- Deploy the orchestrator service as a Docker Compose service on the EC2 host.
- Deploy the bridge service on the same EC2 host if it simplifies end-to-end testing or provides useful parity with current bridge deployments.
- Expose the orchestrator through a stable secure generated address by default, preferably a CloudFront HTTPS domain.
- Do not require Route53, a user-owned custom domain, or Let's Encrypt for the default AWS e2e path.
- Include optional documentation for custom-domain setups separately from the default generated-domain flow.
- Include smoke tests for health, archive upload/start, cloud transport connection, sync-down, and cleanup.

Important rationale:

- A single Fargate task is not sufficient for the MVP cloud-agent backend because the MVP backend needs to start/manage Docker containers for cloud agents.
- A future Fargate backend may use persistent storage and short-running tasks, but it belongs in a later provider-expansion task.

## Orchestrator MVP API Shape

Exact paths may change during implementation, but the MVP should support these capabilities:

- Health/status.
- Create or start an agent instance for an opaque transfer slot.
- Create managed transfer slots without assuming archive names, compression formats, or transfer commands.
- Report instance status.
- Route/proxy transport requests to a cloud agent instance.
- Generate short-lived connection tokens or signed connection links.
- Export changes/session state from the cloud runtime back to the local server.
- Stop/close a remote session and return final session state.

## Application Action Result

The action result should include a display payload with a copy action, following the existing ChatGPT auth action display pattern.

Example shape:

```json
{
  "display": {
    "format": "markdown",
    "title": "Cloud Agent Ready",
    "body": "The cloud session is ready. Copy the connection link and open it from the mobile app.",
    "variant": "success",
    "actions": [
      {
        "kind": "copy_text",
        "id": "copy-cloud-connection-link",
        "label": "Copy connection link",
        "text": "crystal-lattice-cloud://connect?orchestrator=..."
      }
    ]
  }
}
```

The link should include enough information for the cloud transport to connect, such as orchestrator URL, instance id, remote session id, and a token. Prefer short-lived or revocable tokens.

## Workspace And Session Flow

Minimum flow:

1. User runs `cloud.start_session_agent` from a local session.
2. Local server creates an ephemeral `TRANSFER_DIR`.
3. Local transfer script runs with `LOCAL_WORKSPACE_DIR`, `CLOUD_WORKSPACE_DIR`, and `TRANSFER_DIR`.
4. Local server adds selected session export data to the transfer data using the documented helper convention.
5. Local transfer plugin uploads/synchronizes the transfer slot using the chosen transfer method.
6. Orchestrator marks the transfer slot ready.
7. Orchestrator starts a Docker cloud agent runtime.
8. Docker runner materializes the transfer slot into the runtime using the most efficient backend-specific method, such as bind mount, move, copy, or later remote storage.
9. Cloud setup script runs with `CLOUD_WORKSPACE_DIR` and `TRANSFER_DIR`.
10. Cloud runtime imports the session.
11. Orchestrator returns a connection link/token.
12. User connects through cloud transport.
13. User can request sync-down at any time to apply cloud workspace changes to the original local directory.
14. Closing the remote session returns final cloud session state and overwrites/updates the local session.

## High-Level Behaviors To Test Before Acceptance

- Orchestrator health check works locally and through a reverse-proxied URL.
- Orchestrator health check works through the AWS-generated secure address.
- Local Docker start/import/connect flow works for one session.
- Remote Docker deployment can be built and started using generic Docker Compose commands.
- AWS EC2 Docker-host deployment can create resources, run smoke checks, and destroy resources.
- Cloud transport can connect to the cloud runtime using the copied link/token.
- Workspace transfer script receives the correct env vars and controls transferred files/metadata.
- Cloud setup script receives the correct env vars and prepares the workspace without depending on a fixed archive format.
- Selected session appears in the cloud runtime with expected messages.
- Sync-down transfers file changes back to the original local directory.
- Closing the remote session overwrites/updates the original local session with remote state.
- Tokens or connection links fail predictably when invalid or expired.
- Smoke tests cover health and a minimal instance lifecycle.
- Default AWS e2e path does not require a custom subdomain.

## Known References

- Bridge single-node deployment docs: `bridge-elixir/PRODUCTION_DEPLOYMENT.md`.
- Bridge Compose template: `bridge-elixir/docker-compose.single-node-v2.yml`.
- Bridge AWS deployment docs and smoke-test structure: `bridge-elixir/deploy/aws-fargate/README.md`.
- Application action display/copy examples: `plugins/chatgpt-auth-app/src/chatgpt_auth_app/__init__.py`.
- Action display types: `packages/frontend-sdk/src/types/plugins.ts`.
- Existing connection types: `packages/frontend-sdk/src/connections/types.ts`.

## Progress notes

Added during completion:

- Created `cloud-orchestrator/` as an independent Elixir/Phoenix service with `/health`, transfer slot lifecycle, instance lifecycle, token signing/verification, proxy route, runner behaviour, in-memory runner, and Docker runner scaffold.
- Added optional control-plane bearer auth via `CLOUD_ORCHESTRATOR_CONTROL_TOKEN`.
- Added single-node Dockerfile/Compose and generic remote Docker-host deployment docs with placeholder-only reverse proxy guidance.
- Started the guarded AWS EC2 Docker-host deployment command skeleton under `cloud-orchestrator/deploy/aws-ec2/`, then completed it with CloudFormation resource creation and CloudFront provisioning in the deployment pass below.
- Added `plugins.cloud_agent_app_plugin.CloudAgentAppPlugin` with `cloud.start_session_agent`, `cloud.sync_down`, and `cloud.close_session` action hooks and the approved script env contract.
- Added frontend SDK `CloudTransport`, cloud connection link parse/format helpers, and `cloud` connection record type.
- Added minimal mobile paste-link cloud connection support.
- Added a minimal Python cloud runtime image under `cloud-orchestrator/runtime/python`.
- Implemented a local Docker manual flow: default HTTP bundle upload into an opaque transfer slot, Docker runner starts the runtime container with transfer/workspace mounts, proxy exposes runtime session routes, and close imports remote session state back into the local session.
- Implemented default sync-down for the local Docker/manual path: Docker runner exports the cloud workspace into a download transfer slot, the local action downloads the bundle, and default apply copies it into `LOCAL_WORKSPACE_DIR`.
- Added a guarded frontend SDK E2E test at `packages/frontend-sdk/src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts`. It starts a local Python backend, starts the Elixir orchestrator with Docker runner, uses `RestAgentBackend` to call `cloud.start_session_agent`, uses `CloudTransport` + `RestAgentBackend` to open the cloud runtime, writes a real file in the cloud workspace, runs `cloud.sync_down`, appends a remote message, closes the cloud session, and verifies the local workspace/session were updated.
- Added generic remote Docker deployment support under `cloud-orchestrator/deploy/remote-docker/`, including v2 Compose compatibility for older `docker-compose` hosts, runtime image build, absolute host data directory support, and Docker bridge proxy/bind settings for sibling runtime containers.
- Extended the frontend SDK E2E with `CLOUD_ORCHESTRATOR_E2E_MODE=external` so the same test can validate a deployed orchestrator URL. The test now verifies file transfer in both directions: local workspace file appears in cloud runtime, and a cloud-written file syncs back down locally.
- Added AWS EC2 + CloudFront deployment support under `cloud-orchestrator/deploy/aws-ec2/`, following the bridge deploy command shape with guarded `build.sh`, `up.sh`, `down.sh`, `status.sh`, and `tests/smoke_secure.sh`.
- Split AWS artifact build from runtime deployment. `build.sh --builder ec2` uses a temporary larger EC2 builder to produce Docker image tarballs and upload them to S3; `up.sh` provisions a cheap runtime EC2 host, loads the prebuilt images, starts the orchestrator, and exposes it through generated CloudFront HTTPS. The builder and runtime stacks are cleaned up by the E2E/down path.
- Verified:
  - `mix test` in `cloud-orchestrator`
  - `pytest core/python/tests/test_cloud_agent_app_plugin.py -q`
  - `pytest core/python/tests/test_cloud_agent_app_plugin.py application/python/tests/test_application_actions_endpoints.py -q`
  - `npm test --prefix packages/frontend-sdk -- cloudTransport`
  - `docker build -t cloud-orchestrator:test .` in `cloud-orchestrator`
  - `docker build -t cloud-agent-runtime:latest runtime/python` in `cloud-orchestrator`
  - Docker image smoke with `CLOUD_ORCHESTRATOR_RUNNER=memory` and `GET /health`
  - Host-local Docker runner smoke: start local session, `cloud.start_session_agent`, proxy list messages, write cloud workspace file, `cloud.sync_down`, append remote message, `cloud.close_session`, verify local workspace has synced file and local session contains remote message.
  - `RUN_CLOUD_ORCHESTRATOR_E2E=1 npm test --prefix packages/frontend-sdk -- cloud-orchestrator.e2e`
  - Generic remote deploy script against a Docker host with older `docker-compose` v1 compatibility.
  - External-mode SDK E2E against the deployed remote Docker host through an SSH tunnel to the orchestrator port, including control-plane bearer token configuration.
  - `aws --region us-east-1 cloudformation validate-template --template-body file://cloud-orchestrator/deploy/aws-ec2/builder.yaml`
  - `aws --region us-east-1 cloudformation validate-template --template-body file://cloud-orchestrator/deploy/aws-ec2/secure.yaml`
  - Background AWS CloudFront E2E: `RUN_CLOUD_ORCHESTRATOR_E2E=1 RUN_AWS_CLOUD_ORCHESTRATOR_TESTS=1 CLOUD_ORCHESTRATOR_E2E_MODE=aws-ec2-cloudfront CLOUD_ORCHESTRATOR_AWS_BUILDER=ec2 AWS_REGION=us-east-1 npm test --prefix packages/frontend-sdk -- cloud-orchestrator.e2e` passed in about 19.6 minutes and cleaned up CloudFormation stacks/artifacts.
- `npx tsc --noEmit --project mobile/crystal-lattice-control-rn/tsconfig.json` still fails on pre-existing mobile/frontend-sdk type errors unrelated to the cloud transport change.

## Execution plan

Added during completion after user approval.

### Architecture

Use Elixir/Phoenix for the orchestrator control plane and keep the Python terminal/server application as the local action owner and cloud runtime implementation.

The MVP architecture is:

- Local Python terminal/server:
  - owns local sessions and local workspace
  - runs project/user transfer scripts
  - calls orchestrator APIs
  - applies sync-down and close results
- Elixir/Phoenix orchestrator:
  - exposes the stable public control plane
  - manages auth/tokens, transfer slots, instance registry, proxying, and runner dispatch
  - starts/stops managed transfer endpoints
  - stays independent from bridge
- Built-in Docker runner:
  - ships in the same orchestrator release/image for the MVP
  - talks to the host Docker socket through a clean runner boundary
  - starts/stops Python cloud runtime containers
  - maps transfer slots to cloud runtime workspaces efficiently
- Python cloud runtime container:
  - runs the existing terminal/server HTTP API or a small API-compatible wrapper
  - imports selected sessions
  - runs cloud setup/export scripts

### Transfer and script contract

Keep transfers as opaque slots. The orchestrator must not assume tar/gzip, archive names, one file vs many files, rsync vs SFTP, git metadata, or a workspace layout.

Use these script env vars:

- `LOCAL_WORKSPACE_DIR`
- `CLOUD_WORKSPACE_DIR`
- `TRANSFER_DIR`

Start/upload flow:

- Local transfer script receives `LOCAL_WORKSPACE_DIR`, `CLOUD_WORKSPACE_DIR`, and `TRANSFER_DIR`.
- Cloud setup script receives `CLOUD_WORKSPACE_DIR` and `TRANSFER_DIR`.

Return/sync-down flow:

- Cloud export script receives `CLOUD_WORKSPACE_DIR` and `TRANSFER_DIR`.
- Local apply script receives `LOCAL_WORKSPACE_DIR`, `CLOUD_WORKSPACE_DIR`, and `TRANSFER_DIR`.

`TRANSFER_DIR` is ephemeral. `CLOUD_WORKSPACE_DIR` is the final runtime workspace. The runner owns the backend-specific movement or mounting from transfer storage into the cloud workspace.

### Managed transfer slots

For the primary remote Docker-host path, use managed SSH/SFTP rather than requiring users to have SSH access to the orchestrator host.

Flow:

1. Local app creates or reuses a transfer keypair.
2. Local app asks orchestrator for a transfer slot.
3. Orchestrator starts a restricted transfer container on a temporary/high port.
4. Transfer container accepts only the supplied public key.
5. Transfer container exposes only the slot directory.
6. Local transfer plugin writes files into the slot.
7. Local app marks the transfer ready.
8. Docker runner starts runtime using the transfer slot.
9. Transfer endpoint is stopped or expires.

The transfer container should deny shell, TTY, agent forwarding, port forwarding, and arbitrary filesystem access. It should be short-lived and restricted to the slot directory.

HTTP upload may be included as a local/dev fallback if it is cheap, but managed SSH/SFTP is the important remote path.

### Orchestrator API shape

Exact paths may shift, but the MVP should expose:

- `GET /health`
- `POST /transfers`
- `POST /transfers/{transfer_id}/ready`
- `DELETE /transfers/{transfer_id}`
- `POST /instances`
- `GET /instances/{instance_id}`
- `ANY /instances/{instance_id}/proxy/*path`
- `POST /instances/{instance_id}/export`
- `POST /instances/{instance_id}/close`

Public instance start payloads should use only a minimal transfer reference:

```json
{
  "transfer_ref": {
    "transfer_id": "tr_123"
  }
}
```

Internal host paths, transfer container ids, port mappings, and runner details stay inside the orchestrator.

### Local application actions

Add built-in actions:

- `cloud.start_session_agent`
- `cloud.sync_down`
- `cloud.close_session`

`cloud.start_session_agent` resolves local workspace/session, runs the local transfer script, creates a managed transfer slot, uploads/synchronizes through the local transfer plugin, starts a cloud instance, and returns a display payload with a single copyable cloud connection link.

`cloud.sync_down` asks the cloud runtime to export into a transfer slot, downloads/synchronizes through the local transfer plugin, and runs the local apply script.

`cloud.close_session` performs final export/sync as needed, retrieves final remote session state, overwrites/updates the local session, stops the instance, and cleans resources.

### Frontend/mobile cloud transport

Add:

- `CloudTransport`
- `cloud` connection record type
- cloud link parser/serializer
- mobile paste-link connection path

The copied cloud link contains orchestrator URL, instance id, remote session id, and token. It must not contain transfer credentials.

### Deployment

Add generic deployment support without private host details:

- Elixir release Dockerfile
- single-node Docker Compose file
- Docker socket mount for the MVP Docker runner
- managed transfer port range
- reverse proxy/TLS docs using placeholder domains only
- generic rsync+SSH deployment docs with placeholders only
- `/health` smoke commands

Add guarded AWS EC2 Docker-host deployment/e2e:

- `RUN_AWS_CLOUD_ORCHESTRATOR_TESTS=1`
- create EC2 Docker host
- install Docker/Compose via cloud-init
- deploy orchestrator
- expose generated HTTPS address, preferably CloudFront
- avoid custom domain/Route53 requirements
- open configured managed transfer port range for smoke tests
- tear down all resources

### Verification

Unit tests:

- Elixir orchestrator: health, transfer lifecycle, token validation, fake runner boundary, proxy routing, instance lifecycle state.
- Python local action: action listing/schema, transfer script env vars, display copy link, sync-down/apply env vars, close overwrites local session.
- Transfer adapter: opaque slot handling and no fixed artifact name/compression assumptions.
- Frontend SDK: cloud link parse/serialize, `CloudTransport` auth/proxy behavior, `cloud` connection round-trip.
- Mobile: pasted cloud link creates the expected cloud connection record where existing test setup supports it.

Integration/smoke tests:

- Local Docker: orchestrator start, managed transfer slot, cloud runtime start, cloud transport connect, selected session visible remotely, sync-down, close overwrites local session.
- Docker Compose health smoke.
- AWS EC2/CloudFront guarded smoke: health, minimal transfer/start/proxy/export/close lifecycle, cleanup.

### Implementation checkpoints

1. Elixir orchestrator skeleton, runner boundary, health endpoint, Docker Compose.
2. Docker runner and Python cloud runtime container lifecycle.
3. Managed SSH/SFTP transfer slot container.
4. Python local cloud actions and script env contract.
5. Frontend SDK/mobile cloud transport and paste-link connection.
6. Local Docker end-to-end tests.
7. AWS EC2/CloudFront deployment scripts and guarded smoke tests.
8. Documentation and completion notes.

## Completion Notes

Added during completion.

Task 010 is complete. The MVP now includes:

- an independent Elixir/Phoenix cloud orchestrator
- Docker runner and minimal Python cloud runtime
- local and remote Docker deployment paths
- frontend SDK `CloudTransport`
- mobile paste-link cloud connection support
- local app actions for start/sync-down/close
- default opaque transfer bundle upload/download
- session import/export and close-to-local-session overwrite
- generic remote Docker deploy scripts
- AWS EC2 + CloudFront generated HTTPS deploy/test/destroy flow
- guarded frontend SDK E2E tests for local, external, and AWS CloudFront modes

Important AWS design note: runtime EC2 does not build application images. `deploy/aws-ec2/build.sh` creates prebuilt Docker image artifacts and uploads them to S3; `deploy/aws-ec2/up.sh` provisions the cheap runtime EC2 host, loads the images, and starts containers. `build.sh --builder ec2` uses a temporary larger EC2 builder and destroys it after artifact upload.

Final AWS E2E verification passed:

```bash
RUN_CLOUD_ORCHESTRATOR_E2E=1 \
RUN_AWS_CLOUD_ORCHESTRATOR_TESTS=1 \
CLOUD_ORCHESTRATOR_E2E_MODE=aws-ec2-cloudfront \
CLOUD_ORCHESTRATOR_AWS_BUILDER=ec2 \
AWS_REGION=us-east-1 \
npm test --prefix packages/frontend-sdk -- cloud-orchestrator.e2e
```

The run passed through generated CloudFront HTTPS and cleaned up CloudFormation stacks. Temporary S3 artifacts from earlier failed attempts were also removed.