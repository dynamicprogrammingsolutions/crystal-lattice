from __future__ import annotations

import argparse
import json
from pathlib import Path

from .configuration import DEFAULT_ARTIFACT_ROOT
from .results import consolidate_results, render_summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", type=Path, default=DEFAULT_ARTIFACT_ROOT)
    parser.add_argument("--producer-attempt", default="default")
    parser.add_argument("--handoff-attempt", default="default")
    parser.add_argument("--semantic-attempt", default="default")
    parser.add_argument("--dataset-id", default="task-guidance-b0-20260919")
    parser.add_argument("--label", default="current-guidance baseline")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "consolidated dataset JSON; defaults to"
            " <artifact-root>/consolidated/<dataset-id>.json"
        ),
    )
    args = parser.parse_args()
    artifact_root = args.artifact_root.expanduser().resolve()
    output = (
        args.output.expanduser().resolve()
        if args.output is not None
        else artifact_root / "consolidated" / f"{args.dataset_id}.json"
    )
    value = consolidate_results(
        artifact_root,
        producer_attempt=args.producer_attempt,
        handoff_attempt=args.handoff_attempt,
        semantic_attempt=args.semantic_attempt,
        dataset_id=args.dataset_id,
        label=args.label,
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
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
