**How `execute_tool`, `stream_tool`, and `to_display_format` work today**

- **`ToolPlugin.execute_tool` (core contract)**
    - Called by the tool wrapper (`ToolWrapper.execute_tool`) for a single, non‑streaming tool invocation.
    - Signature: `execute_tool(self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]`.
    - Expected to return a **result dict** like `{"success": bool, "result": <any>, "error": <str>, ...}`.
    - In `ApplyPatchTool.execute_tool`:
        - Validates `tool_name == "apply_patch"`.
        - Validates `patch_text` is a non‑empty string and within `max_patch_bytes`.
        - Calls `_process_patch_sandboxed`, which:
            - Resolves and validates paths (`working_directory`, `allowed_paths`).
            - Reads existing files, parses the Codex‑style patch, builds and applies a `Commit`.
        - On success returns:
          ```python
          {
              "success": True,
              "result": "Done!",
              "fuzz": <int>,
              "changes": {path: {"type": "add|update|delete", "move_path": ...}, ...},
          }
          ```
        - On failure returns `{"success": False, "error": "..."}`
          (currently without including the original patch text).

- **`ToolPlugin.stream_tool` (tool‑side streaming)**
    - Signature: `stream_tool(self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]) -> Iterator[Dict[str, Any]]`.
    - **Adapter behavior** (`ToolPluginAdapter.stream_tool`):
        - If the plugin does **not** implement `stream_tool`, the adapter:
            - Calls `execute_tool(...)` once and yields that single RESULT dict.
            - This means *all* tools effectively support the streaming pipeline, even if they’re logically non‑streaming.
        - If the plugin **does** implement `stream_tool` (e.g. `ShellTool`), the adapter:
            - Iterates the plugin’s iterator and forwards any dict chunks it yields.
    - **How core uses it** (`AgentCore.iter_tool_messages`):
        - For each tool call, core does `iterator = tool.stream_tool(name, args, state)` and iterates:
            - If a chunk has `"success"`: it’s treated as the **final RESULT dict**; the last one becomes `last_result`.
            - If a chunk has `"part"`: it’s treated as a **partial display payload** and yielded straight through.
            - Any other dict is wrapped as `{"part": chunk}` for backwards compatibility.
        - If no RESULT dict was ever seen, core synthesizes an error `tool` message like `Error: no tool handled 'name'`.

- **`ToolPlugin.format_tool_result` (LLM‑visible text)**
    - Signature: `format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str`.
    - Called once per tool call **after** streaming completes, with `last_result`.
    - Default adapter behavior: if not overridden, formats as `"Result: ..." / "Error: ..."` from `result`.
    - In `ApplyPatchTool.format_tool_result`:
        - On success:
            - Returns a multi‑line summary string:
                - `"Patch applied successfully."`
                - Optional `"Fuzz factor: N"` when `fuzz > 0`.
                - `"Changes:"` followed by `- add|update|delete: path [-> move_path]` lines.
        - On failure:
            - Returns `"Error applying patch: {error}"`.
        - This **string becomes the `content` of the core `tool` message** that the LLM sees in the conversation.

- **`ToolPlugin.to_display_format` (UI‑only display payload)**
    - Signature: `to_display_format(self, text: str, result: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]`.
        - `text` is exactly the string from `format_tool_result`.
        - `result` is the full RESULT dict from `execute_tool` / `stream_tool`.
    - Default implementations:
        - In `ToolPlugin` (protocol): returns `{"type": "text", "content": text}`.
        - In the adapter (`ToolPluginAdapter.to_display_format`): if the plugin doesn't override this, also wraps `text` in a `{"type": "text"}` payload.
    - How core uses it (`AgentCore.iter_tool_messages`):
        - After formatting, core calls:
          ```python
          display = tool.to_display_format(formatted_content or "", last_result, state)
          ```
          and, if it gets a dict, attaches it as `metadata["display"]` on the final `tool` message.
    - How the terminal uses it (`ToolRenderer` in `event_rendering.py`):
        - For stored/rendered tool messages:
            - If `metadata.display` is a dict with `type == "text"`, it uses `display["content"]` as the printed tool output.
            - Otherwise it falls back to `message["content"]` (the `format_tool_result` text).
        - This means:
            - `format_tool_result` controls what the **LLM** sees as the tool message content.
            - `to_display_format` controls what **humans** see in the UI for that tool call.
    - **Single-line display support:**
        - Tools can include an optional `"single_line"` field in the returned display dict to provide a compact summary for collapsed/short views.
        - Format: `{"type": "text", "content": <full_content>, "single_line": <compact_summary>}`
        - The `single_line` field should contain a brief, one-line (or multi-line if needed) preview suitable for:
            - Terminal `/list short` command output
            - Mobile app collapsed tool result headers
            - Any UI that shows tool results in a compact format
        - Examples:
            - **Shell tool**: `"single_line": "ls -la"` (just the command, first line if multi-line)
            - **Apply patch tool**: `"single_line": "add: file1.py\nupdate: file2.py"` (list of changed files)
        - When `single_line` is present, UIs should prefer it over `content` when rendering collapsed/short views.
        - When expanded, UIs should always use `content` for the full tool result.
    - Concrete example (`ShellTool.to_display_format`):
        - `execute_tool` / `stream_tool` attach `"command"` and `"workdir"` to the result dict.
        - `to_display_format` reads those and prepends a multi‑line header:
            - `Workdir: /path` (when explicitly overridden)
            - `Command executed: <cmd>`
            - `Output:`
        - Then appends the `text` from `format_tool_result`.
        - Also includes `"single_line": <first_line_of_command>` for compact views.
        - The UI shows command + workdir + output, but the raw tool message `content` (seen by the LLM) is just the formatted stdout/stderr.

- **Documentation gap identified**
    - `docs/plugins/development.md`’s **Tool Plugin** section currently documents only:
        - `init`, `get_tool_schemas`, `execute_tool`, `format_tool_result`.
    - It **does not mention**:
        - `stream_tool(tool_name, arguments, state) -> Iterator[dict]` for streaming tools.
        - `to_display_format(text, result, state) -> dict` for display‑only payloads (e.g. showing commands or patches).
    - AGENTS.md and the actual type definitions (`ToolPlugin` in `agent_core/types.py` and adapters) clearly support and expect these optional hooks, so the plugin dev guide is incomplete here.
