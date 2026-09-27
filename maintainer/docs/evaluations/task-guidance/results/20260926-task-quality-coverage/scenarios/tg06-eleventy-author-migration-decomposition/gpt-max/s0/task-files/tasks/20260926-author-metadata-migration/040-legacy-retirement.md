# Close the transition with an evidence-gated legacy decision

Own the final compatibility state. Assemble source and generated-output
evidence from the preceding work, then either remove the legacy fallback and
reject `author` input or explicitly retain it as supported. No rejection is
allowed before the gate passes.

Parent Task: tasks/20260926-author-metadata-migration/000-main.md
Depends On:
- tasks/20260926-author-metadata-migration/020-rendering-output.md
- tasks/20260926-author-metadata-migration/030-content-authoring.md

## Requirements checklist

- [ ] Do not reject legacy input while any supported content, template, feed,
  archive, or authoring path still depends on it.
- [ ] Assemble content-scan, runtime-reference, and generated-output evidence
  proving the canonical model is used throughout the supported site.
- [ ] Apply the approved final state only after the evidence gate passes:
  remove the fallback and reject legacy input with a clear diagnostic, or
  retain the fallback and document it as supported.
- [ ] Run the production build and executable tests again after the final state
  is selected.
- [ ] Leave maintained documentation consistent with the resulting
  compatibility state.

## Requirement questions and decisions

- **Question:** Confirm whether this migration will end by rejecting legacy
  `author` or by retaining a documented compatibility fallback.
- **Recommendation:** Prefer explicit rejection after a clean gate if the
  project wants to prevent regression, but do not make that choice silently.
- **Decision required by the request:** The gate must include both source
  content evidence and generated-output evidence; a repository search alone is
  insufficient.

## Research and supporting facts

- Existing content currently contains the legacy key, so source migration must
  precede any rejection.
- The post layout and feed are current legacy consumers; archive/list surfaces
  require an explicit audit because their shared include currently renders
  only titles and links.
- The existing generated-output tests are placeholders, so the gate must wait
  for executable build assertions from the rendering and content subtasks.
- Task files and documentation may mention the legacy field as historical or
  transition information; the runtime/content audit must classify those
  mentions rather than treating every textual occurrence as a product
  dependency.

## Execution plan
Status: Draft

Collect the completed evidence from the schema, rendering, and
content/authoring tasks. Before changing compatibility behavior, run a clean
inventory over all post source files, inspect runtime references in templates,
configuration, scripts, and tests, and run the real production build with the
canonical content. Confirm that the required post, home, archive, tag, feed,
and sitemap outputs contain the expected values and no legacy-derived
undefined or malformed data.

Treat the gate as a checklist with an explicit recorded result:

1. Every supported post source has the canonical field and no legacy
   front-matter key.
2. All supported consumers use normalized/canonical authors; any remaining
   legacy reference is an intentional transition fixture, diagnostic, or
   historical documentation.
3. Generated-output assertions pass for singleton and multi-author content
   across the real Eleventy build.
4. The authoring helper emits only canonical front matter and its generated
   content has passed through the production build.

Only after all four conditions pass may the chosen final state be applied. If
rejection is selected, remove the compatibility fallback at the agreed
boundary, add a focused negative assertion for legacy input, and run the
complete build/tests again. If compatibility is retained, keep the fallback,
add no premature rejection, and document its supported scope and evidence
requirements for a later removal.

### Implementation decisions and open questions

- The final reject-versus-retain decision is still open.
- A negative test is appropriate only if rejection is approved; it must not
  cause the transition build to fail before the gate.
- The final audit must distinguish intentional test fixtures from accidental
  production dependencies.

### Documentation

Update the maintained development documentation with the final supported
field, authoring behavior, and compatibility state. If rejection is enabled,
document the diagnostic and migration expectation; if fallback is retained,
document that legacy input remains supported and why.

### Task checklist

- [ ] Receive and review the schema, rendering, and content/authoring evidence.
- [ ] Run the complete content and runtime reference audit.
- [ ] Run the clean generated-output gate across all required surfaces.
- [ ] Resolve the final compatibility state.
- [ ] Apply rejection only after the gate passes, if approved.
- [ ] Re-run build/tests and update maintained documentation.
- [ ] Hand the immutable evidence and any deferred compatibility decision to
  the parent task.

### Requirement verification

- Record the exact content scan, runtime-reference classification, and
  generated-output results before any legacy rejection.
- If rejection is selected, run a post-gate negative check showing legacy
  input is rejected at the approved boundary, followed by a clean production
  build of all migrated content.
- If fallback is retained, run the clean canonical build and verify that the
  remaining compatibility path is intentional, isolated, and documented.
- Verify that all required generated surfaces still build and that routes,
  titles, tags, feed output, and sitemap output remain intact after the final
  compatibility-state change.

### Additional implementation verification

- Search for raw legacy reads/writes in supported runtime paths after the final
  state change.
- Check diagnostics for actionable source location and field information.
- Check that evidence and documentation do not accidentally present a
  target-only rejection policy as current behavior before it is implemented.