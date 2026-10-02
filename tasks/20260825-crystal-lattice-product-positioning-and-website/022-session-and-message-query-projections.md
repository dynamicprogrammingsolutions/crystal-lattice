# Session and Message Query Projections

Add low-level, composable session enumeration and per-session canonical message
queries for Python, CLI, HTTP, and frontend callers. Reuse plugin-declared
session filters, add timezone-aware date comparisons, and support RFC 9535
JSONPath include/exclude projection without fixed message roles or named
presets.

Parent Task: `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md`

Depends On: `tasks/20260825-crystal-lattice-product-positioning-and-website/021-headless-agent-runs-and-optimized-history-api.md`

## Requirements checklist

- [x] Existing session and message collection calls with no `include` or
      `exclude` selector retain their current response envelopes, complete
      fields, ordering, omission rules, and consumer types.
- [x] Session and message collection queries accept repeated RFC 9535 JSONPath
      `include` and `exclude` selectors with wildcard and filter expressions;
      includes union their matches, excludes are evaluated against the
      original document and win, and canonical message indices remain stable.
- [x] Projection conditions may inspect any role, metadata discriminator, or
      future field without a fixed role registry or role-specific API options.
- [x] Plugin-driven `session_list_filter` declarations gain timezone-aware
      date input and before/after comparisons with equivalent Python and
      TypeScript interpretation.
- [x] Python callers can list plugin-filtered sessions and retrieve full or
      projected canonical message ranges from one open local runtime.
- [x] `crystal-lattice sessions` applies the active plugin filter schema and
      emits one undecorated session ID per line when that is the only selected
      text value.
- [x] `crystal-lattice messages` queries exactly one session at a time and
      composes safely in a shell loop fed by `crystal-lattice sessions`.
- [x] CLI JSON output is structurally lossless within the selected projection;
      text, TSV, and CSV output is deterministic, human-readable, and keeps
      each selected value on one physical line for ordinary `grep`.
- [x] Existing HTTP session and message collection endpoints expose the same
      plugin filters and include/exclude projection without changing requests
      that omit the new options.
- [x] The frontend SDK can request projected session/message data, represents
      partial results explicitly, and supports lazy hydration without allowing
      partial data to overwrite complete cached messages.
- [x] Projection, ranges, filters, output, and JSONPath complexity are bounded;
      invalid input has actionable errors and projection is not treated as an
      authorization boundary.
- [x] Current user and developer documentation describes canonical fields,
      plugin-contributed fields, projection semantics, date filters, formats,
      and copyable JSON and text pipelines instead of named presets.
- [x] Source, direct archive/manual, Bash-installed, and PowerShell-installed
      runtimes execute the new commands on applicable native release targets.

These requirements map to `SDQ-001` through `SDQ-013`, `SLIST-021` onward,
`HLR-090` onward, and `CLIDIST-119`.

## Resolved requirement decisions

- Projected JSON does not retain `session_id`, canonical message `index`, or
  role automatically when an include list does not select them. JSON
  projection remains strict, while text/TSV/CSV rendering may use
  unprojected identity context in its fixed prefix or columns.
- Repeated GET query parameters are the only initial HTTP expansion. A
  structured read-only POST endpoint requires real transport or URL-length
  evidence and separate approval.
- `datetime` filter runtime values are timezone-bearing ISO-8601 strings.
  Candidate summary data may be numeric epoch seconds or timezone-bearing ISO
  strings.
- CSV/text/TSV normalize or escape embedded record separators to preserve one
  physical record per selected value. JSON is the lossless exact multiline
  format.

## Approved direction

- Create a separate subtask rather than reopening completed task 021.
- Use both `include` and `exclude`; neither option means current behavior.
- Use standard JSONPath notation, including wildcards and filter selectors.
- Evaluate type-specific behavior through data conditions rather than fixed
  role-specific request fields.
- Do not add named projection presets. Documentation examples provide common
  reusable queries.
- Reuse the existing plugin-driven session filter contract and add date input.
- Add one-session `messages` rather than a multi-session messages command.
- Compose broad searches by piping one session ID per line from `sessions`
  into repeated `messages` calls.
- Keep JSON for exact structured consumers and add concise text/TSV/CSV
  formats for humans and ordinary shell search.

