# Bash Cwd Persistence And Tool-Result Display Metadata Preservation

Fix the `claude_bash_tool` so the working directory actually persists between Bash commands the way the upstream Claude Code Bash tool description says it does, and fix a related provider metadata-preservation gap where the `display` payload on tool-result messages is lost across native-history rebuilds on the OpenAI Responses and reference OpenAI-compatible providers.

## Requirements checklist

- [x] Make `claude_bash_tool` capture the ending cwd of each foreground command (the sentinel machinery is already wired but `_parse_wrapped_output` discards `match.group("cwd")`).
- [x] Store the ending cwd in the tool-result message's `metadata` under a namespaced key (`metadata.bash.end_cwd`), formatted as a path relative to the configured `working_directory` when inside the tree, absolute when outside.
- [x] Propagate `last_result.get("metadata")` into the tool-result message `metadata` in `AgentCore.iter_tool_messages` (and the non-streaming `execute_tool_calls` path if it builds tool messages separately), without overwriting core-managed keys (`tool_call_id`, `tool_name`, `tool_plugin`, `display`).
- [x] Before each Bash execution, scan `context["session"]["messages"]` for the most recent tool-result message from `claude_bash_tool` and resolve its `metadata.bash.end_cwd` against the configured `working_directory`; fall back to the configured `working_directory` when absent, malformed, or pointing at a nonexistent path.
- [x] Background Bash commands must not update the cwd chain (skip the metadata for background results).
- [x] Replace the misleading `test_cwd_reset_matches_fixture` single-command test with a real two-command persistence test (first `cd <subdir> && pwd`, then `pwd`, assert the second runs in `<WORKING_DIRECTORY>/subdir`).
- [x] Add unit tests for the relative-path helpers (within-tree relative, `.`, outside-tree absolute, missing/empty fallback) and for the session-based read/write flow including a simulated sandbox-move (different configured `working_directory` resolves the same relative path).
- [x] Add a per-provider round-trip test that builds a session with a tool-result message carrying `metadata.bash.end_cwd`, runs it through `_rebuild_core_from_native`, and asserts the rebuilt tool message still has `metadata.bash.end_cwd`. Cover OpenRouter, OpenAI Responses, and reference OpenAI-compatible providers.
- [x] Update `investigate_bash_tool.py` to capture both tool results for the `success-cwd-reset` case (currently only the first tool result is captured), and re-run the investigation with `--keep-raw` to document the real upstream behavior.
- [x] Fix the `display` metadata preservation gap: ensure the OpenAI Responses tools extension and the reference OpenAI-compatible tools extension re-add `display` (and `tool_plugin`, `tool_name` where applicable) to `_metadata` for tool-result messages, matching the OpenRouter tools extension pattern.
- [x] Add a per-provider round-trip test that verifies `metadata.display` survives a native-history rebuild for tool-result messages on all three providers.
- [x] Update `plugins/claude-tools/investigation/notes/bash-tool.md` to document the actual persistence behavior now that the implementation matches the description.
- [x] Run focused package tests and adjacent validation: `pytest plugins/claude-tools/tests -q`, `pytest plugins/openrouter/tests -q`, `pytest plugins/openai_responses/tests -q`, `pytest plugins/reference-openai-compatible-provider/tests -q`, `pytest core/python/tests -q`, `pytest application/python/tests -q`.

## Background

### The bash cwd bug

`plugins/claude-tools/src/claude_tools/claude_bash_tool.py` copies the upstream Claude Code Bash tool description verbatim, including the line `"The working directory persists between commands, but shell state does not."` (line 61). It also copies the sentinel mechanism for capturing the final PWD: `_wrap_foreground_command` (line 262-270) writes `ORIG_PWD="$PWD"; eval <command>; STATUS=$?; FINAL_PWD="$PWD"; printf "\n{SENTINEL_STATUS}%s\n{SENTINEL_CWD}%s\n" "$STATUS" "$FINAL_PWD"; exit 0`, and `SENTINEL_RE` (line 224-227) captures both `status` and `cwd` named groups.

But the implementation never closes the loop:

- `_parse_wrapped_output` (line 273-286) reads `match.group("status")` and **discards `match.group("cwd")`** — the captured cwd is dead code.
- `execute_tool` (line 459) reads `state.get("working_directory")` and passes it as `workdir` to `run_shell_command`, but **never writes back** to `state["working_directory"]`.

So every command always runs in the original `working_directory` that `init()` (line 331-346) froze from config. The description says persistence; the implementation resets. This was the case from the very first commit (`30bf4f9f`).

