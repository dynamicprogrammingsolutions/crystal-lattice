# Persistent and bounded session listing

Define the complete application-layer session-list contract and implement a
server-only session-list service that reuses summaries across runtimes,
returns every metadata-discovered session within a bounded full-resolution
wait, and hides caching and background-resolution details behind the existing
`SessionListService` interface.

Specification:
`core/python/docs/development/specifications/session-listing/index.md`

## Requirements checklist

### Functional requirements

- [x] The application-layer session-list contract is specified together with
      live implementation, verification, documentation, and evidence status
      for important existing and target behavior.
- [x] `SessionListService` retains its current public query, exact-summary,
      invalidation, diagnostics, and filter-evaluator methods and return types.
- [x] HTTP and terminal adapters continue to consume the same
      `AgentApplication` session-list methods without client-side changes.
- [x] An unfiltered, unlimited list returns one summary-shaped entry for every
      session found by metadata enumeration, including sessions whose full
      files are not resolved during the foreground wait.
- [x] Unresolved sessions use the existing summary and presentation shape with
      values derived only from opaque store records, filename identity, and
      stat metadata; creating a placeholder does not open session content.
- [x] The initial implementation reuses complete summaries across application
      runtimes and does not open unchanged session files when their stored
      revision and summary-contract fingerprint remain valid.
- [x] New, changed, invalidated, or uncached sessions are offered for complete
      resolution in descending modification-time order.
- [x] Complete summaries available by the implementation-specific foreground
      deadline precede metadata-only placeholders; unresolved work continues
      privately and later list calls observe completed summaries.
- [x] Existing complete-summary behavior remains intact: private native
      metadata is excluded, the first user message supplies the preview,
      application-plugin list actions can add fields and ordering, presentation
      fields are derived consistently, malformed records are isolated, filters
      run after ordering and before limits, and exact summary lookup remains
      independent of list filters.
- [x] Application-owned saves and deletes invalidate or refresh internal
      summary state, while external file revision changes and confirmed
      deletions are reconciled.
- [x] The selected service implementation receives opaque application context
      and alone interprets any implementation-specific configuration; no
      shared configuration model or public service surface exposes cache,
      timeout, worker, scan, placeholder-state, or storage-backend concepts.

### Non-functional requirements

- [x] The modification remains within the Python server/application packages
      and does not modify mobile, desktop, frontend SDK, or shared client
      packages.
- [x] Potentially blocking session-content reads do not run on an HTTP event
      loop or hold the session-list service lock, and the initial
      implementation returns after its private foreground budget once
      membership enumeration is complete.
- [x] Resolution concurrency, memory retention, retries, and persistent state
      growth are bounded and do not starve ordinary requests or tool work.
- [x] Concurrent list calls share in-flight work, internal state is thread-safe,
      persistence is transactional, and application close/reload stops owned
      background resources.
- [x] Persistent summary data uses private storage appropriate to its
      implementation, recovers safely from corruption or unavailability, and
      never endangers source session files.
- [x] Diagnostics expose useful timing, cache, placeholder, queue, and failure
      information without logging message content, previews, credentials, or
      complete summaries.
- [x] Existing public API and HTTP contract tests remain valid, and new
      deterministic tests cover persistence, deadline behavior, placeholders,
      ordering, concurrency, failure isolation, and lifecycle cleanup without
      requiring iCloud.

## Scope and specification proposal

Status: Approved by the user on 2026-09-02

### Proposed owner

`core/python/agent_app` owns the shared session-list abstraction through
`SessionListService` and the `AgentApplication` methods consumed by terminal
and HTTP adapters. The proposed package-owned specification location is:

`core/python/docs/development/specifications/session-listing/`

### Proposed behavior scope

The specification will define the complete application-layer session-list
target, including:

- opaque session-store record discovery and exact record lookup;
- base summary shape, preview extraction, metadata exclusion, and fallback
  presentation;
- application-plugin `session_list` action contributions and isolation;
- ordering, path resolution, field rendering, diagnostics, filtering, limits,
  and exact-summary behavior;
- summary validity, invalidation, external-change detection, and deletion;
- implementation-independent `SessionListService` boundaries and opaque
  application context;
- target cross-runtime summary reuse;
- the initial server-side cached/background implementation's complete-entry
  and metadata-only placeholder behavior;
- bounded foreground full resolution after metadata membership is known;
- background ownership, concurrency, persistence safety, privacy, failure
  behavior, and application lifecycle cleanup.

