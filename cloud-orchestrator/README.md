# Cloud Orchestrator

Cloud Orchestrator is the control plane for cloud agent sessions. It is independent from the bridge service.

The MVP service is an Elixir/Phoenix application with a built-in Docker runner. The Docker runner is bundled into the same release image, but it is isolated behind a runner behaviour so later AWS Fargate, Kubernetes, or remote runner implementations can replace it without changing the public API.

## Local Docker

```bash
cd cloud-orchestrator
docker build -t cloud-agent-runtime:latest runtime/python
docker compose -f docker-compose.single-node.yml up --build
curl http://127.0.0.1:4100/health
```

The single-node Docker runner mounts `/var/run/docker.sock`, so the orchestrator container can start sibling cloud runtime containers. Treat access to the orchestrator as privileged and run it behind TLS in remote deployments.

Set `CLOUD_ORCHESTRATOR_CONTROL_TOKEN` in remote deployments. Control-plane calls must then include `Authorization: Bearer <token>`.

For a host-local manual smoke without Compose:

```bash
docker build -t cloud-agent-runtime:latest runtime/python

PORT=4105 \
CLOUD_ORCHESTRATOR_RUNNER=docker \
CLOUD_ORCHESTRATOR_PUBLIC_URL=http://127.0.0.1:4105 \
CLOUD_ORCHESTRATOR_TOKEN_SECRET=manual-secret \
CLOUD_ORCHESTRATOR_DATA_DIR=/tmp/cloud-orchestrator-manual \
CLOUD_ORCHESTRATOR_HOST_DATA_DIR=/tmp/cloud-orchestrator-manual \
mix run --no-halt
```

Then start a local terminal/server configured with `plugins.cloud_agent_app_plugin.CloudAgentAppPlugin` and `application.cloud_agent.orchestrator_url` pointing at `http://127.0.0.1:4105`. The `cloud.start_session_agent` action returns a `crystal-lattice-cloud://connect?...` link that can be pasted into the mobile app's Cloud Agent Link connection flow.

The same local flow supports:

- proxying to the runtime through `CloudTransport`
- `cloud.sync_down` for default workspace export/download/apply
- `cloud.close_session` to stop the runtime and overwrite/update the local session with remote session state

## Remote Docker Host

Generic deployment shape:

```bash
CLOUD_ORCHESTRATOR_REMOTE=user@example-host \
CLOUD_ORCHESTRATOR_PUBLIC_URL=https://cloud.example.com \
./cloud-orchestrator/deploy/remote-docker/deploy.sh
curl https://cloud.example.com/health
```

Use your own host, username, and domain. Do not commit environment-specific deployment commands into the repository.

The deployment script is intentionally generic. It copies `cloud-orchestrator/` to the remote host, builds `cloud-agent-runtime:latest`, builds the orchestrator image, starts Compose, and leaves private host/domain details in your shell environment rather than in committed files.

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

If managed SSH/SFTP transfer slots are enabled, also expose the configured transfer port range, for example `22000-22099`, to clients that will upload/download workspace data.

## Transfer Contract

Transfers are opaque slots. The orchestrator does not assume tar/gzip, file names, rsync, SFTP, git, or a fixed workspace layout.

Project scripts receive:

- `LOCAL_WORKSPACE_DIR`
- `CLOUD_WORKSPACE_DIR`
- `TRANSFER_DIR`

The local transfer script receives all three. The cloud setup script receives `CLOUD_WORKSPACE_DIR` and `TRANSFER_DIR`. Return/sync-down uses the same names in reverse with a cloud export script and local apply script.

## API Smoke

```bash
curl http://127.0.0.1:4100/health

transfer_id="$(
  curl -fsS -X POST http://127.0.0.1:4100/transfers \
    -H 'content-type: application/json' \
    -d '{"direction":"upload","method":"managed_ssh"}' |
  python3 -c 'import json,sys; print(json.load(sys.stdin)["transfer_id"])'
)"

curl -fsS -X POST "http://127.0.0.1:4100/transfers/${transfer_id}/ready"
curl -fsS -X POST http://127.0.0.1:4100/instances \
  -H 'content-type: application/json' \
  -d "{\"session_id\":\"demo\",\"transfer_ref\":{\"transfer_id\":\"${transfer_id}\"}}"
```

## AWS EC2 Docker Host

The default AWS path provisions an EC2 Docker host and exposes the orchestrator through a generated HTTPS address. It is guarded by `RUN_AWS_CLOUD_ORCHESTRATOR_TESTS=1` and should tear down resources after smoke tests.

See `deploy/aws-ec2/README.md`.

## Frontend SDK E2E

Local orchestrator mode:

```bash
RUN_CLOUD_ORCHESTRATOR_E2E=1 npm test --prefix packages/frontend-sdk -- cloud-orchestrator.e2e
```

External deployed orchestrator mode:

```bash
RUN_CLOUD_ORCHESTRATOR_E2E=1 \
CLOUD_ORCHESTRATOR_E2E_MODE=external \
CLOUD_ORCHESTRATOR_E2E_URL=https://cloud.example.com \
npm test --prefix packages/frontend-sdk -- cloud-orchestrator.e2e
```

If the external orchestrator uses a control-plane token, also set `CLOUD_ORCHESTRATOR_E2E_CONTROL_TOKEN`.