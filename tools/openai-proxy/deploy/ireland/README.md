# Ireland reviewer proxy

This directory is the configurable Docker Compose deployment for the external
iOS App Review provider. It runs the generic inspection proxy behind a
self-signed TLS endpoint.

No secret belongs in git. Copy `.env.example` to `.env`, set the upstream
OpenAI key and a separate random reviewer key, and keep the resulting file at
mode `0600`.

All deployment values can be changed through `.env` and
`config/reviewer-proxy.json`, including the public bind address/port, hostname,
internal port, upstream URL, environment-variable names, allowed models,
endpoint paths, service tiers, budget, cooldown, pricing, long-context rules,
state path, logging, and response statuses.

Generate the configured self-signed certificate:

```bash
REVIEWER_PROXY_SERVER_NAME=ireland-s1.dynamicprogrammingsolutions.com \
REVIEWER_PROXY_CERT_SAN=DNS:ireland-s1.dynamicprogrammingsolutions.com,DNS:localhost,IP:127.0.0.1 \
  ./generate-self-signed-cert.sh
```

Start, inspect, and stop:

```bash
docker compose up --build --detach
docker compose ps
docker compose logs --follow
docker compose down
```

The image runs as non-root user `node`. When the host bind-mounted data
directory has a different owner, grant only container UID `1000` access:

```bash
setfacl -m u:1000:rwx data
```

The outer TLS service is the only publicly bound container port. The Node
proxy remains on the Compose network. The rate-limit ledger is retained under
`data/` across container replacement.

The public certificate must be staged as the configured CA for the embedded
reviewer profile before distributing the app. Never disable certificate
verification and never transfer or bundle `server.key`.

The reviewer JSON permits only `/models` and `/responses`. Chat Completions is
rejected before upstream forwarding. The mobile reviewer uses the OpenAI
Responses provider and Codex-like tools; the generic OpenAI-compatible/Ollama
profile remains separate.