#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request
import zipfile


PYTHON_SUPPORT_TAG = "3.12-b10"
PYTHON_VERSION = "3.12"
RUNTIME_LAYOUT_VERSION = "2"
ARCHIVE_NAME = "Python-3.12-iOS-support.b10.tar.gz"
ARCHIVE_URL = (
    "https://github.com/beeware/Python-Apple-support/releases/download/"
    f"{PYTHON_SUPPORT_TAG}/{ARCHIVE_NAME}"
)
ARCHIVE_SHA256 = "18fb042d47b7ec441282eb96da0193e3093de7f02add35f5745d73491c6c0843"

APP_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = APP_ROOT / "ios" / "CrystalLatticePythonRuntime"
VENDOR_DIR = RUNTIME_ROOT / "Vendor"
RESOURCES_DIR = RUNTIME_ROOT / "Resources"
MARKER_PATH = RUNTIME_ROOT / ".prepared-python-runtime"
CACHE_DIR = Path.home() / "Library" / "Caches" / "CrystalLattice" / "python-apple-support"
CACHE_ARCHIVE = CACHE_DIR / ARCHIVE_NAME

STDLIB_EXCLUDES = {
    "__pycache__",
    "ensurepip",
    "idlelib",
    "lib2to3",
    "test",
    "tkinter",
    "turtledemo",
    "venv",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_archive() -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if CACHE_ARCHIVE.is_file() and sha256(CACHE_ARCHIVE) == ARCHIVE_SHA256:
        return CACHE_ARCHIVE

    CACHE_ARCHIVE.unlink(missing_ok=True)
    temporary = CACHE_ARCHIVE.with_suffix(CACHE_ARCHIVE.suffix + ".download")
    temporary.unlink(missing_ok=True)
    print(f"Downloading {ARCHIVE_URL}")
    try:
        urllib.request.urlretrieve(ARCHIVE_URL, temporary)
    except Exception as urllib_error:
        curl = shutil.which("curl")
        if curl is None:
            raise RuntimeError(
                f"Could not download Python support with urllib: {urllib_error}"
            ) from urllib_error
        subprocess.run(
            [curl, "--fail", "--location", "--output", str(temporary), ARCHIVE_URL],
            check=True,
        )
    actual = sha256(temporary)
    if actual != ARCHIVE_SHA256:
        temporary.unlink(missing_ok=True)
        raise RuntimeError(
            f"Python support archive checksum mismatch: expected {ARCHIVE_SHA256}, got {actual}"
        )
    temporary.replace(CACHE_ARCHIVE)
    return CACHE_ARCHIVE


def include_stdlib_path(path: Path, source: Path) -> bool:
    relative = path.relative_to(source)
    if any(part in STDLIB_EXCLUDES for part in relative.parts):
        return False
    return path.suffix not in {".pyc", ".pyo"}


def create_stdlib_archive(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_STORED) as archive:
        for path in sorted(source.rglob("*")):
            if path.is_file() and include_stdlib_path(path, source):
                archive.write(path, path.relative_to(source))


def prepare_runtime(archive: Path) -> None:
    expected_marker = (
        f"{PYTHON_SUPPORT_TAG}:{ARCHIVE_SHA256}:{RUNTIME_LAYOUT_VERSION}\n"
    )
    if (
        MARKER_PATH.is_file()
        and MARKER_PATH.read_text(encoding="utf-8") == expected_marker
        and (VENDOR_DIR / "Python.xcframework").is_dir()
        and (RESOURCES_DIR / "python312.zip").is_file()
    ):
        print(f"iOS Python runtime already prepared at {RUNTIME_ROOT}")
        return

    with tempfile.TemporaryDirectory(prefix="crystal-ios-python-") as temporary:
        extracted = Path(temporary)
        with tarfile.open(archive, "r:gz") as support_archive:
            support_archive.extractall(extracted, filter="data")

        source_framework = extracted / "Python.xcframework"
        source_stdlib = source_framework / "lib" / f"python{PYTHON_VERSION}"
        if not source_framework.is_dir() or not source_stdlib.is_dir():
            raise RuntimeError("Python support archive has an unexpected layout")

        staged_vendor = extracted / "staged-vendor"
        staged_resources = extracted / "staged-resources"
        shutil.copytree(source_framework, staged_vendor / "Python.xcframework")
        create_stdlib_archive(source_stdlib, staged_resources / "python312.zip")

        shutil.rmtree(VENDOR_DIR, ignore_errors=True)
        shutil.rmtree(RESOURCES_DIR, ignore_errors=True)
        VENDOR_DIR.parent.mkdir(parents=True, exist_ok=True)
        RESOURCES_DIR.mkdir(parents=True, exist_ok=True)
        shutil.move(staged_vendor, VENDOR_DIR)
        shutil.move(staged_resources / "python312.zip", RESOURCES_DIR / "python312.zip")

    MARKER_PATH.write_text(expected_marker, encoding="utf-8")
    print(f"Prepared iOS Python runtime at {RUNTIME_ROOT}")


def main() -> None:
    prepare_runtime(ensure_archive())


if __name__ == "__main__":
    main()