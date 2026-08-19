#!/usr/bin/env python3
"""Synchronize a named roadmap between its CSV and Google Sheets."""

from __future__ import annotations

import argparse
import asyncio
import csv
import difflib
import io
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from generate import (
    FIELDS,
    NormalizedRoadmap,
    Row,
    RoadmapError,
    normalize_csv,
    normalize_csv_text,
    render_markdown,
)
from roadmap_config import (
    MCPServerDefinition,
    RoadmapConfigError,
    RoadmapTarget,
    load_mcp_server,
    load_registry,
    resolve_target,
    unpinned_npm_packages,
)


REPO_ROOT = Path(__file__).resolve().parent.parent
MCP_SHARED_SRC = REPO_ROOT / "plugins" / "mcp-shared" / "src"
if str(MCP_SHARED_SRC) not in sys.path:
    sys.path.insert(0, str(MCP_SHARED_SRC))

from mcp_shared.runtime import (  # noqa: E402
    MCPRuntimeConfig,
    MCPRuntimeManager,
    MCPServerRuntimeSpec,
)


class RoadmapSyncError(RuntimeError):
    """Raised when remote synchronization cannot proceed safely."""


def rows_to_matrix(rows: list[Row]) -> list[list[str]]:
    matrix = [list(FIELDS)]
    for row in rows:
        matrix.append(
            [
                row.task,
                row.external_id,
                row.internal_id,
                row.title,
                row.purpose,
                row.priority,
                row.status,
                ";".join(row.declared_dependencies),
                ";".join(row.inferred_dependencies),
                row.notes,
            ]
        )
    return matrix


def normalize_matrix(values: Any) -> list[list[str]]:
    if not isinstance(values, list):
        raise RoadmapSyncError("Google Sheets values response is not an array")
    matrix: list[list[str]] = []
    for raw_row in values:
        if not isinstance(raw_row, list):
            raise RoadmapSyncError("Google Sheets row is not an array")
        row = ["" if value is None else str(value) for value in raw_row[: len(FIELDS)]]
        row.extend([""] * (len(FIELDS) - len(row)))
        matrix.append(row)
    while matrix and not any(cell for cell in matrix[-1]):
        matrix.pop()
    return matrix


def matrix_to_csv_text(matrix: list[list[str]]) -> str:
    if not matrix:
        raise RoadmapSyncError("remote roadmap is uninitialized")
    if tuple(matrix[0]) != FIELDS:
        raise RoadmapSyncError(
            "remote header must be exactly: " + ",".join(FIELDS)
        )
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerows(matrix)
    return buffer.getvalue()


def matrix_to_unchecked_csv_text(matrix: list[list[str]]) -> str:
    if not matrix:
        return ""
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerows(matrix)
    return buffer.getvalue()


def validate_csv_text(
    text: str,
    *,
    target: RoadmapTarget,
    repo_root: Path,
) -> NormalizedRoadmap:
    return normalize_csv_text(
        text,
        source_name=f"Google Sheet for {target.key}",
        repo_root=repo_root,
    )


def unified_diff(
    before: str,
    after: str,
    *,
    before_name: str,
    after_name: str,
) -> str:
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=before_name,
            tofile=after_name,
        )
    )


def _sheet_range(sheet: str, cells: str) -> str:
    escaped = sheet.replace("'", "''")
    return f"'{escaped}'!{cells}"


def _json_payload(result: Any, *, empty_range_is_empty: bool = False) -> Any:
    if result.is_error:
        raise RoadmapSyncError("mcp-gsheets returned an error")
    for item in result.content:
        if item.get("type") != "text":
            continue
        text = item.get("text", "")
        if (
            empty_range_is_empty
            and isinstance(text, str)
            and text.startswith("No data found in range:")
        ):
            return {"values": []}
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            continue
    raise RoadmapSyncError("mcp-gsheets returned no JSON payload")


