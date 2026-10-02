# Prove generated output and retire the legacy author field

Run the cross-capability transition gate, then enforce canonical-only author
metadata only after source, consumer, and generated-output evidence proves
that the legacy field is no longer required.

Parent Task: tasks/20260920-author-metadata-migration/000-main.md

Depends On:

- tasks/20260920-author-metadata-migration/010-author-contract-and-authoring.md
- tasks/20260920-author-metadata-migration/020-rendering-and-archive-consumers.md
- tasks/20260920-author-metadata-migration/030-source-content-migration.md

## Requirements checklist

- [ ] Collect a complete pre-rejection source and consumer audit with no
  production dependency on the legacy `author` field.
- [ ] Prove through a real production build that migrated post pages, home
  page, blog archive, tag pages, feed, and sitemap all remain generated and
  contain the expected author/routes/content evidence.
- [ ] Only after those checks pass, remove the legacy normalization branch and
  enforce a canonical-only input rule with a targeted diagnostic.
- [ ] Add a negative regression check showing legacy input is rejected after
  the gate, while canonical one/multiple-author input remains accepted.
- [ ] Run the full available test/build commands and record blocked commands
  or environment limitations instead of treating them as passing.

## Research and supporting facts

- The repository currently has no executable generated-output assertions;
  both relevant test files are comment-only placeholders.
- `npm run build` invokes Eleventy and writes `_site`; `npm test` runs the
  Node test files. `node_modules` is absent in the planning checkout.
- `.gitignore` excludes `node_modules/` and `_site/`, so generated verification
  can remain a local build artifact.
- Current legacy consumers are known in the post layout, feed, and authoring
  helper, but the final audit must catch references introduced during the
  migration as well.

## Execution plan

Status: Draft

Add or complete the generated-output test harness so it invokes the real
Eleventy build and inspects `_site`, rather than supplying mocked post data.
Before retirement, run a scoped inventory over production content, templates,
configuration, scripts, and tests; allow only the explicitly documented
compatibility boundary to mention or read the legacy field. Build the
canonical content and assert post author rendering, archive links/routes, all
feed authors, feed location, and sitemap URLs. Review the source and output
results together as the retirement gate.

Once the gate is green, remove the legacy adapter, turn on canonical-only
validation, and add a production-path negative fixture/check for a legacy
front-matter field. Re-run the canonical build and all tests after that
change. The negative check must demonstrate the intended failure without
weakening the normal build path or leaving a legacy fixture in the production
content tree.

### Implementation decisions and open questions

- Confirm the rejection mode; recommendation: fail the build early with the
  field name and migration action in the diagnostic.
- Keep the compatibility branch until the positive output evidence is
  complete; do not use a passing static scan alone as the retirement gate.
- Define the audit scope so historical task text or a deliberate negative
  fixture does not masquerade as a production dependency, while no live
  template/content/script lookup is excluded.
- If dependencies remain unavailable, leave the plan/task incomplete and
  report the exact blocked production commands; do not mark R6 complete from
  static inspection.

### Documentation

- Update the maintained authoring guidance only after canonical-only
  validation is enabled, so it describes current supported behavior.
- Record the source scan, generated-output checks, and negative rejection
  result in completion notes when execution is approved; do not claim this
  evidence in the Draft plan.

### Task checklist

- [ ] Implement/complete real generated-output assertions.
- [ ] Run the pre-rejection source and consumer audit.
- [ ] Build and inspect all required canonical outputs.
- [ ] Review the combined evidence and explicitly authorize the retirement
  step.
- [ ] Remove legacy normalization and enable canonical-only rejection.
- [ ] Add/run the negative legacy-input regression check.
- [ ] Re-run `npm test` and `npm run build`, then record evidence and any
  deferred verification.

### Requirement verification

- The retirement gate is decisive only when the scoped source/consumer audit,
  canonical content build, and generated-output assertions all pass together.
- Generated pages are verified at the public boundary: post HTML contains
  every author, home/blog/tag routes and links remain present, feed output
  contains every author at `/feed/feed.xml`, and sitemap URLs remain intact.
- Legacy rejection is verified by running the actual production validation
  path against representative legacy input and asserting the targeted
  failure, followed by a successful canonical build.
- Overall completion is verified by clean exits from `npm test` and
  `npm run build` with the required dependencies installed; unavailable
  commands remain an explicit verification gap.