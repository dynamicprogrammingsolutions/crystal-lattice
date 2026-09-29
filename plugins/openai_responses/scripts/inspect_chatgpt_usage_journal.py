#!/usr/bin/env python
"""Inspect the ChatGPT usage journal by date.

Reads the append-only ChatGPT usage journal
(``auth/chatgpt-usage-journal.ndjson`` by default) and prints request-usage
totals, usage-percent history, and the left percentage / next reset time at a
specific point in time. Can also export the journal to CSV for date-based
inspection in other tools.

Examples:

    python plugins/openai_responses/scripts/inspect_chatgpt_usage_journal.py
    python plugins/openai_responses/scripts/inspect_chatgpt_usage_journal.py \
        --journal ~/.config/ai-agent/auth/chatgpt-usage-journal.ndjson
    python plugins/openai_responses/scripts/inspect_chatgpt_usage_journal.py \
        --from 2026-09-01 --to "2026-09-19 14:30"
    python plugins/openai_responses/scripts/inspect_chatgpt_usage_journal.py \
        --at "2026-09-19 14:30"
    python plugins/openai_responses/scripts/inspect_chatgpt_usage_journal.py \
        --csv out/usage.csv
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from openai_responses_plugins.chatgpt_usage_journal import (  # noqa: E402
    export_journal_csv,
    iter_journal_records,
    latest_rate_limits,
    percent_history,
    resolve_usage_journal_path,
    totals_since_last_reset,
)


def _parse_date_arg(raw: str | None) -> datetime | None:
    if raw is None or not raw.strip():
        return None
    text = raw.strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            parsed = datetime.strptime(text, fmt)
        except ValueError:
            continue
        return parsed.astimezone()
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        raise SystemExit(f"Could not parse date: {raw!r}")
    if parsed.tzinfo is None:
        return parsed.astimezone()
    return parsed


def _format_reset_time(resets_at: int | None) -> str:
    if not isinstance(resets_at, int):
        return "unknown"
    try:
        reset_dt = datetime.fromtimestamp(resets_at)
    except Exception:
        return "unknown"
    return reset_dt.strftime("%Y-%m-%d %H:%M %Z")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect the ChatGPT usage journal by date."
    )
    parser.add_argument(
        "--journal",
        type=Path,
        default=None,
        help=(
            "Path to the journal file. Defaults to the standard location "
            "resolved from CONFIG_DIR or the current directory."
        ),
    )
    parser.add_argument(
        "--from",
        dest="from_dt",
        type=str,
        default=None,
        help="Inclusive start date or date+time (server timezone), e.g. 2026-09-19 or 2026-09-19 14:30.",
    )
    parser.add_argument(
        "--to",
        dest="to_dt",
        type=str,
        default=None,
        help="Inclusive end date or date+time (server timezone).",
    )
    parser.add_argument(
        "--at",
        dest="at_dt",
        type=str,
        default=None,
        help=(
            "Show the left percentage and next reset time at a specific "
            "point in time instead of the latest snapshot."
        ),
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=None,
        help="Export the (filtered) journal to a CSV file.",
    )
    args = parser.parse_args()

    config: dict = {}
    journal_path = args.journal or resolve_usage_journal_path(config)
    if not journal_path.exists():
        print(f"No usage journal found at {journal_path}")
        return 1

    from_dt = _parse_date_arg(args.from_dt)
    to_dt = _parse_date_arg(args.to_dt)
    at_dt = _parse_date_arg(args.at_dt)

    if args.csv is not None:
        rows = export_journal_csv(journal_path, args.csv, from_dt=from_dt, to_dt=to_dt)
        print(f"Wrote {rows} rows to {args.csv}")

    records = list(iter_journal_records(journal_path, from_dt=from_dt, to_dt=to_dt))
    snapshot_count = sum(1 for r in records if r.get("type") == "rate_limit_snapshot")
    reset_count = sum(1 for r in records if r.get("type") == "usage_reset")
    print(f"Journal: {journal_path}")
    if from_dt is not None or to_dt is not None:
        print(
            "Range: "
            f"{from_dt.strftime('%Y-%m-%d %H:%M') if from_dt else 'start'} -> "
            f"{to_dt.strftime('%Y-%m-%d %H:%M') if to_dt else 'now'}"
        )
    print(
        f"Records in scope: {len(records)} "
        f"({snapshot_count} snapshots, {reset_count} resets)"
    )
    print()

    totals = totals_since_last_reset(journal_path, from_dt=from_dt, to_dt=to_dt)
    print("Estimated usage since last reset marker:")
    if totals.get("reset_at"):
        print(f"  Reset marker at: {totals['reset_at']}")
    print(f"  Requests:          {totals['request_count']:,}")
    print(f"  Input tokens:       {totals['input_tokens']:,}")
    print(f"  Cached tokens:      {totals['cached_tokens']:,}")
    print(f"  Cache write tokens: {totals['cache_write_tokens']:,}")
    print(f"  Output tokens:      {totals['output_tokens']:,}")
    print(f"  Reasoning tokens:   {totals['reasoning_tokens']:,}")
    print(f"  Estimated cost:     ${totals['estimated_cost']:.6f}")
    print()

    snapshot = latest_rate_limits(journal_path, at_dt=at_dt if at_dt is not None else to_dt)
    if snapshot is None:
        print("No rate-limit snapshots recorded.")
    else:
        if at_dt is not None:
            print(f"Usage limits at {at_dt.strftime('%Y-%m-%d %H:%M')}:")
        else:
            print("Latest usage limits:")
        for item in snapshot.get("snapshots") or []:
            limit_id = item.get("limit_id") or "codex"
            for window_kind in ("primary", "secondary"):
                window = item.get(window_kind)
                if not isinstance(window, dict):
                    continue
                used = window.get("used_percent")
                if isinstance(used, (int, float)):
                    remaining = 100.0 - float(used)
                    print(
                        f"  {limit_id} {window_kind}: "
                        f"{remaining:.0f}% left (used {float(used):.0f}%), "
                        f"resets {_format_reset_time(window.get('resets_at'))}"
                    )
                else:
                    print(f"  {limit_id} {window_kind}: usage available")
        print()

    history = percent_history(journal_path, from_dt=from_dt, to_dt=to_dt)
    if history:
        print("Usage percent history:")
        for entry in history:
            print(
                f"  {entry.get('timestamp')} {entry.get('limit_id')} "
                f"{entry.get('window')}: {entry.get('used_percent'):.0f}% used, "
                f"resets {_format_reset_time(entry.get('resets_at'))}"
            )
    else:
        print("No usage-percent history in scope.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