## Current behavior and supporting facts

- `AgentApplication.list_session_summaries(...)` already accepts plugin filter
  values, applies filters before limits, and returns shared plugin-enriched
  summaries.
- Session summaries contain `session_id`, numeric `modified`, `preview`,
  metadata, presentation, and plugin-contributed top-level fields.
- Plugins declare `session_list_filter` UI elements over dotted summary paths.
  Current filter types are text, boolean, and select; date comparison is not
  implemented.
- Python and TypeScript maintain corresponding filter evaluators. Frontends
  currently download summaries and apply filters client-side. The interactive
  terminal can pass plugin filter values in process.
- `GET /sessions` currently accepts only `limit`; it does not accept plugin
  filter values or projection.
- `GET /sessions/{session_id}/messages` returns indexed complete canonical
  messages for optional slice-style `start` and `end` bounds.
- Canonical messages contain `role`, `content`, optional `metadata`, optional
  `multipartContent`, and optional `toolResult`. Reasoning is conventionally
  surfaced under metadata.
- The local runtime currently exposes fixed compact `history(...)` and one
  canonical `get_message(...)`; it does not list sessions or full message
  ranges.
- One-shot CLI commands currently reserve `agents`, `run`, and `history`.
- Frontend SDK session and message methods currently return complete
  `SessionSummary` and `IndexedMessage` values and cache complete ranges.
- RFC 9535 JSONPath defines node selection, not the tree-projection rules
  needed by include/exclude. Crystal Lattice must define ancestor retention,
  exclusion precedence, array removal, ordering, and no-match behavior.

## References

### Start here

1. `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md`
   — parent requirements, boundaries, and subtask tracking.
2. `application/python/docs/development/specifications/session-data-query/index.md`
   — owning target specification and requirement links.
3. `application/python/docs/development/specifications/session-data-query/product-spec.md`
   — user workflows, examples, goals, and non-goals.
4. `application/python/docs/development/specifications/session-data-query/technical-spec.md`
   — proposed JSONPath, Python, CLI, HTTP, frontend, output, and limit
   contracts.
5. `application/python/docs/development/specifications/session-data-query/requirements.md`
   — `SDQ-*` implementation, verification, and documentation state.
6. `core/python/docs/development/specifications/session-listing/index.md` and
   `core/python/docs/development/specifications/session-listing/requirements.md`
   — shared summaries and plugin-driven filter ownership.
7. `application/python/docs/development/specifications/headless-agent-runs/index.md`
   and `requirements.md` — local Python and one-shot CLI refinement.
8. `application/python/docs/development/specifications/cli-distribution/index.md`
   and `requirements.md` — native packaged-command verification.

### Current implementation entry points

- `core/python/agent_app/session_listing.py`
- `core/python/agent_app/session_filters.py`
- `core/python/agent_app/history_projection.py`
- `application/python/agent_terminal_app/local_runtime.py`
- `application/python/agent_terminal_app/__main__.py`
- `application/python/agent_terminal_app/server.py`
- `packages/frontend-sdk/src/backend/backend.ts`
- `packages/frontend-sdk/src/backend/restBackend.ts`
- `packages/frontend-sdk/src/sessions/sessionListFilters.ts`

## Target examples

### JSON projection

```bash
crystal-lattice messages \
  --session 01abc \
  --include '$.messages[*].index' \
  --include '$.messages[*].message.role' \
  --include '$.messages[*].message.content' \
  --include '$.messages[*].message.metadata.reasoning' \
  --exclude '$.messages[?(@.message.role == "tool")]' \
  --format json
```

```json
{
  "messages": [
    {
      "index": 12,
      "message": {
        "role": "assistant",
        "content": "Crystal Lattice supports local runtimes.",
        "metadata": {
          "reasoning": "Check the active Crystal Lattice configuration."
        }
      }
    }
  ]
}
```

### Text output

```text
01abc [12] assistant content: Crystal Lattice supports local runtimes.
01abc [12] assistant metadata.reasoning: Check the active Crystal Lattice configuration.
```

### Date-prefiltered shell search

