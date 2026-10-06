#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from pathlib import Path
import plistlib
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile


PYTHON_SUPPORT_TAG = "3.12-b10"
RUNTIME_LAYOUT_VERSION = "18"
ARCHIVE_NAME = "Python-3.12-iOS-support.b10.tar.gz"
ARCHIVE_URL = (
    "https://github.com/beeware/Python-Apple-support/releases/download/"
    f"{PYTHON_SUPPORT_TAG}/{ARCHIVE_NAME}"
)
ARCHIVE_SHA256 = "18fb042d47b7ec441282eb96da0193e3093de7f02add35f5745d73491c6c0843"

APP_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = APP_ROOT.parents[1]
RUNTIME_ROOT = APP_ROOT / "ios" / "CrystalLatticePythonRuntime"
PYTHON_APP_SOURCE = RUNTIME_ROOT / "Python"
VENDOR_DIR = RUNTIME_ROOT / "Vendor"
RESOURCES_DIR = RUNTIME_ROOT / "Resources"
REVIEWER_CA_PATH = RESOURCES_DIR / "reviewer-proxy-ca.pem"
MARKER_PATH = RUNTIME_ROOT / ".prepared-python-runtime"
CACHE_DIR = (
    Path.home() / "Library" / "Caches" / "CrystalLattice" / "python-apple-support"
)
CACHE_ARCHIVE = CACHE_DIR / ARCHIVE_NAME
PURE_DEPENDENCY_CACHE = CACHE_DIR / "pure-dependencies-v2"
PURE_DEPENDENCY_SITE_PACKAGES = PURE_DEPENDENCY_CACHE / "site-packages"
NATIVE_DEPENDENCY_SUFFIXES = frozenset(
    {".a", ".dll", ".dylib", ".framework", ".pyd", ".so", ".xcframework"}
)
FORBIDDEN_RUNTIME_DISTRIBUTIONS = frozenset(
    {
        "black",
        "coverage",
        "mypy",
        "pyright",
        "pytest",
        "pytest-asyncio",
        "pytest-cov",
        "python-dotenv",
        "ruff",
    }
)
APP_PLUGIN_PACKAGES = (
    ("chatgpt-auth-app", "chatgpt_auth_app"),
    ("generate-title-app", "generate_title_app"),
    ("session-actions-app", "session_actions_app"),
    ("session-archive-app", "session_archive_app"),
    ("session-main-search-app", "session_main_search_app"),
    ("session-message-count-meta-app", "session_message_count_meta_app"),
    ("session-ordering-buckets-app", "session_ordering_buckets_app"),
    ("session-pinned-app", "session_pinned_app"),
    ("session-status-app", "session_status_app"),
    ("session-timestamp-meta-app", "session_timestamp_meta_app"),
    ("session-title-app", "session_title_app"),
    ("session-asset-attachments", "session_asset_attachments"),
    ("feature-system-message", "feature_system_message"),
    ("feature-request-options", "feature_request_options"),
    ("timestamp-extension", "timestamp_extension"),
    ("summarize-range-app", "summarize_range_app"),
    ("rebuild-native-app", "rebuild_native_app"),
    ("cost-tracking", "cost_tracking_plugins"),
    ("embedded-workspace-settings", "embedded_workspace_settings"),
)
EMBEDDED_CONFIG_ROOT = (
    REPO_ROOT
    / "application"
    / "python"
    / "agent_terminal_app"
    / "default_config"
    / "embedded-ios"
)
EMBEDDED_CONFIG_PATH = EMBEDDED_CONFIG_ROOT / "config.json"
EMBEDDED_REQUIREMENTS_PATH = EMBEDDED_CONFIG_ROOT / "requirements.txt"
APPLICATION_PACKAGE_INIT = (
    REPO_ROOT / "application" / "python" / "agent_terminal_app" / "__init__.py"
)
UPSTREAM_FRAMEWORK_BUNDLE_ID_LINE = (
    "    FRAMEWORK_BUNDLE_ID=$(echo "
    '$PRODUCT_BUNDLE_IDENTIFIER.$FULL_MODULE_NAME | tr "_" "-")\n'
)
PATCHED_FRAMEWORK_BUNDLE_ID_LINES = (
    '    FRAMEWORK_BUNDLE_COMPONENT=$(echo "$FULL_MODULE_NAME" '
    '| tr "._" "--" | tr -s "-" | sed "s/^-//; s/-$//")\n'
    '    FRAMEWORK_BUNDLE_ID="$PRODUCT_BUNDLE_IDENTIFIER.'
    'python-$FRAMEWORK_BUNDLE_COMPONENT"\n'
)


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


