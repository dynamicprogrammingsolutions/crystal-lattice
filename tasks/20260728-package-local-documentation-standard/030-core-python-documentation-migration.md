Parent Task: tasks/20260728-package-local-documentation-standard/000-main.md

Depends On:

- `tasks/20260728-package-local-documentation-standard/010-documentation-standard-and-agent-guidance.md`
- `tasks/20260728-package-local-documentation-standard/020-package-docs-site-assembly.md`

Specification:
`maintainer/docs/development/specifications/crystal-lattice-guidance-integration/index.md`

Requirement IDs:
`DOCREP-004`, `DOCMIG-001`, `DOCPUB-006`

# Core Python Documentation Migration

Create the Core Python package documentation entry points; migrate
ownership-clear Core SDK, event, and generated examples documentation; replace
the legacy types/protocols page with current overview and reference sources;
and archive the superseded root page with bounded verification.

## Requirements checklist

- [x] `core/python` has the README, package guidance, documentation index,
  quickstart, user documentation, and development-documentation routes
  required by the approved public-package profile.
- [x] `core/python/README.md` is a concise package entry point rather than a
  competing SDK guide, while useful package-owned guidance removed from it
  remains reachable in the Core documentation tree.
- [x] `docs/api/events.md` is relocated to `core/python/docs/events.md` or a
  more appropriate approved Core Python path.
- [x] The event page accurately distinguishes application-owned event
  contracts from terminal-owned event additions, HTTP/bridge transports, and
  frontend/mobile/desktop consumers.
- [x] Event names, common and optional fields, and public/internal distinctions
  documented by the moved page agree with current producers, public transport,
  frontend types, or focused tests.
- [x] `docs/api/core-sdk.md` is relocated to `core/python/docs/core-sdk.md`
  without a comprehensive rewrite or an unsupported claim of exhaustive API
  coverage.
- [x] Core SDK imports, named public methods, data fields, and examples touched
  by the move are verified against current code or focused existing tests.
- [x] `EXAMPLES.md` is moved to `core/python/docs/examples.md`, and
  `scripts/generate_examples_md.py` writes deterministically to that canonical
  location.
- [x] Relevant existing example tests are run before or with regeneration;
  integration-gated examples not deliberately enabled are reported as not run.
- [x] A current `core/python/docs/types-and-protocols.md` preserves the useful
  overview function of `TYPES_AND_PROTOCOLS.md`, so readers can understand the
  important types, plugin families, state ownership, request/streaming flow,
  tool/action relationships, and native-history model without reading source
  code.
- [x] Useful exact-reference information missing from maintained Core
  docstrings is added there, and the live `agent_core.types` MkDocstrings
  directive produces readable reference documentation from those docstrings.
- [x] Every substantive section of `TYPES_AND_PROTOCOLS.md` has a recorded
  disposition to the new overview, maintained docstrings/generated reference,
  an existing authoritative guide, or intentional removal as stale duplicate
  content.
- [x] After useful content and current links are accounted for,
  `TYPES_AND_PROTOCOLS.md` is moved to
  `archive/root-docs/TYPES_AND_PROTOCOLS.md` and is no longer presented by
  current documentation as an authoritative source.
- [x] Known inbound source links are updated, and old/new public route mappings
  are recorded for subtask 060 compatibility work.
- [x] No broad rewrite of the 1,000+ line Core SDK guide or generated examples
  is performed solely for migration, and no runtime behavior or public API is
  changed.

## Supporting details

### Candidate pages and maintained sources

- `core/python/README.md`
- `docs/api/events.md`
- `docs/api/core-sdk.md`
- `EXAMPLES.md`
- `TYPES_AND_PROTOCOLS.md`
- `scripts/generate_examples_md.py`
- `core/python/agent_core/types.py`
- `docs_site/source/reference/agent_core/types.md`
- `core/python/docs/development/index.md`

### Current package-publication baseline

`docs_site/packages.toml` already registers `core/python` at
`packages/core-python`, includes its README and `docs/` tree, and publishes its
development documentation. The assembler prefers `core/python/docs/index.md`
as the package landing page and currently falls back to the 600+ line README
because that index does not exist.

The new package index must become the public landing page. The README remains
the concise repository/package entry point rather than a second long-form
guide.

### Core README and SDK guide findings

The README currently duplicates installation, quickstart, streaming, type,
architecture, API, logging, and complete-example material. It also describes
the distribution as installing only `agent_core`, while the current package
manifest includes `agent_core`, `agent_app`, and core-packaged compatibility
plugins.