def _sheet_titles(payload: dict[str, Any]) -> list[str]:
    titles: list[str] = []
    sheets = payload.get("sheets", [])
    if not isinstance(sheets, list):
        return titles
    for sheet in sheets:
        if not isinstance(sheet, dict):
            continue
        title = sheet.get("title")
        if isinstance(title, str):
            titles.append(title)
            continue
        properties = sheet.get("properties")
        if isinstance(properties, dict) and isinstance(
            properties.get("title"), str
        ):
            titles.append(properties["title"])
    return titles


class GSheetsMCP:
    def __init__(
        self,
        definition: MCPServerDefinition,
        *,
        server_name: str,
    ) -> None:
        self.definition = definition
        self.server_name = server_name
        self.manager = MCPRuntimeManager()

    async def __aenter__(self) -> "GSheetsMCP":
        definition = self.definition
        spec = MCPServerRuntimeSpec(
            name=self.server_name,
            enabled=True,
            transport="stdio",
            command=definition.command,
            args=list(definition.args),
            env=definition.env,
            cwd=definition.cwd,
            startup_timeout_seconds=definition.startup_timeout_seconds or 60,
            tool_timeout_seconds=definition.tool_timeout_seconds or 60,
        )
        await self.manager.start(
            MCPRuntimeConfig(
                servers={self.server_name: spec},
                fail_on_startup_error=True,
            )
        )
        return self

    async def __aexit__(self, *_args: object) -> None:
        await self.manager.close()

    async def _call(self, tool: str, arguments: dict[str, Any]) -> Any:
        return await self.manager.call_tool(
            server_name=self.server_name,
            tool_name=tool,
            arguments=arguments,
            timeout_seconds=self.definition.tool_timeout_seconds or 60,
        )

    async def verify_target(self, target: RoadmapTarget) -> None:
        payload = _json_payload(
            await self._call(
                "sheets_get_metadata",
                {"spreadsheetId": target.spreadsheet_id},
            )
        )
        if not isinstance(payload, dict):
            raise RoadmapSyncError("spreadsheet metadata is not an object")
        if payload.get("spreadsheetId") != target.spreadsheet_id:
            raise RoadmapSyncError("spreadsheet ID does not match named config")
        if payload.get("title") != target.spreadsheet_title:
            raise RoadmapSyncError(
                "spreadsheet title does not match named config"
            )
        if target.sheet not in _sheet_titles(payload):
            raise RoadmapSyncError(
                f"sheet {target.sheet!r} does not exist in spreadsheet"
            )

    async def get_values(self, target: RoadmapTarget) -> list[list[str]]:
        payload = _json_payload(
            await self._call(
                "sheets_get_values",
                {
                    "spreadsheetId": target.spreadsheet_id,
                    "range": _sheet_range(target.sheet, "A:J"),
                    "majorDimension": "ROWS",
                    "valueRenderOption": "UNFORMATTED_VALUE",
                },
            ),
            empty_range_is_empty=True,
        )
        if not isinstance(payload, dict):
            raise RoadmapSyncError("spreadsheet values payload is not an object")
        return normalize_matrix(payload.get("values", []))

    async def update_values(
        self,
        target: RoadmapTarget,
        values: list[list[str]],
    ) -> None:
        result = await self._call(
            "sheets_update_values",
            {
                "spreadsheetId": target.spreadsheet_id,
                "range": _sheet_range(target.sheet, "A1"),
                "values": values,
                "valueInputOption": "RAW",
            },
        )
        if result.is_error:
            raise RoadmapSyncError("mcp-gsheets update failed")

    async def clear_rows(
        self,
        target: RoadmapTarget,
        *,
        first_row: int,
        last_row: int,
    ) -> None:
        result = await self._call(
            "sheets_clear_values",
            {
                "spreadsheetId": target.spreadsheet_id,
                "range": _sheet_range(
                    target.sheet, f"A{first_row}:J{last_row}"
                ),
            },
        )
        if result.is_error:
            raise RoadmapSyncError("mcp-gsheets trailing-row clear failed")


