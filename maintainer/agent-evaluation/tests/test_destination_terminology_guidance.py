from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from maintainer.guidance import compile_guidance
from suites.documentation_standard.destination_terminology import (
    destination_terminology_guidance_source,
    selected_destination_terminology_variant,
)
from suites.documentation_standard.support import (
    CURRENT_GUIDANCE_PATHS,
    SCENARIO_ROOT,
    apply_fixture,
    extract_blockquote,
)
from suites.documentation_standard.test_consumers import (
    _complete_read_positions,
    _first_mutation_tool_index,
    _tool_command_observed,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CURRENT_PORTABLE = (
    REPOSITORY_ROOT / "maintainer/guidance/current/sections/documentation.md"
)
CURRENT_GUIDE = REPOSITORY_ROOT / "docs/development/documentation.md"
CRYSTAL_TARGET = "maintainer/guidance/targets/crystal-lattice"
GUIDE_TARGET = (
    "maintainer/agent-evaluation/suites/documentation_standard/fixtures/"
    "destination_terminology/guidance"
)
CANDIDATES = (
    "destination-terminology-abstract-specific",
    "destination-terminology-explicit-contexts-specific",
)
HELD_OUT_TERMS = (
    "Task 010",
    "Stage A",
    "useful, portable",
    "Milestone Cedar",
    "Phase 1",
    "Phase 2",
    "Phase 3",
    "STATUS-002",
)


def _bundle(candidate_id: str) -> str:
    return f"maintainer/guidance/candidates/{candidate_id}"


def _candidate_section(candidate_id: str, name: str) -> str:
    return (REPOSITORY_ROOT / _bundle(candidate_id) / "sections" / name).read_text(
        encoding="utf-8"
    )


@pytest.mark.parametrize("candidate_id", CANDIDATES)
@pytest.mark.requirements("DOCAGENT-002", "DSEVAL-004")
def test_destination_terminology_candidate_compiles_paired_outputs(
    candidate_id: str,
) -> None:
    """The portable and complete-guide forms share one compiler identity.

    The Crystal Lattice target verifies the concise recurring instruction and
    unchanged task guidance. The suite target verifies the detailed guide
    application without committing a generated repository root.
    """

    root = compile_guidance(
        bundle=_bundle(candidate_id),
        target=CRYSTAL_TARGET,
        repository_root=REPOSITORY_ROOT,
    )
    guide = compile_guidance(
        bundle=_bundle(candidate_id),
        target=GUIDE_TARGET,
        repository_root=REPOSITORY_ROOT,
    )
    root_text = root.outputs["AGENTS.md"].decode("utf-8")
    guide_text = guide.outputs["docs/development/documentation.md"].decode("utf-8")
    portable = _candidate_section(candidate_id, "documentation.md").strip()
    detailed = _candidate_section(
        candidate_id,
        "documentation-guide.md",
    ).strip()

    assert root.bundle_id == candidate_id
    assert guide.bundle_id == candidate_id
    assert root.target_id == "crystal-lattice"
    assert guide.target_id == "destination-terminology-guide"
    assert root.target_kind == "project"
    assert guide.target_kind == "fixture"
    assert root_text.count(portable) == 1
    assert guide_text.count(detailed) == 1
    assert (
        root.outputs["agents/TASKS-v7.md"]
        == (REPOSITORY_ROOT / "agents/TASKS-v7.md").read_bytes()
    )
    assert root.lock["compilation_sha256"] != guide.lock["compilation_sha256"]


@pytest.mark.parametrize("candidate_id", CANDIDATES)
@pytest.mark.requirements("DOCGUIDE-008", "DOCGUIDE-009", "DOCAGENT-002")
def test_destination_terminology_candidates_stay_within_initial_size_limit(
    candidate_id: str,
) -> None:
    """Both maintained guidance forms remain within the approved 20% ceiling."""

    portable_words = len(_candidate_section(candidate_id, "documentation.md").split())
    current_portable_words = len(CURRENT_PORTABLE.read_text(encoding="utf-8").split())
    guide = compile_guidance(
        bundle=_bundle(candidate_id),
        target=GUIDE_TARGET,
        repository_root=REPOSITORY_ROOT,
    )
    guide_words = len(
        guide.outputs["docs/development/documentation.md"].decode("utf-8").split()
    )
    current_guide_words = len(CURRENT_GUIDE.read_text(encoding="utf-8").split())

    assert portable_words <= current_portable_words * 1.20
    assert guide_words <= current_guide_words * 1.20


@pytest.mark.parametrize("candidate_id", CANDIDATES)
@pytest.mark.requirements("DOCGUIDE-008", "DOCGUIDE-009", "DSEVAL-004")
def test_destination_terminology_guide_changes_only_its_owned_section(
    candidate_id: str,
) -> None:
    """The fixture target preserves the current guide outside the candidate."""

    current = CURRENT_GUIDE.read_text(encoding="utf-8")
    detailed = _candidate_section(
        candidate_id,
        "documentation-guide.md",
    ).rstrip()
    start = current.index("## Write pages readers can use")
    end = current.index("## Specifications, requirements, and tasks")
    expected = current[:start] + detailed + "\n\n" + current[end:]
    guide = compile_guidance(
        bundle=_bundle(candidate_id),
        target=GUIDE_TARGET,
        repository_root=REPOSITORY_ROOT,
    )

    assert (
        guide.outputs["docs/development/documentation.md"].decode("utf-8") == expected
    )


@pytest.mark.parametrize("candidate_id", CANDIDATES)
@pytest.mark.requirements("DOCGUIDE-008", "DOCGUIDE-009")
def test_destination_terminology_examples_are_separate_from_scenarios(
    candidate_id: str,
) -> None:
    """Examples illustrate the rule without repeating held-out test wording."""

    portable = _candidate_section(candidate_id, "documentation.md")
    detailed = _candidate_section(candidate_id, "documentation-guide.md")
    combined = portable + "\n" + detailed
    normalized_portable = " ".join(portable.split())
    normalized_detailed = " ".join(detailed.split())

    if candidate_id.endswith("abstract-specific"):
        assert (
            "make no change to that file until the user chooses" in normalized_portable
        )
        assert (
            "make no change to that file until the user chooses" in normalized_detailed
        )
    else:
        assert "cleanup question, not established terminology" in normalized_portable
        assert "not established merely because it is present" in normalized_detailed
    assert "Blue bundle" in normalized_portable
    assert "Blue bundle" not in normalized_detailed
    assert "Launch packet" in normalized_detailed
    assert "Launch packet" not in normalized_portable
    for term in HELD_OUT_TERMS:
        assert term not in combined


@pytest.mark.parametrize("candidate_id", CANDIDATES)
@pytest.mark.requirements("DOCGUIDE-008", "DOCGUIDE-009")
def test_destination_terminology_specific_rules_are_reviewable(
    candidate_id: str,
) -> None:
    """The detailed guide states the non-obvious reference and cleanup rules."""

    detailed = _candidate_section(candidate_id, "documentation-guide.md")
    lowered = detailed.lower()

    assert "### Apply the rules by context" in detailed
    assert "without appending a local number, stage, or nickname" in detailed
    assert "nearby text explains the behavior" in detailed
    assert "pause the affected file" in lowered
    assert "ask before changing internal-looking wording" in lowered
    assert "Expired entries are excluded (CACHE-004)" in detailed
    assert "# CACHE-004: expired entries are excluded" in detailed


@pytest.mark.parametrize(
    "variant",
    (
        "current",
        "abstract-specific",
        "explicit-contexts-specific",
    ),
)
def test_destination_terminology_guidance_source_records_provenance(
    variant: str,
) -> None:
    source = destination_terminology_guidance_source(variant)
    metadata = source.metadata()
    provenance = metadata["provenance"]

    assert tuple(item.path for item in source.files()) == CURRENT_GUIDANCE_PATHS
    assert source.name == f"destination-terminology-{variant}"
    assert isinstance(provenance, dict)
    assert provenance["variant"] == variant
    assert isinstance(provenance["root_compilation"], dict)
    if variant == "current":
        assert isinstance(provenance["guide_source"], dict)
        assert "guide_compilation" not in provenance
    else:
        assert isinstance(provenance["guide_compilation"], dict)
        assert "guide_source" not in provenance


def test_destination_terminology_variant_selection_rejects_unknown_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "AGENT_EVAL_DESTINATION_TERMINOLOGY_VARIANT",
        "unknown",
    )

    with pytest.raises(ValueError, match="must be one of"):
        selected_destination_terminology_variant()


