"""Publication boundary checks for a downloaded desktop release candidate."""

import importlib.util
import json
import tempfile
import unittest
from hashlib import sha256
from pathlib import Path


script_path = Path(__file__).resolve().parents[1] / "verify_desktop_release_candidate.py"
spec = importlib.util.spec_from_file_location("desktop_candidate_verifier", script_path)
assert spec is not None and spec.loader is not None
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)

SOURCE_COMMIT = "a" * 40
DMG_NAME = "Crystal-Lattice-Desktop-v0.9.0-universal.dmg"


class DesktopCandidateVerifierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.dmg = self.directory / DMG_NAME
        self.dmg.write_bytes(b"isolated release-candidate fixture")
        digest = sha256(self.dmg.read_bytes()).hexdigest()
        (self.directory / f"{DMG_NAME}.sha256").write_text(
            f"{digest}  {DMG_NAME}\n"
        )
        self.metadata = {
            "product": "Crystal Lattice Desktop",
            "bundle_id": "com.dynamicprogrammingsolutions.crystallatticecontrol.macos",
            "marketing_version": "0.9.0",
            "build_number": 7,
            "source_commit": SOURCE_COMMIT,
            "source_tree_clean": True,
            "architectures": ["arm64", "x86_64"],
            "minimum_macos": "14.0",
            "dmg": DMG_NAME,
            "notarization_status": "Accepted",
            "notarization_id": "example-submission-id",
            "sha256": digest,
        }
        self.save_metadata()
        (self.directory / "notarization.json").write_text(
            json.dumps({"status": "Accepted", "id": "example-submission-id"})
        )

    def save_metadata(self) -> None:
        (self.directory / "release-metadata.json").write_text(
            json.dumps(self.metadata)
        )

    def check(self) -> tuple[str, str]:
        return verifier.validate(self.directory, SOURCE_COMMIT, "0.9.0")

    def test_accepts_exact_verified_files(self) -> None:
        self.assertEqual(self.check(), (DMG_NAME, self.metadata["sha256"]))

    def test_rejects_changed_dmg(self) -> None:
        self.dmg.write_bytes(b"changed after notarization")
        with self.assertRaisesRegex(ValueError, "digest"):
            self.check()

    def test_rejects_different_source_commit(self) -> None:
        self.metadata["source_commit"] = "b" * 40
        self.save_metadata()
        with self.assertRaisesRegex(ValueError, "source commit"):
            self.check()

    def test_rejects_dirty_source_tree(self) -> None:
        self.metadata["source_tree_clean"] = False
        self.save_metadata()
        with self.assertRaisesRegex(ValueError, "clean source tree"):
            self.check()

    def test_rejects_failed_notarization(self) -> None:
        (self.directory / "notarization.json").write_text(
            json.dumps({"status": "Invalid", "id": "example-submission-id"})
        )
        with self.assertRaisesRegex(ValueError, "Notarization"):
            self.check()

    def test_rejects_extra_asset(self) -> None:
        (self.directory / "unexpected-file.txt").write_text("surprise")
        with self.assertRaisesRegex(ValueError, "exactly"):
            self.check()


if __name__ == "__main__":
    unittest.main()