The hand-written Core SDK page is useful as a selected API guide, and all
methods with dedicated headings still exist. It is not exhaustive and contains
bounded correctness issues that must not be promoted unchanged:

- it describes every `AgentCore` method and provider operation as pure despite
  registration, caches, tool preparation, and provider I/O;
- its `Message` summary omits multipart content and structured tool results;
- one chat example reads an undefined variable;
- some displayed signatures omit current optional context/request parameters;
- it contains duplicated text and a nondeterministic same-input/same-response
  claim;
- its license label conflicts with the package's Apache-2.0 metadata.

Correct these touched claims and examples, label the page as a selected guide,
and route exhaustive member lookup to generated reference. Do not expand it to
cover every public method.

### Event ownership and current drift

The application layer under `core/python/agent_app` owns the event store,
request/tool-loop events, notification lifecycle events, and the internal
checkpoint boundary. The terminal/HTTP package adds session, message, and
snapshot events and exposes stored events over HTTP. Bridge and frontend
packages transport or consume the public events.

The current page mixes those owners and includes stale or contradictory
details:

- application notifications intentionally omit `session_id`, so it is not a
  universal public-event field;
- `assistant_message` has `message_index`, and `final`/`tool_results` have
  `start_index`;
- terminal lifecycle events generally carry mutation fields, indices, or a
  message rather than the full serialized session claimed by the page;
- terminal snapshot selection, clearing, and restoration events are omitted;
- bridge/mobile ownership and consumption descriptions predate the shared
  frontend SDK and React bindings;
- exact mobile/desktop presentation placement belongs to the owning consumer
  documentation rather than the Core event envelope.

Keep one coherent event page in this subtask. Organize it by contract owner,
retain only useful integration summaries, and link detailed transport and
presentation behavior to its owning package documentation.

### Types/protocols source disposition

The legacy root page is neither a reliable exact reference nor a genuinely
language-neutral contract. Its protocol signatures are stale and overlap the
generated `agent_core.types` reference and detailed shared plugin guides.

It nevertheless provides a valuable compact mental model. Preserve that use in
a new user-facing Core page rather than moving the old page intact:

| Legacy subject | Current destination |
|---|---|
| Important Core types and immutability convention | New Core types/protocols overview plus type docstrings |
| Provider/extension/feature shared state and independent tool state | New overview with links to focused plugin guides |
| Plugin-family responsibilities | Compact overview comparison and shared plugin guides |
| Request and streaming flow | Small overview flow plus `plugins/docs/plugin-execution-order.md` |
| Plugin discovery | Core SDK guide and `AgentCore.discover_and_register` reference |
| Tool interop | Short overview plus `plugins/docs/tool-interop.md` |
| Session actions and layered context | Short overview plus `plugins/docs/actions.md` |
| Stream events | Canonical Core event page |
| Provider-native history retention | Overview plus Core/provider guidance |
| Exact protocol members and signatures | Maintained docstrings and generated reference |
| Runnable plugin examples | Canonical generated examples page |
| Superseded, duplicated, or inaccurate signatures | Do not reproduce |

The new overview should answer what the central types represent, what the
immutability convention guarantees, how core and provider-native messages
differ, how each plugin kind participates, how state and context flow, and
where exact reference and detailed authoring guidance live.

### Docstring/reference boundary

`docs_site/source/reference/agent_core/types.md` currently contains the
maintained `::: agent_core.types` directive. Subtask 050 owns final placement
of reference directives, generated-output/snapshot policy, and reference
normalization. This subtask improves the maintained Python sources that the
directive reads and verifies a normal live build, but does not refresh or
hand-edit committed generated reference snapshots.

The focused docstring pass should cover reference facts that belong beside the
Python declarations, including:

- the module-level frozen-dataclass versus nested-container convention;
- `MessageRole` if Griffe supports documenting the alias without changing the
  public API;
- `ToolDescriptor` fields and role;
- `Message.content`, `multipart_content`, `tool_result`, and serialized keys;
- `PartialMessage` fields and incremental rather than accumulated semantics;
- `Session` fields and immutable-by-convention nested values;
- the required `id` and provider-defined extra fields of model descriptor
  dictionaries returned by `ProviderPlugin.get_models`;
- shared protocol identity/UI wording and current plugin-state ownership.

Also repair malformed or misleading source docstrings that already degrade the
generated reference, such as broken example indentation/fences, duplicate
sentences, and examples naming nonexistent APIs. Do not add a new public
`ModelDescriptor` class or otherwise change runtime behavior merely to mirror
the legacy document.

### Archive outcome

After the disposition review, current-page creation, docstring improvements,
and link migration are complete, move the old root file with Git history to:

