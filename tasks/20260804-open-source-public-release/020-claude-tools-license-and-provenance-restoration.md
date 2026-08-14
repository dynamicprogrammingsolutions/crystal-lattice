# Restore Apache-2.0 Licensing For Claude Tools

Replace the ambiguous Anthropic-derived licensing model with a consistent
Apache-2.0 license and an accurate statement that normalized fixtures were
generated from AI observation of publicly visible Claude Code behavior.

## Requirements checklist

- [x] Original Claude Tools code and normalized fixtures are consistently identified as Apache-2.0 licensed Crystal Lattice material.
- [x] No file claims that Anthropic's license applies merely because publicly visible Claude Code behavior was observed.
- [x] The package clearly distinguishes compatibility from affiliation, endorsement, or ownership by Anthropic.
- [x] Raw investigation logs and credentials remain excluded from the repository.
- [x] Package, root licensing, notice, and investigation documentation do not contradict one another.
- [x] Claude Tools tests still pass after notice/header/documentation cleanup.

Parent Task: tasks/20260804-open-source-public-release/000-main.md
Depends On: tasks/20260804-open-source-public-release/010-sensitive-data-and-history-release-gate.md

## Decisions

- Decision: Normalized fixtures are outputs created by AI-assisted observation
  and normalization of publicly visible behavior.
- Decision: Those fixtures and the independently authored implementation are
  published under Apache-2.0.
- Decision: Anthropic retains its own trademarks and rights in Claude and Claude
  Code, but this does not replace the license selected for Crystal Lattice code
  and normalized fixtures.
- Decision: The package must include a clear non-affiliation statement.

## Scope

Review at least:

- `plugins/claude-tools/README.md`
- `plugins/claude-tools/investigation/README.md`
- `plugins/claude-tools/investigation/fixtures/**`
- `plugins/claude-tools/investigation/notes/**`
- `plugins/claude-tools/system_messages/claude/**`
- `plugins/claude-tools/src/claude_tools/**`
- `plugins/claude-tools/tests/**`
- `plugins/claude-tools/pyproject.toml`
- Root `LICENSING.md` and `NOTICE`
- Default-config copies or references to Claude system-message assets

## Known findings

- `plugins/claude-tools` contains 142 tracked files.
- No subtree `LICENSE`, `NOTICE`, or provenance file currently exists.
- Ten implementation modules carry a mixed header that says some material is
  not Apache-2.0 and instead subject to Anthropic's commercial terms.
- `plugins/claude-tools/README.md` repeats the same package-level claim and
  instructs readers to determine rights file by file.
- Forty-three package files already carry a standard Apache-2.0 header.
- `plugins/claude-tools/pyproject.toml` has no license metadata and currently
  permits setuptools versions older than the modern SPDX/license-files metadata
  support.
- Root `LICENSING.md` and the root README broadly say compatibility-oriented
  material may not be Apache-2.0, which would contradict the approved Claude
  Tools licensing decision unless clarified.
- Raw investigation output is correctly ignored; only
  `investigation/raw/.gitkeep` is tracked.
- Seven normalized fixture files still contain the development user's absolute
  home path. These occur in MCP output, MCP error, and system-message fixtures.
- The central normalizer replaces caller-provided paths and volatile IDs but
  does not currently normalize Unix, macOS, or Windows user-home prefixes
  generically.
- Default configuration uses the modular Claude system-message files. The
  legacy `application/python/agent_terminal_app/default_config/CLAUDE_CODE_DEFAULT.md`
  and behavior fixtures also contain observed literal Claude Code identity
  strings.
- Task `010` completed full-tree/history credential scanning; no active
  credential was found in the Claude Tools current tree.

## Execution plan
Status: Approved

### Phase 1: Establish the package license and provenance boundary

Add:

- `plugins/claude-tools/LICENSE`, containing the full Apache License 2.0 text.
- `plugins/claude-tools/PROVENANCE.md`, containing the detailed source and
  generation explanation.
- A concise subtree `NOTICE` only if it adds information not better kept in
  `PROVENANCE.md`.

The provenance document must state:

- Crystal Lattice Claude Tools is an independent compatibility implementation.
- Crystal Lattice is not affiliated with, sponsored by, or endorsed by
  Anthropic.
- Claude and Claude Code are Anthropic product/trademark names used only to
  identify compatibility.
- Tool schemas, result shapes, prompts, and fixtures were generated and
  normalized through AI-assisted observation of publicly visible Claude Code
  behavior.
