# Document and hand off the completed author migration

Update the smallest maintained documentation surface with the supported
structured author model, authoring workflow, compatibility status, and
verification evidence after implementation is complete.

Parent Task: tasks/20260919-author-metadata-migration/000-main.md
Depends On: tasks/20260919-author-metadata-migration/010-author-contract-and-transition.md
Depends On: tasks/20260919-author-metadata-migration/020-content-and-authoring-migration.md
Depends On: tasks/20260919-author-metadata-migration/030-rendering-and-output-migration.md
Depends On: tasks/20260919-author-metadata-migration/040-verification-and-legacy-removal.md

## Requirements checklist

- [ ] Maintained guidance documents the implemented structured metadata and
      single-/multi-author examples.
- [ ] The authoring-tool usage and compatibility/rejection status are current.
- [ ] Documentation claims are backed by the completed production-build and
      output evidence.
- [ ] No placeholder or target-only guidance is presented as current behavior.

## Research and supporting facts

`README.md` currently describes the generated site surfaces but not post
front matter or `scripts/new-post.js`. `docs/development/index.md` contains
only an archive-pagination note, and the documentation policy requires the
smallest structure owned by the affected subsystem. The repository has no
existing author-specific guide.

## Execution plan

Status: Draft

1. Review the accepted contract from subtask 010 and the verified behavior
   from subtasks 020–040.
2. Update `README.md` or the most appropriate existing developer-facing
   location with the current front-matter/tool examples and transition status.
3. Link the documented behavior to the actual build/test evidence without
   claiming unsupported legacy behavior.
4. Review the final task checklist and hand off unresolved or deferred scope.

### Implementation decisions and open questions

- Prefer extending `README.md` unless implementation reveals an existing
  authoring-specific owner; do not create a new documentation hierarchy for
  one compact contract.
- Document only behavior that passed the final evidence gate.

### Documentation

This subtask is the documentation change. Follow
`docs/development/documentation.md` and keep the public/developer guidance
with the capability it describes.

### Task checklist

- [ ] Select the owning maintained documentation location.
- [ ] Document structured metadata and tool usage.
- [ ] Document transition/rejection status based on evidence.
- [ ] Review links, examples, and claims for consistency with implementation.

### Requirement verification

Compare every documented example and compatibility claim with the final
production build, generated-output assertions, source scan, and post-rejection
test run from subtask 040.

### Additional implementation verification

Confirm the documentation does not instruct authors to use the removed scalar
field and does not imply that generated `_site` output is a source of truth.