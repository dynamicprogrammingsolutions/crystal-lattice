# Publish the Managed Remote-Access Paid Launch Website

Publish the production managed remote-access offer through the validated
Crystal Lattice website while preserving local-network and user-operated
bridge choices and matching current trial, pricing, purchase, entitlement,
privacy, E2EE, support, and platform behavior.

## Requirements checklist

### Functional requirements

- [ ] The website presents the approved production managed remote-access
      product, localized store price, trial eligibility, purchase/restore
      paths, subscription lifecycle, and platform availability accurately.
- [ ] Local-network direct connection and user-operated bridge choices remain
      visible and usable without purchase.
- [ ] Privacy, terms, E2EE, account deletion, support, cancellation, refund,
      quota/fair-use, and service-availability statements match current
      approved production behavior.
- [ ] Website actions route users to the correct iOS, Android, account,
      subscription-management, support, and connection workflows.
- [ ] Store reviewers and public users can follow complete current guidance
      without internal credentials, task context, or private operational
      knowledge.

### Non-functional requirements

- [ ] Paid-offer claims cannot be enabled before the public client,
      policy/security, and owner-confirmed hosted-service release gates pass.
- [ ] The website remains accessible, responsive, measurable under the
      approved privacy model, and independently clear about free versus paid
      choices.
- [ ] Commercial values and service states come from maintained approved
      sources and fail safely when missing or inconsistent.

Parent Task: `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md`

Depends On:

- `tasks/20260825-crystal-lattice-product-positioning-and-website/110-remote-access-and-bridge-viability.md`
- `tasks/20260825-crystal-lattice-product-positioning-and-website/170-validated-website-release-and-product-integration.md`
- `tasks/20260825-crystal-lattice-product-positioning-and-website/180-production-measurement-and-iteration.md`
- `tasks/20260821-modular-bridge-access-platform/210-public-privacy-terms-store-and-e2ee-documentation.md`
- `tasks/20260821-modular-bridge-access-platform/230-public-trial-and-paid-release-client-readiness.md`

## References

### Start here

1. `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md:8-186`
   — shared product requirements, managed-service question, content/research
   boundaries, output rules, and release-mutation constraints.
2. `tasks/20260825-crystal-lattice-product-positioning-and-website/110-remote-access-and-bridge-viability.md:1-125`
   plus its accepted recommendation, trust/bundle matrix, pricing/interest
   observations, and completion manifest. Stop if incomplete.
3. `tasks/20260825-crystal-lattice-product-positioning-and-website/170-validated-website-release-and-product-integration.md:1-119`
   plus its deployed website, page briefs, release integrations, and
   completion evidence. Stop if incomplete.
4. `tasks/20260825-crystal-lattice-product-positioning-and-website/180-production-measurement-and-iteration.md:1-113`
   plus its approved event, privacy, retention, validation, and production
   measurement outputs. Stop if incomplete.
5. `tasks/20260821-modular-bridge-access-platform/210-public-privacy-terms-store-and-e2ee-documentation.md:1-46`
   plus its approved current public policy, E2EE, support, deletion, and store
   outputs. Stop if incomplete.
6. `tasks/20260821-modular-bridge-access-platform/230-public-trial-and-paid-release-client-readiness.md:1-43`
   plus its approved localized product, trial, lifecycle, review, and
   production-client evidence. Stop if incomplete.
7. `landing_page/docs/development/specifications/product-website-content/content-spec.md:205-274`
   — local/remote, current/future, proof, and progressive-release content
   boundaries.
8. `landing_page/docs/development/specifications/product-website-content/requirements.md:6-23`
   — live remote, open-path, paid-offer, proof, accessibility, and measurement
   state.

### Additional references

- Current iOS and Android public release documentation and maintained store
  product metadata selected by the public bridge client-readiness task.
- Owner-confirmed hosted-service launch readiness and approved public
  commercial values. Do not require or expose private implementation details.
- Current landing page, mobile, privacy, terms, support, account-deletion, and
  connection content named by the task-170 page-brief manifest.

## Known facts and supporting details

- This is a paid-offer launch integration, not the task that defines the
  service, pricing strategy, subscription implementation, E2EE protocol, or
  production operations.
- Store-displayed localized price and eligibility are authoritative for
  purchase UX; the website must not hard-code stale approximate values where a
  maintained release source is available.
