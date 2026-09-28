from __future__ import annotations

from typing import Any

from agent_core.tool_interop import (
    OpenAIResponsesCustomToolSchemaAccessor,
    get_schema_target_formats_from_config,
)
from agent_core.types import ToolPlugin
from embedded_tools_shared import (
    DEFAULT_MAX_PATCH_BYTES,
    PatchError,
    apply_workspace_patch,
    resolve_workspace_root,
)


APPLY_PATCH_GRAMMAR = """start: begin_patch hunk+ end_patch
begin_patch: "*** Begin Patch" LF
end_patch: "*** End Patch" LF?

hunk: add_hunk | delete_hunk | update_hunk
add_hunk: "*** Add File: " filename LF add_line+
delete_hunk: "*** Delete File: " filename LF
update_hunk: "*** Update File: " filename LF change_move? change?

filename: /(.+)/
add_line: "+" /(.*)/ LF -> line

change_move: "*** Move to: " filename LF
change: (change_context | change_line)+ eof_line?
change_context: ("@@" | "@@ " /(.+)/) LF
change_line: ("+" | "-" | " ") /(.*)/ LF
eof_line: "*** End of File" LF

%import common.LF
"""


def _function_schema() -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": "apply_patch",
            "description": (
                "Apply a Codex-style patch to workspace-relative files. The input "
                "must start with `*** Begin Patch` and end with `*** End Patch`."
            ),
            "strict": False,
            "parameters": {
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": "Complete apply_patch text",
                    }
                },
                "required": ["input"],
                "additionalProperties": False,
            },
        },
    }


def _custom_schema() -> dict[str, Any]:
    return {
        "type": "custom",
        "name": "apply_patch",
        "description": (
            "Use apply_patch to edit workspace files. This is a FREEFORM tool; "
            "send the patch directly without wrapping it in JSON."
        ),
        "format": {
            "type": "grammar",
            "syntax": "lark",
            "definition": APPLY_PATCH_GRAMMAR,
        },
    }


def _extract_patch(payload: Any) -> str | None:
    if isinstance(payload, str) and payload.strip():
        return payload
    if isinstance(payload, dict):
        value = payload.get("input")
        if isinstance(value, str) and value.strip():
            return value
    return None


class CodexLikeApplyPatchTool(ToolPlugin):
    name = "embedded_codex_apply_patch"
    version = "0.1.0"

    def init(self, config: dict[str, Any]) -> dict[str, Any]:
        return {
            "config": config,
            "workspace_root": resolve_workspace_root(config),
            "max_patch_bytes": max(
                1024,
                min(
                    int(config.get("max_patch_bytes", DEFAULT_MAX_PATCH_BYTES)),
                    DEFAULT_MAX_PATCH_BYTES,
                ),
            ),
        }

    def get_tool_schemas(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        targets = set(
            get_schema_target_formats_from_config(state.get("config") or {})
        )
        if OpenAIResponsesCustomToolSchemaAccessor.format_id in targets:
            return [_custom_schema()]
        return [_function_schema()]

    def can_handle_tool_call(
        self,
        tool_name: str | None,
        payload: Any,
        state: dict[str, Any],
        **_: Any,
    ) -> bool:
        _ = state
        return tool_name in {None, "apply_patch"} and _extract_patch(payload) is not None

    def format_tool_call_preview(
        self,
        tool_name: str | None,
        payload: Any,
        state: dict[str, Any],
        **_: Any,
    ) -> str:
        _ = tool_name, state
        patch = _extract_patch(payload)
        if patch is None:
            return ""
        operations = [
            line.removeprefix("*** ").strip()
            for line in patch.splitlines()
            if line.startswith(
                ("*** Add File: ", "*** Update File: ", "*** Delete File: ")
            )
        ]
        return "; ".join(operations)

    def execute_tool(
        self,
        tool_name: str | None,
        payload: Any,
        state: dict[str, Any],
        **_: Any,
    ) -> dict[str, Any]:
        if tool_name not in {None, "apply_patch"}:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        patch = _extract_patch(payload)
        if patch is None:
            return {"success": False, "error": "input must be a non-empty string"}
        try:
            result = apply_workspace_patch(
                state["workspace_root"],
                patch,
                max_bytes=state["max_patch_bytes"],
            )
            changes = [
                {
                    "type": change.type,
                    "path": change.path,
                    "move_path": change.move_path,
                }
                for change in result.changes
            ]
            return {
                "success": True,
                "changes": changes,
                "fuzz": result.fuzz,
                "input": patch,
            }
        except (OSError, UnicodeError, PatchError, ValueError) as error:
            return {"success": False, "error": str(error), "input": patch}

    def format_tool_result(
        self,
        result: dict[str, Any],
        state: dict[str, Any],
    ) -> str:
        _ = state
        if not result.get("success"):
            return f"Error applying patch: {result.get('error')}"
        lines = ["Patch applied successfully.", "Changes:"]
        for change in result.get("changes") or []:
            move = change.get("move_path")
            suffix = f" -> {move}" if move else ""
            lines.append(f"- {change.get('type')}: {change.get('path')}{suffix}")
        if result.get("fuzz"):
            lines.append(f"Fuzz factor: {result['fuzz']}")
        return "\n".join(lines)

    def to_display_format(
        self,
        text: str,
        result: dict[str, Any],
        state: dict[str, Any],
    ) -> dict[str, Any]:
        _ = state
        return {
            "type": "text",
            "content": f"{text}\n\nPatch:\n{result.get('input') or ''}",
            "single_line": "\n".join(
                f"{change.get('type')}: {change.get('path')}"
                for change in result.get("changes") or []
            ),
        }