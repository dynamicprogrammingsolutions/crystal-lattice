from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = ROOT / "application" / "python" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import smoke_runtime_archive as runtime_smoke  # type: ignore[import-not-found]  # noqa: E402


def test_otool_library_reference_parser_preserves_spaces_in_path() -> None:
    assert (
        runtime_smoke.parse_otool_library_reference(
            "\t/private/tmp/runtime extraction/module.abi3.so "
            "(compatibility version 0.0.0, current version 0.0.0)"
        )
        == "/private/tmp/runtime extraction/module.abi3.so"
    )


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
    assert (
        runtime_smoke.is_unsafe_macos_library_reference(
            "/usr/local/opt/openssl@3/lib/libssl.3.dylib"
        )
        is True
    )


def test_macos_native_validation_checks_extension_modules(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package_dir = tmp_path / "package"
    python = package_dir / "python" / "bin" / "python"
    extension = (
        package_dir
        / "python"
        / "lib"
        / "python3.11"
        / "site-packages"
        / "cryptography"
        / "_rust.abi3.so"
    )
    python.parent.mkdir(parents=True)
    extension.parent.mkdir(parents=True)
    python.write_bytes(b"python")
    extension.write_bytes(b"extension")

    def fake_otool(command: list[str], **_kwargs: object) -> str:
        if Path(command[-1]) == extension:
            return (
                f"{extension}:\n"
                f"\t{extension} "
                "(compatibility version 0.0.0, current version 0.0.0)\n"
                "\t/usr/local/opt/openssl@3/lib/libssl.3.dylib "
                "(compatibility version 3.0.0, current version 3.0.0)\n"
            )
        return (
            f"{python}:\n"
            "\t/usr/lib/libSystem.B.dylib "
            "(compatibility version 1.0.0, current version 1.0.0)\n"
        )

    monkeypatch.setattr(runtime_smoke.subprocess, "check_output", fake_otool)

    with pytest.raises(
        RuntimeError,
        match=r"cryptography/_rust\.abi3\.so -> /usr/local/opt/openssl@3",
    ):
        runtime_smoke.validate_portable_python_links(
            package_dir,
            {"platform": "darwin"},
        )


def test_macos_native_validation_allows_absolute_self_install_id(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package_dir = tmp_path / "package"
    python = package_dir / "python" / "bin" / "python"
    extension = package_dir / "python" / "lib" / "module.abi3.so"
    python.parent.mkdir(parents=True)
    extension.parent.mkdir(parents=True)
    python.write_bytes(b"python")
    extension.write_bytes(b"extension")

    def fake_otool(command: list[str], **_kwargs: object) -> str:
        binary = Path(command[-1])
        return (
            f"{binary}:\n"
            f"\t/private/build/root with spaces/{binary.name} "
            "(compatibility version 0.0.0, current version 0.0.0)\n"
            "\t/usr/lib/libSystem.B.dylib "
            "(compatibility version 1.0.0, current version 1.0.0)\n"
        )

    monkeypatch.setattr(runtime_smoke.subprocess, "check_output", fake_otool)

    runtime_smoke.validate_portable_python_links(
        package_dir,
        {"platform": "darwin"},
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
