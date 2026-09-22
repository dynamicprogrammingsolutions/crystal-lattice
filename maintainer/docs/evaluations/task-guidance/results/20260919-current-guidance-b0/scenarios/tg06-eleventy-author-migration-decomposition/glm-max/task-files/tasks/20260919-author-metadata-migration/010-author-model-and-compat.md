# 010 — Author model and compatibility layer

Define the canonical structured multi-author author field and a normalization
step that yields a uniform authors list from either the new form or the legacy
single-name scalar, so every downstream consumer reads one view. No consumer or
content changes in this subtask.

Parent Task: tasks/20260919-author-metadata-migration/000-main.md
Depends On:

## Requirements checklist

- [ ] R1 (slice): canonical `authors` model implemented per the approved shape
      decision (000-main, decision D1).
- [ ] R6 (slice): legacy scalar `author:` posts normalize to the same uniform
      authors list as new-form posts, so mixed content builds correctly.
- [ ] R8 (slice): unit tests cover normalization of the new form, the legacy
      scalar, and their equivalence in output shape.

## Tasks

- [ ] `npm install` (dependencies absent in this worktree); record the
      installed Eleventy version.
- [ ] Capture a baseline production build of the current content into a
      gitignored/temporary output directory as the comparison artifact for
      020/040.
- [ ] Implement the canonical `authors` model and normalization (e.g.
      Eleventy computed data on the posts collection or an equivalent data
      step) so every post exposes a uniform authors list; legacy `author:`
      maps into it unchanged in behavior.
- [ ] Add unit tests for normalization: new-form list input, legacy scalar
      input, and shape equivalence between the two.

## Verification

- Unit tests for both forms pass and collect cleanly under
  `node --test tests/*.test.js`.
- Production build of unchanged content still succeeds and produces output
  matching the pre-change baseline (no consumer behavior change yet).

## Notes

- Blocked until the D1 shape decision in 000-main is approved.
- Do not touch templates, feed, authoring tool, or content in this subtask.