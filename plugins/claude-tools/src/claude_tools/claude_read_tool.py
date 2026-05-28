# Licensing note:
# This file may contain both original code authored for this repository and
# material derived from or adapted from Claude Code or other
# Anthropic-authored materials.
#
# Original code in this file authored for this repository is licensed under
# the Apache License, Version 2.0.
#
# Copyright 2026 Dynamic Programming Solutions Kft.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Anthropic-derived material in this file is not licensed by us under
# Apache-2.0, and are instead subject to Anthropic's terms:
#
# © Anthropic PBC. All rights reserved. Use is subject to Anthropic's
# Commercial Terms of Service:
# https://www.anthropic.com/legal/commercial-terms

from __future__ import annotations

import base64
import json
import mimetypes
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent_core.tool_result_payloads import (
    FORMAT_ANTHROPIC_MESSAGES,
    make_provider_native_tool_result,
)
from agent_core.types import ToolPlugin
from tool_compat_shared import read_file_with_encoding

from .interop import claude_tool_interop_contribution


READ_DESCRIPTION = (
    "Reads a file from the local filesystem. You can access any file directly by using this tool.\n"
    "Assume this tool is able to read all files on the machine. If the User provides a path to a file assume that path is valid. It is okay to read a file that does not exist; an error will be returned.\n\n"
    "Usage:\n"
    "- The file_path parameter must be an absolute path, not a relative path\n"
    "- By default, it reads up to 2000 lines starting from the beginning of the file\n"
    "- You can optionally specify a line offset and limit (especially handy for long files), but it's recommended to read the whole file by not providing these parameters\n"
    "- Results are returned using cat -n format, with line numbers starting at 1\n"
    "- This tool allows Claude Code to read images (eg PNG, JPG, etc). When reading an image file the contents are presented visually as Claude Code is a multimodal LLM.\n"
    '- This tool can read PDF files (.pdf). For large PDFs (more than 10 pages), you MUST provide the pages parameter to read specific page ranges (e.g., pages: "1-5"). Reading a large PDF without the pages parameter will fail. Maximum 20 pages per request.\n'
    "- This tool can read Jupyter notebooks (.ipynb files) and returns all cells with their outputs, combining code, text, and visualizations.\n"
    "- This tool can only read files, not directories. To list files in a directory, use the registered shell tool.\n"
    "- You will regularly be asked to read screenshots. If the user provides a path to a screenshot, ALWAYS use this tool to view the file at the path. This tool will work with all temporary file paths.\n"
    "- If you read a file that exists but has empty contents you will receive a system reminder warning in place of file contents."
)

READ_SCHEMA: Dict[str, Any] = {
    "name": "Read",
    "description": READ_DESCRIPTION,
    "input_schema": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": {
            "file_path": {
                "description": "The absolute path to the file to read",
                "type": "string",
            },
            "limit": {
                "description": "The number of lines to read. Only provide if the file is too large to read at once.",
                "exclusiveMinimum": 0,
                "maximum": 9007199254740991,
                "type": "integer",
            },
            "offset": {
                "description": "The line number to start reading from. Only provide if the file is too large to read at once",
                "maximum": 9007199254740991,
                "minimum": 0,
                "type": "integer",
            },
            "pages": {
                "description": 'Page range for PDF files (e.g., "1-5", "3", "10-20"). Only applicable to PDF files. Maximum 20 pages per request.',
                "type": "string",
            },
        },
        "required": ["file_path"],
        "type": "object",
    },
}

DEFAULT_LINE_LIMIT = 2000
MAX_FULL_READ_BYTES = 256 * 1024
MAX_PDF_PAGES_WITHOUT_RANGE = 10
MAX_PDF_PAGES_PER_REQUEST = 20


def _resolve_path(raw_path: str, *, working_directory: str) -> Path:
    path = Path(os.path.expanduser(raw_path))
    if not path.is_absolute():
        path = Path(working_directory) / path
    return path.resolve()


def _allowed_roots(config: Dict[str, Any], *, working_directory: str) -> List[Path]:
    raw_allowed = config.get("allowed_paths")
    values = (
        raw_allowed
        if isinstance(raw_allowed, list) and raw_allowed
        else [working_directory]
    )
    roots = []
    for item in values:
        if isinstance(item, str) and item.strip():
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


