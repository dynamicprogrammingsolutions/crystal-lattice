Parent Task: tasks/20260728-package-local-documentation-standard/000-main.md

Depends On:

- `tasks/20260728-package-local-documentation-standard/030-core-python-documentation-migration.md`
- `tasks/20260728-package-local-documentation-standard/040-application-and-plugin-documentation-migration.md`
- `tasks/20260728-package-local-documentation-standard/050-cross-package-and-reference-documentation-triage.md`

# Navigation, Compatibility, and Build Triggers

Update documentation navigation, LLM indexes, repository links, compatibility
paths, and deployment triggers after canonical migration destinations are
known.

## Requirements checklist

- [ ] MkDocs navigation points to canonical package-local documentation through
  prepared site destinations.
- [ ] LLM documentation sections point to canonical prepared paths.
- [ ] Root and package READMEs, AGENTS files, source comments, and documentation
  links no longer point to moved source paths except where a compatibility page
  is intentionally referenced.
- [ ] Existing public documentation URLs affected by migration resolve through
  compatibility pages or redirects.
- [ ] Compatibility behavior does not create a second editable source of truth.
- [ ] The static-site deployment workflow triggers for registered package
  README and documentation sources.
- [ ] Package registry or assembly changes also trigger the docs build.
- [ ] Navigation changes preserve existing plugin and built-in-plugin
  discoverability.
- [ ] Link and route changes are documented in the migration inventory.

## Supporting details

### Current navigation

`docs_site/mkdocs.yml` currently contains manually maintained sections for:

- root overview and guides;
- copied plugin development docs;
- generated built-in plugin README pages;
- Core SDK and event guides;
- generated/default reference.

The package assembly work introduces public prepared paths such as:

```text
packages/core-python/
packages/application-python/
```

Navigation may remain manually curated in this task. Automatic navigation
generation is not required unless it materially simplifies the implementation
without changing approved public information architecture.

### Compatibility principle

Moved source paths and moved public URLs are separate concerns:

- repository links should use canonical source paths;
- prepared compatibility pages or redirects may preserve old website URLs;
- compatibility pages contain only a short relocation notice/link or generated
  redirect behavior and are not authored duplicates of the full page.

### Current workflow gap

`.github/workflows/deploy-static-sites.yml` does not generally watch:

- `core/python/docs/**`
- `application/python/docs/**`
- `packages/*/docs/**`
- package READMEs used as documentation-site sources

The workflow must trigger when any registered public source changes. A
maintainable broad path pattern is acceptable if an exact generated list would
be brittle.

## Execution plan

Status: Draft

1. Update MkDocs navigation to canonical prepared package paths.
2. Update `llmstxt` sections to canonical pages.
3. Search and update all repository references to moved source documents.
4. Add generated compatibility pages or configured redirects for old public
   URLs.
5. Update deployment path filters for registered package docs and READMEs.
6. Confirm existing plugin/built-in pages remain discoverable.
7. Record path mappings in the migration inventory.

### Implementation decisions and open questions

- Initial URL compatibility is approved.
- Compatibility pages must remain generated or minimal and must not become
  competing full-content sources.
- Manual versus generated MkDocs nav is a local implementation decision unless
  it changes public grouping or URLs.
- If preserving every old URL requires a new MkDocs plugin or significant
  deployment behavior, propose the smallest compatible solution and record the
  tradeoff before expanding dependencies.

### Documentation

- `docs_site/mkdocs.yml`
- `docs_site/README.md`
- compatibility mapping/inventory
- repository README and AGENTS links
- workflow comments where path-filter intent is not obvious

### Task checklist

- [ ] Update MkDocs navigation.
- [ ] Update LLM page lists.
- [ ] Update source links.
- [ ] Add URL compatibility behavior.
- [ ] Update docs deployment triggers.
- [ ] Confirm plugin discoverability.
- [ ] Record path mappings.

### Requirement verification

| Requirement group | Acceptance evidence |
|---|---|
| Canonical navigation | Built site navigation opens canonical package pages and retains shared plugin/built-in sections. |
| LLM outputs | Generated `llms.txt`/`llms-full.txt` include canonical migrated pages. |
| Source links | Repository-wide search finds no unintended references to old source locations. |
| URL compatibility | Each moved public route has a tested compatibility page/redirect or an explicitly approved exception. |
| Workflow triggers | Workflow path filters include package-local docs and README sources used by the registry. |

### Additional implementation verification

- Run the docs preparation and normal build.
- Inspect old and new route outputs under `docs_site/dist/`.
- Review workflow path patterns against all registry entries.
- Check representative links from root README, package README, AGENTS, and
  plugin docs.