The specification will distinguish durable consumer-visible requirements from
the replaceable cached/background implementation. It will not make local cache
paths, SQLite, timeout keys, worker counts, scan generations, or placeholder
status part of the public service contract.

### Why existing specifications are insufficient

No current package specification defines the `agent_app` session-list
abstraction or its existing tested summary, plugin, ordering, filter,
diagnostic, and invalidation behavior. The target also introduces persisted
derived state, concurrency, bounded waiting, and lifecycle decisions that are
substantial enough to preserve independently of this task.

### Relationship and overlap

- `docs/development/specifications/sessions-actions/` continues to own the
  frontend Sessions action model. It does not own list construction or server
  resolution.
- `core/python/docs/development/specifications/application-configuration-composition/`
  continues to own generic application configuration loading and composition.
  The session-list implementation receives resolved context and privately
  interprets its own keys.
- `docs/development/specifications/application-runtime-reload/` continues to
  own runtime replacement and the requirement that old application resources
  close. The session-list specification refines which resources this service
  owns and must release.
- The application HTTP package remains an adapter and verification boundary;
  it does not become the specification owner.
- Client behavior, frontend actions, and frontend refresh/polling are excluded.

### Proposed specification files

- `index.md` — ownership, scope, relationships, and document map.
- `product-spec.md` — users, developer consumers, existing behavior, target
  outcomes, goals, non-goals, and acceptance examples.
- `technical-spec.md` — stable service contract, store records, summary
  construction, plugin contributions, ordering/filtering, implementation
  encapsulation, initial cached/background design, persistence, concurrency,
  lifecycle, failures, privacy, and verification.
- `requirements.md` — stable `SLIST-*` requirements with separate
  implementation, verification, documentation, and evidence state.
- `decisions/001-service-boundary-and-implementation-independence.md` —
  preserve the existing service surface while keeping resolution and storage
  mechanisms replaceable and private.

Existing tested requirements will begin with evidence-backed `Implemented`
and `Automated` states. New persistence, deadline, placeholder, and background
requirements will begin `Not started`, `Unverified`, and `Pending`.

## Requirement questions and decisions

### Confirmed requirement decisions

- Decision: implementation scope is server/application Python only; no client
  changes are allowed.
- Decision: every metadata-discovered session remains present in an unlimited
  response; unresolved files receive standard-shape placeholders.
- Decision: `SessionListService` retains its current public method surface.
- Decision: implementation-specific behavior and configuration remain private
  to the selected service implementation.
- Decision: the initial cached/background behavior is replaceable and must not
  introduce public scan, cache, timeout, or storage concepts.

### Resolved requirement question

- Decision: metadata enumeration means reading only session membership and
  file attributes. It occurs before the implementation-specific foreground
  deadline begins. The deadline bounds opening and resolving complete session
  content after current membership is known.

## Research and current behavior

### Verified facts

- `FilesystemSessionStore.list_records()` returns opaque records containing
  session identity, modification time, and a revision based on filesystem
  metadata without exposing paths.
- `SessionListService` currently enumerates records, loads each uncached
  session synchronously, derives a summary, executes `session_list` actions,
  applies ordering, then filters and limits the result.
- The current cache is process-local and validates entries by record revision
  and a token derived from list actions and presentation fields.
- Saving through `AgentApplication` invalidates the process-local summary;
  external changes are detected through revision comparison.
- Existing tests verify opaque records, preview and metadata behavior, plugin
  field/action isolation, deterministic plugin ordering, mtime fallback,
  process-local caching, save invalidation, external changes, malformed-record
  fallbacks, filter ordering, exact-summary behavior, shared presentation
  cases, HTTP serialization, and HTTP/terminal delegation.
- The current presentation fallback produces `Session <first-eight-id-chars>`
  when neither a declared title nor preview is available.
- The authored specification prepares successfully for the documentation site,
  and the MkDocs build completes without a session-listing link warning.

### Assumptions to validate during execution

- Store record metadata can be extended with optional access time, birth time,
  and file size without breaking existing stores or test doubles.
- The initial implementation can persist complete summaries and normalized
  ordering data without persisting complete sessions.
- Application-plugin list enrichment should initially remain serialized unless
  its execution boundary is proven safe for concurrent calls.
- A private implementation factory or private delegate under
  `SessionListService` provides enough replacement flexibility without
  introducing a new public strategy API.

## Execution plan

Status: Approved

The task first creates the approved package specification and live
requirements, then implements the target through the stable
`SessionListService` boundary. The specification describes the complete
session-list contract, while the implementation keeps the cached/background
approach private and replaceable.

