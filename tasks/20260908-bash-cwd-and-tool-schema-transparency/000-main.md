# Bash CWD Handling and Tool Schema Transparency

Two parallel improvements to agent tooling behavior and transparency:
(1) configurable bash working-directory persistence, cwd visibility in tool
results, and cd guidance for the claude-tools Bash tool; (2) a tool schema
transparency plugin that lets users inspect and adjust the tool schemas the
model receives, from a rich UI element around the composer. The subtasks have
no dependency on each other and can be executed in parallel.

## Requirements checklist

- [x] Bash tool cwd persistence, result visibility, and cd guidance config options are delivered and verified per `tasks/20260908-bash-cwd-and-tool-schema-transparency/010-bash-cwd-persistence-and-visibility.md`.
- [ ] Tool schema transparency capabilities are delivered per the requirements in `tasks/20260908-bash-cwd-and-tool-schema-transparency/020-tool-schema-transparency.md`, with the implementation approach and UX planned in a separate brainstorming session before execution.

## Subtasks

- [x] `tasks/20260908-bash-cwd-and-tool-schema-transparency/010-bash-cwd-persistence-and-visibility.md`
- [ ] `tasks/20260908-bash-cwd-and-tool-schema-transparency/020-tool-schema-transparency.md`
  - PARALLEL with `010-bash-cwd-persistence-and-visibility.md` — no dependency in either direction.

## Context

### Background: the stuck-loop session

Session `.crystal/sessions/d4da57d2-512c-446c-99bf-ed493f3b8eb9` (claude
agent, mkdocs site in the `docs_site/` subdirectory) showed the model
repeatedly issuing `mkdocs build 2>&1 | tail -5` from the repo root and
receiving `Error: Config file 'mkdocs.yml' does not exist.` every time. The
model's reasoning correctly identified the fix ("cd into docs_site", "chain
the cd with the mkdocs command using &&") four times in a row, but the
emitted tool call never contained `cd`. Root causes found in the session
analysis:

1. The Bash tool description tells the model to avoid `cd` ("You may use `cd`
   if the User explicitly requests it"), which suppresses `cd` in the emitted
   command even when the model's reasoning says otherwise; the intent leaks
   into the `description` field instead of the `command`.
2. The model never sees the current cwd — `bash.end_cwd` metadata is internal
   (`_metadata` is not sent to the model), so the model cannot tell where it
   is, forgot it had cd'd back to the root, and concluded "cd doesn't persist".
3. Cwd persistence itself works (the `end_cwd` chain was confirmed in the
   session at messages 188–199), but the model had no visible evidence of it.

Subtask 010 addresses causes 1 and 2 with opt-in config options and an
improved default system message. Subtask 020 grew from the same transparency
theme: users should be able to inspect and adjust the tool schemas the model
sees.