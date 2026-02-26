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
from typing import Any, Dict, List, Optional, Tuple

from agent_core.types import FeaturePlugin
from agent_core.utils import get_logger


class FileContextFeature(FeaturePlugin):
    name: str = "file_context"
    version: str = "0.1.0"

    def __init__(self) -> None:  # pragma: no cover - trivial initializer
        # Simple in-memory caches to avoid repeated filesystem walks and
        # git ls-files calls on every completion invocation.
        # Keyed by the resolved working_directory path string.
        # Values are (non_ignored_paths, ignored_paths), both as posix
        # paths relative to working_directory.
        self._path_cache: Dict[str, Tuple[List[str], List[str]]] = {}
        self._line_count_cache: Dict[Path, Tuple[float, int]] = {}

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

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
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

    def _resolve_path(self, path: str, config: Dict[str, Any]) -> Path | None:
        """Resolve a path with working_directory and allowed_paths.

        Returns an absolute :class:`Path` when the path is allowed and
        points to an existing file; otherwise returns ``None``.
        """

        working_dir = config.get("working_directory") or "."
        allowed = config.get("allowed_paths") or ["."]

        try:
            base_dir = Path(working_dir).resolve()
            candidate = Path(path)
            if not candidate.is_absolute():
                candidate = base_dir / candidate
            abs_path = candidate.resolve()
        except Exception:
            return None

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
                abs_path == base or (
                    hasattr(abs_path, "is_relative_to")
                    and abs_path.is_relative_to(base)  # type: ignore[attr-defined]
                )
                or (not hasattr(abs_path, "is_relative_to") and str(abs_path).startswith(str(base)))
                for base in allowed_abs
            ):
                return None
        except Exception:
            return None

        try:
            if not abs_path.is_file():
                return None
        except Exception:
            return None

        return abs_path

    def _iter_paths(self, config: Dict[str, Any]) -> Tuple[Path, List[str], List[str]]:
        """Return (root, non_ignored_paths, ignored_paths).

        Paths are relative to ``working_directory`` and always use
        forward slashes. When inside a Git repository, paths are
        obtained via ``git ls-files`` using GitPython so that .gitignore
        rules are respected precisely. Outside a Git repo, this falls
        back to a simple filesystem walk that treats all files as
        non-ignored.
        """

        working_dir = config.get("working_directory") or "."
        try:
            root = Path(working_dir).resolve()
        except Exception:
            return Path("."), [], []

        if not root.exists() or not root.is_dir():
            return root, [], []

        root_str = str(root)
        cached = self._path_cache.get(root_str)
        if cached is not None:
            non_ignored_cached, ignored_cached = cached
            return root, non_ignored_cached, ignored_cached

        non_ignored: List[str] = []
        ignored: List[str] = []

        # Primary path discovery: GitPython + git ls-files, matching the
        # following commands when inside a Git repository:
        #   git ls-files --cached --others --exclude-standard
        #   git ls-files --cached --others
        try:
            from git import Repo  # type: ignore[import]

            try:
                repo = Repo(root, search_parent_directories=True)
                repo_root = Path(repo.working_tree_dir).resolve()

                def _ls_files(args: List[str]) -> List[str]:
                    output = repo.git.ls_files(*args)
                    if not output:
                        return []
                    return [line.strip() for line in output.splitlines() if line.strip()]

                # Non-ignored files according to Git (.gitignore and
                # standard excludes).
                git_non_ignored = _ls_files(["--cached", "--others", "--exclude-standard"])
                # All Git-tracked/other files, including those ignored by
                # .gitignore.
                git_all = _ls_files(["--cached", "--others"])

                if git_all:
                    non_ignored_set = set(git_non_ignored)
                    for rel_repo in git_all:
                        abs_path = repo_root / rel_repo
                        try:
                            rel_to_root = abs_path.relative_to(root)
                        except ValueError:
                            # Outside the configured working_directory.
                            continue
                        rel_posix = rel_to_root.as_posix()
                        if rel_repo in non_ignored_set:
                            non_ignored.append(rel_posix)
                        else:
                            ignored.append(rel_posix)
            except Exception:
                # Any Git-related failure falls back to a plain walk.
                pass
        except Exception:
            # GitPython not available; fall back to a plain walk.
            pass

        # Fallback: simple filesystem walk when Git is unavailable or the
        # directory is not a Git repository. All files are treated as
        # non-ignored in this mode.
        if not non_ignored and not ignored:
            for dirpath, _dirnames, filenames in os.walk(root):
                for name in filenames:
                    try:
                        abs_path = Path(dirpath, name)
                        rel = abs_path.relative_to(root)
                    except Exception:
                        continue
                    non_ignored.append(rel.as_posix())

        non_ignored.sort()
        ignored.sort()
        self._path_cache[root_str] = (non_ignored, ignored)
        return root, non_ignored, ignored

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

        # raw_suffix is of the form "path" or "path:range". Use only the
        # path fragment for matching, but keep any trailing range fragment so
        # that apply_completion can respect the user's input.
        path_fragment, _, range_input = raw_suffix.partition(":")
        root, base_non_ignored, base_ignored = self._iter_paths(config)
        if not base_non_ignored and not base_ignored:
            return []

        fragment = path_fragment.lower()
        if fragment:
            non_ignored = [p for p in base_non_ignored if fragment in p.lower()]
            ignored = [p for p in base_ignored if fragment in p.lower()]
        else:
            non_ignored = list(base_non_ignored)
            ignored = list(base_ignored)

        # Apply ordering rules on non-ignored candidates:
        # - Exact matches (case-insensitive) first.
        # - Non-ignored, non-exact files ordered by path length.
        # - Among those, up to 3 whose basename contains the fragment are
        #   prioritized to the very top of the length-ordered group.
        # - Next, up to 3 additional non-hidden paths (no component starting
        #   with '.') are prioritized.

        def _is_hidden(path: str) -> bool:
            return any(part.startswith(".") for part in path.split("/"))

        exact: List[str] = []
        rest_non_ignored: List[str] = []
        for p in non_ignored:
            if fragment and p.lower() == fragment:
                exact.append(p)
            else:
                rest_non_ignored.append(p)

        # Order the non-ignored, non-exact paths by length.
        rest_sorted = sorted(rest_non_ignored, key=len)

        # Prioritize up to 3 whose basename contains the fragment.
        prioritized_basename: List[str] = []
        remaining: List[str] = []
        if fragment:
            for p in rest_sorted:
                base = p.split("/")[-1].lower()
                if fragment in base and len(prioritized_basename) < 3:
                    prioritized_basename.append(p)
                else:
                    remaining.append(p)
        else:
            remaining = rest_sorted

        # From the remaining, prioritize up to 3 that are not hidden.
        prioritized_visible: List[str] = []
        final_rest: List[str] = []
        for p in remaining:
            if not _is_hidden(p) and len(prioritized_visible) < 3:
                prioritized_visible.append(p)
            else:
                final_rest.append(p)

        ordered = exact + prioritized_basename + prioritized_visible + final_rest + ignored

        # Limit number of suggestions for usability.
        max_suggestions = 30
        candidates = ordered[:max_suggestions]

        completions: List[Dict[str, Any]] = []
        for path in candidates:
            # Insert the @file:path reference, preserving any user-typed
            # range suffix so that selecting the completion does not
            # discard explicit ranges like ":10-20".
            suffix = f":{range_input}" if range_input else ""
            replacement = f"@file:{path}{suffix}"
            display = path if not range_input else f"{path}:{range_input}"

            completions.append(
                {
                    "replacement": replacement,
                    "start": prefix_start,
                    "display": display,
                    "display_meta": "file",
                    "path": path,
                    "range_input": range_input,
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

        abs_path = self._resolve_path(path, config)
        if abs_path is None:
            return ""

        max_bytes = int(config.get("file_context_max_bytes", 65536) or 65536)
        if max_bytes <= 0:
            max_bytes = 65536

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

    # ---- Completion-accept handling ----
    def apply_completion(
        self,
        config: Dict[str, Any],
        text: str,
        completion: Dict[str, Any],
    ) -> str:
        """Turn an accepted @file: completion into a template snippet.

        This hook is called by the core when a completion previously
        returned by :meth:`get_completions` is accepted. It constructs a
        snippet using this feature's template and the accepted path.
        """

        if not isinstance(text, str) or "@file:" not in text:
            return ""

        if not isinstance(completion, dict):
            return ""

        # Determine the referenced path. Prefer the explicit "path" that
        # get_completions attaches; fall back to parsing replacement/text.
        path = completion.get("path")
        if not isinstance(path, str) or not path:
            raw = completion.get("replacement")
            candidate = raw if isinstance(raw, str) else text
            if not isinstance(candidate, str) or not candidate.startswith("@file:"):
                return ""
            suffix = candidate[len("@file:") :]
            path = suffix.split(":", 1)[0]
            if not path:
                return ""

        # Parse optional range input from the completion (user-typed
        # suffix). Supported forms:
        #   ""         -> default (start at 1)
        #   "10"       -> start at 10, end computed from max_lines
        #   "10-"      -> start at 10, end computed from max_lines
        #   "10-20"    -> explicit start/end
        range_input = completion.get("range_input") or ""
        if not isinstance(range_input, str):
            range_input = ""
        range_input = range_input.strip()

        start_line: int
        end_line: int | None

        if not range_input:
            start_line = 1
            end_line = None
        else:
            if "-" in range_input:
                start_s, _, end_s = range_input.partition("-")
                try:
                    start_line = int(start_s)
                except Exception:
                    logger = get_logger("file_context_feature")
                    logger.warning(
                        "invalid_range_start",
                        path=path,
                        range_input=range_input,
                    )
                    raise ValueError(
                        f"Invalid start line in range {range_input!r} for @file:{path}"
                    )
                if end_s:
                    try:
                        end_line = int(end_s)
                    except Exception:
                        logger = get_logger("file_context_feature")
                        logger.warning(
                            "invalid_range_end",
                            path=path,
                            range_input=range_input,
                        )
                        raise ValueError(
                            f"Invalid end line in range {range_input!r} for @file:{path}"
                        )
                else:
                    end_line = None
            else:
                try:
                    start_line = int(range_input)
                except Exception:
                    logger = get_logger("file_context_feature")
                    logger.warning(
                        "invalid_range_start",
                        path=path,
                        range_input=range_input,
                    )
                    raise ValueError(
                        f"Invalid start line in range {range_input!r} for @file:{path}"
                    )
                end_line = None

        if start_line <= 0:
            logger = get_logger("file_context_feature")
            logger.warning(
                "range_start_out_of_bounds",
                path=path,
                range_input=range_input,
                start_line=start_line,
            )
            raise ValueError(
                f"Start line {start_line} is outside the valid range for @file:{path}"
            )

        abs_path = self._resolve_path(path, config)
        if abs_path is None:
            logger = get_logger("file_context_feature")
            logger.warning(
                "path_unreadable_for_completion",
                path=path,
            )
            raise ValueError(f"Cannot read file for @file:{path}")

        # Compute the file's total line count (cached by mtime).
        line_count = 0
        try:
            stat = abs_path.stat()
            cached = self._line_count_cache.get(abs_path)
            if cached is not None and cached[0] == stat.st_mtime:
                line_count = cached[1]
            else:
                with abs_path.open("r", encoding="utf-8") as f:
                    for idx, _line in enumerate(f, start=1):
                        line_count = idx
                self._line_count_cache[abs_path] = (stat.st_mtime, line_count)
        except Exception:
            logger = get_logger("file_context_feature")
            logger.warning("failed_to_count_lines", path=path)
            raise ValueError(f"Cannot read file for @file:{path}")

        if line_count == 0:
            logger = get_logger("file_context_feature")
            logger.warning("empty_file_for_range", path=path)
            raise ValueError(f"File for @file:{path} is empty; no lines to reference")

        max_lines = int(config.get("file_context_max_lines", 2000) or 2000)
        if max_lines <= 0:
            max_lines = 2000

        if end_line is None:
            # Default end: advance by max_lines, but do not exceed actual
            # file length.
            end_line = start_line + max_lines - 1
            if end_line > line_count:
                end_line = line_count
        else:
            # Explicit end: must be within the file's bounds.
            if end_line < start_line or end_line > line_count:
                logger = get_logger("file_context_feature")
                logger.warning(
                    "range_out_of_bounds",
                    path=path,
                    range_input=range_input,
                    start_line=start_line,
                    end_line=end_line,
                    line_count=line_count,
                )
                raise ValueError(
                    f"Line range {start_line}-{end_line} is outside the file's "
                    f"valid line range 1-{line_count} for @file:{path}"
                )

        if start_line > line_count:
            logger = get_logger("file_context_feature")
            logger.warning(
                "range_start_after_eof",
                path=path,
                range_input=range_input,
                start_line=start_line,
                line_count=line_count,
            )
            raise ValueError(
                f"Start line {start_line} is outside the file's valid line range "
                f"1-{line_count} for @file:{path}"
            )

        template = self.get_template(config)
        lang = self._guess_language(path)
        range_str = f"{start_line}-{end_line}"
        return template.format(path=path, lang=lang, range=range_str)