- The normalized fixtures, investigation notes/scripts, tests, system-message
  compatibility assets, and independently authored implementation in this
  subtree are distributed under Apache-2.0.
- Raw logs and authentication material are excluded and must not be committed.
- Literal compatibility strings may mention Claude Code or reproduce observed
  behavior without changing Crystal Lattice's independent status.

Do not claim that Anthropic licensed, approved, or contributed the Crystal
Lattice implementation or generated fixtures.

### Phase 2: Replace mixed source and package license claims

For the ten implementation modules with mixed headers:

1. Remove the preliminary "derived/adapted" note.
2. Remove the Anthropic commercial-terms block.
3. Retain one standard Dynamic Programming Solutions Kft. Apache-2.0 header.
4. Make no executable-code or schema changes as part of the header edit.

Update `plugins/claude-tools/README.md` so its license section:

- applies Apache-2.0 consistently to the package;
- links to `LICENSE` and `PROVENANCE.md`;
- includes the concise non-affiliation statement;
- no longer says rights must be determined file by file;
- no longer attributes Crystal Lattice files to Anthropic or imports
  Anthropic's commercial terms as their license.

Update `plugins/claude-tools/investigation/README.md` to explain the fixture
generation and normalization boundary and to reinforce that raw logs are
local-only.

### Phase 3: Add distributable package metadata

Update `plugins/claude-tools/pyproject.toml` to:

- declare the SPDX license expression `Apache-2.0`;
- include the subtree `LICENSE` in built distributions;
- add the repository/project URL fields appropriate for the public package;
- use a setuptools build requirement new enough to support the selected
  standardized license metadata.

Build a wheel and source distribution in a temporary directory and inspect:

- wheel/sdist contents;
- core metadata license expression;
- inclusion of `LICENSE`, README, and any required provenance/notice file.

Do not normalize all other plugin package metadata in this task; that remains
owned by post-publication task `120`.

### Phase 4: Fix normalization at the source

Extend the shared fixture normalization logic so future investigations
normalize user-home paths after explicit workspace/raw-directory replacements:

- macOS: `/Users/<name>`
- Linux: `/home/<name>`
- Windows: drive-letter `Users` paths

Use a stable placeholder such as `<USER_HOME>`. Preserve the more-specific
`<WORKSPACE>`, `<RAW_DIR>`, and related placeholders by applying explicit
replacements first.

Add deterministic unit coverage for:

- macOS, Linux, and Windows home-path normalization;
- preserving already-normalized placeholders;
- nested strings in dictionaries/lists;
- avoiding unrelated URL or schema changes.

Update the relevant investigation scripts where their replacement maps are
currently incomplete, especially:

- system-message workspace resolution;
- MCP persisted-output/debug paths;
- MCP missing-file paths.

Normalize the seven existing affected fixtures by running repository-owned
normalization code over the committed JSON. Do not manually transcribe fixture
content. Review the resulting diffs to confirm that only path placeholders and
mechanically necessary formatting changed.

### Phase 5: Align root and default-config licensing statements

Update root `LICENSING.md` and the root README so they distinguish:

- independently implemented compatibility behavior and generated normalized
  fixtures, which may be Apache-2.0 under the applicable project/subtree
  license; from
- actual third-party source/material, whose upstream license and notices still
  apply.

Keep the existing Codex, Gemini, Kimi, Qwen, and Grok notices intact. Do not
relicense or reclassify those subtrees in this task.

Update root `NOTICE` only if needed to point to the Claude Tools subtree
provenance/non-affiliation notice. Do not add an Anthropic copyright attribution
for Crystal Lattice-authored or generated materials.

Treat the literal identity and behavior strings in:

- `plugins/claude-tools/system_messages/claude/**`;
- normalized fixtures; and
- `application/python/agent_terminal_app/default_config/CLAUDE_CODE_DEFAULT.md`

as behavior-critical compatibility assets. Keep their runtime text unchanged
unless a test or source review shows that a string is accidental rather than
observed behavior. Explain their status in provenance documentation instead of
injecting legal comments into LLM-facing prompts.

### Phase 6: Update package-local agent guidance

With approval of this plan, update `plugins/claude-tools/AGENTS.md` with a short
licensing/provenance section covering:

- Apache-2.0 as the subtree license;
- normalized observed behavior as project fixture material;
- raw-log exclusion;
- mandatory user-home/workspace normalization;
- preservation of behavior-critical compatibility strings;
- non-affiliation language for user-facing documentation.

