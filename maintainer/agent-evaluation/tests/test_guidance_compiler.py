from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from maintainer.guidance import compile_guidance
from maintainer.guidance.compiler import check_compilation


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CURRENT_BUNDLE = "maintainer/guidance/current"
CANDIDATE_BUNDLE = (
    "maintainer/guidance/candidates/root-requirements-testing-v2"
)
CRYSTAL_TARGET = "maintainer/guidance/targets/crystal-lattice"


def test_current_crystal_lattice_compilation_is_exact() -> None:
    result = compile_guidance(
        bundle=CURRENT_BUNDLE,
        target=CRYSTAL_TARGET,
        repository_root=REPOSITORY_ROOT,
    )

    assert check_compilation(
        result,
        destination=REPOSITORY_ROOT,
    ) == ()
    assert result.outputs["AGENTS.md"] == (
        REPOSITORY_ROOT / "AGENTS.md"
    ).read_bytes()
    assert result.outputs["agents/TASKS-v7.md"] == (
        REPOSITORY_ROOT / "agents/TASKS-v7.md"
    ).read_bytes()


def test_candidate_reproduces_reviewed_crystal_lattice_rendering() -> None:
    result = compile_guidance(
        bundle=CANDIDATE_BUNDLE,
        target=CRYSTAL_TARGET,
        repository_root=REPOSITORY_ROOT,
    )
    reviewed = (
        REPOSITORY_ROOT
        / "maintainer/agent-evaluation/suites/documentation_standard/"
        "guidance_variants/root-guidance/combined-v2/AGENTS.md"
    ).read_bytes()

    assert result.outputs["AGENTS.md"] == reviewed
    assert result.outputs["agents/TASKS-v7.md"] == (
        REPOSITORY_ROOT / "agents/TASKS-v7.md"
    ).read_bytes()


def test_external_target_can_live_outside_source_repository(
    tmp_path: Path,
) -> None:
    target = tmp_path / "consumer-guidance"
    _write(
        target,
        "target.toml",
        """
format = 1
id = "consumer"
[outputs]
"AGENTS.md" = "AGENTS.md.in"
[slots.project-context]
source = "target"
path = "project-context.md"
[slots.requirements]
source = "bundle"
section = "requirements"
[slots.testing-strategy]
source = "bundle"
section = "testing-strategy"
""",
    )
    _write(
        target,
        "AGENTS.md.in",
        """# Consumer project

<!-- guidance-slot:project-context -->

<!-- guidance-slot:requirements -->

<!-- guidance-slot:testing-strategy -->
""",
    )
    _write(
        target,
        "project-context.md",
        "## Project context\n\nConsumer-owned local instructions.\n",
    )
    current = compile_guidance(
        bundle=REPOSITORY_ROOT / CURRENT_BUNDLE,
        target=target,
    )
    candidate = compile_guidance(
        bundle=REPOSITORY_ROOT / CANDIDATE_BUNDLE,
        target=target,
    )
    current_text = current.outputs["AGENTS.md"].decode("utf-8")
    candidate_text = candidate.outputs["AGENTS.md"].decode("utf-8")

    assert "Consumer-owned local instructions." in current_text
    assert "Consumer-owned local instructions." in candidate_text
    assert "## Requirements" not in current_text
    assert "## Requirements" in candidate_text
    assert current.lock["target"]["path"] == str(target.resolve())


def test_compiler_rejects_duplicate_and_unused_slots(
    tmp_path: Path,
) -> None:
    repository = _temporary_repository(tmp_path)
    _write(
        repository,
        "bundle/bundle.toml",
        """
format = 1
id = "test"
[sections]
one = "one.md"
two = "two.md"
""",
    )
    _write(repository, "bundle/one.md", "one")
    _write(repository, "bundle/two.md", "two")
    _write(
        repository,
        "target/target.toml",
        """
format = 1
id = "target"
[outputs]
"AGENTS.md" = "AGENTS.md.in"
[slots.one]
source = "bundle"
section = "one"
[slots.two]
source = "bundle"
section = "two"
""",
    )
    _write(
        repository,
        "target/AGENTS.md.in",
        "<!-- guidance-slot:one --><!-- guidance-slot:one -->",
    )
    _commit(repository, "initial")

    with pytest.raises(ValueError, match="duplicate slots"):
        compile_guidance(
            bundle="bundle",
            target="target",
            repository_root=repository,
        )

    _write(
        repository,
        "target/AGENTS.md.in",
        "<!-- guidance-slot:one -->",
    )
    with pytest.raises(ValueError, match="unused slots"):
        compile_guidance(
            bundle="bundle",
            target="target",
            repository_root=repository,
        )


def test_compilation_hash_is_stable_across_absolute_locations(
    tmp_path: Path,
) -> None:
    hashes: list[str] = []
    for name in ("first", "second"):
        repository = tmp_path / name
        bundle = repository / "bundle"
        target = repository / "target"
        _write(
            bundle,
            "bundle.toml",
            """
format = 1
id = "test"
[sections]
body = "body.md"
""",
        )
        _write(bundle, "body.md", "portable body\n")
        _write(
            target,
            "target.toml",
            """
format = 1
id = "target"
[outputs]
"AGENTS.md" = "AGENTS.md.in"
[slots.body]
source = "bundle"
section = "body"
""",
        )
        _write(
            target,
            "AGENTS.md.in",
            "<!-- guidance-slot:body -->",
        )
        result = compile_guidance(bundle=bundle, target=target)
        assert result.outputs["AGENTS.md"] == b"portable body\n"
        hashes.append(str(result.lock["compilation_sha256"]))

    assert hashes[0] == hashes[1]


def _temporary_repository(tmp_path: Path) -> Path:
    repository = tmp_path / "repository"
    repository.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repository, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repository,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repository,
        check=True,
    )
    return repository


def _write(repository: Path, relative: str, content: str) -> None:
    path = repository / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip(), encoding="utf-8")


def _commit(repository: Path, message: str) -> str:
    subprocess.run(["git", "add", "."], cwd=repository, check=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", message],
        cwd=repository,
        check=True,
    )
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()