### Specification approach

Create the approved specification file set under
`core/python/docs/development/specifications/session-listing/`. Record
important existing behavior as implemented requirements only where current
tests or direct implementation inspection provide evidence. Record target
requirements for persistent reuse, bounded full resolution, complete
membership through placeholders, opaque implementation context, concurrency,
and lifecycle cleanup. Add the specification to the Core Python development
index and keep task/progress language out of current user documentation.

### Implementation approach

1. Preserve `SessionListService` as the sole application-facing session-list
   façade. Pass opaque application context into construction and either keep
   the cached/background engine directly private to the class or delegate to a
   package-private implementation selected by a package-private factory.
2. Extend opaque store records only with generally useful optional metadata
   needed to construct placeholders without reading content.
3. Separate complete summary derivation from session loading so existing
   summary, action, presentation, ordering, filter, and diagnostic behavior can
   be reused by foreground work, background work, and application-owned saves.
4. Add pure metadata-only placeholder construction that returns the existing
   summary shape and presentation fallback without invoking session-dependent
   plugin actions.
5. Implement private persistent summary storage for the initial local
   implementation. Validate entries through record revision and a complete
   summary-contract fingerprint. Keep storage location, format, recovery, and
   locking private to that implementation.
6. Add a private coordinator that deduplicates scans, seeds complete results
   from valid persisted summaries, prioritizes remaining records by descending
   mtime, waits for the implementation's configured foreground budget, and
   continues unresolved work with bounded background resources.
7. Return all discovered sessions: apply existing ordering to complete
   summaries, append placeholders by descending mtime, then apply conservative
   filtering and the existing limit semantics.
8. Integrate invalidation with session saves/deletes and close background
   resources through `AgentApplication` lifecycle without adding public
   scanner methods.
9. Verify public application and HTTP boundaries, deterministic delayed-store
   behavior, cross-runtime reuse, corruption recovery, concurrency, and clean
   shutdown. No client package is changed.

### Implementation decisions and open questions

- Recommendation: use a stable `SessionListService` façade with a private
  implementation delegate. This minimizes consumer changes while allowing a
  later cloud-indexed or otherwise materially different implementation.
- Recommendation: do not add public scan-state or placeholder-state fields.
  Placeholder entries use only the established summary shape.
- Recommendation: use SQLite for the initial local implementation because it
  supports incremental transactional updates and concurrent readers, but do
  not mention SQLite in the stable service contract.
- Recommendation: keep plugin enrichment serialized initially; bounded file
  loading may use separate workers if it can preserve newest-first priority
  and clean shutdown.
- Decision: metadata-only membership enumeration precedes the foreground
  full-resolution deadline.
- Open implementation decision: exact persistent fingerprint inputs and
  representation must be finalized after inspecting application-plugin
  identity/version and resolved UI/action inputs.
- Open implementation decision: whether application-owned saves should
  synchronously publish a complete derived summary or only invalidate and
  enqueue it, provided public correctness and bounded request work are
  preserved.

### Documentation

- Create the approved package-owned session-list specification and requirements.
- Link it from `core/python/docs/development/index.md`.
- Update current Core application-layer implementation documentation for
  delivered architecture and operational behavior when implementation lands.
- Update application server user documentation only if the delivered
  implementation introduces a supported configuration key or user-observable
  placeholder behavior that requires explanation.
- Do not add task IDs, requirement IDs, phase labels, or unimplemented claims
  to current user documentation.
- Do not modify client documentation.

### Task checklist

- [x] Create isolated worktree and branch from the committed `develop` state.
- [x] Review repository documentation/specification standards and owning
      package entry points.
- [x] Inspect existing session-list implementation, tests, and adjacent
      specifications sufficiently to propose ownership and overlap.
- [x] Record the specification scope, file set, existing evidence approach, and
      draft implementation plan in this task.
- [x] Obtain explicit approval for the proposed specification ownership,
      behavior scope, overlap, file set, and foreground-deadline boundary.
- [x] Write the approved session-list specification and requirements, then
      check this item complete while leaving the implementation plan `Draft`.
- [x] Link the specification from the Core Python development index.
- [x] Present the completed specification and reassessed draft implementation
      plan for execution approval.
- [x] After explicit execution approval, mark the plan `Approved`.
- [x] Implement the server-side session-list correction.
- [x] Add and run focused Core application-layer tests.
- [x] Add and run HTTP/server contract tests without client changes.
- [x] Run broader affected Core and application verification.
- [x] Update current implementation and user documentation as warranted by
      delivered behavior.