def _detect_image_mime(data: bytes, path: Path) -> Optional[str]:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    mime_type, _encoding = mimetypes.guess_type(str(path))
    if isinstance(mime_type, str) and mime_type.startswith("image/"):
        return mime_type
    return None


def _format_large_size(size: int) -> str:
    if size < 1024:
        return f"{size} bytes"
    return f"{size / 1024:.1f}KB"


def _format_file_size(size: int) -> str:
    if size < 1024:
        return f"{size} bytes"
    kb = max(1, round(size / 1024))
    return f"{kb}KB"


def _tool_result_block(
    tool_use_id: str,
    content: Any,
    *,
    is_error: bool = False,
    cache_control: bool = True,
) -> Dict[str, Any]:
    block: Dict[str, Any] = {
        "type": "tool_result",
        "tool_use_id": tool_use_id,
        "content": content,
    }
    if is_error:
        block["is_error"] = True
    if cache_control:
        block["cache_control"] = {"type": "ephemeral"}
    return block


def _image_block(
    data: bytes, media_type: str, *, cache_control: bool = False
) -> Dict[str, Any]:
    block: Dict[str, Any] = {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": media_type,
            "data": base64.b64encode(data).decode("ascii"),
        },
    }
    if cache_control:
        block["cache_control"] = {"type": "ephemeral"}
    return block


def _parse_pdf_pages(pages: str) -> tuple[int, int] | None:
    value = pages.strip()
    if not value:
        return None
    match = re.fullmatch(r"(\d+)(?:\s*-\s*(\d+))?", value)
    if not match:
        return None
    start = int(match.group(1))
    end = int(match.group(2) or match.group(1))
    if start < 1 or end < start:
        return None
    if end - start + 1 > MAX_PDF_PAGES_PER_REQUEST:
        return None
    return start, end


