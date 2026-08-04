from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional


REPO_ROOT = Path(__file__).resolve().parents[3]
BENCHMARK_DIR = Path(__file__).resolve().parent
if str(BENCHMARK_DIR) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_DIR))

from openai_responses_tier_matrix_store import (  # noqa: E402
    DEFAULT_RESULTS_JSON_PATH,
    aggregate_records,
    load_results_store,
    render_summary_lines,
)


def _parse_csv(raw: Optional[str]) -> Optional[set[str]]:
    if not isinstance(raw, str) or not raw.strip():
        return None
    return {item.strip() for item in raw.split(",") if item.strip()}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize cumulative OpenAI Responses tier benchmark runs.")
    parser.add_argument(
        "--results-json",
        default=str(DEFAULT_RESULTS_JSON_PATH),
        help="Path to the cumulative JSON results store.",
    )
    parser.add_argument("--profiles", help="Comma-separated profile filter.")
    parser.add_argument("--models", help="Comma-separated model filter.")
    parser.add_argument("--case-names", help="Comma-separated case-name filter.")
    parser.add_argument("--output", help="Optional path to save the summary text.")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    results_json_path = Path(args.results_json).expanduser()
    payload = load_results_store(results_json_path)
    runs = payload.get("runs") or []
    summaries = aggregate_records(
        runs,
        profiles=_parse_csv(args.profiles),
        models=_parse_csv(args.models),
        case_names=_parse_csv(args.case_names),
    )
    lines = list(render_summary_lines(summaries))
    text = "\n".join(lines)
    if args.output:
        output_path = Path(args.output).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())