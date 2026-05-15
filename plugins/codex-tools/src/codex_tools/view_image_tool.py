"""Codex view_image tool."""

from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent_core.tool_result_payloads import (
    FORMAT_OPENAI_RESPONSES,
    make_provider_native_tool_result,
)
from agent_core.types import ToolPlugin

from .workdir import resolve_turn_cwd


VIEW_IMAGE_DESCRIPTION = (
    "View a local image from the filesystem (only use if given a full filepath "
    "by the user, and the image isn't already attached to the thread context "
    "within <image ...> tags)."
)
PATH_DESCRIPTION = "Local filesystem path to an image file"
DETAIL_DESCRIPTION = (
    "Optional detail override. The only supported value is `original`; omit "
    "this field for default resized behavior. Use `original` to preserve the "
    "file's original resolution instead of resizing to fit. This is important "
    "when high-fidelity image perception or precise localization is needed, "
    "especially for CUA agents."
)
DEFAULT_IMAGE_DETAIL = "high"
SESSION_ASSET_DOWNLOAD_PLUGIN_ID = "session_asset_attachments"


def _detect_image_mime(data: bytes) -> Optional[str]:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def _resolve_path(raw_path: str, *, working_directory: str) -> Path:
    path = Path(os.path.expanduser(raw_path))
    if not path.is_absolute():
        path = Path(working_directory) / path
    return path.resolve()


def _allowed_roots(config: Dict[str, Any], *, working_directory: str) -> List[Path]:
    raw_allowed = config.get("allowed_paths")
    allowed = raw_allowed if isinstance(raw_allowed, list) and raw_allowed else ["."]
    roots: List[Path] = []
    for item in allowed:
        if not isinstance(item, str) or not item.strip():
            continue
        roots.append(_resolve_path(item, working_directory=working_directory))
    return roots or [Path(working_directory).resolve()]


def _is_within_allowed(path: Path, roots: List[Path]) -> bool:
    for root in roots:
        try:
            path.relative_to(root)
            return True
        except ValueError:
            continue
    return False


def _parameters_schema(*, include_detail: bool) -> Dict[str, Any]:
    properties: Dict[str, Any] = {
        "path": {
            "type": "string",
            "description": PATH_DESCRIPTION,
        }
    }
    if include_detail:
        properties["detail"] = {
            "type": "string",
            "description": DETAIL_DESCRIPTION,
        }
    return {
        "type": "object",
        "properties": properties,
        "required": ["path"],
        "additionalProperties": False,
    }


def _output_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "image_url": {
                "type": "string",
                "description": "Data URL for the loaded image.",
            },
            "detail": {
                "type": ["string", "null"],
                "description": (
                    "Image detail hint returned by view_image. Returns `original` "
                    "when original resolution is preserved, otherwise `null`."
                ),
            },
        },
        "required": ["image_url", "detail"],
        "additionalProperties": False,
    }


def _session_id_from_context(context: Any) -> Optional[str]:
    if not isinstance(context, dict):
        return None
    session_id = context.get("session_id")
    if isinstance(session_id, str) and session_id:
        return session_id
    session = context.get("session")
    if isinstance(session, dict):
        value = session.get("session_id")
        if isinstance(value, str) and value:
            return value
    return None


def _asset_backed_image_part(
    *,
    data: bytes,
    data_base64: str,
    filename: str,
    mime_type: str,
    path: str,
    detail: str,
    context: Any,
) -> Optional[Dict[str, Any]]:
    if not isinstance(context, dict):
        return None
    store = context.get("session_asset_store")
    session_id = _session_id_from_context(context)
    if store is None or not session_id:
        return None

    try:
        record = store.store_base64(
            session_id=session_id,
            attachment_type="image",
            filename=filename,
            mime_type=mime_type,
            data_base64=data_base64,
            metadata={"source_tool": "view_image", "path": path},
        )
    except Exception:
        return None

    return {
        "type": "image",
        "content": {
            "asset_ref": record.asset_ref(),
            "filename": record.filename,
            "mime_type": record.mime_type,
            "preview_data_base64": data_base64,
            "preview_mime_type": mime_type,
        },
        "metadata": {
            "download_plugin_id": SESSION_ASSET_DOWNLOAD_PLUGIN_ID,
            "source_tool": "view_image",
            "detail": detail,
            "path": path,
            "bytes": len(data),
        },
    }


