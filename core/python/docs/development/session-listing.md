# Session-listing implementation

This page maps the current `agent_app` implementation to the
[application session-listing specification](specifications/session-listing/index.md).
It does not redefine that contract.

## Ownership

`agent_app/session_listing.py` owns:

- the `SessionListService` API used by `AgentApplication`;
- summary construction and fallback presentation;
- application-plugin `session_list` trigger execution;
- ordering, filtering integration, limits, and diagnostics;
- private foreground/background resolution coordination.

`agent_app/_session_list_cache.py` owns the current local persistent derived
summary store. `agent_app/sessions.py` owns opaque session-store records and
full session serialization.

`AgentApplication` supplies callbacks and opaque context, delegates session
queries to the service, invalidates summaries after saves and deletes, and
shuts the service down before application plugins close.

Terminal and HTTP packages remain adapters. They do not scan session storage.

## Resolution flow

For an unlimited unfiltered list, the service:

1. loads current action and presentation declarations;
2. enumerates live session records using identities and file attributes only;
3. validates process-local and persistent complete summaries;
4. schedules remaining records by descending modification time;
5. waits up to the current implementation's foreground interval;
6. orders complete summaries with existing plugin rules;
7. appends unresolved metadata-only summaries by descending modification time;
8. applies filters and the optional limit;
9. leaves unresolved work with the private background resolver.

The foreground interval begins after record enumeration. Blocking content reads
run on bounded daemon workers. Concurrent list calls share compatible work.

Metadata-only summaries use empty preview and metadata values and derive normal
presentation, including the established ID-based title fallback. They do not
run session-list actions.

Exact summary lookup remains independent of list filters and is not governed
by the collection foreground interval.

## Persistent derived summaries

The current implementation stores complete summaries in a private SQLite
database selected from a hash of the canonical session root. Each row includes
the opaque revision fingerprint, summary-contract fingerprint, complete
summary, normalized order declarations, and diagnostics.

The default cache directory is `~/.crystal/cache/session-list`. A configured
local cache directory can place this state elsewhere. Ephemeral session roots
under the operating system temporary directory keep their derived cache beside
that temporary root so tests and temporary applications clean it up together.

Operation-scoped SQLite connections permit concurrent readers and writers.
The database uses WAL mode and user-private file permissions. An incompatible
schema is rebuilt. A corrupt database is moved aside and rebuilt; an
unavailable cache degrades to process-local resolution.

Only summaries whose record revision and contract fingerprint match are
reused. The contract fingerprint includes:

- summary derivation version;
- action and presentation declarations;
- resolved application configuration;
- application-plugin identities and versions.

Source sessions remain authoritative. Persistent derived state can be deleted
without losing a session.

## Concurrency and shutdown

The resolver associates work with session ID, revision fingerprint, contract
fingerprint, and an invalidation epoch. Completion is published only if all
four still match, preventing obsolete work from replacing a newer result.

Session-list plugin enrichment is serialized independently from resolver state
locks. No service state lock is held during a content read or plugin call.

Shutdown:

- prevents new work;
- invalidates desired results;
- cancels queued work cooperatively;
- prevents a blocked read from executing plugin enrichment or publishing after
  it eventually returns;
- closes persistent cache use.

Worker threads are daemon threads because Python cannot cancel an operating
system file read that is already blocked.

## Primary verification

- `core/python/tests/test_application_session_listing.py`
- `core/python/tests/test_application_session_filters.py`
- `core/python/tests/test_session_list_cache.py`
- `application/python/tests/test_session_list_http_contract.py`
- focused terminal/server delegation tests in
  `application/python/tests/test_agent_terminal_app_server.py`

The delayed test stores exercise bounded foreground return, newest-first work,
metadata-only results, shared concurrent work, background completion, and
shutdown without relying on iCloud.