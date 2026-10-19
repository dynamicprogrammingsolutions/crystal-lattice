# Bridge connection integration

This page describes how the mobile application integrates the shared bridge
transports: connection selection, pairing, saved-record reconstruction,
foreground recovery, and repair. The frontend SDK owns the transport
implementations and their portable contracts.

Bridge transports are created only through the frontend SDK's
`createBridgeConnectionTransport()` factory. Mobile supports:

| Selection | Mobile behavior |
| --- | --- |
| HTTP | Product default for discovery, pairing, events, and requests through bridge HTTP v1; no frontend WebSocket. |
| WebSocket | Explicit legacy development override for all bridge operations. |
| Hybrid | Explicit legacy development override: HTTP discovery/pairing/normal requests and WebSocket only for exact `GET /events`. |

The Home connection modal has no transport selector. Home → Development
Settings presents a general window with a Bridge section. Its versioned,
app-wide preference is hydrated before construction, separately persisted,
and changes only future transports. Reset preserves other settings.
There is no automatic fallback or in-flight replay.

Bridge input prefers a bare-domain placeholder. The shared address helper
validates it with HTTPS as the omitted-scheme default, while explicit
HTTP(S)/WS(S) values remain supported. History retains the trimmed entered
address; transport construction derives its HTTP base or legacy endpoint.
Connectivity testing shares that normalization.

The connection wizard requests keyboard avoidance from
`CenteredModalSurface`. The keyboard wrapper uses iOS padding/Android height
behavior and contains a flex viewport; modal percentages and the wizard
scroll area are bounded by the remaining space. Native checks type into the
real field with the software keyboard and compare modal/viewport bounds.

Successful pairing stores a `BridgeConnectionRecord` with bridge URL, server
ID/name, pairing token, and product `transportMode: 'http'`, even with a
diagnostic override. Historical modes remain readable but do not select the
production transport. The effective mode is the development override or HTTP;
saved identity, URL, token, and cache ownership remain intact.

`useSavedBridgeUrls` uses the SDK endpoint store independently of paired
connections. Successful discovery upserts the endpoint before pairing; failed
discovery does not write it. Its serialized writes wait for hydration and
preserve labels when refreshing timestamps. Removing an endpoint leaves paired
connections intact.

Reopening a saved record supplies its server ID and pairing token to the mode
factory. Invalid token or server mismatch clears the stale token and opens the
repair flow. A temporarily absent server keeps the record available for
re-pairing when it returns.

Foreground recovery uses the structural `BridgeConnectionTransport` lifecycle:

1. call `prepareForResume()`;
2. reconnect/validate;
3. persist a changed pairing token if one is returned;
4. open repair when the server or credential is no longer valid.

Production selectors cover Home's development entry, settings controls, saved
endpoint rows/removal, and server pairing. Component tests cover historical
record modes, independent preference fields, hydration, and endpoint persistence.
The real-bridge App integration starts from Home and crosses production
discovery/pairing, persisted reopen, and session creation. Deterministic native
checks supplement real network evidence.

## Native verification

The focused native scenarios are `bridgeTransportMode.e2e.test.ts` and
`bridgeConnection.e2e.test.ts`. The former checks the production Home menu,
settings persistence/reset, and normal wizard; the latter starts a real
registered backend and crosses discovery, pairing, send/response, relaunch,
endpoint removal, and saved-server reopen.

Android verification uses an isolated API 35 plain AOSP ARM64 emulator.
Select your AVD with `DETOX_ANDROID_AVD`; the package's Android test scripts
perform the standard emulator preparation. Both iOS and Android scenarios
must finish successfully, including teardown, before counting native coverage.

The `IS_DETOX_E2E` variant keeps navigation/system UI stable at startup and
on window focus. `MainActivity` applies the same immersive-mode guard in
both lifecycle callbacks so Android's first-run fullscreen prompt cannot
steal focus from production controls. Ordinary builds retain their
existing immersive behavior; native UI, connection handlers, SDK adapters,
and backend routes remain the production implementations.

See the frontend SDK's
[bridge transport implementation](../../../../packages/frontend-sdk/docs/development/bridge-transport-implementation.md)
for mode-specific transport ownership. The cross-package
[bridge-connectivity frontend specification](../../../../docs/development/specifications/bridge-connectivity/frontend-behavior.md)
owns portable mode and migration behavior, while the mobile
[connection lifecycle specification](specifications/connection-lifecycle/index.md)
defines mobile lifecycle requirements.

Maintainer entry points:

- `App.tsx`
- `src/connectionInfo.ts`
- `src/bridgeConnection.ts`
- bridge connection and transport-mode component tests
- focused bridge transport Detox scenarios