```bash
cutoff="$(
  python -c 'from datetime import datetime, timedelta, timezone; print((datetime.now(timezone.utc) - timedelta(days=14)).isoformat())'
)"

crystal-lattice sessions \
  --filter "modified_after=$cutoff" \
  --include '$.sessions[*].session_id' \
  --format text |
while IFS= read -r session_id; do
  crystal-lattice messages \
    --session "$session_id" \
    --include '$.messages[*].index' \
    --include '$.messages[*].message.role' \
    --include '$.messages[*].message.content' \
    --include '$.messages[*].message.metadata.reasoning' \
    --exclude '$.messages[?(@.message.role == "tool")]' \
    --format text
done |
grep -i 'crystal lattice'
```

## Scope boundaries

- Do not implement a server-side full-text index or general search DSL.
- Do not add named projection presets.
- Do not add role-specific request fields or validate against a closed role
  set.
- Do not add an initial multi-session messages command.
- Do not replace compact history or change canonical storage.
- Do not make projection an authorization mechanism.
- Do not publish target-only commands or examples as current user guidance
  before implementation and verification.
- Do not weaken metadata-only session-list behavior, snapshots, request
  coordination, or frontend cache consistency.

## Expected outputs

- Target and requirement updates remain under the owning application/core
  development specifications until implemented.
- Current Python, CLI, HTTP, frontend, and plugin documentation is updated
  only with delivered behavior.
- Unit, contract, integration, subprocess, frontend, and native-distribution
  tests prove the boundaries claimed by their evidence.
- No generated documentation tree is edited directly.

## Execution plan

Status: Approved

Implement one shared pure projection layer over already serialized response
documents. Keep session summary/filter ownership in `agent_app`, then expose
thin Python, CLI, HTTP, and TypeScript adapters over those application
operations. Preserve current unprojected paths as the decisive compatibility
boundary.

First, settle the open public-contract decisions and select an RFC 9535
implementation through focused conformance probes. Add projection tests before
adapter work, including filtered selectors, wildcard selection, ancestor
reconstruction, exclude precedence, whole-array-element removal, missing
matches, invalid syntax, ordering, and hard limits.

Extend the normalized plugin filter contract with timezone-aware datetime
comparison in Python and TypeScript. Use current session summaries and
contributed fields; do not create an adapter-specific date flag. Add parity
fixtures and verify filtering, established ordering, limits, defaults,
metadata-only conservative behavior, and exact lookup.

Add local-runtime `list_sessions(...)` and `list_messages(...)` methods over
shared application operations. Retain `history(...)` and `get_message(...)`.
Then add one-shot `sessions` and one-session `messages` commands with repeated
filter/include/exclude arguments and exact JSON/text/TSV/CSV renderers.

Extend existing HTTP collection endpoints with repeated query parameters only
after the application operations are covered. Add frontend SDK query options
and projected result types, then update real mobile/desktop consumers to
request focused visible fields and lazily hydrate omitted fields where that
improves network use without corrupting complete caches.

Finally, update current documentation from the verified implementation, run
the documented date-prefiltered grep pipeline, and add deterministic native
distribution checks for the new commands across source, archives, Bash
installation, and PowerShell installation.

### Implementation decisions and open questions

- Approved: selectors use RFC 9535 syntax; no selector preserves current
  behavior; includes union; exclusion wins; selectors may condition on
  arbitrary data; no presets or fixed role registry.
- Approved: the initial CLI uses one-session `messages` and shell chaining,
  not a multi-session command.
- Approved: plugin-driven filtering remains the session-prefilter authority
  and gains a date input.
- Decision: JSON projection is strict and adds no implicit identity fields,
  while line-oriented renderers may use
  original session/index/role context in their fixed columns.
- Decision: repeated GET parameters are the only initial HTTP expansion;
  evidence, not speculation, is required before adding a POST query endpoint.
- Decision: caller date values must carry timezone information; numeric epochs
  remain valid candidate data rather than preferred CLI input.
- Decision: text, TSV, and CSV normalize or escape embedded record separators;
  JSON remains the exact multiline representation.
- Local implementation choice after approval: select an RFC 9535 library only
  after conformance, maintenance, dependency, performance, and license review.

### Documentation

- Keep the new target under
  `application/python/docs/development/specifications/session-data-query/`.
