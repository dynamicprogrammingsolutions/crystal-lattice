Parent Task: tasks/20260728-package-local-documentation-standard/000-main.md

# Documentation Standard and Agent Guidance

Create the canonical repository documentation and specification standards,
define package documentation profiles, and update agent routing without adding
boilerplate or reconstructed documentation to every package.

## Requirements checklist

- [ ] `docs/development/index.md` provides a concise map to repository-wide
  development documentation.
- [ ] `docs/development/documentation-structure.md` documents package profiles,
  artifact roles, ownership, source-of-truth rules, incremental adoption, and
  generated-site boundaries.
- [ ] `docs/development/specification-driven-development.md` documents product
  specifications, technical specifications, requirements traceability,
  architecture decisions, lifecycle, testing relationships, and task-file
  relationships.
- [ ] Root `AGENTS.md` contains concise routing and update guidance and points to
  the full standard.
- [ ] The standard does not require placeholder pages, duplicated boilerplate,
  or broad reverse engineering of undocumented packages.
- [ ] Initial major package roots receive or refine `AGENTS.md`,
  `docs/index.md`, and `docs/quickstart.md` only where the approved package
  profile requires them and existing verified material can support them.
- [ ] The approved decision register in the parent task remains reflected in
  the authored standard and remains reviewable.

## Supporting details

### Approved model

The full rationale, research references, package profiles, documentation roles,
specification convention, lifecycle, and approved decision register are in:

- `tasks/20260728-package-local-documentation-standard/000-main.md`

The standard should preserve the distinction between:

- concise repository/package routing in `AGENTS.md`;
- first-use and installation guidance in README and quickstart;
- package-user documentation in `<package>/docs/`;
- contributor and internals documentation in
  `<package>/docs/development/`;
- root cross-package guidance in `docs/development/`;
- generated reference and site outputs.

### Proposed root `AGENTS.md` text

Use this as the baseline, adapting links and wording only as necessary:

```markdown
## Documentation ownership and workflow

Documentation is authored next to the package or subsystem that owns it.

- Start package work by reading the package `README.md`, nearest `AGENTS.md`,
  and `docs/index.md` when present.
- Keep `README.md` concise: purpose, installation, first use/build/test, and
  pointers to detailed documentation.
- Put package-user documentation under `<package>/docs/`.
- Put package internals, contributor workflows, architecture, and
  specifications under `<package>/docs/development/`.
- Keep root `docs/` for repository-wide guidance and genuinely cross-package
  contracts. Do not use it as the default location for package documentation.
- Treat package-local files as the source of truth. `docs_site/prepared/` and
  `docs_site/dist/` are generated outputs and must not be edited directly.
- Before implementing a substantive new capability, create or update the
  owning package's specification under
  `docs/development/specifications/<feature>/`.
- Use stable requirement IDs for important acceptance behavior and record
  implementation, verification, documentation, task, and delivery evidence.
  Keep execution steps in `tasks/`; do not duplicate the task plan in a spec.
- Update specifications when behavior changes during implementation. Update
  user documentation, tests, and requirements evidence before completion.
- Do not invent a documentation baseline by reconstructing large areas of
  unfamiliar code. Document facts verified during the current work and record
  larger documentation gaps for later migration.

See:

- `docs/development/documentation-structure.md`
- `docs/development/specification-driven-development.md`
```

### Package entry-point principle

Do not create nearly empty `AGENTS.md`, `docs/index.md`, or
`docs/quickstart.md` across every plugin. The approved package profiles permit
README-only small packages and inherited parent guidance.

For a major package that lacks the full structure, use existing README and
verified documentation to create concise routing pages. Do not fabricate
long-form content merely to complete the shape.

## Execution plan

Status: Draft

1. Write the root development documentation index and the two standards pages.
2. Move documentation-maintenance principles from root `AGENTS.md` into the
   full standard where explanation is valuable, while retaining concise
   actionable routing in `AGENTS.md`.
3. Preserve or expand the remaining root `AGENTS.md` guidance when it helps an
   agent choose the correct package, tests, or documentation owner.
4. Classify initial package roots using the approved profiles.
5. Add only concise, evidence-backed entry points needed by the first migration
   packages.
6. Update repository-level links to the new standards.

### Implementation decisions and open questions

- Package profiles, publication behavior, proportional specifications, living
  specs, and traceability granularity are approved in the parent task's
  decision register.
- No requirement questions are open.
- If a package cannot be confidently classified using existing manifests and
  repository ownership, record it for the deferred inventory instead of
  inventing a classification.

### Documentation

- `docs/development/index.md`
- `docs/development/documentation-structure.md`
- `docs/development/specification-driven-development.md`
- root `AGENTS.md`
- initial package entry-point docs required by the approved profiles

### Task checklist

- [ ] Write the documentation structure standard.
- [ ] Write the specification-driven development standard.
- [ ] Create the root development docs index.
- [ ] Update root agent routing.
- [ ] Classify initial package profiles.
- [ ] Add concise package entry points where required and supportable.
- [ ] Update links to the standards.

### Requirement verification

| Requirement group | Acceptance evidence |
|---|---|
| Documentation structure | Human inspection confirms artifact roles, package profiles, ownership, source-of-truth, root-doc exception, generated-output rule, and incremental adoption are explicit. |
| Specification workflow | Human inspection confirms product/technical/requirements distinctions, lifecycle, stable IDs, evidence fields, tasks relationship, and proportional use. |
| Agent guidance | Root `AGENTS.md` routes agents to package docs and full standards without duplicating the full pages. |
| No filler/reconstruction | Changed package entry points are short, link to verified existing content, and contain no unsupported baseline claims. |

### Additional implementation verification

- Check all new relative links from root and package `AGENTS.md`.
- Confirm the standard preserves all approved decisions from the parent task.
- Search for contradictory root documentation-maintenance guidance and update
  or explicitly retain it.
