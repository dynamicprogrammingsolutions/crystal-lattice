# Tests And Docs For Live Compact Tool Rendering

Parent Task: tasks/20260730-one-line-tool-calls-terminal/000-main.md
Depends On: tasks/20260730-one-line-tool-calls-terminal/030-compact-toggle-slash-command-and-expand.md

Cover the new behaviour with tests in `application/python/tests` (and the
tool-loop event change in `core/python/tests`), and document the new command
and config key.

## Requirements checklist

- [x] Renderer tests (no live provider; synthesize events and capture output
      with a `lines.append` writer — pattern:
      `application/python/tests/test_terminal_event_rendering_web_citations.py`
      ~lines 36-75 for source-loading + echo-config app fixture):
  - [x] compact OFF: `tool_partial` start/stream/end renders exactly as
        today (guard against regression).
  - [x] compact ON: start/stream produce no output; end produces exactly one
        line containing `[<message_index>]`, the tool name, and the
        short/single_line content; `single_line` from `metadata.display` is
        preferred when present.
  - [x] compact ON with a missing `message_index` field renders cleanly
        without the index bracket.
  - [x] toggling mid-call does not mix modes for that call.
- [x] Slash command tests (pattern: direct `_cmd_*` invocation with
      `outputs: list[str]` and `ui_state: dict` —
      `application/python/tests/test_terminal_application.py` ~lines 987-1010):
  - [x] `/compact` toggles `ui_state`, prints state + expand hint;
        `on`/`off`/bad-arg behaviour.
  - [x] config default `tool_output_live_compact` seeds the initial state.
  - [x] `/list <index>` on a stored tool message prints full content +
        footer (the expand path).
- [x] Tool-loop test for `message_index` on `phase=end` events (see subtask
      010 pointers; multi-call batch asserts consecutive indices).
- [x] Docs:
  - [x] `application/python/README.md` "Terminal Usage" slash-command list
        (~line 412) gains `/compact`; "Listing Messages" section (~line 450)
        mentions expanding a compact tool call via `/list <index>`.
  - [x] `docs/reference/default-config.md` application section (~line 563)
        and `application/python/agent_terminal_app/default_config/config.json`
        (~line 527) gain `tool_output_live_compact` if defaults are listed
        there (keep default `false`).

## Run

- `application/python` tests run with the repo venv
  (`/home/pujan/Work/crystal-lattice/.venv`); renderer/command tests need no
  network or provider keys (echo config:
  `agent_terminal_app/config_echo_app.json`). Integration tests marked
  `ollama`/`integration` are out of scope.
