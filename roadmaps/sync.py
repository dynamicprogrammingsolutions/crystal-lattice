#!/usr/bin/env python3
"""Synchronize a named roadmap between its CSV and Google Sheets."""

from __future__ import annotations

import argparse
import csv
import difflib
import io
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2 import service_account

from generate import (
    PRESENTATION_FIELDS,
    REQUIRED_FIELDS,
    NormalizedRoadmap,
    RoadmapError,
    derive_readiness,
    normalize_csv,
    normalize_csv_text,
    render_markdown,
)
from roadmap_config import (
    GoogleSheetsSettings,
    RoadmapConfigError,
    RoadmapTarget,
    load_registry,
    resolve_target,
)


SHEETS_SCOPE = "https://www.googleapis.com/auth/spreadsheets"
SHEETS_API = "https://sheets.googleapis.com/v4/spreadsheets"
MANAGED_SHEET_COLORS = (
    (0.85, 0.92, 0.83),
    (0.99, 0.90, 0.80),
    (0.85, 0.92, 0.97),
    (217 / 255, 210 / 255, 233 / 255),
)


class RoadmapSyncError(RuntimeError):
    """Raised when remote synchronization cannot proceed safely."""


def column_letter(index: int) -> str:
    if index < 0:
        raise ValueError("column index must not be negative")
    value = index + 1
    letters = ""
    while value:
        value, remainder = divmod(value - 1, 26)
        letters = chr(ord("A") + remainder) + letters
    return letters


def csv_text_to_matrix(text: str) -> list[list[str]]:
    return [list(row) for row in csv.reader(io.StringIO(text))]


def rows_to_matrix(roadmap: NormalizedRoadmap) -> list[list[str]]:
    return csv_text_to_matrix(roadmap.text)


def normalize_matrix(values: Any) -> list[list[str]]:
    if not isinstance(values, list):
        raise RoadmapSyncError("Google Sheets values response is not an array")
    if not values:
        return []
    if not isinstance(values[0], list):
        raise RoadmapSyncError("Google Sheets row is not an array")
    width = len(values[0])
    matrix: list[list[str]] = []
    for raw_row in values:
        if not isinstance(raw_row, list):
            raise RoadmapSyncError("Google Sheets row is not an array")
        row = ["" if value is None else str(value) for value in raw_row[:width]]
        row.extend([""] * (width - len(row)))
        matrix.append(row)
    while matrix and not any(cell for cell in matrix[-1]):
        matrix.pop()
    return matrix


def _validate_source_header(header: list[str]) -> None:
    if not header or any(not value for value in header):
        raise RoadmapSyncError("remote roadmap header contains an empty cell")
    lowered = [value.casefold() for value in header]
    if len(lowered) != len(set(lowered)):
        raise RoadmapSyncError("remote roadmap header contains duplicates")
    missing = [
        field for field in REQUIRED_FIELDS if field.casefold() not in lowered
    ]
    if missing:
        raise RoadmapSyncError(
            "remote roadmap is missing required headers: "
            + ",".join(missing)
        )


def matrix_to_csv_text(matrix: list[list[str]]) -> str:
    if not matrix:
        raise RoadmapSyncError("remote roadmap is uninitialized")
    _validate_source_header(matrix[0])
    return matrix_to_unchecked_csv_text(matrix)


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
        task_directory_entry=target.task_directory_entry,
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


def _sheet_range(sheet: str, cells: str | None = None) -> str:
    escaped = sheet.replace("'", "''")
    quoted = f"'{escaped}'"
    return f"{quoted}!{cells}" if cells else quoted


def _sheet_titles(payload: dict[str, Any]) -> list[str]:
    titles: list[str] = []
    sheets = payload.get("sheets", [])
    if not isinstance(sheets, list):
        return titles
    for sheet in sheets:
        if not isinstance(sheet, dict):
            continue
        properties = sheet.get("properties")
        if isinstance(properties, dict) and isinstance(
            properties.get("title"), str
        ):
            titles.append(properties["title"])
    return titles