```text
archive/root-docs/TYPES_AND_PROTOCOLS.md
```

`archive/README.md` already defines `archive/root-docs/` as historical former
root documentation and warns that archived material may contain obsolete
paths, commands, APIs, and assumptions. Current user and development indexes
must not route readers to the archived page. Historical tasks and completion
evidence may name the old and archived paths.

### Worktree and concurrent-work boundary

Planning is performed on branch
`task/20260728-core-python-documentation-migration` in:

```text
/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-core-python-documentation-migration
```

The branch was created from then-current `main` at commit
`7becd53729b180a5a9532a3944f25fe9950b2886`. The committed subtask 065 work is
already part of this baseline. Any later 065 follow-up is expected to own
`CONTRIBUTING.md` and its own task evidence, while this subtask owns Core
package documentation.

Likely shared bookkeeping files are the parent task and
`maintainer/docs/development/specifications/crystal-lattice-guidance-integration/requirements.md`.
Re-read them immediately before narrow evidence updates, preserve concurrent
changes, and do not edit the 065 task file. Recheck `main` before integration;
do not silently absorb unrelated changes into this task branch.

### Verification boundary

Verify only:

- installation, import, public method, data-field, and expected-output claims
  used by the new entry points and touched Core SDK sections;
- event names, fields, ordering/cursor statements, and internal/external
  distinctions directly documented by the moved event page;
- the exact credential-free quickstart path;
- the examples generator destination, source-derived headings/links, and
  relevant existing tested flows;
- the types/protocols disposition and docstrings touched for generated
  reference;
- links, site paths, and headings directly affected by relocation.

Do not comprehensively re-document all Core APIs, plugin behavior, frontend
event reduction, bridge behavior, or generated-reference policy.

## Execution plan

Status: Approved

This subtask will leave Core with one concise package entry point, one
credential-free first-success path, focused user guides, a useful
types/protocols mental model, maintained exact-reference docstrings, and no
active dependency on the superseded root pages. It will not change runtime
behavior, comprehensively rewrite the long SDK/examples pages, or implement
old-route redirects owned by subtask 060.

### 1. Preserve the exact baseline and coordinate downstream ownership

1. Work only in the dedicated task branch/worktree based on `7becd537`.
2. Recheck worktree status and current `main` before implementation and before
   final evidence updates.
3. Preserve all unrelated and subtask 065 changes; do not edit its task or
   `CONTRIBUTING.md`.
4. Before subtask 050 executes, record 030 as its dependency because 050 will
   consume the docstrings and reference handoff produced here.
5. Keep subtask 060 responsible for old public URL compatibility, exhaustive
   final link audit, final navigation curation, and docs-deployment triggers.

### 2. Create concise Core package entry points

1. Add `core/python/AGENTS.md` with package ownership, important directories,
   documentation routes, and focused verification commands. Keep it concise
   and inherit repository-wide guidance rather than repeating it.
2. Add `core/python/docs/index.md` as the preferred package/site landing page.
   Route readers to quickstart, Core SDK guide, types/protocols overview,
   events, examples, generated reference, shared plugin-authoring docs, and
   Core development docs.
3. Add `core/python/docs/quickstart.md` using the packaged deterministic echo
   provider so installation and one complete request produce a concrete result
   without credentials or network services.
4. Add focused automated coverage for the exact quickstart code and expected
   output, preferably by executing the maintained documentation snippet rather
   than maintaining a second divergent copy.
5. Reduce `core/python/README.md` to purpose, installed modules/boundaries,
   source installation, a compact first-use route, tests, documentation links,
   and license.
6. Move the detailed structured-logging material removed from the README to
   `core/python/docs/development/logging.md`, correct only touched commands or
   claims, and link it from the development index.

### 3. Move and boundedly reconcile the Core SDK guide

1. Move `docs/api/core-sdk.md` to `core/python/docs/core-sdk.md`.
2. Present it as a hand-written guide to selected Core APIs and link generated
   reference for exhaustive member lookup.
3. Verify all named methods and imports against current code.
4. Correct only the identified or directly touched inaccuracies:
   architecture/purity wording, data fields, simplified signatures, broken or
   nondeterministic examples, duplicate text, installation wording, and
   license.
5. Reuse the tested quickstart or link to it instead of maintaining a second
   conflicting first-success flow.
6. Do not add sections merely to enumerate every currently public
   non-underscore method.

### 4. Move and organize the event contract by owner

1. Move `docs/api/events.md` to `core/python/docs/events.md`.
2. Open with the application-owned event-store/envelope boundary, making
   `event_id` and `type` common while documenting `session_id` and
   `request_id` as event-dependent.
