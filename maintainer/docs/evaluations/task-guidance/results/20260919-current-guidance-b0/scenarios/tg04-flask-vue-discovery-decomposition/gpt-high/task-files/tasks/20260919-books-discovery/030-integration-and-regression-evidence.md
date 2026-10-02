# Books discovery integration and regression evidence

Verify the selected discovery behavior across the client/API boundary and
preserve the existing CRUD and unfiltered compatibility paths.

Parent Task: tasks/20260919-books-discovery/000-main.md
Depends On: tasks/20260919-books-discovery/010-server-discovery-contract.md, tasks/20260919-books-discovery/020-client-discovery-state.md

## Requirements checklist

- [ ] A realistic client-to-API test proves a filtered and paginated Books
      request crosses the production transport boundary.
- [ ] A realistic mutation refresh proves the current discovery query is
      retained after add, update, and delete behavior.
- [ ] Regression coverage proves unfiltered API consumers and existing CRUD
      behavior remain supported.
- [ ] The maintained documentation source, if any, describes the verified
      supported discovery and sharing behavior.
- [ ] The complete relevant client and server test suites collect and exit
      successfully.

## Supporting facts

- `client/tests/books.integration.js` is currently an explicit placeholder
  with no production transport integration coverage.
- `tests/test_books_api.py` covers only endpoint status codes and basic CRUD
  calls.
- The root README describes the application at a high level but does not
  document query parameters or URL state.

## Execution plan

Status: Draft

Add the smallest integration coverage that crosses the real client API module,
HTTP adapter, Flask route, and response consumption. Keep component tests
focused on local state/rendering while using the integration path for
transport/contract confidence. Run the full available client and server test
commands, inspect collection and exit status, and update the appropriate
maintained documentation only after behavior is verified.

### Implementation decisions and open questions

This subtask inherits the approved contracts and state policy from the parent
and the two implementation subtasks. It must not broaden the feature with
unrequested end-to-end infrastructure or a new documentation hierarchy.

### Documentation

Document only verified current behavior. If no existing maintained location
has a suitable audience, record that no documentation page was added rather
than creating a placeholder. Any target-only wording must be visibly marked
as not implemented until the feature is complete.

### Task checklist

- [ ] Confirm the implemented API and client contracts.
- [ ] Replace the transport placeholder with focused realistic integration
      evidence.
- [ ] Add or strengthen CRUD and unfiltered compatibility regressions.
- [ ] Run client and server test suites and record exact evidence.
- [ ] Update the maintained documentation source if applicable.
- [ ] Mark the parent requirements only when their evidence is complete.

### Requirement verification

The integration test must use the production request path and a real Flask
response, proving that query parameters selected by the page result in the
expected filtered page and metadata. Separate regression tests must prove
that an unparameterized list request and POST/PUT/DELETE still work.

### Additional implementation verification

- Verify the test harness itself is consumed by a real integration test.
- Check that documentation claims match the final parameter names and URL
  behavior rather than the earlier draft recommendations.
- Report any gated or environment-dependent tests that could not run instead
  of treating them as successful.