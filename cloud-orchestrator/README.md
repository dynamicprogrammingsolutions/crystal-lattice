# Cloud Orchestrator

Cloud Orchestrator is the control plane for cloud agent sessions. It is independent from the bridge service.

The MVP service is an Elixir/Phoenix application with a built-in Docker runner. The Docker runner is bundled into the same release image, but it is isolated behind a runner behaviour so later AWS Fargate, Kubernetes, or remote runner implementations can replace it without changing the public API.

Conceptually:

- The orchestrator is the always-reachable control plane. It validates tokens, stores instance metadata, and delegates backend-specific work.
- The runner owns lifecycle and request handling for an instance. The Docker runner starts a long-running runtime container and proxies requests to it.
- The runtime is the process inside the container. The Python runtime boots a real `AgentApplication` from transferred cloud config and session storage.

## Local Docker

```bash
cd cloud-orchestrator
cd ..
docker build -t cloud-agent-runtime:latest -f cloud-orchestrator/runtime/python/Dockerfile .
cd cloud-orchestrator
docker compose -f docker-compose.single-node.yml up --build
curl http://127.0.0.1:4100/health
```

The single-node Docker runner mounts `/var/run/docker.sock`, so the orchestrator container can start sibling cloud runtime containers. Treat access to the orchestrator as privileged and run it behind TLS in remote deployments.

Set `CLOUD_ORCHESTRATOR_CONTROL_TOKEN` in remote deployments. Control-plane calls must then include `Authorization: Bearer <token>`.

For a host-local manual smoke without Compose:

```bash
docker build -t cloud-agent-runtime:latest -f cloud-orchestrator/runtime/python/Dockerfile .
docker build -t cloud-agent-transfer-ssh:latest cloud-orchestrator/transfer/managed-ssh

PORT=4105 \
CLOUD_ORCHESTRATOR_RUNNER=docker \
CLOUD_ORCHESTRATOR_PUBLIC_URL=http://127.0.0.1:4105 \
CLOUD_ORCHESTRATOR_TOKEN_SECRET=manual-secret \
CLOUD_ORCHESTRATOR_DATA_DIR=/tmp/cloud-orchestrator-manual \
CLOUD_ORCHESTRATOR_HOST_DATA_DIR=/tmp/cloud-orchestrator-manual \
mix run --no-halt
```

Then start a local terminal/server configured with `path:${env:BUILTIN_PLUGINS}/cloud-agent-app` and `application.cloud_agent.orchestrator_url` pointing at `http://127.0.0.1:4105`. The `cloud.start_session_agent` action returns a `crystal-lattice-cloud://connect?...` link that can be pasted into the mobile app's Cloud Agent Link connection flow. New links are connection-scoped and include `connection_id`; legacy instance-scoped links with only `instance_id` continue to work during migration.

The same local flow supports:

- proxying to the runtime through `CloudTransport`
- one UI cloud connection routing to multiple cloud session instances
- `cloud.sync_down` for explicit cloud export, managed-SSH rsync download, and local apply
- `cloud.close_session` for final sync, stop, and local session update

## Remote Docker Host

Generic deployment shape:

```bash
CLOUD_ORCHESTRATOR_REMOTE=user@example-host \
CLOUD_ORCHESTRATOR_PUBLIC_URL=https://cloud.example.com \
./cloud-orchestrator/deploy/remote-docker/deploy.sh
curl https://cloud.example.com/health
```

Use your own host, username, and domain. Do not commit environment-specific deployment commands into the repository.

The deployment script is intentionally generic. It copies the repository paths needed by the orchestrator/runtime to the remote host, builds `cloud-agent-runtime:latest`, builds `cloud-agent-transfer-ssh:latest`, builds the orchestrator image, starts Compose, and leaves private host/domain details in your shell environment rather than in committed files.

On Linux Docker hosts, the deploy script defaults runtime ports to bind on the Docker bridge gateway (`172.17.0.1`) and has the orchestrator proxy to `host.docker.internal`. This keeps per-session runtime containers off public interfaces while still reachable from the orchestrator container.

For a reverse proxy, forward HTTPS traffic to the internal orchestrator HTTP port:

```nginx
server {
  listen 443 ssl http2;
  server_name cloud.example.com;

  location / {
    proxy_pass http://127.0.0.1:4100;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto https;
  }
}
```

Expose the configured managed-SSH transfer port range, for example `22000-22099`, to clients that will upload/download workspace data with rsync over SSH. When the public HTTP URL is not the same host clients should use for those SSH ports, set `CLOUD_ORCHESTRATOR_TRANSFER_PUBLIC_HOST` to the SSH-reachable host. If it is unset, managed SSH endpoints fall back to the host from `CLOUD_ORCHESTRATOR_PUBLIC_URL`.

