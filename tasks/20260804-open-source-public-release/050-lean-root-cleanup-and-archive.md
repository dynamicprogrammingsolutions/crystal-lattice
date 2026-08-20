# Perform Lean Root Cleanup And Archive Historical Material

Reduce obvious root-level confusion before publication without reorganizing
active agent guidance, test fixtures, or the broader historical document tree.

## Requirements checklist

- [x] The reviewed AGI conversation export is moved to `archive/conversations/`.
- [x] The archive has a concise index explaining that archived material is historical and not current product guidance.
- [x] Clearly temporary root files such as `poem.txt` are removed.
- [x] Obsolete root planning/documentation files that materially confuse a newcomer are moved under the archive after reference checks.
- [x] The complete historical `plan/` and `plans/` trees are moved under the archive with still-relevant task references updated.
- [x] Active repository-level test infrastructure lives under `test/`, while unreferenced ad hoc root glob scripts are preserved as inert archived examples.
- [x] Active documentation links continue to resolve.
- [x] `agents/` and `test_dir/` remain intact.
- [x] The cleanup does not move sensitive content into the archive as a substitute for sanitization.

Parent Task: tasks/20260804-open-source-public-release/000-main.md
Depends On: tasks/20260804-open-source-public-release/010-sensitive-data-and-history-release-gate.md

## Decisions

- Decision: Preserve
  `conversation_ai-agent-architecture_2025-11-16-1202.agi.json` under
  `archive/conversations/` after task `010` approves it.
- Decision: Preserve `agents/` exactly as an active project area.
- Decision: Preserve `test_dir/` exactly.
- Decision: Delete obvious temporary content such as `poem.txt`.
- Decision: Move the complete `plan/` and `plans/` trees under `archive/`.
- Decision: Move `repo_test_env.py` to `test/repo_test_env.py` and update suite
  bootstraps so current consumers continue to import it.
- Decision: Archive the two unreferenced root glob scripts under non-test
  filenames.
- Decision: Defer versioned agent task documents, IDE settings, and remaining
  test/scratch artifacts to task `140`.

## Suggested archive shape

```text
archive/
  README.md
  conversations/
  plan/
  plans/
  root-docs/
  root-tests/
```

Create only the directories actually needed by the files moved in this stage.

## Current audit findings

- Task `010` approved
  `conversation_ai-agent-architecture_2025-11-16-1202.agi.json` for
  publication and normal archival movement.
- The AGI export is a 395,572-byte, 23-message historical conversation. Its
  current SHA-256 is
  `1f972b29bd94d4721848bbe635a049fa23186686d1a636b52700893eb82ae93b`.
- The following root files are unreferenced outside historical/task context and
  are superseded by current implementation and package documentation:
  - `bonjour-integration-plan.md`
  - `bonjour-integration-implementation-summary.md`
  - `persistent_token_plan.md`
  - `naming.md`
- Current Bonjour, bridge, pairing-token, resume, and mobile connection
  behavior is documented in the root, application, mobile, and bridge READMEs
  and is covered by current implementation/tests.
- `PROJECT_PLAN.md` presents itself as a current living roadmap but contains
  stale architecture assumptions, unfinished historical stages, old coverage
  policy, and a link to missing `PLUGIN_EXAMPLES.md`.
- Root `AGENTS.md` currently lists `PROJECT_PLAN.md` among current documentation
  entrypoints and classifies `plan/` and `plans/` as older planning records.
- `plan/` contains 11 tracked historical plan files. Its current tracked-index
  inventory hash is
  `867b429770ff02a0288c71a07e97983e44c6cd8cfa7419ba6108779e4526127d`.
- `plans/` contains 13 tracked historical plan/design files. Its current
  tracked-index inventory hash is
  `79919d76b7495fba5d9d0ee46034ca2320847080b2084128255e3016847fae4f`.
- External references to `plan/` are generic historical/task mentions only.
- Several frontend SDK task handoffs still link specific files under
  `plans/frontend-sdk/`. Those exact links must be updated to
  `archive/plans/frontend-sdk/`.
- Historical tasks describing the earlier movement of docs into `plans/` may
  retain their original paths when they accurately describe past state.