- [x] Update requirement evidence.
- [x] Append completion notes with final delivery evidence.

### Requirement verification

- Public service compatibility and existing complete-summary behavior:
  existing Core session-list, filter, plugin, and application API contract
  tests plus focused regressions.
- Complete membership and metadata-only placeholders: deterministic delayed
  store tests asserting every discovered ID is returned and unresolved records
  are never opened by placeholder construction.
- Persistent reuse: construct a second application/service over the same
  session root and assert unchanged sessions are complete without store loads.
- Deadline and background completion: controlled clock/blocking-store tests
  assert bounded foreground return, newest-first attempts, placeholder suffix,
  shared in-flight work, and complete later calls.
- Server boundary: FastAPI `TestClient` verifies the unchanged
  `{"sessions": [...]}` envelope and valid summary shape without any frontend
  modifications.
- Lifecycle and safety: application close/reload tests verify owned workers and
  persistent resources are released; corruption tests verify safe rebuilding.

### Additional implementation verification

- Run the focused session-list and filter suites under `core/python/tests`.
- Run `application/python/tests/test_session_list_http_contract.py` and focused
  terminal/server delegation tests.
- Run the default Core and application Python suites if focused verification
  passes.
- Run relevant lint and type checks for changed Python modules.
- Inspect the final diff to confirm no mobile, desktop, frontend SDK, or other
  client package changes.

## Implementation Notes

- Execution began after explicit approval on 2026-09-02. The specification and
  approved plan baseline was committed as `180b7829`.
- The initial persistence implementation uses a package-private SQLite helper
  with operation-scoped connections. Its location, schema, revision token, and
  failure behavior are not added to the public `SessionListService` surface.
- Optional access time, creation time, and size were added to opaque
  `SessionStoreRecord` values with defaults so existing stores and test doubles
  remain source-compatible.
- The cached/background resolver remains private inside `SessionListService`
  instead of introducing a public or injected strategy. This keeps existing
  summary/action/order helpers together and permits a future implementation to
  replace the service internals or the whole service.
- Full application verification revealed that deriving cache location from a
  bundled configuration path could write generated databases into the source
  tree. The final default is `~/.crystal/cache/session-list`; ephemeral session
  roots under the operating-system temporary directory keep their cache beside
  that temporary root.
- One scheduled task per session bounds obsolete queued revisions. When stale
  work exits, the resolver automatically schedules the latest desired revision
  so background convergence does not require another list request.

## Completion Notes

### Outcome

- `SessionListService` now enumerates opaque session attributes before starting
  a configurable full-resolution budget, reuses valid complete summaries from
  private persistent state, resolves misses newest-first, and returns every
  discovered session through the existing summary shape.
- Complete summaries precede metadata-only fallbacks while unresolved work
  continues on bounded private daemon workers. Later calls observe completed
  work without a client protocol change.
- The existing public service and `AgentApplication` methods remain unchanged.
  HTTP retains the `{"sessions": [...]}` envelope, and no client package was
  modified.
- The current implementation reads only its own
  `application.cached_background_session_list` settings from opaque
  application context. No shared implementation-specific configuration model
  or public cache/scanner surface was introduced.
- Complete derived summaries are stored in user-private SQLite databases under
  `~/.crystal/cache/session-list` by default. Temporary session roots use
  temporary colocated state. Revision, contract, and invalidation tokens
  prevent stale reuse or obsolete background publication.

### Requirement evidence

- `SLIST-001` through `SLIST-010` retain their existing implementation and
  automated evidence.
- `SLIST-011` through `SLIST-020` are implemented, automated, and documented in
  `core/python/docs/development/specifications/session-listing/requirements.md`.
- Primary implementation: `core/python/agent_app/session_listing.py`,
  `core/python/agent_app/_session_list_cache.py`,
  `core/python/agent_app/sessions.py`, and
  `core/python/agent_app/application_future.py`.
- Primary regression coverage:
  `core/python/tests/test_application_session_listing.py`,
  `core/python/tests/test_session_list_cache.py`, and
  `application/python/tests/test_session_list_http_contract.py`.
- Implementation delivery commit: `a2fcebfa`.

### Verification

