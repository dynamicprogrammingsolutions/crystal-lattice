from __future__ import annotations

import json
import re
import subprocess
import sys
from typing import Any

from suites.documentation_standard.support import (
    CURRENT_GUIDANCE_PATHS,
    REPOSITORY_ROOT,
    GuidanceSource,
)


FIXTURE_ROOT = (
    REPOSITORY_ROOT
    / "maintainer/agent-evaluation/suites/documentation_standard/fixtures/"
    "destination_terminology_guidance_sets"
)
SETS_ROOT = FIXTURE_ROOT / "sets"
SOURCES_ROOT = FIXTURE_ROOT / "sources"
COMPILER = FIXTURE_ROOT / "compile.py"
BASE_SET_ID = "option-a-checkpoint"
FAMILIES = (
    "abstract",
    "action-first",
    "file-centered",
    "explicit-contexts",
    "contextual",
)
EXPECTED_SET_IDS = {
    BASE_SET_ID,
    *(f"{family}-{mode}" for family in FAMILIES for mode in ("generic", "specific")),
}
CHANGED_GUIDANCE_PATHS = {
    "AGENTS.md",
    "docs/development/documentation.md",
}
HELD_OUT_TERMS = (
    "task 010",
    "stage a",
    "track a",
    "track b",
    "phase 1",
    "phase 2",
    "phase 3",
    "portable",
    "useful",
    "status-002",
)


def _manifest(set_id: str) -> dict[str, Any]:
    return json.loads((SETS_ROOT / set_id / "guidance-set.json").read_text())


def _examples(text: str) -> tuple[str, ...]:
    matches = re.findall(
        r"\*Example:\*\s*(.*?)(?=\n\n(?:[1-5]\. |<!-- SPECIFIC_RULES -->))",
        text + "\n\n<!-- SPECIFIC_RULES -->",
        flags=re.DOTALL,
    )
    return tuple(re.sub(r"\s+", " ", match.strip()) for match in matches)


def test_compiled_guidance_sets_match_their_sources() -> None:
    """DOCVAL-011: committed guidance roots reproduce from their fixture sources."""

    subprocess.run(
        [sys.executable, str(COMPILER), "--check"],
        cwd=REPOSITORY_ROOT,
        check=True,
    )


def test_compiled_guidance_sets_are_complete_custom_sources() -> None:
    """DOCVAL-011: every fixture is complete and its manifest matches loading."""

    assert {
        path.name for path in SETS_ROOT.iterdir() if path.is_dir()
    } == EXPECTED_SET_IDS

    for set_id in sorted(EXPECTED_SET_IDS):
        set_root = SETS_ROOT / set_id
        manifest = _manifest(set_id)
        source = GuidanceSource(name=set_id, root=set_root)

        assert manifest["set_id"] == set_id
        assert manifest["base_set"] == BASE_SET_ID
        assert (
            tuple(item["path"] for item in manifest["files"]) == CURRENT_GUIDANCE_PATHS
        )
        assert manifest["combined_sha256"] == source.sha256()
        assert manifest["files"] == [item.__dict__ for item in source.files()]

        guide_words = len(
            source.read_bytes("docs/development/documentation.md").decode().split()
        )
        agents = source.read_bytes("AGENTS.md").decode()
        policy_start = agents.index("## Documentation ownership and routing")
        policy_end = agents.index("**Auxiliary directories**", policy_start)
        root_words = len(agents[policy_start:policy_end].split())

        assert manifest["word_counts"] == {
            "portable_guide": guide_words,
            "root_documentation_policy": root_words,
        }
        assert 200 <= root_words <= 300
        if manifest["rule_mode"] == "generic":
            assert guide_words <= 2200
        elif manifest["rule_mode"] == "specific":
            assert guide_words <= 2466


def test_candidate_sets_change_only_the_reviewed_guidance_files() -> None:
    """DOCVAL-011: candidates preserve every unrelated guidance file exactly."""

    checkpoint = SETS_ROOT / BASE_SET_ID
    for set_id in sorted(EXPECTED_SET_IDS - {BASE_SET_ID}):
        set_root = SETS_ROOT / set_id
        changed = {
            relative
            for relative in CURRENT_GUIDANCE_PATHS
            if (set_root / relative).read_bytes()
            != (checkpoint / relative).read_bytes()
        }
        assert changed == CHANGED_GUIDANCE_PATHS


def test_generic_and_specific_sets_share_the_same_general_wording() -> None:
    """DOCGUIDE-007: adding specific rules does not change general wording."""

    specific_rules = (SOURCES_ROOT / "specific-rules.md").read_text().rstrip()
    for family in FAMILIES:
        generic_root = SETS_ROOT / f"{family}-generic"
        specific_root = SETS_ROOT / f"{family}-specific"

        for relative in CURRENT_GUIDANCE_PATHS:
            if relative == "docs/development/documentation.md":
                continue
            assert (generic_root / relative).read_bytes() == (
                specific_root / relative
            ).read_bytes()

        generic_guide = (generic_root / "docs/development/documentation.md").read_text()
        specific_guide = (
            specific_root / "docs/development/documentation.md"
        ).read_text()
        assert "### Apply the rules by context" not in generic_guide
        assert specific_rules in specific_guide
        assert (
            specific_guide.replace(
                f"\n\n{specific_rules}\n\n",
                "\n\n",
            )
            == generic_guide
        )


def test_wording_families_share_examples_without_held_out_terms() -> None:
    """DOCGUIDE-008: examples stay constant and separate from scenario wording."""

    guide_examples: tuple[str, ...] | None = None
    root_examples: str | None = None

    for family in FAMILIES:
        guide_source = (SOURCES_ROOT / family / "documentation-section.md").read_text()
        family_examples = _examples(guide_source)
        assert len(family_examples) == 5
        if guide_examples is None:
            guide_examples = family_examples
        assert family_examples == guide_examples

        agents_source = (SOURCES_ROOT / family / "agents-section.md").read_text()
        assert agents_source.count("Examples:") == 1
        family_root_examples = re.sub(
            r"\s+",
            " ",
            agents_source.split("Examples:", 1)[1].strip(),
        )
        if root_examples is None:
            root_examples = family_root_examples
        assert family_root_examples == root_examples

    assert guide_examples is not None
    assert root_examples is not None
    rendered = ("\n".join(guide_examples) + "\n" + root_examples).lower()
    assert all(term not in rendered for term in HELD_OUT_TERMS)


def test_contextual_candidate_defines_context_before_applying_it() -> None:
    """DOCGUIDE-007: the concise context term is defined before its rules."""

    guide = (SOURCES_ROOT / "contextual/documentation-section.md").read_text()
    agents = (SOURCES_ROOT / "contextual/agents-section.md").read_text()
    normalized_guide = re.sub(r"\s+", " ", guide)
    normalized_agents = re.sub(r"\s+", " ", agents)

    assert guide.index("Context means") < guide.index("1. Use source context")
    assert "provide source context" in normalized_guide
    assert "its audience" in normalized_guide
    assert "their own context" in normalized_guide
    assert agents.startswith("Context means")
    assert "source context" in agents
    assert re.search(
        r"choose (?:terms|terminology) and organization for "
        r"(?:the current|that) context",
        normalized_agents,
    )
    assert "audience" in agents
