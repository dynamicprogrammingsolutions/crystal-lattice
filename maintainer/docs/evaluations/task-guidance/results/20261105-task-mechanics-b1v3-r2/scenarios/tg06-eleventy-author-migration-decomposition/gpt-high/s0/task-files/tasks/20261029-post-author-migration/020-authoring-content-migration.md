# Migrate Authoring and Existing Posts

Update the post authoring tool and existing post metadata to use the approved structured multi-author form while preserving every existing author name.

Parent Task: tasks/20261029-post-author-migration/000-main.md
Depends On: tasks/20261029-post-author-migration/010-transitional-rendering.md

## Requirements checklist

- [ ] The new-post tool emits the approved structured author metadata.
- [ ] Every existing post is migrated without losing its author information.
- [ ] Maintained authoring guidance documents the supported form.
- [ ] The migrated content builds through the production Eleventy path.

## Supporting details

- `scripts/new-post.js` currently takes one author string and emits `author: "..."`.
- `content/posts/first.md` and `content/posts/second.md` are the only current post records; they have distinct single authors.
- `README.md` is the only package-level user-facing guidance currently present.

## Execution notes

Wait for the structured author schema and helper interface decision in `tasks/20261029-post-author-migration/000-main.md`. Keep legacy acceptance enabled in this stage; retirement and strict rejection belong to `tasks/20261029-post-author-migration/030-legacy-retirement.md`.