- `poem.txt` and `test_file.md` are unrelated poems, have no code/test/doc
  references, and are unmistakable scratch content.
- `repo_test_env.py` is active shared test infrastructure. It is imported by
  the core, application, example, cloud-agent, OpenAI Responses, OpenRouter, and
  reference-provider test suites and belongs under the repository-level
  `test/` directory.
- `test_glob_functionality.py` and
  `test_glob_performance_and_functionality.py` have no source, documentation,
  script, or task consumers.
- Pytest collects four tests from the two glob scripts solely because they are
  root `test_*.py` files. They are not part of the documented package-local
  validation commands.
- The glob scripts should be preserved under non-test-prefixed archive names so
  root pytest discovery no longer presents them as maintained tests.
- `.idea/`, `.run/`, `.vscode/`, `scratch/`, and broader root tooling cleanup
  remain deferred to task `140`.
- `.cloud-agent/` contains active cloud commands and is not an archive
  candidate.
- `agents/` currently contains eight tracked files. The tracked-index baseline
  hash is
  `0058ce4cfa49fb8efbc62d5ae50a2f517f710088481998090dda63e283955eb5`.
- `test_dir/` currently contains 80 tracked files. The tracked-index baseline
  hash is
  `7f32087cb680cc422245125d146d2755a73e10e6e07c84804d235ca8ec2d6d95`.
- Work will occur in the original `develop` worktree. Task `040` remains on
  `main` for a later merge.
- The `develop` worktree contains unrelated in-progress documentation-site
  changes. Task `050` must not restore, modify, stage, or absorb them.

## Execution plan
Status: Approved

### Phase 1: Freeze and verify the approved cleanup set

Record the current blob/hash, reference, tracked-path, and file-count state for
every candidate before moving or deleting it.

The approved move set for this task is:

```text
conversation_ai-agent-architecture_2025-11-16-1202.agi.json
  -> archive/conversations/conversation_ai-agent-architecture_2025-11-16-1202.agi.json

PROJECT_PLAN.md
  -> archive/root-docs/PROJECT_PLAN.md

bonjour-integration-plan.md
  -> archive/root-docs/bonjour-integration-plan.md

bonjour-integration-implementation-summary.md
  -> archive/root-docs/bonjour-integration-implementation-summary.md

persistent_token_plan.md
  -> archive/root-docs/persistent_token_plan.md

naming.md
  -> archive/root-docs/naming.md

plan/
  -> archive/plan/

plans/
  -> archive/plans/

test_glob_functionality.py
  -> archive/root-tests/glob-functionality.py

test_glob_performance_and_functionality.py
  -> archive/root-tests/glob-performance-and-functionality.py

repo_test_env.py
  -> test/repo_test_env.py
```

The approved delete set is:

```text
poem.txt
test_file.md
```

Do not add another candidate during execution merely because it looks old.
Unexpected references, sensitive content, or unclear ownership are blockers for
that file and defer it to task `140` rather than expanding this batch.

### Phase 2: Create the archive and current-doc routing

Create:

```text
archive/
  README.md
  conversations/
  plan/
  plans/
  root-docs/
  root-tests/
```

`archive/README.md` will:

- state that archive content is retained historical context, not current
  product, architecture, security, release, test, or contributor guidance;
- route readers to:
  - root `README.md`;
  - `ARCHITECTURE.md`;
  - `CONTRIBUTING.md`;
  - `docs/development/index.md`;
- index the archived conversation, root documents, planning trees, and glob
  scripts;
- identify the AGI file as a reviewed historical design conversation;
- warn that archived plans/scripts may contain obsolete paths, assumptions,
  commands, APIs, performance expectations, or incomplete proposals.

Add short `archive/plan/README.md`, `archive/plans/README.md`, and
`archive/root-tests/README.md` routing notices when the moved tree lacks a
clear root index. These notices must not reinterpret the historical content as
current behavior.

Add a concise `archive/` entry to the root README repository layout so GitHub
readers can distinguish historical content from active documentation.

