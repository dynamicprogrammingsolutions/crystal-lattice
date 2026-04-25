"""ApplyPatchTool plugin: Codex-style apply_patch file editing."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from agent_core.types import ToolPlugin

from .apply_patch_runtime import (
    apply_patch_display,
    execute_apply_patch_text,
    extract_patch_text,
    format_apply_patch_result,
    select_apply_patch_schemas,
    summarize_patch_text,
)


class ApplyPatchTool(ToolPlugin):
    name: str = "apply_patch"
    version: str = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "allowed_paths": {
                "type": "array",
                "items": {"type": "string"},
                "default": ["."],
                "description": "Allowed base paths for patch application",
            },
            "working_directory": {
                "type": "string",
                "default": ".",
                "description": "Working directory for resolving relative file paths in patches",
            },
            "max_patch_bytes": {
                "type": "integer",
                "default": 2 * 1024 * 1024,
                "description": "Maximum patch size (in bytes) that will be accepted",
            },
        }

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        return []

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": config}

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return select_apply_patch_schemas(state.get("config") or {})

    def can_handle_tool_call(
        self,
        tool_name: Optional[str],
        payload: Any,
        state: Dict[str, Any],
        *,
        payload_kind: Optional[str] = None,
        payload_format: Optional[str] = None,
        payload_metadata: Optional[Dict[str, Any]] = None,
        tool_call: Optional[Dict[str, Any]] = None,
        tool_schema: Optional[Dict[str, Any]] = None,
    ) -> Optional[bool]:
        if tool_name not in {None, "apply_patch"}:
            return False
        patch_text, _error = extract_patch_text(payload, payload_kind=payload_kind)
        return patch_text is not None

    def format_tool_call_preview(
        self,
        tool_name: Optional[str],
        payload: Any,
        state: Dict[str, Any],
        *,
        payload_kind: Optional[str] = None,
        payload_format: Optional[str] = None,
        payload_metadata: Optional[Dict[str, Any]] = None,
        tool_call: Optional[Dict[str, Any]] = None,
    ) -> str:
        if tool_name not in {None, "apply_patch"}:
            return ""
        patch_text, _error = extract_patch_text(payload, payload_kind=payload_kind)
        if patch_text is None:
            return ""
        return summarize_patch_text(patch_text)

    def execute_tool(
        self,
        tool_name: Optional[str],
        payload: Any,
        state: Dict[str, Any],
        *,
        payload_kind: Optional[str] = None,
        payload_format: Optional[str] = None,
        payload_metadata: Optional[Dict[str, Any]] = None,
        tool_call: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if tool_name not in {None, "apply_patch"}:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

        patch_text, error = extract_patch_text(payload, payload_kind=payload_kind)
        if patch_text is None:
            return {"success": False, "error": error or "input must be a non-empty string"}

        return execute_apply_patch_text(
            patch_text,
            config=state.get("config") or {},
        )

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        return format_apply_patch_result(result)

    def to_display_format(
        self,
        text: str,
        result: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        return apply_patch_display(text, result)