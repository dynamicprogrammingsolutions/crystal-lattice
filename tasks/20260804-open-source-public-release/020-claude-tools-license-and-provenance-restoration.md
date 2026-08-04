# Restore Apache-2.0 Licensing For Claude Tools

Replace the ambiguous Anthropic-derived licensing model with a consistent
Apache-2.0 license and an accurate statement that normalized fixtures were
generated from AI observation of publicly visible Claude Code behavior.

## Requirements checklist

- [ ] Original Claude Tools code and normalized fixtures are consistently identified as Apache-2.0 licensed Crystal Lattice material.
- [ ] No file claims that Anthropic's license applies merely because publicly visible Claude Code behavior was observed.
- [ ] The package clearly distinguishes compatibility from affiliation, endorsement, or ownership by Anthropic.
- [ ] Raw investigation logs and credentials remain excluded from the repository.
- [ ] Package, root licensing, notice, and investigation documentation do not contradict one another.
- [ ] Claude Tools tests still pass after notice/header/documentation cleanup.

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

## Execution plan
Status: Draft

Inventory every current mixed-license header and every document that describes
Anthropic-derived material. Replace blanket Anthropic commercial-terms notices
with a package-level Apache-2.0 license statement and provenance explanation.
Use file headers only where the repository convention requires them; do not
repeat long ambiguous legal blocks throughout implementation files.

Add a subtree `LICENSE` and, if useful, a concise `NOTICE` or provenance document
that states:

- Crystal Lattice is not affiliated with or endorsed by Anthropic.
- Claude and Claude Code are Anthropic trademarks.
- Compatibility behavior was observed through publicly visible interfaces.
- Normalized fixtures and implementation in this repository are independently
  authored/AI-generated project materials under Apache-2.0.
- Raw investigation logs are excluded.

Review system-message and fixture files for accidental raw logs, credentials, or
unnecessary captured material. Preserve behavior-critical fixture content when
it is intentionally part of the compatibility implementation.

### Implementation decisions and open questions

- Do not retain the current statement that some files are automatically subject
  to Anthropic's commercial terms.
- Do not imply that Crystal Lattice is the official Claude CLI.
- Compatibility strings required for runtime behavior may still mention Claude
  Code where factually necessary.
- No external CLA or separate proprietary subtree license is planned.

### Documentation

- Update Claude Tools README and investigation README.
- Update root licensing/notice text only where needed for consistency.
- Add a concise non-affiliation/trademark statement.

### Task checklist

- [ ] Inventory mixed and ambiguous notices.
- [ ] Add/confirm subtree Apache-2.0 license material.
- [ ] Replace file-level and README licensing claims.
- [ ] Add provenance and non-affiliation wording.
- [ ] Audit fixtures/system messages for raw or unintended captured data.
- [ ] Run focused Claude Tools and default-config tests.

### Requirement verification

- Repository search finds no remaining claim that Anthropic's license applies
  because content is behavior-derived.
- License/provenance wording is consistent across package and root documents.
- Focused Claude Tools tests and relevant default-config tests pass.