3. Reconcile request, assistant, tool, notification, checkpoint, session,
   message, and snapshot event names and fields against current producers,
   focused tests, and frontend types.
4. Clearly separate:
   - application-owned public events;
   - internal `session_checkpoint` values filtered before publication;
   - terminal/HTTP-owned lifecycle additions and polling behavior;
   - bridge and frontend packages as transports/consumers.
5. Retain only integration detail needed to understand exposure. Replace
   stale UI-placement and mobile implementation narration with links to
   current owning documentation.
6. Preserve a coherent single page; do not create partially reconstructed
   transport-specific companion pages.

### 5. Move and regenerate the examples catalog

1. Run the relevant existing non-integration example tests before changing the
   generated output.
2. Change `scripts/generate_examples_md.py` to write
   `core/python/docs/examples.md`.
3. Keep deterministic generation and all current example/test associations.
4. Remove obsolete internal provenance labels such as `PROJECT_PLAN` and
   references to the removed `PLUGIN_EXAMPLES.md` from maintained example
   docstrings so they do not enter public user documentation.
5. Adjust only generator paths, links, headings, and audience-inappropriate
   source labels needed by the move. Do not broadly rewrite or reorder the
   generated examples.
6. Regenerate, rerun the relevant example tests, and confirm a second
   generation produces no diff.
7. Report local-service and hosted-API example tests as not run unless their
   gates are deliberately enabled and they are actually collected.

### 6. Replace the legacy types/protocols page without losing its useful role

1. Create `core/python/docs/types-and-protocols.md` as a current conceptual
   overview, not a second exhaustive signature reference.
2. Include:
   - a compact important-type table;
   - accurate frozen-dataclass/nested-container semantics;
   - core versus provider-native message distinction;
   - plugin-family responsibilities and state ownership;
   - small non-streaming and streaming flow diagrams;
   - tool interop, actions, layered context, and native-history summaries;
   - audience-compatible links to exact generated reference, focused plugin
     guides, events, SDK usage, and examples.
3. Compare every substantive legacy section with the new page, maintained
   docstrings, and existing authoritative guides. Record a concise disposition
   matrix in implementation/completion notes rather than copying stale
   signatures.
4. Do not reproduce the unsupported claim that the legacy Python-shaped page
   is a language-neutral contract.

### 7. Improve the maintained type/protocol reference sources

1. Update only documentation strings and comments in
   `core/python/agent_core/types.py`; do not change runtime interfaces or
   behavior.
2. Add the missing declaration-local reference facts identified above.
3. Repair malformed examples, code fences, duplicated prose, and nonexistent
   API names already emitted by MkDocstrings.
4. Keep broad mental-model prose in the new overview and detailed plugin
   authoring in `plugins/docs/`; docstrings should own exact Python member
   semantics and compact examples.
5. Build the live `agent_core.types` directive and inspect representative
   output for `Message`, `PartialMessage`, `Session`, `ToolDescriptor`, and all
   four plugin protocols.
6. Do not edit `docs/reference/agent_core/types.md` as if it were an authored
   source and do not refresh committed snapshots; provide 050 with the clean
   docstring/reference handoff.

### 8. Archive the superseded page and migrate links

1. After the disposition check passes, move `TYPES_AND_PROTOCOLS.md` to
   `archive/root-docs/TYPES_AND_PROTOCOLS.md`.
2. Update known current source links to all moved Core pages, including root
   README/AGENTS, root docs index, Core indexes, application request-execution
   guidance, and directly affected MkDocs/LLM entries.
3. Ensure no current user/development page presents the archived page as
   authoritative. Historical tasks/archive content may retain historical
   references.
4. Keep minimal current site configuration pointed at canonical prepared
   package paths so preparation/build remains usable; leave final information
   architecture to 060.
5. Record public route mappings for 060:
   - `/api/core-sdk/` to `/packages/core-python/core-sdk/`;
   - `/api/events/` to `/packages/core-python/events/`;
   - new `/packages/core-python/examples/`;
   - new `/packages/core-python/types-and-protocols/`.
6. Do not author duplicate full-content compatibility pages. Subtask 060 owns
   redirects or minimal non-authoritative compatibility pages.

### 9. Verify the package and public documentation boundary

1. Run the exact quickstart coverage and focused Core API/type tests.
2. Run focused application event, event-store, notification, and HTTP event
   tests corresponding to documented claims.
3. Run relevant example tests before and after regeneration and classify gated
   tests honestly.
4. Run focused docs-site assembler tests.
5. Run production documentation preparation and a normal MkDocs build without
   refreshing committed reference snapshots.