This prevents future contributors from recreating the mixed-license wording.

### Phase 7: Verify behavior, packaging, and wording

Run:

- `pytest plugins/claude-tools/tests -q -m 'not integration'`
- `ruff check plugins/claude-tools/src/claude_tools plugins/claude-tools/tests`
- `pytest application/python/tests/test_claude_system_message_helpers.py -q`
- `pytest application/python/tests/test_claude_compaction_feature_action.py -q`
- relevant default-config/plugin-loading tests selected during implementation;
- wheel/sdist build and metadata/content inspection.

Static verification must confirm:

- no remaining mixed Anthropic commercial-terms notice in Claude Tools;
- no claim that observed behavior causes Anthropic's license to apply;
- no `/Users/ferenci84` or equivalent unnormalized real user-home path remains
  under `plugins/claude-tools`;
- only `.gitkeep` is tracked under `investigation/raw`;
- package/root licensing statements agree;
- generated package metadata reports Apache-2.0;
- executable schemas, result strings, and system-message behavior remain
  unchanged except for approved normalization placeholders.

### Implementation decisions and open questions

- Do not retain the current statement that some files are automatically subject
  to Anthropic's commercial terms.
- Do not imply that Crystal Lattice is the official Claude CLI.
- Keep observed, behavior-critical literal strings such as the Claude Code
  identity prompt inside LLM-facing compatibility assets. The non-affiliation
  distinction belongs in package/provenance documentation, not injected into
  the runtime prompt.
- No external CLA or separate proprietary subtree license is planned.
- Use `<USER_HOME>` for generic home-path normalization and preserve
  `<WORKSPACE>` when the path is the explicit investigation workspace.
- Add license metadata to Claude Tools now; leave repository-wide package
  metadata normalization to task `120`.
- Update `plugins/claude-tools/AGENTS.md` as described in Phase 6. Approval of
  this execution plan constitutes approval for that package-local guidance
  update.

### Documentation

- Add subtree `LICENSE` and `PROVENANCE.md`.
- Update Claude Tools README, investigation README, and package-local
  `AGENTS.md`.
- Update root README and `LICENSING.md` only enough to remove the contradiction.
- Update root `NOTICE` only if needed to point to the subtree provenance.

### Task checklist

- [x] Inventory mixed and ambiguous notices.
- [x] Add/confirm subtree Apache-2.0 license material.
- [x] Replace file-level and README licensing claims.
- [x] Add provenance and non-affiliation wording.
- [x] Add Claude Tools package license/project metadata.
- [x] Fix home-path normalization and normalize affected fixtures.
- [x] Audit fixtures/system messages for raw or unintended captured data.
- [x] Align root licensing/README wording without changing other subtree licenses.
- [x] Update Claude Tools package-local agent guidance.
- [x] Build and inspect wheel/sdist license metadata and included files.
- [x] Run focused Claude Tools and default-config tests.

### Requirement verification

- Repository search finds no remaining claim that Anthropic's license applies
  because content is behavior-derived.
- License/provenance wording is consistent across package and root documents.
- Package build metadata and contents identify Apache-2.0 and include the
  required license/provenance files.
- Fixture scans find no real user-home path or tracked raw log.
- Focused Claude Tools tests and relevant default-config tests pass.

### Additional implementation verification

- Compare tool schemas, result fixtures, and modular system-message assets
  before and after changes, allowing only approved path-placeholder changes.
- Verify no unrelated package or subtree license/notice was changed.
- Verify the existing dirty worktree changes outside task `020` remain
  untouched and unstaged.

## Implementation Notes

### License and provenance boundary

- Added a full Apache-2.0 subtree `LICENSE`.
- Added `PROVENANCE.md` describing the AI-assisted public-behavior
  investigation and normalization process.
- The provenance statement identifies Claude Tools as an independent
  compatibility implementation and states that Crystal Lattice is not
  affiliated with, sponsored by, or endorsed by Anthropic.
- The package README and investigation README now use the same license and
  provenance model.
- Ten implementation modules now carry only the standard Dynamic Programming
  Solutions Kft. Apache-2.0 header. Hash comparison from each module's
  `from __future__` line through end of file confirmed that executable source
  content did not change.
- Root README, `LICENSING.md`, and `NOTICE` now distinguish independently
  produced compatibility material from actual copied or adapted third-party
  material without changing the existing Codex, Gemini, Kimi, Grok, or Qwen
  notices.

### Packaging

