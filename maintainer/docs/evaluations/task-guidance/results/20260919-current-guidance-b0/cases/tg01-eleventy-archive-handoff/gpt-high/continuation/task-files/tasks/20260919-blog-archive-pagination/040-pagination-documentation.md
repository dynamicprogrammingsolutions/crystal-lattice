# Archive pagination documentation

Update the owning developer documentation once archive pagination is
implemented and its public URL contract is verified.

Parent Task: tasks/20260919-blog-archive-pagination/000-main.md

Depends On:

- tasks/20260919-blog-archive-pagination/010-archive-pagination-generation.md
- tasks/20260919-blog-archive-pagination/020-accessible-archive-navigation.md
- tasks/20260919-blog-archive-pagination/030-regression-coverage.md

## Requirements checklist

- [ ] Document the verified first-page and later-page archive URL behavior.
- [ ] Document the twenty-post page limit and static previous/next navigation
  as current supported behavior.
- [ ] Keep documentation aligned with the implemented and tested output.

## Supporting facts

- `docs/development/index.md` currently says that no archive pagination
  specification exists.
- `README.md` describes the site as producing a blog archive and static
  output but does not prescribe an archive URL pattern.
- The documentation rules favor the smallest owned document and prohibit
  documenting target-only behavior as current guidance.

## Execution plan

Status: Draft

- Replace the obsolete development-doc statement with concise guidance for
  archive page URLs, page size, ordering, and static navigation.
- Use the final approved URL pattern and only claims supported by the
  production-build test.
- Leave README unchanged unless the implemented behavior requires a
  user-facing clarification beyond its existing accurate summary.

### Implementation decisions and open questions

- Documentation must wait for approval of the later-page URL pattern and
  successful output verification.
- Do not create a separate specification directory for this small capability.

### Documentation

The maintained destination is `docs/development/index.md`, owned by the
development documentation area. No generated documentation source is present.

### Task checklist

- [ ] Update the development documentation with verified archive behavior.
- [ ] Check that all documented URLs and limits match generated output.
- [ ] Leave unrelated README and documentation structure unchanged.

### Requirement verification

- Review the edited documentation against the production-build test results
  and generated archive paths.
- Confirm no target-only or unresolved URL claim is presented as current
  guidance.