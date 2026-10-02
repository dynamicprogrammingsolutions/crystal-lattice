Parent Task: tasks/20260728-package-local-documentation-standard/000-main.md

Depends On:

- `tasks/20260728-package-local-documentation-standard/030-core-python-documentation-migration.md`
- `tasks/20260728-package-local-documentation-standard/040-application-and-plugin-documentation-migration.md`
- `tasks/20260728-package-local-documentation-standard/050-cross-package-and-reference-documentation-triage.md`

Specification:
`maintainer/docs/development/specifications/crystal-lattice-guidance-integration/index.md`

Requirement IDs:
`DOCPUB-004`–`DOCPUB-006`, `DOCVAL-003`

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
- [ ] Every published deep package and plugin page participates in a navigation
  hierarchy that provides active ancestry, a route to its owning index, and
  breadcrumbs or an equivalent visible path.
- [ ] Generated built-in-plugin README pages and published plugin-local docs
  are reachable from nested menu or owning-index routes without flattening
  every plugin into the global top level.
- [ ] A concise Getting Started entry point helps new users install, start,
  configure, connect to, and extend Crystal Lattice by linking canonical
  package documentation rather than duplicating it.
- [ ] Navigation and entry points are designed for specific intended audiences
  and common tasks so each audience can easily find the documentation it
  needs. Public pages do not have to name those audience classifications when
  doing so would not help their readers.
- [ ] The information-architecture pass may add, rewrite, move, or restructure
  a bounded set of documentation needed for useful entry points. Larger
  documentation work is proposed as separately approved follow-up tasks instead
  of expanding into project-wide rewriting or code archaeology.
- [ ] Link and route changes are documented in the migration inventory.

## Supporting details

### Current navigation baseline

Subtask 020 established an initial audience-oriented navigation baseline with:

- overview and guides;
- grouped registered packages;
- shared plugin development;
- reference and development material;
- a link back to the website.

The baseline still omits some published deep package pages from `nav`, exposes
only the built-in-plugin index rather than individual README leaves, and does
not assemble all plugin-local docs until subtask 040. Material for MkDocs
supports `navigation.path`; breadcrumbs only work for pages represented in the
configured hierarchy.

Navigation may remain manually curated. Automatic navigation generation is not
required unless it materially reduces registry/menu drift without changing the
approved public information architecture.

### Audience-oriented information architecture

Use concrete user journeys rather than repository provenance to organize entry
points. Relevant audiences include first-time users, application operators,
SDK and frontend integrators, plugin authors, package contributors, and
maintainers of cross-package contracts. These classifications guide design;
they are not mandatory headings or labels in public pages.

A likely top-level structure is:

```text
Getting Started
Guides
Packages
Plugin Development
Reference
Development
Website
```

The exact labels remain an implementation decision after migrated content is
available. Avoid listing the same page in several nav branches because active
ancestry becomes ambiguous. Prefer one canonical nav location plus links from
Getting Started and other audience-compatible indexes.

`docs/getting-started/index.md` is an appropriate root site entry point because
it coordinates several packages. It should curate canonical installation,
first-workspace, configuration, client-connection, package-selection, and
plugin-extension routes. Detailed instructions remain with the package that
owns them.

The architecture page handled by subtask 050 may be linked as an optional
conceptual next step, but contributor architecture must not block first
success.

### Compatibility principle

Moved source paths and moved public URLs are separate concerns:

- repository links should use canonical source paths;
- prepared compatibility pages or redirects may preserve old website URLs;
- compatibility pages contain only a short relocation notice/link or generated
  redirect behavior and are not authored duplicates of the full page.

Known mappings delivered by subtask 040:

| Old public route | Canonical route |
|---|---|
| `/plugins/application-config/` | `/packages/application-python/configuration/` |
| `/plugins/development/` | `/plugin-development/overview/` |

Root `DEVELOPMENT.md` moved to
`application/python/docs/development/terminal-and-http-features.md`; it had no
prepared-site route, but repository source links were updated.

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

1. Inspect the migrated page set by audience, common task, authority, and
   owning index; identify findability gaps without requiring audience labels in
   the pages themselves.
2. Create or refine the bounded Getting Started entry point and link canonical
   package quickstarts/guides.
3. Update MkDocs navigation to canonical prepared package and plugin paths,
   including deep pages needed for active ancestry.
4. Enable breadcrumb/path and previous/next behavior where supported and verify
   left-navigation state on representative deep routes.
5. Update `llmstxt` sections to canonical pages.
6. Search and update all repository references to moved source documents.
7. Add generated compatibility pages or configured redirects for old public
   URLs.
8. Update deployment path filters for registered package and plugin docs and
   READMEs.
9. Confirm shared plugin guides, generated plugin README pages, and
   plugin-local docs remain discoverable without an exhaustive global menu.
10. If useful entry points require a larger content rewrite than the bounded
    pages approved here, present and create separately approved follow-up tasks.
11. Record path mappings and audience-journey evidence in the migration
    inventory.

### Implementation decisions and open questions

- Initial URL compatibility is approved.
- Compatibility pages must remain generated or minimal and must not become
  competing full-content sources.
- Manual versus generated MkDocs nav is a local implementation decision unless
  it changes public grouping or URLs.
- Audience analysis guides navigation and content decisions but is not required
  to appear as explicit “Audience” prose in each public document.
- Limited new, moved, restructured, or rewritten entry-point documentation is
  approved. Broad package rewrites and code archaeology are not.
- If preserving every old URL requires a new MkDocs plugin or significant
  deployment behavior, propose the smallest compatible solution and record the
  tradeoff before expanding dependencies.

### Documentation

- `docs_site/mkdocs.yml`
- `docs_site/README.md`
- compatibility mapping/inventory
- `docs/getting-started/index.md` or a smaller existing-page refinement if that
  gives a complete first-success route without duplication
- repository README and AGENTS links
- workflow comments where path-filter intent is not obvious

### Task checklist

- [ ] Update MkDocs navigation.
- [ ] Update LLM page lists.
- [ ] Update source links.
- [ ] Add URL compatibility behavior.
- [ ] Update docs deployment triggers.
- [ ] Confirm plugin discoverability.
- [ ] Add Getting Started and audience-oriented entry routes.
- [ ] Add breadcrumbs, deep-page active ancestry, and previous/next behavior.
- [ ] Verify representative user journeys for each intended audience.
- [ ] Split larger documentation gaps into approved follow-up tasks when needed.
- [ ] Record path mappings.

### Requirement verification

| Requirement group | Acceptance evidence |
|---|---|
| Canonical navigation | Built site navigation opens canonical package pages and retains shared plugin/built-in sections. |
| Audience findability | Headed desktop/mobile journeys show that first-time users, operators, integrators, plugin authors, contributors, and contract maintainers can reach their likely starting documents without repository-path knowledge. |
| Deep-page orientation | Representative package and plugin deep pages show active navigation ancestry, breadcrumb/path context, and a route to the owning index. |
| Getting Started | A new user can follow installation, first-workspace, configuration, connection, package-selection, and extension routes without duplicated canonical instructions. |
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
- Exercise `packages/application-python/development/request-execution/` and
  representative deep plugin docs in headed Playwright at desktop and phone
  widths.
