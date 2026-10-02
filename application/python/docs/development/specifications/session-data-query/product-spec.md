# Session and message data query product specification

## Purpose

Agents, shell users, and frontends need to inspect persisted Crystal Lattice
sessions without always downloading every message field and every tool result.
They also need enough low-level flexibility to perform searches that the
product has not anticipated.

The target provides session enumeration, per-session canonical message
ranges, plugin-driven session prefiltering, and generic JSONPath projection.
It does not encode fixed searches, message roles, or named projection presets.

## Users

### Shell users and configured agents

These users need to:

- enumerate matching session IDs as one value per line;
- reuse plugin-defined filters such as a modified-after date;
- retrieve one session's selected message fields;
- omit tool messages or other types using data-driven conditions;
- inspect human-readable output or pipe it through `grep`;
- switch to JSON when exact structure matters.

### Python callers

These users need to:

- list the same summaries used by the application;
- use the same plugin filter schema and defaults;
- retrieve full or projected canonical message ranges;
- preserve canonical indices while performing arbitrary local analysis;
- avoid opening a new application runtime for each session.

### Frontend and SDK callers

These users need to:

- preserve today's complete responses when they request no projection;
- request only visible fields such as content and reasoning;
- defer large tool-call, tool-result, multipart, attachment, or metadata
  subtrees until a user expands them;
- apply the same plugin-declared filters as the current client-side
  implementation;
- distinguish partial projected data from complete canonical messages.

### Plugin authors

These users need to:

- continue defining session-list filters through `session_list_filter`;
- declare date inputs and comparisons without implementing adapter-specific
  filtering;
- target built-in or plugin-contributed summary fields;
- have equivalent Python and TypeScript interpretation.

## Current experience

Current behavior provides:

- complete session summaries from `AgentApplication` and `GET /sessions`;
- client-side plugin-driven text, boolean, and select filters;
- complete canonical ranges from `GET /sessions/{id}/messages`;
- fixed compact history plus one-message full retrieval in the local Python
  runtime and one-shot CLI.

It does not provide:

- one-shot `sessions` or full-range `messages` CLI commands;
- a local-runtime session-list method;
- JSONPath include/exclude projection;
- HTTP plugin filter values;
- declarative date comparison filters;
- partial projected frontend message types.

## Target experience

### Enumerate recent sessions

A plugin declares a date filter over the built-in `modified` field or a
plugin-contributed timestamp. The same filter ID is available to frontends,
Python callers, terminal consumers, HTTP callers, and the one-shot CLI.

```text
crystal-lattice sessions \
  --filter modified_after=2026-09-01T00:00:00Z \
  --include '$.sessions[*].session_id' \
  --format text
```

When the projection selects only session IDs, text output contains exactly one
ID per line:

```text
01abc
02xyz
03def
```

### Retrieve focused data from one session

```text
crystal-lattice messages \
  --session 01abc \
  --include '$.messages[*].index' \
  --include '$.messages[*].message.role' \
  --include '$.messages[*].message.content' \
  --include '$.messages[*].message.metadata.reasoning' \
  --exclude '$.messages[?(@.message.role == "tool")]' \
  --format json
```

Illustrative JSON result:

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

The same projection in text form is understandable and searchable:

```text
01abc [12] assistant content: Crystal Lattice supports local runtimes.
01abc [12] assistant metadata.reasoning: Check the active Crystal Lattice configuration.
```

### Chain low-level commands

The initial CLI does not need a multi-session messages command:

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

Large or latency-sensitive searches may keep one Python runtime open and
perform the same per-session operations without repeated CLI startup.

## Goals

- Preserve exact current responses when no include or exclude selector is
  supplied.
- Use standard JSONPath syntax with wildcard and filter selectors.
- Support both additive inclusion and subtractive exclusion.
- Let selectors condition behavior on any message or metadata field without a
  fixed role registry.
- Reuse plugin-defined session filters across every consumer.
- Add a timezone-safe date input and comparison contract.
- Keep the CLI composable through one-session commands and one-value-per-line
  enumeration.
- Offer lossless JSON and predictable line-oriented human formats.
- Let frontends defer heavy fields and hydrate them later.
- Document canonical, envelope, snapshot, and plugin-contributed fields well
  enough for callers to write their own selectors.

## Non-goals

- A server-side full-text search index or query language.
- Named projection presets.
- Fixed role-specific options such as `toolInclude` or `assistantInclude`.
- A closed registry of message roles.
- A multi-session messages CLI command in the initial target.
- Replacing compact history.
- Rewriting canonical session or message storage.
- Treating projection as authorization.
- Requiring implementation-specific JSONPath regex or text-search extensions.

## Acceptance examples

### No projection preserves compatibility

An existing HTTP or frontend call with no include or exclude selectors receives
the same complete envelope and canonical values as before the feature.

### Exclusion wins

Given selectors that include message content and exclude messages whose
current role is `tool`, no tool message appears even though its content also
matched the include selector.

### Future roles remain usable

Given a message with a role unknown to current code, wildcard selectors return
it and a caller may condition on its role or metadata without a schema update.

### Grep-friendly output

Given content or reasoning containing embedded whitespace, text and TSV output
emit each selected leaf on one physical line with stable context, allowing
ordinary case-insensitive `grep`.

### Date-filter parity

Given one plugin-declared modified-after filter and the same value, Python,
CLI, HTTP, and frontend evaluation select the same fully resolved summaries.