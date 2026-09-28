# Application session-listing product specification

## Purpose

Applications need one authoritative session collection that can be consumed
through Python, terminal, and HTTP boundaries. The collection must retain
plugin-contributed presentation, ordering, and filtering behavior without
requiring each adapter to understand session persistence.

Session files can be large or backed by storage that materializes content only
when opened. Building every summary from complete session content on each new
application runtime can therefore delay the whole collection for minutes even
though session identifiers and file attributes are already available.

The target preserves the established session-list contract while allowing the
service to reuse complete summaries across runtimes. When complete summaries
cannot all be resolved during the implementation's foreground budget, every
discovered session remains visible through the normal summary shape and later
requests naturally observe completed background work.

## Users

Application users need:

- stored sessions to remain discoverable when older files are slow to open;
- the newest useful session details to become available first;
- stable list ordering, titles, previews, metadata, filters, and limits;
- one malformed or unavailable session not to prevent other sessions from
  appearing;
- subsequent application starts not to reread every unchanged transcript.

Developers using `AgentApplication` need:

- one shared list and exact-summary API across adapters;
- deterministic summary and presentation shapes;
- plugin-contributed fields and ordering to compose predictably;
- structured diagnostics for invalid contributions and unreadable sessions;
- session-store implementations to expose opaque records rather than paths;
- storage and resolution mechanisms to remain replaceable without changing
  the public session-list API.

Server maintainers need:

- blocking storage reads isolated from request and UI threads;
- bounded background work and clean application shutdown;
- persistent derived data that cannot corrupt source sessions;
- implementation-specific configuration to remain owned by the selected
  implementation rather than a shared session-list configuration model.

## Existing experience

`AgentApplication.list_session_summaries()` returns an ordered collection of
shared summaries. Each summary contains:

- an opaque session ID;
- storage modification time;
- a preview from the first non-empty user message;
- session metadata excluding provider-native transcript copies;
- application-plugin contributed fields;
- application-derived title, subtitle, and meta presentation.

Application plugins can contribute list fields and ordering through
`trigger: "session_list"` actions. Declarative filters operate on the ordered
summaries, and a limit applies after filtering. Exact summary lookup is
independent of list filters. Invalid actions, fields, order declarations, and
individual stored sessions produce diagnostics without failing the complete
request.

The current process-local summary cache avoids repeated loads within one
application instance, but a new runtime rebuilds every summary from session
content.

## Target experience

On a runtime with reusable complete summaries:

1. The service enumerates live session identities and attributes.
2. Unchanged complete summaries are reused without opening session content.
3. New or changed sessions are resolved from newest to oldest.
4. The response preserves the established summary contract.

On a cold runtime backed by slow or on-demand storage:

1. The service first enumerates session filenames and attributes without
   opening session contents.
2. Full resolution begins with the most recently modified sessions.
3. The implementation waits for full results only for its configured
   foreground interval, which defaults to ten seconds for the initial
   implementation.
4. Fully resolved summaries appear first.
5. Every remaining discovered session appears in the same response using a
   metadata-only summary with empty content-derived values and normal
   presentation fallbacks.
6. Resolution continues privately after the response.
7. Later list calls reuse the summaries completed in the foreground or
   background.

No client-specific scan state or polling protocol is required.

## Acceptance examples

### Reusing unchanged sessions

Given a previous application runtime derived complete summaries for stored
sessions, a new runtime lists unchanged sessions without opening their complete
session content.

### Returning a complete membership set

Given fifty discovered session records and storage that resolves only twelve
complete sessions during the foreground interval, an unfiltered unlimited
request returns fifty entries. The twelve complete summaries appear before
thirty-eight metadata-only summaries.

### Prioritizing recent work

Given uncached sessions with different modification times, full resolution is
attempted from newest to oldest. A slow older session does not prevent an
already completed newer summary from being returned.

### Isolating unavailable content

Given one malformed or temporarily unavailable session, the list still
contains that session using fallback summary values and returns complete
summaries for unaffected sessions. Diagnostics identify the failed session
without exposing its content.

### Preserving application-plugin behavior

Given complete summaries and valid list-trigger contributions, application
plugin fields, ordering, presentation, filters, and limits retain their
established results.

## Goals

- Preserve the public `SessionListService` and `AgentApplication` list
  interfaces.
- Preserve existing complete-summary, plugin, ordering, presentation, filter,
  limit, exact-lookup, and diagnostic behavior.
- Return every metadata-discovered session from an unfiltered unlimited list.
- Avoid opening unchanged session content across application runtimes.
- Bound foreground full-content resolution after metadata enumeration.
- Continue unresolved work without requiring client changes.
- Keep persistence, scheduling, timeout, and storage-backend choices private
  and replaceable.
- Release implementation-owned resources during application close and reload.

## Non-goals

- A new frontend loading, polling, progress, or scan-status protocol.
- Client package changes.
- A public cache, scanner, future, generation, or placeholder-state API.
- A shared configuration model for local cache paths, worker counts, or scan
  timeouts.
- A hard deadline for discovering filenames when storage blocks metadata
  enumeration.
- Changing the session JSON format.
- Changing session snapshot behavior.
- Requiring every future session-list implementation to use local files,
  SQLite, background threads, or a foreground timeout.