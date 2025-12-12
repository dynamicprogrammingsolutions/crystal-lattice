"""FileContextFeature plugin.

Provides inline file context expansion and completions using the
``@file:{path[:start-end]}`` syntax.

Two responsibilities:

- During :meth:`initialize_request`, occurrences of ``@file:`` markers in
  provider-native message content are replaced with the referenced file
  contents (subject to simple range and size limits).
- Via :meth:`get_completions`, the plugin performs a fuzzy file search
  to suggest paths and returns completion templates that expand
  ``@file`` mentions into an editable multi-line snippet.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from agent_core.types import FeaturePlugin


class FileContextFeature(FeaturePlugin):
    name: str = "file_context"
    version: str = "0.1.0"

    # ---- Config / UI ----
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "file_context_enabled": {
                "type": "boolean",
                "default": True,
                "description": "Enable @file: path expansion and file completions.",
            },
            "file_context_on_the_fly": {
                "type": "boolean",
                "default": False,
                "description": (
                    "When true, expand @file markers only for the current "
                    "request by overriding state['request']['messages'] and "
                    "leave native history unchanged. When false, expand "
                    "native messages (and existing request messages only)."
                ),
            },
            "file_context_max_bytes": {
                "type": "integer",
                "default": 65536,
                "description": "Maximum bytes of file content inserted per @file reference.",
            },
            "file_context_max_lines": {
                "type": "integer",
                "default": 2000,
                "description": "Maximum number of lines read when range end is omitted.",
            },
            "file_context_template": {
                "type": "string",
                "default": "{path}\n```{lang}\n@file:{path}:{range}\n```",
                "description": (
                    "Template applied when a file completion is accepted. "
                    "Supports {path}, {lang}, and {range} placeholders."
                ),
            },
        }

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        # No dedicated UI widgets; configuration is JSON-only for now.
        return []

    # Uses adapter default get_models / get_tags / required_tags

    # ---- Templates ----
    def get_template(self, config: Dict[str, Any]) -> str:
        raw = config.get("file_context_template")
        if isinstance(raw, str) and raw:
            return raw
        return "{path}\n```{lang}\n@file:{path}:{range}\n```"

    # ---- Completion helpers ----
    def _guess_language(self, path: str) -> str:
        """Best-effort language identifier for fenced code blocks."""

        suffix = Path(path).suffix.lower()
        mapping = {
            ".py": "python",
            ".js": "js",
            ".jsx": "jsx",
            ".ts": "ts",
            ".tsx": "tsx",
            ".json": "json",
            ".md": "markdown",
            ".mdx": "markdown",
            ".html": "html",
            ".css": "css",
            ".rs": "rust",
            ".go": "go",
            ".java": "java",
            ".cs": "csharp",
            ".cpp": "cpp",
            ".cxx": "cpp",
            ".cc": "cpp",
            ".c": "c",
            ".sh": "bash",
            ".bash": "bash",
            ".zsh": "bash",
            ".toml": "toml",
            ".yaml": "yaml",
            ".yml": "yaml",
        }
        return mapping.get(suffix, "")

    def _iter_paths(self, config: Dict[str, Any]) -> List[str]:
        """Return a list of candidate file paths relative to working_directory.

        The search is rooted at ``working_directory``; paths are returned
        using forward slashes regardless of platform.
        """

        working_dir = config.get("working_directory") or "."
        try:
            root = Path(working_dir).resolve()
        except Exception:
            return []

        if not root.exists() or not root.is_dir():
            return []

        results: List[str] = []
        for dirpath, _dirnames, filenames in os.walk(root):
            for name in filenames:
                try:
                    abs_path = Path(dirpath, name)
                    rel = abs_path.relative_to(root)
                except Exception:
                    continue
                results.append(rel.as_posix())

        results.sort()
        return results

    def get_completions(self, config: Dict[str, Any], text: str) -> List[Dict[str, Any]]:
        enabled = bool(config.get("file_context_enabled", True))
        if not enabled:
            return []

        if not isinstance(text, str) or not text:
            return []

        # Look for an @file: token ending at the cursor.
        match = re.search(r"@file:([^\s]*)$", text)
        if not match:
            return []

        prefix_start = match.start()
        raw_suffix = match.group(1) or ""

        # Strip any partial range from the suffix when searching paths.
        path_fragment = raw_suffix.split(":", 1)[0]

        all_paths = self._iter_paths(config)
        if not all_paths:
            return []

        fragment = path_fragment.lower()
        if fragment:
            candidates = [p for p in all_paths if fragment in p.lower()]
        else:
            candidates = list(all_paths)

        # Limit number of suggestions for usability.
        max_suggestions = 30
        candidates = candidates[:max_suggestions]

        template = self.get_template(config)
        max_lines = int(config.get("file_context_max_lines", 2000) or 2000)
        if max_lines <= 0:
            max_lines = 2000
        default_range = f"1-{max_lines}"

        completions: List[Dict[str, Any]] = []
        for path in candidates:
            lang = self._guess_language(path)
            replacement = template.format(path=path, lang=lang, range=default_range)
            completions.append(
                {
                    "replacement": replacement,
                    "start": prefix_start,
                    "display": path,
                    "display_meta": "file",
                }
            )

        return completions

    # ---- Request-time expansion ----
    def _read_file_range(
        self,
        path: str,
        start_line: int,
        end_line: int,
        config: Dict[str, Any],
    ) -> str:
        """Read a slice of a file subject to basic safety limits.

        Paths are resolved relative to ``working_directory`` when
        relative. Access is constrained by ``allowed_paths`` when
        present. The slice is limited by ``file_context_max_bytes``.
        """

        if start_line <= 0 or end_line < start_line:
            return ""

        working_dir = config.get("working_directory") or "."
        allowed = config.get("allowed_paths") or ["."]
        max_bytes = int(config.get("file_context_max_bytes", 65536) or 65536)
        if max_bytes <= 0:
            max_bytes = 65536

        try:
            base_dir = Path(working_dir).resolve()
            candidate = Path(path)
            if not candidate.is_absolute():
                candidate = base_dir / candidate
            abs_path = candidate.resolve()
        except Exception:
            return ""

        # Enforce allowlist.
        try:
            allowed_abs: List[Path] = []
            for base in allowed:
                try:
                    base_path = Path(base)
                    if not base_path.is_absolute():
                        base_path = base_dir / base_path
                    allowed_abs.append(base_path.resolve())
                except Exception:
                    continue

            if allowed_abs and not any(
                abs_path == base or abs_path.is_relative_to(base)  # type: ignore[attr-defined]
                if hasattr(Path, "is_relative_to")
                else str(abs_path).startswith(str(base))
                for base in allowed_abs
            ):
                return ""
        except Exception:
            return ""

        try:
            if not abs_path.is_file():
                return ""
        except Exception:
            return ""

        contents: List[str] = []
        total = 0
        try:
            with abs_path.open("r", encoding="utf-8") as f:
                for idx, line in enumerate(f, start=1):
                    if idx < start_line:
                        continue
                    if idx > end_line:
                        break
                    chunk = line
                    contents.append(chunk)
                    total += len(chunk)
                    if total >= max_bytes:
                        break
        except Exception:
            return ""

        return "".join(contents)

    def _expand_file_markers(self, content: str, config: Dict[str, Any]) -> str:
        pattern = re.compile(r"@file:(?P<path>[^\s:]+)(?::(?P<start>\d+)-(?P<end>\d+))?")

        def _repl(match: re.Match[str]) -> str:
            path = match.group("path")
            start_s = match.group("start")
            end_s = match.group("end")

            max_lines = int(config.get("file_context_max_lines", 2000) or 2000)
            if max_lines <= 0:
                max_lines = 2000

            if start_s is None and end_s is None:
                start_line = 1
                end_line = start_line + max_lines - 1
            else:
                try:
                    start_line = int(start_s or "1")
                    end_line = int(end_s or str(start_line + max_lines - 1))
                except ValueError:
                    return match.group(0)

            snippet = self._read_file_range(path, start_line, end_line, config)
            if not snippet:
                # Preserve the original marker when the file cannot be read.
                return match.group(0)
            return snippet

        return pattern.sub(_repl, content)

    def _expand_messages(
        self,
        messages: List[Dict[str, Any]],
        cfg: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        new_messages: List[Dict[str, Any]] = []
        for msg in messages:
            if not isinstance(msg, dict):
                new_messages.append(msg)
                continue
            # Only expand @file markers in user messages; system/assistant/tool
            # content is left untouched to avoid surprising modifications of
            # prompts or model outputs.
            role = msg.get("role")
            if role != "user":
                new_messages.append(msg)
                continue
            content = msg.get("content")
            if not isinstance(content, str) or "@file:" not in content:
                new_messages.append(msg)
                continue
            expanded = self._expand_file_markers(content, cfg)
            new_messages.append({**msg, "content": expanded})

        return new_messages

    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:

        config_state = state.get("config", {}) or {}
        enabled = bool(config_state.get("file_context_enabled", True))
        if not enabled:
            return native_messages, state
        cfg = config_state

        on_the_fly = bool(cfg.get("file_context_on_the_fly", False))

        request = state.get("request") or {}
        request_messages = request.get("messages")

        # On-the-fly mode: expand markers only for this request by adding or
        # overriding ``request['messages']`` and leave native history
        # unchanged.
        if on_the_fly:
            base_messages: List[Dict[str, Any]]
            if isinstance(request_messages, list) and request_messages:
                base_messages = request_messages
            else:
                base_messages = native_messages

            new_request_messages = self._expand_messages(base_messages, cfg)
            new_request = {**request, "messages": new_request_messages}
            new_state = {**state, "request": new_request}
            return native_messages, new_state

        # Persistent mode (default): expand ``native_messages`` so that the
        # provider-native history carries the inlined file contents. If
        # ``request['messages']`` already exists, expand that as well, but do
        # not create it when missing.

        # First, compute candidate expanded native messages.
        candidate_native = self._expand_messages(native_messages, cfg)

        # If the expanded native history still contains any @file markers
        # (according to the same pattern used in _expand_file_markers), then
        # expanding natively would cause further replacements on the next
        # turn. In that case, fall back to on-the-fly behaviour for this
        # request only.
        pattern = re.compile(r"@file:(?P<path>[^\s:]+)(?::(?P<start>\d+)-(?P<end>\d+))?")
        has_residual_markers = False
        for msg in candidate_native:
            if not isinstance(msg, dict):
                continue
            # Residual-marker guarding only cares about user messages; markers
            # in system/assistant/tool content are ignored.
            role = msg.get("role")
            if role != "user":
                continue
            content = msg.get("content")
            if not isinstance(content, str):
                continue
            if pattern.search(content):
                has_residual_markers = True
                break

        if has_residual_markers:
            # Fallback: behave as if on_the_fly were true for this request.
            base_messages = (
                request_messages
                if isinstance(request_messages, list) and request_messages
                else native_messages
            )
            new_request_messages = self._expand_messages(base_messages, cfg)
            new_request = {**request, "messages": new_request_messages}
            new_state = {**state, "request": new_request}
            return native_messages, new_state

        new_state = state
        if isinstance(request_messages, list) and request_messages:
            new_request_messages = self._expand_messages(request_messages, cfg)
            new_request = {**request, "messages": new_request_messages}
            new_state = {**state, "request": new_request}

        return candidate_native, new_state

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        # Responses are not changed by this feature.
        return final_messages, native_messages, state
