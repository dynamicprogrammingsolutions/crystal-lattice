# Static-Token Bridge Security

Protect user-deployed bridges with a deployment-configured static token so
possession of the bridge URL alone does not allow server registration,
discovery, pairing, resume, or request proxying.

## Requirements checklist

- [ ] A configured static token protects app and server access over WebSocket,
  HTTP, and hybrid transports.
- [ ] The deployment token is distinct from pairing-token signing secrets,
  pairing tokens, transfer tokens, and future account access grants.
- [ ] Missing or incorrect tokens fail before any protected bridge operation.
- [ ] Health and minimal capability discovery remain usable without exposing
  servers, sessions, secrets, or account data.
- [ ] Mobile and terminal/server clients can supply and securely persist the
  deployment token.
- [ ] Tokens are compared safely and are excluded from URLs, logs, errors,
  debug timelines, and ordinary connection records.
- [ ] Existing explicitly open local deployments remain compatible.
- [ ] User and maintainer documentation covers configuration, rotation, and the
  token taxonomy.

Parent Task: `tasks/20260821-modular-bridge-access-platform/000-main.md`

Depends On:
`tasks/20260610-mobile-message-refresh-performance/050-plain-http-bridge-large-payload-path.md`
for final HTTP/hybrid integration when that work lands.

## Required reading

- `bridge-elixir/lib/bridge/socket.ex`
- `bridge-elixir/lib/bridge/app_channel.ex`
- `bridge-elixir/lib/bridge/server_channel.ex`
- `bridge-elixir/lib/bridge/endpoint.ex`
- `cloud-orchestrator/lib/cloud_orchestrator/router.ex`
- `packages/frontend-sdk/src/transport/bridgeTransport.ts`
- Mixed-transport worktree versions of `httpBridgeTransport.ts`,
  `hybridBridgeTransport.ts`, and `bridge-elixir/lib/bridge/http_router.ex`

## Supporting details

The cloud orchestrator already protects configured control routes with
`Authorization: Bearer <token>` and constant-time comparison. The bridge needs
equivalent deployment protection at both of its public transport boundaries.

The mixed transport reserves `X-Crystal-Bridge-Token` for the app/server
pairing token and preserves the caller's ordinary `Authorization` header for
the local backend. Use a distinct bridge access credential, tentatively
`X-Crystal-Bridge-Access-Token`, for HTTP control and proxy requests. Transfer
endpoints continue to use their short-lived direction-scoped bearer tokens.

Do not send the long-lived static token in the WebSocket URL. Select a portable
header, subprotocol, socket parameter that is not logged, or mandatory initial
authentication exchange before channel operations. The same `accessToken`
transport option must work in WebSocket, HTTP, and hybrid factories.

## Execution plan

Status: Draft

Add a common deployment-token verifier and apply it before every protected
bridge action. Extend SDK and Python configuration without overloading pairing
credentials. Add secure mobile storage for the token. Preserve `/health` and a
minimal `/bridge/v1/capabilities` response, but protect server listing and all
mutation/proxy behavior.

### Implementation decisions and open questions

- Use one deployment token for trusted app and server clients in this first
  implementation.
- Pairing remains required in this task; configurable pairing is Task 020.
- Production-like profiles fail startup when a required token is absent.
- Exact WebSocket credential carriage is a local design choice, but URL query
  storage and logging are prohibited.
- Token overlap/rotation support is desirable but may be deferred if replacing
  the configured token with a reconnect is clearly documented.

### Documentation

- Update bridge deployment and protocol guides with token creation,
  configuration, client setup, rotation, and failure behavior.
- Update frontend SDK transport documentation and mobile/terminal connection
  guides.
- Explain deployment token versus pairing, transfer, and access-grant tokens.

### Task checklist

- [ ] Add deployment-token configuration and verifier.
- [ ] Protect WebSocket app and server channel use.
- [ ] Protect HTTP discovery, pairing, resume, and proxy routes.
- [ ] Extend all bridge transport factories with an access-token option.
- [ ] Add terminal CLI/env/profile support.
- [ ] Add mobile entry and secure storage.
- [ ] Redact credentials from logs and diagnostics.
- [ ] Add unit, integration, cluster, mobile, and compatibility tests.
- [ ] Update public and development documentation.

### Requirement verification

- Connect app/server clients with no token, wrong token, and correct token over
  WebSocket, HTTP, and hybrid modes.
- Assert unauthorized clients cannot list servers, request pairing, register,
  resume, or proxy.
- Assert local backend `Authorization` survives HTTP proxying unchanged.
- Inspect captured logs and persisted connection data for token absence.
- Verify an explicitly configured local-open deployment retains existing
  behavior.

### Additional implementation verification

- Test proxy/header behavior through the Docker cluster and at least one
  supported AWS edge profile.
- Test token replacement and reconnect behavior.
- Run static scans for the configured token in generated test output.