def _split_sheet_values(values: Any) -> list[list[str]]:
    matrix = normalize_matrix(values)
    if not matrix:
        return []
    header = matrix[0]
    lowered = [value.casefold() for value in header]
    presentation = [value.casefold() for value in PRESENTATION_FIELDS]
    if len(header) >= 2 and lowered[-2:] == presentation:
        width = len(header) - 2
    else:
        if any(value in lowered for value in presentation):
            raise RoadmapSyncError(
                "reserved presentation headers must be the final two columns"
            )
        width = len(header)
    source = [row[:width] for row in matrix]
    while source and not any(source[-1]):
        source.pop()
    if source:
        _validate_source_header(source[0])
    return source


def _formula_is_managed(formula: Any) -> bool:
    if not isinstance(formula, str):
        return False
    column = r"\$[A-Z]+2"
    patterns = (
        rf'^={column}="done"$',
        rf'^={column}="ready"$',
        rf'^={column}="queued"$',
        rf'^=OR\({column}="in progress",{column}="review"\)$',
        rf'^=OR\({column}="pending",{column}="ready"\)$',
    )
    return any(re.fullmatch(pattern, formula) for pattern in patterns)


def _format_has_managed_color(boolean_rule: dict[str, Any]) -> bool:
    cell_format = boolean_rule.get("format")
    if not isinstance(cell_format, dict):
        return False
    color = cell_format.get("backgroundColor")
    if not isinstance(color, dict):
        style = cell_format.get("backgroundColorStyle")
        color = style.get("rgbColor") if isinstance(style, dict) else None
    if not isinstance(color, dict):
        return False
    actual = tuple(
        float(color.get(component, 0.0))
        for component in ("red", "green", "blue")
    )
    return any(
        all(abs(found - expected) < 0.02 for found, expected in zip(
            actual, managed, strict=True
        ))
        for managed in MANAGED_SHEET_COLORS
    )


