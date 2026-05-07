"""Shared Codex-style apply_patch runtime and schema helpers."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from agent_core.tool_interop import (
    OpenAIChatToolSchemaAccessor,
    OpenAIResponsesCustomToolSchemaAccessor,
    OpenAIResponsesFunctionToolSchemaAccessor,
    get_schema_target_formats_from_config,
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

_FREEFORM_DESCRIPTION = (
    "Use the `apply_patch` tool to edit files. "
    "This is a FREEFORM tool, so do not wrap the patch in JSON."
)

_FUNCTION_DESCRIPTION = """Use the `apply_patch` tool to edit files.
Your patch language is a stripped-down, file-oriented diff format designed to be easy to parse and safe to apply. You can think of it as a high-level envelope:

*** Begin Patch
[ one or more file sections ]
*** End Patch

Within that envelope, you get a sequence of file operations.
You MUST include a header to specify the action you are taking.
Each operation starts with one of three headers:

*** Add File: <path> - create a new file. Every following line is a + line (the initial contents).
*** Delete File: <path> - remove an existing file. Nothing follows.
*** Update File: <path> - patch an existing file in place (optionally with a rename).

May be immediately followed by *** Move to: <new path> if you want to rename the file.
Then one or more hunks, each introduced by @@ (optionally followed by a hunk header).
Within a hunk each line starts with:

For instructions on [context_before] and [context_after]:
- By default, show 3 lines of code immediately above and 3 lines immediately below each change. If a change is within 3 lines of a previous change, do NOT duplicate the first change's [context_after] lines in the second change's [context_before] lines.
- If 3 lines of context is insufficient to uniquely identify the snippet of code within the file, use the @@ operator to indicate the class or function to which the snippet belongs.
- If a code block is repeated so many times in a class or function such that even a single @@ statement and 3 lines of context cannot uniquely identify the snippet of code, you can use multiple @@ statements to jump to the right context.

The full grammar definition is below:
Patch := Begin { FileOp } End
Begin := "*** Begin Patch" NEWLINE
End := "*** End Patch" NEWLINE
FileOp := AddFile | DeleteFile | UpdateFile
AddFile := "*** Add File: " path NEWLINE { "+" line NEWLINE }
DeleteFile := "*** Delete File: " path NEWLINE
UpdateFile := "*** Update File: " path NEWLINE [ MoveTo ] { Hunk }
MoveTo := "*** Move to: " newPath NEWLINE
Hunk := "@@" [ header ] NEWLINE { HunkLine } [ "*** End of File" NEWLINE ]
HunkLine := (" " | "-" | "+") text NEWLINE

A full patch can combine several operations:

*** Begin Patch
*** Add File: hello.txt
+Hello world
*** Update File: src/app.py
*** Move to: src/main.py
@@ def greet():
-print("Hi")
+print("Hello, world!")
*** Delete File: obsolete.txt
*** End Patch

It is important to remember:

