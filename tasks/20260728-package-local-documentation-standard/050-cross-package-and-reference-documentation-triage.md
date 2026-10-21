Parent Task: tasks/20260728-package-local-documentation-standard/000-main.md

Depends On:

- `tasks/20260728-package-local-documentation-standard/010-documentation-standard-and-agent-guidance.md`
- `tasks/20260728-package-local-documentation-standard/020-package-docs-site-assembly.md`
- `tasks/20260728-package-local-documentation-standard/030-core-python-documentation-migration.md`

Specification:
`maintainer/docs/development/specifications/crystal-lattice-guidance-integration/index.md`

Requirement IDs:
`DOCREP-003`, `DOCMIG-003`, `DOCPUB-006`

# Cross-Package and Reference Documentation Triage

Inspect the cross-package architecture, endpoint parity plan, tool-host
protocol, and generated reference pipeline; relocate or normalize only what can
be established with bounded verification.

## Requirements checklist

- [x] `ARCHITECTURE.md` is spot-checked and either relocated to
  `docs/development/architecture.md`, retained with rationale, or deferred.
- [x] `application/python/agent_terminal_app/server_endpoints_parity.md` is
  compared with current public routes sufficiently to classify it as a living
  spec, a current gap document, a historical plan, or obsolete material.
- [x] The endpoint parity page is moved, archived, retained, or deferred
  according to that classification without silently publishing stale
  `NEW`/`EXISTING` claims.
- [x] Ownership of the tool-host protocol is explicitly decided as either a
  cross-package root contract or a package-owned contract.
- [x] Duplicate tool-host protocol authoring sources are normalized.
- [x] The relationship between package-local reference source directives,
  generated site output, and committed reference snapshots is documented and
  normalized as far as the approved scope allows.
- [x] The stale OpenAI-compatible provider mkdocstrings directive/import path
  is corrected or explicitly deferred with a blocking reason.
- [x] Any decision not completed without broad code reconstruction is recorded
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

Status: Approved

This subtask will leave one maintained source for each reference page, generated
API output only in the ignored documentation build trees, and explicit
classification for the two legacy planning documents. It will not rewrite the
cross-package architecture, add HTTP endpoints, remove the legacy Core-packaged
OpenAI-compatible provider, or implement old-route compatibility owned by
subtask 060.

1. Retain `ARCHITECTURE.md` as a visibly deferred legacy overview because its
   WebSocket-only frontend path, Core tool-execution boundary, plugin
   configuration statements, and aspirational repository tree are not safe to
   relocate as current architecture. Route current readers to the concise root
   README architecture overview and record a future comprehensive
   cross-package architecture pass for the deferred inventory.
2. Archive `server_endpoints_parity.md` as a historical phase plan. Record that
   all four `EXISTING` routes and 16 of 19 `NEW` routes now exist under their
   documented paths, while application configuration evolved to other
   settings/UI/action routes and feature completions remain terminal-only.
   Remove current documentation and agent-guidance links to the archived plan
   without changing product behavior.
3. Keep the tool-host protocol at `docs/reference/tool-host-protocol.md` as a
   root cross-package contract jointly implemented by the Python proxy and
   Node host. Make it the single authored source, link it from both package
   documentation areas, and boundedly reconcile the handshake, defaulted
   `init`, required plugin methods, optional methods, streaming, state, and
   error behavior with the implementations.
4. Move the AgentCore, type/protocol, and provider-wrapper Mkdocstrings
   directives to `core/python/docs/reference/`. Move the OpenAI-compatible
   provider directive to
   `plugins/reference-openai-compatible-provider/docs/reference/` and point it
   at `reference_openai_compatible_provider.provider`.
5. Publish those package-owned directives through the existing package and
   built-in-plugin assembly paths. Add the provider package `src` directory to
   Mkdocstrings import paths and update the directly affected navigation, LLM,
   index, and plugin-guide links to canonical generated routes.
6. Remove committed generated reference snapshots and the snapshot-refresh
   stage. Keep maintained root reference pages as preparation inputs, keep
   default configuration generated directly from its JSON source, and make the
   convenience build perform only preparation plus MkDocs generation.
7. Update documentation-site, repository-convention, deployment, package, and
   requirements-evidence text affected by snapshot retirement. Record old/new
   AgentCore/provider public routes for subtask 060 rather than creating a
   second authored compatibility source here.
8. Add focused preparation/source-ownership coverage, run the package
   preparation tests, execute the production preparation and normal MkDocs
   build, inspect generated reference routes/import identity, run focused Node
   tool-host tests when Node is available, and search for stale sources,
   imports, links, and snapshot instructions.

### Implementation decisions and open questions

- **Architecture:** retain the file with an explicit deferred/historical
  status; do not publish it as current `docs/development/architecture.md`.