Remove `PROJECT_PLAN.md`, `plan/`, and `plans/` from current-document routing in
`AGENTS.md`. Point active agent/contributor routing at current architecture,
development, examples, types/protocols, tasks, and package documentation
instead.

### Phase 3: Move historical material without disguising it as current

Move the AGI JSON byte-for-byte. Do not edit, normalize, reserialize, or redact
it during relocation; task `010` already approved the exact reviewed content.
Verify its SHA-256 is unchanged after the move.

Move the five historical root Markdown files into `archive/root-docs/`.

Add a short archive notice at the top of each moved root Markdown file:

- historical/non-authoritative status;
- pointer to `archive/README.md`;
- pointer to current documentation where an obvious current owner exists.

Move `plan/` and `plans/` while preserving every existing file body and relative
subtree layout. Verify all 24 original blobs remain present under the new
prefixes.

Update exact still-relevant task references, including the frontend SDK and
desktop handoffs, from `plans/...` to `archive/plans/...`. For the unfinished
VS Code phase, label the archived plan references as historical context that
must be revalidated before implementation.

Do not rewrite completed/historical task prose that accurately records the
former `plan/` or `plans/` location.

Update task `140` so already archived plan trees and glob scripts are removed
from its candidate scope while remaining ambiguous IDE/scratch/root tooling
work stays deferred.

### Phase 4: Remove scratch content and archive inert glob scripts

Delete:

- `poem.txt`;
- `test_file.md`.

Move the two glob scripts under `archive/root-tests/` using names that do not
start with `test_`.

Preserve their source body except for an optional top-level archive notice.
Do not modernize their API usage, timing threshold, formatting, or assertions
inside this cleanup task.

Verify:

- no current code, documentation, script, or task imports/invokes them;
- supported package-local test commands remain unchanged;
- root pytest discovery no longer collects these archived scripts as tests;
- explicitly invoking the archived scripts is not documented as a supported
  validation path.

Move `repo_test_env.py` to `test/repo_test_env.py`.

Do not turn `test/` into an import package. Update each owning suite bootstrap
to add the root `test/` directory to `sys.path` before importing
`repo_test_env`. This preserves the existing import name without shadowing
Python's standard `test` package.

Update the helper's repository-root calculation for its new location and
verify all known consumers continue to resolve the root `.env`.

Do not delete or move:

- `.idea/`;
- `.run/`;
- `.vscode/`;
- `scratch/`;
- `.cloud-agent/`;
- `agents/`;
- `test_dir/`.

### Phase 5: Recheck privacy, links, and current documentation

Confirm the AGI hash matches the approved task `010` baseline.

Run targeted current-tree checks over `archive/` for:

- common credential/private-key patterns;
- absolute personal home paths;
- `.env` values or runtime-session structures not already approved;
- accidental inclusion of scanner output, local backups, generated caches, or
  dependency directories.

Do not treat movement as sanitization. If a new sensitive finding appears,
leave the source file unmoved or restore it to its prior location, report the
finding without its value, and stop for owner direction.

Verify:

- no active source, script, workflow, package README, current documentation, or
  active task handoff points to a removed root path;
- root/current Markdown links still resolve;
- the root README and archive indexes route newcomers to current guidance;
- `git diff --check` passes;
- no generated docs-site output is staged.

Run documentation preparation and the non-strict MkDocs build if the existing
unrelated documentation-site work leaves the maintained preparation script
available. If that external work deletes or blocks the script, report
documentation build verification as blocked rather than restoring the script,
editing generated output, or broadening task `050`.

Historical task references to former root paths do not need rewriting when they
accurately describe past repository state.

### Phase 6: Prove preserved-directory and scope integrity

Recompute the tracked-index hashes and file counts for `agents/` and
`test_dir/`. They must match the recorded baselines exactly.

Confirm:

- no path under `agents/` or `test_dir/` changed;
- `test/repo_test_env.py` and its active consumers remain functional;
- `.cloud-agent/` remains intact;
- deferred IDE/scratch/tooling paths remain unchanged;
- task `040` remains confined to `main` and is not copied into this `develop`
  change;
- unrelated `develop` worktree changes remain untouched and unstaged;
- only the approved move/delete/index/routing/reference paths belong to task
  `050`;
