Parent Task: tasks/20260728-package-local-documentation-standard/000-main.md

Depends On:

- `tasks/20260728-package-local-documentation-standard/010-documentation-standard-and-agent-guidance.md`
- `tasks/20260728-package-local-documentation-standard/020-package-docs-site-assembly.md`

# Core Python Documentation Migration

Create the Core Python package documentation entry points and migrate
ownership-clear Core SDK, event, examples, and types/protocol documentation
with bounded verification.

## Requirements checklist

- [ ] `core/python` has package documentation entry points required by the
  approved public-package profile.
- [ ] `docs/api/events.md` is relocated to `core/python/docs/events.md` or a
  more appropriate approved Core Python path.
- [ ] The event page distinguishes application-owned event contracts from
  terminal, bridge, mobile, and frontend transport/consumer details.
- [ ] `docs/api/core-sdk.md` is relocated to `core/python/docs/core-sdk.md`
  without requiring a full rewrite.
- [ ] Core SDK imports, named public methods, and examples touched by the move
  are verified against current code or existing tests.
- [ ] `EXAMPLES.md` is moved to a Core Python documentation path and the
  examples generator writes to the new canonical location.
- [ ] Existing example tests are run before or with regeneration.
- [ ] `TYPES_AND_PROTOCOLS.md` is boundedly inspected and either relocated to a
  Core Python development-doc path, retained with rationale, or explicitly
  deferred.
- [ ] Existing inbound links and public site paths are recorded for subtask 060
  compatibility work.
- [ ] No broad rewrite of the 1,000+ line Core SDK guide or generated examples
  is performed solely for migration.

## Supporting details

### Candidate pages

- `docs/api/events.md`
- `docs/api/core-sdk.md`
- `EXAMPLES.md`
- `TYPES_AND_PROTOCOLS.md`
- `core/python/README.md`

### Event ownership

The event page describes:

- `core/python/agent_app/events.py`;
- `AgentApplication` event production;
- `ToolLoopRunner` streaming/tool events;
- terminal HTTP polling;
- bridge forwarding;
- mobile/frontend consumption.

The public event contract is primarily owned by the application layer packaged
under `core/python`, but cross-package transport details should remain clearly
identified as consumers/integrations rather than implied Core-only behavior.

### Verification boundary

Verify only:

- event type names, common fields, and internal/external distinctions directly
  documented by the moved page;
- import paths and public methods used in quickstart/core guide examples;
- the examples generator output path and existing tested example flow;
- file links and headings directly affected by relocation.

Do not attempt to comprehensively re-document all Core APIs.

## Execution plan

Status: Draft

1. Add concise `core/python/AGENTS.md`, `docs/index.md`, and
   `docs/quickstart.md` using existing README and verified docs as source.
2. Move the event and Core SDK pages to canonical package-local locations.
3. Spot-check event claims against producers, transports, frontend types, and
   focused existing tests.
4. Spot-check Core SDK examples and public names without rewriting the whole
   guide.
5. Move the generated examples catalog, update
   `scripts/generate_examples_md.py`, run relevant example tests, and
   regenerate.
6. Inspect `TYPES_AND_PROTOCOLS.md`, choose relocate/retain/defer, and record
   rationale.
7. Update package-local links; leave cross-repository/public compatibility
   completion to subtask 060.

### Implementation decisions and open questions

- Package-local Core ownership and bounded verification are approved.
- The exact user/development placement of `TYPES_AND_PROTOCOLS.md` remains a
  design decision to resolve from its current content without broad rewriting.
- If the event page cannot remain coherent without splitting transport details,
  keep the existing content together for this task and record a later split;
  do not create partially reconstructed companion pages.

### Documentation

- `core/python/AGENTS.md`
- `core/python/docs/index.md`
- `core/python/docs/quickstart.md`
- `core/python/docs/core-sdk.md`
- `core/python/docs/events.md`
- `core/python/docs/examples.md`
- possible `core/python/docs/development/types-and-protocols.md`

### Task checklist

- [ ] Create Core Python package entry points.
- [ ] Move and verify event documentation.
- [ ] Move and spot-check Core SDK guide.
- [ ] Move examples output and update generator.
- [ ] Run example tests and regenerate.
- [ ] Classify and handle `TYPES_AND_PROTOCOLS.md`.
- [ ] Record inbound links and compatibility needs.

### Requirement verification

| Requirement group | Acceptance evidence |
|---|---|
| Package entry points | Core README/AGENTS/docs index/quickstart form a concise, non-duplicative route to installation, first use, detailed docs, and development guidance. |
| Event documentation | Focused comparison with event producers/types/tests confirms documented event names and public/internal distinctions. |
| Core SDK guide | Referenced imports and public method names exist; representative examples align with current tested usage. |
| Generated examples | Existing example tests pass and the generator deterministically writes the new canonical file. |
| Types/protocols classification | Completion notes record relocate/retain/defer outcome and verification boundary. |

### Additional implementation verification

- Run the relevant Core example tests before regeneration.
- Run focused event/application tests selected from existing suites.
- Search repository links to all moved Core documentation paths.
- Inspect the prepared package output generated by subtask 020.
