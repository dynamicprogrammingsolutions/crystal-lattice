# Migrate existing post content to structured authors

Convert the existing posts' front matter from the legacy single-name `author`
field to the structured multi-author model, preserving values exactly and
proving through the production build that generated output is unchanged.

Parent Task: tasks/20260926-author-metadata-migration/000-main.md

Depends On: tasks/20260926-author-metadata-migration/010-structured-authors-adoption.md
(the structured model must exist and the build-output evidence must be in
place before content switches to it)

## Requirements checklist

- [ ] `content/posts/first.md` and `content/posts/second.md` use only the
      structured model; the legacy `author` field is removed from them.
- [ ] Author values are preserved exactly and in order: "Ada Example" and
      "Grace Example".
- [ ] Generated output after migration is unchanged versus the pre-migration
      output: post page author lines and feed author elements stay identical
      (proven by the production-build assertions from 010, now exercising the
      structured path).
- [ ] No content file retains or introduces the legacy field after migration
      (repo-wide content scan clean).
- [ ] Documentation contains no stale claim that existing posts still use the
      legacy form (no behavioral change is introduced by this stage).

## Supporting facts

- Current front matter to migrate:
  - `content/posts/first.md`: `author: "Ada Example"`
  - `content/posts/second.md`: `author: "Grace Example"`
- Conversion is mechanical and value-preserving (1:1): the legacy string
  becomes a single structured entry carrying the same name, in file order.
- Both posts are single-author, so their canonical rendered output must be
  byte-identical before and after migration — this is exactly what the 010
  equivalence assertions are designed to prove.
- If an unexpected front matter shape is found during migration (missing
  author, non-string value), report it instead of inventing a default; no
  fallback behavior is specified.

## Execution plan

Status: Draft

- Convert both content files to the approved structured schema (Q1), removing
  the legacy field from each.
- Run the production build and the full test suite. The 010 build-output
  assertions (which pin the exact legacy-era author strings) must pass after
  migration — passing through the structured path is the output-unchanged
  proof for this stage.
- Run a content scan confirming no `author:` legacy field remains under
  `content/`.
- Documentation: no behavior change in this stage (dual acceptance is still
  the supported behavior); verify no maintained doc claims existing posts use
  the legacy form, and leave the rest unchanged.

Execution tasks:

1. Migrate `content/posts/first.md` to the structured form.
2. Migrate `content/posts/second.md` to the structured form.
3. Production build + full test suite (equivalence assertions pass).
4. Content scan for residual legacy fields.
5. Check maintained docs for stale claims.

### Implementation decisions and open questions

- None new. The schema is fixed by the approved answer to parent Q1. The
  conversion is mechanical; any anomaly in existing front matter is reported,
  not silently normalized.

### Documentation

- No user-facing change is made here; supported behavior (dual acceptance)
  is unchanged. Only a stale-claims check is in scope for this stage.

### Task checklist

- [ ] `content/posts/first.md` migrated, value preserved
- [ ] `content/posts/second.md` migrated, value preserved
- [ ] Production build + tests clean (output unchanged)
- [ ] Content scan shows no legacy `author:` field
- [ ] Docs checked for stale legacy-content claims

### Requirement verification

- Values preserved and legacy removed (parent R4): front-matter inspection of
  both files plus the content scan.
- Output unchanged (parent R2, R4): the production-build assertions from 010
  pin the exact author strings; they pass after migration while reading the
  structured field — real build output, not a mocked cascade.
- Gate contribution (parent R5): the clean content scan and passing build
  from this stage are the content half of the 030 gate; 030 re-verifies it
  fresh rather than assuming it.