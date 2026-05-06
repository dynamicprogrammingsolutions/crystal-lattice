from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

from agent_core.tool_result_payloads import (
    FORMAT_OPENAI_CHAT_COMPLETIONS,
    make_provider_native_tool_result,
)
from agent_core.types import ToolPlugin
from tool_compat_shared import (
    MEDIA_SNIFF_BYTES,
    detect_media_file_type,
    extract_image_size,
    media_data_url,
    resolve_path,
    validate_path_within_directories,
)


MAX_MEDIA_BYTES = 100 * 1024 * 1024
READ_BACK_NOTE = (
    "If you need to output coordinates, output relative coordinates first and "
    "compute absolute coordinates using the original image size; if you generate or "
    "edit images/videos via commands or scripts, read the result back immediately "
    "before continuing."
)
PATH_DESCRIPTION = (
    "The path to the file to read. Absolute paths are required when reading files "
    "outside the working directory."
)


def _normalize_capabilities(raw: Any) -> set[str]:
    if raw is None:
        return {"image_in"}
    if isinstance(raw, str):
        return {raw}
    if isinstance(raw, (list, tuple, set)):
        return {str(item) for item in raw if isinstance(item, str)}
    return set()


def _description(capabilities: set[str]) -> str:
    lines = [
        "Read media content from a file.",
        "",
        "**Tips:**",
        "- Make sure you follow the description of each tool parameter.",
        "- A `<system>` tag will be given before the read file content.",
        "- The system will notify you when there is anything wrong when reading the file.",
        "- This tool is a tool that you typically want to use in parallel. Always read multiple files in one response when possible.",
        "- This tool can only read image or video files. To read other types of files, use the ReadFile tool. To list directories, use the Glob tool or `ls` command via the Shell tool.",
        "- If the file doesn't exist or path is invalid, an error will be returned.",
        f"- The maximum size that can be read is {MAX_MEDIA_BYTES // (1024 * 1024)}MB. An error will be returned if the file is larger than this limit.",
        "- The media content will be returned in a form that you can directly view and understand.",
        "",
        "**Capabilities**",
    ]
    if {"image_in", "video_in"}.issubset(capabilities):
        lines.append(
            "- This tool supports image and video files for the current model."
        )
    elif "image_in" in capabilities:
        lines.extend(
            [
                "- This tool supports image files for the current model.",
                "- Video files are not supported by the current model.",
            ]
        )
    elif "video_in" in capabilities:
        lines.extend(
            [
                "- This tool supports video files for the current model.",
                "- Image files are not supported by the current model.",
            ]
        )
    else:
        lines.append("- The current model does not support image or video input.")
    return "\n".join(lines)


