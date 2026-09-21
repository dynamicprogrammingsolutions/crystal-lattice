from __future__ import annotations

import argparse
import json
from pathlib import Path

from .results import consolidate_results, render_summary


SUITE_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = SUITE_ROOT.parents[3]
DEFAULT_ARTIFACT_ROOT = (
    REPOSITORY_ROOT / "tmp" / "agent-evaluation" / "task-guidance"
)
DEFAULT_RESULTS = (
    SUITE_ROOT / "fixtures" / "results" / "task_guidance_b0_results.json"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", type=Path, default=DEFAULT_ARTIFACT_ROOT)
    parser.add_argument("--producer-attempt", default="default")
    parser.add_argument("--handoff-attempt", default="default")
    parser.add_argument("--semantic-attempt", default="default")
    parser.add_argument("--dataset-id", default="task-guidance-b0-20260919")
    parser.add_argument("--label", default="current-guidance baseline")
    parser.add_argument("--output", type=Path, default=DEFAULT_RESULTS)
    args = parser.parse_args()
    value = consolidate_results(
        args.artifact_root.expanduser().resolve(),
        producer_attempt=args.producer_attempt,
        handoff_attempt=args.handoff_attempt,
        semantic_attempt=args.semantic_attempt,
        dataset_id=args.dataset_id,
        label=args.label,
    )
    output = args.output.expanduser().resolve()
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