- Git recognizes historical changes as moves where content permits.

Complete a newcomer root walkthrough and confirm the remaining root files no
longer present obsolete roadmaps, historical plan trees, pre-name-selection
notes, completed integration plans, accidental tests, or unrelated poems as
current project guidance.

### Implementation decisions and open questions

- `archive/` is discoverable but clearly non-authoritative.
- Do not rename or restructure active `tasks/`.
- Do not clean `agents/` or `test_dir/`.
- Archive the AGI export byte-for-byte.
- Archive `PROJECT_PLAN.md`, both Bonjour files, `persistent_token_plan.md`, and
  `naming.md`.
- Move the complete `plan/` and `plans/` trees under `archive/`.
- Delete `poem.txt` and `test_file.md`.
- Move active `repo_test_env.py` under `test/` and update suite bootstraps.
- Archive the unreferenced glob scripts under non-test-prefixed filenames.
- Update exact active task links to moved frontend SDK plans.
- Defer remaining IDE/scratch/root tooling reorganization to task `140`.
- No unresolved material question remains. Approval authorizes only the exact
  move/delete/routing/reference set above.

### Documentation

- Add `archive/README.md` and focused indexes for archived planning/test trees.
- Add archive notices to moved root Markdown plans.
- Update root README repository layout and active `AGENTS.md` routing.
- Update active task references to moved plan files.
- Update task `140`'s deferred candidate inventory.
- Do not add archived material to the public docs-site navigation.
- Do not rewrite historical tasks merely because they mention former paths.

### Task checklist

- [x] Confirm task `010` approval for the AGI export.
- [x] Search references for stage-one cleanup candidates.
- [x] Audit `plan/`, `plans/`, root test helpers, and glob scripts.
- [x] Create the archive structure and indexes.
- [x] Move the AGI export, root docs, and complete planning trees.
- [x] Delete the two approved scratch files.
- [x] Archive the two glob scripts and move `repo_test_env.py` under `test/`.
- [x] Update current routing, active task references, and task `140`.
- [x] Recheck archive privacy and current links.
- [x] Verify docs when available, pytest collection, and preserved directories.

### Requirement verification

- The root is materially clearer without broad restructuring.
- The AGI export exists under `archive/conversations/`.
- The AGI export hash is unchanged from the reviewed task `010` baseline.
- `PROJECT_PLAN.md`, root integration plans, `plan/`, and `plans/` no longer
  appear at the repository root.
- All 24 historical planning files remain present under `archive/`.
- `poem.txt` and `test_file.md` are absent.
- Archived plans are visibly historical and current entrypoints do not route to
  them as authoritative guidance.
- Active task links to retained archived plan context resolve.
- `test/repo_test_env.py` and its consumers remain functional.
- Root pytest discovery no longer collects the two archived glob scripts.
- Active documentation links pass, and documentation build is either successful
  or explicitly blocked by the pre-existing unrelated docs-site work.
- `agents/` and `test_dir/` are byte-for-byte unaffected by this task.

### Additional implementation verification

- Verify no task `040` file or hunk is introduced on `develop`.
- Verify unrelated `develop` worktree changes remain untouched and unstaged.
- Verify `test/repo_test_env.py`, `.cloud-agent/`, and active root
  documentation remain at their approved paths.
- Verify deferred IDE/scratch/tooling paths remain unchanged.
- Verify no scanner output, backup bundle, generated site, dependency tree, or
  credential value is added to the archive or staged.

## Implementation Notes

### Cleanup execution on August 20, 2026

- Created the historical archive index and focused indexes for the former
  `plan/`, `plans/`, and root diagnostic trees.
- Moved the reviewed AGI export byte-for-byte to `archive/conversations/`.
  Its SHA-256 remains
  `1f972b29bd94d4721848bbe635a049fa23186686d1a636b52700893eb82ae93b`.
- Moved five obsolete root documents to `archive/root-docs/` and added concise
  non-authoritative archive notices and current-document routes.
- Moved all 11 former `plan/` files and all 13 former `plans/` files while
  preserving every original blob byte-for-byte.