- `pytest core/python/tests -q`: 511 passed, 26 deselected, 1 expected failure.
- `pytest application/python/tests -q`: 370 passed, 92 deselected.
- Final focused Core session-list/filter/cache run: 23 passed.
- Source-path-controlled HTTP contract run: 5 passed.
- Focused application-plugin close/runtime-environment run: 20 passed.
- Targeted `ruff check`: passed.
- Targeted production-module `pyright`: 0 errors.
- Python compilation checks: passed.
- Documentation-site preparation: passed.
- MkDocs build: passed with existing unrelated navigation/reference warnings.
- `git diff --check`: passed before the implementation commit.

The broader `pyright` invocation that included all of
`application_future.py` still reports unrelated existing errors in that module.
The new session-listing modules and modified session-store module pass targeted
type checking, and no reported error points to the added application-context
or shutdown wiring.

### Plan deviations and findings

- The service keeps the cached/background resolver private within
  `SessionListService` instead of adding a separate injected public strategy.
  A private persistence module isolates storage details while existing summary
  helpers remain together.
- The cache default was changed during verification from configuration-relative
  storage to `~/.crystal/cache/session-list` after the full application suite
  demonstrated that bundled configurations could otherwise create generated
  databases in the source tree. Those generated test files were removed.
- Queue coalescing was strengthened so at most one revision per session is
  scheduled while stale completion automatically schedules the latest desired
  revision.

### Unresolved or deferred scope

- No live iCloud timing test was run because it would hydrate the preserved
  dataless session files. Deterministic blocked-store tests cover the same
  server contract without changing cloud-storage state.
- Metadata membership enumeration is intentionally outside the full-resolution
  deadline. An implementation cannot guarantee both discovery of every current
  filename and a hard deadline when the storage provider itself blocks
  attribute enumeration.
- Python cannot cancel an operating-system file read already in progress.
  Shutdown cancels queued work and prevents a blocked daemon worker from
  running plugin enrichment or publishing after the read returns.

## Post-completion follow-up

### Requirement organization and traceability

- [x] Group preserved and new requirements separately.
- [x] Divide each group into functional and non-functional requirements.
- [x] Replace plain evidence paths with relative Markdown links whose labels
      identify the repository path.
- [x] Add applicable `SLIST-*` identifiers beside the assertions in primary
      Core, cache, HTTP, and terminal/server test code.
- [x] Assess preserved functional coverage and integration coverage of every
      new functional requirement without changing implementation code.

Assessment:

- Preserved functional coverage is strong for `SLIST-001`, `SLIST-002`,
  `SLIST-006`, `SLIST-007`, and `SLIST-010`.
- `SLIST-003` lacks direct assertions for preview whitespace normalization,
  first-non-empty-user selection, and the 80-character truncation boundary.
- `SLIST-004` lacks direct assertions for non-JSON-serializable contributed
  fields and malformed `session_list_fields` / `session_list_order` result
  containers.
- `SLIST-005` lacks direct assertions for missing order fallbacks,
  non-sortable values, incompatible value categories, and conflicting
  declarations occupying the same plugin slot.
- None of the primary requirement-tagged tests is marked
  `pytest.mark.integration`; marker-selected integration runs therefore do not
  collect these session-list requirements.
- `SLIST-014` has a substantive application integration flow through two
  `AgentApplication` instances, filesystem sessions, and persistent derived
  state, although the test is not marked as integration.
- `SLIST-013` has route/service HTTP coverage, but it overrides
  `AgentApplication` and uses only one session, so it does not prove mixed
  complete/placeholder membership through the full production application
  composition.
- `SLIST-012`, `SLIST-015`, `SLIST-016`, and `SLIST-019` do not each have one
  integration test asserting their complete main statement. Their evidence is
  split across component tests, existing complete-list integration behavior,
  and narrower HTTP assertions.
- No implementation or test behavior was changed after this assessment.

### In-table generated test evidence

- [x] Restore evidence to each preserved/new functional/non-functional
      requirement table.
- [x] Keep hand-maintained implementation and documentation links in the table
      while generating test links after a stable marker.
- [x] Expand requirement annotations above tests with a concise statement of
      what each test proves.
- [x] Add `scripts/update_session_list_requirement_evidence.py` with explicit
      requirements/test-file inputs, line-numbered relative links, update mode,
      and `--check` mode.
- [x] Add an automated synchronization test for generated requirement
      evidence.
- [x] Verify the updater, focused Core tests, selected HTTP/terminal tests,
      documentation preparation, and MkDocs build.

The generator currently emits 74 test-function links across all 20
requirements. Link labels contain the package- or repository-relative test path
and current definition line; targets use relative Markdown paths with `#L…`
anchors. Manual source and documentation links remain editable before the
`<!-- test-evidence -->` marker.