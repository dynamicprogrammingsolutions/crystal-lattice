# Gate and complete legacy author-field removal

Own the final compatibility decision: collect content and generated-output
evidence, then remove or reject the legacy form only when the evidence gate
passes.

Parent Task: `tasks/20260926-author-metadata-migration/000-main.md`

Depends On:

- `tasks/20260926-author-metadata-migration/010-source-and-authoring.md`
- `tasks/20260926-author-metadata-migration/020-public-rendering.md`

## Requirements checklist

- [ ] R5. Legacy `author` input is removed or rejected only after both source
  content and production-generated-output evidence show that supported paths
  no longer depend on it.
- [ ] The final behavior for an accidental legacy post is explicit, tested,
  and consistent with the approved post-cutover policy.

## Unresolved requirement questions

- Q3. Confirm whether accidental legacy input must fail the build with a clear
  validation error or use another explicit unsupported-input behavior.

## Research and supporting facts

- Legacy references currently exist in both source content and production
  consumers: two post files, the post layout, the feed, and the authoring
  helper.
- The existing test files are comments only, so no current evidence can
  authorize a cutover.
- There is no checked-in `_site`; generated-output evidence must come from a
  fresh real Eleventy build after the preceding migration/rendering work.

## Execution plan

Status: Draft

Treat legacy removal as an evidence-gated compatibility state, not as a
cleanup step. First establish a complete source scan for legacy keys and
direct field reads. Then run the production build over migrated content and
inspect every affected public output, including the feed and all archive
paths. Only when both evidence sets pass should the compatibility reader be
removed and the approved build-time rejection or equivalent unsupported-input
behavior be enabled.

Ordered work:

1. Define the exact scan scope: source front matter, templates, scripts,
   tests/fixtures, documentation claims, and generated output.
2. Run a repository content/implementation scan and fail the gate if any
   supported source path still requires the scalar field.
3. Run `npm run build` from the migrated repository and assert the expected
   route set, author output, feed validity, and absence of legacy-dependent
   rendering symptoms.
4. Review the two evidence sets together; if either fails, retain
   compatibility and record the dependency instead of cutting over.
5. If both pass, remove the legacy normalization and implement the approved
   invalid-input behavior, then add a regression test proving accidental
   legacy metadata cannot silently pass.
6. Re-run the full test/build evidence after the cutover and update the
   maintained documentation to describe only the final supported contract.

### Implementation decisions and open questions

- Q3 controls whether invalid legacy input produces a clear build failure or
  another approved result. Do not silently discard the value.
- A source scan alone is insufficient: generated output must be inspected
  through the real Eleventy build before rejection is enabled.
- If the gate fails, the safe outcome is a documented transition state with
  compatibility retained; the task must not force a rejection merely to close
  the migration.

### Documentation

After successful cutover, update the maintained developer documentation to
remove transitional wording and state the final structured metadata and
legacy-input behavior. If the gate does not pass, document the remaining
compatibility state and the evidence gap instead.

### Task checklist

- [ ] Define and run the complete source/reference scan.
- [ ] Run and inspect a fresh production build.
- [ ] Record pass/fail evidence for every affected public route.
- [ ] Remove compatibility only after both evidence sets pass.
- [ ] Add and run the final legacy-input regression test.
- [ ] Update final documentation and parent requirement status.

### Requirement verification

- R5: The decisive check is a recorded pair: a repository-wide scan showing no
  remaining supported dependency on the legacy field, followed by a fresh
  `npm run build` whose post, home, blog, tag, and feed outputs contain the
  expected structured-author results. The legacy rejection change is applied
  only after both checks pass.
- Final invalid-input behavior: an integration test supplies legacy front
  matter through the normal content/build path and asserts the approved
  failure or handling behavior, rather than testing only a helper in
  isolation.

### Additional implementation verification

- Check the final route set against the pre-migration route inventory.
- Search generated output for stale legacy markers, missing names,
  `[object Object]`, malformed XML, and accidental empty author elements.
- Ensure documentation and test fixtures do not falsely claim that the legacy
  field remains supported after the gate closes.