# Verify and document the complete notes-query capability

Reconcile evidence across the API, reusable client, and CLI, then finalize
maintained documentation for the supported behavior.

Parent Task: tasks/20260919-notes-query/000-main.md
Depends On: tasks/20260919-notes-query/020-api-query.md
Depends On: tasks/20260919-notes-query/030-client-query.md
Depends On: tasks/20260919-notes-query/040-cli-query.md

## Requirements checklist

- [ ] Run the focused API, client, and CLI suites with their real required
      boundaries enabled.
- [ ] Confirm all three consumers use the same approved parameter names and
      semantics.
- [ ] Confirm unparameterized API, client, and CLI behavior remains compatible.
- [ ] Confirm CLI evidence crosses the production client and HTTP service
      boundary.
- [ ] Reconcile maintained documentation with only verified current behavior.
- [ ] Record remaining gaps or deferred contract decisions instead of silently
      expanding scope.

## Supporting facts

The current tests are split across `src/tests`, `packages/notes_client/tests`,
and `apps/notes_cli/tests`. API and client tests currently cover only basic
unparameterized behavior, while the CLI test uses a fake client. The package
READMEs and development index are the maintained documentation surfaces
identified during planning.

## Execution plan

Status: Draft

1. Review each completed subtask against the approved contract and compare
   parameter names, defaults, bounds, response shape, sorting, filtering, and
   errors.
2. Run the smallest focused suites first, then the cross-boundary CLI
   integration test with the service lifecycle enabled.
3. Inspect the final documentation for current-behavior claims, examples, and
   explicit compatibility guidance.
4. Record evidence in the parent task and leave any unresolved requirement
   question or blocked gate visible.

### Implementation decisions and open questions

- Decision: this subtask owns evidence reconciliation, not new query
  semantics; inconsistencies return to the contract task.
- Open: test command names and service fixture details should follow the
  repository’s available tooling once implementation begins.

### Documentation

Review the contract page, API/development documentation,
`packages/notes_client/README.md`, and `apps/notes_cli/README.md` together.
Remove or mark target-only claims that are not implemented. Keep the
specification and current user guidance distinguishable if implementation is
still staged.

### Task checklist

- [ ] Reconcile cross-consumer contract conformance.
- [ ] Run focused and integration verification.
- [ ] Review and correct maintained documentation.
- [ ] Update parent requirement evidence and status.

### Requirement verification

- One matrix or equivalent evidence record maps each contract capability to
  the API, client, and CLI boundary.
- Compatibility is verified independently at each public boundary.
- The CLI production-path test is identified by its real service/client
  evidence, not by a mock-only test.
- Documentation statements are checked against passing evidence.

### Additional implementation verification

- Run the full relevant test collection to detect import/configuration issues
  across the separate package and application roots.
- Check that the integration harness itself is consumed by a real CLI test and
  does not hide transport or lifecycle defects.