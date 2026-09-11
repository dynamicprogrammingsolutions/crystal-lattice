# Bridge transport policy and default

Select and implement the supported bridge transport policy for ordinary HTTP traffic after the optimized HTTP path is verified, while retaining an explicit legacy compatibility mode.

## Requirements checklist

- [ ] **BTP-001** A benchmark- and compatibility-backed decision records whether hybrid becomes the default or remains opt-in.
- [ ] **BTP-002** If hybrid is selected as default, ordinary HTTP requests such as messages, settings, schemas, and actions use HTTP bridge v2 while event delivery continues through the established WebSocket path.
- [ ] **BTP-003** Legacy WebSocket transport remains explicitly selectable for compatibility and rollback.
- [ ] **BTP-004** Pairing, resume, supersession, cancellation, timeout, reconnect, and authorization behavior remains correct in every supported mode.
- [ ] **BTP-005** The active transport mode and request path are observable through bounded diagnostics suitable for troubleshooting.
- [ ] **BTP-006** Existing saved connection records without an explicit transport mode have defined migration/default behavior.
- [ ] **BTP-007** Mobile and desktop behavior is consistent unless a documented platform constraint requires a difference.
- [ ] **BTP-008** Realistic integration tests cover large message responses, event delivery, reconnect, cancellation, and explicit rollback across the public bridge deployment flow.
- [ ] **BTP-009** Current user documentation explains the selected default, compatibility mode, and troubleshooting behavior without exposing internal task phases.

## Scope

In scope:

- Frontend bridge transport selection and persisted connection settings.
- HTTP/hybrid versus legacy WebSocket routing policy.
- Compatibility, migration, diagnostics, pairing/resume/reconnect, tests, and user documentation.

Out of scope:

- Implementing response compression itself.
- Replacing the bridge pairing model.
- Removing legacy WebSocket support.

Parent Task: `tasks/20260911-session-performance-and-storage-optimization/000-main.md`

Depends On: `tasks/20260911-session-performance-and-storage-optimization/090-bridge-response-compression.md`

## Requirement question

- After HTTP v2 compression and realistic integration verification, should hybrid become the default for new and mode-unspecified connections, or should it remain an explicit opt-in?

## Research details and suggested direction

The current shared transport factory and mobile application default to legacy WebSocket mode. Hybrid routes ordinary requests through raw HTTP v2 and reserves legacy WebSocket for `/events`.

The policy decision should use measured latency, failure recovery, deployment compatibility, mobile/desktop support, and operational visibility. It should not switch defaults merely because HTTP is architecturally preferable.

If hybrid becomes the default, existing explicitly selected WebSocket connections should remain unchanged. The treatment of old records with no stored mode is a material migration decision and should be made explicit.

This task intentionally omits an execution plan until the compression task demonstrates that the HTTP path is production-ready and the default-policy question is approved.