- **Endpoint plan:** archive it with a concise classification note. The one
  remaining exact product gap is recorded as a finding, not implemented or
  promoted to a requirement.
- **Protocol ownership:** the language-neutral NDJSON protocol remains a root
  cross-package contract because the Python client and Node host jointly
  implement it and neither package can change it independently.
- **Generated reference:** package-local directives and ignored site output
  are sufficient. The committed snapshots have no build or runtime consumer
  and are removed rather than retained as a third representation.
- **Reference routes:** Core and provider API reference moves to package-owned
  site routes. Subtask 060 remains responsible for compatibility at the old
  public routes and final navigation curation.
- **Default configuration:** it remains generated during preparation at
  `/reference/default-config/`; only its redundant committed snapshot is
  removed.
- The user approved these decisions and authorized implementation in a new
  worktree from `develop`.
- No requirement questions remain. Local wording and helper decomposition may
  be adjusted without changing these outcomes.

### Documentation

- Deferred-status note for the root architecture page and current architecture
  routing
- Archived endpoint parity plan and updated current application routes
- Canonical tool-host protocol page
- Package-local Python reference directives
- Reference-generation/source ownership and build guidance
- Updated references from Python and Node package docs

### Task checklist

- [x] Mark the architecture page as deferred and route current readers.
- [x] Archive and unlink the historical endpoint parity plan.
- [x] Establish root cross-package tool-host protocol ownership.
- [x] Reconcile and normalize the canonical protocol source.
- [x] Move Core and provider reference directives to package owners.
- [x] Remove committed reference snapshots and refresh tooling.
- [x] Update affected build, deployment, source, index, and evidence links.
- [x] Record old/new public reference routes for subtask 060.
- [x] Run focused tests, preparation, build, import/output, and stale-source checks.
- [x] Record deferred decisions or migration items.

### Requirement verification

| Requirement group | Acceptance evidence |
|---|---|
| Architecture | Major referenced paths/layers are spot-checked, the legacy page is visibly deferred, and current routing points to the accurate concise overview. |
| Endpoint parity | Route inspection supports the historical classification; the page is archived and no current guide presents stale statuses as live. |
| Tool-host protocol | One root authored source exists, ownership is stated, both implementations link to it, and focused Node/Python flow tests cover the documented boundary. |
| Generated reference | Preparation tests and the normal build show package-local directives producing package-owned site pages; no committed generated snapshot or refresh stage remains. |
| Provider reference | Built Mkdocstrings output identifies `reference_openai_compatible_provider.provider`, and the stale directive/import is absent. |
| Compatibility handoff | Old/new Core and provider reference routes are recorded for 060 without duplicate full-content compatibility pages. |

### Additional implementation verification

- Inspect current FastAPI route declarations rather than reconstructing server
  behavior beyond endpoint classification.
- Build the affected mkdocstrings reference pages.
- Search for duplicate protocol content and stale provider import references.
- Verify links from `packages/tool-host-node`, Core tool-host code docs, and
  plugin docs.
- Confirm generated `docs_site/prepared/` and `docs_site/dist/` remain ignored
  and no generated output is tracked as authored source.

## Implementation Notes

- Implementation began in
  `/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-cross-package-reference-triage`
  on branch `task/20260728-cross-package-reference-triage`, created from the
  committed local `develop` HEAD `29604c237630311b3f68d002178581cfcebdf975`.
  Uncommitted changes in the original `develop` worktree remain untouched.
- The committed baseline includes completed subtask 030. Its package-local
  Core guides and maintained docstrings are the source/reference handoff
  consumed here.
- Static route comparison found all four `EXISTING` entries and 16 of 19
  `NEW` entries at their exact method/path in `server.py`. The three absent
  paths are the two proposed `/config/application` reads and the proposed
  session completion route.
- The committed reference snapshots have no build or runtime consumer. Current
  references to them are documentation routes or evidence links that can point
  to package-owned generated pages, maintained sources, or the build
  generator.
- Root reference pages are now preparation inputs. A focused collision check
  prevents an authored `docs/reference/default-config.md` from silently
  replacing the default-configuration page generated from `config.json`.
- Recompiling root guidance initially exposed a pre-existing source/output
  drift for the `.crystal/` directory note. The maintained target input was
  reconciled so compilation preserves that existing guidance while applying
  only the intended Core-reference route change.
- The normal build reports ten pre-existing broken-link warnings from unchanged
  shared plugin pages. Four protocol implementation links initially introduced
  warnings because their source files are not public pages; changing those
  links to repository-source URLs removed every warning introduced here.

## Completion Notes

### Outcome

- `ARCHITECTURE.md` remains at root with an explicit deferred-legacy notice.
  Root README and compiled agent guidance route current architecture readers to
  the concise README overview. A comprehensive replacement remains deferred
  until Core, application, frontend transports, mobile/desktop, bridge, cloud,
  and plugin boundaries can be reviewed together.