6. Inspect `docs_site/prepared/packages/core-python/` and built Core,
   event, examples, types/protocols, development-logging, and live generated
   type-reference pages.
7. Search for old source paths, unintended archive links, broken relative
   links, obsolete public provenance labels, and duplicate authored sources.
8. Run focused Ruff checks for changed Python/doc-test sources and
   `git diff --check`.
9. Update the task, parent task, and requirements evidence narrowly after
   re-reading their latest state. Leave public URL compatibility incomplete
   until 060 implements and verifies it.

### Implementation decisions and open questions

- **Approved direction:** useful legacy types/protocols content is preserved in
  current documentation or docstrings, and the superseded root page is
  archived rather than deferred.
- **Overview placement:** `core/python/docs/types-and-protocols.md` is
  user-facing because SDK consumers and plugin authors use it to understand
  supported public concepts. Current implementation-only details remain in
  development docs.
- **Reference authority:** exact Python signatures and member semantics live in
  maintained docstrings and generated reference. The new overview links to
  that reference instead of duplicating every hook.
- **No API invention:** the old `ModelDescriptor` prose does not justify
  adding a new exported class or alias. Document the current dictionary
  contract where `get_models` is declared.
- **Archive placement:** `archive/root-docs/TYPES_AND_PROTOCOLS.md` is the
  final historical location after current replacements and links are complete.
- **README preservation:** detailed logging guidance moves to a focused Core
  development page instead of being discarded while the README is shortened.
- **Quickstart:** use a deterministic, credential-free packaged provider and
  verify its exact observable result.
- **Events:** keep one page while clearly labeling application contracts,
  terminal additions, transport, and consumers.
- **Generated snapshots:** 030 verifies live MkDocstrings output but does not
  refresh or normalize committed snapshots; 050 owns that policy and final
  reference placement.
- **Downstream task order:** 050 should declare 030 as a dependency before
  consuming the reference sources. 060 remains the compatibility/navigation
  owner.
- **Concurrent work:** subtask 065 content is in the branch baseline. Do not
  modify its task or `CONTRIBUTING.md`; reconcile only genuinely shared
  bookkeeping files if later changes appear.
- No requirement questions remain. Local wording and test-file decomposition
  may be adjusted without changing these outcomes.

### Documentation

- `core/python/README.md`
- `core/python/AGENTS.md`
- `core/python/docs/index.md`
- `core/python/docs/quickstart.md`
- `core/python/docs/core-sdk.md`
- `core/python/docs/events.md`
- `core/python/docs/examples.md`
- `core/python/docs/types-and-protocols.md`
- `core/python/docs/development/index.md`
- `core/python/docs/development/logging.md`
- documentation strings in `core/python/agent_core/types.py`
- current root/package links and directly affected docs-site configuration
- `archive/root-docs/TYPES_AND_PROTOCOLS.md`
- task/requirements evidence after implementation

### Task checklist

- [x] Preserve the task worktree baseline and recheck concurrent/shared files.
- [x] Record 030 as a dependency of 050 before reference normalization begins.
- [x] Create Core package AGENTS, docs index, and tested quickstart.
- [x] Reduce the Core README and preserve logging guidance in development docs.
- [x] Move and boundedly correct the Core SDK guide.
- [x] Move, reorganize, and verify the event documentation.
- [x] Run relevant example tests before changing generated output.
- [x] Move examples output, update the generator/source labels, and regenerate.
- [x] Create the current types/protocols conceptual overview.
- [x] Improve exact-reference docstrings without changing runtime behavior.
- [x] Record the complete legacy types/protocols disposition.
- [x] Verify live MkDocstrings rendering and hand reference ownership to 050.
- [x] Archive the superseded root types/protocols page.
- [x] Update current source links and record public route mappings for 060.
- [x] Run focused tests, preparation, build, output inspection, and diff checks.
- [x] Update task, parent, and requirement evidence without overwriting
  concurrent work.

### Requirement verification

