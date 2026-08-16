# Frontend Sdk

Frontend Sdk package for Crystal Lattice.

## Testing

Run fast/default package tests from the repository root:

```bash
npm --workspace @crystal-lattice/frontend-sdk test
```

Or from this package directory:

```bash
npm test
```

The default Vitest config excludes `src/integration/**`, so this command is the
safe everyday check for SDK logic, transports, reducers, plugin helpers, and
other unit-style tests.

Integration and e2e suites live under `src/integration/__tests__` and are
selected by explicit package scripts. Start with the detailed integration guide:

- [src/integration/__tests__/README.md](src/integration/__tests__/README.md)

Common categories:

- Local backend integration: `npm run integration:backend`
- Hosted provider integration: `npm run integration:backend:openai`, `npm run integration:backend:openrouter`, `npm run integration:backend:openrouter-images`, `npm run integration:backend:openrouter:mcp`
- Bridge e2e: `npm run integration:bridge`
- Cloud orchestrator e2e: `npm run integration:cloud`, `npm run integration:cloud:profiles`
- AWS-backed e2e and maintenance commands: run only when intentionally working on those deployments

## Bridge transport modes

`createBridgeConnectionTransport()` supports three explicit modes:

- `websocket` is the compatibility default and returns the existing
  `BridgeTransport` unchanged.
- `http` uses the bridge HTTP v1 API for discovery, pairing, token validation,
  event polling, and every proxied backend request. The frontend does not open
  a WebSocket in this mode.
- `hybrid` uses HTTP for discovery, pairing, validation, and normal backend
  requests. Only exact `GET /events` requests (including query strings) use
  the existing `BridgeTransport`.

HTTP requests never fall back automatically to WebSocket. Recreate the
connection with `mode: "websocket"` for an explicit rollback; automatic retry
could duplicate non-idempotent writes.

Both HTTP modes accept the existing `ws(s)://.../ws/websocket` bridge URL and
derive the matching HTTP origin. Set `bridgeHttpBaseUrl` when a deployment uses
different public HTTP and WebSocket origins. JSON and text preserve the
standard `Transport` response contract, while non-text responses return an
`ArrayBuffer` and binary request bodies are sent as raw bytes.

## License

Copyright 2026 Dynamic Programming Solutions Kft.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

<http://www.apache.org/licenses/LICENSE-2.0>

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