def source_digest() -> str:
    digest = hashlib.sha256()
    source_roots = (
        REPO_ROOT / "core" / "python" / "agent_core",
        REPO_ROOT / "core" / "python" / "agent_app",
        (
            REPO_ROOT
            / "plugins"
            / "reference-openai-compatible-provider"
            / "src"
            / "reference_openai_compatible_provider"
        ),
        (
            REPO_ROOT
            / "plugins"
            / "embedded-tools-shared"
            / "src"
            / "embedded_tools_shared"
        ),
        (
            REPO_ROOT
            / "plugins"
            / "embedded-claude-tools"
            / "src"
            / "embedded_claude_tools"
        ),
        (
            REPO_ROOT
            / "plugins"
            / "embedded-codex-tools"
            / "src"
            / "embedded_codex_tools"
        ),
        (
            REPO_ROOT
            / "plugins"
            / "openai_responses"
            / "src"
            / "openai_responses_plugins"
        ),
        (
            REPO_ROOT
            / "plugins"
            / "anthropic-compatible"
            / "src"
            / "anthropic_plugins"
        ),
        REPO_ROOT / "plugins" / "openrouter" / "src" / "openrouter_plugins",
        *(
            REPO_ROOT / "plugins" / project / "src" / package
            for project, package in APP_PLUGIN_PACKAGES
        ),
        PYTHON_APP_SOURCE,
    )
    for source_root in source_roots:
        for path in sorted(source_root.rglob("*.py")):
            digest.update(str(path.relative_to(REPO_ROOT)).encode("utf-8"))
            digest.update(path.read_bytes())
    for path in (
        APPLICATION_PACKAGE_INIT,
        EMBEDDED_CONFIG_PATH,
        EMBEDDED_REQUIREMENTS_PATH,
    ):
        digest.update(path.relative_to(REPO_ROOT).as_posix().encode("utf-8"))
        digest.update(path.read_bytes())
    if REVIEWER_CA_PATH.is_file():
        digest.update(REVIEWER_CA_PATH.relative_to(REPO_ROOT).as_posix().encode("utf-8"))
        digest.update(REVIEWER_CA_PATH.read_bytes())
    return digest.hexdigest()


def normalized_distribution_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def embedded_requirements() -> tuple[str, ...]:
    requirements: list[str] = []
    names: set[str] = set()
    for line_number, raw_line in enumerate(
        EMBEDDED_REQUIREMENTS_PATH.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        line = raw_line.partition("#")[0].strip()
        if not line:
            continue
        if line.count("==") != 1:
            raise RuntimeError(
                "Embedded iOS requirements must use exact pins: "
                f"{EMBEDDED_REQUIREMENTS_PATH}:{line_number}: {line!r}"
            )
        name, version = (part.strip() for part in line.split("==", 1))
        if (
            not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name)
            or not version
            or any(character.isspace() for character in version)
        ):
            raise RuntimeError(
                "Invalid embedded iOS requirement: "
                f"{EMBEDDED_REQUIREMENTS_PATH}:{line_number}: {line!r}"
            )
        normalized_name = normalized_distribution_name(name)
        if normalized_name in names:
            raise RuntimeError(
                f"Duplicate embedded iOS requirement for {name!r}"
            )
        if normalized_name in FORBIDDEN_RUNTIME_DISTRIBUTIONS:
            raise RuntimeError(
                f"Development dependency is forbidden in the iOS runtime: {name}"
            )
        names.add(normalized_name)
        requirements.append(f"{name}=={version}")
    if not requirements:
        raise RuntimeError("Embedded iOS requirements must not be empty")
    return tuple(requirements)


