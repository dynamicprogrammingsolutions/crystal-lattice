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


HEADERS = (
    "task",
    "external_id",
    "internal_id",
    "owner",
    "priority",
    "status",
    "declared_dependencies",
    "inferred_dependencies",
)


class FakeSheets:
    def __init__(self, values: list[list[str]]) -> None:
        self.values = sync.normalize_matrix(values)
        self.updated: list[list[str]] | None = None
        self.presentation: generate.NormalizedRoadmap | None = None

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

    def update_presentation(
        self,
        _target: RoadmapTarget,
        roadmap: generate.NormalizedRoadmap,
    ) -> None:
        self.presentation = roadmap


class RoadmapSyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        task_dir = self.root / "work" / "20260101-sample"
        task_dir.mkdir(parents=True)
        (task_dir / "010-first.md").write_text("# First\n", encoding="utf-8")
        (task_dir / "020-second.md").write_text("# Second\n", encoding="utf-8")
        (task_dir / "000-main.md").write_text("# Main\n", encoding="utf-8")
        self.csv_path = self.root / "sample.csv"
        with self.csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=HEADERS)
            writer.writeheader()
            writer.writerow(
                {
                    "task": "work/20260101-sample/010-first.md",
                    "external_id": "",
                    "internal_id": "0101-SA-010",
                    "owner": "Example team",
                    "priority": "must have",
                    "status": "done",
                    "declared_dependencies": "",
                    "inferred_dependencies": "",
                }
            )
        self.target = RoadmapTarget(
            key="sample",
            csv_path=self.csv_path,
            spreadsheet_id="sheet-id",
            spreadsheet_title="Roadmap",
            sheet="Sheet1",
            repository_root=self.root,
        )

    def _local_matrix(self) -> list[list[str]]:
        roadmap = generate.normalize_csv(
            self.csv_path,
            repo_root=self.root,
        )
        return sync.rows_to_matrix(roadmap)

    def test_matrix_header_is_dynamic(self) -> None:
        matrix = sync.normalize_matrix(
            [["task", "owner", "status"], ["one"], [], []]
        )

        self.assertEqual(
            matrix,
            [
                ["task", "owner", "status"],
                ["one", "", ""],
            ],
        )

    def test_column_letters_support_columns_after_z(self) -> None:
        self.assertEqual(sync.column_letter(0), "A")
        self.assertEqual(sync.column_letter(25), "Z")
        self.assertEqual(sync.column_letter(26), "AA")
        self.assertEqual(sync.column_letter(52), "BA")

    def test_sheet_source_strips_trailing_presentation_columns(self) -> None:
        values = [
            [*HEADERS, *generate.PRESENTATION_FIELDS],
            [
                "free task",
                "",
                "FRE-TAS",
                "Team",
                "must have",
                "pending",
                "",
                "",
                "ready",
                "",
            ],
        ]

        source = sync._split_sheet_values(values)

        self.assertEqual(source[0], list(HEADERS))
        self.assertEqual(len(source[1]), len(HEADERS))

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

    def test_conditional_formatting_uses_dynamic_columns(self) -> None:
        client = object.__new__(sync.GoogleSheetsClient)
        client._sheet_metadata = {
            "sample": {
                "properties": {
                    "sheetId": 123,
                    "title": "Sheet1",
                    "gridProperties": {
                        "rowCount": 1000,
                        "columnCount": 30,
                    },
                },
                "conditionalFormats": [
                    {
                        "ranges": [
                            {
                                "startRowIndex": 1,
                                "startColumnIndex": 0,
                                "endColumnIndex": 12,
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
                            },
                            "format": {
                                "backgroundColor": {
                                    "red": 0.85,
                                    "green": 0.92,
                                    "blue": 0.97,
                                }
                            },
                        },
                    }
                ],
            }
        }

        requests = client._conditional_format_requests(
            self.target,
            headers=HEADERS,
        )
        formulas = []
        deletions = []
        for request in requests:
            if "deleteConditionalFormatRule" in request:
                deletions.append(
                    request["deleteConditionalFormatRule"]["index"]
                )
                continue
            rule = request["addConditionalFormatRule"]["rule"]
            formulas.append(
                rule["booleanRule"]["condition"]["values"][0][
                    "userEnteredValue"
                ]
            )
            self.assertEqual(
                rule["ranges"][0]["endColumnIndex"],
                len(HEADERS) + 2,
            )

        self.assertEqual(
            set(formulas),
            {
                '=$F2="done"',
                '=OR($F2="in progress",$F2="review")',
                '=$I2="ready"',
                '=$I2="queued"',
            },
        )
        self.assertEqual(deletions, [0])

    def test_initial_push_preserves_arbitrary_fields(self) -> None:
        sheets = FakeSheets([])

        with redirect_stdout(io.StringIO()):
            sync.synchronize(
                action="push",
                target=self.target,
                sheets=sheets,
                write=True,
            )

        self.assertIsNotNone(sheets.updated)
        self.assertEqual(sheets.updated[0], list(HEADERS))
        self.assertEqual(sheets.updated[1][3], "Example team")
        self.assertIsNotNone(sheets.presentation)

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

    def test_pull_adds_an_arbitrary_column(self) -> None:
        remote = self._local_matrix()
        remote[0].insert(4, "target date")
        remote[1].insert(4, "2026-09-01")
        sheets = FakeSheets(remote)

        with redirect_stdout(io.StringIO()):
            sync.synchronize(
                action="pull",
                target=self.target,
                sheets=sheets,
                write=True,
            )

        rows = list(csv.DictReader(self.csv_path.read_text().splitlines()))
        self.assertEqual(rows[0]["target date"], "2026-09-01")
        self.assertIn(
            "target date",
            self.csv_path.with_suffix(".md").read_text(encoding="utf-8"),
        )

    def test_pull_removes_dependency_to_deleted_row(self) -> None:
        with self.csv_path.open("a", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=HEADERS)
            writer.writerow(
                {
                    "task": "work/20260101-sample/020-second.md",
                    "external_id": "",
                    "internal_id": "0101-SA-020",
                    "owner": "Example team",
                    "priority": "must have",
                    "status": "pending",
                    "declared_dependencies": "0101-SA-010",
                    "inferred_dependencies": "",
                }
            )
        remote = self._local_matrix()
        remote.pop(1)
        sheets = FakeSheets(remote)
        output = io.StringIO()

        with redirect_stdout(output):
            sync.synchronize(
                action="pull",
                target=self.target,
                sheets=sheets,
                write=True,
            )

        row = next(csv.DictReader(self.csv_path.read_text().splitlines()))
        self.assertEqual(row["declared_dependencies"], "")
        self.assertIn("removed missing declared dependency", output.getvalue())

    def test_pull_normalizes_remote_internal_id(self) -> None:
        remote = self._local_matrix()
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
        self.assertEqual(sheets.updated[1][2], "0101-S-010")

    def test_empty_remote_pull_is_rejected(self) -> None:
        sheets = FakeSheets([])

        with self.assertRaisesRegex(sync.RoadmapSyncError, "uninitialized"):
            sync.synchronize(
                action="pull",
                target=self.target,
                sheets=sheets,
                write=True,
            )


if __name__ == "__main__":
    unittest.main()