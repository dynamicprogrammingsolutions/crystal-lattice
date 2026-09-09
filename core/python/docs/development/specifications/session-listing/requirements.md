# Application session-listing requirements

These requirements track the live state relative to the
[application session-listing specification](index.md).

The preserved groups describe behavior that existed before persistent,
deadline-bounded session listing. The new groups describe behavior introduced
by that correction. Functional requirements define results observed by
application users or developers consuming the application API.
Non-functional requirements constrain compatibility, reliability,
performance, encapsulation, concurrency, privacy, and maintainability.

## Preserved requirements

### Functional requirements

| ID | Requirement | Implementation | Verification | Documentation |
|---|---|---|---|---|
| SLIST-001 | `AgentApplication` provides one shared ordered session-summary collection, exact unfiltered summary lookup, structured diagnostics, filter schema access, and filter-evaluator installation through `SessionListService`. | Implemented | Automated | Documented |
| SLIST-002 | Session stores expose opaque live-session records with identity, modification time, and equality-comparable revision, and support collection and exact-record lookup without exposing storage paths. | Implemented | Automated | Not applicable |
| SLIST-003 | A complete summary contains record identity and modification time, a normalized first-user-message preview, session metadata excluding `native_messages`, contributed fields, and stable title/subtitle/meta presentation. | Implemented | Automated | Documented |
| SLIST-004 | Valid `session_list` application actions execute in plugin and declaration order with only declared inputs and application lifecycle context, may contribute JSON-serializable non-reserved fields and ordering, and fail independently with diagnostics. | Implemented | Automated | Documented |
| SLIST-005 | Session-list ordering defaults to descending modification time and composes valid contributed order declarations deterministically while ignoring invalid, incomplete, incompatible, or conflicting declarations with diagnostics. | Implemented | Automated | Documented |
| SLIST-006 | Presentation fields resolve dotted summary paths, apply deterministic role/order/template/datetime rules, and fall back from title fields to preview and then an ID-derived title. | Implemented | Automated | Documented |
| SLIST-007 | Declarative filters preserve ordered input, combine paths and active filters according to their typed contract, report invalid declarations and values without losing unrelated filters, run before limits, and do not affect exact lookup. | Implemented | Automated | Documented |
| SLIST-010 | HTTP and terminal adapters delegate session listing and exact lookup to `AgentApplication`; HTTP preserves the `{"sessions": [...]}` envelope and maps missing exact IDs to `404`. | Implemented | Automated | Documented |

### Non-functional requirements

| ID | Requirement | Implementation | Verification | Documentation |
|---|---|---|---|---|
| SLIST-008 | An unreadable or malformed stored session and an invalid plugin contribution do not fail the collection; the service returns safe fallback summary values and structured diagnostics. | Implemented | Automated | Documented |
| SLIST-009 | Within one application instance, complete summaries are reused only while record revision and list contract token match; saves, deletes, external changes, and missing records invalidate stale results. | Implemented | Automated | Not applicable |

## New requirements

### Functional requirements

| ID | Requirement | Implementation | Verification | Documentation |
|---|---|---|---|---|
| SLIST-012 | Metadata enumeration establishes current session membership from identities and attributes without opening session content before the initial implementation's foreground full-resolution interval starts. | Implemented | Automated | Documented |
| SLIST-013 | An unfiltered unlimited list returns one ordinary summary-shaped entry for every metadata-discovered session; unresolved entries use content-free fallback values and normal presentation without exposing implementation state. | Implemented | Automated | Documented |
| SLIST-014 | Complete summaries remain reusable across application runtimes, and unchanged records with compatible revisions and summary-contract fingerprints do not require session-content reads. | Implemented | Automated | Documented |
| SLIST-015 | The initial implementation attempts required full resolutions in descending modification time, waits no longer than its privately configured foreground interval after enumeration, and continues unfinished work for later calls without requiring client changes. | Implemented | Automated | Documented |
| SLIST-016 | While unresolved entries remain, complete summaries use established ordering and precede metadata-only summaries ordered by descending modification time; filters conservatively retain entries whose unavailable data prevents a conclusive decision, and limits remain last. | Implemented | Automated | Documented |
| SLIST-019 | Application-owned saves and deletes and externally observed revisions converge persistent and in-memory summaries without allowing obsolete work to overwrite a newer record or contract. | Implemented | Automated | Documented |

