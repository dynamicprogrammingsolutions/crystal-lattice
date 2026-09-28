# Application session-listing technical specification

## Ownership

`core/python/agent_app` owns live-session discovery, shared summary
construction, application-plugin list triggers, presentation, ordering,
in-process filtering, exact summary lookup, diagnostics, and summary
invalidation.

`application/python` exposes this behavior through terminal and HTTP adapters.
Adapters delegate to `AgentApplication`; they do not scan session storage or
reimplement the summary contract.

Application plugins define action and UI declarations consumed by the service.
They do not own collection orchestration or persistence of shared summaries.

## Stable application interface

`AgentApplication` exposes:

```python
def list_session_summaries(
    *,
    filter_values: Optional[Dict[str, object]] = None,
    apply_filter_defaults: bool = False,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]: ...

def get_session_summary(session_id: str) -> Dict[str, Any]: ...

def get_session_list_diagnostics() -> List[Dict[str, Any]]: ...

def get_session_list_filter_schema() -> Dict[str, Any]: ...

def set_session_list_filter_evaluator(
    evaluator: SessionListFilterEvaluator,
) -> None: ...
```

`SessionListService` remains the sole implementation authority behind these
methods. Its public query, exact-summary, invalidation, diagnostics, and
filter-evaluator methods retain their current signatures and return types.

The service may receive opaque application context during construction. The
selected implementation alone interprets any implementation-specific
configuration. Common application wiring does not expose or normalize cache,
deadline, worker, scan-generation, placeholder-state, or storage-backend
concepts.

## Session-store records

Collection membership comes from `SessionStore.list_records()`. Exact summary
membership comes from `SessionStore.get_record(session_id)`.

A record provides:

- opaque `session_id`;
- numeric `modified` time;
- opaque equality-comparable `revision`;
- optional implementation-neutral storage attributes useful for fallback
  summaries, such as access time, creation time, and size.

Records do not expose filesystem paths through the application contract.
Stores choose their own revision representation. The filesystem store uses
mtime, ctime, size, and inode where available.

Enumerating records may read directory membership and file attributes. It does
not open session content. Snapshot files are not live-session records.

## Shared summary contract

Every returned entry has this base shape:

```typescript
interface SessionSummary {
  session_id: string;
  modified: number;
  preview: string;
  metadata: Record<string, unknown>;
  presentation: {
    title: string;
    subtitle: string | null;
    meta: string | null;
  };
  [contributedField: string]: unknown;
}
```

For a complete session:

- `session_id` and `modified` come from its store record;
- `metadata` contains session metadata except `native_messages`;
- `preview` is the first non-empty user-message content, collapsed to one
  whitespace-normalized line and truncated to 80 characters with a
  three-character ellipsis;
- application-plugin list actions may add valid top-level fields;
- `presentation` is derived after action contributions.

The service reserves `session_id`, `modified`, `preview`, `metadata`, and
`presentation`. Plugin writes to reserved or invalid keys are diagnosed and
ignored. Contributed values must be JSON-serializable.

Returned summaries are treated as immutable by convention.

## Metadata-only summaries

An implementation may need to represent a discovered session before complete
content is available. Such an entry uses the ordinary `SessionSummary` shape:

- `session_id` and `modified` come from the record;
- `preview` is empty;
- `metadata` is empty;
- no session-dependent action contribution is invented;
- `presentation` uses ordinary derivation and therefore falls back to
  `Session ` plus the first eight session-ID characters when no field or
  preview supplies a title.

Creating this summary does not call `SessionStore.load()`, open content, read
snapshots, or invoke a list action that could load the session indirectly.
The public summary does not expose whether it came from a foreground resolver,
background resolver, local cache, cloud index, or metadata fallback.

## Application-plugin list triggers

The service discovers application-plugin actions whose `trigger` is
`"session_list"` or contains `"session_list"`.

For each complete stored session, matching actions execute in application
plugin configuration order and action declaration order. The service supplies
only declared inputs:

- `session_id`: the opaque ID;
- `session_summary`: the summary accumulated through earlier actions;
- `session`: the loaded live `Session`.

Execution context contains:

```python
{
    "lifecycle": "session_list",
    "trigger_source": "application",
    "session_id": session_id,
}
```

Actions may return:

- `session_list_fields`, a mapping of contributed top-level summary fields;
- `session_list_order`, one order declaration or an ordered list.

