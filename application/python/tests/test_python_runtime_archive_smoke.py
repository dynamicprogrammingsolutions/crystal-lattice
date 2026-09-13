from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = ROOT / "application" / "python" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import smoke_runtime_archive as runtime_smoke  # type: ignore[import-not-found]  # noqa: E402


def test_macos_library_reference_classifier_allows_relative_and_system_paths() -> None:
    assert (
        runtime_smoke.is_unsafe_macos_library_reference(
            "@executable_path/../lib/libpython3.11.dylib"
        )
        is False
    )
    assert (
        runtime_smoke.is_unsafe_macos_library_reference(
            "/System/Library/Frameworks/CoreFoundation.framework/Versions/A/CoreFoundation"
        )
        is False
    )
    assert (
        runtime_smoke.is_unsafe_macos_library_reference("/usr/lib/libSystem.B.dylib")
        is False
    )


def test_macos_library_reference_classifier_rejects_host_paths() -> None:
    assert (
        runtime_smoke.is_unsafe_macos_library_reference(
            "/Library/Frameworks/Python.framework/Versions/3.11/Python"
        )
        is True
    )
    assert (
        runtime_smoke.is_unsafe_macos_library_reference(
            "/Users/runner/hostedtoolcache/Python/3.11.13/arm64/Python"
        )
        is True
    )
    assert (
        runtime_smoke.is_unsafe_macos_library_reference(
            "/opt/homebrew/opt/gettext/lib/libintl.8.dylib"
        )
        is True
    )