- The endpoint parity phase plan moved to
  `archive/server-endpoints-parity.md`. Current application guidance no longer
  links it, and its archive notice records the exact route comparison.
- `docs/reference/tool-host-protocol.md` is the single maintained,
  cross-package NDJSON contract. It now documents the implemented handshake,
  version/error validation, defaulted `init`, two required Node plugin methods,
  optional methods, state round-tripping, streaming parts, and structured
  result boundary. Core and Node package documentation link to it.
- Mkdocstrings directives moved to their owning packages:
  - `core/python/docs/reference/` owns AgentCore, types/protocols, and provider
    wrapper directives;
  - `plugins/reference-openai-compatible-provider/docs/reference/provider.md`
    owns the first-party compatible-provider directive and imports
    `reference_openai_compatible_provider.provider`.
- The assembler publishes those sources at package-owned routes and publishes
  the maintained root protocol at its unchanged `/reference/tool-host-protocol/`
  route. The default configuration remains generated directly from
  `application/python/agent_terminal_app/default_config/config.json`.
- Committed generated reference snapshots and
  `refresh_reference_snapshots.py` were removed. The convenience build now
  performs preparation plus MkDocs generation, leaving all generated Markdown
  and HTML in ignored `docs_site/prepared/` and `docs_site/dist/`.

### Public route handoff for subtask 060

| Previous route | Canonical route after this task |
|---|---|
| `/reference/agent_core/core/` | `/packages/core-python/reference/core/` |
| `/reference/agent_core/types/` | `/packages/core-python/reference/types/` |
| `/reference/agent_core/plugin/provider/` | `/packages/core-python/reference/plugin/provider/` |
| `/reference/providers/openai_provider/` | `/built-in-plugins/reference-openai-compatible-provider/docs/reference/provider/` |
| `/reference/tool-host-protocol/` | Unchanged |
| `/reference/default-config/` | Unchanged |

Subtask 060 remains responsible for non-authoritative compatibility pages or
redirects at the four moved routes and for final navigation curation.

### Requirement evidence

- Architecture inspection found current native-history material alongside
  obsolete WebSocket-only transport, Core tool-execution, plugin
  configuration, and aspirational-tree claims. The visible notice and current
  routing prevent promotion of that mixed page as current architecture.
- AST comparison with `server.py` confirms 4/4 `EXISTING` and 16/19 `NEW`
  entries under exact method/path pairs. The two proposed application-config
  reads and session completion route are absent; no product behavior changed.
- Preparation-source mapping tests prove the root protocol, three Core
  directives, and provider directive each map from one maintained owner to the
  intended prepared path. They also prove committed snapshots are absent and
  authored content cannot collide with generated default configuration.
- Built provider output identifies
  `reference_openai_compatible_provider.provider.OpenAICompatibleProvider` and
  source `reference_openai_compatible_provider/provider.py`; the stale
  `plugins.openai_provider` directive is absent.
- Prepared and built output contains all three Core references, the provider
  reference, tool-host protocol, and generated default configuration. Package
  README/index links resolve to their prepared destinations.

### Verification performed

- `python -m pytest docs_site/tests -q`: `19 passed`.
- `pytest core/python/tests/test_node_tool_plugins.py -q -m 'not integration'`:
  `10 passed`.
- `ruff check docs_site/scripts/prepare_mkdocs_site.py
  docs_site/scripts/build_mkdocs_site.py
  docs_site/tests/test_prepare_mkdocs_site.py`: passed.
- `python -m compileall -q docs_site/scripts`: passed.
- `python -m maintainer.guidance check --bundle
  maintainer/guidance/current --target
  maintainer/guidance/targets/crystal-lattice --destination .`: passed.
- Import smoke with Core and provider package source roots resolved all four
  Mkdocstrings targets to the intended worktree files.
- `python docs_site/scripts/build_mkdocs_site.py`: passed. The ten reported
  broken-link warnings are from unchanged shared plugin pages; this task
  introduces no build warning.
- Generated-route, provider-source, link-rewrite, stale-source/import,
  generated-tree ignore, and `git diff --check` inspections passed.

### Deferred and excluded work

- A current full cross-package architecture page is deferred to a task that can
  verify every major runtime and transport boundary together.
- `POST /sessions/{session_id}/completions` remains a terminal-only capability
  finding. This documentation task neither requires nor implements an HTTP
  endpoint.
- The legacy Core-packaged `plugins.openai_provider` implementation remains for
  compatibility and tests; only the first-party reference directive changed.
- Public compatibility implementation and the remaining pre-existing MkDocs
  warnings remain with subtasks 060 and 070.
