from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import generate  # noqa: E402


class RoadmapGeneratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.roadmaps = self.root / "roadmaps"
        self.roadmaps.mkdir()
        self.task_dir = (
            self.root / "tasks" / "20260804-open-source-public-release"
        )
        self.task_dir.mkdir(parents=True)
        for name in ("000-main.md", "010-first.md", "020-second.md"):
            (self.task_dir / name).write_text(
                f"# {name}\n", encoding="utf-8"
            )
        (self.root / "tasks" / "20260729-standalone-task.md").write_text(
            "# Standalone\n", encoding="utf-8"
        )

    def _write_csv(self, rows: list[dict[str, str]]) -> Path:
        path = self.roadmaps / "test-roadmap.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=generate.FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def _row(self, **overrides: str) -> dict[str, str]:
        row = {
            "task": (
                "tasks/20260804-open-source-public-release/010-first.md"
            ),
            "external_id": "",
            "internal_id": "",
            "title": "First task",
            "purpose": "Establish the first result.",
            "priority": "must have",
            "status": "done",
            "declared_dependencies": "",
            "inferred_dependencies": "",
            "notes": "",
        }
        row.update(overrides)
        return row

    def test_normalizes_ids_aliases_links_and_free_task(self) -> None:
        first_task = (
            "tasks/20260804-open-source-public-release/010-first.md"
        )
        csv_path = self._write_csv(
            [
                self._row(internal_id="OLD-FIRST"),
                self._row(
                    task=(
                        "tasks/20260804-open-source-public-release/"
                        "020-second.md"
                    ),
                    external_id="CL-368",
                    internal_id="MANUAL-ID",
                    title="Second task",
                    status="review",
                    declared_dependencies=first_task,
                ),
                self._row(
                    task="website-ios-review",
                    internal_id="WEB-TBD",
                    title="Website placeholder",
                    status="pending",
                    inferred_dependencies="MANUAL-ID",
                ),
            ]
        )

        output = generate.generate(csv_path, repo_root=self.root)
        rendered = output.read_text(encoding="utf-8")
        normalized = csv_path.read_text(encoding="utf-8")

        self.assertIn("[`0804-OS-010`](../tasks/", rendered)
        self.assertIn("[`CL-368-020`](../tasks/", rendered)
        self.assertIn("| `WEB-IOS` | Website placeholder |", rendered)
        self.assertIn("| First task |", rendered)
        self.assertIn("| Second task |", rendered)
        self.assertIn("| `CL-368` |", rendered)
        self.assertIn("*(inferred)*", rendered)
        self.assertIn(
            "[Updating roadmaps](docs/updating-roadmaps.md)",
            rendered,
        )
        self.assertIn(",0804-OS-010,", normalized)
        self.assertIn(",CL-368-020,", normalized)
        self.assertIn(",WEB-IOS,", normalized)
        self.assertNotIn("OLD-FIRST", normalized)
        self.assertNotIn("MANUAL-ID", normalized)

    def test_task_directory_links_to_main_task(self) -> None:
        csv_path = self._write_csv(
            [
                self._row(
                    task="tasks/20260804-open-source-public-release/",
                    internal_id="",
                )
            ]
        )

        output = generate.generate(csv_path, repo_root=self.root)
        rendered = output.read_text(encoding="utf-8")

        self.assertIn("[`0804-OS`](../tasks/", rendered)
        self.assertIn("| First task |", rendered)
        self.assertIn(
            "../tasks/20260804-open-source-public-release/000-main.md",
            rendered,
        )

    def test_standalone_task_has_deterministic_id(self) -> None:
        csv_path = self._write_csv(
            [
                self._row(
                    task="tasks/20260729-standalone-task.md",
                    internal_id="",
                )
            ]
        )

        generate.generate(csv_path, repo_root=self.root)

        self.assertIn(
            ",0729-ST,",
            csv_path.read_text(encoding="utf-8"),
        )

    def test_shared_external_id_is_ambiguous_as_dependency(self) -> None:
        csv_path = self._write_csv(
            [
                self._row(external_id="CL-368"),
                self._row(
                    task=(
                        "tasks/20260804-open-source-public-release/"
                        "020-second.md"
                    ),
                    external_id="CL-368",
                    status="pending",
                ),
                self._row(
                    task="website",
                    status="pending",
                    declared_dependencies="CL-368",
                ),
            ]
        )

        with self.assertRaisesRegex(
            generate.RoadmapError, "ambiguous external ID"
        ):
            generate.generate(csv_path, repo_root=self.root)

    def test_unique_external_id_dependency_is_canonicalized(self) -> None:
        csv_path = self._write_csv(
            [
                self._row(external_id="CL-368"),
                self._row(
                    task="website",
                    status="pending",
                    declared_dependencies="CL-368",
                ),
            ]
        )

        generate.generate(csv_path, repo_root=self.root)
        rows = list(csv.DictReader(csv_path.read_text().splitlines()))

        self.assertEqual(rows[0]["internal_id"], "CL-368-010")
        self.assertEqual(
            rows[1]["declared_dependencies"],
            "CL-368-010",
        )

    def test_duplicate_previous_internal_id_is_rejected(self) -> None:
        csv_path = self._write_csv(
            [
                self._row(internal_id="OLD"),
                self._row(
                    task=(
                        "tasks/20260804-open-source-public-release/"
                        "020-second.md"
                    ),
                    internal_id="OLD",
                    status="pending",
                ),
            ]
        )

        with self.assertRaisesRegex(
            generate.RoadmapError, "ambiguous previous internal ID"
        ):
            generate.generate(csv_path, repo_root=self.root)

    def test_free_name_collision_uses_deterministic_hash(self) -> None:
        csv_path = self._write_csv(
            [
                self._row(task="website-ios", internal_id=""),
                self._row(
                    task="webbing-ios",
                    internal_id="",
                    status="pending",
                ),
            ]
        )

        generate.generate(csv_path, repo_root=self.root)
        rows = list(csv.DictReader(csv_path.read_text().splitlines()))

        self.assertRegex(rows[0]["internal_id"], r"^WEB-IOS-[A-F0-9]{4}$")
        self.assertRegex(rows[1]["internal_id"], r"^WEB-IOS-[A-F0-9]{4}$")
        self.assertNotEqual(rows[0]["internal_id"], rows[1]["internal_id"])

    def test_rejects_done_row_after_non_done_row(self) -> None:
        csv_path = self._write_csv(
            [
                self._row(status="pending"),
                self._row(
                    task=(
                        "tasks/20260804-open-source-public-release/"
                        "020-second.md"
                    ),
                    status="done",
                ),
            ]
        )

        with self.assertRaisesRegex(
            generate.RoadmapError, "done rows must be at the top"
        ):
            generate.generate(csv_path, repo_root=self.root)

    def test_rejects_dependency_that_appears_later(self) -> None:
        csv_path = self._write_csv(
            [
                self._row(
                    status="pending",
                    declared_dependencies="0804-OS-020",
                ),
                self._row(
                    task=(
                        "tasks/20260804-open-source-public-release/"
                        "020-second.md"
                    ),
                    status="pending",
                ),
            ]
        )

        with self.assertRaisesRegex(
            generate.RoadmapError, "must appear above"
        ):
            generate.generate(csv_path, repo_root=self.root)

    def test_rejects_missing_main_task_for_task_directory(self) -> None:
        directory = self.root / "tasks" / "20260805-no-main"
        directory.mkdir()
        csv_path = self._write_csv(
            [self._row(task="tasks/20260805-no-main")]
        )

        with self.assertRaisesRegex(generate.RoadmapError, "no 000-main"):
            generate.generate(csv_path, repo_root=self.root)

    def test_rejects_path_traversal(self) -> None:
        csv_path = self._write_csv([self._row(task="../outside.md")])

        with self.assertRaisesRegex(generate.RoadmapError, "escapes"):
            generate.generate(csv_path, repo_root=self.root)

    def test_rejects_unexpected_extra_columns(self) -> None:
        csv_path = self._write_csv([self._row()])
        with csv_path.open("a", encoding="utf-8") as handle:
            handle.write("extra,,,,,,,,,,unexpected\n")

        with self.assertRaisesRegex(
            generate.RoadmapError, "unexpected extra columns"
        ):
            generate.generate(csv_path, repo_root=self.root)

    def test_check_rejects_noncanonical_csv_and_stale_markdown(self) -> None:
        csv_path = self._write_csv([self._row(internal_id="MANUAL")])

        with self.assertRaisesRegex(generate.RoadmapError, "normalization"):
            generate.generate(csv_path, repo_root=self.root, check=True)

        output = generate.generate(csv_path, repo_root=self.root)
        generate.generate(csv_path, repo_root=self.root, check=True)
        output.write_text("stale\n", encoding="utf-8")
        with self.assertRaisesRegex(generate.RoadmapError, "stale"):
            generate.generate(csv_path, repo_root=self.root, check=True)


if __name__ == "__main__":
    unittest.main()