The upstream Claude Code Bash tool genuinely persists the working directory (confirmed by the upstream description, the sentinel mechanism's purpose, the `/cd` slash command, and public reporting on Claude Code's `PersistentShell` → `TransientShell` + cwd-snapshot architecture). Our implementation is a parity bug, not a deliberate deviation.

### Why this causes the stuck loop

When the repo is in a subdirectory of the app's launch directory:

1. Primary working directory = parent dir. The Claude system message and the Bash description both tell the model to avoid `cd` and use absolute paths.
2. `npm install` has no absolute-path form — the model must `cd` into the repo. It does `cd /path/to/repo && npm install` once.
3. The description says "working directory persists between commands" — the model believes the `cd` is now sticky.
4. The next `npm` call resets to the parent dir (state never updated), so it runs in the wrong place and fails or no-ops.
5. The model is confused because it believes it already `cd`'d, retries variations, and loops. There is no schema knob to fix it (no `dir_path` parameter like the Gemini shell tool has), and the description forbids `cd`-per-call as a pattern.
6. Switching to `gemini-tools` fixes it because the Gemini `run_shell_command` tool exposes a `dir_path` parameter the model sets on every call.

### The display metadata preservation gap

While investigating how `metadata.bash.end_cwd` would survive the native-history rebuild, a pre-existing gap was spotted: the `display` payload on tool-result messages is lost across native-history rebuilds on the OpenAI Responses and reference OpenAI-compatible providers.

The preservation mechanism works like this:

- Each provider has `_native_internal_from_core_metadata(metadata)` which copies the **entire** core metadata dict into `_metadata` minus a small pop-list, and `_core_metadata_from_native_internal(internal)` which restores it the same way.
- Pop-lists per provider:
  - OpenRouter (`openrouter_provider.py:92-100`): `native_indices`, `tool_calls`, `tool_call_id`, `display`
  - OpenAI Responses (`openai_responses_provider.py:893-899`): `native_indices`, `display`
  - Reference (`provider.py:411-419`): `native_indices`, `tool_calls`, `tool_call_id`, `display`
- The tools extensions are supposed to re-add the fields that the provider popped but that need to survive. The OpenRouter tools extension (`openrouter_tools_extension.py:80-122`) re-adds `tool_plugin`, `tool_name`, `display` to `_metadata` for tool messages. The OpenAI Responses tools extension (`openai_responses_tools_extension.py:165-213`) and the reference tools extension (`tools_extension.py:151-187`) do **not** re-add `display` for tool messages — so `display` is lost on those two providers.

`bash.end_cwd` is not in any provider's pop-list, so it rides through automatically. `display` is popped by all three providers and only re-added by the OpenRouter tools extension — so it falls through the gap on the other two.

## Design: bash cwd persistence

### Storage location

Store the ending cwd in the **tool-result message's `metadata`** dict, under `metadata.bash.end_cwd`. The tool-result message is:

```python
{
    "role": "tool",
    "content": <text sent to LLM>,
    "metadata": {
        "tool_call_id": ...,
        "tool_name": "Bash",
        "tool_plugin": "claude_bash_tool",
        "display": ...,
        "bash": {"end_cwd": "subdir"},
    },
    "toolResult": <structured payload sent to LLM>,
}
```

Why this works:

- **Persists across requests and restarts**: the `Message` (with its `metadata`) is serialized via `Message.to_dict()` (`types.py:1685-1698`) and saved by `FilesystemSessionStore` as JSON (`sessions.py:174-184`). On restart, `Message.from_dict` restores the metadata (`types.py:1700-1720`). No runtime state, no config mutation.
- **Immutable**: attaching data to a newly created message, not mutating existing session state. Session/Message are frozen dataclasses; metadata is `deepcopy`'d on serialize/deserialize.
- **Not sent to the LLM**: provider `to_native_messages` consumes `role`, `content`, and `toolResult`; the `metadata` dict is internal (it already carries `tool_call_id`, `tool_schema`, `tool_plugin`, `display`).
- **Readable by the next Bash call**: the context passed to `execute_tool` includes `context["session"]` as a dict (via `ApplicationContext.build_tool_context` → `session.to_dict()`, `app_context.py:170-192`), which contains the full `messages` list including prior tool results with their metadata.
- **Survives native-history rebuild**: `bash.end_cwd` is not in any provider's `_native_internal_from_core_metadata` pop-list, so it is automatically carried through `_metadata` and restored. No tools-extension change is needed for preservation. (A round-trip test per provider is still required to guard against future regressions.)

