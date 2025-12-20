# Bridge Service – Production Deployment Guide

This document describes how to deploy the Bridge service in production using Docker.

It focuses on:

- Single-node deployments (for simple or lab setups)
- Multi-node clustered deployments with HAProxy
- Where and how to terminate TLS

Internal TLS directly in the Elixir app is **not** enabled by default. At the end
of this document there is a short section describing what would need to be changed
if you decide to add it later.

---

## 1. Prerequisites

- **Docker** and **Docker Compose / docker compose** installed
- A host or VM where you can open ports for:
  - The public WebSocket endpoint (e.g. 4000 or 443)
  - Optional: HAProxy stats (default 8404)
- For TLS:
  - A domain name (e.g. `bridge.example.com`)
  - A valid certificate and private key (e.g. from Let’s Encrypt)

The bridge is a stateful WebSocket relay. You should plan to run at least two
nodes for high availability in production.

---

## 2. Environment variables

The bridge behavior is controlled by environment variables. The most important
ones for deployment are:

### Core

- `MIX_ENV` – should be `prod` in production.
- `PORT` – HTTP port the Phoenix endpoint listens on inside the container.
  - Single-node default (in this repo): `4000`.
  - Cluster nodes in `docker-compose.yml`: `4001`, `4002`, …

### Clustering (multi-node only)

