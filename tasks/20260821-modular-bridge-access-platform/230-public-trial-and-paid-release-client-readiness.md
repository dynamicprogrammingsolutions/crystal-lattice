# Public Trial And Paid-Release Client Readiness

Prepare the public mobile and client code for a hosted bridge offer with a
store-managed trial and approximately USD 10/month reference price after
production E2EE, limits, and hosted services are ready.

## Requirements checklist

- [ ] Mobile clients present the approved monthly product and localized price
  from the native store.
- [ ] The public introductory trial is shown only when the store reports the
  applicable offer and the hosted service permits access.
- [ ] Trial, paid, grace, billing issue, cancellation, expiration, refund, and
  restore states produce accurate UX.
- [ ] Hosted access requires production E2EE, entitlement, and configured
  limits while free direct/self-hosted modes remain available.
- [ ] Store review notes and public support paths explain how reviewers can test
  the hosted bridge.
- [ ] Versioning, build, signing, TestFlight, and Play internal-track workflows
  remain compatible.
- [ ] Accessibility, localization, privacy links, terms, and manage-subscription
  actions are complete.
- [ ] Public documentation does not claim launch before production approval.

Parent Task: `tasks/20260821-modular-bridge-access-platform/000-main.md`

Depends On:

- `tasks/20260821-modular-bridge-access-platform/210-public-privacy-terms-store-and-e2ee-documentation.md`
- `tasks/20260821-modular-bridge-access-platform/220-public-sandbox-integration-harness.md`
- Production launch approval supplied externally

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
