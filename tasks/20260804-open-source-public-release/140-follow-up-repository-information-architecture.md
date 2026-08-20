# Refine Repository Information Architecture After Feedback

Reorganize historical plans, obsolete root documents, and developer convenience
files only after public users reveal which material causes real confusion.

## Requirements checklist

- [ ] Current authoritative documentation is visibly separated from historical material.
- [ ] Historical plans that remain useful are indexed under the archive rather than scattered through the root.
- [ ] Obsolete scratch and duplicate files are removed without deleting active fixtures or agent guidance.
- [ ] `agents/` and `test_dir/` remain intact unless the owner later changes that requirement.
- [ ] Links, scripts, tests, and contributor workflows remain valid after moves.

Parent Task: tasks/20260804-open-source-public-release/000-main.md
Depends On: tasks/20260804-open-source-public-release/080-post-publication-validation-and-early-adopter-intake.md

## Candidate scope

- Root historical material not handled by task `050`.
- Versioned historical task-guidance documents, while preserving active
  `agents/`.
- Remaining root ad hoc test scripts, sample files, and developer conveniences
  not handled by task `050`.
- Checked-in IDE/run configurations.
- Archive indexing and retention criteria.

The existing `tasks/` system, `agents/`, and `test_dir/` are not blanket cleanup
targets.

## Execution plan
Status: Draft

Collect actual confusion reported by early users. Build a reference graph for
candidate files before moving them. Define which locations are authoritative,
historical, generated, fixture-only, or local-only. Move in small batches with
link/test verification.

Prefer deletion for valueless scratch content, archive for durable historical
context, and current documentation for maintained guidance.

### Implementation decisions and open questions

- Preserve `agents/` and `test_dir/`.
- Do not perform a repository-wide rename merely for visual tidiness.
- Archive layout may expand from the minimal structure introduced by task `050`.

### Documentation

- Maintain `archive/README.md`.
- Update root and documentation navigation only as required by approved moves.

### Task checklist

- [ ] Gather public feedback and reference data.
- [ ] Classify candidate files.
- [ ] Approve a small move/delete batch.
- [ ] Apply moves and update links.
- [ ] Verify tests, scripts, and clean-clone navigation.

### Requirement verification

- Public users can distinguish current guidance from historical context.
- No active workflow or required fixture is broken.
- Preserved directories remain intact.