| Requirement group | Acceptance evidence |
|---|---|
| Package entry points | Core README/AGENTS/docs index/quickstart provide concise, non-duplicative routes to installation, a credential-free observable result, user guides, reference, and development docs; the assembler uses the docs index as the package landing page. |
| Core SDK guide | Every dedicated method name/import and touched data field exists in current code; corrected representative examples run or align with focused tests; the page explicitly routes exhaustive lookup to generated reference. |
| Event documentation | Focused producer/type/test comparison confirms documented event names, required/optional fields, owner boundaries, cursor/checkpoint semantics, and internal `session_checkpoint` filtering. |
| Generated examples | Relevant non-integration example tests pass before/after the move; the generator writes the canonical file twice without a second diff; gated suites are explicitly classified. |
| Types/protocols overview | A reader can identify important types, immutability semantics, plugin responsibilities/state, request and streaming flows, tool/action/context relationships, and native history from the new page without reading source code. |
| Docstring reference | Source inspection and the normal MkDocs build show readable generated entries for central types and all plugin protocols, with missing exact facts supplied and malformed examples repaired. |
| Legacy-page retirement | A section disposition accounts for useful content; repository search finds no current authoritative link to the root page; Git records it under `archive/root-docs/`. |
| Link and publication continuity | Known source links resolve to canonical package-local sources, prepared/built package pages exist, and old/new web routes are recorded for 060 without a second full authored copy. |
| Scope boundary | Diff inspection shows no runtime/API changes, generated snapshot edits, broad SDK/examples rewrite, compatibility implementation, or unrelated subtask 065 changes. |

### Additional implementation verification

- Run the focused quickstart test and representative Core API/type tests,
  including `core/python/tests/test_core.py` and
  `core/python/tests/test_types.py`.
- Run:

  ```bash
  pytest core/python/examples/tests -m 'not integration' -q
  ```

  before and after regeneration. Run gated Ollama/API slices only when
  deliberately enabled; otherwise report them as not run.
- Run focused tests from:
  - `core/python/tests/test_application_layer_streaming.py`;
  - `core/python/tests/test_event_store_cursors_and_locks.py`;
  - `core/python/tests/test_application_notifications.py`;
  - `core/python/tests/test_session_notifications.py`;
  - selected event/cursor/snapshot cases in
    `application/python/tests/test_agent_terminal_app_server.py`.
- Run `python -m pytest docs_site/tests/test_prepare_mkdocs_site.py -q`.
- Run `python scripts/generate_examples_md.py` twice and confirm the second run
  is clean.
- Run `python docs_site/scripts/prepare_mkdocs_site.py`.
- Run `(cd docs_site && mkdocs build)` without the snapshot-refresh wrapper.
- Inspect prepared and built Core package pages plus the live
  `/reference/agent_core/types/` output.
- Validate changed relative links and search live sources for:
  - `docs/api/events.md`;
  - `docs/api/core-sdk.md`;
  - root `EXAMPLES.md`;
  - root `TYPES_AND_PROTOCOLS.md`;
  - links into `archive/root-docs/TYPES_AND_PROTOCOLS.md`;
  - `PROJECT_PLAN` and `PLUGIN_EXAMPLES.md` in generated public examples.
- Run focused Ruff checks for changed Python files and documentation tests.
- Run `git diff --check`.
- Confirm generated `docs_site/prepared/` and `docs_site/dist/` remain ignored
  and no committed reference snapshot changed.

## Implementation Notes

- Implementation began from approved-plan commit `dc0e73f1` on
  `task/20260728-core-python-documentation-migration`, based on `main` commit
  `7becd53729b180a5a9532a3944f25fe9950b2886`.
- The dedicated worktree was clean after the plan commit. The separate `main`
  worktree contained only an unrelated untracked
  `application/python/agent_terminal_app/cache/` directory at the baseline
  recheck; no file from that directory is in scope.
- Subtask 065's committed work is included in the branch baseline. Its task and
  `CONTRIBUTING.md` remain outside this subtask.
- Subtask 050 now declares this subtask as a dependency so its
  generated-reference work consumes the maintained docstrings produced here.
- Baseline examples passed before generator changes: `5 passed, 8 deselected`
  with the integration gate explicitly excluded.
- The exact documentation quickstart executed successfully and produced
  `SYS= | USER=Hello from the echo provider!`; its returned session contained
  the user and assistant messages.
- The Core SDK source moved to `core/python/docs/core-sdk.md`. Its 19 dedicated
  method headings all resolve to methods on the current `AgentCore`; focused
  Core/type/quickstart verification passed with `42 passed`.
- The event source moved to `core/python/docs/events.md` and now distinguishes
  application contracts, internal session checkpoints, terminal lifecycle
  additions, HTTP exposure, bridge transport, and frontend consumers.
  Application event/store/notification verification passed with `56 passed`;
  selected HTTP event, cursor, compaction, lifecycle, and snapshot verification
  passed with `17 passed, 44 deselected`.
- Six example/test pairs whose filenames exposed the old `project_plan` label
  were renamed mechanically. Their imports and embedded launch commands were
  updated, and the full default example collection still produced
  `5 passed, 8 deselected`.
