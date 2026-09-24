from __future__ import annotations

import re
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[5]
REVIEW_ROOT = REPOSITORY_ROOT / "maintainer" / "docs" / "evaluations" / "task-guidance"
SUITE_ROOT = Path(__file__).resolve().parents[1]
INTEGRATION_ROOT = (
    REPOSITORY_ROOT
    / "maintainer"
    / "docs"
    / "development"
    / "specifications"
    / "crystal-lattice-guidance-integration"
)
TASK_PATH = (
    REPOSITORY_ROOT
    / "tasks"
    / "20260728-package-local-documentation-standard"
    / "090-task-guidance-handoff-baseline-and-placement.md"
)
STAGE_ID = re.compile(r"\bB[012]\b")
SCENARIO_ID = re.compile(r"\bTG-0[1-6]\b")
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)


def test_review_document_set_is_complete() -> None:
    expected = {
        "index.md",
        "test-plan.md",
        "test-cases.md",
        "20260919-current-guidance-baseline-results.md",
        "20260919-task-mechanics-b1-results.md",
        "reproducing-and-inspecting-results.md",
    }

    assert expected <= {path.name for path in REVIEW_ROOT.glob("*.md")}
    assert not REVIEW_ROOT.joinpath("20260919-current-guidance-glm-b0.md").exists()


def _reviewed_documents() -> tuple[Path, ...]:
    values = {
        *REVIEW_ROOT.glob("*.md"),
        *SUITE_ROOT.joinpath("docs").rglob("*.md"),
        SUITE_ROOT / "scenarios" / "index.md",
        *INTEGRATION_ROOT.glob("*.md"),
        TASK_PATH,
    }
    return tuple(sorted(values))


def test_stage_and_scenario_ids_are_explained_where_used() -> None:
    failures: list[str] = []
    for path in _reviewed_documents():
        for number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            for match in STAGE_ID.finditer(line):
                label = f"Stage {match.group()} —"
                if label not in line:
                    failures.append(f"{path}:{number}: unexplained {match.group()}")
            for match in SCENARIO_ID.finditer(line):
                label = f"Scenario {match.group()} —"
                contract_heading = f"# {match.group()}:"
                if label not in line and contract_heading not in line:
                    failures.append(f"{path}:{number}: unexplained {match.group()}")

    assert not failures, "\n".join(failures)


def test_review_document_links_resolve() -> None:
    missing: list[str] = []
    for path in _reviewed_documents():
        text = path.read_text(encoding="utf-8")
        for target in MARKDOWN_LINK.findall(text):
            if target.startswith(("http:", "https:", "#", "mailto:")):
                continue
            raw, _, fragment = target.partition("#")
            destination = (path.parent / raw).resolve() if raw else path
            if raw and not destination.exists():
                missing.append(f"{path}: {target}")
                continue
            if fragment and destination.suffix == ".md":
                headings = {
                    _heading_slug(value)
                    for value in HEADING.findall(
                        destination.read_text(encoding="utf-8")
                    )
                }
                if fragment not in headings:
                    missing.append(f"{path}: missing anchor {target}")

    assert not missing, "\n".join(missing)


def _heading_slug(value: str) -> str:
    normalized = re.sub(r"[^\w\- ]", "", value.lower())
    return normalized.replace(" ", "-")
