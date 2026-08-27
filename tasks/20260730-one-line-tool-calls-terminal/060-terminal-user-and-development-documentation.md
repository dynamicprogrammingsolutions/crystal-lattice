# Terminal User Documentation, Help, And Development Guidance

Parent Task: tasks/20260730-one-line-tool-calls-terminal/000-main.md
Depends On: tasks/20260730-one-line-tool-calls-terminal/015-preserve-tool-end-events-through-compaction.md
Depends On: tasks/20260730-one-line-tool-calls-terminal/020-compact-live-tool-rendering.md
Depends On: tasks/20260730-one-line-tool-calls-terminal/030-compact-toggle-slash-command-and-expand.md
Depends On: tasks/20260730-one-line-tool-calls-terminal/050-terminal-progress-and-interactive-ui-tests.md

Provide audience-appropriate, discoverable documentation for important
terminal commands, application-owned rendering configuration, progress
behavior, and implementation/testing boundaries. Align the internal `/help`
experience with the same command registry and decide what concise guidance
appears when the terminal starts.

## Requirements checklist

- [x] A focused application-owned user page explains important terminal
      commands, command modes, message expansion, progress behavior, and
      relevant configuration in supported-user vocabulary.
- [x] The package README remains concise and links to the detailed terminal
      guide; `application/python/docs/index.md` makes the guide discoverable.
- [x] Each documented tool-output configuration key explains its type,
      default, units/limits, startup/runtime effect, persistence boundary,
      fallback behavior, and interaction with the slash command.
- [x] `/help` lists every registered slash command exactly once with accurate
      descriptions and exposes the approved tool-output mode vocabulary.
- [x] `/help config` accurately describes application-level terminal settings
      and their current/default values without implying that runtime-only
      command state is persisted.
- [x] The terminal presents an approved startup-help experience that is useful
      without overwhelming recurring users, and its behavior is tested.
- [x] Development documentation explains event compaction, terminal polling,
      renderer lifecycle state, progress ownership/redraw, and the layered
      interactive UI test strategy.
- [x] Generated/prepared reference output is refreshed from maintained sources
      through the approved documentation workflow, and documentation examples
      are checked against tests or captured current behavior.

## Documentation placement and audience

- **Package user guide:** add a focused page such as
  `application/python/docs/terminal.md`. Move or translate detailed terminal
  usage from the oversized package README; do not expose task ids, review
  severities, or implementation phases.
- **Package entry points:** keep `application/python/README.md` to a concise
  command overview and link, and add the terminal guide to
  `application/python/docs/index.md`.
- **Configuration guide:** place explanatory application configuration in the
  package user docs. The default JSON remains the maintained value source.
- **Development guide:** update
  `application/python/docs/development/terminal-and-http-features.md` and
  `application/python/docs/development/request-execution.md`, or create one
  focused terminal rendering/testing page if those pages would become
  unwieldy. Link any new page from the development index.
- **Generated reference:** update maintained config/schema sources and run
  `docs_site/scripts/prepare_mkdocs_site.py`; do not edit
  `docs_site/prepared/` or `docs_site/dist/` directly.

## Execution plan
Status: Approved

First finalize command names, configuration names, compact output, progress
labels, and startup behavior in the preceding subtasks. Then write the user
guide from verified current behavior.

Create a terminal command/configuration table whose source is the registered
command set and application configuration schema, while keeping prose focused
on user intent:

- starting and exiting;
- sessions and agents;
- sending, appending, cancelling, listing, modifying, deleting, and forking;
- plugin/config controls;
- tool-output presentation and `/list <index>` expansion;
- request/LLM/tool progress and cancellation;
- runtime mode versus startup configuration.

Strengthen `/help` tests so command registration and help cannot drift.
Consider command-specific help only if the main catalog cannot communicate
mode syntax clearly. Do not duplicate a separate hand-maintained command list
inside the implementation.

Evaluate startup choices with representative output:

1. full `/help` catalog every launch;
2. concise quick-help summary;
3. existing one-line hint;
4. configurable `summary|hint|off`.

Recommendation: default to a concise summary containing the prompt convention,
send/cancel, session/help, and tool-output command, with a documented
application setting allowing `hint` or `off`. Avoid printing the full command
catalog on every launch.

For development documentation, describe current code ownership and invariants:

- application event compaction preserves semantically terminal tool end
  events;
- terminal polling consumes public events and does not infer lost results;
- permanent renderers and transient progress presentation have separate
  responsibilities;
- request-terminal events clear renderer/progress state;
- deterministic reducer/pipe-input tests are distinct from real-PTY screen
  tests;
- supported platform and fallback boundaries are explicit.

### Implementation decisions and open questions

- Approve the terminal guide filename; recommendation:
  `application/python/docs/terminal.md`.
- Approve startup behavior; recommendation: configurable
  `summary|hint|off`, default `summary`.
- Decide whether `/help <command>` is in scope. Recommendation: keep the
  catalog plus argument completions unless mode syntax becomes unclear.
- Decide whether config reference text should be generated from richer schema
  descriptions in the future. This task should not build a new generator
  unless current authored guides and `/help config` remain insufficient.

### Documentation

- This subtask owns all documentation changes described above.
- User pages describe delivered behavior directly and do not link task files
  or internal completion evidence.
- Development pages identify code/test entry points and verification
  boundaries without duplicating the execution plan.

### Task checklist

- [x] Approve startup-help behavior and terminal guide placement.
- [x] Add/link the focused terminal user guide and shorten duplicated README
      detail.
- [x] Document command modes, config semantics, progress, cancellation, and
      expansion with tested examples.
- [x] Strengthen `/help`, `/help config`, and startup-output tests.
- [x] Update event/rendering/progress/testing development documentation.
- [x] Prepare the documentation site and verify links/examples.
- [x] Run the relevant docs preparation/build checks and application tests.

### Requirement verification

- Navigation inspection reaches the terminal guide from README/docs index in
  at most two links.
- Tests compare `/help` output with the registered command set and assert the
  approved tool-output syntax.
- Startup-output tests cover the approved default and any configurable
  alternatives.
- User examples match exact normalized output from deterministic tests.
- `/help config` and the user guide agree with maintained schema/defaults.
- Documentation preparation succeeds without direct edits to generated trees.

### Additional implementation verification

- Review docs at narrow terminal widths and as plain text to keep tables and
  examples readable.
- Search for stale `/compact`, old config-key names, “exactly one physical
  line” claims, and outdated progress behavior after implementation.

## Completion Notes

- Added `application/python/docs/terminal.md` and linked it from the package
  README and docs index.
- The guide covers command syntax, `/help`, `/help config`, startup modes,
  request/LLM/tool progress, one-line/full tool output, expansion, session
  filters, plugins, shortcuts, reload/provider keys, non-TTY behavior, and all
  terminal-owned configuration keys.
- Added `application/python/docs/development/terminal-ui.md`; updated the
  development index, request-execution page, and terminal/HTTP feature guide.
- Help tests compare output with the command registry and verify the approved
  command/config names. Startup mode tests cover `summary`, `hint`, and `off`.
- `docs_site/scripts/build_mkdocs_site.py` prepared and built the site and
  refreshed `docs/reference/default-config.md` from maintained config.
- The build passed with existing navigation and cross-reference warnings; no
  new broken-link failure was reported.