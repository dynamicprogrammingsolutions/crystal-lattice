#!/usr/bin/env python3
"""Check the exact files handed from a notarized build to a draft release."""

import argparse
import hashlib
import json
import re
from pathlib import Path


def validate(directory: Path, source_commit: str, version: str) -> tuple[str, str]:
    metadata = json.loads((directory / "release-metadata.json").read_text())
    notarization = json.loads((directory / "notarization.json").read_text())
    dmg_name = f"Crystal-Lattice-Desktop-v{version}-universal.dmg"
    checksum_name = f"{dmg_name}.sha256"
    expected = {dmg_name, checksum_name, "release-metadata.json", "notarization.json"}
    actual = {path.name for path in directory.iterdir()}
    if actual != expected or any(not (directory / name).is_file() for name in expected):
        raise ValueError(f"Expected exactly {sorted(expected)}, found {sorted(actual)}")

    if metadata.get("product") != "Crystal Lattice Desktop":
        raise ValueError("Unexpected product")
    if metadata.get("bundle_id") != "com.dynamicprogrammingsolutions.crystallatticecontrol.macos":
        raise ValueError("Unexpected bundle ID")
    if metadata.get("marketing_version") != version:
        raise ValueError("Unexpected marketing version")
    if not isinstance(metadata.get("build_number"), int) or metadata["build_number"] < 1:
        raise ValueError("Build number must be a positive integer")
    if metadata.get("source_commit") != source_commit:
        raise ValueError("Candidate was built from a different source commit")
    if metadata.get("source_tree_clean") is not True:
        raise ValueError("Candidate was not built from a clean source tree")
    if metadata.get("architectures") != ["arm64", "x86_64"]:
        raise ValueError("Candidate is not the expected universal build")
    if metadata.get("minimum_macos") != "14.0" or metadata.get("dmg") != dmg_name:
        raise ValueError("Unexpected release contract")
    if metadata.get("notarization_status") != "Accepted":
        raise ValueError("Candidate is not marked as accepted by notarization")
    if notarization.get("status") != "Accepted" or not isinstance(notarization.get("id"), str):
        raise ValueError("Notarization result is missing or not accepted")
    if metadata.get("notarization_id") != notarization["id"]:
        raise ValueError("Notarization ID differs from release metadata")

    with (directory / dmg_name).open("rb") as dmg_file:
        digest = hashlib.file_digest(dmg_file, "sha256").hexdigest()
    if metadata.get("sha256") != digest:
        raise ValueError("DMG digest differs from release metadata")
    checksum = (directory / checksum_name).read_text()
    if checksum != f"{digest}  {dmg_name}\n" or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError("Checksum manifest does not match the DMG")

    return dmg_name, digest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--version", default="0.9.0")
    args = parser.parse_args()
    name, checksum = validate(args.directory, args.commit, args.version)
    print(f"Verified {name} from {args.commit}: SHA-256 {checksum}")


if __name__ == "__main__":
    main()