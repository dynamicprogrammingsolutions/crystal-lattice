# Perform The Public Repository Readiness Gate

Produce a single evidence-backed go/no-go decision before changing repository
visibility.

## Requirements checklist

- [ ] Mandatory subtasks `010` through `050` are complete with evidence.
- [ ] A clean clone passes the agreed minimum build/test/documentation checks.
- [ ] The root presentation, license, support, security, and issue paths are coherent.
- [ ] No unresolved critical legal, security, privacy, cost, or newcomer-understanding blocker remains.
- [ ] Existing GitHub Actions logs/artifacts have been reviewed for public exposure.
- [ ] The owner explicitly approves the candidate commit and publication timing.
- [ ] A rollback and collaborator communication plan exists for any required history rewrite or publication problem.

Parent Task: tasks/20260804-open-source-public-release/000-main.md
Depends On: tasks/20260804-open-source-public-release/010-sensitive-data-and-history-release-gate.md
Depends On: tasks/20260804-open-source-public-release/020-claude-tools-license-and-provenance-restoration.md
Depends On: tasks/20260804-open-source-public-release/030-minimum-public-documentation-and-support.md
Depends On: tasks/20260804-open-source-public-release/040-minimum-ci-and-automation-hardening.md
Depends On: tasks/20260804-open-source-public-release/050-lean-root-cleanup-and-archive.md

## Release gate

The result must be one of:

- `GO`: no unresolved mandatory blocker; proceed to task `070`.
- `NO-GO`: list blocking evidence and return to the owning subtask.

Optional tasks `110` through `140` cannot cause `NO-GO` unless new evidence
shows that a supposedly optional item is actually a legal, security, cost, or
major comprehension risk.

## Execution plan
Status: Draft

Create a publication candidate commit and test it from a fresh clone with no
local untracked configuration. Review the repository as an anonymous developer,
not as an existing maintainer. Confirm that secrets and publication credentials
are absent, README paths are current, issue/security routing is clear, and
minimum CI is green.

Record the exact commit SHA approved for publication. Freeze merges between the
final review and the visibility change unless the gate is rerun.

### Implementation decisions and open questions

- Publication approval is tied to an exact commit.
- The first public release need not be a tagged software release.
- Optional cleanup remains optional unless evidence reclassifies its risk.

### Documentation

- Add a compact go/no-go record to Implementation Notes when execution starts.
- Do not create a marketing announcement as part of this gate.

### Task checklist

- [ ] Confirm predecessor completion.
- [ ] Create and test a clean clone.
- [ ] Review public-facing repository paths.
- [ ] Review Actions history/artifacts and GitHub settings checklist.
- [ ] Record candidate SHA and owner approval.
- [ ] Declare `GO` or `NO-GO`.

### Requirement verification

- The gate record links each mandatory requirement to a test, scan, inspection,
  or owner confirmation.
- Only a recorded `GO` authorizes task `070`.
