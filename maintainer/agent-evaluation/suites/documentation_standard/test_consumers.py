from __future__ import annotations

from collections.abc import Iterator

import pytest

from .support import (
    AssertionFinding,
    DocumentationEvaluationHarness,
    assert_findings,
    basic_run_findings,
    enforce_real_model_gate,
    file_text,
    record_review,
    selected_profile,
)


pytestmark = pytest.mark.agent_eval


@pytest.fixture(scope="session")
def harness() -> Iterator[DocumentationEvaluationHarness]:
    profile = selected_profile()
    enforce_real_model_gate(profile)
    value = DocumentationEvaluationHarness(profile)
    yield value
    value.close()


def _seed_01(harness: DocumentationEvaluationHarness):
    seed = harness.seed(
        seed_id="seed-01-js-single-file-tool-documentation",
        spec_file="seed-01-js-single-file-tool-documentation.md",
        fixture_id="js-single-file-tool",
    )
    seed.raise_for_error()
    assert seed.value.completed
    assert not seed.changed_paths
    return seed


@pytest.mark.requirements("DOCGEN-001")
def test_01_small_package_documentation(
    harness: DocumentationEvaluationHarness,
) -> None:
    run = harness.branch(
        test_id="01-small-package-documentation",
        spec_file="01-small-package-documentation.md",
        parent=_seed_01(harness),
        fixture_id="js-single-file-tool",
    )
    readme = file_text(run, "plugins/js-single-file-tool/README.md")
    lower = readme.lower()
    findings = basic_run_findings(run) + (
        AssertionFinding(
            "README-only mutation",
            run.changed_paths == ("plugins/js-single-file-tool/README.md",),
            repr(run.changed_paths),
        ),
        AssertionFinding("upper documented", "upper" in lower, "upper is present"),
        AssertionFinding(
            "configuration documented",
            "node:" in readme or "node_tool" in readme,
            "expected node loading form",
        ),
        AssertionFinding(
            "first use documented",
            "hello" in lower and "hello".upper() in readme,
            "expected input/output example",
        ),
        AssertionFinding(
            "verification documented",
            "verif" in lower or "confirm" in lower or "expected" in lower,
            "expected practical verification language",
        ),
    )
    record_review(
        run,
        spec_file="01-small-package-documentation.md",
        findings=findings,
    )
    assert_findings(findings)


@pytest.mark.requirements("DOCGEN-001")
def test_02_generated_output_correction(
    harness: DocumentationEvaluationHarness,
) -> None:
    run = harness.branch(
        test_id="02-generated-output-correction",
        spec_file="02-generated-output-correction.md",
        parent=_seed_01(harness),
        fixture_id="js-single-file-tool",
        branch_variant="generated-typo",
    )
    readme = file_text(run, "plugins/js-single-file-tool/README.md")
    prepared = file_text(
        run,
        "docs_site/prepared/plugins/js-single-file-tool/index.md",
    )
    findings = basic_run_findings(run) + (
        AssertionFinding(
            "authored source corrected",
            "pip install example-package" in readme
            and "pip instal example-package" not in readme,
            "README should contain corrected command",
        ),
        AssertionFinding(
            "generated output not directly edited",
            "docs_site/prepared/plugins/js-single-file-tool/index.md"
            not in run.changed_paths,
            repr(run.changed_paths),
        ),
        AssertionFinding(
            "prepared fixture remains generated",
            "generated from plugins/js-single-file-tool/README.md" in prepared,
            "generated source marker retained",
        ),
    )
    record_review(
        run,
        spec_file="02-generated-output-correction.md",
        findings=findings,
    )
    assert_findings(findings)