- Free direct and user-operated bridge modes remain part of the product.
- Public E2EE, metadata, quota, retention, refund, deletion, availability, and
  support claims require accepted owning evidence.
- A technically ready service is not publicly launched until the owner has
  confirmed production launch readiness.
- Website measurement must not collect prompts, message content, credentials,
  private sessions, or unnecessary persistent identifiers.

## Expected outputs

Content decision:

- `landing_page/docs/development/research/findings/managed-remote-access-paid-launch-content-decision.md`

Required target/state updates:

- `landing_page/docs/development/specifications/product-website-content/content-spec.md`
  when the paid current-state target changes;
- `landing_page/docs/development/specifications/product-website-content/requirements.md`
  with implementation, verification, documentation, and delivery evidence.

Current public content:

- managed remote-access product/connection content in the routes selected by
  the task-170 architecture;
- affected home, mobile, navigation, footer, pricing/offer, privacy, terms,
  support, account-deletion, and connection sources;
- maintained product, platform, price, trial, store, and support data inputs;
- current App Store and Google Play routes and subscription-management links.

Verification and delivery:

- focused content/data validation and landing build;
- responsive, keyboard, semantic, contrast, localization, link, purchase,
  restore, subscription-management, privacy, support, and free-mode checks;
- iOS and Android real-device or release-build verification at their public
  boundaries;
- production deployment and public-route validation only when authorized;
- completion manifest under
  `landing_page/research/190-managed-remote-access-paid-launch-website/`.

Disposable output:

- `landing_page/artifacts/research/190-managed-remote-access-paid-launch-website/`
  for previews, store screenshots, temporary product data, and deployment
  diagnostics.

## Scope boundaries

- Do not choose or change price, trial duration, commercial limits,
  subscription products, E2EE behavior, or service policy.
- Do not launch, enable purchases, configure stores, mutate hosted services, or
  deploy production content without the authority required at execution time.
- Do not expose private hosted-service topology, credentials, fraud controls,
  thresholds, customer data, support operations, or unpublished findings.
- Do not hide, de-emphasize into irrelevance, or disable free local-network and
  user-operated bridge paths.
- Do not publish approximate or planned commercial behavior as current.
- Do not reopen completed positioning research unless current production
  evidence contradicts a required public claim.

## Execution plan

Status: Draft

Reconcile the accepted remote-access offer recommendation with the final public
client, policy, security, store, and owner-confirmed production launch
evidence. Update the content specification first when the intended current
paid-offer target changes, then implement the smallest coherent set of public
pages and maintained data integrations.

Verify free and paid choices together, validate localized store/product routes
on release builds and real devices, run the landing checks, obtain the required
deployment/launch confirmation, and verify the production website after
release.

### Implementation decisions and open questions

- Use approved current store values and service policy rather than the earlier
  approximate research reference price.
- Preserve one coherent connection explanation across local, user-operated,
  trial, paid, expired, and unavailable states.
- Resolve final route and CTA labels from the task-170 architecture and current
  client/store behavior.
- Treat owner confirmation of hosted production readiness as a release gate,
  not as implementation context to publish.

### Documentation

- Public content describes delivered paid and free behavior directly.
- Current content-system documentation changes only when new maintained data,
  validation, route, or section behavior is delivered.
- Private hosted-service tasks and operations remain outside public
  documentation.

### Task checklist

- [ ] Confirm every declared and external production-readiness dependency.
- [ ] Reconcile approved commercial/product data and public policies.
- [ ] Update content target and requirements.
- [ ] Implement maintained offer, platform, and support data.
- [ ] Update affected public pages and actions.
- [ ] Run local automated, accessibility, localization, and visual checks.
- [ ] Verify release clients, store routes, free modes, and subscription
      lifecycle guidance.
- [ ] Obtain production website and paid-offer launch approval.
- [ ] Deploy and validate production when authorized.
- [ ] Record requirement, delivery, and completion evidence.

### Requirement verification

- Every paid-offer, price, trial, E2EE, quota, privacy, terms, support, and
  platform claim traces to current approved evidence.
- Free direct and user-operated bridge paths remain findable and usable.
- Store and subscription-management actions resolve correctly on supported
  platforms.
- Automated and human accessibility/localization/device checks pass.
- Production routes, product data, policies, and release clients agree after
  launch.
