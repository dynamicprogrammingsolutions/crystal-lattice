# Remote Docker Orchestrator MVP
Build the first usable end-to-end version: a Dockerized orchestrator deployable on a remote Docker host with a stable secure address, local Docker testing support, an AWS EC2 Docker-host deployment/e2e path, a cloud transport, and an action that starts a cloud agent for one session and returns a copyable connection link.

## Requirements checklist

- [ ] Add a standalone orchestrator service independent from bridge.
- [ ] Add a Docker backend for cloud agents, usable both locally for testing and on a remote Docker host.
- [ ] Add Docker Compose and deployment docs for a single-node orchestrator reachable through a stable secure address.
- [ ] Add an AWS EC2 Docker-host deployment/e2e path that can be run with AWS CLI credentials and tears resources down after smoke tests.
- [ ] Expose the AWS e2e deployment through a generated CloudFront HTTPS address by default, without requiring a custom subdomain.
- [ ] Optionally support generic remote-host reverse proxy/subdomain deployment with Nginx/Certbot or equivalent docs.
- [ ] Add a `/health` endpoint and smoke test path for orchestrator deployment.
- [ ] Add a cloud transport and `cloud` connection record type in the frontend SDK/mobile.
- [ ] Add terminal/server startup configuration for orchestrator URL and access token/secret.
- [ ] Add an application action, conventionally `cloud.start_session_agent`, that starts a cloud agent for one selected session.
- [ ] Implement project-defined transfer/setup/export/apply scripts using `LOCAL_WORKSPACE_DIR`, `CLOUD_WORKSPACE_DIR`, and `TRANSFER_DIR`.
- [ ] Transfer the selected session and project files/metadata through an opaque transfer slot to the cloud runtime.
- [ ] Import the session into the cloud runtime and expose it through the cloud transport.
- [ ] Return a display payload with a single copyable cloud connection link containing URL/token/session target.
- [ ] Support transferring cloud workspace changes back to the original local directory at any time.
- [ ] Support closing the remote session and overwriting/updating the local session with the remote session state.
- [ ] Add enough generic documentation and script hooks so a private rsync+SSH deploy command can be assembled in the current environment without committing private host/domain details.

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
