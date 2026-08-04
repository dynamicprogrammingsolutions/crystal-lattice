# Perform Lean Root Cleanup And Archive Historical Material

Reduce obvious root-level confusion before publication without reorganizing
active agent guidance, test fixtures, or the broader historical document tree.

## Requirements checklist

- [ ] The reviewed AGI conversation export is moved to `archive/conversations/`.
- [ ] The archive has a concise index explaining that archived material is historical and not current product guidance.
- [ ] Clearly temporary root files such as `poem.txt` are removed.
- [ ] Obsolete root planning/documentation files that materially confuse a newcomer are moved under the archive after reference checks.
- [ ] Active documentation links continue to resolve.
- [ ] `agents/` and `test_dir/` remain intact.
- [ ] The cleanup does not move sensitive content into the archive as a substitute for sanitization.

Parent Task: tasks/20260804-open-source-public-release/000-main.md
Depends On: tasks/20260804-open-source-public-release/010-sensitive-data-and-history-release-gate.md

## Decisions

- Decision: Preserve
  `conversation_ai-agent-architecture_2025-11-16-1202.agi.json` under
  `archive/conversations/` after task `010` approves it.
- Decision: Preserve `agents/` exactly as an active project area.
- Decision: Preserve `test_dir/` exactly.
- Decision: Delete obvious temporary content such as `poem.txt`.
- Decision: Defer broad restructuring of `plan/`, `plans/`, versioned agent task
  documents, IDE settings, and extensive test artifacts to task `140`.

## Suggested archive shape

```text
archive/
  README.md
  conversations/
  root-docs/
```

Create only the directories actually needed by the files moved in this stage.

## Execution plan
Status: Draft

Search references to each candidate before moving or deleting it. Move the AGI
export after sensitive-data approval. Remove `poem.txt` and other unmistakable
scratch files that have no test/documentation role.

Review root historical files such as old Bonjour plans, persistent-token plans,
and naming notes. Move only those that would otherwise mislead a newcomer into
treating obsolete material as current guidance. Leave ambiguous files in place
for the post-publication information-architecture task rather than expanding
scope.

Add an archive index that points readers to the current README, architecture,
development, and task system.

### Implementation decisions and open questions

- `archive/` is discoverable but clearly non-authoritative.
- Do not rename or restructure active `tasks/`.
- Do not clean `agents/` or `test_dir/`.
- Root test scripts should move only if confirmed obsolete and unreferenced.

### Documentation

- Add `archive/README.md`.
- Update links affected by approved moves.

### Task checklist

- [ ] Confirm task `010` approval for the AGI export.
- [ ] Search references for stage-one cleanup candidates.
- [ ] Create the minimal archive structure.
- [ ] Move the AGI export and approved obsolete root docs.
- [ ] Delete obvious scratch files.
- [ ] Verify links and preserved directories.

### Requirement verification

- The root is materially clearer without broad restructuring.
- The AGI export exists under `archive/conversations/`.
- `poem.txt` and approved scratch files are absent.
- `agents/` and `test_dir/` are byte-for-byte unaffected by this task.
