from __future__ import annotations

import importlib.util
from pathlib import Path
import plistlib
import subprocess


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "prepare_ios_python_runtime.py"
)
SPEC = importlib.util.spec_from_file_location("prepare_ios_python_runtime", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
prepare_ios_python_runtime = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prepare_ios_python_runtime)


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