class KimiReadMediaFileTool(ToolPlugin):
    name = "kimi_read_media_file_tool"
    version = "0.1.0"

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        working_directory = str(config.get("working_directory") or os.getcwd())
        workspace_dirs = config.get("allowed_paths") or [working_directory]
        max_bytes = config.get("kimi_read_media_max_bytes", MAX_MEDIA_BYTES)
        try:
            max_bytes = int(max_bytes)
        except (TypeError, ValueError):
            max_bytes = MAX_MEDIA_BYTES
        return {
            "working_directory": working_directory,
            "workspace_dirs": [
                str(Path(p).resolve()) for p in workspace_dirs if isinstance(p, str)
            ],
            "capabilities": _normalize_capabilities(
                config.get("kimi_read_media_capabilities")
            ),
            "max_bytes": max_bytes,
        }

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        capabilities = state.get("capabilities")
        if not isinstance(capabilities, set):
            capabilities = set()
        if "image_in" not in capabilities and "video_in" not in capabilities:
            return []
        return [
            {
                "type": "function",
                "function": {
                    "name": "ReadMediaFile",
                    "description": _description(capabilities),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": PATH_DESCRIPTION,
                            }
                        },
                        "required": ["path"],
                    },
                },
            }
        ]

    def format_tool_call_preview(
        self,
        tool_name: str | None,
        payload: Any,
        state: Dict[str, Any],
        **_: Any,
    ) -> str:
        if tool_name != "ReadMediaFile" or not isinstance(payload, dict):
            return ""
        path = payload.get("path")
        return f"ReadMediaFile: {path}" if isinstance(path, str) and path else ""

    def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        if tool_name != "ReadMediaFile":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

        raw_path = arguments.get("path") if isinstance(arguments, dict) else None
        if not isinstance(raw_path, str) or not raw_path.strip():
            return {"success": False, "error": "File path cannot be empty."}

        working_directory = state["working_directory"]
        resolved = resolve_path(
            raw_path, working_directory=working_directory, allow_relative=True
        )
        allowed_dirs = list(state["workspace_dirs"])

        if not os.path.isabs(raw_path) and not validate_path_within_directories(
            resolved, allowed_dirs
        ):
            return {
                "success": False,
                "error": (
                    f"`{raw_path}` is not an absolute path. "
                    "You must provide an absolute path to read a file "
                    "outside the working directory."
                ),
                "brief": "Invalid path",
            }

        target = Path(resolved)
        if not target.exists():
            return {
                "success": False,
                "error": f"`{raw_path}` does not exist.",
                "brief": "File not found",
            }
        if not target.is_file():
            return {
                "success": False,
                "error": f"`{raw_path}` is not a file.",
                "brief": "Invalid path",
            }

        try:
            size = target.stat().st_size
        except OSError as exc:
            return {
                "success": False,
                "error": f"Failed to read {raw_path}. Error: {exc}",
                "brief": "Failed to read file",
            }
        if size == 0:
            return {
                "success": False,
                "error": f"`{raw_path}` is empty.",
                "brief": "Empty file",
            }

        max_bytes = int(state.get("max_bytes", MAX_MEDIA_BYTES))
        if size > max_bytes:
            return {
                "success": False,
                "error": (
                    f"`{raw_path}` is {size} bytes, which exceeds the max "
                    f"{max_bytes // (1024 * 1024)}MB bytes for media files."
                ),
                "brief": "File too large",
            }

        try:
            with target.open("rb") as handle:
                header = handle.read(MEDIA_SNIFF_BYTES)
            file_type = detect_media_file_type(target, header=header)
        except OSError as exc:
            return {
                "success": False,
                "error": f"Failed to read {raw_path}. Error: {exc}",
                "brief": "Failed to read file",
            }

        if file_type.kind == "text":
            return {
                "success": False,
                "error": f"`{raw_path}` is a text file. Use ReadFile to read text files.",
                "brief": "Unsupported file type",
            }
        if file_type.kind == "unknown":
            return {
                "success": False,
                "error": (
                    f"`{raw_path}` seems not readable as an image or video file. "
                    "You may need to read it with proper shell commands, Python tools "
                    "or MCP tools if available. "
                    "If you read/operate it with Python, you MUST ensure that any "
                    "third-party packages are installed in a virtual environment (venv)."
                ),
                "brief": "File not readable",
            }

        capabilities = state.get("capabilities")
        if not isinstance(capabilities, set):
            capabilities = set()
        if file_type.kind == "image" and "image_in" not in capabilities:
            return {
                "success": False,
                "error": (
                    "The current model does not support image input. "
                    "Tell the user to use a model with image input capability."
                ),
                "brief": "Unsupported media type",
            }
        if file_type.kind == "video" and "video_in" not in capabilities:
            return {
                "success": False,
                "error": (
                    "The current model does not support video input. "
                    "Tell the user to use a model with video input capability."
                ),
                "brief": "Unsupported media type",
            }

        if file_type.kind == "video":
            return {
                "success": False,
                "error": "Video media output is not yet supported by this plugin.",
                "brief": "Unsupported media type",
            }

        try:
            data = target.read_bytes()
        except OSError as exc:
            return {
                "success": False,
                "error": f"Failed to read {raw_path}. Error: {exc}",
                "brief": "Failed to read file",
            }

        data_url = media_data_url(file_type.mime_type, data)
        image_size = extract_image_size(data)
        size_hint = (
            f", original size {image_size[0]}x{image_size[1]}px" if image_size else ""
        )
        message = (
            f"Loaded image file `{target}` ({file_type.mime_type}, {len(data)} bytes{size_hint}). "
            f"{READ_BACK_NOTE}"
        )
        return {
            "success": True,
            "kind": "image",
            "path": str(target),
            "mime_type": file_type.mime_type,
            "bytes": len(data),
            "image_url": data_url,
            "width": image_size[0] if image_size else None,
            "height": image_size[1] if image_size else None,
            "message": message,
            "tool_output_content": [
                {
                    "type": "input_image",
                    "image_url": data_url,
                }
            ],
            "multipartContent": [
                {
                    "type": "image",
                    "content": {"url": data_url},
                    "metadata": {"path": str(target), "mime_type": file_type.mime_type},
                }
            ],
        }

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> Any:
        if result.get("success") is not True:
            return f"Error: {result.get('error')}"

        path = str(result.get("path") or "")
        content = [
            {
                "type": "text",
                "text": (
                    f"<system>\n{result.get('message') or ''}\n</system>\n"
                    f'<image path="{path}">'
                ),
            },
            {
                "type": "image_url",
                "image_url": {"url": result.get("image_url") or ""},
            },
            {"type": "text", "text": "</image>"},
        ]
        return make_provider_native_tool_result(
            format=FORMAT_OPENAI_CHAT_COMPLETIONS,
            content=content,
        )

    def to_display_format(
        self,
        text: str,
        result: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        if result.get("success") is not True:
            return {"type": "text", "content": text}
        path = str(result.get("path") or "")
        return {
            "type": "image",
            "content": result.get("image_url") or "",
            "mime_type": result.get("mime_type"),
            "path": path,
            "single_line": f"ReadMediaFile: {Path(path).name if path else 'image'}",
            "text_fallback": text or str(result.get("message") or ""),
        }


__all__ = ["KimiReadMediaFileTool"]