def _installed_distribution_names(source: Path) -> set[str]:
    names: set[str] = set()
    for metadata_path in sorted(source.glob("*.dist-info/METADATA")):
        for line in metadata_path.read_text(
            encoding="utf-8",
            errors="replace",
        ).splitlines():
            if line.startswith("Name:"):
                name = line.partition(":")[2].strip()
                if name:
                    names.add(normalized_distribution_name(name))
                break
    return names


def validate_pure_dependency_tree(source: Path) -> None:
    if not source.is_dir():
        raise RuntimeError(f"Embedded dependency staging directory is missing: {source}")

    invalid_files: list[str] = []
    for path in sorted(source.rglob("*")):
        if path.is_symlink():
            invalid_files.append(f"{path.relative_to(source)} (symlink)")
            continue
        if (
            path.is_dir()
            and path.suffix.lower() in NATIVE_DEPENDENCY_SUFFIXES
        ):
            invalid_files.append(str(path.relative_to(source)))
            continue
        if not path.is_file():
            continue
        relative = path.relative_to(source)
        suffixes = {suffix.lower() for suffix in path.suffixes}
        if suffixes & NATIVE_DEPENDENCY_SUFFIXES:
            invalid_files.append(str(relative))
    if invalid_files:
        raise RuntimeError(
            "Embedded iOS dependencies must be platform-neutral pure Python; "
            f"unsupported files: {invalid_files[:10]}"
        )

    wheel_paths = sorted(source.glob("*.dist-info/WHEEL"))
    if not wheel_paths:
        raise RuntimeError("Embedded dependency staging contains no wheel metadata")
    invalid_wheels: list[str] = []
    for wheel_path in wheel_paths:
        text = wheel_path.read_text(encoding="utf-8", errors="replace")
        tags = [
            line.partition(":")[2].strip()
            for line in text.splitlines()
            if line.startswith("Tag:")
        ]
        if (
            "Root-Is-Purelib: true" not in text
            or not tags
            or any(not tag.endswith("-none-any") for tag in tags)
        ):
            invalid_wheels.append(str(wheel_path.relative_to(source)))
    if invalid_wheels:
        raise RuntimeError(
            "Embedded iOS dependencies must come from platform-neutral wheels; "
            f"invalid wheel metadata: {invalid_wheels[:10]}"
        )

    forbidden = sorted(
        _installed_distribution_names(source) & FORBIDDEN_RUNTIME_DISTRIBUTIONS
    )
    if forbidden:
        raise RuntimeError(
            "Embedded iOS dependency staging contains development distributions: "
            f"{forbidden}"
        )


def ensure_pure_dependencies() -> Path:
    embedded_requirements()
    requirements_text = EMBEDDED_REQUIREMENTS_PATH.read_text(encoding="utf-8")
    marker = PURE_DEPENDENCY_CACHE / ".requirements"
    if (
        marker.is_file()
        and marker.read_text(encoding="utf-8") == requirements_text
        and PURE_DEPENDENCY_SITE_PACKAGES.is_dir()
    ):
        validate_pure_dependency_tree(PURE_DEPENDENCY_SITE_PACKAGES)
        return PURE_DEPENDENCY_SITE_PACKAGES

    shutil.rmtree(PURE_DEPENDENCY_CACHE, ignore_errors=True)
    PURE_DEPENDENCY_SITE_PACKAGES.mkdir(parents=True)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--target",
            str(PURE_DEPENDENCY_SITE_PACKAGES),
            "--only-binary=:all:",
            "--platform",
            "any",
            "--implementation",
            "py",
            "--python-version",
            "3.12",
            "--abi",
            "none",
            "--requirement",
            str(EMBEDDED_REQUIREMENTS_PATH),
        ],
        check=True,
    )
    validate_pure_dependency_tree(PURE_DEPENDENCY_SITE_PACKAGES)
    marker.write_text(requirements_text, encoding="utf-8")
    return PURE_DEPENDENCY_SITE_PACKAGES


