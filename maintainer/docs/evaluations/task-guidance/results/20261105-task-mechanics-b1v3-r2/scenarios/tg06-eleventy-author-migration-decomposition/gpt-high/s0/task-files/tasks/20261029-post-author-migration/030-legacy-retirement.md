# Retire Legacy Author Metadata

Reject the legacy single-name author form only after source-content and production generated-output evidence demonstrates that no remaining content or output depends on it.

Parent Task: tasks/20261029-post-author-migration/000-main.md
Depends On: tasks/20261029-post-author-migration/020-authoring-content-migration.md

## Requirements checklist

- [ ] A complete source-content audit confirms all posts use the approved structured form.
- [ ] Production generated-output evidence confirms the migrated form supplies required author output.
- [ ] Build-time validation rejects legacy author metadata only after both audits pass.
- [ ] Regression coverage proves legacy input is rejected and structured input continues to build.

## Supporting details

- Current source has two posts, but the final audit must cover the complete content tree at execution time, not rely on today’s file count.
- A passing metadata unit test alone does not prove generated pages or feed no longer depend on the legacy form.

## Execution notes

This is the final dependent stage. Preserve legacy compatibility and defer strict validation if either source content or generated production output still relies on the legacy form. Record the actual audit method and production-build evidence when executing.