from __future__ import annotations

import sys
from pathlib import Path

import pytest

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


def test_native_python_identity_accepts_matching_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        runtime_smoke.subprocess,
        "check_output",
        lambda *args, **kwargs: '{"platform": "linux", "machine": "aarch64"}\n',
    )
    monkeypatch.setattr(
        runtime_smoke,
        "python_path",
        lambda _package_dir: tmp_path / "python",
    )

    runtime_smoke.validate_native_python_identity(
        tmp_path,
        {"platform": "linux", "arch": "arm64"},
    )


def test_native_python_identity_rejects_mislabeled_archive(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        runtime_smoke.subprocess,
        "check_output",
        lambda *args, **kwargs: '{"platform": "win32", "machine": "AMD64"}\n',
    )
    monkeypatch.setattr(
        runtime_smoke,
        "python_path",
        lambda _package_dir: tmp_path / "python.exe",
    )

    with pytest.raises(
        RuntimeError,
        match="expected windows-arm64, got windows-amd64",
    ):
        runtime_smoke.validate_native_python_identity(
            tmp_path,
            {"platform": "windows", "arch": "arm64"},
        )