def _local_state(
    target: RoadmapTarget,
) -> tuple[NormalizedRoadmap, str, list[list[str]]]:
    normalized = normalize_csv(target.csv_path, repo_root=REPO_ROOT)
    source = target.csv_path.read_text(encoding="utf-8")
    return normalized, source, rows_to_matrix(normalized.rows)


def _print_diff(
    local_text: str,
    remote_text: str,
    *,
    direction: str,
) -> None:
    if direction == "push":
        before, after = remote_text, local_text
        before_name, after_name = "sheet", "csv"
    else:
        before, after = local_text, remote_text
        before_name, after_name = "csv", "sheet"
    diff = unified_diff(
        before,
        after,
        before_name=before_name,
        after_name=after_name,
    )
    print(diff if diff else "No differences.")


def _atomic_write(path: Path, content: str) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        text=True,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


async def synchronize(
    *,
    action: str,
    target: RoadmapTarget,
    mcp: GSheetsMCP,
    write: bool,
) -> None:
    local, local_source, local_matrix = _local_state(target)
    local_markdown = render_markdown(
        target.csv_path,
        local.rows,
        REPO_ROOT,
    )
    markdown_path = target.csv_path.with_suffix(".md")
    current_markdown = (
        markdown_path.read_text(encoding="utf-8")
        if markdown_path.exists()
        else ""
    )
    await mcp.verify_target(target)
    remote_matrix = await mcp.get_values(target)
    remote_raw_text = matrix_to_unchecked_csv_text(remote_matrix)

    if action == "status":
        if not remote_matrix:
            print("Remote roadmap is uninitialized.")
            _print_diff(local.text, remote_raw_text, direction="push")
            return
        try:
            remote = validate_csv_text(
                remote_raw_text,
                target=target,
                repo_root=REPO_ROOT,
            )
        except RoadmapError as exc:
            print(f"Remote roadmap is invalid or requires migration: {exc}")
            return
        differences: list[str] = []
        if local.changed:
            differences.append("local CSV requires normalization")
        if remote.changed:
            differences.append("Google Sheet requires normalization")
        if rows_to_matrix(local.rows) != rows_to_matrix(remote.rows):
            differences.append("normalized task data differs")
        if current_markdown != local_markdown:
            differences.append("generated Markdown is stale")
        if not differences:
            print("Local CSV and Google Sheet are synchronized.")
        else:
            print("; ".join(differences) + ".")
        return

    if action == "push":
        remote_matches = normalize_matrix(local_matrix) == remote_matrix
        markdown_matches = current_markdown == local_markdown
        if not local.changed and remote_matches and markdown_matches:
            print("Local CSV and Google Sheet are already synchronized.")
            return
        if local.changed:
            print(
                unified_diff(
                    local_source,
                    local.text,
                    before_name=target.csv_path.name,
                    after_name=f"{target.csv_path.name} (normalized)",
                )
            )
        if not remote_matches:
            _print_diff(local.text, remote_raw_text, direction="push")
        if not markdown_matches:
            print(
                unified_diff(
                    current_markdown,
                    local_markdown,
                    before_name=markdown_path.name,
                    after_name=f"{markdown_path.name} (generated)",
                )
            )
        if not write:
            print(
                "Dry run only; pass --write to normalize local files and "
                "update Google Sheets."
            )
            return
        if local.changed:
            _atomic_write(target.csv_path, local.text)
        if not markdown_matches:
            _atomic_write(markdown_path, local_markdown)
        previous_rows = len(remote_matrix)
        if not remote_matches:
            await mcp.update_values(target, local_matrix)
            if previous_rows > len(local_matrix):
                await mcp.clear_rows(
                    target,
                    first_row=len(local_matrix) + 1,
                    last_row=previous_rows,
                )
        read_back = await mcp.get_values(target)
        if read_back != normalize_matrix(local_matrix):
            raise RoadmapSyncError(
                "Google Sheets read-back does not match the local CSV"
            )
        print("Local files and Google Sheet normalized; read-back verified.")
        return

    if action == "pull":
        if not remote_matrix:
            raise RoadmapSyncError(
                "remote roadmap is uninitialized; refusing to overwrite local files"
            )
        remote = validate_csv_text(
            remote_raw_text,
            target=target,
            repo_root=REPO_ROOT,
        )
        pulled_markdown = render_markdown(
            target.csv_path,
            remote.rows,
            REPO_ROOT,
        )
        normalized_remote_matrix = rows_to_matrix(remote.rows)
        if (
            local.text == remote.text
            and current_markdown == pulled_markdown
            and not local.changed
            and not remote.changed
        ):
            print("Local files already match Google Sheets.")
            return
        if local.changed:
            print(
                unified_diff(
                    local_source,
                    local.text,
                    before_name=target.csv_path.name,
                    after_name=f"{target.csv_path.name} (normalized)",
                )
            )
        _print_diff(local.text, remote.text, direction="pull")
        markdown_diff = unified_diff(
            current_markdown,
            pulled_markdown,
            before_name=markdown_path.name,
            after_name=f"{markdown_path.name} (from sheet)",
        )
        if markdown_diff:
            print(markdown_diff)
        if remote.changed:
            print("Google Sheet IDs or dependencies require normalization.")
        if not write:
            print(
                "Dry run only; pass --write to update local files and "
                "normalize Google Sheets."
            )
            return
        _atomic_write(target.csv_path, remote.text)
        _atomic_write(markdown_path, pulled_markdown)
        if remote.changed:
            await mcp.update_values(target, normalized_remote_matrix)
            if len(remote_matrix) > len(normalized_remote_matrix):
                await mcp.clear_rows(
                    target,
                    first_row=len(normalized_remote_matrix) + 1,
                    last_row=len(remote_matrix),
                )
        read_back = await mcp.get_values(target)
        if read_back != normalize_matrix(normalized_remote_matrix):
            raise RoadmapSyncError(
                "Google Sheets read-back does not match normalized pull data"
            )
        verified = normalize_csv(target.csv_path, repo_root=REPO_ROOT)
        if verified.changed:
            raise RoadmapSyncError("local CSV remains noncanonical after pull")
        print(
            "Local CSV, generated Markdown, and Google Sheet normalized "
            "from pull."
        )
        return

    raise RoadmapSyncError(f"unsupported action {action!r}")


