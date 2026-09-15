from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_bundle_runner_selects_only_marked_provider_files() -> None:
    module = load_module(
        "embedded_provider_bundle_runner_test",
        ROOT
        / "mobile"
        / "crystal-lattice-control-rn"
        / "scripts"
        / "run_embedded_provider_bundle_tests.py",
    )

    selected = {
        suite.project: [path.name for path in suite.marked_test_files()]
        for suite in module.SUITES
    }

    assert selected["openai_responses"] == [
        "test_openai_responses_provider_integration.py"
    ]
    assert selected["openrouter"] == [
        "test_openrouter_basic_integration.py",
        "test_openrouter_models_api_integration.py",
        "test_openrouter_usage_extension_integration.py",
    ]
    assert all(
        not name.startswith("test_agent_application")
        for names in selected.values()
        for name in names
    )


def test_bundle_runner_installs_dev_requirements_without_artifact_runtime() -> None:
    module = load_module(
        "embedded_provider_bundle_requirements_test",
        ROOT
        / "mobile"
        / "crystal-lattice-control-rn"
        / "scripts"
        / "run_embedded_provider_bundle_tests.py",
    )

    for suite in module.SUITES:
        requirements = module.dev_requirements(suite)
        names = {
            module.normalized_distribution_name(requirement)
            for requirement in requirements
        }
        assert "agent-core" not in names
        assert suite.distribution not in names
        assert "pytest" in names


def test_bundle_runner_archive_digest_detects_changes(tmp_path: Path) -> None:
    module = load_module(
        "embedded_provider_bundle_digest_test",
        ROOT
        / "mobile"
        / "crystal-lattice-control-rn"
        / "scripts"
        / "run_embedded_provider_bundle_tests.py",
    )
    archive = tmp_path / "runtime.zip"
    archive.write_bytes(b"first")
    before = module.archive_digest(archive)
    archive.write_bytes(b"second")
    assert module.archive_digest(archive) != before


def test_bundle_runner_rejects_dev_content_in_archive(tmp_path: Path) -> None:
    module = load_module(
        "embedded_provider_bundle_dev_content_test",
        ROOT
        / "mobile"
        / "crystal-lattice-control-rn"
        / "scripts"
        / "run_embedded_provider_bundle_tests.py",
    )
    archive = tmp_path / "runtime.zip"
    import zipfile

    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("pytest/__init__.py", "")

    with pytest.raises(RuntimeError, match="dev/test content"):
        module.assert_archive_excludes_dev_content(archive)


def test_provenance_plugin_rejects_runtime_module_outside_archive(
    tmp_path: Path,
) -> None:
    bootstrap = load_module(
        "embedded_provider_bundle_bootstrap_test",
        ROOT / "test" / "run_pytest_from_embedded_bundle.py",
    )
    archive = tmp_path / "runtime.zip"
    plugin = bootstrap.BundleProvenancePlugin(archive, ["provider_under_test"])
    module = types.ModuleType("provider_under_test")
    module.__file__ = str(tmp_path / "source" / "__init__.py")
    sys.modules[module.__name__] = module
    try:
        with pytest.raises(AssertionError, match="did not import"):
            plugin.assert_origins()
    finally:
        sys.modules.pop(module.__name__, None)