class ViewImageTool(ToolPlugin):
    name: str = "view_image"
    version: str = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "allowed_paths": {
                "type": "array",
                "items": {"type": "string"},
                "default": ["."],
                "description": "Allowed base paths for image loading",
            },
            "working_directory": {
                "type": "string",
                "default": ".",
                "description": "Working directory for resolving relative image paths",
            },
            "enable_view_image_detail_original": {
                "type": "boolean",
                "default": False,
                "description": "Expose and honor view_image.detail='original'",
            },
            "view_image_max_bytes": {
                "type": "integer",
                "default": 10 * 1024 * 1024,
                "description": "Maximum image file size accepted by view_image",
            },
        }

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": config}

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        config = state.get("config") or {}
        include_detail = bool(config.get("enable_view_image_detail_original"))
        return [
            {
                "type": "function",
                "name": "view_image",
                "description": VIEW_IMAGE_DESCRIPTION,
                "strict": False,
                "parameters": _parameters_schema(include_detail=include_detail),
                "output_schema": _output_schema(),
            }
        ]

    def format_tool_call_preview(
        self,
        tool_name: Optional[str],
        payload: Any,
        state: Dict[str, Any],
        **_: Any,
    ) -> str:
        if tool_name != "view_image" or not isinstance(payload, dict):
            return ""
        path = payload.get("path")
        return f"view_image: {path}" if isinstance(path, str) and path else ""

    def execute_tool(
        self,
        tool_name: Optional[str],
        payload: Any,
        state: Dict[str, Any],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        if tool_name != "view_image":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        if not isinstance(payload, dict):
            return {"success": False, "error": "view_image input must be an object"}

        raw_path = payload.get("path")
        if not isinstance(raw_path, str) or not raw_path.strip():
            return {"success": False, "error": "path must be a non-empty string"}

        raw_detail = payload.get("detail")
        if raw_detail is not None and raw_detail != "original":
            return {
                "success": False,
                "error": (
                    "view_image.detail only supports `original`; omit `detail` "
                    f"for default resized behavior, got `{raw_detail}`"
                ),
            }

        config = state.get("config") or {}
        if raw_detail == "original" and not config.get(
            "enable_view_image_detail_original"
        ):
            return {
                "success": False,
                "error": "view_image.detail='original' is unavailable in this configuration",
            }

        working_directory = resolve_turn_cwd(config)
        try:
            image_path = _resolve_path(raw_path, working_directory=working_directory)
        except Exception as exc:
            return {"success": False, "error": f"unable to resolve image path: {exc}"}

        roots = _allowed_roots(config, working_directory=working_directory)
        if not _is_within_allowed(image_path, roots):
            return {"success": False, "error": f"Access denied for path: {raw_path}"}

        if not image_path.exists():
            return {
                "success": False,
                "error": f"unable to locate image at `{image_path}`",
            }
        if not image_path.is_file():
            return {
                "success": False,
                "error": f"image path `{image_path}` is not a file",
            }

        max_bytes = int(config.get("view_image_max_bytes", 10 * 1024 * 1024))
        try:
            size = image_path.stat().st_size
        except OSError as exc:
            return {
                "success": False,
                "error": f"unable to inspect image at `{image_path}`: {exc}",
            }
        if size > max_bytes:
            return {"success": False, "error": f"Image too large (>{max_bytes} bytes)"}

        try:
            data = image_path.read_bytes()
        except OSError as exc:
            return {
                "success": False,
                "error": f"unable to read image at `{image_path}`: {exc}",
            }

        mime_type = _detect_image_mime(data)
        if mime_type is None:
            return {
                "success": False,
                "error": f"unable to process image at `{image_path}`: unsupported image format",
            }

        data_base64 = base64.b64encode(data).decode("ascii")
        image_url = f"data:{mime_type};base64,{data_base64}"
        detail = "original" if raw_detail == "original" else DEFAULT_IMAGE_DETAIL
        path = str(image_path)
        asset_part = _asset_backed_image_part(
            data=data,
            data_base64=data_base64,
            filename=image_path.name,
            mime_type=mime_type,
            path=path,
            detail=detail,
            context=kwargs.get("context"),
        )
        display_content = (
            asset_part.get("content")
            if isinstance(asset_part, dict)
            else {
                "url": image_url,
                "filename": image_path.name,
                "mime_type": mime_type,
            }
        )
        tool_result_image_payload: Any = (
            {
                "asset_ref": display_content.get("asset_ref"),
                "filename": display_content.get("filename"),
                "mime_type": display_content.get("mime_type"),
            }
            if isinstance(display_content, dict)
            and isinstance(display_content.get("asset_ref"), dict)
            else image_url
        )
        return {
            "success": True,
            "message": f"Loaded image file `{path}` ({mime_type}, {len(data)} bytes).",
            "image_url": image_url,
            "detail": detail,
            "path": path,
            "mime_type": mime_type,
            "filename": image_path.name,
            "bytes": len(data),
            "display_content": display_content,
            "tool_result_image_payload": tool_result_image_payload,
        }

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> Any:
        if not result.get("success"):
            return f"Error: {result.get('error')}"
        message = str(result.get("message") or "")
        image_payload = result.get("tool_result_image_payload")
        if image_payload is None:
            image_payload = result.get("image_url") or ""
        return make_provider_native_tool_result(
            format=FORMAT_OPENAI_RESPONSES,
            output=[
                {"type": "input_text", "text": message},
                {
                    "type": "input_image",
                    "image_url": image_payload,
                    "detail": result.get("detail"),
                },
            ],
            text=message,
        )

    def to_display_format(
        self,
        text: str,
        result: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        if not result.get("success"):
            return {"type": "text", "content": text}
        path = str(result.get("path") or "")
        return {
            "type": "image",
            "content": result.get("display_content") or {"url": result.get("image_url") or ""},
            "mime_type": result.get("mime_type"),
            "path": path,
            "single_line": f"view_image: {Path(path).name if path else 'image'}",
            "content_text": str(result.get("message") or text),
            "text_fallback": text or str(result.get("message") or ""),
            "metadata": {
                "download_plugin_id": SESSION_ASSET_DOWNLOAD_PLUGIN_ID,
                "detail": result.get("detail"),
            },
        }


__all__ = ["ViewImageTool"]
