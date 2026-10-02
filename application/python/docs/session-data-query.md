# Query sessions and messages

Crystal Lattice can enumerate plugin-filtered session summaries and retrieve
canonical message ranges without downloading every available field. Python,
the one-shot CLI, HTTP, and the frontend SDK share the same session filters and
RFC 9535 JSONPath include/exclude behavior.

Use JSON when exact structure matters. Use text, TSV, or CSV when a human or a
line-oriented shell tool needs a concise result.

## Python

Keep one runtime open when inspecting several sessions:

```python
from datetime import datetime, timedelta, timezone

from agent_terminal_app import open_runtime


cutoff = (datetime.now(timezone.utc) - timedelta(days=14)).isoformat()

with open_runtime() as runtime:
    sessions = runtime.list_sessions(
        filter_values={"modified_after": cutoff},
        include=["$.sessions[*].session_id"],
    )
    for item in sessions["sessions"]:
        messages = runtime.list_messages(
            item["session_id"],
            include=[
                "$.messages[*].index",
                "$.messages[*].message.role",
                "$.messages[*].message.content",
                "$.messages[*].message.metadata.reasoning",
            ],
            exclude=['$.messages[?(@.message.role == "tool")]'],
        )
        print(item["session_id"], messages)
```

`runtime.list_sessions(...)` applies plugin filter defaults unless
`apply_filter_defaults=False` is supplied. `runtime.list_messages(...)`
accepts Python-style `start` and `end` bounds, including negative values.

If neither `include` nor `exclude` is supplied, both methods return the
complete current envelope.

## Command line

List every session ID:

```bash
crystal-lattice sessions \
  --include '$.sessions[*].session_id' \
  --format text
```

When session IDs are the only selected value, text output contains exactly one
undecorated ID per line:

```text
01abc
02xyz
03def
```

Filter IDs come from active application plugins. The default timestamp
metadata plugin provides `modified_after`, whose value must be a
timezone-bearing ISO-8601 datetime:

```bash
crystal-lattice sessions \
  --filter modified_after=2026-09-01T00:00:00Z \
  --include '$.sessions[*].session_id' \
  --format text
```

Plugin defaults apply unless `--no-filter-defaults` is supplied. Repeat
`--filter` for multiple filters. Active filters combine with AND; paths inside
one filter combine with OR.

Read selected fields from one session:

```bash
crystal-lattice messages \
  --session 01abc \
  --include '$.messages[*].index' \
  --include '$.messages[*].message.role' \
  --include '$.messages[*].message.content' \
  --include '$.messages[*].message.metadata.reasoning' \
  --exclude '$.messages[?(@.message.role == "tool")]' \
  --format text
```

Example:

```text
01abc [12] assistant content: Crystal Lattice supports local runtimes.
01abc [12] assistant metadata.reasoning: Check the active configuration.
```

The initial command intentionally retrieves one session at a time. Chain it
with `sessions` for broad searches:

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

For large collections, use the Python API to avoid opening the runtime once per
session.

## JSON output

Use `--format json` for the exact projected document:

```json
{
  "messages": [
    {
      "index": 12,
      "message": {
        "role": "assistant",
        "content": "Crystal Lattice supports local runtimes.",
        "metadata": {
          "reasoning": "Check the active configuration."
        }
      }
    }
  ]
}
```

JSON adds no implicit identity fields. Select `index`, `role`, or
`session_id` when the result needs them.

Text output uses the command's session ID and any selected index/role as
context. TSV and CSV use:

```text
session_id,index,role,path,value
```

Session rows use `session_id,path,value`. Textual whitespace is collapsed and
record separators are escaped or normalized so each selected value occupies
one physical line. Arrays and objects use compact JSON in the `value` column.
Use JSON rather than a line format when exact multiline values are required.

## JSONPath projection

Selectors use RFC 9535 JSONPath:

- repeated includes form a union;
- ancestors needed to preserve JSON structure are retained;
- selectors are evaluated against the original complete document;
- excludes are applied after inclusion and win;
- excluding an array element removes it rather than leaving a `null`
  placeholder;
- retained message indices keep their canonical values;
- a valid selector matching nothing succeeds;
- invalid syntax is a Python value error, HTTP `400`, or CLI exit `2`.

Because exclusions inspect the original document, this works even though role
is not included:

```text
--include '$.messages[*].message.content'
--exclude '$.messages[?(@.message.role == "tool")]'
```

Roles are ordinary data, not a closed enum. Selectors can condition on future
roles or metadata:

```text
$.messages[?(@.message.metadata.kind == "custom-event")]
```

JSONPath is used for structural selection. Perform free-text matching in the
caller; implementation-specific regex/search extensions are not part of this
contract.

## Session summary fields

Every complete summary has:

| Field | Meaning |
|---|---|
| `session_id` | Opaque persisted session identity |
| `modified` | Storage modification time in Unix epoch seconds |
| `preview` | Whitespace-normalized first user-message preview |
| `metadata` | Session metadata except provider-native transcript copies |
| `presentation.title` | Application-derived display title |
| `presentation.subtitle` | Optional application-derived subtitle |
| `presentation.meta` | Optional application-derived metadata line |

Application plugins may contribute additional top-level fields. A
metadata-only summary returned while content is resolving has the same base
shape but may have empty content-derived values.

## Message fields

`messages` contains indexed canonical entries:

```json
{
  "index": 12,
  "message": {
    "role": "assistant",
    "content": "Answer",
    "metadata": {},
    "multipartContent": [],
    "toolResult": {}
  }
}
```

`index` is the canonical session position. `role` is an arbitrary string.
`content` is the canonical JSON value. `metadata`, `multipartContent`, and
`toolResult` are optional and retain their existing omission rules. Provider
extensions normally expose reasoning under `metadata.reasoning`.

The complete HTTP message envelope may also contain:

| Field | Meaning |
|---|---|
| `cursor_event_id` | Event cursor matching the returned checkpoint |
| `active_request_id` | Current request identity when one is active |
| `readonly` | Whether a selected snapshot makes this view readonly |
| `snapshot_id` | Selected snapshot identity, or `null` |

## HTTP

Existing endpoints accept repeated query parameters:

```text
GET /sessions
GET /sessions/{session_id}/messages
```

Session parameters:

- `filter=<id>=<value>` (repeatable);
- `apply_filter_defaults=true|false`;
- `limit=<count>`;
- `include=<jsonpath>` and `exclude=<jsonpath>` (repeatable).

Message parameters:

- `start=<index>` and `end=<index>`;
- `include=<jsonpath>` and `exclude=<jsonpath>` (repeatable).

Use URL encoding rather than interpolating JSONPath manually:

```bash
curl --get http://127.0.0.1:8000/sessions \
  --data-urlencode 'filter=modified_after=2026-09-01T00:00:00Z' \
  --data-urlencode 'include=$.sessions[*].session_id'
```

No new parameter means the existing complete response is unchanged.

## Bounds and security

One projected request accepts at most 64 selectors, 4,096 characters per
selector, 100,000 matched nodes, and 20,000,000 serialized JSON characters.
A session query accepts at most 64 plugin filter assignments and 4,096
characters per assignment. Line output accepts at most 100,000 rows and 16,384
characters per rendered value. Narrow the range or projection when a bound is
reached.

Projection reduces transferred data; it is not authorization. A caller can
select only data that the unprojected operation already permits it to read.