### Non-functional requirements

| ID | Requirement | Implementation | Verification | Documentation |
|---|---|---|---|---|
| SLIST-011 | `SessionListService` retains its existing public method signatures and return types while selected implementations receive opaque application context and keep cache, deadline, worker, scan, placeholder-state, and storage-backend concepts out of the public surface and shared configuration model. | Implemented | Automated | Documented |
| SLIST-017 | Concurrent calls share compatible in-flight work; background resource use and retries are bounded; blocking reads do not hold the service lock or request event loop; and application close or reload releases implementation-owned resources. | Implemented | Automated | Documented |
| SLIST-018 | Persistent derived state is private, transactional, bounded, and recoverable; corruption or unavailability degrades safely without changing source sessions, and diagnostics and logs do not expose session content or credentials. | Implemented | Automated | Documented |
| SLIST-020 | The server delivers the target through existing application and HTTP contracts without changes to mobile, desktop, frontend SDK, or other client packages. | Implemented | Automated | Documented |

## Evidence

### Preserved functional requirements

- **SLIST-001:** [agent_app/application_future.py](../../../../agent_app/application_future.py),
  [agent_app/session_listing.py](../../../../agent_app/session_listing.py),
  [tests/test_application_session_listing.py](../../../../tests/test_application_session_listing.py),
  and [plugins/docs/application-plugins.md](../../../../../../plugins/docs/application-plugins.md).
- **SLIST-002:** [agent_app/sessions.py](../../../../agent_app/sessions.py) and
  [tests/test_application_session_listing.py](../../../../tests/test_application_session_listing.py).
- **SLIST-003:** [agent_app/session_listing.py](../../../../agent_app/session_listing.py),
  [tests/test_application_session_listing.py](../../../../tests/test_application_session_listing.py),
  [application/python/tests/test_session_list_http_contract.py](../../../../../../application/python/tests/test_session_list_http_contract.py),
  and [plugins/docs/application-plugins.md](../../../../../../plugins/docs/application-plugins.md).
- **SLIST-004:** [agent_app/session_listing.py](../../../../agent_app/session_listing.py),
  [tests/fixtures/session_listing_app_plugin.py](../../../../tests/fixtures/session_listing_app_plugin.py),
  [tests/test_application_session_listing.py](../../../../tests/test_application_session_listing.py),
  and [plugins/docs/actions.md](../../../../../../plugins/docs/actions.md).
- **SLIST-005:** [agent_app/session_listing.py](../../../../agent_app/session_listing.py),
  [tests/test_application_session_listing.py](../../../../tests/test_application_session_listing.py),
  [application/python/tests/test_session_list_http_contract.py](../../../../../../application/python/tests/test_session_list_http_contract.py),
  and [plugins/docs/actions.md](../../../../../../plugins/docs/actions.md).
- **SLIST-006:** [agent_app/session_listing.py](../../../../agent_app/session_listing.py),
  [tests/test_application_session_listing.py](../../../../tests/test_application_session_listing.py),
  [test/fixture/session-list/v1/contract-cases.json](../../../../../../test/fixture/session-list/v1/contract-cases.json),
  and [plugins/docs/ui-elements.md](../../../../../../plugins/docs/ui-elements.md).
- **SLIST-007:** [agent_app/session_filters.py](../../../../agent_app/session_filters.py),
  [tests/test_application_session_filters.py](../../../../tests/test_application_session_filters.py),
  [tests/test_application_session_listing.py](../../../../tests/test_application_session_listing.py),
  [application/python/tests/test_session_list_http_contract.py](../../../../../../application/python/tests/test_session_list_http_contract.py),
  and [plugins/docs/ui-elements.md](../../../../../../plugins/docs/ui-elements.md).
- **SLIST-010:** [application/python/agent_terminal_app/server.py](../../../../../../application/python/agent_terminal_app/server.py),
  [application/python/agent_terminal_app/terminal_app.py](../../../../../../application/python/agent_terminal_app/terminal_app.py),
  [application/python/tests/test_session_list_http_contract.py](../../../../../../application/python/tests/test_session_list_http_contract.py),
  and [application/python/tests/test_agent_terminal_app_server.py](../../../../../../application/python/tests/test_agent_terminal_app_server.py).

