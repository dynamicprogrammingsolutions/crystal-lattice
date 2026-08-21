# Mixed Transport Access, E2EE, And Metering Alignment

Integrate access profiles, grants, pairing policy, E2EE, and metering with the
in-progress HTTP/hybrid transport without duplicating or weakening its
transport contracts.

## Requirements checklist

- [ ] WebSocket, HTTP, and hybrid modes share one effective access and
  capability model.
- [ ] Static tokens, provider grants, pairing state, and E2EE credentials have
  distinct headers/envelopes and cannot overwrite backend authorization.
- [ ] HTTP control/proxy/transfer and hybrid event paths enforce equivalent
  subject, entitlement, quota, expiry, and E2EE decisions.
- [ ] Raw request/response byte accounting is complete and idempotent.
- [ ] Capability negotiation versioning preserves compatibility with older
  WebSocket-only bridges and saved connections.
- [ ] No automatic fallback duplicates non-idempotent requests.
- [ ] Edge proxies forward required credentials without caching or logging
  them.
- [ ] Cluster tests exercise different-node control, transfer, and session
  paths.
- [ ] Protocol and SDK documentation define the combined contract.

Parent Task: `tasks/20260821-modular-bridge-access-platform/000-main.md`

Depends On:

- `tasks/20260610-mobile-message-refresh-performance/050-plain-http-bridge-large-payload-path.md`
- `tasks/20260821-modular-bridge-access-platform/070-e2ee-implementation.md`
- `tasks/20260821-modular-bridge-access-platform/140-hosted-access-grant-enforcement.md`

## Required reading

- The complete mixed-transport task and implementation branch
- Bridge access, quota, E2EE, and capability contracts from this umbrella
- CloudFront/HAProxy forwarding configuration

## Execution plan

Status: Draft

Rebase/reconcile the mixed-transport implementation, centralize credentials and
policy decisions in the shared bridge connection abstraction, make encrypted
payloads and usage hooks first-class in HTTP transfers, and expand the existing
transport matrix rather than adding parallel adapters.

### Implementation decisions and open questions

- `X-Crystal-Bridge-Token` remains the pairing token.
- Deployment/access-grant credentials use separate names or handshake fields.
- Application `Authorization` continues to reach the local backend.
- No transparent HTTP/WebSocket retry after a request starts.

### Documentation

- Consolidate protocol credential taxonomy, capabilities, mode behavior,
  E2EE, metering, edge requirements, and migration/rollback instructions.

### Task checklist

- [ ] Reconcile branches and shared transport interfaces.
- [ ] Apply common authentication and capabilities.
- [ ] Integrate E2EE envelopes and byte accounting.
- [ ] Update edge forwarding/redaction.
- [ ] Expand SDK, bridge, Python, cluster, mobile, and AWS tests.
- [ ] Update protocol and transport documentation.

### Requirement verification

- Run the complete transport/access/E2EE/limits matrix.
- Inspect edge and bridge logs for credentials/plaintext.
- Exercise cross-node raw transfers and reconnect.
- Verify old saved connections retain explicit compatibility behavior.