Used by [libcluster](https://hexdocs.pm/libcluster/) when nodes run in
distributed mode:

- `NODE_NAME` – base node name. In Docker this becomes something like
  `bridge@bridge-node-1` based on the hostname.
- `COOKIE` – Erlang distribution cookie. **Must be the same on all nodes**, and
  should be treated as a secret.
- `GOSSIP_PORT` – UDP port used by the Gossip strategy (default `45892`).
- `GOSSIP_MULTICAST_ADDR` – Multicast address used for gossip (default `230.1.1.251`).

These are already wired in `config/config.exs` and the provided
`docker-compose.yml`.

### Pairing & session behavior

Configured in `config/config.exs`:

- `PAIRING_CODE_TTL` – seconds before a pairing code expires (default `300`).
- `MAX_PAIRING_ATTEMPTS` – max code submissions per client (default `3`).
- `SESSION_TIMEOUT` – seconds before an inactive session is cleaned up (default `3600`).

### TLS-related variables (for future internal TLS)

These are **not used by default** but are referenced in `BRIDGE_PLAN.md` and in
the example config snippet in `README.md`:

- `TLS_ENABLED` – if set to `true`/`1`, internal TLS could be enabled.
- `TLS_CERT_PATH` – path to a certificate file inside the container.
- `TLS_KEY_PATH` – path to the private key file inside the container.

See [Section 7](#7-future-adding-internal-tls) for what would need to change in
the code base to support these.

---

## 3. Single-node deployment

This is the simplest way to run the bridge: one container, one HTTP endpoint.
Use this for development, labs, or small internal deployments.

### 3.0. Copying `bridge-elixir` to the server (rsync)

For a simple test or single-node deployment, a common pattern is:

1. Develop locally.
2. `rsync` the `bridge-elixir` directory to your server.
3. Run the Docker Compose commands on the server.

From the **repository root on your local machine**, run:

```bash
cd /path/to/ai-agent-platform

# Replace user@server with your SSH user and hostname/IP.
rsync -av --exclude '_build'  --exclude 'deps'  bridge-elixir/ user@server:~/bridge-elixir/
```

Then SSH into the server and continue with the Docker commands below:

```bash
ssh user@server
cd ~/bridge-elixir
```

### 3.1. Single node, HTTP only (no TLS)

Use the provided `docker-compose.single-node.yml`:

```bash
cd bridge-elixir

# Start single-node bridge
docker compose -f docker-compose.single-node.yml up -d
# With older docker:
docker-compose -f docker-compose.single-node-v2.yml up -d

# Or, if your environment uses docker-compose v1:
# docker-compose -f docker-compose.single-node.yml up -d

# Check health
curl http://localhost:4000/health
```

This starts one bridge node listening on port **4000** (HTTP only). WebSocket
clients should connect to:

```text
ws://<host>:4000/ws/websocket?type=server
ws://<host>:4000/ws/websocket?type=app
```

> **Security note:** HTTP-only is suitable only for trusted networks (e.g. a lab
> or VPN). For internet-facing deployments, terminate TLS in front of the
> container (next section) or add internal TLS later.

### 3.2. Single node behind an external TLS terminator (recommended)

In many production setups you will terminate HTTPS/TLS at an external reverse
proxy or load balancer (Nginx, Traefik, AWS ALB, Cloudflare, …). The bridge
container remains HTTP-only.

Below are step-by-step instructions for integrating with an **existing Nginx**
instance on the same server, first with HTTP-only proxying, then adding TLS via
Let’s Encrypt.

#### 3.2.1. Add HTTP proxy in existing Nginx (no TLS yet)

1. Ensure the bridge is running on the server (HTTP-only single-node):

   ```bash
   cd ~/bridge-elixir
   docker compose -f docker-compose.single-node.yml up -d
   # or: docker-compose -f docker-compose.single-node.yml up -d

   curl http://localhost:4000/health
   ```

2. On the server, edit your Nginx config (for example
   `/etc/nginx/sites-available/bridge.conf`), and add a server block for your
   bridge subdomain (e.g. `bridge.example.com`):

   ```nginx
   server {
     listen 80;
     server_name bridge.example.com;

     location / {
       proxy_pass http://127.0.0.1:4000;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection "upgrade";
       proxy_set_header Host $host;
     }
   }
   ```

   - If Nginx runs in Docker and the bridge container is on the same Docker
     network, you can use `proxy_pass http://bridge:4000;` instead of
     `127.0.0.1`.

3. Enable the site and reload Nginx:

   ```bash
   # Example for Debian/Ubuntu layout
   sudo ln -s /etc/nginx/sites-available/bridge.conf /etc/nginx/sites-enabled/bridge.conf
   sudo nginx -t   # verify config
   sudo systemctl reload nginx
   ```

4. Test HTTP access from your workstation:

   ```bash
   curl http://bridge.example.com/health
   ```

   You should see the same JSON as when calling `http://localhost:4000/health`
   on the server.

At this point, WebSocket clients can connect over **plain ws://**:

```text
ws://bridge.example.com/ws/websocket?type=server
ws://bridge.example.com/ws/websocket?type=app
```

#### 3.2.2. Add TLS using Let’s Encrypt (Certbot + Nginx)

Once the HTTP proxy is working, you can obtain and configure a TLS certificate
for `bridge.example.com` using Let’s Encrypt.

1. Install Certbot and the Nginx plugin (example for Debian/Ubuntu):

   ```bash
   sudo apt-get update
   sudo apt-get install -y certbot python3-certbot-nginx
   ```

   On other distros the package names may differ (e.g. `certbot-nginx`).

2. Run Certbot for your bridge subdomain:

   ```bash
   sudo certbot --nginx -d bridge.example.com
   ```

   - Certbot will:
     - Detect the existing `server_name bridge.example.com;` block.
     - Perform HTTP-01 validation via that server.
     - Optionally create a new HTTPS (`listen 443 ssl`) server block and
       redirect HTTP to HTTPS.

3. After Certbot finishes, your Nginx config for `bridge.example.com` will
   typically have:

   - A `server` block on port 80 that redirects to HTTPS.
   - A `server` block on port 443 with `ssl_certificate` / `ssl_certificate_key`
     lines and the same `location / { proxy_pass ... }` stanza.

4. Reload Nginx (Certbot usually does this automatically, but you can verify):

   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

5. Test HTTPS access and WebSockets:

   ```bash
   curl https://bridge.example.com/health
   ```

   WebSocket clients should now use **wss://**:

   ```text
   wss://bridge.example.com/ws/websocket?type=server
   wss://bridge.example.com/ws/websocket?type=app
   ```

6. Start your Python agent server pointed at the bridge.

   On the machine running your Python `agent_terminal_app` (this can be
   separate from the bridge host), start it with the `--bridge-url` pointing to
   the secure WebSocket endpoint you just configured:

   ```bash
   cd /path/to/ai-agent-platform/application/python

   python -m agent_terminal_app \
     --host 0.0.0.0 \
     --port 9000 \
     --bridge-url wss://bridge.example.com/ws/websocket \
     --bridge-display-name "My Agent Server" \
     --bridge-location "Office"
   ```

   - Use `wss://bridge.example.com/ws/websocket` for `--bridge-url` (note the
     `wss://` scheme and the `/ws/websocket` path used by the Phoenix bridge).
   - `--bridge-display-name` and `--bridge-location` are optional and control
     how this server appears in the mobile app when browsing available
     servers.

If you prefer to manage TLS manually instead of using Certbot’s Nginx
integration, you can use a configuration similar to this (for reference only):

```nginx
events {}

http {
  upstream bridge_upstream {
    server 127.0.0.1:4000;
  }

  server {
    listen 443 ssl;
    server_name bridge.example.com;

    ssl_certificate     /etc/nginx/certs/fullchain.pem;
    ssl_certificate_key /etc/nginx/certs/privkey.pem;

    location / {
      proxy_pass http://bridge_upstream;
      proxy_http_version 1.1;
      proxy_set_header Upgrade $http_upgrade;
      proxy_set_header Connection "upgrade";
      proxy_set_header Host $host;
    }
  }
}
```

This is the **recommended** approach for most deployments: keep the bridge HTTP
inside your infrastructure and terminate TLS at the edge (Nginx, HAProxy, or a
cloud load balancer).

---

## 4. Multi-node (clustered) deployment

For high availability and scalability, you can run multiple bridge nodes in a
cluster behind HAProxy. The repository already includes a working Docker
Compose-based cluster setup.

### 4.1. HTTP-only cluster behind HAProxy

The default `docker-compose.yml` starts:

- `bridge-node-1` – Elixir node on port `4001`
- `bridge-node-2` – Elixir node on port `4002`
- `haproxy` – load balancer on port `4000` (HTTP)

HAProxy distributes traffic across the bridge nodes and performs health checks
on `/health`.

Start the cluster:

```bash
cd bridge-elixir

# Start 2-node cluster + HAProxy (HTTP only)
docker compose up -d

# Or:
# docker-compose up -d

# Check cluster health through HAProxy
curl http://localhost:4000/health
```

WebSocket clients should use the HAProxy entrypoint:

```text
ws://<host>:4000/ws/websocket?type=server
ws://<host>:4000/ws/websocket?type=app
```

> **Note:** individual node ports (4001, 4002) are intended for internal use
> only and should not be exposed to the public internet.

### 4.2. TLS termination at HAProxy (wss://)

If you want TLS termination at HAProxy, use the provided `haproxy-ssl.cfg` and
the override compose file `docker-compose.cluster-ssl.yml`.

1. Create a PEM bundle that includes your private key and certificate chain, e.g.:

   ```bash
   cd bridge-elixir
   mkdir -p certs
   cat privkey.pem fullchain.pem > certs/bridge.pem
   ```

2. Start the cluster with the SSL override:

   ```bash
   cd bridge-elixir

   # Using docker compose v2
   docker compose -f docker-compose.yml -f docker-compose.cluster-ssl.yml up -d

   # Or with docker-compose v1
   # docker-compose -f docker-compose.yml -f docker-compose.cluster-ssl.yml up -d

   # Check health
   curl http://localhost:4000/health
   ```

3. HAProxy will now listen on port **4000** with TLS, using
   `/usr/local/etc/haproxy/certs/bridge.pem` inside the container.

Clients connect via:

```text
wss://bridge.example.com:4000/ws/websocket?type=server
wss://bridge.example.com:4000/ws/websocket?type=app
```

You can also change HAProxy to listen on `443` instead of `4000` by editing
`haproxy-ssl.cfg`.

### 4.3. Scaling the cluster

The default compose file defines two nodes explicitly. To add more nodes you can:

- Duplicate the `bridge-node-2` service as `bridge-node-3`, `bridge-node-4`,
  etc., each with a unique `PORT` and IP in the custom `bridge_network`
  subnet, then add matching `server` lines in `haproxy.cfg` / `haproxy-ssl.cfg`.

For more dynamic scaling, you’d typically move to a Kubernetes-based deployment
with libcluster’s DNS or Kubernetes strategies (see `BRIDGE_PLAN.md`).

---

## 5. Health checks and monitoring

The bridge exposes a simple JSON health endpoint on each node and through
HAProxy:

```bash
curl http://localhost:4000/health
```

Example response:

```json
{
  "status": "healthy",
  "node": "bridge@bridge-node-1",
  "cluster_size": 2,
  "active_servers": 3,
  "active_sessions": 5
}
```

### HAProxy stats

The default cluster expose HAProxy stats on port `8404`:

```text
http://<host>:8404/stats
```

Use this for basic visibility into backend health and connection counts.

### External load balancers

If you place a cloud load balancer in front of HAProxy (or directly in front of
single-node bridge), configure its health check to call:

```text
GET /health HTTP/1.1
Host: bridge.example.com
```

and require a `200` status code.

---

## 6. Security recommendations

1. **Expose only the entrypoint.**
   - For a cluster, expose only HAProxy’s public port (4000 or 443).
   - Do **not** expose the internal node ports (4001, 4002, …) publicly.

2. **Protect the Erlang cookie.**
   - The `COOKIE` environment variable controls which nodes can join the
     Erlang cluster.
   - Use a long, random value and treat it as a secret.

3. **Use TLS for untrusted networks.**
   - For internet-facing deployments, always terminate TLS at a reverse proxy
     or HAProxy, or (in the future) inside Phoenix.

4. **Tune pairing & session limits.**
   - Adjust `PAIRING_CODE_TTL`, `MAX_PAIRING_ATTEMPTS`, and `SESSION_TIMEOUT`
     for your traffic patterns and risk tolerance.

5. **Set resource limits.**
   - In Docker Compose you can use the `deploy.resources` section (or
     Kubernetes `resources`) to cap CPU/RAM usage.

6. **Centralize logs and metrics.**
   - Forward container logs to a centralized system (ELK, Loki, etc.).
   - Consider adding Prometheus metrics in a future iteration (see `BRIDGE_PLAN.md`).

---

## 7. Future: adding internal TLS (not implemented yet)

Right now, the recommended and supported approach is to terminate TLS at a
reverse proxy or HAProxy. Internal TLS directly in the Phoenix `Bridge.Endpoint`
is **not wired up** in `config/runtime.exs`.

If you decide you want the Elixir app itself to handle TLS, you would need to:

1. **Decide on environment variables** (these are already mentioned in
   `BRIDGE_PLAN.md`):

   ```bash
   TLS_ENABLED=true
   TLS_CERT_PATH=/path/to/cert.pem
   TLS_KEY_PATH=/path/to/key.pem
   ```

2. **Update `config/runtime.exs`** to configure `https` for `Bridge.Endpoint`
   when `TLS_ENABLED` is set. For example:

   ```elixir
   import Config

   if System.get_env("TLS_ENABLED") in ["true", "1"] do
     port = String.to_integer(System.get_env("PORT") || "4000")

     config :bridge, Bridge.Endpoint,
       https: [
         port: port,
         cipher_suite: :strong,
         keyfile: System.fetch_env!("TLS_KEY_PATH"),
         certfile: System.fetch_env!("TLS_CERT_PATH")
       ],
       http: false
   end
   ```

   This snippet is **not** present in the code base yet; it’s an example of the
   type of change that would be required.

3. **Adjust deployment:**
   - Make sure the certificate and key files are available inside the container
     at the paths specified by `TLS_CERT_PATH` / `TLS_KEY_PATH` (e.g. via
     Docker volume mounts or baked into the image).
   - Expose the TLS port (typically 443) from the container.
   - Update clients to use `wss://` directly against the Phoenix endpoint
     instead of (or in addition to) HAProxy.

4. **Revisit HAProxy / LB configuration (if present):**
   - If you keep HAProxy in front, you can either:
     - Terminate TLS at HAProxy and talk HTTP to Phoenix (current recommended
       pattern), **or**
     - Use TCP mode in HAProxy to pass TLS through to Phoenix.

In most cases, terminating TLS at the load balancer gives you more flexibility
and a simpler Phoenix configuration, which is why internal TLS has not been
implemented by default.