### Preserved non-functional requirements

- **SLIST-008:** [agent_app/session_listing.py](../../../../agent_app/session_listing.py),
  [tests/test_application_session_listing.py](../../../../tests/test_application_session_listing.py),
  [application/python/tests/test_session_list_http_contract.py](../../../../../../application/python/tests/test_session_list_http_contract.py),
  and [plugins/docs/actions.md](../../../../../../plugins/docs/actions.md).
- **SLIST-009:** [agent_app/session_listing.py](../../../../agent_app/session_listing.py),
  [agent_app/application_future.py](../../../../agent_app/application_future.py),
  and [tests/test_application_session_listing.py](../../../../tests/test_application_session_listing.py).

### New functional requirements

- **SLIST-012:** [agent_app/sessions.py](../../../../agent_app/sessions.py),
  [agent_app/session_listing.py](../../../../agent_app/session_listing.py),
  [tests/test_application_session_listing.py](../../../../tests/test_application_session_listing.py),
  and [docs/development/session-listing.md](../../session-listing.md).
- **SLIST-013:** [agent_app/session_listing.py](../../../../agent_app/session_listing.py),
  [tests/test_application_session_listing.py](../../../../tests/test_application_session_listing.py),
  [application/python/tests/test_session_list_http_contract.py](../../../../../../application/python/tests/test_session_list_http_contract.py),
  and [application/python/docs/configuration.md](../../../../../../application/python/docs/configuration.md).
- **SLIST-014:** [agent_app/_session_list_cache.py](../../../../agent_app/_session_list_cache.py),
  [tests/test_application_session_listing.py](../../../../tests/test_application_session_listing.py),
  [tests/test_session_list_cache.py](../../../../tests/test_session_list_cache.py),
  and [docs/development/session-listing.md](../../session-listing.md).
- **SLIST-015:** [agent_app/session_listing.py](../../../../agent_app/session_listing.py),
  [tests/test_application_session_listing.py](../../../../tests/test_application_session_listing.py),
  [application/python/tests/test_session_list_http_contract.py](../../../../../../application/python/tests/test_session_list_http_contract.py),
  and [application/python/docs/configuration.md](../../../../../../application/python/docs/configuration.md).
- **SLIST-016:** [agent_app/session_listing.py](../../../../agent_app/session_listing.py),
  [agent_app/session_filters.py](../../../../agent_app/session_filters.py),
  [tests/test_application_session_listing.py](../../../../tests/test_application_session_listing.py),
  and [technical-spec.md](technical-spec.md).
- **SLIST-019:** [agent_app/session_listing.py](../../../../agent_app/session_listing.py),
  [agent_app/application_future.py](../../../../agent_app/application_future.py),
  [tests/test_application_session_listing.py](../../../../tests/test_application_session_listing.py),
  and [docs/development/session-listing.md](../../session-listing.md).

### New non-functional requirements

- **SLIST-011:** [agent_app/session_listing.py](../../../../agent_app/session_listing.py),
  [agent_app/application_future.py](../../../../agent_app/application_future.py),
  [tests/test_application_session_listing.py](../../../../tests/test_application_session_listing.py),
  and [decisions/001-service-boundary-and-implementation-independence.md](decisions/001-service-boundary-and-implementation-independence.md).
- **SLIST-017:** [agent_app/session_listing.py](../../../../agent_app/session_listing.py),
  [agent_app/application_future.py](../../../../agent_app/application_future.py),
  [tests/test_application_session_listing.py](../../../../tests/test_application_session_listing.py),
  and [docs/development/session-listing.md](../../session-listing.md).
- **SLIST-018:** [agent_app/_session_list_cache.py](../../../../agent_app/_session_list_cache.py),
  [tests/test_session_list_cache.py](../../../../tests/test_session_list_cache.py),
  [docs/development/session-listing.md](../../session-listing.md),
  and [application/python/docs/configuration.md](../../../../../../application/python/docs/configuration.md).
- **SLIST-020:** [application/python/tests/test_session_list_http_contract.py](../../../../../../application/python/tests/test_session_list_http_contract.py),
  [application/python/agent_terminal_app/server.py](../../../../../../application/python/agent_terminal_app/server.py),
  and [tasks/20260902-session-list-caching.md](../../../../../../tasks/20260902-session-list-caching.md).