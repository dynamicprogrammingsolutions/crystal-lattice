from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MAIN_TASKS = (
    "tasks/20260804-open-source-public-release/000-main.md",
    "tasks/20260728-package-local-documentation-standard/000-main.md",
    "tasks/20260617-cli-download-domain-release-automation/000-main.md",
    "tasks/20260628-cli-simplification-and-bridge-ux/000-main.md",
    "tasks/20260614-ios-testflight-github-fastlane/000-main.md",
)


class RoadmapDocumentationTests(unittest.TestCase):
    def test_main_tasks_gate_and_route_roadmap_updates(self) -> None:
        for relative_path in MAIN_TASKS:
            with self.subTest(task=relative_path):
                text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
                compact = " ".join(text.split())
                checklist = (
                    text.find("## Requirements checklist")
                    if "## Requirements checklist" in text
                    else text.find("## Task checklist")
                )
                section = text.find("## Roadmap status updates")

                self.assertGreaterEqual(checklist, 0)
                self.assertGreater(section, checklist)
                self.assertIn(
                    "[Open Source and iOS Release]"
                    "(../../roadmaps/open-source-and-ios-release.md)",
                    text,
                )
                self.assertIn(
                    "[Updating a roadmap through CSV]"
                    "(../../roadmaps/docs/updating-roadmaps.md)",
                    text,
                )
                self.assertIn(
                    "Do not read the linked roadmap or instructions",
                    compact,
                )
                self.assertIn(
                    "only when the user explicitly requests",
                    compact,
                )
                self.assertIn(
                    "synchronizing the configured Google Sheet",
                    compact,
                )

    def test_update_guide_requires_configured_sheet_synchronization(
        self,
    ) -> None:
        update_guide = (
            REPO_ROOT / "roadmaps/docs/updating-roadmaps.md"
        ).read_text(encoding="utf-8")
        sync_guide = (
            REPO_ROOT / "roadmaps/docs/synchronizing-google-sheets.md"
        ).read_text(encoding="utf-8")
        compact_update = " ".join(update_guide.split())
        compact_sync = " ".join(sync_guide.split())

        self.assertIn(
            "A direct request such as “update the task status",
            compact_update,
        )
        self.assertIn(
            "is incomplete until the Google Sheet has been synchronized",
            compact_update,
        )
        self.assertIn("npm run roadmap:update", update_guide)
        self.assertIn("unrelated remote edits", update_guide)
        self.assertIn(
            "is that explicit approval",
            compact_sync,
        )
        self.assertIn(
            "must perform and verify the sheet synchronization",
            compact_sync,
        )


if __name__ == "__main__":
    unittest.main()