- You must include a header with your intended action (Add/Delete/Update)
- You must prefix new lines with `+` even when creating a new file
- File references can only be relative, NEVER ABSOLUTE.
"""

_HEREDOC_PATTERN = re.compile(
    r"^\s*apply_patch\s+<<(?P<quote>['\"]?)(?P<tag>[A-Za-z0-9_]+)(?P=quote)\s*\n"
    r"(?P<body>.*?)(?:\n)?(?P=tag)\s*;?\s*$",
    re.DOTALL,
)


class ActionType(str, Enum):
    ADD = "add"
    DELETE = "delete"
    UPDATE = "update"


@dataclass
class FileChange:
    type: ActionType
    old_content: Optional[str] = None
    new_content: Optional[str] = None
    move_path: Optional[str] = None


@dataclass
class Commit:
    changes: Dict[str, FileChange] = field(default_factory=dict)


def assemble_changes(orig: Dict[str, Optional[str]], dest: Dict[str, Optional[str]]) -> Commit:
    commit = Commit()
    for path in sorted(set(orig.keys()).union(dest.keys())):
        old_content = orig.get(path)
        new_content = dest.get(path)
        if old_content != new_content:
            if old_content is not None and new_content is not None:
                commit.changes[path] = FileChange(
                    type=ActionType.UPDATE,
                    old_content=old_content,
                    new_content=new_content,
                )
            elif new_content:
                commit.changes[path] = FileChange(
                    type=ActionType.ADD,
                    new_content=new_content,
                )
            elif old_content:
                commit.changes[path] = FileChange(
                    type=ActionType.DELETE,
                    old_content=old_content,
                )
            else:  # pragma: no cover - defensive
                raise AssertionError("assemble_changes reached impossible branch")
    return commit


@dataclass
class Chunk:
    orig_index: int = -1
    del_lines: List[str] = field(default_factory=list)
    ins_lines: List[str] = field(default_factory=list)


@dataclass
class PatchAction:
    type: ActionType
    new_file: Optional[str] = None
    chunks: List[Chunk] = field(default_factory=list)
    move_path: Optional[str] = None


@dataclass
class Patch:
    actions: Dict[str, PatchAction] = field(default_factory=dict)


class DiffError(ValueError):
    """Raised when the patch text is invalid or cannot be applied."""


@dataclass
class Parser:
    current_files: Dict[str, str] = field(default_factory=dict)
    lines: List[str] = field(default_factory=list)
    index: int = 0
    patch: Patch = field(default_factory=Patch)
    fuzz: int = 0

    def is_done(self, prefixes: Optional[Tuple[str, ...]] = None) -> bool:
        if self.index >= len(self.lines):
            return True
        if prefixes and self.lines[self.index].startswith(prefixes):
            return True
        return False

    def startswith(self, prefix: str) -> bool:
        assert self.index < len(self.lines), f"Index: {self.index} >= {len(self.lines)}"
        return self.lines[self.index].startswith(prefix)

    def read_str(self, prefix: str = "", return_everything: bool = False) -> str:
        assert self.index < len(self.lines), f"Index: {self.index} >= {len(self.lines)}"
        line = self.lines[self.index]
        if line.startswith(prefix):
            text = line if return_everything else line[len(prefix) :]
            self.index += 1
            return text
        return ""

    def parse(self) -> None:
        while not self.is_done(("*** End Patch",)):
            path = self.read_str("*** Update File: ")
            if path:
                if path in self.patch.actions:
                    raise DiffError(f"Update File Error: Duplicate Path: {path}")
                move_to = self.read_str("*** Move to: ")
                if path not in self.current_files:
                    raise DiffError(f"Update File Error: Missing File: {path}")
                text = self.current_files[path]
                action = self.parse_update_file(text)
                action.move_path = move_to or None
                self.patch.actions[path] = action
                continue

            path = self.read_str("*** Delete File: ")
            if path:
                if path in self.patch.actions:
                    raise DiffError(f"Delete File Error: Duplicate Path: {path}")
                if path not in self.current_files:
                    raise DiffError(f"Delete File Error: Missing File: {path}")
                self.patch.actions[path] = PatchAction(type=ActionType.DELETE)
                continue

            path = self.read_str("*** Add File: ")
            if path:
                if path in self.patch.actions:
                    raise DiffError(f"Add File Error: Duplicate Path: {path}")
                self.patch.actions[path] = self.parse_add_file()
                continue

            raise DiffError(f"Unknown Line: {self.lines[self.index]}")

        if not self.startswith("*** End Patch"):
            raise DiffError("Missing End Patch")
        self.index += 1

    def parse_update_file(self, text: str) -> PatchAction:
        action = PatchAction(type=ActionType.UPDATE)
        lines = text.split("\n")
        index = 0
        while not self.is_done(
            (
                "*** End Patch",
                "*** Update File:",
                "*** Delete File:",
                "*** Add File:",
                "*** End of File",
            )
        ):
            def_str = self.read_str("@@ ")
            section_str = ""
            if not def_str and self.lines[self.index] == "@@":
                section_str = self.lines[self.index]
                self.index += 1

            if not (def_str or section_str or index == 0):
                raise DiffError(f"Invalid Line:\n{self.lines[self.index]}")

            if def_str.strip():
                found = False
                if not [s for s in lines[:index] if s == def_str]:
                    for i, s in enumerate(lines[index:], index):
                        if s == def_str:
                            index = i + 1
                            found = True
                            break

                if not found and not [s for s in lines[:index] if s.strip() == def_str.strip()]:
                    for i, s in enumerate(lines[index:], index):
                        if s.strip() == def_str.strip():
                            index = i + 1
                            self.fuzz += 1
                            found = True
                            break

            next_chunk_context, chunks, end_patch_index, eof = peek_next_section(
                self.lines, self.index
            )
            next_chunk_text = "\n".join(next_chunk_context)
            new_index, fuzz = find_context(lines, next_chunk_context, index, eof)
            if new_index == -1:
                if eof:
                    raise DiffError(f"Invalid EOF Context {index}:\n{next_chunk_text}")
                raise DiffError(f"Invalid Context {index}:\n{next_chunk_text}")

            self.fuzz += fuzz
            for ch in chunks:
                ch.orig_index += new_index
                action.chunks.append(ch)

            index = new_index + len(next_chunk_context)
            self.index = end_patch_index

        return action

    def parse_add_file(self) -> PatchAction:
        lines: List[str] = []
        while not self.is_done(
            ("*** End Patch", "*** Update File:", "*** Delete File:", "*** Add File:")
        ):
            s = self.read_str()
            if not s.startswith("+"):
                raise DiffError(f"Invalid Add File Line: {s}")
            lines.append(s[1:])
        return PatchAction(type=ActionType.ADD, new_file="\n".join(lines))


def find_context_core(lines: List[str], context: List[str], start: int) -> Tuple[int, int]:
    if not context:
        return start, 0

    for i in range(start, len(lines)):
        if lines[i : i + len(context)] == context:
            return i, 0

    for i in range(start, len(lines)):
        if [s.rstrip() for s in lines[i : i + len(context)]] == [s.rstrip() for s in context]:
            return i, 1

    for i in range(start, len(lines)):
        if [s.strip() for s in lines[i : i + len(context)]] == [s.strip() for s in context]:
            return i, 100

    return -1, 0


def find_context(
    lines: List[str], context: List[str], start: int, eof: bool
) -> Tuple[int, int]:
    if eof:
        new_index, fuzz = find_context_core(lines, context, len(lines) - len(context))
        if new_index != -1:
            return new_index, fuzz
        new_index, fuzz = find_context_core(lines, context, start)
        return new_index, fuzz + 10000
    return find_context_core(lines, context, start)


def peek_next_section(
    lines: List[str], index: int
) -> Tuple[List[str], List[Chunk], int, bool]:
    old: List[str] = []
    del_lines: List[str] = []
    ins_lines: List[str] = []
    chunks: List[Chunk] = []
    mode = "keep"
    orig_index = index

    while index < len(lines):
        s = lines[index]
        if s.startswith(
            (
                "@@",
                "*** End Patch",
                "*** Update File:",
                "*** Delete File:",
                "*** Add File:",
                "*** End of File",
            )
        ):
            break
        if s == "***":
            break
        if s.startswith("***"):
            raise DiffError(f"Invalid Line: {s}")

        index += 1
        last_mode = mode
        if s == "":
            s = " "
        if s[0] == "+":
            mode = "add"
        elif s[0] == "-":
            mode = "delete"
        elif s[0] == " ":
            mode = "keep"
        else:
            raise DiffError(f"Invalid Line: {s}")

        s = s[1:]
        if mode == "keep" and last_mode != mode and (ins_lines or del_lines):
            chunks.append(
                Chunk(
                    orig_index=len(old) - len(del_lines),
                    del_lines=del_lines,
                    ins_lines=ins_lines,
                )
            )
            del_lines = []
            ins_lines = []

        if mode == "delete":
            del_lines.append(s)
            old.append(s)
        elif mode == "add":
            ins_lines.append(s)
        elif mode == "keep":
            old.append(s)

    if ins_lines or del_lines:
        chunks.append(
            Chunk(
                orig_index=len(old) - len(del_lines),
                del_lines=del_lines,
                ins_lines=ins_lines,
            )
        )

    if index < len(lines) and lines[index] == "*** End of File":
        index += 1
        return old, chunks, index, True

    if index == orig_index:
        raise DiffError(f"Nothing in this section - index={index} {lines[index]}")

    return old, chunks, index, False


def text_to_patch(text: str, orig: Dict[str, str]) -> Tuple[Patch, int]:
    lines = text.strip().split("\n")
    if len(lines) < 2 or not lines[0].startswith("*** Begin Patch") or lines[-1] != "*** End Patch":
        raise DiffError("Invalid patch text")

    parser = Parser(current_files=orig, lines=lines, index=1)
    parser.parse()
    return parser.patch, parser.fuzz


def identify_files_needed(text: str) -> List[str]:
    lines = text.strip().split("\n")
    result: set[str] = set()
    for line in lines:
        if line.startswith("*** Update File: "):
            result.add(line[len("*** Update File: ") :])
        if line.startswith("*** Delete File: "):
            result.add(line[len("*** Delete File: ") :])
    return list(result)


def _get_updated_file(text: str, action: PatchAction, path: str) -> str:
    assert action.type == ActionType.UPDATE
    orig_lines = text.split("\n")
    dest_lines: List[str] = []
    orig_index = 0
    dest_index = 0

    for chunk in action.chunks:
        if chunk.orig_index > len(orig_lines):
            raise DiffError(
                f"_get_updated_file: {path}: chunk.orig_index {chunk.orig_index} > len(lines) {len(orig_lines)}"
            )
        if orig_index > chunk.orig_index:
            raise DiffError(
                f"_get_updated_file: {path}: orig_index {orig_index} > chunk.orig_index {chunk.orig_index}"
            )

        dest_lines.extend(orig_lines[orig_index : chunk.orig_index])
        delta = chunk.orig_index - orig_index
        orig_index += delta
        dest_index += delta

        if chunk.ins_lines:
            dest_lines.extend(chunk.ins_lines)
            dest_index += len(chunk.ins_lines)

        orig_index += len(chunk.del_lines)

    dest_lines.extend(orig_lines[orig_index:])
    delta = len(orig_lines) - orig_index
    orig_index += delta
    dest_index += delta

    assert orig_index == len(orig_lines)
    assert dest_index == len(dest_lines)

    return "\n".join(dest_lines)


def patch_to_commit(patch: Patch, orig: Dict[str, str]) -> Commit:
    commit = Commit()
    for path, action in patch.actions.items():
        if action.type == ActionType.DELETE:
            commit.changes[path] = FileChange(type=ActionType.DELETE, old_content=orig[path])
        elif action.type == ActionType.ADD:
            commit.changes[path] = FileChange(type=ActionType.ADD, new_content=action.new_file)
        elif action.type == ActionType.UPDATE:
            new_content = _get_updated_file(text=orig[path], action=action, path=path)
            commit.changes[path] = FileChange(
                type=ActionType.UPDATE,
                old_content=orig[path],
                new_content=new_content,
                move_path=action.move_path,
            )
    return commit


def apply_commit(
    commit: Commit, write_fn: Callable[[str, str], None], remove_fn: Callable[[str], None]
) -> None:
    for path, change in commit.changes.items():
        if change.type == ActionType.DELETE:
            remove_fn(path)
        elif change.type == ActionType.ADD:
            assert change.new_content is not None
            write_fn(path, change.new_content)
        elif change.type == ActionType.UPDATE:
            assert change.new_content is not None
            if change.move_path:
                write_fn(change.move_path, change.new_content)
                remove_fn(path)
            else:
                write_fn(path, change.new_content)


def process_patch(
    text: str,
    open_fn: Callable[[str], str],
    write_fn: Callable[[str, str], None],
    remove_fn: Callable[[str], None],
) -> Tuple[str, int, Commit]:
    if not text.startswith("*** Begin Patch"):
        raise DiffError("Patch must start with '*** Begin Patch'")
    paths = identify_files_needed(text)
    orig = load_files(paths, open_fn)
    patch, fuzz = text_to_patch(text, orig)
    commit = patch_to_commit(patch, orig)
    apply_commit(commit, write_fn, remove_fn)
    return "Done!", fuzz, commit


def load_files(paths: List[str], open_fn: Callable[[str], str]) -> Dict[str, str]:
    orig: Dict[str, str] = {}
    for path in paths:
        orig[path] = open_fn(path)
    return orig


def build_apply_patch_freeform_schema(working_dir: str) -> Dict[str, Any]:
    return {
        "type": "custom",
        "name": "apply_patch",
        "description": (
            f"{_FREEFORM_DESCRIPTION} Files are resolved relative to {working_dir}. "
            "Paths are sandboxed to allowed_paths."
        ),
        "format": {
            "type": "grammar",
            "syntax": "lark",
            "definition": APPLY_PATCH_GRAMMAR,
        },
    }


def build_apply_patch_function_schema(working_dir: str) -> Dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": "apply_patch",
            "description": (
                f"{_FUNCTION_DESCRIPTION}\nPaths are resolved relative to {working_dir}. "
                "Paths are sandboxed to allowed_paths."
            ),
            "strict": False,
            "parameters": {
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": "The entire contents of the apply_patch command",
                    }
                },
                "required": ["input"],
                "additionalProperties": False,
            },
        },
    }


def select_apply_patch_schemas(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    working_dir = str((config or {}).get("working_directory", "."))
    target_formats = set(get_schema_target_formats_from_config(config or {}))

    if OpenAIResponsesCustomToolSchemaAccessor.format_id in target_formats:
        return [build_apply_patch_freeform_schema(working_dir)]

    function_formats = {
        OpenAIChatToolSchemaAccessor.format_id,
        OpenAIResponsesFunctionToolSchemaAccessor.format_id,
    }
    if not target_formats or target_formats.intersection(function_formats):
        return [build_apply_patch_function_schema(working_dir)]

    return []


def extract_patch_text(payload: Any, payload_kind: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    if isinstance(payload, str):
        if payload.strip():
            return payload, None
        return None, "input must be a non-empty string"

    if isinstance(payload, dict):
        patch_text = payload.get("input", "")
        if isinstance(patch_text, str) and patch_text.strip():
            return patch_text, None
        return None, "input must be a non-empty string"

    if payload_kind == "text":
        return None, "input must be a non-empty string"

    return None, "payload must be freeform text or an object containing 'input'"


def summarize_patch_text(patch_text: str) -> str:
    if not isinstance(patch_text, str) or not patch_text.strip():
        return ""

    lines = patch_text.splitlines()
    if not lines or not lines[0].lstrip().startswith("*** Begin Patch"):
        return ""

    parts: List[str] = []
    idx = 0
    while idx < len(lines):
        line = lines[idx].strip()

        if line.startswith("*** Add File:"):
            path = line.removeprefix("*** Add File:").strip()
            if path:
                parts.append(f"add: {path}")
        elif line.startswith("*** Update File:"):
            path = line.removeprefix("*** Update File:").strip()
            move_to: Optional[str] = None
            if idx + 1 < len(lines):
                next_line = lines[idx + 1].strip()
                if next_line.startswith("*** Move to:"):
                    move_to = next_line.removeprefix("*** Move to:").strip() or None
                    idx += 1
            if path:
                parts.append(f"update: {path} -> {move_to}" if move_to else f"update: {path}")
        elif line.startswith("*** Delete File:"):
            path = line.removeprefix("*** Delete File:").strip()
            if path:
                parts.append(f"delete: {path}")

        idx += 1

    return "; ".join(parts)


def format_apply_patch_result(result: Dict[str, Any]) -> str:
    if not result.get("success"):
        return f"Error applying patch: {result.get('error')}"

    fuzz = result.get("fuzz")
    changes = result.get("changes") or {}
    lines = ["Patch applied successfully."]

    if isinstance(fuzz, int) and fuzz > 0:
        lines.append(f"Fuzz factor: {fuzz}")

    if isinstance(changes, dict) and changes:
        lines.append("Changes:")
        for path, info in changes.items():
            change_type = info.get("type", "?")
            move_to = info.get("move_path")
            lines.append(f"- {change_type}: {path} -> {move_to}" if move_to else f"- {change_type}: {path}")

    return "\n".join(lines)


def apply_patch_display(text: str, result: Dict[str, Any]) -> Dict[str, Any]:
    patch_text = result.get("input")
    if not isinstance(patch_text, str) or not patch_text.strip():
        return {"type": "text", "content": text}

    header = text or "Patch result:"
    content = f"{header}\n\nPatch:\n{patch_text}"
    changes = result.get("changes") or {}
    single_line_parts: List[str] = []
    if isinstance(changes, dict) and changes:
        for path in sorted(changes):
            info = changes.get(path) or {}
            if not isinstance(info, dict):
                continue
            change_type = info.get("type", "?")
            move_to = info.get("move_path")
            single_line_parts.append(
                f"{change_type}: {path} -> {move_to}" if move_to else f"{change_type}: {path}"
            )

    display: Dict[str, Any] = {"type": "text", "content": content}
    if single_line_parts:
        display["single_line"] = "\n".join(single_line_parts)
    return display


def execute_apply_patch_text(
    patch_text: str,
    *,
    config: Dict[str, Any],
    working_dir: Optional[str] = None,
) -> Dict[str, Any]:
    if not isinstance(patch_text, str) or not patch_text.strip():
        return {"success": False, "error": "input must be a non-empty string"}

    max_bytes = int(config.get("max_patch_bytes", 2 * 1024 * 1024))
    if len(patch_text.encode("utf-8")) > max_bytes:
        return {"success": False, "error": f"Patch too large (>{max_bytes} bytes)"}

    effective_working_dir = str(working_dir or config.get("working_directory", "."))
    allowed_cfg = config.get("allowed_paths")
    allowed_paths = allowed_cfg if isinstance(allowed_cfg, list) and allowed_cfg else ["."]

    try:
        message, fuzz, commit = process_patch_sandboxed(
            patch_text,
            working_dir=effective_working_dir,
            allowed_paths=allowed_paths,
        )
    except DiffError as exc:
        return {"success": False, "error": f"Patch failed: {exc}"}
    except Exception as exc:  # pragma: no cover - defensive
        return {"success": False, "error": f"Unexpected error applying patch: {exc}"}

    changes_summary = {
        path: {"type": change.type.value, "move_path": change.move_path}
        for path, change in commit.changes.items()
    }
    return {
        "success": True,
        "result": message,
        "fuzz": fuzz,
        "changes": changes_summary,
        "input": patch_text,
    }


def process_patch_sandboxed(
    patch_text: str,
    *,
    working_dir: str,
    allowed_paths: List[str],
) -> Tuple[str, int, Commit]:
    expanded_working_dir = os.path.abspath(os.path.expanduser(working_dir or "."))

    def resolve_path(rel_path: str) -> str:
        raw_path = str(rel_path).strip()
        if not raw_path:
            raise DiffError("Empty path in patch")

        expanded_path = os.path.expanduser(raw_path)
        if os.path.isabs(expanded_path):
            abs_path = os.path.abspath(expanded_path)
        else:
            abs_path = os.path.abspath(os.path.join(expanded_working_dir, expanded_path))

        allowed = allowed_paths or ["."]
        abs_allowed = [os.path.abspath(os.path.expanduser(path)) for path in allowed]
        if not any(abs_path == root or abs_path.startswith(root + os.sep) for root in abs_allowed):
            raise DiffError(f"Access denied for path: {raw_path}")

        return abs_path

    def open_fn(path: str) -> str:
        abs_path = resolve_path(path)
        try:
            with open(abs_path, "rt", encoding="utf-8") as handle:
                return handle.read()
        except FileNotFoundError as exc:
            raise DiffError(f"Missing file for update/delete: {path}") from exc

    def write_fn(path: str, content: str) -> None:
        abs_path = resolve_path(path)
        directory = os.path.dirname(abs_path) or "."
        os.makedirs(directory, exist_ok=True)
        with open(abs_path, "wt", encoding="utf-8") as handle:
            handle.write(content)

    def remove_fn(path: str) -> None:
        abs_path = resolve_path(path)
        if os.path.exists(abs_path):
            os.remove(abs_path)

    return process_patch(patch_text, open_fn, write_fn, remove_fn)


def maybe_extract_patch_from_shell_command(command: Any) -> Optional[str]:
    if isinstance(command, str):
        return _extract_patch_from_shell_script(command)

    if not isinstance(command, list) or not command:
        return None

    if len(command) == 2 and command[0] == "apply_patch" and isinstance(command[1], str):
        return command[1]

    if len(command) >= 3 and isinstance(command[0], str) and isinstance(command[1], str):
        shell_name = os.path.basename(command[0])
        if shell_name in {"bash", "sh", "zsh"} and command[1] in {"-lc", "-c"}:
            script = command[2]
            if isinstance(script, str):
                return _extract_patch_from_shell_script(script)

    return None


def _extract_patch_from_shell_script(script: str) -> Optional[str]:
    if not isinstance(script, str) or "apply_patch" not in script:
        return None

    heredoc_match = _HEREDOC_PATTERN.match(script.strip())
    if heredoc_match:
        body = heredoc_match.group("body")
        return body if body.endswith("\n") else f"{body}\n"

    stripped = script.strip()
    if stripped.startswith("apply_patch "):
        patch_text = stripped[len("apply_patch ") :].strip()
        if patch_text.startswith("*** Begin Patch"):
            return patch_text

    return None


__all__ = [
    "APPLY_PATCH_GRAMMAR",
    "DiffError",
    "apply_patch_display",
    "build_apply_patch_freeform_schema",
    "build_apply_patch_function_schema",
    "execute_apply_patch_text",
    "extract_patch_text",
    "format_apply_patch_result",
    "maybe_extract_patch_from_shell_command",
    "process_patch_sandboxed",
    "select_apply_patch_schemas",
    "summarize_patch_text",
]