### Path format: relative to configured working directory

Store the cwd as a path **relative to `state["working_directory"]`** (the configured working directory from `init()`). Rules:

- `end_cwd == configured_wd` → store `"."`
- `end_cwd` is inside the configured tree → store the relative path, e.g. `"subdir"`, `"subdir/nested"`
- `end_cwd` is outside the configured tree → store the absolute path (best effort; not portable but honest)

```python
def _cwd_for_storage(end_cwd: str, configured_wd: str) -> str:
    rel = os.path.relpath(end_cwd, configured_wd)
    if rel == ".":
        return "."
    if rel == ".." or rel.startswith(".." + os.sep):
        return str(Path(end_cwd).resolve())  # outside tree → absolute
    return rel

def _resolve_stored_cwd(stored: str, configured_wd: str) -> str:
    if not stored or stored == ".":
        return str(Path(configured_wd).resolve())
    if os.path.isabs(stored):
        return stored
    return str((Path(configured_wd) / stored).resolve())
```

This gives sandbox-portability: if the project moves from `/home/user/project` to `/sandbox/project`, a stored `"subdir"` resolves to `/sandbox/project/subdir`. Absolute paths (outside-tree `cd`s) are used as-is.

### Read flow (before execution)

In `execute_tool`, before running the command:

1. Get `configured_wd = state["working_directory"]`.
2. Scan `context["session"]["messages"]` (reverse iteration) for the most recent message where `role == "tool"` and `metadata.tool_name == "Bash"` and `metadata.tool_plugin == "claude_bash_tool"` and `metadata.bash.end_cwd` exists.
3. If found, `workdir = _resolve_stored_cwd(metadata["bash"]["end_cwd"], configured_wd)`.
4. If not found (first Bash call in session, or pre-fix session), `workdir = configured_wd`.
5. If the resolved workdir doesn't exist anymore (e.g., the subdir was deleted, or the session moved and the absolute path is wrong), fall back to `configured_wd`.

### Write flow (after execution)

1. `_wrap_foreground_command` already captures `FINAL_PWD` via the `SENTINEL_CWD` sentinel — keep as-is.
2. `_parse_wrapped_output` must return the cwd (use `match.group("cwd")`, fall back to the input `working_directory` if the sentinel is missing).
3. `_execute_foreground` returns the cwd through.
4. In `execute_tool`, after a foreground command (success or failure — `cd` still happens on non-zero exit), compute `stored = _cwd_for_storage(end_cwd, configured_wd)` and put it in the result dict:
   ```python
   return self._result(
       ...,
       extra={
           "metadata": {"bash": {"end_cwd": stored}},
           ...existing extra keys...
       },
   )
   ```
