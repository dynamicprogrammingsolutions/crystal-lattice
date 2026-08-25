# Deliver the Validated Product Website Release

Implement the approved information architecture, page briefs, copy,
compatibility content, visual proof, and product/release integrations as the
larger validated Crystal Lattice website release.

## Requirements checklist

- [ ] The implemented website matches the approved content specification,
      experiment decisions, page briefs, and claim/evidence boundaries.
- [ ] Mobile, desktop, CLI, GitHub, documentation, compatibility, plugin,
      contributor, remote-access, support, privacy, and legal paths use current
      owning sources.
- [ ] Release metadata and download states fail safely when missing or stale.
- [ ] Desktop/mobile responsiveness, accessibility, SEO, performance, links,
      downloads, commands, and real product proof are verified.
- [ ] Production deployment and public route validation complete without
      exposing internal research or task context.

Parent Task: `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md`
Depends On:

- `tasks/20260825-crystal-lattice-product-positioning-and-website/150-website-information-architecture-and-content-briefs.md`
- `tasks/20260825-crystal-lattice-product-positioning-and-website/160-visual-proof-and-reproducible-assets.md`

## Integration boundaries

- iOS and Android tasks own store and review state.
- macOS distribution tasks own artifact choices, architectures, checksums, and
  installation differences.
- CLI release tasks own installer and version behavior.
- open-source release tasks own repository availability.
- bridge tasks own security, identity, E2EE, purchase, entitlement, and
  production readiness.
- documentation packages own their current user and developer contracts.

## References

### Start here

1. `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md:8-186`
   — shared requirements, content/research decisions, output rules, public
   boundaries, and remote-mutation constraints.
2. `tasks/20260825-crystal-lattice-product-positioning-and-website/150-website-information-architecture-and-content-briefs.md:1-115`
   plus its approved architecture, page briefs, claim/proof matrix, and
   implementation handoff. Stop if incomplete.
3. `tasks/20260825-crystal-lattice-product-positioning-and-website/160-visual-proof-and-reproducible-assets.md:1-114`
   plus its approved visual manifest, public assets, and completion evidence.
   Stop if incomplete.
4. `landing_page/docs/development/specifications/product-website-content/content-spec.md:1-305`
   and `landing_page/docs/development/specifications/product-website-content/requirements.md:6-22`
   — approved target and live requirement state.
5. `landing_page/docs/development/content-system.md:1-148` and
   `landing_page/README.md:1-137` — current implementation, build, preview,
   URL, and documentation behavior.
6. The exact product/release owners identified by the page-brief manifest for
   mobile, desktop, CLI, GitHub, docs, compatibility, plugins, remote access,
   support, privacy, and legal claims.

## Known facts and supporting details

- This task implements approved content and architecture; it does not repeat
  market research.
- Release facts remain owned by release packages and should be consumed from
  maintained metadata or validated source routes where practical.
- Missing or stale release metadata must fail safely rather than silently
  publishing broken downloads.
- Public content may not expose task, phase, research-confidence, or
  requirement-tracking language.
- Production deployment is a remote mutation requiring the applicable
  confirmation at execution time.

## Expected outputs

Current website implementation:

- page, content, Markdown, section, component, navigation, footer, style, data,
  and route files named by the approved page-brief and implementation
  manifests;
- maintained release/compatibility data inputs and validation;
- focused content/component tests;
- approved production visuals from
  `tasks/20260825-crystal-lattice-product-positioning-and-website/160-visual-proof-and-reproducible-assets.md`.

Current documentation:

- updated `landing_page/README.md`;
- updated `landing_page/docs/development/content-system.md`;
- additional current development pages only for delivered mechanics that no
  longer fit the content-system page;
- updated support, privacy, legal, and package docs when delivered behavior
  changes them.

Target/state:

- final approved updates to
  `landing_page/docs/development/specifications/product-website-content/content-spec.md`;
- completed evidence/status updates in
  `landing_page/docs/development/specifications/product-website-content/requirements.md`.

Verification and delivery:

- focused tests and `yarn build`;
- landing/documentation-site smoke;
- responsive, accessibility, SEO, performance, link, command, download, and
  visual evidence;
- production deployment and public validation only when authorized.

## Scope boundaries

- Do not reopen completed research without a concrete blocking contradiction.
- Do not fabricate missing release facts or weaken build validation.
- Do not directly edit generated `landing_page/dist/` or docs-site output.
- Do not mutate product/release systems outside the approved implementation
  and deployment scope.
- Store previews and deployment diagnostics under
  `landing_page/artifacts/research/170-validated-website-release-and-product-integration/`
  unless an owning release task specifies another generated-output path.

## Execution plan

Status: Draft

Update the content specification and requirements for final approved target
decisions, then implement page content and content-system changes. Consume
maintained release and compatibility inputs rather than manually duplicating
facts where practical.

Run focused component/content tests, full landing build, two-site docs smoke,
browser accessibility and responsive checks, real download/route checks, and
manual visual review. Obtain confirmation before production deployment, then
verify the deployed site and linked public products.

### Implementation decisions and open questions

- Decision: this task implements approved content; it does not reopen market
  research by default.
- Recommendation: split implementation into manual checkpoints by coherent
  page/product groups when the final brief set is substantial.
- Open questions: exact release metadata mechanism, deployment grouping, and
  any product dependency still not delivered when implementation begins.

### Documentation

- Update current package and content-system documentation for delivered
  mechanics.
- Update requirements with implementation, automated, human, documentation,
  and delivery evidence.
- Public pages omit research confidence, task, phase, and requirement
  vocabulary.

### Task checklist

- [ ] Confirm all required product/release inputs.
- [ ] Finalize current content target and requirements.
- [ ] Implement approved pages, navigation, content, and data inputs.
- [ ] Integrate approved production visuals.
- [ ] Add focused tests and validation.
- [ ] Run local build, docs smoke, accessibility, responsive, and visual
      verification.
- [ ] Verify downloads, commands, and public links.
- [ ] Obtain production deployment approval.
- [ ] Deploy and validate production when authorized.
- [ ] Record completion evidence and deferred product-dependent content.

### Requirement verification

- Page-level acceptance evidence maps to the content requirements.
- Product and release claims match current owning sources.
- Automated checks and human visual/device review both pass where required.
- The deployed site contains no missing proof, internal planning language, or
  broken user path.