def test_revised_test_13_fixture_starts_without_progress_labels(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "sync-engine"
    workspace.mkdir()
    workspace.joinpath(".git").write_text("fixture\n", encoding="utf-8")
    apply_fixture(workspace, "sync-engine", "base")

    readme = workspace.joinpath("packages/sync-engine/README.md").read_text(
        encoding="utf-8"
    )
    product = workspace.joinpath(
        "packages/sync-engine/docs/development/specifications/"
        "sync-v2/product-spec.md"
    ).read_text(encoding="utf-8")

    assert "Phase" not in readme
    assert "local changes" in readme
    assert "Phase 1" in product
    assert "Phase 2" in product
    assert "Phase 3" in product


@pytest.mark.parametrize(
    ("fixture_id", "variant", "relative", "term"),
    (
        (
            "batch-sync",
            "terminology-task-number",
            "tasks/batch-offline-sync.md",
            "Task 010",
        ),
        (
            "batch-sync",
            "terminology-sequence-label",
            "tasks/batch-offline-sync.md",
            "Stage A",
        ),
        (
            "batch-sync",
            "terminology-evaluative-wording",
            "tasks/batch-offline-sync.md",
            "useful, portable",
        ),
        (
            "status-labels",
            "terminology-task-number",
            "tasks/status-label-formatting.md",
            "Task 010",
        ),
        (
            "status-labels",
            "terminology-sequence-label",
            "tasks/status-label-formatting.md",
            "Stage A",
        ),
        (
            "status-labels",
            "terminology-evaluative-wording",
            "tasks/status-label-formatting.md",
            "useful, portable",
        ),
    ),
)
def test_source_terms_are_confined_to_branch_tasks(
    tmp_path: Path,
    fixture_id: str,
    variant: str,
    relative: str,
    term: str,
) -> None:
    workspace = tmp_path / f"{fixture_id}-{variant}"
    workspace.mkdir()
    workspace.joinpath(".git").write_text("fixture\n", encoding="utf-8")
    apply_fixture(workspace, fixture_id, variant)

    task = workspace.joinpath(relative).read_text(encoding="utf-8")
    other_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in workspace.rglob("*")
        if path.is_file()
        and path.name != ".git"
        and path.relative_to(workspace).as_posix() != relative
    )

    assert term in task
    assert term not in other_text