One action failure is diagnosed and does not stop later sessions or actions.
An action requiring `session` cannot run when complete session content is
unavailable. Metadata-only summaries do not cause the service to execute
session-list actions speculatively.

List-trigger actions should be deterministic for a stored session and should
not mutate sessions as a side effect.

## Presentation fields

Application UI elements with `ui_type: "session_list_field"` declare a stable
field ID, role, dotted data path, optional template, order, and optional
formatting metadata.

Supported roles are `title`, `subtitle`, and `meta`. Fields are evaluated by
ascending order and declaration order.

- Title and subtitle use the first non-missing, non-null, non-empty rendered
  value.
- Meta renders every usable value and joins them with ` · `.
- `{{data}}` and `{{ data }}` substitute the resolved value once.
- `metadata.format: "datetime"` formats valid epoch or ISO values as UTC ISO
  timestamps and leaves invalid values unchanged.
- A missing title falls back to the preview, then to `Session ` plus the first
  eight session-ID characters.
- Missing subtitle and meta values are `None`.

Invalid declarations are ignored with structured diagnostics.

## Dotted-path resolution

Summary presentation, ordering, and filtering use one dotted-path resolver.
It:

- distinguishes a missing path from an explicit null value;
- traverses mappings by key;
- traverses lists and tuples by non-negative integer index;
- rejects empty paths, invalid indices, out-of-range indices, and traversal
  through unsupported values without raising to consumers.

## Ordering

The default order is descending numeric `modified`, treating a missing or
invalid value as zero.

List actions may contribute order declarations with:

- a non-empty dotted `key`;
- `direction` of `asc` or `desc`;
- optional `fallback`;
- integer `priority`, defaulting to `100`.

Lower priority values apply first. Plugin configuration order, action order,
and declaration order resolve ties. Stable sorting preserves the mtime
fallback beneath contributed ordering.

An order declaration is ignored with diagnostics when:

- its shape is invalid;
- any summary lacks the key and no fallback exists;
- values are not sortable;
- values mix incompatible sortable categories;
- the same plugin/action/declaration slot contributes conflicting contracts.

Equivalent repeated declarations in one slot are accepted.

When an implementation returns a mixture of complete and metadata-only
summaries, it first applies established ordering among complete summaries and
then appends metadata-only summaries in descending modification time. Once all
summaries are complete, established ordering applies to the whole collection.

## Filtering and limits

Session-list filters are declarative UI elements interpreted by the
application-owned filter engine. Supported filter types are text, boolean,
single select, and multiple select, with their existing typed matching,
defaults, missing-value, option, and main-search rules.

The list pipeline is:

1. derive summaries;
2. order summaries;
3. apply optional filters;
4. apply a non-negative limit.

Filtering preserves input order. Exact summary lookup is independent of list
filters.

If an active filter depends on data absent from a metadata-only summary, the
initial partial-resolution implementation retains that summary rather than
falsely concluding that the session does not match. A filter may reject the
summary only when available metadata conclusively fails the filter. Retained
unknown summaries remain in the metadata-only suffix. Later calls evaluate
the complete data once resolution succeeds.

Invalid filter declarations and runtime values produce diagnostics without
disabling unrelated valid filters.

### Date-filter refinement

The
[session and message data query specification](../../../../../../application/python/docs/development/specifications/session-data-query/index.md)
adds a `datetime` filter type with timezone-aware caller input and
`before`, `on_or_before`, `after`, and `on_or_after` matches.

Declarations continue to use plugin-owned IDs and dotted summary paths. A
datetime filter may target the built-in numeric `modified` epoch or an ISO
plugin-contributed value. Python and TypeScript evaluators normalize both
candidate forms to UTC instants and reject naive or invalid runtime values
with diagnostics. Existing text, boolean, and select behavior remains
unchanged.

Adapters pass caller values through the normalized schema and coercion path;
they do not hardcode a modified-date flag. Established ordering remains before
filter evaluation, and limits remain after filtering. JSONPath projection is
outside `SessionListService` and occurs after the ordinary result envelope is
serialized.

## Exact summary lookup

`get_session_summary(session_id)` validates a non-empty ID and performs exact
store-record lookup. A missing record raises `KeyError`. The method does not
apply collection filters.

A valid reusable complete summary may satisfy exact lookup. Otherwise exact
lookup retains existing complete-load and malformed-record fallback behavior.
The collection foreground budget does not change the exact-lookup contract.

