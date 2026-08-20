from __future__ import annotations

import json
import os
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
        self.assertEqual(
            registry.google_sheets.credentials_file,
            self.credential.resolve(),
        )
        self.assertEqual(registry.google_sheets.timeout_seconds, 45)

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

    def test_missing_dotenv_is_rejected_with_setup_instruction(self) -> None:
        config = self._write_registry()
        self.env_file.unlink()

        with self.assertRaisesRegex(
            roadmap_config.RoadmapConfigError, "copy roadmaps/.env.example"
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


if __name__ == "__main__":
    unittest.main()