- Deleted `poem.txt` and `test_file.md`.
- Moved the two unreferenced glob scripts to `archive/root-tests/` under
  non-test-prefixed filenames. Pytest reports no tests collected from that
  directory.
- Moved `repo_test_env.py` to `test/repo_test_env.py`, corrected its repository
  root calculation, and updated seven suite bootstraps to add root `test/` to
  `sys.path`.
- Updated root README and AGENTS routing, active frontend/desktop task
  references, and task `140`'s remaining candidate scope.
- Added a narrow `.gitignore` exception for the approved AGI archive path after
  verification found that the general `conversation_*.agi.json` rule would
  otherwise silently omit the moved file.
- A temporary Git index recognized 33 moves, including the AGI export, all 24
  planning files, five root documents, two diagnostics, and the active test
  helper. The real Git index was not modified.

### Privacy and scope review

- The archive scan found no private-key file, credential file, backup, scanner
  output, dependency tree, or generated cache.
- Credential-related terminology appears only in the reviewed AGI export as
  approved architectural example text.
- One archived plugin-loader plan contains an accepted historical personal
  development path already covered by task `010`.
- `agents/` retained its eight-file tracked-index hash
  `0058ce4cfa49fb8efbc62d5ae50a2f517f710088481998090dda63e283955eb5`.
- `test_dir/` retained its 80-file tracked-index hash
  `7f32087cb680cc422245125d146d2755a73e10e6e07c84804d235ca8ec2d6d95`.
- `.cloud-agent/` remained unchanged.
- No task `040` path or hunk was introduced on `develop`; the `main` worktree
  remained clean.
- Unrelated in-progress documentation-site, landing-page, maintainer, and task
  changes in the `develop` worktree were not edited, staged, or absorbed.

### Verification

- `ruff check` passed for `test/repo_test_env.py` and all changed active suite
  bootstraps.
- Helper import/root resolution passed from the new `test/` location.
- Core: 464 passed, 26 deselected, one expected xfail.
- Core examples: 5 passed, 8 deselected.
- Application: 320 passed, 90 deselected, seven existing warnings.
- Cloud-agent application plugin: 53 passed.
- Documentation preparation and non-strict MkDocs build passed against the
  concurrent docs-site work.
- Local Markdown links in the archive/current entry files passed.
- Active task references to retained frontend SDK plans resolve under
  `archive/plans/`.
- `git diff --check` passed.
- Provider package runs exposed existing failures that reproduce identically in
  a clean detached checkout of pre-task commit `6c0f4c7e`:
  - OpenRouter: 3 failed, 129 passed, 99 deselected.
  - OpenAI Responses: 3 failed, 409 passed, 76 deselected.
  - Reference OpenAI-compatible provider: 15 failed, 86 passed, 61 deselected.
  These failures are outside task `050` and were not changed or weakened.

## Completion Notes

Task `050` completed on August 20, 2026.

The repository root now routes readers to current guidance while preserving
reviewed historical context under `archive/`. The AGI conversation, former
planning trees, obsolete root plans, and ad hoc glob diagnostics remain
available without appearing as current documentation or maintained tests.

Active shared environment-loading support now lives at
`test/repo_test_env.py`; all owning suite bootstraps use that location, and the
affected core, example, application, and cloud-agent suites pass.

The root scratch poems were deleted. `agents/`, `test_dir/`, `.cloud-agent/`,
and deferred IDE/scratch/tooling areas remained unchanged. Task `040` remains
confined to `main` for the owner's later merge.

Plan deviations and discoveries:

- The owner expanded the approved scope to include the complete `plan/` and
  `plans/` trees and the active test helper.
- The AGI destination required a narrow `.gitignore` exception so the approved
  file remains tracked after relocation.
- Provider-suite baseline failures were documented after clean-checkout
  reproduction; no provider behavior was changed.

## Post-completion follow-up

On August 20, 2026, roadmap row `0804-OS-050` was changed from `pending` to
`done`. The authored CSV and generated Markdown passed roadmap checks and all
35 roadmap tests. The configured Google Sheet push contained only that status
change; write read-back, synchronized status, and pull dry run all passed.
