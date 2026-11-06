# Migrate existing posts to the structured form

Convert all existing post front matter from the legacy single-name `author`
field to the structured multi-author form, proving production-build output
parity for every generated file. The build still accepts the legacy form after
this subtask (retirement is 030); repository content simply no longer uses it.

Parent Task: tasks/20261029-post-author-migration/000-main.md

Depends On: tasks/20261029-post-author-migration/010-introduce-multi-author-model.md

## Requirements checklist

- [ ] Every file in `content/posts/` uses only the structured authors form; no
      legacy `author:` key remains anywhere in `content/`.
- [ ] A production build after the migration is byte-identical to the
      pre-migration build for every generated file (home, archive, tag pages,
      post pages, feed, sitemap).
- [ ] The parity comparison result and the content scan are recorded in this
      task file as the gate evidence later consumed by 030.
- [ ] The full test suite remains green, including the 010 integration pins
      against the migrated content.

## Supporting details

- Only two posts exist: `content/posts/first.md` (Ada Example) and
  `content/posts/second.md` (Grace Example); each becomes a one-element
  structured list per approved D1.
- `_site/` is gitignored; keep baseline snapshots in a temp location outside
  version control and do not commit them.
- This subtask changes only content files. If output parity fails, stop and
  investigate the 010 normalization/model path — do not "fix" templates here.

## Execution plan

Status: Draft

1. Build at the current state and hash every file under `_site/` (baseline
   snapshot in a temp directory).
2. Rewrite the two posts' front matter to the structured form (mechanical
   one-element lists).
3. Rebuild and compare hashes for every generated file; any diff is a defect
   in the model/normalization work — investigate before proceeding.
4. Scan `content/` for the legacy `author:` key (expected: no matches).
5. Run `npm test`; confirm the 010 integration pins still pass against the
   migrated content.
6. Record the parity result, scan result, and suite status in
   `## Implementation Notes` — this is the R5 gate evidence.

### Implementation decisions and open questions

- None new; shape and rendering follow the decisions approved on the parent.

### Documentation

- None: the 010 README wording ("legacy still accepted during migration")
  remains accurate after content migration; it is rewritten in 030.

### Task checklist

- [ ] Baseline build + hash snapshot captured before any content edit.
- [ ] `content/posts/first.md` and `content/posts/second.md` converted.
- [ ] Post-migration hash comparison run — all generated files identical.
- [ ] Legacy-key content scan run — no matches in `content/`.
- [ ] `npm test` green.
- [ ] Gate evidence recorded in `## Implementation Notes` and referenced by
      the parent checklist.

### Requirement verification

- Safe content migration (R4): the hash comparison over the real production
  build output before/after the content edit — decisive, full-surface, no
  mocked rendering.
- Content fully migrated (R4): the repository content scan showing no legacy
  `author:` keys.
- Suite green: `npm test` collects and exits cleanly.