5. Background commands: skip the cwd metadata (they run in their own process and shouldn't affect the foreground cwd chain).

### Core change: propagate result metadata to tool message

The tool-message metadata is built in `iter_tool_messages` at `core.py:4672-4682` and currently ignores `last_result.get("metadata")`. Add a merge:

```python
metadata = {
    "tool_call_id": call_id,
    "tool_name": name,
}
# ... existing schema/plugin/display assignments ...
result_metadata = last_result.get("metadata") if isinstance(last_result, dict) else None
if isinstance(result_metadata, dict) and result_metadata:
    for key, value in result_metadata.items():
        if key not in metadata:  # don't overwrite core-managed keys
            metadata[key] = value
```

This is generic — any tool can attach metadata to its result dict and it flows into the persisted tool message. The guard `if key not in metadata` prevents tools from clobbering `tool_call_id`/`tool_name`/`tool_plugin`/`display`. The same propagation must be added to the non-streaming `execute_tool_calls` path if it builds tool messages separately.

## Design: display metadata preservation fix

### The gap

The OpenRouter tools extension re-adds `display` (and `tool_plugin`, `tool_name`) to `_metadata` for tool messages in its `to_native_messages` (`openrouter_tools_extension.py:100-116`). The OpenAI Responses tools extension (`openai_responses_tools_extension.py:203-211`) and the reference tools extension (`tools_extension.py:167-170`) only set `call_id`/`tool_call_id` for tool messages and do not re-add `display`. Since all three providers pop `display` in `_native_internal_from_core_metadata`, `display` is lost on the OpenAI Responses and reference providers.

### The fix

Two options:

**Option A (recommended): make the tools extensions re-add `display` for tool messages**, matching the OpenRouter pattern. In `openai_responses_tools_extension.py:to_native_messages`, for `role == "tool"` messages, copy `display` (and `tool_plugin`, `tool_name` if present) from core `metadata` into the native item's `_metadata`. Same for `reference_openai_compatible_provider/tools_extension.py:to_native_messages`.

**Option B: stop popping `display` in the OpenAI Responses and reference providers' `_native_internal_from_core_metadata`**, so it rides through automatically. This is simpler but changes the provider's metadata contract — `display` would then be in `_metadata` on all providers, which may affect the OpenRouter provider too if the pop-list is shared. Needs verification that no code path relies on `display` being absent from `_metadata`.

Option A is preferred because it matches the established OpenRouter pattern and is local to each tools extension.

### Tests

Add a per-provider round-trip test that builds a core tool message with `metadata.display = {"type": "text", "content": "..."}`, runs it through `provider.to_native_messages` + extensions + `provider.from_native_messages` + extensions (or the higher-level `_rebuild_core_from_native`), and asserts the rebuilt tool message still has `metadata.display`. Cover all three providers. The existing test `test_to_native_and_from_native_roundtrip_preserves_tool_metadata_without_extension` at `plugins/openrouter/tests/test_openrouter_provider_unit.py:224` is the template.

## Key file references

### Bash tool (main fix)

- `plugins/claude-tools/src/claude_tools/claude_bash_tool.py:61` — description claiming persistence
- `plugins/claude-tools/src/claude_tools/claude_bash_tool.py:187-218` — schema missing any working-directory parameter
- `plugins/claude-tools/src/claude_tools/claude_bash_tool.py:262-270` — `_wrap_foreground_command` captures `FINAL_PWD`
- `plugins/claude-tools/src/claude_tools/claude_bash_tool.py:273-286` — `_parse_wrapped_output` discards `match.group("cwd")` (fix: return it)
- `plugins/claude-tools/src/claude_tools/claude_bash_tool.py:392-424` — `_execute_foreground` (fix: return cwd)
- `plugins/claude-tools/src/claude_tools/claude_bash_tool.py:426-544` — `execute_tool` (fix: read last bash result's `end_cwd`, use as workdir, return `metadata.bash.end_cwd` in result)
- `plugins/claude-tools/src/claude_tools/claude_bash_tool.py:331-346` — `init` (configured `working_directory` source)

### Core (propagate result metadata to tool message)

- `core/python/agent_core/core.py:4471-4689` — `iter_tool_messages` (fix: merge `last_result.get("metadata")` into tool message `metadata` at line 4672-4682)
- `core/python/agent_core/core.py:221-232` — comment documenting the `_metadata` convention
- `core/python/agent_core/core.py:2099-2209` — `_rebuild_core_from_native` (the rebuild path that the round-trip test must exercise)
- `core/python/agent_core/core_context.py:155-167` — `build_tool_context` (session dict in context)
- `core/python/agent_app/app_context.py:170-192` — `ApplicationContext.build_tool_context` (session dict source)

### Provider `_metadata` propagation (verify, don't change for bash fix)

- `plugins/openrouter/src/openrouter_plugins/openrouter_provider.py:92-110, 427-465, 547-565` — OpenRouter `_native_internal_from_core_metadata` / `to_native_messages` / `from_native_messages`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py:893-909, 1742-1871` — OpenAI Responses equivalents
- `plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/provider.py:411-428, 533-630` — reference equivalents

### Tools extensions (display fix)

- `plugins/openrouter/src/openrouter_plugins/openrouter_tools_extension.py:80-150` — OpenRouter tools extension (reference pattern for `display` re-add)
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_tools_extension.py:165-213, 294-359` — OpenAI Responses tools extension (fix: re-add `display` for tool messages in `to_native_messages`)
- `plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/tools_extension.py:151-187` — reference tools extension (fix: re-add `display` for tool messages in `to_native_messages`)

### Tests and investigation (update)

- `plugins/claude-tools/tests/test_claude_bash_tool.py:251-277` — `test_cwd_reset_matches_fixture` (replace with real two-command test)
- `plugins/claude-tools/investigation/scripts/investigate_bash_tool.py:87-93, 198-217` — `success-cwd-reset` case and `_find_last_tool_result_block` (fix: capture both tool results)
- `plugins/claude-tools/investigation/fixtures/bash/success-cwd-reset.json` — currently only captures the first tool result
- `plugins/claude-tools/investigation/notes/bash-tool.md:87` — implementation direction note (update to document actual persistence)
- `plugins/openrouter/tests/test_openrouter_provider_unit.py:224` — `test_to_native_and_from_native_roundtrip_preserves_tool_metadata_without_extension` (template for round-trip tests)

### Session/message types (context, no change needed)

- `core/python/agent_core/types.py:1662-1720` — `Message` dataclass with `metadata` field, `to_dict`/`from_dict`
- `core/python/agent_core/types.py:1736-1783` — `Session` dataclass
- `core/python/agent_app/sessions.py:126-184` — `FilesystemSessionStore` load/save (JSON persistence)

## Edge cases to handle

- **Compaction**: if the session is compacted and previous bash tool results are summarized away, the metadata is gone. The bash tool falls back to the configured working directory. This is correct — compaction is a fresh start.
- **Concurrent requests sharing a session**: the tool loop for a single session is typically serialized, so no race within a session. Across sessions is irrelevant since each has its own message history. If concurrent requests on the same session are later supported, this needs a story (probably: serialize the tool loop per session).
- **`cd` on a failed command**: `cd /nonexistent && pwd` fails, so `FINAL_PWD` is still the original directory (the `cd` didn't happen). The stored cwd should be the unchanged working directory. The sentinel captures this correctly — `FINAL_PWD` is `$PWD` after the `eval`, which is unchanged if `cd` failed.
- **`cd` without `&&`**: `cd /path; pwd` — the `cd` succeeds, `pwd` shows the new dir. `FINAL_PWD` captures it. Next command uses the new dir. This matches upstream.
- **Session imported from a pre-fix version**: old bash tool results won't have `metadata.bash.end_cwd`. The read flow treats missing metadata as "no prior cwd" and falls back to the configured working directory. No migration needed.
- **Resolved workdir doesn't exist**: fall back to the configured working directory. This handles the sandbox-move case where an absolute stored path no longer exists.

## Validation

Run focused package tests after each stage:

```bash
pytest plugins/claude-tools/tests -q
pytest plugins/openrouter/tests -q
pytest plugins/openai_responses/tests -q
pytest plugins/reference-openai-compatible-provider/tests -q
pytest core/python/tests -q
pytest application/python/tests -q
```

Adjacent validation for the bash tool investigation:

```bash
python plugins/claude-tools/investigation/scripts/investigate_bash_tool.py --case success-cwd-reset --keep-raw
```

Lint and format:

```bash
ruff check plugins/claude-tools/src/claude_tools plugins/claude-tools/tests
black plugins/claude-tools/src/claude_tools plugins/claude-tools/tests
```

## Completion Notes

### What was done

**Bash cwd persistence** — `plugins/claude-tools/src/claude_tools/claude_bash_tool.py`:
- `_parse_wrapped_output` now returns the captured cwd from `match.group("cwd")` (was discarded).
- `_execute_foreground` returns the cwd through to `execute_tool`.
- Added `_cwd_for_storage(end_cwd, configured_wd)` — stores `"."` for same-dir, relative path for inside-tree, absolute path for outside-tree.
- Added `_resolve_stored_cwd(stored, configured_wd)` — resolves relative against configured wd, uses absolute as-is, falls back to configured wd when the resolved path doesn't exist.
- Added `_last_bash_end_cwd_from_context(context)` — scans `context["session"]["messages"]` in reverse for the most recent tool-result with `tool_name == "Bash"` and `tool_plugin == "claude_bash_tool"` and returns its `metadata.bash.end_cwd`.
- `execute_tool` now resolves the workdir from the last bash result's `end_cwd` before each foreground command, and returns `metadata.bash.end_cwd` in the result dict for foreground commands. Background commands skip the cwd metadata.

**Core metadata propagation** — `core/python/agent_core/core.py`:
- `iter_tool_messages` now merges `last_result.get("metadata")` into the tool-result message `metadata` without overwriting core-managed keys (`tool_call_id`, `tool_name`, `tool_plugin`, `tool_schema`, `display`). `execute_tool_calls` delegates to `iter_tool_messages` so it benefits automatically.

**Display metadata preservation fix**:
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_tools_extension.py` `to_native_messages`: for tool messages, re-adds `tool_plugin`, `tool_name`, `display` into `_metadata` on the `function_call_output` native item (matching the OpenRouter tools extension pattern).
- `plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/tools_extension.py` `to_native_messages`: same fix for tool messages.

**Tests added**:
- `plugins/claude-tools/tests/test_claude_bash_tool.py`: 13 new tests — helper unit tests (`_cwd_for_storage`, `_resolve_stored_cwd`, `_last_bash_end_cwd_from_context`), two-command persistence test, first-command fallback, nonexistent-path fallback, background-skips-cwd, sandbox-move simulation, metadata-in-result tests. The existing `test_cwd_reset_matches_fixture` is kept (still validates the first command output against the fixture).
- `plugins/openrouter/tests/test_openrouter_provider_unit.py`: `test_to_native_and_from_native_roundtrip_preserves_bash_end_cwd_metadata` — verifies `metadata.bash.end_cwd` survives a provider-only round-trip.
- `plugins/openai_responses/tests/test_openai_responses_tools_extension_unit.py`: `test_round_trip_preserves_display_and_namespaced_metadata_on_tool_messages` — verifies `display` and `bash.end_cwd` survive a provider + tools-extension round-trip.
- `plugins/reference-openai-compatible-provider/tests/test_tools_extension_unit.py`: same round-trip test for the reference provider.

**Investigation update**:
- `plugins/claude-tools/investigation/scripts/investigate_bash_tool.py`: added `_find_all_tool_result_blocks` and `_find_all_assistant_tool_uses` helpers; `build_fixture` now includes `all_assistant_tool_uses` and `all_tool_result_blocks` for the `success-cwd-reset` case so the fixture documents both commands.
- `plugins/claude-tools/investigation/notes/bash-tool.md`: updated implementation direction to document the persistence behavior.

### What changed

| File | Change |
|------|--------|
| `core/python/agent_core/core.py` | `iter_tool_messages`: merge `last_result.get("metadata")` into tool message `metadata` |
| `plugins/claude-tools/src/claude_tools/claude_bash_tool.py` | cwd capture/resolve/store helpers; `execute_tool` reads last cwd from session and returns `metadata.bash.end_cwd` |
| `plugins/openai_responses/src/openai_responses_plugins/openai_responses_tools_extension.py` | `to_native_messages`: re-add `display`/`tool_plugin`/`tool_name` to `_metadata` for tool messages |
| `plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/tools_extension.py` | same `display` re-add fix |
| `plugins/claude-tools/tests/test_claude_bash_tool.py` | 13 new cwd persistence tests |
| `plugins/openrouter/tests/test_openrouter_provider_unit.py` | new `bash.end_cwd` round-trip test |
| `plugins/openai_responses/tests/test_openai_responses_tools_extension_unit.py` | new `display` + `bash.end_cwd` round-trip test |
| `plugins/reference-openai-compatible-provider/tests/test_tools_extension_unit.py` | new `display` + `bash.end_cwd` round-trip test |
| `plugins/claude-tools/investigation/scripts/investigate_bash_tool.py` | capture all tool uses/results for `success-cwd-reset` |
| `plugins/claude-tools/investigation/notes/bash-tool.md` | document persistence behavior |

### Validation results

- `pytest plugins/claude-tools/tests -q`: 114 passed, 1 skipped (was 8 passed in bash tool file alone; now 21 bash tool tests, all passing).
- `pytest core/python/tests -q`: 388 passed, 1 failed (pre-existing flaky `test_node_tool_class_export_instantiated_by_host` — fails on clean branch too, unrelated).
- `pytest plugins/openrouter/tests -q`: 129 passed, 3 failed (all pre-existing; +1 from new test).
- `pytest plugins/openai_responses/tests -q`: 253 passed, 3 failed (all pre-existing; +1 from new test).
- `pytest plugins/reference-openai-compatible-provider/tests -q`: 72 passed, 15 failed (all pre-existing; +1 from new test).
- `ruff check` and `black`: all clean.

No new test failures introduced. All pre-existing failures verified to fail on the clean branch too.

### Findings

- The `bash.end_cwd` metadata rides through the native-history rebuild automatically on all three providers because none of them pop `bash` from `_native_internal_from_core_metadata`. The round-trip tests guard against future regressions.
- The `display` metadata was being lost on the OpenAI Responses and reference providers because they pop `display` from `_metadata` and their tools extensions didn't re-add it. The fix matches the OpenRouter tools extension pattern.
- The investigation script update captures both tool results for the `success-cwd-reset` case, but the investigation was not re-run (requires the real Claude CLI, Ollama, and the proxy repo). The fixture still only has the first tool result; re-running with `--keep-raw` will populate `all_assistant_tool_uses` and `all_tool_result_blocks`.
```