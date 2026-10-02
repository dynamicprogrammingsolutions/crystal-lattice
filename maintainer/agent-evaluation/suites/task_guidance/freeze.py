"""Freeze the consolidated dataset of one completed evaluation.

The CLI is generic: it takes the artifact root, the run labels to freeze
(latest label per cell by default), the dataset identity, and the guidance
bundle whose compilation hash is recorded as provenance. Stage-specific
run-selection arguments are gone — one run label covers every stage of one
invocation.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = PACKAGE_ROOT.parents[1]
for import_root in (REPOSITORY_ROOT, PACKAGE_ROOT / "src"):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from maintainer.guidance import compile_guidance  # noqa: E402

from .configuration import (  # noqa: E402
    DEFAULT_ARTIFACT_ROOT,
    GUIDANCE_TARGET,
    REPOSITORY_ROOT,
    selected_bundle,
)
from .results import consolidate_results, render_summary  # noqa: E402


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, default=DEFAULT_ARTIFACT_ROOT)
    parser.add_argument(
        "--labels",
        default=None,
        help=(
            "comma-separated run labels to freeze; every record of the"
            " listed labels becomes one sample of its cell. Default:"
            " the latest label of each cell"
        ),
    )
    parser.add_argument("--dataset-id", default="task-guidance-b0-20260919")
    parser.add_argument("--label", default="current-guidance baseline")
    parser.add_argument(
        "--bundle",
        type=Path,
        default=None,
        help="guidance bundle to record as provenance; defaults to the selected bundle",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "consolidated dataset JSON; defaults to"
            " <artifact-root>/consolidated/<dataset-id>.json"
        ),
    )
    args = parser.parse_args(argv)
    artifact_root = args.artifact_root.expanduser().resolve()
    labels = (
        [item.strip() for item in args.labels.split(",") if item.strip()]
        if args.labels
        else None
    )
    bundle = (
        args.bundle.expanduser().resolve()
        if args.bundle is not None
        else selected_bundle()
    )
    compilation = compile_guidance(
        bundle=bundle,
        target=GUIDANCE_TARGET,
        repository_root=REPOSITORY_ROOT,
    )
    bundle_provenance = {
        "path": str(bundle),
        "compilation_sha256": str(compilation.lock["compilation_sha256"]),
    }
    output = (
        args.output.expanduser().resolve()
        if args.output is not None
        else artifact_root / "consolidated" / f"{args.dataset_id}.json"
    )
    value = consolidate_results(
        artifact_root,
        labels=labels,
        dataset_id=args.dataset_id,
        label=args.label,
        bundle=bundle_provenance,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    output.with_suffix(".md").write_text(
        render_summary(value),
        encoding="utf-8",
    )
    print(f"froze {args.dataset_id} -> {output}")
    print(value["selection"] or "(no cells selected)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
