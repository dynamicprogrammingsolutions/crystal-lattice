#!/usr/bin/env python3
"""Synchronize a named roadmap between its CSV and Google Sheets."""

from __future__ import annotations

import argparse
import csv
import difflib
import io
import json
import os
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
    FIELDS,
    NormalizedRoadmap,
    Row,
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


REPO_ROOT = Path(__file__).resolve().parent.parent
SHEETS_SCOPE = "https://www.googleapis.com/auth/spreadsheets"
SHEETS_API = "https://sheets.googleapis.com/v4/spreadsheets"


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
        row = [
            "" if value is None else str(value)
            for value in raw_row[: len(FIELDS)]
        ]
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
                properties = sheet.get("properties")
                if (
                    isinstance(properties, dict)
                    and properties.get("title") == target.sheet
                ):
                    self._sheet_metadata[target.key] = sheet
                    break

    def get_values(self, target: RoadmapTarget) -> list[list[str]]:
        range_name = quote(_sheet_range(target.sheet, "A:J"), safe="")
        payload = self._request_json(
            "GET",
            f"{SHEETS_API}/{target.spreadsheet_id}/values/{range_name}",
            operation="values read",
            params={
                "majorDimension": "ROWS",
                "valueRenderOption": "UNFORMATTED_VALUE",
            },
        )
        return normalize_matrix(payload.get("values", []))

    def update_values(
        self,
        target: RoadmapTarget,
        values: list[list[str]],
    ) -> None:
        range_name = quote(_sheet_range(target.sheet, "A1"), safe="")
        self._request_json(
            "PUT",
            f"{SHEETS_API}/{target.spreadsheet_id}/values/{range_name}",
            operation="values update",
            params={"valueInputOption": "RAW"},
            payload={"majorDimension": "ROWS", "values": values},
        )

    def clear_rows(
        self,
        target: RoadmapTarget,
        *,
        first_row: int,
        last_row: int,
    ) -> None:
        range_name = quote(
            _sheet_range(target.sheet, f"A{first_row}:J{last_row}"),
            safe="",
        )
        self._request_json(
            "POST",
            (
                f"{SHEETS_API}/{target.spreadsheet_id}/values/"
                f"{range_name}:clear"
            ),
            operation="trailing-row clear",
            payload={},
        )

    def get_presentation(self, target: RoadmapTarget) -> list[list[str]]:
        range_name = quote(_sheet_range(target.sheet, "K:L"), safe="")
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
    ) -> list[dict[str, Any]]:
        sheet = self._sheet_metadata.get(target.key)
        if not isinstance(sheet, dict):
            raise RoadmapSyncError("spreadsheet metadata is unavailable")
        properties = sheet.get("properties")
        if not isinstance(properties, dict):
            raise RoadmapSyncError("sheet properties are unavailable")
        sheet_id = properties.get("sheetId")
        if not isinstance(sheet_id, int):
            raise RoadmapSyncError("numeric sheet ID is unavailable")

        formulas_and_colors = (
            ('=$G2="done"', (0.85, 0.92, 0.83)),
            (
                '=OR($G2="in progress",$G2="review")',
                (0.99, 0.90, 0.80),
            ),
            (
                '=$K2="ready"',
                (0.85, 0.92, 0.97),
            ),
            (
                '=$K2="queued"',
                (
                    217 / 255,
                    210 / 255,
                    233 / 255,
                ),
            ),
        )
        owned_formulas = {
            formula for formula, _color in formulas_and_colors
        } | {'=OR($G2="pending",$K2="ready")'}

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
            if formula not in owned_formulas:
                return False
            ranges = rule.get("ranges")
            if not isinstance(ranges, list):
                return False
            return any(
                isinstance(cell_range, dict)
                and cell_range.get("sheetId", sheet_id) == sheet_id
                and cell_range.get("startRowIndex") == 1
                and cell_range.get("startColumnIndex") == 0
                and cell_range.get("endColumnIndex") == 12
                for cell_range in ranges
            )

        requests_payload: list[dict[str, Any]] = []
        existing = sheet.get("conditionalFormats", [])
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
                                    "endColumnIndex": 12,
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
        rows: list[Row],
    ) -> None:
        readiness = derive_readiness(rows)
        values = [["readiness", "blocking_dependencies"]]
        values.extend(
            [
                readiness[row.internal_id.casefold()][0],
                ";".join(readiness[row.internal_id.casefold()][1]),
            ]
            for row in rows
        )
        range_name = quote(_sheet_range(target.sheet, "K1"), safe="")
        self._request_json(
            "PUT",
            f"{SHEETS_API}/{target.spreadsheet_id}/values/{range_name}",
            operation="presentation update",
            params={"valueInputOption": "RAW"},
            payload={"majorDimension": "ROWS", "values": values},
        )

        sheet = self._sheet_metadata.get(target.key, {})
        properties = (
            sheet.get("properties") if isinstance(sheet, dict) else None
        )
        grid = (
            properties.get("gridProperties")
            if isinstance(properties, dict)
            else None
        )
        row_count = (
            grid.get("rowCount")
            if isinstance(grid, dict)
            and isinstance(grid.get("rowCount"), int)
            else len(values)
        )
        if row_count > len(values):
            trailing_range = quote(
                _sheet_range(
                    target.sheet,
                    f"K{len(values) + 1}:L{row_count}",
                ),
                safe="",
            )
            self._request_json(
                "POST",
                (
                    f"{SHEETS_API}/{target.spreadsheet_id}/values/"
                    f"{trailing_range}:clear"
                ),
                operation="presentation trailing-row clear",
                payload={},
            )

        formatting_requests = self._conditional_format_requests(target)
        if formatting_requests:
            self._request_json(
                "POST",
                f"{SHEETS_API}/{target.spreadsheet_id}:batchUpdate",
                operation="conditional formatting update",
                payload={"requests": formatting_requests},
            )

        read_back = self.get_presentation(target)
        expected = [[str(cell) for cell in row] for row in values]
        if read_back != expected:
            raise RoadmapSyncError(
                "Google Sheets presentation read-back does not match"
            )


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


def synchronize(
    *,
    action: str,
    target: RoadmapTarget,
    sheets: Any,
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
            if write:
                sheets.update_presentation(target, local.rows)
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
        previous_rows = len(remote_matrix)
        if not remote_matches:
            sheets.update_values(target, local_matrix)
            if previous_rows > len(local_matrix):
                sheets.clear_rows(
                    target,
                    first_row=len(local_matrix) + 1,
                    last_row=previous_rows,
                )
        read_back = sheets.get_values(target)
        if read_back != normalize_matrix(local_matrix):
            raise RoadmapSyncError(
                "Google Sheets read-back does not match the local CSV"
            )
        sheets.update_presentation(target, local.rows)
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
            if write:
                sheets.update_presentation(target, remote.rows)
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
            sheets.update_values(target, normalized_remote_matrix)
            if len(remote_matrix) > len(normalized_remote_matrix):
                sheets.clear_rows(
                    target,
                    first_row=len(normalized_remote_matrix) + 1,
                    last_row=len(remote_matrix),
                )
        read_back = sheets.get_values(target)
        if read_back != normalize_matrix(normalized_remote_matrix):
            raise RoadmapSyncError(
                "Google Sheets read-back does not match normalized pull data"
            )
        sheets.update_presentation(target, remote.rows)
        verified = normalize_csv(target.csv_path, repo_root=REPO_ROOT)
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