- Extend the session-listing specification and application-plugin UI-element
  guide for datetime filters.
- Extend headless-run and CLI-distribution specifications by reference rather
  than duplicating projection semantics.
- After implementation, update the application headless/CLI guides, HTTP
  endpoint guidance, frontend SDK docs, and plugin UI-element docs.
- Document every canonical envelope field and plugin-extension boundary.
- Include JSON, text, TSV/CSV, Python, HTTP, and shell-loop examples. Examples
  replace named presets and must be verified against the implementation.

### Task checklist

- [x] Approve the remaining public-contract recommendations above.
- [x] Select and verify an RFC 9535 implementation.
- [x] Implement the pure include/exclude projector and limits.
- [x] Add datetime plugin filters with Python/TypeScript parity.
- [x] Add application and local-runtime session/message query methods.
- [x] Add `sessions` and one-session `messages` CLI commands and all formats.
- [x] Extend existing HTTP endpoints without changing default responses.
- [x] Add frontend SDK projected types, query options, and cache-safe hydration.
- [x] Add focused, integration, subprocess, frontend, and compatibility tests.
- [x] Update current consumer and developer documentation after delivery.
- [x] Verify source and all applicable native archive/installer paths.
- [x] Update all affected requirement evidence and append completion notes.

### Requirement verification

- **Backward compatibility (`SDQ-001`):** Existing Python, HTTP, and frontend
  calls without selectors produce structurally equal complete results; current
  compact history and full-message lookup tests remain green.
- **Projection (`SDQ-002`, `SDQ-003`, `SDQ-011`):** Pure contract tests and
  public-boundary integration tests prove RFC syntax, conditional wildcards,
  include union, exclude precedence, ancestors, subtrees, arrays, no matches,
  generic roles, stable indices, limits, and bounded errors.
- **Plugin filtering (`SDQ-004`, `SLIST-021+`):** Shared fixtures produce the
  same selected sessions and diagnostics in Python and TypeScript for valid,
  invalid, timezone-offset, defaulted, and metadata-only cases.
- **Python and CLI (`SDQ-005`–`SDQ-007`, `HLR-090+`):** Public runtime tests
  and real subprocess tests prove session enumeration, one-session ranges,
  exact stdout/stderr, all formats, failures, and the documented shell chain.
- **HTTP and frontend (`SDQ-008`, `SDQ-009`):** FastAPI `TestClient` contract
  tests plus production REST-adapter integration prove encoded selectors,
  unchanged defaults, projected types, lazy hydration, and cache isolation.
- **Output and documentation (`SDQ-010`, `SDQ-012`):** Exact output fixtures
  and executable documentation examples prove one-line text/TSV/CSV behavior
  and parseable lossless JSON.
- **Native distribution (`SDQ-013`, `CLIDIST-119`):** Existing smoke
  scenarios execute representative JSONPath queries and line chaining through
  source, direct archives, Bash-installed commands, and native PowerShell
  commands on applicable targets.

### Additional implementation verification

- Run Core, application, frontend SDK, frontend React, shared React Native,
  mobile, and desktop default suites affected by the contract.
- Run changed-file Ruff, Black, Pyright, TypeScript, JSON, documentation,
  workflow-security, and whitespace checks.
- Test shell quoting with spaces and JSONPath filter expressions on POSIX,
  PowerShell, and `cmd.exe`.
- Measure projection and client-transfer reduction with representative large
  tool payloads; do not weaken output or limit assertions to improve timing.

## Implementation Notes

- The user approved the complete Draft plan and all four recommended
  public-contract decisions. Implementation began with the specification and
  task changes present in the worktree.
- Selected MIT-licensed `python-jsonpath` 2.x in strict mode after package
  metadata, supported-Python, node-location, filter, wildcard,
  recursive-descent, and root-query probes. It is tested against the standard
  compliance suite and is pure Python on all six native targets. The initially
  preferred `jsonpath-rfc9535` package was rejected because its compiled
  `iregexp-check` dependency has no Windows ARM64 wheel. The existing
  `jsonpath-ng` dependency remains for its unrelated existing consumer.
- Added strict include/exclude reconstruction with source-order preservation,
  clean array removal, selectors evaluated against the original document,
  match/selector/length/output bounds, and no-selector identity behavior.
