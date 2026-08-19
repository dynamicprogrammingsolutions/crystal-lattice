from __future__ import annotations

import csv
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import generate  # noqa: E402
import sync  # noqa: E402
from roadmap_config import GoogleSheetsSettings, RoadmapTarget  # noqa: E402


class FakeSheets:
    def __init__(self, values: list[list[str]]) -> None:
        self.values = values
        self.updated: list[list[str]] | None = None
        self.cleared: tuple[int, int] | None = None
        self.presentation_rows: list[generate.Row] | None = None

    def verify_target(self, _target: RoadmapTarget) -> None:
        return None

    def get_values(self, _target: RoadmapTarget) -> list[list[str]]:
        return sync.normalize_matrix(self.values)

    def update_values(
        self,
        _target: RoadmapTarget,
        values: list[list[str]],
    ) -> None:
        self.updated = values
        self.values = values

    def clear_rows(
        self,
        _target: RoadmapTarget,
        *,
        first_row: int,
        last_row: int,
    ) -> None:
        self.cleared = (first_row, last_row)

    def update_presentation(
        self,
        _target: RoadmapTarget,
        rows: list[generate.Row],
    ) -> None:
        self.presentation_rows = rows


class RoadmapSyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.csv_path = self.root / "release.csv"
        with self.csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=generate.FIELDS)
            writer.writeheader()
            writer.writerow(
                {
                    "task": (
                        "tasks/20260804-open-source-public-release/"
                        "010-sensitive-data-and-history-release-gate.md"
                    ),
                    "external_id": "",
                    "internal_id": "0804-OS-010",
                    "title": "First",
                    "purpose": "First purpose.",
                    "priority": "must have",
                    "status": "done",
                    "declared_dependencies": "",
                    "inferred_dependencies": "",
                    "notes": "",
                }
            )
        self.target = RoadmapTarget(
            key="release",
            csv_path=self.csv_path,
            spreadsheet_id="sheet-id",
            spreadsheet_title="Roadmap",
            sheet="Sheet1",
        )

    def test_matrix_to_csv_requires_exact_header(self) -> None:
        with self.assertRaisesRegex(sync.RoadmapSyncError, "header"):
            sync.matrix_to_csv_text([["wrong"]])

    def test_normalize_matrix_pads_cells_and_drops_blank_rows(self) -> None:
        matrix = sync.normalize_matrix(
            [["task", "external_id"], ["one"], [], []]
        )

        self.assertEqual(len(matrix), 2)
        self.assertEqual(len(matrix[0]), len(generate.FIELDS))
        self.assertEqual(matrix[1][0], "one")

    def test_direct_client_treats_missing_values_as_empty(self) -> None:
        client = object.__new__(sync.GoogleSheetsClient)
        client._request_json = lambda *_args, **_kwargs: {}

        values = client.get_values(self.target)

        self.assertEqual(values, [])

    def test_direct_client_redacts_authentication_failure(self) -> None:
        settings = GoogleSheetsSettings(
            credentials_file=Path("/private/credential.json"),
            timeout_seconds=30,
        )
        with patch.object(
            sync.service_account.Credentials,
            "from_service_account_file",
            side_effect=ValueError("/private/credential.json is invalid"),
        ):
            with self.assertRaisesRegex(
                sync.RoadmapSyncError,
                "^Google Sheets authentication failed$",
            ):
                sync.GoogleSheetsClient(settings)

    def test_conditional_formatting_rules_cover_whole_managed_row(self) -> None:
        client = object.__new__(sync.GoogleSheetsClient)
        client._sheet_metadata = {
            "release": {
                "properties": {
                    "sheetId": 123,
                    "title": "Sheet1",
                },
                "conditionalFormats": [
                    {
                        "ranges": [
                            {
                                "startRowIndex": 1,
                                "startColumnIndex": 0,
                                "endColumnIndex": 12,
                                "endRowIndex": 1000,
                            }
                        ],
                        "booleanRule": {
                            "condition": {
                                "type": "CUSTOM_FORMULA",
                                "values": [
                                    {
                                        "userEnteredValue": (
                                            '=OR($G2="pending",$K2="ready")'
                                        )
                                    }
                                ],
                            }
                        },
                    }
                ],
            }
        }

        requests = client._conditional_format_requests(self.target)
        formulas = []
        deleted = []
        for request in requests:
            delete = request.get("deleteConditionalFormatRule")
            if delete:
                deleted.append(delete["index"])
                continue
            add = request.get("addConditionalFormatRule")
            if not add:
                continue
            rule = add["rule"]
            cell_range = rule["ranges"][0]
            formulas.append(
                rule["booleanRule"]["condition"]["values"][0][
                    "userEnteredValue"
                ]
            )
            self.assertEqual(cell_range["startColumnIndex"], 0)
            self.assertEqual(cell_range["endColumnIndex"], 12)
            self.assertEqual(cell_range["startRowIndex"], 1)

        self.assertEqual(
            set(formulas),
            {
                '=$G2="done"',
                '=$K2="ready"',
                '=$K2="queued"',
                '=OR($G2="in progress",$G2="review")',
            },
        )
        self.assertEqual(deleted, [0])

    def test_initial_push_writes_and_verifies(self) -> None:
        sheets = FakeSheets([])

        with redirect_stdout(io.StringIO()):
            sync.synchronize(
                action="push",
                target=self.target,
                sheets=sheets,
                write=True,
            )

        self.assertIsNotNone(sheets.updated)
        self.assertEqual(sheets.updated[0], list(generate.FIELDS))
        self.assertIsNotNone(sheets.presentation_rows)

    def test_push_dry_run_does_not_write(self) -> None:
        sheets = FakeSheets([])

        with redirect_stdout(io.StringIO()):
            sync.synchronize(
                action="push",
                target=self.target,
                sheets=sheets,
                write=False,
            )

        self.assertIsNone(sheets.updated)

    def test_push_clears_only_trailing_old_rows(self) -> None:
        rows = generate._read_rows(self.csv_path, sync.REPO_ROOT)
        old_values = sync.rows_to_matrix(rows)
        old_values.append(["stale"] + [""] * (len(generate.FIELDS) - 1))
        sheets = FakeSheets(old_values)

        with redirect_stdout(io.StringIO()):
            sync.synchronize(
                action="push",
                target=self.target,
                sheets=sheets,
                write=True,
            )

        self.assertEqual(
            sheets.cleared,
            (len(old_values), len(old_values)),
        )

    def test_pull_updates_csv_and_generated_markdown(self) -> None:
        rows = generate._read_rows(self.csv_path, sync.REPO_ROOT)
        remote = sync.rows_to_matrix(rows)
        remote[1][3] = "Updated from sheet"
        sheets = FakeSheets(remote)

        with redirect_stdout(io.StringIO()):
            sync.synchronize(
                action="pull",
                target=self.target,
                sheets=sheets,
                write=True,
            )

        self.assertIn(
            "Updated from sheet",
            self.csv_path.read_text(encoding="utf-8"),
        )
        self.assertIn(
            "Updated from sheet",
            self.csv_path.with_suffix(".md").read_text(encoding="utf-8"),
        )

    def test_pull_normalizes_remote_internal_id_and_writes_back(self) -> None:
        rows = generate._read_rows(self.csv_path, sync.REPO_ROOT)
        remote = sync.rows_to_matrix(rows)
        remote[1][2] = "MANUAL-ID"
        sheets = FakeSheets(remote)

        with redirect_stdout(io.StringIO()):
            sync.synchronize(
                action="pull",
                target=self.target,
                sheets=sheets,
                write=True,
            )

        self.assertIsNotNone(sheets.updated)
        self.assertEqual(sheets.updated[1][2], "0804-OS-010")
        self.assertIn(
            ",0804-OS-010,",
            self.csv_path.read_text(encoding="utf-8"),
        )

    def test_pull_normalizes_local_internal_id_when_remote_is_canonical(
        self,
    ) -> None:
        rows = generate._read_rows(self.csv_path, sync.REPO_ROOT)
        remote = sync.rows_to_matrix(rows)
        local_text = self.csv_path.read_text(encoding="utf-8")
        self.csv_path.write_text(
            local_text.replace("0804-OS-010", "MANUAL-ID", 1),
            encoding="utf-8",
        )
        sheets = FakeSheets(remote)

        with redirect_stdout(io.StringIO()):
            sync.synchronize(
                action="pull",
                target=self.target,
                sheets=sheets,
                write=True,
            )

        self.assertIn(
            ",0804-OS-010,",
            self.csv_path.read_text(encoding="utf-8"),
        )

    def test_empty_remote_pull_is_rejected(self) -> None:
        sheets = FakeSheets([])

        with self.assertRaisesRegex(
            sync.RoadmapSyncError, "uninitialized"
        ):
            sync.synchronize(
                action="pull",
                target=self.target,
                sheets=sheets,
                write=True,
            )


if __name__ == "__main__":
    unittest.main()