# Remote Docker Deployment

This deployment path copies `cloud-orchestrator/` to a remote Docker host, builds the orchestrator image, builds the Python cloud runtime image, and starts the single-node Compose service.

Required:

- SSH access to a host with Docker and Docker Compose
- a stable public URL that reaches the orchestrator HTTP port through HTTPS or a trusted reverse proxy

Example:

```bash
CLOUD_ORCHESTRATOR_REMOTE=user@example-host \
CLOUD_ORCHESTRATOR_PUBLIC_URL=https://cloud.example.com \
./cloud-orchestrator/deploy/remote-docker/deploy.sh
```

Optional:

```bash
CLOUD_ORCHESTRATOR_REMOTE_DIR=~/cloud-orchestrator
CLOUD_ORCHESTRATOR_HOST_DATA_DIR=/var/lib/cloud-orchestrator
CLOUD_ORCHESTRATOR_CONTROL_TOKEN=replace-with-a-secret-token
CLOUD_ORCHESTRATOR_TOKEN_SECRET=replace-with-a-secret-signing-key
CLOUD_ORCHESTRATOR_DOCKER_PROXY_HOST=host.docker.internal
CLOUD_ORCHESTRATOR_DOCKER_BIND_HOST=172.17.0.1
```

After deployment:

```bash
curl -fsS https://cloud.example.com/health
```

The host data directory must be an absolute path. The orchestrator container passes this path to sibling runtime containers through Docker bind mounts.

On Linux Docker hosts, the deploy script defaults runtime port binding to `172.17.0.1` and runtime proxying to `host.docker.internal`. That keeps runtime containers reachable from the orchestrator container without publishing per-session runtime ports on all public interfaces. Override both values if your Docker bridge gateway differs.

The deploy script auto-selects:

- `docker compose` with `docker-compose.single-node.yml` on modern Docker
- `docker-compose` with `docker-compose.single-node-v2.yml` on older hosts