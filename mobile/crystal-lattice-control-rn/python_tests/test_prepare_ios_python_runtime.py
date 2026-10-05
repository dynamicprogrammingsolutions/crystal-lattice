from __future__ import annotations

import importlib.util
from pathlib import Path
import plistlib
import subprocess
import zipfile

import pytest


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "prepare_ios_python_runtime.py"
)
SPEC = importlib.util.spec_from_file_location("prepare_ios_python_runtime", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
prepare_ios_python_runtime = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prepare_ios_python_runtime)


def write_pure_wheel_metadata(
    root: Path,
    *,
    distribution: str,
    version: str,
) -> None:
    metadata_root = root / f"{distribution.replace('-', '_')}-{version}.dist-info"
    metadata_root.mkdir(parents=True)
    (metadata_root / "METADATA").write_text(
        f"Name: {distribution}\nVersion: {version}\n",
        encoding="utf-8",
    )
    (metadata_root / "WHEEL").write_text(
        "Wheel-Version: 1.0\n"
        "Root-Is-Purelib: true\n"
        "Tag: py3-none-any\n",
        encoding="utf-8",
    )


def test_embedded_requirements_are_exact_and_include_both_jsonpath_packages() -> None:
    requirements = prepare_ios_python_runtime.embedded_requirements()

    assert "jsonpath-ng==1.7.0" in requirements
    assert "python-jsonpath==2.2.1" in requirements
    assert all(requirement.count("==") == 1 for requirement in requirements)


def test_dependency_tree_is_archived_without_import_name_mapping(
    tmp_path: Path,
) -> None:
    staging = tmp_path / "site-packages"
    package = staging / "jsonpath"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("VALUE = 1\n", encoding="utf-8")
    (package / "py.typed").write_text("", encoding="utf-8")
    (package / "data.txt").write_text("runtime data\n", encoding="utf-8")
    (package / "__pycache__").mkdir()
    (package / "__pycache__" / "ignored.pyc").write_bytes(b"cache")
    (staging / "bin").mkdir()
    (staging / "bin" / "jsonpath").write_text("#!/bin/sh\n", encoding="utf-8")
    write_pure_wheel_metadata(
        staging,
        distribution="python-jsonpath",
        version="2.2.1",
    )

    archive_path = tmp_path / "runtime.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        prepare_ios_python_runtime.add_pure_dependency_tree(archive, staging)

    with zipfile.ZipFile(archive_path) as archive:
        names = set(archive.namelist())
    assert "jsonpath/__init__.py" in names
    assert "jsonpath/py.typed" in names
    assert "jsonpath/data.txt" in names
    assert "python_jsonpath-2.2.1.dist-info/METADATA" in names
    assert "bin/jsonpath" not in names
    assert not any("__pycache__" in name or name.endswith(".pyc") for name in names)


def test_dependency_tree_rejects_native_extensions(tmp_path: Path) -> None:
    staging = tmp_path / "site-packages"
    package = staging / "example"
    package.mkdir(parents=True)
    (package / "native.cpython-312-darwin.so").write_bytes(b"not-ios")
    write_pure_wheel_metadata(
        staging,
        distribution="example",
        version="1.0.0",
    )

    with pytest.raises(RuntimeError, match="platform-neutral pure Python"):
        prepare_ios_python_runtime.validate_pure_dependency_tree(staging)


def test_dependency_tree_rejects_development_distributions(tmp_path: Path) -> None:
    staging = tmp_path / "site-packages"
    write_pure_wheel_metadata(
        staging,
        distribution="pytest",
        version="9.0.0",
    )

    with pytest.raises(RuntimeError, match="development distributions"):
        prepare_ios_python_runtime.validate_pure_dependency_tree(staging)


def test_patch_python_build_utils_emits_valid_framework_bundle_ids(
    tmp_path: Path,
) -> None:
    framework_root = tmp_path / "Python.xcframework"
    utils_path = framework_root / "build" / "utils.sh"
    utils_path.parent.mkdir(parents=True)
    utils_path.write_text(
        "\n".join(
            [
                "framework_bundle_id() {",
                "    PRODUCT_BUNDLE_IDENTIFIER=$1",
                "    FULL_MODULE_NAME=$2",
                prepare_ios_python_runtime.UPSTREAM_FRAMEWORK_BUNDLE_ID_LINE.rstrip(
                    "\n"
                ),
                '    printf "%s\\n" "$FRAMEWORK_BUNDLE_ID"',
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    prepare_ios_python_runtime.patch_python_build_utils(framework_root)

    patched = utils_path.read_text(encoding="utf-8")
    assert prepare_ios_python_runtime.UPSTREAM_FRAMEWORK_BUNDLE_ID_LINE not in patched
    assert prepare_ios_python_runtime.PATCHED_FRAMEWORK_BUNDLE_ID_LINES in patched

    for module_name, expected in (
        ("_socket", "com.example.app.python-socket\n"),
        ("pkg._native", "com.example.app.python-pkg-native\n"),
        ("math", "com.example.app.python-math\n"),
    ):
        result = subprocess.run(
            [
                "sh",
                "-c",
                f'. "{utils_path}"; '
                f"framework_bundle_id com.example.app {module_name}",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        assert result.stdout == expected


def test_patch_python_dylib_info_templates_marks_frameworks_as_frameworks(
    tmp_path: Path,
) -> None:
    framework_root = tmp_path / "Python.xcframework"
    template_path = framework_root / "build" / "iOS-dylib-Info-template.plist"
    template_path.parent.mkdir(parents=True)
    with template_path.open("wb") as handle:
        plistlib.dump(
            {
                "CFBundleExecutable": "",
                "CFBundleIdentifier": "",
                "CFBundlePackageType": "APPL",
            },
            handle,
        )

    prepare_ios_python_runtime.patch_python_dylib_info_templates(framework_root)

    with template_path.open("rb") as handle:
        patched = plistlib.load(handle)
    assert patched["CFBundlePackageType"] == "FMWK"