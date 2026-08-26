# Publish a Release-Safe Early-User Website

Replace the intermediate public homepage with a truthful, useful baseline that
helps early users understand and try the current product without waiting for
market research.

## Requirements checklist

- [ ] The public website plainly presents the current coding-agent-first
      product running on the user's computer.
- [ ] It distinguishes Crystal Lattice compatibility profiles from official
      upstream applications and sessions.
- [ ] It explains direct local-network mobile use and the user-operated bridge
      accurately.
- [ ] Early users have a short, verified first-success path and current
      availability, support, privacy, docs, and source routes.
- [ ] Visible planning placeholders, knowingly unverified APIs, and stale
      availability claims are removed or omitted.
- [ ] Desktop and mobile visual/accessibility review confirms the baseline is
      suitable for early-user and reviewer-facing use.

Parent Task: `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md`

Depends On:

- `tasks/20260825-crystal-lattice-product-positioning-and-website/020-current-product-and-compatibility-baseline.md`
- `tasks/20260825-crystal-lattice-product-positioning-and-website/025-integrate-current-visual-baseline-and-bootstrap-asset-pipeline.md`

## Scope

This is a bounded baseline rewrite, not the final positioning or information
architecture. It may satisfy or replace the factual `WEB-IOS` roadmap
placeholder after a separate roadmap update.

## References

### Start here

1. `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md:8-186`
   — shared program requirements, current positioning decisions, output rules,
   and public/research boundaries.
2. `tasks/20260825-crystal-lattice-product-positioning-and-website/020-current-product-and-compatibility-baseline.md:1-125`
   plus its completed outputs — required current product, configured-agent,
   provider/account, feature, and evidence baseline. Stop if incomplete.
3. `tasks/20260825-crystal-lattice-product-positioning-and-website/025-integrate-current-visual-baseline-and-bootstrap-asset-pipeline.md:1-232`
   plus its accepted early visual manifest, public assets, browser validation,
   and completion evidence. Stop if incomplete.
4. `landing_page/docs/development/specifications/product-website-content/content-spec.md:1-305`
   — complete current content target, terminology, compatibility, proof, and
   progressive-revision requirements.
5. `landing_page/docs/development/specifications/product-website-content/requirements.md:6-23`
   — live target state and evidence mapping.
6. `landing_page/docs/development/content-system.md:7-159` — current authored
   sources, rendering, assets, extension points, boundaries, and verification.
7. `landing_page/src/content/pages/home.yaml:1-441`,
   `landing_page/src/content/pages/mobile.yaml:1-119`, and
   `landing_page/src/content/markdown/privacy.md:1-104` — current public
   product, mobile, and privacy content to audit before editing.

### Additional references

- `application/python/README.md:1-210` and
  `mobile/crystal-lattice-control-rn/README.md:1-180` — current first-use and
  connection behavior.
- Current iOS, Android, macOS, CLI, open-source, and bridge release task files
  listed in `landing_page/docs/development/research/evidence-index.md:65-75`
  when their facts are used.
- Historical landing-page task and brainstorm listed in the main task only as
  prior hypotheses.

## Known facts and supporting details

- This rewrite exists so early users are not blocked by later market research.
- The current public sources include visible planning placeholders and
  explicitly unverified examples.
- Task 025 owns the reviewed early visual baseline and minimal asset workflow;
  this task consumes those accepted outputs rather than independently
  re-importing or selecting screenshots.
- The approved current baseline is coding-agent-first, runs on the user's
  computer, and distinguishes Crystal Lattice profiles from official upstream
  applications and sessions.
- Mobile can connect directly on the same local network; the bridge relays the
  Crystal Lattice connection when away from that network.
- The rewrite may satisfy the factual website part of the existing iOS review
  placeholder, but roadmap mutation is separate.

## Expected outputs

Content decision:

- `landing_page/docs/development/research/findings/release-safe-early-user-content-decision.md`

Required current-content updates:

- `landing_page/src/content/pages/home.yaml`;
- `landing_page/src/content/pages/mobile.yaml` when availability or
  explanation changes;
- affected support, privacy, terms, navigation, footer, section, or component
  sources only when the verified baseline requires them.

Required target/state updates:

- `landing_page/docs/development/specifications/product-website-content/content-spec.md`
  when the approved intended content changes;
- `landing_page/docs/development/specifications/product-website-content/requirements.md`
  with implementation, verification, documentation, and evidence state.

Verification outputs:

- successful landing build;
- focused link/command checks;
- desktop and mobile viewport observations;
- accessibility observations;
- production deployment evidence only when separately authorized.

## Scope boundaries

- Do not wait for
  `tasks/20260825-crystal-lattice-product-positioning-and-website/040-research-foundation.md`
  through
  `tasks/20260825-crystal-lattice-product-positioning-and-website/080-competitor-category-and-multi-agent-research.md`.
- Do not invent final positioning, pricing, comparisons, or managed-bridge
  behavior.
- Do not add speculative screenshots or unverified code to replace removed
  placeholders.
- Do not update the roadmap or deploy remotely without the relevant separate
  authority.

## Execution plan

Status: Draft

Update the content specification first if the approved baseline target needs
clarification. Rewrite the smallest set of current public pages needed for
early understanding and first success. Hide or remove incomplete proof rather
than replacing it with speculative content.

Use verified product screenshots already available only when they match the
current product and the task-025 visual manifest. Validate build, links,
responsive behavior, accessibility, commands, and reviewer-facing facts.
Prepare production deployment and request the required confirmation before
remote mutation.

### Implementation decisions and open questions

- Decision: do not wait for search, community, competitor, or interview
  research.
- Decision: label this content as normal current product content, not as a
  research phase.
- Open question: determine the smallest current visual set that is accurate
  enough for release without starting the later visual-production task.

### Documentation

- Update current public content and content requirements.
- Update `content-system.md` only if the implementation changes.
- Record larger positioning questions in research, not public copy.

### Task checklist

- [ ] Reconcile the current page against the compatibility baseline.
- [ ] Confirm the accepted task-025 visual baseline and asset checks.
- [ ] Update the content target and affected requirements.
- [ ] Rewrite the homepage and affected product routes.
- [ ] Remove public placeholders and unverified examples.
- [ ] Verify first-success commands and links.
- [ ] Run build, responsive, accessibility, and visual checks.
- [ ] Obtain approval for production deployment.
- [ ] Deploy and verify public routes when authorized.

### Requirement verification

- A reviewer unfamiliar with the product can answer the acceptance questions
  in the content specification.
- Current commands and links produce the documented result.
- No visible placeholder or internal planning label remains.
- Production content matches current owning release and product sources.
