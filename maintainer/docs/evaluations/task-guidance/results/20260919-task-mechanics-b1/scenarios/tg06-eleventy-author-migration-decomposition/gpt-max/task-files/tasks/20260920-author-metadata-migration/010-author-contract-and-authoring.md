# Define the author contract and migrate authoring input

Establish the canonical `authors` data contract and the temporary
compatibility boundary, then make the post-authoring helper emit canonical
front matter without prematurely breaking existing callers or content.

Parent Task: tasks/20260920-author-metadata-migration/000-main.md

Depends On: None

## Requirements checklist

- [ ] Define an ordered, non-empty canonical author collection and the
  required display identity for each entry.
- [ ] Normalize a legacy scalar `author` to one canonical author during the
  transition, while making the legacy/canonical collision behavior explicit.
- [ ] Make `scripts/new-post.js` produce canonical `authors` front matter for
  one or multiple authors and preserve safe compatibility for existing
  single-author callers until the retirement gate.
- [ ] Add focused evidence for normalization, serialization, ordering, and
  invalid/ambiguous input.
- [ ] Document the canonical authoring example in the maintained documentation
  owned by this capability.

## Research and supporting facts

- `scripts/new-post.js` currently exports a two-argument
  `frontMatter(title, author)` helper and writes `author: "..."`.
- No Eleventy data normalization or front-matter validation exists in
  `eleventy.config.js`.
- The current post layout receives front-matter fields directly, so changing
  the source field without a shared boundary would create inconsistent
  transition behavior across templates.
- There are no executable tests for the helper or the legacy transition.

## Execution plan

Status: Draft

After the canonical element shape is approved, introduce one normalization
and validation boundary in the Eleventy data path. It should expose only the
canonical collection to downstream templates, adapt a legacy scalar while the
migration is in progress, and identify both-field or malformed input with a
targeted error. Update the exported helper so its canonical output is stable
and YAML-safe for one and multiple authors; if its old scalar call shape is
retained temporarily, it must still write `authors`, not recreate `author`.
Add tests that exercise the helper and the production data boundary rather
than mocking the fields. Keep the compatibility branch available until the
retirement subtask proves it can be removed.

### Implementation decisions and open questions

- Resolve whether an item is a string or a record with required `name`;
  the parent recommendation is the record form.
- Resolve whether both fields fail immediately; the parent recommendation is
  to fail rather than apply precedence.
- Preserve author order exactly as supplied. Do not sort, deduplicate, or
  infer author identity from display text.
- Treat empty author collections and blank names as invalid input, with the
  exact diagnostic tested at the boundary.

### Documentation

- Extend `README.md` (or the smallest approved owning document) with the
  canonical front-matter example and the one/multiple-author input rule.
- Describe the compatibility behavior as transitional only; do not claim
  legacy rejection until the retirement child completes it.

### Task checklist

- [ ] Confirm canonical item shape and validation/collision semantics.
- [ ] Add the shared compatibility normalization and validation boundary.
- [ ] Update `scripts/new-post.js` to serialize canonical one/multiple-author
  metadata safely.
- [ ] Add production-boundary tests for canonical input, legacy adaptation,
  malformed input, and ambiguous dual input.
- [ ] Update the maintained authoring guidance.

### Requirement verification

- The canonical contract is proven by parsing helper output through the same
  data path used by Eleventy pages, with one and multiple ordered entries.
- Transition safety is proven by a representative legacy front matter input
  producing the same normalized one-author value without a template-specific
  fallback.
- Authoring compatibility is proven by tests of the exported helper’s
  canonical output and any retained scalar call form.
- Validation is proven by production-path failures for blank/empty and
  ambiguous metadata, not by a mock that bypasses Eleventy data loading.