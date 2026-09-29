Parent Task: tasks/20260728-package-local-documentation-standard/000-main.md

Depends On:

- `tasks/20260728-package-local-documentation-standard/010-documentation-standard-and-agent-guidance.md`
- `tasks/20260728-package-local-documentation-standard/020-package-docs-site-assembly.md`
- `tasks/20260728-package-local-documentation-standard/030-core-python-documentation-migration.md`

Specification:
`maintainer/specifications/documentation-and-specification-standard/index.md`

Requirement IDs:
`DOCREP-003`, `DOCMIG-003`, `DOCPUB-006`

# Cross-Package and Reference Documentation Triage

Inspect the cross-package architecture, endpoint parity plan, tool-host
protocol, and generated reference pipeline; relocate or normalize only what can
be established with bounded verification.

## Requirements checklist

- [ ] `ARCHITECTURE.md` is spot-checked and either relocated to
  `docs/development/architecture.md`, retained with rationale, or deferred.
- [ ] `application/python/agent_terminal_app/server_endpoints_parity.md` is
  compared with current public routes sufficiently to classify it as a living
  spec, a current gap document, a historical plan, or obsolete material.
- [ ] The endpoint parity page is moved, archived, retained, or deferred
  according to that classification without silently publishing stale
  `NEW`/`EXISTING` claims.
- [ ] Ownership of the tool-host protocol is explicitly decided as either a
  cross-package root contract or a package-owned contract.
- [ ] Duplicate tool-host protocol authoring sources are normalized.
- [ ] The relationship between package-local reference source directives,
  generated site output, and committed reference snapshots is documented and
  normalized as far as the approved scope allows.
- [ ] The stale OpenAI-compatible provider mkdocstrings directive/import path
  is corrected or explicitly deferred with a blocking reason.
- [ ] Any decision not completed without broad code reconstruction is recorded
  for the deferred migration inventory.

## Supporting details

### Candidate artifacts

- `ARCHITECTURE.md`
- `application/python/agent_terminal_app/server_endpoints_parity.md`
- `docs/reference/tool-host-protocol.md`
- `docs_site/source/reference/tool-host-protocol.md`
- `docs_site/source/reference/agent_core/**`
- `docs/reference/agent_core/**`
- `docs_site/source/reference/providers/openai_provider.md`
- `docs/reference/providers/openai_provider.md`
- `docs_site/scripts/refresh_reference_snapshots.py`

### Current generated-reference shape

- Mkdocstrings source directives live under `docs_site/source/reference/`.
- MkDocs generates site output under `docs_site/dist/reference/`.
- `refresh_reference_snapshots.py` copies generated Markdown-like output back
  to root `docs/reference/` for inspection.
- Root snapshots are not supposed to be MkDocs source input.

The approved direction prefers package-local reference source directives and
generated site output. Whether committed generated snapshots remain valuable
is explicitly reviewable and need not be forced if it would broaden this task.

### Tool-host protocol ownership

The protocol is implemented by:

- Python proxy/client code under `core/python/agent_core/tool_hosts/`;
- the Node host under `packages/tool-host-node/`.

Possible valid outcomes:

- keep it under root `docs/reference/` as a genuinely cross-package contract;
- designate Core Python as protocol owner and publish it from
  `core/python/docs/reference/`;
- designate the Node tool-host package as owner if that package is declared the
  protocol authority.

The chosen owner must be explicit and linked from both implementations.

### Provider reference issue

The current mkdocstrings directive points at:

```text
plugins.openai_provider
```

The current first-party package implementation is under:

```text
reference_openai_compatible_provider.provider
```

This is a documentation correctness issue and must not be preserved blindly
during relocation.

## Execution plan

Status: Draft

1. Spot-check architecture paths and major layer descriptions, then relocate or
   defer without rewriting the entire architecture.
2. Compare documented endpoint statuses with the current FastAPI route surface
   and classify the parity document.
3. Establish explicit tool-host protocol ownership and eliminate duplicate
   authored copies.
4. Map reference source directives, generated output, and snapshot use.
5. Move source directives package-locally where practical, update preparation
   and mkdocstrings paths, and avoid committing generated output as authored
   source.
6. Correct the provider directive to the active package/import target.
7. Record any deferred normalization with rationale and a future trigger.

### Implementation decisions and open questions

- Cross-package docs remain valid at root when no single package is the honest
  contract owner.
- Generated site output is preferred over duplicate authored/generated
  snapshots, but committed snapshot removal remains reviewable.
- Tool-host contract ownership and committed reference snapshot retention are
  material design decisions to resolve during this subtask using current
  consumers and build/release needs. If the choice would change public
  contract ownership or release packaging beyond this task, return the plan to
  Draft and request user approval.
- No requirement question is currently known; the possible outcomes above
  preserve the same requirement that ownership be explicit and duplication be
  normalized.

### Documentation

- Root or package-local architecture page
- Classified endpoint parity/specification page or archive note
- Canonical tool-host protocol page
- Reference-generation/source ownership guidance
- Updated references from Python and Node package docs

### Task checklist

- [ ] Classify and handle architecture document.
- [ ] Classify and handle endpoint parity plan.
- [ ] Decide tool-host protocol owner.
- [ ] Normalize duplicate protocol sources.
- [ ] Map and normalize reference source/output roles.
- [ ] Correct provider reference directive.
- [ ] Record deferred decisions or migration items.

### Requirement verification

| Requirement group | Acceptance evidence |
|---|---|
| Architecture | Major referenced paths/layers are spot-checked and the page has a recorded relocate/retain/defer outcome. |
| Endpoint parity | Route inspection supports its classification; stale statuses are not presented as current without correction. |
| Tool-host protocol | One canonical authored source exists, ownership is stated, and both Python and Node implementations link to it. |
| Generated reference | Build docs clearly identify authored directives, generated outputs, and any retained snapshots; pipeline produces expected reference pages. |
| Provider reference | Mkdocstrings imports the current provider package or completion notes identify an explicit blocker. |

### Additional implementation verification

- Inspect current FastAPI route declarations rather than reconstructing server
  behavior beyond endpoint classification.
- Build the affected mkdocstrings reference pages.
- Search for duplicate protocol content and stale provider import references.
- Verify links from `packages/tool-host-node`, Core tool-host code docs, and
  plugin docs.
