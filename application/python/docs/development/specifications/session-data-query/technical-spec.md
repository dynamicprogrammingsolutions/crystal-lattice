# Session and message data query technical specification

This is a target specification. Current user and implementation documentation
must not claim this behavior until the corresponding requirements are
implemented and verified.

## Ownership

`core/python/agent_app` owns:

- session-summary construction and plugin-driven filtering;
- canonical session/message loading;
- pure JSONPath projection over serialized response documents;
- deterministic projection diagnostics and bounds.

`application/python/agent_terminal_app` owns:

- local Python convenience methods;
- one-shot command parsing and rendering;
- HTTP query parameters and response mapping;
- stdout/stderr and exit behavior.

`packages/frontend-sdk` owns:

- REST query encoding;
- projected result types;
- frontend-facing lazy hydration helpers;
- TypeScript parity for plugin filter evaluation.

Application plugins continue to own filter declarations and contributed
summary fields. They do not implement CLI, HTTP, or frontend adapters.

## Canonical source documents

Projection operates only after current canonical serialization.

The session collection source document remains:

```json
{
  "sessions": [
    {
      "session_id": "01abc",
      "modified": 1789400000.0,
      "preview": "First user message",
      "metadata": {},
      "presentation": {
        "title": "Example",
        "subtitle": null,
        "meta": null
      }
    }
  ]
}
```

Plugin-contributed summary fields may appear beside the reserved fields.

The message collection source document remains:

```json
{
  "messages": [
    {
      "index": 12,
      "message": {
        "role": "assistant",
        "content": "Answer",
        "metadata": {
          "reasoning": "Reasoning"
        },
        "multipartContent": [],
        "toolResult": {}
      }
    }
  ],
  "cursor_event_id": "event-id",
  "active_request_id": null,
  "readonly": false,
  "snapshot_id": null
}
```

Optional canonical message fields retain their current omission rules.
Projection does not synthesize absent values or rename current fields.

## JSONPath contract

Selectors use RFC 9535 JSONPath notation. Conformance tests prove the supported
syntax and result ordering required here.

The initial implementation uses MIT-licensed `python-jsonpath` 2.x with
`JSONPathEnvironment(strict=True)`. It is pure Python across all supported
native targets and is tested upstream against the JSONPath compliance suite.
The stricter standalone package from the same maintainer was not selected
because one compiled transitive dependency lacks a Windows ARM64 wheel.

Request options are ordered sequences:

```python
include: Sequence[str] | None
exclude: Sequence[str] | None
```

The contract is:

1. When both options are absent, return the exact unprojected document.
2. Parse every selector before reading or transforming returned data.
3. Evaluate every include and exclude selector against the same original,
   unprojected document.
4. If include is absent, begin with the complete document.
5. If include is present, retain the union of matched nodes plus the ancestors
   required to preserve their JSON structure.
6. Remove the union of exclude matches after inclusion; exclusion wins.
7. Matching an object or array selects or removes its complete subtree.
8. Excluding an array element removes that element instead of leaving a null
   or empty positional placeholder.
9. When retained by the projection, an indexed message's canonical `index`
   value is unchanged; projected array position is never a replacement
   identity.
10. A valid selector matching no node is successful.
11. Invalid or unsupported syntax is an actionable Python value error, HTTP
    `400`, or CLI usage error with exit code `2`.

The implementation preserves source object order and array order. It does not
mutate canonical session objects or persist projected forms.

JSONPath is structural selection, not the target's text-search language.
Implementation-specific regex or `search()` extensions are not part of the
portable contract.

## Generic conditional projection

Filter selectors may use any current or future discriminator:

```text
$.messages[?(@.message.role == "tool")]
$.messages[?(@.message.metadata.kind == "custom-event")]
```

The API does not validate message role values against a fixed set. Conditional
include selectors may choose different fields for different data shapes:

```text
$.messages[?(@.message.role == "assistant")].message.content
$.messages[?(@.message.role == "assistant")].message.metadata.reasoning
$.messages[?(@.message.role == "user")].message.content
```

Selectors are evaluated against the original document, so an exclusion may
use a discriminator that is not present in the final included projection.

## Session filter contract

Session query filtering reuses normalized `session_list_filter` declarations.
CLI and HTTP adapters do not define filter IDs or data paths.

The target adds a `datetime` filter type with timezone-aware values and these
comparison matches:

- `before`;
- `on_or_before`;
- `after`;
- `on_or_after`.

A plugin declaration may target the built-in numeric `modified` epoch value or
an ISO-8601 plugin-contributed field:

```json
{
  "ui_type": "session_list_filter",
  "id": "modified_after",
  "label": "Modified after",
  "data": "modified",
  "type": "datetime",
  "match": "on_or_after"
}
```

Runtime values use timezone-bearing ISO-8601 text. Naive datetimes and invalid
candidate values produce diagnostics rather than locale-dependent comparison.
Python and TypeScript normalization compare UTC instants.

Multiple data paths within one filter remain alternatives. Active filters
remain conjunctive. Filtering remains conservative for metadata-only summaries
whose required data is unavailable.

The query pipeline is:

1. enumerate and resolve summaries under the session-listing contract;
2. enrich complete summaries through plugins;
3. apply established ordering;
4. apply plugin-declared filter defaults and caller values;
5. apply limit or pagination;
6. serialize the ordinary collection envelope;
7. apply JSONPath projection.