async def synchronize_with_mcp(
    *,
    action: str,
    target: RoadmapTarget,
    definition: MCPServerDefinition,
    server_name: str,
    write: bool,
) -> None:
    async with GSheetsMCP(
        definition,
        server_name=server_name,
    ) as mcp:
        await synchronize(
            action=action,
            target=target,
            mcp=mcp,
            write=write,
        )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        help="named roadmap config; defaults to roadmaps/config.json",
    )
    parser.add_argument("action", choices=("status", "push", "pull"))
    parser.add_argument("roadmap", help="named roadmap key")
    parser.add_argument(
        "--write",
        action="store_true",
        help="apply push or pull changes; defaults to a dry run",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.action == "status" and args.write:
        print("roadmap sync error: --write is not valid with status", file=sys.stderr)
        return 1
    try:
        registry = load_registry(args.config)
        target = resolve_target(args.roadmap, registry)
        definition = load_mcp_server(registry.mcp)
        unpinned = unpinned_npm_packages(definition)
        if unpinned:
            print(
                "warning: MCP package is unpinned: " + ", ".join(unpinned),
                file=sys.stderr,
            )
        asyncio.run(
            synchronize_with_mcp(
                action=args.action,
                target=target,
                definition=definition,
                server_name=registry.mcp.server,
                write=args.write,
            )
        )
    except (
        RoadmapConfigError,
        RoadmapError,
        RoadmapSyncError,
        OSError,
        RuntimeError,
    ) as exc:
        print(f"roadmap sync error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())