- `pyproject.toml` now declares the SPDX expression `Apache-2.0`, includes
  `LICENSE` and `PROVENANCE.md` as license files, and identifies the public
  repository and issue tracker.
- An isolated build produced both wheel and source distributions.
- The wheel metadata reported:
  - `License-Expression: Apache-2.0`
  - `License-File: LICENSE`
  - `License-File: PROVENANCE.md`
- Both wheel and source distributions included the license, provenance, and
  README material.

### Fixture normalization and publication audit

- Added generic normalization for macOS, Linux, and Windows user-home paths,
  including Claude's encoded project-directory keys.
- Explicit replacements such as `<WORKSPACE>` and `<RAW_DIR>` run before
  generic home normalization.
- Added deterministic normalization tests, including a scan over every
  committed Claude fixture.
- Seven fixtures were regenerated through the repository normalizer. Their
  diffs changed only real home paths and encoded home keys to `<USER_HOME>` and
  `<USER_HOME_KEY>`.
- Static checks found no remaining real user-home path in committed Claude
  fixtures.
- Only `investigation/raw/.gitkeep` is tracked under the raw investigation
  directory. Existing ignored local raw logs were not modified or added.
- Task `010` had already established that the publication candidate contained
  no unresolved active credential in the Claude Tools current tree.

### Verification findings

- The task-owned Ruff scope passed.
- A broader package Ruff command also reported two pre-existing unused imports
  in unchanged files:
  - `investigation/scripts/investigate_read_tool.py`
  - `tests/test_claude_compaction_feature_ollama_integration.py`
  These are unrelated to the licensing/provenance changes and were not changed.
- The normal production default-config tests currently fail before Claude
  Tools is resolved because the installed OpenAI Responses plugin imports an
  `aiohttp.SocketTimeoutError` attribute unavailable in that test
  environment's dependency combination.
- A temporary derived configuration removed only the unrelated OpenAI
  Responses provider registration. It retained the production `claude` agent,
  OpenRouter provider, Claude mixins, system-message assets, and
  `path:${env:BUILTIN_PLUGINS}/claude-tools` plugin source. That smoke test
  created the Claude session and compiled the full system message successfully.

## Completion Notes

Completed on August 12, 2026.

### Outcome

- Claude Tools code, normalized fixtures, investigation assets, tests, and
  compatibility system-message assets are consistently presented as
  Apache-2.0 Crystal Lattice material.
- The former claim that Anthropic's commercial terms automatically apply to
  behavior-derived Crystal Lattice files has been removed.
- Public documentation now clearly separates compatibility from affiliation
  and preserves observed Claude-facing strings only where they form part of
  the compatibility contract.
- Package metadata and built distributions carry the intended license and
  provenance files.
- Fixture generation now prevents real platform user-home paths from being
  recommitted.

### Requirement evidence

- License consistency: repository searches found no remaining mixed Anthropic
  commercial-terms wording in Claude Tools, root licensing, README, or notice
  content.
- Non-affiliation: package README and `PROVENANCE.md` explicitly identify the
  implementation as independent and not affiliated with or endorsed by
  Anthropic.
- Raw-data exclusion: Git tracks only `.gitkeep` under
  `investigation/raw`; fixture scans find no real user-home path.
- Behavior preservation: all ten header-only implementation edits retained
  byte-identical executable source bodies.
- Package behavior: `114` Claude Tools non-integration tests passed.
- Application behavior: all `8` Claude compaction action tests passed; the
  production-shaped Claude default-config smoke passed.
- Packaging: isolated wheel/sdist build and metadata inspection passed.

### Verification performed

- `pytest plugins/claude-tools/tests -q -m 'not integration'`
  - `114 passed`, `9 deselected`
- `pytest plugins/claude-tools/tests/test_fixture_normalization.py -q`
  - `4 passed`
- Task-owned Ruff check
  - passed
- `pytest application/python/tests/test_claude_compaction_feature_action.py -q`
  - `8 passed`
- Claude helper tests not requiring full plugin resolution
  - `2 passed`
- Isolated wheel and source-distribution build
  - passed
- Production-shaped Claude agent/config/system-message smoke
  - passed
- Static license, raw-log, home-path, and diff checks
  - passed

### Deferred adjacent issue

The repository's full default-config test environment has an OpenAI
Responses/aiohttp compatibility failure that occurs before Claude Tools loads.
It is not caused by this task and does not change the Claude Tools completion
evidence. It should be handled in the owning provider or dependency-hardening
work rather than expanding this legal/provenance task.