- `scripts/generate_examples_md.py` now writes
  `core/python/docs/examples.md`. Two consecutive post-change runs produced
  SHA-256
  `6c465e63b5a6602743fc2dd2c9c38a3d4c582acd1c684073db3d0ba5497f8244`.
- The new `core/python/docs/types-and-protocols.md` provides the compact mental
  model formerly supplied by the root page. Maintained type and Core
  docstrings now describe the actual frozen/nested-value boundary, message
  fields, `MessageRole`, tool descriptors, model descriptor dictionaries,
  plugin state, cancellation, and Core-owned caches/I/O.
- Live MkDocstrings output was inspected for `MessageRole`, `Message`,
  `PartialMessage`, `Session`, `ToolDescriptor`, `ProviderPlugin`,
  `ProviderExtensionPlugin`, `FeaturePlugin`, and `ToolPlugin`. Malformed
  provider examples, duplicate prose, nonexistent `stream_request`, and
  misleading all-methods-pure claims were removed from maintained sources.
- The superseded root page moved to
  `archive/root-docs/TYPES_AND_PROTOCOLS.md`. Current root, package,
  application, MkDocs, and LLM links now route to package-local Core sources.

### Legacy types/protocols disposition

| Legacy section | Disposition |
|---|---|
| Core data types | Current fields and semantics are in the new overview and maintained `agent_core.types` docstrings. The old `ModelDescriptor` pseudo-type was replaced by the actual `get_models` dictionary contract; no API was invented. |
| State model | Shared provider/extension/feature state, independent tool state, short-lived instances, and application-owned durability are summarized in the new overview and detailed in shared plugin guides. |
| Plugin type detection | The current structural classification is summarized in the overview and retained in the moved Core SDK guide and `AgentCore.discover_and_register` reference. |
| Base plugin properties and UI | Actual protocol identity/config/UI hooks remain in `BasePlugin` docstrings. Current UI shapes and compatibility are owned by `plugins/docs/ui-elements.md`; unsupported legacy `description`/`author`/`repository` requirements were not reproduced. |
| Provider protocol | Exact current members come from `ProviderPlugin` docstrings; lifecycle, streaming, and native-history recipes remain in `plugins/docs/provider-plugins.md`. Stale signature listings were discarded. |
| Provider-extension protocol | Exact current members come from docstrings; hot/cold-path responsibilities and recipes remain in `plugins/docs/provider-extensions.md`. |
| Feature protocol | Exact current members come from docstrings; cold-path behavior, actions, templates, completions, context, and UI guidance remain in `plugins/docs/feature-plugins.md` and `plugins/docs/actions.md`. |
| Tool protocol | Exact current members come from docstrings; preparation, schema/call/result interop, execution, streaming, context, and testing remain in `plugins/docs/tool-plugins.md` and `plugins/docs/tool-interop.md`. |
| Core SDK interface | Selected workflows and methods are in the moved Core SDK guide; exhaustive signatures remain generated from `agent_core.core`. |
| Tool interop model | A compact relationship is retained in the new overview, with the full current contract in `plugins/docs/tool-interop.md`. |
| Stream event format | Replaced by the verified application event page, including application/terminal/transport ownership and current indexing/checkpoint fields. |
| Configuration format | Application-managed request configuration and UI contribution concepts are summarized in the overview; current formats are owned by application configuration and shared config-schema/UI guides. |
| Session actions and layered context | Summarized in the overview and owned in detail by `plugins/docs/actions.md` plus protocol docstrings. |
| Basic and streaming flows | Replaced by concise current flow diagrams and linked to `plugins/docs/plugin-execution-order.md`. |
| Session metadata retention | Retained as the provider-native-history explanation in the overview and linked to the provider guide. |
| Plugin examples | Replaced by the canonical generated examples catalog and focused plugin-author guides. |

## Completion Notes

### Outcome

- Core Python now has a concise README, package `AGENTS.md`, public docs index,
  credential-free quickstart, selected Core SDK guide, ownership-organized
  event contract, generated examples catalog, types/protocols overview, and
  structured-logging development guide.
- `docs/index.md`, root README/AGENTS, application request-execution guidance,
  MkDocs navigation, and LLM sections now route to the package-local Core
  sources.
- `TYPES_AND_PROTOCOLS.md` was mined section by section. Useful conceptual
  material now lives in the Core overview or owning focused guides, exact
  Python facts live in maintained docstrings, and the unchanged historical
  source is archived at `archive/root-docs/TYPES_AND_PROTOCOLS.md`.
- The examples generator writes only
  `core/python/docs/examples.md`. Internal plan terminology was removed from
  public headings and paths, and six example/test pairs were renamed
  mechanically.
