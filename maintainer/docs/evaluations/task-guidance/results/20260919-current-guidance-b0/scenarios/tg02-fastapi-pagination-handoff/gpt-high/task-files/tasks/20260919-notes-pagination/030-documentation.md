# Document the notes collection pagination contract

Update the maintained public description after the endpoint behavior is
implemented and verified.

Parent Task: tasks/20260919-notes-pagination/000-main.md

## Requirements checklist

- [ ] Update `README.md` with the exact `limit`/`offset` query contract.
- [ ] Document ascending-ID ordering and the total-count response header.
- [ ] Document invalid-value handling at the level supported by the API.
- [ ] State that requests without pagination retain the full JSON array.
- [ ] Avoid documenting target behavior before implementation and tests are
      complete.

Depends On: tasks/20260919-notes-pagination/010-api-pagination.md,
tasks/20260919-notes-pagination/020-route-tests.md

## Scope and implementation notes

Use the existing README rather than creating a new specification directory.
Document only the final approved and tested behavior, including the exact
header name, defaults, partial-parameter semantics, and validation bounds.

## Verification

Review the README against the implemented route and focused integration
tests. Documentation review confirms consistency but does not substitute for
runtime evidence.