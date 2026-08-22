# Public Trial And Paid-Release Client Readiness

Prepare the public mobile and client code for a hosted bridge offer with a
store-managed trial and approximately USD 10/month reference price after
production E2EE, limits, and hosted services are ready.

## Requirements checklist

### Functional requirements

- [ ] **P1** — Mobile clients display the approved localized monthly product
  and present the introductory offer only when store and hosted-service
  eligibility permit it.
- [ ] **P1** — Trial, paid, grace, billing issue, cancellation, expiration,
  refund, and restore states produce accurate UX.
- [ ] **P1** — Hosted access requires production E2EE, entitlement, and
  configured limits while free direct/self-hosted modes remain available.
- [ ] **P1** — Store reviewers can test the hosted service through
  release-compatible TestFlight and Play workflows with complete review and
  support guidance.
- [ ] **P1** — Accessibility, localization, privacy links, terms, and
  manage-subscription actions are complete.

### Non-functional requirements

- [ ] **P1** — Public release claims and product presentation are enabled only
  after production approval.

Parent Task: `tasks/20260821-modular-bridge-access-platform/000-main.md`

Depends On:

- `tasks/20260821-modular-bridge-access-platform/210-public-privacy-terms-store-and-e2ee-documentation.md`
- `tasks/20260821-modular-bridge-access-platform/220-public-sandbox-integration-harness.md`
- Production launch approval supplied externally

## Specifications and requirements

- `docs/development/specifications/hosted-bridge-client-experience/index.md`:
  `HBC-005` through `HBC-010`, `HBC-013`, `HBC-014`
- `docs/development/specifications/bridge-e2ee/index.md`:
  `BEE-012`, `BEE-013`

## Required reading

- iOS TestFlight and Android Play release task packages
- Mobile subscription UX from Task 160
- Implemented trial/product data returned by the stores
- Public privacy, terms, support, and E2EE pages

## Execution plan

Status: Draft

Enable the approved public product/trial presentation, complete review-mode
guidance, and verify release builds against production-style hosted access.
Keep exact annual-product, trial-duration, and commercial quota expansion
outside scope unless separately approved.

### Implementation decisions and open questions

- Initial public offer is monthly only unless changed before execution.
- Reference price is approximately USD 10/month; the app displays localized
  store values.
- Trial duration is decided before store-product configuration; seven days is
  the current recommendation.

### Documentation

- Update mobile release/readiness docs, store-review notes, public product
  pages, support, and trial/subscription explanations.

### Task checklist

- [ ] Enable approved product/trial display.
- [ ] Complete all subscription lifecycle UX.
- [ ] Add review/test instructions and accessible controls.
- [ ] Verify production-style hosted connection and free modes.
- [ ] Run release builds, native tests, sandbox/internal tracks, and docs.
- [ ] Record human store-console and real-device evidence.

### Requirement verification

- Complete trial-to-paid and trial-expiry scenarios on both platforms.
- Verify localized price and offer eligibility come from the store.
- Verify review users can reach a functioning hosted test server.
- Verify free connection modes remain usable without purchase.
