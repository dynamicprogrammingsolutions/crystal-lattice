# 050 — Legacy-dependency gate and rejection of the legacy form

Evaluate the evidence gate showing nothing still depends on the legacy
single-name form, then reject it with an explicit build-time error and land
the final documentation state.

Parent Task: tasks/20260919-author-metadata-migration/000-main.md
Depends On:
- tasks/20260919-author-metadata-migration/010-author-model-and-compat.md
- tasks/20260919-author-metadata-migration/020-templates-feed-and-archives.md
- tasks/20260919-author-metadata-migration/030-authoring-tool.md
- tasks/20260919-author-metadata-migration/040-migrate-existing-posts.md

## Requirements checklist

- [ ] R9: gate evidence recorded (content scan: zero legacy usage in
      `content/`; authoring tool emits only the structured form; full
      build/test suite green) before any rejection change.
- [ ] R9 (slice): legacy `author:` is rejected by an explicit build-time error
      listing offending files (mechanism per approved D2).
- [ ] R8 (final): full suite collects and exits cleanly after the rejection
      change.
- [ ] R10: `README.md` updated in the same reviewed change — transitional
      note removed, legacy form documented as rejected with the error
      behavior and an example of the accepted form.

## Tasks

- [ ] Record gate evidence: content scan of `content/` for legacy scalar
      usage, 030 tool output check, full suite + production build run.
- [ ] Remove legacy acceptance from the normalization path.
- [ ] Add the build-time rejection check with a clear error naming offending
      files; add a test that a legacy-form post fails the build with the
      documented error.
- [ ] Re-run the full suite and production build; verify no scratch or fixture
      leakage into production `content/`.
- [ ] Update `README.md` to the final rejection state (same change as the
      rejection code).

## Verification

- Full `node --test tests/*.test.js` run passes including the new
  legacy-rejection test.
- Production build of the real site succeeds; `README.md` matches the
  implemented behavior.

## Notes

- Do not start this subtask until D2 is approved and all dependency evidence
  exists.
- If the gate cannot be satisfied (e.g. a consumer or content file still
  depends on the legacy form), stop, report the blocker, and keep the
  compatibility path in place.