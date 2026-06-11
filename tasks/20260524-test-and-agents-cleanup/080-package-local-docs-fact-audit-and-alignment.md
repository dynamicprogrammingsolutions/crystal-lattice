# Package-local Docs Fact Audit And Alignment

Audit package-local `README.md` and `AGENTS.md` files for stale repo facts, inconsistent terminology, and command drift, then decide how to split the resulting work into focused follow-up subtasks. This task is intentionally an audit-and-planning pass first, because the package-local docs surface is large enough that implementation may need to be delegated by area.

## Requirements checklist

- [ ] Inventory package-local `README.md` and `AGENTS.md` files that carry repo-structure, command, or contributor-guidance claims.
- [ ] Identify files already covered by narrower tasks `051` and `052` so work is not duplicated.
- [ ] Classify package-local doc issues into terminology drift, setup/install drift, command drift, and repo-structure drift.
- [ ] Recommend a sensible split into `081+` follow-up subtasks by area if the implementation surface is broad.
- [ ] Preserve enough findings and references that separate agents can take the follow-up slices without re-scoping from scratch.

Parent Task: `tasks/20260524-test-and-agents-cleanup/000-main.md`

Depends On: `tasks/20260524-test-and-agents-cleanup/050-root-agents-fact-audit-and-structure-refresh.md`

## Why this task exists

After the root `AGENTS.md` and root README are aligned, package-local docs still need their own fact check. The likely affected areas span multiple subtrees and styles of documentation:

- package-local runtime guidance
- package-local install/test/build guidance
- repo-structure assumptions copied into subdirectory docs
- package-local AGENTS files that may still steer contributors using older terminology

This is too broad to assume one implementation pass should touch all of it blindly.

## Suggested primary audit surface

Start with docs in these areas:

- `application/python/README.md`
- `application/python/agent_terminal_app/AGENTS.md`
- `mobile/crystal-lattice-control-rn/README.md`
- `mobile/crystal-lattice-control-rn/AGENTS.md`
- `desktop/crystal-lattice-control-desktop-rn/README.md`
- package-local README files under `packages/`

Then decide whether repo-root plugin package docs also need a broader package-local pass beyond what `051` and `052` already cover.

## Coordination notes

Avoid duplicating the work already assigned to:

- `tasks/20260524-test-and-agents-cleanup/051-plugin-terminology-and-docs-entrypoint-alignment.md`
- `tasks/20260524-test-and-agents-cleanup/052-setup-and-install-guidance-alignment.md`

This task should either:

- explicitly exclude their file set, or
- wait for their results and then audit the remaining package-local surface.

## Suggested split targets if needed

If the audit shows the surface is too large, likely follow-ups could be:

- `081-application-and-runtime-docs-alignment.md`
- `082-mobile-desktop-and-packages-docs-alignment.md`
- `083-package-local-command-guidance-cleanup.md`

Do not create these unless the audit confirms the split is useful.

## Suggested implementation steps

1. Inventory package-local docs that contain repo facts or maintainer guidance.
2. Mark which ones overlap with tasks `051` and `052`.
3. For the remaining files, classify the kind of drift:
   - terminology
   - setup/install
   - test/build commands
   - repo structure or doc-entrypoint guidance
4. Decide on the minimum useful split into `081+` follow-ups.
5. Write those follow-up tasks with enough references to support delegation.