def add_python_tree(
    archive: zipfile.ZipFile,
    source: Path,
    destination: Path,
) -> None:
    for path in sorted(source.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        archive.write(path, destination / path.relative_to(source))


def add_package_tree(
    archive: zipfile.ZipFile,
    source: Path,
    destination: Path,
) -> None:
    for path in sorted(source.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        if path.suffix not in {".json", ".pem", ".py"}:
            continue
        archive.write(path, destination / path.relative_to(source))


def add_pure_dependency_tree(
    archive: zipfile.ZipFile,
    source: Path,
) -> None:
    validate_pure_dependency_tree(source)
    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(source)
        if relative.parts[0] == "bin" or "__pycache__" in relative.parts:
            continue
        if path.suffix == ".pyc":
            continue
        archive.write(path, relative)


def create_application_archive(destination: Path) -> None:
    dependencies = ensure_pure_dependencies()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_STORED) as archive:
        add_python_tree(
            archive,
            REPO_ROOT / "core" / "python" / "agent_core",
            Path("agent_core"),
        )
        add_python_tree(
            archive,
            REPO_ROOT / "core" / "python" / "agent_app",
            Path("agent_app"),
        )
        add_python_tree(
            archive,
            (
                REPO_ROOT
                / "plugins"
                / "reference-openai-compatible-provider"
                / "src"
                / "reference_openai_compatible_provider"
            ),
            Path("reference_openai_compatible_provider"),
        )
        add_python_tree(
            archive,
            (
                REPO_ROOT
                / "plugins"
                / "embedded-tools-shared"
                / "src"
                / "embedded_tools_shared"
            ),
            Path("embedded_tools_shared"),
        )
        add_python_tree(
            archive,
            (
                REPO_ROOT
                / "plugins"
                / "embedded-claude-tools"
                / "src"
                / "embedded_claude_tools"
            ),
            Path("embedded_claude_tools"),
        )
        add_python_tree(
            archive,
            (
                REPO_ROOT
                / "plugins"
                / "embedded-codex-tools"
                / "src"
                / "embedded_codex_tools"
            ),
            Path("embedded_codex_tools"),
        )
        add_package_tree(
            archive,
            (
                REPO_ROOT
                / "plugins"
                / "openai_responses"
                / "src"
                / "openai_responses_plugins"
            ),
            Path("openai_responses_plugins"),
        )
        add_package_tree(
            archive,
            (
                REPO_ROOT
                / "plugins"
                / "anthropic-compatible"
                / "src"
                / "anthropic_plugins"
            ),
            Path("anthropic_plugins"),
        )
        add_package_tree(
            archive,
            REPO_ROOT / "plugins" / "openrouter" / "src" / "openrouter_plugins",
            Path("openrouter_plugins"),
        )
        for project, package in APP_PLUGIN_PACKAGES:
            add_python_tree(
                archive,
                REPO_ROOT / "plugins" / project / "src" / package,
                Path(package),
            )
        archive.write(
            APPLICATION_PACKAGE_INIT,
            Path("agent_terminal_app") / "__init__.py",
        )
        archive.write(
            EMBEDDED_CONFIG_PATH,
            Path("agent_terminal_app")
            / "default_config"
            / "embedded-ios"
            / "config.json",
        )
        add_python_tree(archive, PYTHON_APP_SOURCE, Path())
        add_pure_dependency_tree(archive, dependencies)


def patch_python_build_utils(framework_root: Path) -> None:
    utils_path = framework_root / "build" / "utils.sh"
    text = utils_path.read_text(encoding="utf-8")
    count = text.count(UPSTREAM_FRAMEWORK_BUNDLE_ID_LINE)
    if count != 1:
        raise RuntimeError(
            "Python support build helper changed unexpectedly: expected one "
            f"framework bundle-ID assignment in {utils_path}, found {count}"
        )
    utils_path.write_text(
        text.replace(
            UPSTREAM_FRAMEWORK_BUNDLE_ID_LINE,
            PATCHED_FRAMEWORK_BUNDLE_ID_LINES,
        ),
        encoding="utf-8",
    )


def patch_python_dylib_info_templates(framework_root: Path) -> None:
    template_paths = sorted(
        (framework_root / "build").glob("*-dylib-Info-template.plist")
    )
    if not template_paths:
        raise RuntimeError(
            "Python support archive has no dynamic-library Info.plist templates"
        )
    for template_path in template_paths:
        with template_path.open("rb") as handle:
            plist = plistlib.load(handle)
        package_type = plist.get("CFBundlePackageType")
        if package_type != "APPL":
            raise RuntimeError(
                "Python support framework template changed unexpectedly: "
                f"{template_path} has CFBundlePackageType={package_type!r}"
            )
        plist["CFBundlePackageType"] = "FMWK"
        with template_path.open("wb") as handle:
            plistlib.dump(plist, handle, sort_keys=False)


def prepare_runtime(archive: Path) -> None:
    app_source_digest = source_digest()
    expected_marker = (
        f"{PYTHON_SUPPORT_TAG}:{ARCHIVE_SHA256}:{RUNTIME_LAYOUT_VERSION}:"
        f"{app_source_digest}\n"
    )
    if (
        MARKER_PATH.is_file()
        and MARKER_PATH.read_text(encoding="utf-8") == expected_marker
        and (VENDOR_DIR / "Python.xcframework").is_dir()
        and (RESOURCES_DIR / "crystal_lattice_app.zip").is_file()
    ):
        print(f"iOS Python runtime already prepared at {RUNTIME_ROOT}")
        return

    with tempfile.TemporaryDirectory(prefix="crystal-ios-python-") as temporary:
        extracted = Path(temporary)
        with tarfile.open(archive, "r:gz") as support_archive:
            support_archive.extractall(extracted, filter="data")

        source_framework = extracted / "Python.xcframework"
        if not source_framework.is_dir():
            raise RuntimeError("Python support archive has an unexpected layout")

        staged_vendor = extracted / "staged-vendor"
        staged_resources = extracted / "staged-resources"
        staged_framework = staged_vendor / "Python.xcframework"
        shutil.copytree(source_framework, staged_framework)
        patch_python_build_utils(staged_framework)
        patch_python_dylib_info_templates(staged_framework)
        create_application_archive(staged_resources / "crystal_lattice_app.zip")
        shutil.copy2(
            EMBEDDED_CONFIG_PATH,
            staged_resources / "embedded-ios-config.json",
        )
        if REVIEWER_CA_PATH.is_file():
            shutil.copy2(
                REVIEWER_CA_PATH,
                staged_resources / REVIEWER_CA_PATH.name,
            )

        shutil.rmtree(VENDOR_DIR, ignore_errors=True)
        shutil.rmtree(RESOURCES_DIR, ignore_errors=True)
        VENDOR_DIR.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(staged_vendor, VENDOR_DIR)
        shutil.move(staged_resources, RESOURCES_DIR)

    MARKER_PATH.write_text(expected_marker, encoding="utf-8")
    print(f"Prepared iOS Python runtime at {RUNTIME_ROOT}")


def main() -> None:
    prepare_runtime(ensure_archive())


if __name__ == "__main__":
    main()