- Added plugin-owned timezone-aware datetime filters in Python and TypeScript;
  the default timestamp metadata plugin now declares `modified_after` over the
  built-in `modified` field. Mobile and desktop share a draft-then-commit date
  input so partial timestamps are not rejected during typing.
- Added direct Python, CLI, existing-HTTP-route, and frontend REST query
  surfaces. Projected SDK methods are separate from complete list methods, so
  partial messages cannot enter the existing complete-message cache path.
- Focused projection, filter, CLI subprocess, local-runtime, rendering,
  FastAPI, production REST-adapter, shared-component, mobile, and desktop
  checks passed before the complete suites and distribution matrix. Final
  counts and evidence are recorded in Completion Notes.
- The first all-native run exposed PowerShell `-File` argument forwarding
  removing inner double quotes from the tool-role JSONPath string. The smoke
  now uses the equivalent RFC-valid single-quoted literal and has a focused
  regression assertion. Final run
  [36442124636](https://github.com/dynamicprogrammingsolutions/crystal-lattice/actions/runs/36442124636)
  passed the hosted tests and all six native archive/installer jobs at commit
  `9592b1ba`.

## Completion Notes

- Delivered strict RFC 9535 include/exclude projection for session and message
  response envelopes with source-order preservation, clean array removal,
  generic conditional selectors, deterministic limits, and unchanged
  no-selector behavior.
- Added timezone-aware plugin datetime filters in Python and TypeScript. The
  built-in timestamp metadata plugin declares `modified_after`; mobile and
  desktop render a draft-then-commit date control.
- Added `LocalAgentRuntime.list_sessions(...)` and `list_messages(...)`,
  one-shot `crystal-lattice sessions` and one-session `messages`, JSON/text/
  TSV/CSV output, existing-route HTTP query parameters, and explicit projected
  frontend SDK types and REST methods.
- Added complete field and usage documentation with Python, CLI, HTTP,
  TypeScript, JSON, text, and `sessions | while read ... messages | grep`
  examples. No named preset, multi-session messages command, server-side text
  index, fixed role registry, or POST query endpoint was introduced.
- Automated local evidence:
  - Core default: 556 passed, 26 deselected, 1 expected xfail.
  - Application default: 486 passed, 1 skipped, 98 deselected.
  - Query/headless integration: 16 passed.
  - Timestamp plugin: 4 passed.
  - Frontend SDK: 351 passed; React bindings: 20 passed; shared RN components:
    51 passed.
  - Mobile: 181 passed; desktop: 144 passed.
  - Production frontend REST adapter against real FastAPI: passed.
  - Targeted Python Pyright, Ruff, Black, JSON, requirement-evidence, link,
    docs preparation, and MkDocs build checks passed.
- Distribution evidence:
  - Clean source installation, direct archive, and default Bash installer
    passed locally on macOS ARM64.
  - Final non-publishing native workflow
    [36442124636](https://github.com/dynamicprogrammingsolutions/crystal-lattice/actions/runs/36442124636)
    passed Linux AMD64/ARM64, macOS AMD64/ARM64, and Windows AMD64/ARM64,
    including every applicable direct archive, Bash installer, and native
    PowerShell installer path. Real-provider access was intentionally disabled
    because this query contract requires no hosted model call.
- Implementation findings and deviations:
  - `jsonpath-rfc9535` was rejected after its compiled `iregexp-check`
    dependency proved to lack a Windows ARM64 wheel. The delivered
    `python-jsonpath` strict-mode engine is pure Python, MIT licensed, and
    compliance-suite tested.
  - Native smoke use of the timestamp plugin exposed and fixed its assumption
    that every config contains an `application` object.
  - The first Windows run exposed PowerShell stripping inner double quotes from
    an argv JSONPath literal; switching the smoke to RFC-valid single quotes
    passed both Windows architectures.
- Existing repository quality baselines remain outside this task: mobile
  ESLint has no discoverable configuration; desktop lint and full frontend SDK
  typecheck report established unrelated errors; and MkDocs reports existing
  plugin/reference warnings. Mobile TypeScript compilation and all affected
  runtime/component tests passed.
- No unresolved or deferred task scope remains.