## Transfer Contract

Transfers are opaque slots. The orchestrator does not assume tar/gzip, archive file names, git metadata, or a fixed workspace layout. The built-in byte transport is managed SSH, and the local app drives rsync through a platform adapter script.

Project scripts receive:

- `LOCAL_WORKSPACE_DIR`
- `CLOUD_WORKSPACE_DIR`
- `TRANSFER_DIR`

The local transfer script receives all three. The cloud setup script receives `CLOUD_WORKSPACE_DIR` and `TRANSFER_DIR`. Return/sync-down uses the same names in reverse with a cloud export script and local apply script. These scripts choose file contents only; the software moves bytes between transfer slots.

## Runtime Config, Assets, And Env

When `cloud.start_session_agent` runs, the local application writes a portable
cloud runtime bundle under `.cloud-agent/` in the transfer payload:

```text
.cloud-agent/
  config/
    config.json
    assets/
  env/
    runtime.env
    runtime.env.d/
  sessions/
```

The generated `config/config.json` is based on the local raw config, but the
local `application.cloud_agent` control-plane section is removed and runtime
storage such as `plugin_cache_dir` is pointed at the cloud instance state
directory. Plugin-owned fields such as `working_directory`, `allowed_paths`,
tool paths, provider settings, and plugin path descriptors are preserved.

`CONFIG_DIR` assets are copied broadly into `config/assets/`. Copy policy lives
in `application.cloud_agent.config_assets`, including exclude patterns and a
per-top-level-entry size limit. This lets projects exclude `.env`,
`.plugin_cache`, logs, or other bulky/private entries without the runtime
hardcoding project-specific paths.

Runtime env values are written through `application.cloud_agent.runtime_env`.
By default, env placeholders referenced by config can be transferred by name,
with explicit excludes for local control-plane and runtime-owned variables.
Secret values are written only into runtime env files, never into action display
payloads.

The Docker runner mounts each instance at:

```text
/cloud-agent/instance/
  workspace/
  sessions/
  config/
  env/
  logs/
  state/
```

and sets `CONFIG_DIR=/cloud-agent/instance/config/assets` and
`WORKING_DIR=/cloud-agent/instance/workspace`.

## API Smoke

```bash
curl http://127.0.0.1:4100/health

transfer_id="$(
  curl -fsS -X POST http://127.0.0.1:4100/transfers \
    -H 'content-type: application/json' \
    -d '{"direction":"upload","method":"managed_ssh","public_key":"ssh-ed25519 AAAA... user@example"}' |
  python3 -c 'import json,sys; print(json.load(sys.stdin)["transfer_id"])'
)"

curl -fsS -X POST "http://127.0.0.1:4100/transfers/${transfer_id}/ready"
curl -fsS -X POST http://127.0.0.1:4100/instances \
  -H 'content-type: application/json' \
  -d "{\"session_id\":\"demo\",\"transfer_ref\":{\"transfer_id\":\"${transfer_id}\"}}"
```

## AWS EC2 Docker Host

The default AWS path provisions an EC2 Docker host and exposes the orchestrator HTTP API through a generated CloudFront HTTPS address. Managed SSH transfer slots are advertised with the EC2 origin public DNS so local apps can use CloudFront for HTTP while rsync connects directly to the EC2 transfer ports. It is guarded by `ALLOW_AWS_DEPLOY=1` and should tear down resources after smoke tests.

See `deploy/aws-ec2/README.md`.

## Frontend SDK E2E

Local orchestrator mode:

```bash
RUN_CLOUD_ORCHESTRATOR_E2E=1 npm test --prefix packages/frontend-sdk -- cloud-orchestrator.e2e
```

Real OpenRouter tool-loop E2E is opt-in:

```bash
RUN_CLOUD_ORCHESTRATOR_E2E=1 \
RUN_CLOUD_ORCHESTRATOR_OPENROUTER_E2E=1 \
OPENROUTER_API_KEY=... \
npm test --prefix packages/frontend-sdk -- cloud-orchestrator.e2e
```

Set `CLOUD_ORCHESTRATOR_OPENROUTER_MODEL` to choose the model; the test uses a
cheap tool-capable fallback when unset.

External deployed orchestrator mode:

```bash
RUN_CLOUD_ORCHESTRATOR_E2E=1 \
CLOUD_ORCHESTRATOR_E2E_MODE=external \
CLOUD_ORCHESTRATOR_E2E_URL=https://cloud.example.com \
npm test --prefix packages/frontend-sdk -- cloud-orchestrator.e2e
```

If the external orchestrator uses a control-plane token, also set `CLOUD_ORCHESTRATOR_E2E_CONTROL_TOKEN`.