def _pdf_page_count(path: Path) -> Optional[int]:
    pdfinfo = shutil.which("pdfinfo")
    if not pdfinfo:
        return None
    try:
        completed = subprocess.run(
            [pdfinfo, str(path)],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception:
        return None
    for line in completed.stdout.splitlines():
        if line.startswith("Pages:"):
            try:
                return int(line.split(":", 1)[1].strip())
            except ValueError:
                return None
    return None


def _notebook_text(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    cells = data.get("cells")
    if not isinstance(cells, list):
        return ""
    parts: List[str] = []
    for index, cell in enumerate(cells):
        if not isinstance(cell, dict):
            continue
        cell_type = cell.get("cell_type")
        source = cell.get("source")
        source_text = "".join(source) if isinstance(source, list) else str(source or "")
        parts.append(f'<cell id="cell-{index}">')
        if cell_type == "markdown":
            parts.append("<cell_type>markdown</cell_type>")
        parts.append(source_text)
        parts.append(f'</cell id="cell-{index}">\n')
        outputs = cell.get("outputs")
        if isinstance(outputs, list):
            for output in outputs:
                if not isinstance(output, dict):
                    continue
                text = output.get("text")
                if isinstance(text, list):
                    parts.append("".join(str(item) for item in text))
                elif isinstance(text, str):
                    parts.append(text)
    return "".join(parts)


class ClaudeReadTool(ToolPlugin):
    name = "claude_read_tool"
    version = "0.1.0"

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        working_directory = str(config.get("working_directory") or os.getcwd())
        return {
            "config": config,
            "working_directory": working_directory,
            "allowed_roots": _allowed_roots(
                config, working_directory=working_directory
            ),
        }

    def get_tool_interop_contribution(self, state: Dict[str, Any]):
        return claude_tool_interop_contribution()

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [READ_SCHEMA]

    def can_handle_tool_call(
        self,
        tool_name: Optional[str],
        payload: Any,
        state: Dict[str, Any],
        **_: Any,
    ) -> Optional[bool]:
        return tool_name == "Read"

    def _result(
        self,
        *,
        tool_use_id: str,
        content: List[Dict[str, Any]],
        text: str = "",
        success: bool = True,
        path: Optional[str] = None,
        kind: str = "text",
        display_content: Any = None,
    ) -> Dict[str, Any]:
        return {
            "success": success,
            "anthropic_content": content,
            "text": text,
            "path": path,
            "kind": kind,
            "display_content": display_content,
            "tool_use_id": tool_use_id,
        }

    def _error(
        self, tool_use_id: str, message: str, *, path: Optional[str] = None
    ) -> Dict[str, Any]:
        return self._result(
            tool_use_id=tool_use_id,
            content=[_tool_result_block(tool_use_id, message, is_error=True)],
            text=message,
            success=False,
            path=path,
        )

    def _read_image(self, path: Path, tool_use_id: str) -> Dict[str, Any]:
        data = path.read_bytes()
        media_type = _detect_image_mime(data, path) or "application/octet-stream"
        image = _image_block(data, media_type)
        data_url = f"data:{media_type};base64,{base64.b64encode(data).decode('ascii')}"
        return self._result(
            tool_use_id=tool_use_id,
            content=[_tool_result_block(tool_use_id, [image])],
            text="",
            path=str(path),
            kind="image",
            display_content={
                "url": data_url,
                "filename": path.name,
                "mime_type": media_type,
            },
        )

    def _read_pdf(
        self, path: Path, tool_use_id: str, pages: Optional[str]
    ) -> Dict[str, Any]:
        size_text = _format_file_size(path.stat().st_size)
        page_count = _pdf_page_count(path)
        if not pages:
            if isinstance(page_count, int) and page_count > MAX_PDF_PAGES_WITHOUT_RANGE:
                message = (
                    f"This PDF has {page_count} pages, which is too many to read at once. "
                    'Use the pages parameter to read specific page ranges (e.g., pages: "1-5"). '
                    "Maximum 20 pages per request."
                )
                return self._error(tool_use_id, message, path=str(path))
            message = f"PDF file read: {path} ({size_text})"
            return self._result(
                tool_use_id=tool_use_id,
                content=[_tool_result_block(tool_use_id, message, cache_control=False)],
                text=message,
                path=str(path),
                kind="pdf",
            )

        page_range = _parse_pdf_pages(pages)
        if page_range is None:
            return self._error(tool_use_id, "Invalid pages parameter.", path=str(path))
        pdftoppm = shutil.which("pdftoppm")
        if not pdftoppm:
            return self._error(
                tool_use_id,
                "pdftoppm is not installed. Install poppler-utils (e.g. `brew install poppler` or `apt-get install poppler-utils`) to enable PDF page rendering.",
                path=str(path),
            )

        start, end = page_range
        with tempfile.TemporaryDirectory(prefix="claude-read-pdf-") as tmpdir:
            prefix = str(Path(tmpdir) / "page")
            subprocess.run(
                [
                    pdftoppm,
                    "-jpeg",
                    "-f",
                    str(start),
                    "-l",
                    str(end),
                    str(path),
                    prefix,
                ],
                check=True,
                capture_output=True,
                timeout=30,
            )
            images = sorted(Path(tmpdir).glob("page-*.jpg"))
            message = (
                f"PDF pages extracted: {len(images)} page(s) from {path} ({size_text})"
            )
            content: List[Dict[str, Any]] = [
                _tool_result_block(tool_use_id, message, cache_control=False)
            ]
            for index, image_path in enumerate(images):
                content.append(
                    _image_block(
                        image_path.read_bytes(),
                        "image/jpeg",
                        cache_control=index == len(images) - 1,
                    )
                )
            return self._result(
                tool_use_id=tool_use_id,
                content=content,
                text=message,
                path=str(path),
                kind="pdf",
            )

    def _read_notebook(self, path: Path, tool_use_id: str) -> Dict[str, Any]:
        text = _notebook_text(path)
        return self._result(
            tool_use_id=tool_use_id,
            content=[_tool_result_block(tool_use_id, [{"type": "text", "text": text}])],
            text=text,
            path=str(path),
            kind="notebook",
        )

    def _read_text(
        self,
        path: Path,
        tool_use_id: str,
        *,
        offset: Optional[int],
        limit: Optional[int],
    ) -> Dict[str, Any]:
        size = path.stat().st_size
        if offset is None and limit is None and size > MAX_FULL_READ_BYTES:
            message = (
                f"File content ({_format_large_size(size)}) exceeds maximum allowed size (256KB). "
                "Use offset and limit parameters to read specific portions of the file, "
                "or search for specific content instead of reading the whole file."
            )
            return self._error(tool_use_id, message, path=str(path))

        text = read_file_with_encoding(path)
        lines = text.split("\n")
        if text == "":
            message = (
                "<system-reminder>Warning: the file exists but is shorter than the provided offset (1). "
                "The file has 1 lines.</system-reminder>"
            )
            return self._result(
                tool_use_id=tool_use_id,
                content=[_tool_result_block(tool_use_id, message)],
                text=message,
                path=str(path),
            )

        start_line = offset if isinstance(offset, int) else 1
        start_index = max(start_line - 1, 0)
        effective_limit = limit if isinstance(limit, int) else DEFAULT_LINE_LIMIT
        selected = lines[start_index : start_index + effective_limit]
        if not selected:
            message = (
                f"<system-reminder>Warning: the file exists but is shorter than the provided offset ({start_line}). "
                f"The file has {len(lines)} lines.</system-reminder>"
            )
            return self._result(
                tool_use_id=tool_use_id,
                content=[_tool_result_block(tool_use_id, message)],
                text=message,
                path=str(path),
            )
        body = "\n".join(
            f"{start_index + index + 1}\t{line}" for index, line in enumerate(selected)
        )
        return self._result(
            tool_use_id=tool_use_id,
            content=[_tool_result_block(tool_use_id, body)],
            text=body,
            path=str(path),
        )

    def execute_tool(
        self,
        tool_name: Optional[str],
        payload: Any,
        state: Dict[str, Any],
        *,
        tool_call: Optional[Dict[str, Any]] = None,
        **_: Any,
    ) -> Dict[str, Any]:
        if tool_name != "Read":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        if not isinstance(payload, dict):
            return {"success": False, "error": "Read input must be an object"}

        raw_path = payload.get("file_path")
        if not isinstance(raw_path, str) or not raw_path.strip():
            return {"success": False, "error": "file_path must be a non-empty string"}

        tool_use_id = "call_Read"
        if isinstance(tool_call, dict):
            raw_id = tool_call.get("id")
            if isinstance(raw_id, str) and raw_id:
                tool_use_id = raw_id

        working_directory = str(state.get("working_directory") or os.getcwd())
        try:
            path = _resolve_path(raw_path, working_directory=working_directory)
        except Exception as exc:
            return self._error(tool_use_id, f"Unable to resolve path: {exc}")

        allowed_roots = state.get("allowed_roots")
        roots = allowed_roots if isinstance(allowed_roots, list) else []
        if roots and not _is_within_allowed(path, roots):
            return self._error(
                tool_use_id, f"Access denied for path: {raw_path}", path=str(path)
            )

        if not path.exists():
            return self._error(
                tool_use_id,
                f"File does not exist. Note: your current working directory is {working_directory}.",
                path=str(path),
            )
        if path.is_dir():
            return self._error(
                tool_use_id,
                f"EISDIR: illegal operation on a directory, read '{path}'",
                path=str(path),
            )

        pages = payload.get("pages")
        pages_value = pages if isinstance(pages, str) else None
        if path.suffix.lower() == ".pdf":
            return self._read_pdf(path, tool_use_id, pages_value)
        if path.suffix.lower() == ".ipynb":
            try:
                return self._read_notebook(path, tool_use_id)
            except Exception as exc:
                return self._error(tool_use_id, str(exc), path=str(path))

        data = path.read_bytes()
        if _detect_image_mime(data, path) is not None:
            return self._read_image(path, tool_use_id)

        offset = payload.get("offset")
        limit = payload.get("limit")
        return self._read_text(
            path,
            tool_use_id,
            offset=offset if isinstance(offset, int) else None,
            limit=limit if isinstance(limit, int) else None,
        )

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> Any:
        content = result.get("anthropic_content")
        if isinstance(content, list) and all(
            isinstance(item, dict) for item in content
        ):
            return make_provider_native_tool_result(
                format=FORMAT_ANTHROPIC_MESSAGES,
                content=content,
                text=str(result.get("text") or ""),
            )
        if result.get("success"):
            return str(result.get("text") or result.get("result") or "")
        return f"Error: {result.get('error')}"

    def to_display_format(
        self,
        text: str,
        result: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        if result.get("kind") == "image":
            path = str(result.get("path") or "")
            return {
                "type": "image",
                "content": result.get("display_content") or {},
                "path": path,
                "single_line": f"Read: {Path(path).name if path else 'image'}",
                "text_fallback": text,
            }
        return {
            "type": "text",
            "content": text,
            "single_line": (
                f"Read: {Path(str(result.get('path'))).name}"
                if result.get("path")
                else "Read"
            ),
        }


__all__ = ["ClaudeReadTool", "READ_SCHEMA"]
