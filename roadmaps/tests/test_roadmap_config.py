from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import roadmap_config  # noqa: E402


class RoadmapConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.credential = self.root / "service-account.json"
        self.credential.write_text("{}", encoding="utf-8")
        self.env_file = self.root / ".env"
        self.env_file.write_text(
            "\n".join(
                (
                    f"GOOGLE_APPLICATION_CREDENTIALS={self.credential}",
                    "ROADMAP_SHEET_ID=sheet-from-dotenv",
                    "ROADMAP_PRODUCT_SHEET_ID=product-sheet-from-dotenv",
                    "",
                )
            ),
            encoding="utf-8",
        )

    def _write_registry(self) -> Path:
        path = self.root / "config.json"
        path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "env_file": ".env",
                    "repository_root": ".",
                    "task_directory_entry": "main.md",
                    "google_sheets": {
                        "credentials_file": (
                            "${env:GOOGLE_APPLICATION_CREDENTIALS}"
                        ),
                        "timeout_seconds": 45,
                    },
                    "roadmaps": {
                        "release": {
                            "csv": "release.csv",
                            "spreadsheet_id": (
                                "${env:ROADMAP_SHEET_ID}"
                            ),
                            "spreadsheet_title": "Roadmap",
                            "sheet": "Sheet1",
                        },
                        "product": {
                            "csv": "product.csv",
                            "spreadsheet_id": (
                                "${env:ROADMAP_PRODUCT_SHEET_ID}"
                            ),
                            "spreadsheet_title": "Product roadmap",
                            "sheet": "Product",
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        return path

    def test_named_target_and_sheets_settings_resolve_from_dotenv(self) -> None:
        registry = roadmap_config.load_registry(self._write_registry())

        target = roadmap_config.resolve_target("release", registry)

        self.assertEqual(target.csv_path, (self.root / "release.csv").resolve())
        self.assertEqual(target.spreadsheet_id, "sheet-from-dotenv")
        self.assertEqual(target.repository_root, self.root.resolve())
        self.assertEqual(target.task_directory_entry, "main.md")
        self.assertEqual(
            registry.google_sheets.credentials_file,
            self.credential.resolve(),
        )
        self.assertEqual(registry.google_sheets.timeout_seconds, 45)
        self.assertEqual(
            roadmap_config.resolve_target("product", registry).spreadsheet_id,
            "product-sheet-from-dotenv",
        )

    def test_exported_environment_overrides_dotenv(self) -> None:
        with patch.dict(
            os.environ,
            {"ROADMAP_SHEET_ID": "sheet-from-process"},
            clear=False,
        ):
            registry = roadmap_config.load_registry(self._write_registry())

        self.assertEqual(
            registry.roadmaps["release"].spreadsheet_id,
            "sheet-from-process",
        )

    def test_missing_dotenv_is_rejected(self) -> None:
        config = self._write_registry()
        self.env_file.unlink()

        with self.assertRaisesRegex(
            roadmap_config.RoadmapConfigError,
            "roadmap environment file is missing",
        ):
            roadmap_config.load_registry(config)

    def test_missing_required_environment_value_is_rejected(self) -> None:
        self.env_file.write_text(
            f"GOOGLE_APPLICATION_CREDENTIALS={self.credential}\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            roadmap_config.RoadmapConfigError, "ROADMAP_SHEET_ID"
        ):
            roadmap_config.load_registry(self._write_registry())

    def test_missing_credential_file_is_rejected_without_exposing_path(
        self,
    ) -> None:
        self.env_file.write_text(
            "\n".join(
                (
                    "GOOGLE_APPLICATION_CREDENTIALS=/private/missing.json",
                    "ROADMAP_SHEET_ID=sheet",
                )
            ),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            roadmap_config.RoadmapConfigError,
            "^configured Google application credentials file is missing$",
        ):
            roadmap_config.load_registry(self._write_registry())

    def test_invalid_timeout_is_rejected(self) -> None:
        config = self._write_registry()
        data = json.loads(config.read_text(encoding="utf-8"))
        data["google_sheets"]["timeout_seconds"] = 0
        config.write_text(json.dumps(data), encoding="utf-8")

        with self.assertRaisesRegex(
            roadmap_config.RoadmapConfigError, "positive integer"
        ):
            roadmap_config.load_registry(config)

    def test_generator_runs_from_an_unrelated_working_directory(self) -> None:
        project = self.root / "project"
        task_dir = project / "work" / "20260101-example"
        task_dir.mkdir(parents=True)
        (task_dir / "010-step.md").write_text("# Step\n", encoding="utf-8")
        settings = self.root / "settings"
        settings.mkdir()
        csv_path = settings / "sample.csv"
        csv_path.write_text(
            "\n".join(
                (
                    "task,external_id,internal_id,owner,priority,status,"
                    "declared_dependencies,inferred_dependencies",
                    "work/20260101-example/010-step.md,,,Team,"
                    "must have,pending,,",
                    "",
                )
            ),
            encoding="utf-8",
        )
        env_path = settings / ".env"
        env_path.write_text(
            "\n".join(
                (
                    f"GOOGLE_APPLICATION_CREDENTIALS={self.credential}",
                    "SAMPLE_SHEET_ID=unused",
                    "",
                )
            ),
            encoding="utf-8",
        )
        config_path = settings / "config.json"
        config_path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "env_file": ".env",
                    "repository_root": "../project",
                    "google_sheets": {
                        "credentials_file": (
                            "${env:GOOGLE_APPLICATION_CREDENTIALS}"
                        )
                    },
                    "roadmaps": {
                        "sample": {
                            "csv": "sample.csv",
                            "spreadsheet_id": "${env:SAMPLE_SHEET_ID}",
                            "spreadsheet_title": "Sample",
                            "sheet": "Tasks",
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        elsewhere = self.root / "elsewhere"
        elsewhere.mkdir()
        script = Path(__file__).resolve().parents[1] / "generate.py"

        completed = subprocess.run(
            [
                sys.executable,
                str(script),
                "--config",
                str(config_path),
                "sample",
            ],
            cwd=elsewhere,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(csv_path.with_suffix(".md").is_file())
        self.assertIn("0101-E-010", csv_path.read_text(encoding="utf-8"))

    def test_direct_csv_generation_does_not_require_sheet_config(self) -> None:
        project = self.root / "standalone-project"
        task_dir = project / "work" / "20260103-direct"
        task_dir.mkdir(parents=True)
        (task_dir / "010-step.md").write_text("# Step\n", encoding="utf-8")
        csv_path = project / "sample.csv"
        csv_path.write_text(
            "\n".join(
                (
                    "task,external_id,internal_id,owner,priority,status,"
                    "declared_dependencies,inferred_dependencies",
                    "work/20260103-direct/010-step.md,,,Team,"
                    "must have,pending,,",
                    "",
                )
            ),
            encoding="utf-8",
        )
        elsewhere = self.root / "direct-cwd"
        elsewhere.mkdir()
        script = Path(__file__).resolve().parents[1] / "generate.py"
        environment = dict(os.environ)
        environment["ROADMAP_REPOSITORY_ROOT"] = str(project)
        environment["ROADMAP_CONFIG"] = str(self.root / "missing.json")

        completed = subprocess.run(
            [sys.executable, str(script), str(csv_path)],
            cwd=elsewhere,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("0103-D-010", csv_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()