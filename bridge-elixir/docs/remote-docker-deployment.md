# Remote Docker deployment

The Bridge service includes a reusable deployment command for a single remote
Docker host. The command uploads a clean source bundle, builds and recreates
one bridge node, and verifies the origin and public capability endpoints.

Use a gitignored local wrapper for a concrete hostname, SSH identity, public
URL, and signing secret. Do not commit deployment credentials.

## Required configuration

From the repository root:

```bash
BRIDGE_REMOTE=user@example-host \
BRIDGE_PUBLIC_URL=https://bridge.example.com \
BRIDGE_TOKEN_SECRET=replace-with-a-stable-random-secret \
./bridge-elixir/deploy/remote-docker/deploy.sh
```

`BRIDGE_TOKEN_SECRET` signs saved pairing credentials. Keep the same value
across deployments. Replacing it requires frontends to pair again.

Common optional settings:

```bash
BRIDGE_REMOTE_DIR=bridge-elixir
BRIDGE_COMPOSE_PROJECT=bridgeelixir
BRIDGE_BIND_HOST=127.0.0.1
BRIDGE_PORT=4000
SSH_OPTS="-i /absolute/path/to/key -o BatchMode=yes"
```

Use an explicit `BRIDGE_COMPOSE_PROJECT` when adopting a container created by
an older Compose installation. Every later deployment must use the same
project name.

`BRIDGE_BIND_HOST=127.0.0.1` is appropriate when Nginx or another edge on the
same host is the only public entry point. Keep `0.0.0.0` only when direct
trusted-network access to the Cowboy port is intentional.

## Gitignored wrapper

A machine-specific wrapper can persist concrete values while the reusable
script remains committed:

```bash
#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
secret_file="${repo_root}/.crystal/bridge-token-secret"

if [[ ! -s "$secret_file" ]]; then
  umask 077
  openssl rand -hex 32 >"$secret_file"
fi

BRIDGE_REMOTE=user@example-host \
BRIDGE_PUBLIC_URL=https://bridge.example.com \
BRIDGE_COMPOSE_PROJECT=bridgeelixir \
BRIDGE_BIND_HOST=127.0.0.1 \
BRIDGE_TOKEN_SECRET="$(<"$secret_file")" \
SSH_OPTS="-i ${HOME}/.ssh/bridge.pem -o BatchMode=yes" \
"${repo_root}/bridge-elixir/deploy/remote-docker/deploy.sh"
```

Keep the wrapper and secret file outside Git with permissions `0700` and
`0600`, respectively. Back up the signing secret securely: losing it makes
existing saved pairings unverifiable after the next deployment.

## Deployment behavior

The command:

1. requires the stable signing secret and the committed Mix lockfile;
2. archives the Bridge service without local builds or dependency caches;
3. uploads the source and a private runtime environment file;
4. cleans the previous remote source tree so removed files cannot linger;
5. selects `docker compose` or `docker-compose`;
6. builds before replacing the running single-node container;
7. waits for origin health and HTTP v1 capabilities;
8. verifies the public health and capability endpoints.

Set `BRIDGE_VERIFY_LARGE_BODY=1` to require a 1.2 MB request to pass the public
edge and reach the bridge. A `413` response indicates that the edge request
limit is too small.

Set `BRIDGE_RUN_EXTERNAL_E2E=1` to run the frontend SDK bridge E2E against the
deployed public endpoint after the deployment checks pass.

## Edge requirements

An internet-facing bridge requires HTTPS/WSS. The edge must:

- forward WebSocket upgrades, query strings, and all HTTP methods;
- retain `Authorization`, `X-Crystal-Bridge-Token`, and
  `X-Crystal-Bridge-Body-Present`;
- accept bodies up to the configured bridge limit;
- disable request/response buffering for streamed transfer paths;
- disable caching;
- use timeouts at least as long as the bridge transfer timeout.

See `deploy/remote-docker/nginx-site.example` for a complete Nginx example.

After changing Nginx:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## Verification

```bash
curl -fsS https://bridge.example.com/health
curl -fsS https://bridge.example.com/bridge/v1/capabilities
```

The capability response advertises HTTP protocol version 1. For full hosted
verification:

```bash
BRIDGE_E2E_MODE=external \
BRIDGE_E2E_URL=wss://bridge.example.com/ws/websocket \
npm --workspace @crystal-lattice/frontend-sdk run integration:bridge
```

External mode verifies legacy WebSocket, HTTP-only, and hybrid operation
without restarting the independently managed bridge.