- Type and Core docstrings now generate readable current reference for the
  important values and plugin protocols. No committed generated reference
  snapshot was edited.
- No runtime behavior or public API was changed.

### Requirement evidence

- Package entry points: production preparation selects
  `core/python/docs/index.md` for `packages/core-python`; the prepared tree
  contains every planned Core page and excludes `AGENTS.md`.
- Quickstart: the exact fenced example executes against the package-local echo
  provider, prints `SYS= | USER=Hello from the echo provider!`, and returns a
  two-message session.
- Core SDK: all 19 dedicated method headings resolve to current `AgentCore`
  methods; the full default Core test suite passed.
- Events: application producer/store/notification and selected terminal HTTP
  event/cursor/compaction/lifecycle/snapshot suites passed.
- Examples: default tests passed before and after migration, all 13 tests
  collected, and two final generator runs produced the same SHA-256
  `6c465e63b5a6602743fc2dd2c9c38a3d4c582acd1c684073db3d0ba5497f8244`.
- Types/protocols: generated HTML contains `MessageRole`, `Message`,
  `PartialMessage`, `Session`, `ToolDescriptor`, `ProviderPlugin`,
  `ProviderExtensionPlugin`, `FeaturePlugin`, and `ToolPlugin` with the
  corrected source descriptions.
- Legacy retirement: the archived file SHA-256
  `b4941aed355ea602498e9fdf5b5776869744be384b43c888ea2dcd8f72ec3928`
  matches the former root file exactly; no current source links to it.
- Publication: package preparation and normal MkDocs build pass, all canonical
  built routes exist, and Core guides appear in generated LLM output.

### Verification performed

- `pytest core/python/tests -q -m 'not integration'`:
  `508 passed, 1 xfailed, 26 deselected`.
- `pytest core/python/examples/tests -q -m 'not integration'` before and after
  migration: `5 passed, 8 deselected` each time.
- Focused Core/type/quickstart tests: `42 passed`.
- Focused application streaming, event store, application notification, and
  session notification tests: `56 passed`.
- Selected terminal HTTP event, cursor, compaction, message lifecycle, fork,
  send-message, and snapshot tests: `17 passed, 44 deselected`.
- `python -m pytest docs_site/tests/test_prepare_mkdocs_site.py -q`:
  `15 passed`.
- `python docs_site/scripts/prepare_mkdocs_site.py`: passed.
- Normal `mkdocs build`: passed.
- Focused Ruff checks for changed Core, event-store, example, generator, and
  documentation-test sources: passed.
- `ruff check application/python/agent_terminal_app/server.py --ignore F811`:
  passed. Running that whole file without the baseline exclusion reports its
  two pre-existing duplicate route-function definitions.
- Current Markdown target validation, stale-source/provenance searches,
  generated-tree ignore checks, output inspection, and `git diff --check`:
  passed.

### Findings and plan adjustments

- The previous package README contained useful logging details, so those were
  retained in a dedicated development page while the README was shortened.
- Merely changing example headings would have left internal `project_plan`
  language in public file paths. Six example/test pairs and their internal
  imports/launch commands were therefore renamed without changing behavior or
  catalog order.
- Existing Core and event-store docstrings repeated two inaccuracies exposed
  during documentation verification: universal Core purity and integer-like
  event IDs. These nearby maintained reference sources were corrected along
  with `agent_core.types`.
- The final MkDocs build reports six pre-existing broken-link warnings from
  unchanged shared plugin pages. This subtask introduced no unresolved build
  warning and removed the Core docstring parsing/cross-reference warnings seen
  during implementation.
- The full server module has two pre-existing Ruff `F811` findings for
  duplicate route-function names. The only server change here corrects the
  `GET /events` parameter documentation; lint passes when those baseline
  findings are excluded.

### Downstream work

- Eight integration-gated examples were not run: five local Ollama examples
  and three hosted/provider examples. They were collected but deliberately
  excluded by `-m 'not integration'`.
- Subtask 050 now depends on 030 and owns package-local generated-reference
  directives, committed snapshot policy, and final reference normalization.
- Subtask 060 owns compatibility for `/api/core-sdk/` and `/api/events/`, final
  navigation curation, exhaustive inbound-link review, and documentation build
  triggers. The canonical destinations and new examples/types routes are
  recorded in this task.
- Subtask 070 owns final cross-task build, audience-journey, warning-baseline,
  and migration-inventory verification.
- No human-only acceptance requirement is assigned to this subtask.

## Post-completion follow-up

- Correction to the integration-gated example breakdown above: the eight
  examples not run comprise six local Ollama examples and two hosted
  OpenRouter examples. The total and verification classification are
  unchanged.