Exact summary lookup remains independent of collection filters.

## Python surface

The local runtime gains:

```python
runtime.list_sessions(
    *,
    filter_values: Mapping[str, object] | None = None,
    apply_filter_defaults: bool = True,
    limit: int | None = None,
    include: Sequence[str] | None = None,
    exclude: Sequence[str] | None = None,
) -> Mapping[str, Any]

runtime.list_messages(
    session_id: str,
    *,
    start: int | None = None,
    end: int | None = None,
    include: Sequence[str] | None = None,
    exclude: Sequence[str] | None = None,
) -> Mapping[str, Any]
```

The methods use the same active config, plugins, snapshots, session root, and
canonical serialization as existing application consumers. `history(...)` and
`get_message(...)` retain their compact/full contracts.

## CLI surface

### Sessions

```text
crystal-lattice [global options] sessions
  [--filter ID=VALUE ...]
  [--no-filter-defaults]
  [--limit COUNT]
  [--include JSONPATH ...]
  [--exclude JSONPATH ...]
  [--format text|json|tsv|csv]
```

Filter IDs and values are normalized through the active plugin schema.
Unknown IDs, duplicate assignments, and invalid values are usage errors.

When text projection selects only
`$.sessions[*].session_id`, stdout contains one ID per line with no header or
decoration.

### Messages

```text
crystal-lattice [global options] messages
  --session ID
  [--start INDEX]
  [--end INDEX]
  [--include JSONPATH ...]
  [--exclude JSONPATH ...]
  [--format text|json|tsv|csv]
```

The initial command accepts exactly one session. Users compose multi-session
searches by chaining `sessions` into repeated `messages` invocations. The
Python API remains the efficient option for keeping one runtime open.

JSON output is the projected response document. Text output emits each selected
leaf on one physical line:

```text
<session-id> [<canonical-index>] <role> <path>: <value>
```

TSV and CSV use these columns:

```text
session_id,index,role,path,value
```

Textual scalar whitespace is normalized or escaped so embedded newlines and
tabs do not create additional physical records. Non-scalar values use compact
JSON in the value field. CSV follows ordinary quoting rules while preserving
the one-physical-record guarantee; TSV escapes tabs, newlines, carriage
returns, and backslashes.

Normal output goes to stdout. Diagnostics go to stderr. JSON output remains
one parseable document.

## HTTP surface

Existing collection endpoints retain their routes and unprojected default
responses:

```text
GET /sessions
GET /sessions/{session_id}/messages
```

The target adds repeated query parameters:

```text
filter=<id>=<value>
include=<jsonpath>
exclude=<jsonpath>
apply_filter_defaults=true|false
```

Message range parameters remain `start` and `end`. Session `limit` remains
supported. The adapter delegates filter normalization and projection; it does
not implement either contract independently.

If URL length or transport interoperability proves inadequate during focused
implementation tests, a structured read-only query body is a material API
decision and returns to task approval rather than being introduced silently.

## Frontend SDK

The backend methods gain optional query arguments corresponding to the HTTP
contract. Calls without them remain source-compatible and receive complete
current types.

Calls with projections return explicit projected types whose canonical message
fields are optional or represented as JSON values. A projected response is not
cast to the complete `IndexedMessage` or `Message` contract.

Frontends may request visible fields first and fetch omitted subtrees later.
Cache identity includes session ID, range, snapshot identity or cursor, and the
ordered include/exclude selectors so a partial response cannot overwrite a
complete one.

The existing TypeScript session-filter evaluator gains datetime parity with
the Python evaluator. Existing client-side filtering remains available even
when server-side prefiltering is used.

## Compatibility

- Existing `GET /sessions` and message requests without new parameters are
  byte-shape compatible after ordinary JSON serialization.
- Existing frontend list and message methods without query options retain
  complete result types.
- Existing compact-history Python and CLI behavior remains unchanged.
- Existing text, boolean, and select session filters retain their semantics.
- Message roles remain ordinary data; no new role enum is introduced.
- Canonical storage and snapshot selection remain unchanged.

## Limits and safety

The implementation defines bounded defaults and hard maximums for:

- selector count and length;
- JSONPath parse complexity and recursive descent;
- returned sessions and messages;
- projected scalar and total output size;
- CLI line length before explicit truncation metadata or failure.

Projection is data minimization, not authorization. Callers may select only
fields they are already permitted to retrieve through the unprojected
endpoint. Diagnostics never echo credentials or unrestricted selected values.

## Verification

Verification must cover:

- RFC 9535 syntax and wildcard/filter conformance;
- include union, exclude precedence, ancestors, subtrees, arrays, missing
  matches, and canonical indices;
- no-selector compatibility at Python, real HTTP, CLI subprocess, and
  production frontend-adapter boundaries;
- Python/TypeScript filter parity, including timezone and metadata-only cases;
- JSON, text, TSV, and CSV exact output with escaping;
- the documented shell pipeline using plugin date filtering and `grep`;
- frontend partial hydration without cache corruption;
- invalid selector, filter, range, limit, and output-bound failures;
- source, archive, Bash-installed, and PowerShell-installed commands on
  applicable native targets.