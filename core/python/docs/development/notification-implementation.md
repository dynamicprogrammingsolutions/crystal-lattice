# Notification implementation

This page maps Core/Application Python code to the root notification
specification. Lifecycle and frontend semantics remain authoritative in the
root specification.

## Session notifications

`core/python/agent_app/notifications.py` implements normalized creation,
same-key update, update by ID/key, dismissal, resolution, expiration, listing,
revision conflicts, lifecycle transitions, locking, persistence, event
publication, and pruning.

The implementation:

- loads the live session record;
- acquires the application session lock;
- saves a new immutable `Session`;
- publishes lifecycle events and records a checkpoint;
- preserves notification metadata across request reconciliation.

## Application notifications

`core/python/agent_app/application_notifications.py` defines the
`ApplicationNotificationStore` contract plus in-memory and SQLite
implementations. The runtime creates one long-lived store and injects it into
every `AgentApplication` generation.

`AgentApplication` owns the public create/update/dismiss/resolve/expire/list
contract and publishes lifecycle events after durable mutation. Event
publication remains best effort. `ApplicationControl` coordinates reload only;
the owner creates reload notifications through the current application.

The terminal/server runtime resolves
`application.notifications.store.path`, opens the SQLite store before
constructing the owner, and closes it after the owner shuts down. The default
path is `application-notifications.sqlite3` beside the active config file.
Changing the configured path requires reconstructing the owning runtime; inner
application reloads continue using the already-open store.

The SQLite store preserves active and terminal records across
`AgentApplication` replacement and process restart. It applies the same
revision, active/terminal, stable-key, and terminal-transition rules as session
notifications.

New records start at integer revision `1`. Existing records without an integer
revision accept `updated_at` as a compatibility token and migrate on first
mutation.

## Tool boundary

`ApplicationContext.build_tool_context` installs a request/session-bound
`NotificationSink`. The sink catches notification failures so a malformed or
failed notification cannot abort tool execution.

## Verification

Primary tests:

- `core/python/tests/test_session_notifications.py`
- `core/python/tests/test_application_notifications.py`
- `core/python/tests/test_application_owner.py`
- `application/python/tests/test_notification_demo_plugins_http.py`

When modifying records or statuses, update the root `NTF-*` requirements first
and add focused persistence, event, pruning, and failure-containment tests.