def test_existing_terminology_is_absent_from_prompt_and_guidance(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "event-retry"
    workspace.mkdir()
    workspace.joinpath(".git").write_text("fixture\n", encoding="utf-8")
    apply_fixture(
        workspace,
        "event-retry",
        "existing-terminology-confirmation",
    )
    publishing = workspace.joinpath("packages/event-sdk/docs/publishing.md").read_text(
        encoding="utf-8"
    )
    prompt = extract_blockquote(
        SCENARIO_ROOT / "38-confirm-existing-terminology-cleanup.md",
        "## Exact user prompt",
    )
    candidate_text = "\n".join(
        path.read_text(encoding="utf-8")
        for candidate_id in CANDIDATES
        for path in (REPOSITORY_ROOT / _bundle(candidate_id) / "sections").glob("*.md")
    )

    assert "Release marker Birch" in publishing
    assert "release marker birch" not in prompt.lower()
    assert "release marker birch" not in candidate_text.lower()


def test_production_claude_tool_observation_uses_call_timeline(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    artifact_dir = tmp_path / "artifact"
    target = workspace / "docs/development/documentation.md"
    target.parent.mkdir(parents=True)
    target.write_text("complete guide\n", encoding="utf-8")
    recorded_target = (
        tmp_path / "cached-run/workspace/docs/development/documentation.md"
    )
    raw = artifact_dir / "raw/environment"
    raw.mkdir(parents=True)
    session = {
        "messages": [
            {
                "role": "assistant",
                "metadata": {
                    "tool_calls": [
                        {
                            "function": {
                                "name": "read",
                                "arguments": json.dumps(
                                    {"file_path": str(recorded_target)}
                                ),
                            }
                        }
                    ]
                },
            },
            {
                "role": "tool",
                "_metadata": {
                    "tool_name": "read",
                    "tool_plugin": "claude_read_tool",
                },
                "content": "complete guide\n",
            },
            {
                "role": "assistant",
                "tool_calls": [
                    {
                        "function": {
                            "name": "bash",
                            "arguments": json.dumps(
                                {
                                    "command": (
                                        "python -m pytest "
                                        "packages/status-labels/tests -q"
                                    )
                                }
                            ),
                        }
                    }
                ],
            },
            {
                "role": "tool",
                "_metadata": {
                    "tool_name": "bash",
                    "tool_plugin": "claude_bash_tool",
                },
                "content": "3 passed in 0.01s",
            },
            {
                "role": "assistant",
                "metadata": {
                    "tool_calls": [
                        {
                            "function": {
                                "name": "edit",
                                "arguments": json.dumps(
                                    {
                                        "file_path": str(target),
                                        "old_string": "complete",
                                        "new_string": "updated",
                                    }
                                ),
                            }
                        }
                    ]
                },
            },
        ]
    }
    raw.joinpath("crystal-lattice-session.json").write_text(
        json.dumps(session),
        encoding="utf-8",
    )
    run = SimpleNamespace(
        artifact_dir=artifact_dir,
        workspace=workspace,
    )

    assert _tool_command_observed(run, "pytest")
    assert _complete_read_positions(
        run,
        ("docs/development/documentation.md",),
    ) == {"docs/development/documentation.md": 0}
    assert _first_mutation_tool_index(run) == 4


def test_production_gpt_shell_reads_combine_complete_file_ranges(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    artifact_dir = tmp_path / "artifact"
    relative = "docs/development/documentation.md"
    target = workspace / relative
    target.parent.mkdir(parents=True)
    target.write_text("one\ntwo\nthree\nfour\n", encoding="utf-8")
    raw = artifact_dir / "raw/environment"
    raw.mkdir(parents=True)
    session = {
        "messages": [
            {
                "role": "assistant",
                "tool_calls": [
                    {
                        "function": {
                            "name": "shell",
                            "arguments": json.dumps(
                                {
                                    "command": [
                                        "bash",
                                        "-lc",
                                        f"sed -n '1,2p' {relative}",
                                    ]
                                }
                            ),
                        }
                    }
                ],
            },
            {"role": "tool", "content": "one\ntwo\n"},
            {
                "role": "assistant",
                "metadata": {
                    "tool_calls": [
                        {
                            "function": {
                                "name": "shell",
                                "arguments": json.dumps(
                                    {
                                        "command": [
                                            "bash",
                                            "-lc",
                                            f"sed -n '3,20p' {relative}",
                                        ]
                                    }
                                ),
                            }
                        }
                    ]
                },
            },
            {"role": "tool", "content": "three\nfour\n"},
            {
                "role": "assistant",
                "tool_calls": [
                    {
                        "function": {
                            "name": "apply_patch",
                            "arguments": json.dumps({"patch": "change"}),
                        }
                    }
                ],
            },
        ]
    }
    raw.joinpath("crystal-lattice-session.json").write_text(
        json.dumps(session),
        encoding="utf-8",
    )
    run = SimpleNamespace(
        artifact_dir=artifact_dir,
        workspace=workspace,
    )

    assert _complete_read_positions(run, (relative,)) == {relative: 2}
    assert _first_mutation_tool_index(run) == 4
