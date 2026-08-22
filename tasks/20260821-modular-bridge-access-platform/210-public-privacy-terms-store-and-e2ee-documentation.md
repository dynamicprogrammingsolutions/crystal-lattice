# Public Privacy, Terms, Store, And E2EE Documentation

Update public policy, product, store, and support content so account,
subscription, hosted relay, metadata, and verified E2EE behavior are described
accurately without exposing private operational material.

## Requirements checklist

### Functional requirements

- [ ] **P1** — Privacy content describes account identifiers, identity
  providers, subscription status, server/device metadata, security logs, relay
  processing, retention, deletion, and subprocessors at the public level.
- [ ] **P1** — Terms describe the hosted service, recurring subscription,
  cancellation, refunds, acceptable use, fair use, availability, and account
  deletion.
- [ ] **P1** — E2EE claims state exactly what is encrypted, endpoint scope,
  visible metadata, key/reset limitations, and verification status.
- [ ] **P1** — Landing/mobile product pages and App Store/Play disclosures
  distinguish free direct/self-hosted access from paid hosted access and match
  implemented data behavior.
- [ ] **P1** — Support and account-deletion URLs provide complete user-facing
  workflows.

### Non-functional requirements

- [ ] **P1** — Public pages do not expose task phases, private infrastructure,
  fraud controls, internal thresholds, customer data, or unpublished security
  findings.

Parent Task: `tasks/20260821-modular-bridge-access-platform/000-main.md`

Depends On:

- `tasks/20260821-modular-bridge-access-platform/070-e2ee-implementation.md`
- `tasks/20260821-modular-bridge-access-platform/160-mobile-login-purchase-and-subscription-ux.md`

## Required reading

- `landing_page/src/content/pages/privacy.yaml`
- `landing_page/src/content/pages/terms.yaml`
- `landing_page/src/content/pages/mobile.yaml`
- `landing_page/src/content/pages/support.yaml`
- Current iOS and Android store-preparation task packages
- Implemented E2EE and account-deletion behavior

## Execution plan

Status: Draft

Translate verified current behavior into public policy and product language.
Coordinate legal-reviewed public text supplied through the hosted-service
process, but keep public pages self-contained and free of internal provenance.

### Implementation decisions and open questions

- E2EE marketing is not published before Task 070 verification.
- Concrete commercial limit values are published only when approved for public
  launch.
- Platform-specific cancellation/refund behavior is described accurately.

### Documentation

This task is documentation-owned. Update authored landing/store sources, not
generated site output, and run the relevant site preparation/build/tests.

### Task checklist

- [ ] Update privacy and terms.
- [ ] Update landing/mobile hosted-service and E2EE copy.
- [ ] Update support and deletion guidance.
- [ ] Update App Store privacy/subscription metadata inputs.
- [ ] Update Play Data safety/subscription metadata inputs.
- [ ] Validate links, rendering, and claims.
- [ ] Obtain required human/legal confirmation.

### Requirement verification

- Trace each public claim to implemented behavior or approved legal text.
- Verify E2EE statement against protocol capture/security evidence.
- Run landing/docs builds and tests.
- Leave human/legal verification incomplete until confirmed.