class GoogleSheetsClient:
    """Small direct Google Sheets REST client for roadmap synchronization."""

    def __init__(self, settings: GoogleSheetsSettings) -> None:
        self.timeout_seconds = settings.timeout_seconds
        self.session = requests.Session()
        self._sheet_metadata: dict[str, dict[str, Any]] = {}
        try:
            credentials = service_account.Credentials.from_service_account_file(
                str(settings.credentials_file),
                scopes=[SHEETS_SCOPE],
            )
            credentials.refresh(GoogleAuthRequest())
        except (
            GoogleAuthError,
            OSError,
            ValueError,
            requests.RequestException,
        ) as exc:
            self.session.close()
            raise RoadmapSyncError(
                "Google Sheets authentication failed"
            ) from exc
        self.session.headers.update(
            {
                "Authorization": f"Bearer {credentials.token}",
                "Accept": "application/json",
            }
        )

    def close(self) -> None:
        self.session.close()

    def _request_json(
        self,
        method: str,
        url: str,
        *,
        operation: str,
        params: dict[str, str] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            response = self.session.request(
                method,
                url,
                params=params,
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, json.JSONDecodeError) as exc:
            raise RoadmapSyncError(
                f"Google Sheets {operation} failed"
            ) from exc
        if not isinstance(data, dict):
            raise RoadmapSyncError(
                f"Google Sheets {operation} returned an invalid response"
            )
        return data

    def verify_target(self, target: RoadmapTarget) -> None:
        payload = self._request_json(
            "GET",
            f"{SHEETS_API}/{target.spreadsheet_id}",
            operation="metadata read",
        )
        if payload.get("spreadsheetId") != target.spreadsheet_id:
            raise RoadmapSyncError(
                "spreadsheet ID does not match named config"
            )
        properties = payload.get("properties")
        title = (
            properties.get("title")
            if isinstance(properties, dict)
            else None
        )
        if title != target.spreadsheet_title:
            raise RoadmapSyncError(
                "spreadsheet title does not match named config"
            )
        if target.sheet not in _sheet_titles(payload):
            raise RoadmapSyncError(
                f"sheet {target.sheet!r} does not exist in spreadsheet"
            )
        sheets = payload.get("sheets", [])
        if isinstance(sheets, list):
            for sheet in sheets:
                if not isinstance(sheet, dict):
                    continue
                sheet_properties = sheet.get("properties")
                if (
                    isinstance(sheet_properties, dict)
                    and sheet_properties.get("title") == target.sheet
                ):
                    self._sheet_metadata[target.key] = sheet
                    break

    def _get_raw_values(self, target: RoadmapTarget) -> list[list[str]]:
        range_name = quote(_sheet_range(target.sheet), safe="")
        payload = self._request_json(
            "GET",
            f"{SHEETS_API}/{target.spreadsheet_id}/values/{range_name}",
            operation="values read",
            params={
                "majorDimension": "ROWS",
                "valueRenderOption": "UNFORMATTED_VALUE",
            },
        )
        values = payload.get("values", [])
        if not isinstance(values, list):
            raise RoadmapSyncError(
                "Google Sheets values response is not an array"
            )
        return values

    def get_values(self, target: RoadmapTarget) -> list[list[str]]:
        return _split_sheet_values(self._get_raw_values(target))

    def _sheet_id_and_grid(self, target: RoadmapTarget) -> tuple[int, int, int]:
        sheet = self._sheet_metadata.get(target.key)
        if not isinstance(sheet, dict):
            raise RoadmapSyncError("spreadsheet metadata is unavailable")
        properties = sheet.get("properties")
        if not isinstance(properties, dict):
            raise RoadmapSyncError("sheet properties are unavailable")
        sheet_id = properties.get("sheetId")
        grid = properties.get("gridProperties")
        if not isinstance(sheet_id, int) or not isinstance(grid, dict):
            raise RoadmapSyncError("sheet grid metadata is unavailable")
        rows = grid.get("rowCount", 0)
        columns = grid.get("columnCount", 0)
        if not isinstance(rows, int) or not isinstance(columns, int):
            raise RoadmapSyncError("sheet grid dimensions are unavailable")
        return sheet_id, rows, columns

    def _ensure_grid_size(
        self,
        target: RoadmapTarget,
        *,
        rows: int,
        columns: int,
    ) -> None:
        sheet_id, current_rows, current_columns = self._sheet_id_and_grid(target)
        if rows <= current_rows and columns <= current_columns:
            return
        self._request_json(
            "POST",
            f"{SHEETS_API}/{target.spreadsheet_id}:batchUpdate",
            operation="grid resize",
            payload={
                "requests": [
                    {
                        "updateSheetProperties": {
                            "properties": {
                                "sheetId": sheet_id,
                                "gridProperties": {
                                    "rowCount": max(rows, current_rows),
                                    "columnCount": max(columns, current_columns),
                                },
                            },
                            "fields": (
                                "gridProperties.rowCount,"
                                "gridProperties.columnCount"
                            ),
                        }
                    }
                ]
            },
        )

    def update_values(
        self,
        target: RoadmapTarget,
        values: list[list[str]],
    ) -> None:
        width = len(values[0]) if values else 0
        self._ensure_grid_size(
            target,
            rows=max(len(values), 1),
            columns=max(width + 2, 1),
        )
        whole_sheet = quote(_sheet_range(target.sheet), safe="")
        self._request_json(
            "POST",
            (
                f"{SHEETS_API}/{target.spreadsheet_id}/values/"
                f"{whole_sheet}:clear"
            ),
            operation="values clear",
            payload={},
        )
        if not values:
            return
        range_name = quote(_sheet_range(target.sheet, "A1"), safe="")
        self._request_json(
            "PUT",
            f"{SHEETS_API}/{target.spreadsheet_id}/values/{range_name}",
            operation="values update",
            params={"valueInputOption": "RAW"},
            payload={"majorDimension": "ROWS", "values": values},
        )

    def get_presentation(
        self,
        target: RoadmapTarget,
        *,
        source_width: int,
    ) -> list[list[str]]:
        start = column_letter(source_width)
        end = column_letter(source_width + 1)
        range_name = quote(
            _sheet_range(target.sheet, f"{start}:{end}"),
            safe="",
        )
        payload = self._request_json(
            "GET",
            f"{SHEETS_API}/{target.spreadsheet_id}/values/{range_name}",
            operation="presentation read",
            params={
                "majorDimension": "ROWS",
                "valueRenderOption": "UNFORMATTED_VALUE",
            },
        )
        values = payload.get("values", [])
        if not isinstance(values, list):
            raise RoadmapSyncError(
                "Google Sheets presentation response is not an array"
            )
        matrix: list[list[str]] = []
        for raw_row in values:
            if not isinstance(raw_row, list):
                raise RoadmapSyncError(
                    "Google Sheets presentation row is not an array"
                )
            row = ["" if value is None else str(value) for value in raw_row[:2]]
            row.extend([""] * (2 - len(row)))
            matrix.append(row)
        while matrix and not any(matrix[-1]):
            matrix.pop()
        return matrix

    def _conditional_format_requests(
        self,
        target: RoadmapTarget,
        *,
        headers: tuple[str, ...],
    ) -> list[dict[str, Any]]:
        sheet_id, _rows, _columns = self._sheet_id_and_grid(target)
        status_column = column_letter(headers.index("status"))
        readiness_column = column_letter(len(headers))
        end_column = len(headers) + len(PRESENTATION_FIELDS)
        formulas_and_colors = (
            (f'=${status_column}2="done"', (0.85, 0.92, 0.83)),
            (
                (
                    f'=OR(${status_column}2="in progress",'
                    f'${status_column}2="review")'
                ),
                (0.99, 0.90, 0.80),
            ),
            (f'=${readiness_column}2="ready"', (0.85, 0.92, 0.97)),
            (
                f'=${readiness_column}2="queued"',
                (217 / 255, 210 / 255, 233 / 255),
            ),
        )

        def is_owned(rule: Any) -> bool:
            if not isinstance(rule, dict):
                return False
            boolean_rule = rule.get("booleanRule")
            if not isinstance(boolean_rule, dict):
                return False
            condition = boolean_rule.get("condition")
            if not isinstance(condition, dict):
                return False
            values = condition.get("values")
            if not isinstance(values, list) or not values:
                return False
            formula = values[0].get("userEnteredValue")
            if not _formula_is_managed(formula):
                return False
            if not _format_has_managed_color(boolean_rule):
                return False
            ranges = rule.get("ranges")
            if not isinstance(ranges, list):
                return False
            return any(
                isinstance(cell_range, dict)
                and cell_range.get("sheetId", sheet_id) == sheet_id
                and cell_range.get("startRowIndex") == 1
                and cell_range.get("startColumnIndex") == 0
                for cell_range in ranges
            )

        requests_payload: list[dict[str, Any]] = []
        sheet = self._sheet_metadata.get(target.key, {})
        existing = (
            sheet.get("conditionalFormats", [])
            if isinstance(sheet, dict)
            else []
        )
        if isinstance(existing, list):
            for index in reversed(range(len(existing))):
                if is_owned(existing[index]):
                    requests_payload.append(
                        {
                            "deleteConditionalFormatRule": {
                                "sheetId": sheet_id,
                                "index": index,
                            }
                        }
                    )

        for formula, (red, green, blue) in reversed(formulas_and_colors):
            requests_payload.append(
                {
                    "addConditionalFormatRule": {
                        "rule": {
                            "ranges": [
                                {
                                    "sheetId": sheet_id,
                                    "startRowIndex": 1,
                                    "startColumnIndex": 0,
                                    "endColumnIndex": end_column,
                                }
                            ],
                            "booleanRule": {
                                "condition": {
                                    "type": "CUSTOM_FORMULA",
                                    "values": [
                                        {"userEnteredValue": formula}
                                    ],
                                },
                                "format": {
                                    "backgroundColor": {
                                        "red": red,
                                        "green": green,
                                        "blue": blue,
                                    }
                                },
                            },
                        },
                        "index": 0,
                    }
                }
            )
        return requests_payload

    def update_presentation(
        self,
        target: RoadmapTarget,
        roadmap: NormalizedRoadmap,
    ) -> None:
        readiness = derive_readiness(roadmap.rows)
        values = [list(PRESENTATION_FIELDS)]
        values.extend(
            [
                readiness[row.internal_id.casefold()][0],
                ";".join(readiness[row.internal_id.casefold()][1]),
            ]
            for row in roadmap.rows
        )
        source_width = len(roadmap.headers)
        self._ensure_grid_size(
            target,
            rows=len(values),
            columns=source_width + len(PRESENTATION_FIELDS),
        )
        start = column_letter(source_width)
        end = column_letter(source_width + 1)
        presentation_range = quote(
            _sheet_range(target.sheet, f"{start}:{end}"),
            safe="",
        )
        self._request_json(
            "POST",
            (
                f"{SHEETS_API}/{target.spreadsheet_id}/values/"
                f"{presentation_range}:clear"
            ),
            operation="presentation clear",
            payload={},
        )
        range_name = quote(
            _sheet_range(target.sheet, f"{start}1"),
            safe="",
        )
        self._request_json(
            "PUT",
            f"{SHEETS_API}/{target.spreadsheet_id}/values/{range_name}",
            operation="presentation update",
            params={"valueInputOption": "RAW"},
            payload={"majorDimension": "ROWS", "values": values},
        )

        formatting_requests = self._conditional_format_requests(
            target,
            headers=roadmap.headers,
        )
        if formatting_requests:
            self._request_json(
                "POST",
                f"{SHEETS_API}/{target.spreadsheet_id}:batchUpdate",
                operation="conditional formatting update",
                payload={"requests": formatting_requests},
            )

        read_back = self.get_presentation(
            target,
            source_width=source_width,
        )
        expected = [[str(cell) for cell in row] for row in values]
        if read_back != expected:
            raise RoadmapSyncError(
                "Google Sheets presentation read-back does not match"
            )


def _repo_root(target: RoadmapTarget) -> Path:
    return (
        target.repository_root.resolve()
        if target.repository_root is not None
        else target.csv_path.parent.resolve()
    )


def _local_state(
    target: RoadmapTarget,
) -> tuple[NormalizedRoadmap, str, list[list[str]]]:
    normalized = normalize_csv(
        target.csv_path,
        repo_root=_repo_root(target),
        task_directory_entry=target.task_directory_entry,
    )
    source = target.csv_path.read_text(encoding="utf-8")
    return normalized, source, rows_to_matrix(normalized)


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
        with os.fdopen(
            descriptor,
            "w",
            encoding="utf-8",
            newline="",
        ) as handle:
            handle.write(content)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _print_warnings(label: str, warnings: tuple[str, ...]) -> None:
    for warning in warnings:
        print(f"{label} warning: {warning}")


def synchronize(
    *,
    action: str,
    target: RoadmapTarget,
    sheets: Any,
    write: bool,
) -> None:
    repo_root = _repo_root(target)
    local, local_source, local_matrix = _local_state(target)
    _print_warnings("local roadmap", local.warnings)
    local_markdown = render_markdown(
        target.csv_path,
        local.rows,
        repo_root,
        local.headers,
    )
    markdown_path = target.csv_path.with_suffix(".md")
    current_markdown = (
        markdown_path.read_text(encoding="utf-8")
        if markdown_path.exists()
        else ""
    )
    sheets.verify_target(target)
    remote_matrix = sheets.get_values(target)
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
                repo_root=repo_root,
            )
        except RoadmapError as exc:
            print(f"Remote roadmap is invalid or requires migration: {exc}")
            return
        _print_warnings("Google Sheet", remote.warnings)
        differences: list[str] = []
        if local.changed:
            differences.append("local CSV requires normalization")
        if remote.changed:
            differences.append("Google Sheet requires normalization")
        if rows_to_matrix(local) != rows_to_matrix(remote):
            differences.append("normalized task data differs")
        if current_markdown != local_markdown:
            differences.append("generated Markdown is stale")
        if not differences:
            print("Local CSV and Google Sheet are synchronized.")
        else:
            print("; ".join(differences) + ".")
        return

    if action == "push":
        remote_matches = local_matrix == remote_matrix
        markdown_matches = current_markdown == local_markdown
        if not local.changed and remote_matches and markdown_matches:
            if write:
                sheets.update_presentation(target, local)
                print(
                    "Local CSV and Google Sheet are synchronized; "
                    "presentation refreshed."
                )
            else:
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
        if not remote_matches:
            sheets.update_values(target, local_matrix)
        read_back = sheets.get_values(target)
        if read_back != local_matrix:
            raise RoadmapSyncError(
                "Google Sheets read-back does not match the local CSV"
            )
        sheets.update_presentation(target, local)
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
            repo_root=repo_root,
        )
        _print_warnings("Google Sheet", remote.warnings)
        pulled_markdown = render_markdown(
            target.csv_path,
            remote.rows,
            repo_root,
            remote.headers,
        )
        normalized_remote_matrix = rows_to_matrix(remote)
        if (
            local.text == remote.text
            and current_markdown == pulled_markdown
            and not local.changed
            and not remote.changed
        ):
            if write:
                sheets.update_presentation(target, remote)
                print(
                    "Local files match Google Sheets; presentation refreshed."
                )
            else:
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
            print("Google Sheet requires normalization.")
        if not write:
            print(
                "Dry run only; pass --write to update local files and "
                "normalize Google Sheets."
            )
            return
        _atomic_write(target.csv_path, remote.text)
        _atomic_write(markdown_path, pulled_markdown)
        if remote.changed:
            sheets.update_values(target, normalized_remote_matrix)
        read_back = sheets.get_values(target)
        if read_back != normalized_remote_matrix:
            raise RoadmapSyncError(
                "Google Sheets read-back does not match normalized pull data"
            )
        sheets.update_presentation(target, remote)
        verified = normalize_csv(
            target.csv_path,
            repo_root=repo_root,
            task_directory_entry=target.task_directory_entry,
        )
        if verified.changed:
            raise RoadmapSyncError("local CSV remains noncanonical after pull")
        print(
            "Local CSV, generated Markdown, and Google Sheet normalized "
            "from pull."
        )
        return

    raise RoadmapSyncError(f"unsupported action {action!r}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        help="named roadmap config; defaults beside this script",
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
        print(
            "roadmap sync error: --write is not valid with status",
            file=sys.stderr,
        )
        return 1
    client: GoogleSheetsClient | None = None
    try:
        registry = load_registry(args.config)
        target = resolve_target(args.roadmap, registry)
        client = GoogleSheetsClient(registry.google_sheets)
        synchronize(
            action=args.action,
            target=target,
            sheets=client,
            write=args.write,
        )
    except (
        RoadmapConfigError,
        RoadmapError,
        RoadmapSyncError,
        OSError,
    ) as exc:
        print(f"roadmap sync error: {exc}", file=sys.stderr)
        return 1
    finally:
        if client is not None:
            client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())