## Summary validity and invalidation

A reusable complete summary is valid only when:

- it belongs to the same logical session-store namespace;
- its session ID matches;
- its stored revision equals the current opaque store revision;
- its summary-contract fingerprint matches;
- its persisted representation is compatible with the implementation.

The fingerprint covers inputs whose change can alter a summary, including
normalized list-trigger actions, presentation declarations, relevant plugin
identity or version, relevant implementation configuration, and derivation
schema version. Secret configuration values are not persisted in clear text.

Application-owned save and delete paths invalidate the affected session
through `SessionListService.invalidate()`. An implementation may update a
complete summary directly when the saved `Session` is already available.
External changes are detected through record revision comparison. A complete,
successful membership enumeration removes summaries for records confirmed
deleted; an interrupted enumeration does not imply deletion.

## Persistent reuse

The target preserves complete derived summaries across `AgentApplication`
instances so unchanged sessions do not require content reads after a restart.
Only complete summaries are persisted as reusable complete data;
metadata-only fallbacks are reconstructed from current records.

Persistence format, location, and backend are implementation details. A local
implementation should use user-private storage outside storage likely to
evict source session contents. A cloud implementation may use provider
metadata or a remote index and may not have a local cache root.

Persistent-state corruption or unavailability does not prevent listing.
Implementations rebuild safely or degrade to process-local state and
metadata-only summaries without changing source sessions.

## Initial bounded-resolution implementation

The initial implementation performs:

1. synchronous metadata-only membership enumeration;
2. validation and reuse of available complete summaries;
3. newest-first scheduling of new, changed, invalid, or uncached records;
4. bounded waiting for complete resolution;
5. complete-summary ordering followed by a metadata-only suffix;
6. continued private resolution after the caller returns.

The foreground clock starts only after metadata enumeration has established
the current record collection. The initial default is ten seconds. The
selected implementation may read an override from the opaque resolved
application context, but its key and validation are owned by that
implementation rather than a shared session-list configuration model.

Potentially blocking reads run outside the request thread. Expiration of the
foreground interval does not cancel owned work; completed summaries become
available to later calls. Concurrent list calls join or observe compatible
in-flight work instead of starting duplicate loads.

This scheduling model is replaceable. The stable contract does not require
future implementations to use a timeout, background threads, local
persistence, or metadata-only transitional work.

## Concurrency and lifecycle

An implementation that performs concurrent or background work:

- bounds its worker, queue, memory, and retry use;
- does not hold the service state lock during blocking reads or re-entrant
  application-plugin execution;
- publishes completed immutable summary records atomically;
- prevents superseded work from overwriting a newer revision or contract;
- serializes plugin enrichment unless the execution boundary is explicitly
  safe for concurrency;
- releases workers and persistent resources during `AgentApplication.close()`.

Runtime replacement remains governed by the application runtime reload
specification. This service owns the cleanup of resources it creates.

## Diagnostics and failure behavior

Diagnostics are structured, nonfatal records available from
`get_session_list_diagnostics()`. They identify invalid fields, actions,
ordering, filters, unavailable sessions, persistence recovery, and background
failures as applicable.

One action, declaration, cache entry, or session failure does not fail the
whole list. Operational logging may include session IDs, durations, cache
outcomes, counts, and queue depth. It does not include message content,
previews, credentials, complete summaries, or provider-native transcript
copies.

## Adapter contract

The HTTP adapter returns:

```json
{
  "sessions": []
}
```

and delegates optional `limit` to `AgentApplication`. Exact HTTP lookup wraps
one shared summary and maps a missing ID to `404`.

Terminal adapters use the same application methods and may supply in-process
filter state. No adapter scans the session root or independently runs
application-plugin list actions.

No client change is required for metadata-only summaries because they retain
the existing summary shape.

## Verification

Verification includes:

- deterministic summary, action, presentation, ordering, filter, limit,
  exact-lookup, invalidation, and malformed-record tests;
- store tests proving metadata enumeration is opaque and content-free;
- controlled delayed-load tests proving complete membership, metadata-only
  fallback, newest-first scheduling, and bounded foreground return;
- cross-application tests proving unchanged sessions avoid content reads;
- concurrency and application-close tests for private background resources;
- persistence corruption and unavailable-backend fallback tests;
- HTTP tests using the unchanged response envelope and production adapter;
- inspection confirming no client package changes.