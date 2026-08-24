from __future__ import annotations

import csv
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import generate  # noqa: E402


HEADERS = (
    "task",
    "external_id",
    "internal_id",
    "owner",
    "custom field",
    "priority",
    "status",
    "declared_dependencies",
    "inferred_dependencies",
)


class RoadmapGeneratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.sources = self.root / "planning-data"
        self.sources.mkdir()
        self.task_dir = self.root / "work" / "20260101-sample-project"
        self.task_dir.mkdir(parents=True)
        for name in ("000-main.md", "010-first.md", "020-second.md"):
            (self.task_dir / name).write_text(
                f"# {name}\n", encoding="utf-8"
            )
        (self.root / "work" / "20260102-standalone.md").write_text(
            "# Standalone\n", encoding="utf-8"
        )

    def _write_csv(
        self,
        rows: list[dict[str, str]],
        *,
        headers: tuple[str, ...] = HEADERS,
    ) -> Path:
        path = self.sources / "sample.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def _row(self, **overrides: str) -> dict[str, str]:
        row = {
            "task": "work/20260101-sample-project/010-first.md",
            "external_id": "",
            "internal_id": "",
            "owner": "Example team",
            "custom field": "Arbitrary value",
            "priority": "must have",
            "status": "done",
            "declared_dependencies": "",
            "inferred_dependencies": "",
        }
        row.update(overrides)
        return row

    def test_arbitrary_fields_round_trip_and_render_in_order(self) -> None:
        csv_path = self._write_csv([self._row()])

        output = generate.generate(csv_path, repo_root=self.root)
        normalized = generate.normalize_csv(csv_path, repo_root=self.root)
        rendered = output.read_text(encoding="utf-8")

        self.assertEqual(normalized.headers, HEADERS)
        self.assertEqual(normalized.rows[0].field_value("owner"), "Example team")
        self.assertEqual(
            normalized.rows[0].field_value("custom field"),
            "Arbitrary value",
        )
        self.assertIn("| Order | ID | owner | custom field |", rendered)
        self.assertIn("Example team | Arbitrary value", rendered)
        self.assertIn('style="color:#188038"', rendered)
        self.assertNotIn("title", generate.REQUIRED_FIELDS)
        self.assertNotIn("purpose", generate.REQUIRED_FIELDS)

    def test_arbitrary_field_after_status_renders_after_status(self) -> None:
        headers = list(HEADERS)
        headers.insert(headers.index("status") + 1, "finished on")
        csv_path = self._write_csv(
            [self._row(**{"finished on": "2026-01-02"})],
            headers=tuple(headers),
        )

        rendered = generate.generate(
            csv_path,
            repo_root=self.root,
        ).read_text(encoding="utf-8")

        self.assertIn("| Priority | Status | finished on |", rendered)
        self.assertIn("| must have | done | 2026-01-02 |", rendered)

    def test_task_paths_are_portable_outside_tasks_directory(self) -> None:
        csv_path = self._write_csv(
            [self._row(task="work/20260101-sample-project")]
        )

        output = generate.generate(csv_path, repo_root=self.root)
        rendered = output.read_text(encoding="utf-8")

        self.assertIn("0101-SP", csv_path.read_text(encoding="utf-8"))
        self.assertIn(
            "../work/20260101-sample-project/000-main.md",
            rendered,
        )

    def test_standalone_task_has_deterministic_id(self) -> None:
        csv_path = self._write_csv(
            [self._row(task="work/20260102-standalone.md")]
        )

        generate.generate(csv_path, repo_root=self.root)

        self.assertIn(",0102-S,", csv_path.read_text(encoding="utf-8"))

    def test_aliases_are_canonicalized(self) -> None:
        first = "work/20260101-sample-project/010-first.md"
        csv_path = self._write_csv(
            [
                self._row(internal_id="OLD"),
                self._row(
                    task="work/20260101-sample-project/020-second.md",
                    external_id="EX-7",
                    internal_id="MANUAL",
                    status="review",
                    declared_dependencies=first,
                ),
                self._row(
                    task="free placeholder",
                    status="pending",
                    inferred_dependencies="MANUAL",
                ),
            ]
        )

        generate.generate(csv_path, repo_root=self.root)
        rows = list(csv.DictReader(csv_path.read_text().splitlines()))

        self.assertEqual(rows[0]["internal_id"], "0101-SP-010")
        self.assertEqual(rows[1]["internal_id"], "EX-7-020")
        self.assertEqual(rows[1]["declared_dependencies"], "0101-SP-010")
        self.assertEqual(rows[2]["inferred_dependencies"], "EX-7-020")

    def test_unknown_dependencies_are_removed_with_warning(self) -> None:
        csv_path = self._write_csv(
            [
                self._row(
                    status="pending",
                    declared_dependencies="DELETED-010",
                    inferred_dependencies="DELETED-020",
                )
            ]
        )
        stderr = io.StringIO()

        with redirect_stderr(stderr):
            generate.generate(csv_path, repo_root=self.root)
        row = next(csv.DictReader(csv_path.read_text().splitlines()))

        self.assertEqual(row["declared_dependencies"], "")
        self.assertEqual(row["inferred_dependencies"], "")
        self.assertIn("removed missing declared dependency", stderr.getvalue())
        self.assertIn("removed missing inferred dependency", stderr.getvalue())

    def test_check_reports_dependency_cleanup_without_writing(self) -> None:
        csv_path = self._write_csv(
            [self._row(status="pending", declared_dependencies="MISSING")]
        )
        before = csv_path.read_text(encoding="utf-8")

        with self.assertRaisesRegex(generate.RoadmapError, "normalization"):
            generate.generate(csv_path, repo_root=self.root, check=True)

        self.assertEqual(csv_path.read_text(encoding="utf-8"), before)

    def test_shared_external_id_is_ambiguous_as_dependency(self) -> None:
        csv_path = self._write_csv(
            [
                self._row(external_id="EX-7"),
                self._row(
                    task="work/20260101-sample-project/020-second.md",
                    external_id="EX-7",
                    status="pending",
                ),
                self._row(
                    task="free placeholder",
                    status="pending",
                    declared_dependencies="EX-7",
                ),
            ]
        )

        with self.assertRaisesRegex(
            generate.RoadmapError, "ambiguous external ID"
        ):
            generate.generate(csv_path, repo_root=self.root)

    def test_readiness_and_primary_id_colors(self) -> None:
        csv_path = self._write_csv(
            [
                self._row(status="done"),
                self._row(
                    task="work/20260101-sample-project/020-second.md",
                    status="in progress",
                    declared_dependencies="0101-SP-010",
                ),
                self._row(task="ready task", status="pending"),
                self._row(
                    task="queued task",
                    status="pending",
                    declared_dependencies="0101-SP-020",
                ),
                self._row(
                    task="blocked task",
                    status="pending",
                    declared_dependencies="QUE-TAS",
                ),
            ]
        )

        output = generate.generate(csv_path, repo_root=self.root)
        normalized = generate.normalize_csv(csv_path, repo_root=self.root)
        readiness = generate.derive_readiness(normalized.rows)
        rendered = output.read_text(encoding="utf-8")

        states = {
            row.task: readiness[row.internal_id.casefold()][0]
            for row in normalized.rows
        }
        self.assertEqual(states["ready task"], "ready")
        self.assertEqual(states["queued task"], "queued")
        self.assertEqual(states["blocked task"], "blocked")
        for color in generate.READINESS_LINK_COLORS.values():
            self.assertIn(color, rendered)

    def test_blocking_dependency_link_stays_red(self) -> None:
        csv_path = self._write_csv(
            [
                self._row(status="in progress"),
                self._row(
                    task="work/20260101-sample-project/020-second.md",
                    status="pending",
                    declared_dependencies="0101-SP-010",
                ),
            ]
        )

        rendered = generate.generate(
            csv_path, repo_root=self.root
        ).read_text(encoding="utf-8")

        self.assertIn(
            '<a style="color:red" href="../work/'
            '20260101-sample-project/010-first.md">0101-SP-010</a>',
            rendered,
        )

    def test_preserves_done_row_after_non_done_row(self) -> None:
        csv_path = self._write_csv(
            [
                self._row(status="pending"),
                self._row(
                    task="work/20260101-sample-project/020-second.md",
                    status="done",
                ),
            ]
        )

        generate.generate(csv_path, repo_root=self.root)
        rows = list(csv.DictReader(csv_path.read_text().splitlines()))

        self.assertEqual([row["status"] for row in rows], ["pending", "done"])

    def test_rejects_dependency_that_appears_later(self) -> None:
        csv_path = self._write_csv(
            [
                self._row(
                    status="pending",
                    declared_dependencies="0101-SP-020",
                ),
                self._row(
                    task="work/20260101-sample-project/020-second.md",
                    status="pending",
                ),
            ]
        )

        with self.assertRaisesRegex(
            generate.RoadmapError, "must appear above"
        ):
            generate.generate(csv_path, repo_root=self.root)

    def test_rejects_reserved_or_missing_headers(self) -> None:
        headers = (*HEADERS, "readiness")
        csv_path = self._write_csv(
            [self._row(readiness="manual")],
            headers=headers,
        )
        with self.assertRaisesRegex(
            generate.RoadmapError, "reserved presentation"
        ):
            generate.generate(csv_path, repo_root=self.root)

        headers = tuple(header for header in HEADERS if header != "status")
        row = self._row()
        del row["status"]
        csv_path = self._write_csv([row], headers=headers)
        with self.assertRaisesRegex(
            generate.RoadmapError, "missing required headers"
        ):
            generate.generate(csv_path, repo_root=self.root)

    def test_rejects_path_traversal(self) -> None:
        csv_path = self._write_csv([self._row(task="../outside.md")])

        with self.assertRaisesRegex(generate.RoadmapError, "escapes"):
            generate.generate(csv_path, repo_root=self.root)

    def test_check_rejects_stale_markdown(self) -> None:
        csv_path = self._write_csv([self._row()])
        output = generate.generate(csv_path, repo_root=self.root)
        generate.generate(csv_path, repo_root=self.root, check=True)
        output.write_text("stale\n", encoding="utf-8")

        with self.assertRaisesRegex(generate.RoadmapError, "stale"):
            generate.generate(csv_path, repo_root=self.root, check=True)


if __name__ == "__main__":
    unittest.main()