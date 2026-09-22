# Migrate existing post source content

Convert every repository post to the canonical multi-author front matter
after the compatibility boundary exists, preserving content identity and
leaving auditable evidence that no source post still requires the legacy
field.

Parent Task: tasks/20260920-author-metadata-migration/000-main.md

Depends On: tasks/20260920-author-metadata-migration/010-author-contract-and-authoring.md

## Requirements checklist

- [ ] Inventory all post-like source files and front-matter locations before
  editing them.
- [ ] Convert every legacy `author` value to one canonical author entry,
  preserving each name, source order, title, body, tags, and route inputs.
- [ ] Verify the migrated content through the real Eleventy build while the
  compatibility path is still available.
- [ ] Produce a scoped source audit showing no legacy post field remains and
  distinguishing intentional migration documentation/tests from production
  content.

## Research and supporting facts

- The known source inventory is `content/posts/first.md` and
  `content/posts/second.md`; both use the scalar field.
- `content/posts/posts.json` applies the common post layout and `posts` tag,
  so source migration must preserve collection membership.
- No explicit permalink appears in either post; route stability therefore
  depends on preserving filenames and Eleventy defaults.
- The repository has no migration utility or content validation test today.

## Execution plan

Status: Draft

Run a repository-scoped inventory over Markdown, JSON data, templates, helper
code, and tests before changing source. After subtask 010 establishes
normalization, convert the known posts (and any inventory discoveries) to the
approved canonical form. Review the source diff for exact author names and
order, unchanged bodies, titles, and collection metadata. Build the site
before legacy rejection so the transitional adapter proves that the migrated
canonical content and any remaining compatibility fixtures coexist. Finish
with a source scan whose scope is explicit and whose result is consumable by
the retirement gate.

For the small current inventory, a reviewed one-off content edit is
preferable to adding a permanent migration script; if the inventory grows,
use a repeatable transformation with a dry-run/diff check and do not leave
generated artifacts in source control.

### Implementation decisions and open questions

- Confirm whether any content outside `content/posts/` is an approved post
  source before declaring the inventory complete.
- Do not normalize names by trimming, sorting, deduplicating, or changing
  spelling unless the source review explicitly identifies an error.
- Keep any temporary inventory/migration report outside the repository or
  remove it before handoff; the durable evidence is the source scan and
  tested build.

### Documentation

- The canonical content example belongs in the authoring documentation
  maintained by subtask 010; do not add a second source-format guide here.
- Record the final migrated file inventory in task evidence, not as a
  generated documentation artifact.

### Task checklist

- [ ] Inventory all candidate post/front-matter sources.
- [ ] Convert every legacy post field to the approved canonical form.
- [ ] Review the diff for author identity/order and unchanged post metadata.
- [ ] Build the migrated site while compatibility remains enabled.
- [ ] Run and preserve the scoped no-legacy-source audit for subtask 040.

### Requirement verification

- Inventory completeness is proven by a scoped search covering all supported
  content extensions and front-matter locations.
- Data preservation is proven by source diff review plus comparison of
  title/body/tag/route inputs, not by checking only the new author field.
- Canonical content is proven by a real Eleventy build that renders every
  migrated post and retains its collection membership.
- Legacy retirement input is proven only when the source audit has no
  production `author` field and the consumer scan separately has no stale
  legacy lookup.