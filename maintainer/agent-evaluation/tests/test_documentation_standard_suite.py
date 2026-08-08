from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from suites.documentation_standard.support import (
    PROFILES,
    SPEC_ROOT,
    ScenarioWorkspaceFactory,
    apply_fixture,
    candidate_guidance_files,
    candidate_guidance_sha256,
    completed_tool_call_ids,
    extract_blockquote,
    fixture_revision,
)


def test_profiles_pin_requested_models() -> None:
    assert PROFILES["glm"].model == "glm-5.2:cloud"
    assert PROFILES["glm"].hosted is False
    assert PROFILES["gpt"].model == "gpt-5.6-luna"
    assert PROFILES["gpt"].auth_mode == "chatgpt"
    assert PROFILES["gpt"].hosted is True


def test_candidate_guidance_provenance_is_stable() -> None:
    files = candidate_guidance_files()
    assert files
    assert all(len(item.sha256) == 64 for item in files)
    assert len(candidate_guidance_sha256()) == 64


def test_exact_seed_and_branch_prompts_come_from_specification() -> None:
    seed = extract_blockquote(
        SPEC_ROOT / "seed-01-js-single-file-tool-documentation.md",
        "## Exact seed prompt",
    )
    branch = extract_blockquote(
        SPEC_ROOT / "01-small-package-documentation.md",
        "## Exact user prompt",
    )
    assert seed.startswith("Please investigate `plugins/js-single-file-tool`")
    assert branch == (
        "Please implement the documentation improvements identified in the "
        "investigation. Keep the scope to documentation."
    )


def test_all_current_specification_pages_are_indexed() -> None:
    index = SPEC_ROOT.joinpath("index.md").read_text(encoding="utf-8")
    for path in sorted(SPEC_ROOT.glob("[0-9][0-9]-*.md")):
        assert path.name in index
    for path in sorted(SPEC_ROOT.glob("seed-*.md")):
        assert path.name in index


def test_specification_root_exists() -> None:
    assert isinstance(SPEC_ROOT, Path)
    assert SPEC_ROOT.is_dir()


def test_completed_tool_calls_ignore_stream_fragments() -> None:
    partial = {
        "type": "tool_partial",
        "tool_call_id": "call-1",
        "phase": "stream",
    }
    results = {
        "type": "tool_results",
        "messages": [
            {"metadata": {"tool_call_id": "call-1"}},
            {"metadata": {"tool_call_id": "call-2"}},
        ],
    }

    assert completed_tool_call_ids(partial) == ()
    assert completed_tool_call_ids(results) == ("call-1", "call-2")


def test_completed_tool_calls_support_claude_result_shape() -> None:
    event = {
        "type": "tool_results",
        "messages": [
            {
                "metadata": {
                    "tool_call_id": "call_claude",
                    "tool_name": "Bash",
                }
            }
        ],
    }

    assert completed_tool_call_ids(event) == ("call_claude",)


def test_all_seed_and_consumer_prompts_are_extractable() -> None:
    for path in sorted(SPEC_ROOT.glob("seed-*.md")):
        assert extract_blockquote(path, "## Exact seed prompt")
    for path in sorted(SPEC_ROOT.glob("[0-9][0-9]-*.md")):
        headings = (
            ("## First exact user prompt", "## Second exact user prompt")
            if path.name.startswith("06-")
            else ("## Exact user prompt",)
        )
        for heading in headings:
            assert extract_blockquote(path, heading)


def test_synthetic_fixtures_contain_expected_seed_sources(tmp_path: Path) -> None:
    fixtures = {
        "report-export": "tasks/report-export-max-rows.md",
        "mobile-composer": "tasks/mobile-composer-ux.md",
        "event-retry": "packages/event-sdk/src/events.py",
        "batch-sync": "packages/batch-sdk/src/batch.py",
        "path-policy": "tasks/path-policy-home-relative-bug.md",
        "slug-utils": "packages/slug-utils/src/slug_cache.py",
        "label-utils": (
            "packages/label-utils/docs/development/specifications/"
            "label-normalization/technical-spec.md"
        ),
        "sync-engine": "tasks/sync-v2.md",
    }
    for fixture_id, expected in fixtures.items():
        workspace = tmp_path / fixture_id
        workspace.mkdir()
        workspace.joinpath(".git").write_text("fixture\n", encoding="utf-8")
        apply_fixture(workspace, fixture_id, "base")
        assert workspace.joinpath("AGENTS.md").is_file()
        assert workspace.joinpath(expected).is_file()


def test_synthetic_python_fixture_baselines_are_runnable(tmp_path: Path) -> None:
    package_paths = {
        "report-export": "packages/report-export-sdk/tests",
        "event-retry": "packages/event-sdk/tests",
        "path-policy": "packages/path-policy/tests",
        "slug-utils": "packages/slug-utils/tests",
        "label-utils": "packages/label-utils/tests",
        "sync-engine": "packages/sync-engine/tests",
    }
    for fixture_id, tests_path in package_paths.items():
        workspace = tmp_path / fixture_id
        workspace.mkdir()
        workspace.joinpath(".git").write_text("fixture\n", encoding="utf-8")
        apply_fixture(workspace, fixture_id, "base")

        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", tests_path],
            cwd=workspace,
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, (
            f"{fixture_id} fixture baseline failed:\n"
            f"{result.stdout}\n{result.stderr}"
        )


def test_fixture_revision_participates_in_workspace_fingerprint() -> None:
    factory = ScenarioWorkspaceFactory(
        fixture_id="slug-utils",
        candidate_guidance=False,
    )

    assert fixture_revision("slug-utils") == "v2"
    assert factory.fingerprint()["fixture_revision"] == "v2"


def test_batch_approved_task_variant_adds_authorization(tmp_path: Path) -> None:
    workspace = tmp_path / "batch"
    workspace.mkdir()
    workspace.joinpath(".git").write_text("fixture\n", encoding="utf-8")

    apply_fixture(workspace, "batch-sync", "approved-task")

    task = workspace.joinpath("tasks/batch-offline-sync.md")
    assert task.is_file()
    assert "Status: Approved" in task.read_text(encoding="utf-8")