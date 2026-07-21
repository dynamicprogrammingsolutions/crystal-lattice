#!/usr/bin/env python3
"""Refresh the Crystal Lattice progress snapshot sheet from YouTrack."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import requests
from google.auth.transport.requests import Request
from google.oauth2 import service_account


DEFAULT_CONFIG = Path(__file__).with_name("progress_snapshot.json")
ENV_FILE = Path(".env")

TASKS_SHEET = "Tasks"
SUMMARY_SHEET = "Summary"
TASK_COLUMNS = [
    "Snapshot Key",
    "Snapshot Date",
    "Period Start",
    "Period End",
    "Issue ID",
    "Sprint",
    "State at Snapshot",
    "Summary",
    "Assignee",
    "Story Points",
    "Manual Completion Date",
    "Derived Completion Date",
    "Effective Completion Date",
    "Ticket Updated At",
    "Last Commit Datetime",
    "Commit Count",
    "Pairing Note",
    "Last In Progress Date",
    "State at Period End",
    "Started in Period Date",
    "Started in Period Source",
    "Completed in Period Date",
]
TASK_RANGE = f"{TASKS_SHEET}!A:V"
SUMMARY_RANGE = f"{SUMMARY_SHEET}!A:G"
REVIEW_FIELDS = [
    "Issue ID",
    "Sprint",
    "State at Snapshot",
    "Summary",
    "Assignee",
    "Story Points",
    "Manual Completion Date",
    "Derived Completion Date",
    "Effective Completion Date",
    "State at Period End",
    "Started in Period Date",
    "Started in Period Source",
    "Completed in Period Date",
    "Ticket Updated At",
]
PRESERVED_FIELDS = [
    "Manual Completion Date",
    "Last Commit Datetime",
    "Commit Count",
    "Pairing Note",
]
LEGACY_COLUMN_MAP = {
    "Completion Date": "Manual Completion Date",
    "State": "State at Snapshot",
}


@dataclass(frozen=True)
class Config:
    sheet_id: str
    youtrack_base_url: str
    project: str
    period_start: str
    period_end: str
    snapshot_date: str
    watched_sprints: list[str]
    states: list[str]
    completed_states: list[str]
    exclude_types: set[str]
    exclude_grouping: set[str]
    sprint_order: list[str]
    state_order: list[str]
    assignee_order: list[str]
    summary_assignees: list[str]
    timezone: ZoneInfo


@dataclass(frozen=True)
class Snapshot:
    period_start: str
    period_end: str
    snapshot_date: str

    @property
    def key(self) -> str:
        return f"{self.period_start}..{self.period_end}@{self.snapshot_date}"


@dataclass(frozen=True)
class Issue:
    issue_id: str
    summary: str
    state: str
    sprints: list[str]
    sprint: str
    issue_type: str
    grouping: list[str]
    assignee: str
    story_points: str
    created_date: str
    updated_at: str


@dataclass(frozen=True)
class StateHistory:
    state_at_snapshot: str
    first_completion_date: str
    last_in_progress_date: str
    state_at_period_end: str
    started_in_period_date: str
    started_in_period_source: str
    completed_in_period_date: str


def main() -> int:
    args = parse_args()
    load_dotenv(ENV_FILE)
    config = with_sheet_id(load_config(args.config), args.sheet_id)
    snapshot_date = (
        args.snapshot_date
        or config.snapshot_date
        or date.today().isoformat()
    )
    snapshot = Snapshot(
        period_start=args.period_start or config.period_start,
        period_end=args.period_end or config.period_end,
        snapshot_date=snapshot_date,
    )

    warnings = build_warnings(snapshot)
    youtrack = YouTrackClient(config.youtrack_base_url, os.environ["YOUTRACK_TOKEN"])
    sheets = SheetsClient(config.sheet_id)

    existing_rows = read_task_rows(sheets)
    existing_summary = sheets.get_values(
        SUMMARY_RANGE,
        value_render_option="FORMULA",
    )
    issues = fetch_filtered_issues(youtrack, config)
    expected_rows = build_expected_rows(
        youtrack=youtrack,
        config=config,
        snapshot=snapshot,
        issues=issues,
        existing_rows=existing_rows,
    )
    diff = diff_snapshot_rows(
        existing_rows,
        expected_rows,
        snapshot,
        config,
        replace_same_period=args.replace_same_period,
    )

    print_plan(
        args.mode,
        config,
        snapshot,
        warnings,
        diff,
        args.replace_same_period,
        summary_exists=summary_contains_snapshot(existing_summary, snapshot.key),
    )
    if args.mode == "write":
        write_snapshot(
            sheets,
            config,
            snapshot,
            existing_rows,
            expected_rows,
            existing_summary,
            replace_same_period=args.replace_same_period,
        )
        print("\nWrote snapshot rows and summary blocks.")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Refresh the Crystal Lattice progress snapshot sheet."
    )
    parser.add_argument(
        "mode",
        choices=["show", "write"],
        help="show prints the planned diff; write applies it to Google Sheets.",
    )
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG),
        help=f"Config file path. Defaults to {DEFAULT_CONFIG}.",
    )
    parser.add_argument(
        "--snapshot-date",
        help="Override snapshot date from config. Defaults to config value or system date.",
    )
    parser.add_argument(
        "--period-start",
        help="Override the configured reporting period start date (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--period-end",
        help="Override the configured reporting period end date (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--sheet-id",
        help="Override sheet ID from config. Useful for testing against a copy.",
    )
    parser.add_argument(
        "--replace-same-period",
        action="store_true",
        help="Replace all existing Tasks/Summary snapshot blocks with the same period, even if their snapshot date differs.",
    )
    return parser.parse_args()


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def load_config(path_arg: str) -> Config:
    path = Path(path_arg)
    data = json.loads(path.read_text())
    snapshot = data["snapshot"]
    ordering = data.get("ordering", {})
    exclude = data.get("exclude", {})
    return Config(
        sheet_id=data["sheet_id"],
        youtrack_base_url=data["youtrack_base_url"].rstrip("/"),
        project=data["project"],
        period_start=snapshot["period_start"],
        period_end=snapshot["period_end"],
        snapshot_date=snapshot.get("snapshot_date", ""),
        watched_sprints=list(data["watched_sprints"]),
        states=list(data["states"]),
        completed_states=list(data.get("completed_states", ["Staging", "Done"])),
        exclude_types=set(exclude.get("type", [])),
        exclude_grouping=set(exclude.get("grouping", [])),
        sprint_order=list(ordering.get("sprint", data["watched_sprints"])),
        state_order=list(ordering.get("state", data["states"])),
        assignee_order=list(ordering.get("assignee", [])),
        summary_assignees=list(data.get("summary_assignees", [])),
        timezone=ZoneInfo(data.get("timezone", "UTC")),
    )


def with_sheet_id(config: Config, sheet_id: str | None) -> Config:
    if not sheet_id:
        return config
    return Config(
        sheet_id=sheet_id,
        youtrack_base_url=config.youtrack_base_url,
        project=config.project,
        period_start=config.period_start,
        period_end=config.period_end,
        snapshot_date=config.snapshot_date,
        watched_sprints=config.watched_sprints,
        states=config.states,
        completed_states=config.completed_states,
        exclude_types=config.exclude_types,
        exclude_grouping=config.exclude_grouping,
        sprint_order=config.sprint_order,
        state_order=config.state_order,
        assignee_order=config.assignee_order,
        summary_assignees=config.summary_assignees,
        timezone=config.timezone,
    )


def build_warnings(snapshot: Snapshot) -> list[str]:
    warnings: list[str] = []
    snapshot_date = date.fromisoformat(snapshot.snapshot_date)
    period_start = date.fromisoformat(snapshot.period_start)
    period_end = date.fromisoformat(snapshot.period_end)
    if snapshot_date < period_start or snapshot_date > period_end:
        warnings.append(
            "snapshot date "
            f"{snapshot.snapshot_date} is outside period "
            f"{snapshot.period_start}..{snapshot.period_end}; it remains an "
            "audit/collection timestamp and does not alter period-end metrics."
        )
    system_date = date.today().isoformat()
    if snapshot.snapshot_date != system_date:
        warnings.append(
            f"configured snapshot date {snapshot.snapshot_date} differs from "
            f"system date {system_date}; using configured snapshot date."
        )
    return warnings


class YouTrackClient:
    def __init__(self, base_url: str, token: str) -> None:
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            }
        )

    def search_issues(self, query: str) -> list[dict[str, Any]]:
        fields = (
            "idReadable,summary,created,updated,"
            "customFields(name,value(name,login,presentation))"
        )
        issues: list[dict[str, Any]] = []
        skip = 0
        top = 100
        while True:
            response = self.session.get(
                f"{self.base_url}/api/issues",
                params={
                    "query": query,
                    "fields": fields,
                    "$top": str(top),
                    "$skip": str(skip),
                },
                timeout=30,
            )
            response.raise_for_status()
            page = response.json()
            issues.extend(page)
            if len(page) < top:
                break
            skip += top
        return issues

    def issue_activities(self, issue_id: str) -> list[dict[str, Any]]:
        response = self.session.get(
            f"{self.base_url}/api/issues/{issue_id}/activities",
            params={
                "categories": "CustomFieldCategory",
                "fields": "timestamp,field(name),added(name,presentation),removed(name,presentation)",
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()


class SheetsClient:
    def __init__(self, sheet_id: str) -> None:
        self.sheet_id = sheet_id
        self.session = requests.Session()
        creds = self._credentials()
        creds.refresh(Request())
        self.session.headers.update(
            {
                "Authorization": f"Bearer {creds.token}",
                "Accept": "application/json",
            }
        )

    def _credentials(self) -> service_account.Credentials:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if credentials_path:
            return service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=scopes,
            )
        raise RuntimeError(
            "GOOGLE_APPLICATION_CREDENTIALS is required for Sheets writes/reads."
        )

    def get_values(
        self,
        range_name: str,
        *,
        value_render_option: str = "FORMATTED_VALUE",
    ) -> list[list[Any]]:
        response = self.session.get(
            f"https://sheets.googleapis.com/v4/spreadsheets/{self.sheet_id}/values/{range_name}",
            params={"valueRenderOption": value_render_option},
            timeout=30,
        )
        response.raise_for_status()
        return response.json().get("values", [])

    def update_values(self, range_name: str, values: list[list[Any]]) -> None:
        response = self.session.put(
            f"https://sheets.googleapis.com/v4/spreadsheets/{self.sheet_id}/values/{range_name}",
            params={"valueInputOption": "USER_ENTERED"},
            json={"majorDimension": "ROWS", "values": values},
            timeout=30,
        )
        response.raise_for_status()

    def clear_values(self, range_name: str) -> None:
        response = self.session.post(
            f"https://sheets.googleapis.com/v4/spreadsheets/{self.sheet_id}/values/{range_name}:clear",
            json={},
            timeout=30,
        )
        response.raise_for_status()


def fetch_filtered_issues(youtrack: YouTrackClient, config: Config) -> list[Issue]:
    by_id: dict[str, Issue] = {}
    state_clause = ", ".join(format_query_value(state) for state in config.states)
    for sprint in config.watched_sprints:
        query = (
            f"project: {config.project} "
            f"State: {state_clause} "
            f"Sprints: {format_query_value(sprint)}"
        )
        for raw_issue in youtrack.search_issues(query):
            issue = parse_issue(raw_issue, config)
            if issue and include_issue(issue, config):
                by_id[issue.issue_id] = issue
    return sorted(by_id.values(), key=lambda issue: issue_sort_key(issue, config))


def format_query_value(value: str) -> str:
    if " " in value:
        return "{" + value + "}"
    return value


def parse_issue(raw_issue: dict[str, Any], config: Config) -> Issue | None:
    custom_fields = {
        field.get("name"): field.get("value")
        for field in raw_issue.get("customFields", [])
    }
    state = name_value(custom_fields.get("State"))
    sprints = list_values(custom_fields.get("Sprints"))
    sprint = first_ordered_overlap(sprints, config.watched_sprints)
    if not sprint:
        return None
    return Issue(
        issue_id=raw_issue["idReadable"],
        summary=raw_issue.get("summary", ""),
        state=state,
        sprints=sprints,
        sprint=sprint,
        issue_type=name_value(custom_fields.get("Type")),
        grouping=list_values(custom_fields.get("Grouping")),
        assignee=assignee_value(custom_fields.get("Assignee")),
        story_points=number_value(custom_fields.get("Story points")),
        created_date=date_value(raw_issue.get("created"), config.timezone),
        updated_at=datetime_value(raw_issue.get("updated"), config.timezone),
    )


def include_issue(issue: Issue, config: Config) -> bool:
    if issue.state not in config.states:
        return False
    if issue.issue_type in config.exclude_types:
        return False
    if config.exclude_grouping.intersection(issue.grouping):
        return False
    return bool(set(issue.sprints).intersection(config.watched_sprints))


def name_value(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("name") or value.get("presentation") or "")
    if value is None:
        return ""
    return str(value)


def list_values(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [name_value(item) for item in value if name_value(item)]
    single = name_value(value)
    return [single] if single else []


def assignee_value(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("login") or value.get("name") or "Unassigned")
    return "Unassigned"


def number_value(value: Any) -> str:
    if value is None:
        return "0"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if number.is_integer():
        return str(int(number))
    return str(number)


def datetime_value(timestamp_ms: Any, timezone: ZoneInfo) -> str:
    if not timestamp_ms:
        return ""
    timestamp = int(timestamp_ms) / 1000
    return datetime.fromtimestamp(timestamp, timezone).strftime("%Y-%m-%d %H:%M:%S")


def date_value(timestamp_ms: Any, timezone: ZoneInfo) -> str:
    if not timestamp_ms:
        return ""
    timestamp = int(timestamp_ms) / 1000
    return datetime.fromtimestamp(timestamp, timezone).date().isoformat()


def first_ordered_overlap(values: list[str], preferred_order: list[str]) -> str:
    for preferred in preferred_order:
        if preferred in values:
            return preferred
    return values[0] if values else ""


def read_task_rows(sheets: SheetsClient) -> list[dict[str, str]]:
    values = sheets.get_values(TASK_RANGE)
    if not values:
        return []
    headers = values[0]
    rows: list[dict[str, str]] = []
    for value_row in values[1:]:
        if not any(cell.strip() for cell in value_row):
            continue
        row = row_to_dict(headers, value_row)
        rows.append(normalize_existing_row(row))
    return rows


def row_to_dict(headers: list[str], values: list[str]) -> dict[str, str]:
    row: dict[str, str] = {}
    for index, header in enumerate(headers):
        if not header:
            continue
        row[header] = values[index] if index < len(values) else ""
    return row


def normalize_existing_row(row: dict[str, str]) -> dict[str, str]:
    normalized = {column: "" for column in TASK_COLUMNS}
    for column in TASK_COLUMNS:
        normalized[column] = row.get(column, "")
    for old_column, new_column in LEGACY_COLUMN_MAP.items():
        if not normalized.get(new_column) and row.get(old_column):
            normalized[new_column] = row[old_column]
    normalized["Ticket Updated At"] = normalize_datetime_text(
        normalized["Ticket Updated At"]
    )
    normalized["Effective Completion Date"] = (
        normalized["Manual Completion Date"]
        or normalized["Derived Completion Date"]
    )
    return normalized


def normalize_datetime_text(value: str) -> str:
    if not value:
        return ""
    for pattern in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(value, pattern).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    return value


def build_expected_rows(
    *,
    youtrack: YouTrackClient,
    config: Config,
    snapshot: Snapshot,
    issues: list[Issue],
    existing_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    existing_manuals = build_existing_manual_map(existing_rows, snapshot)
    rows: list[dict[str, str]] = []
    for issue in issues:
        if issue.created_date > snapshot.period_end:
            continue
        manual = existing_manuals.get(issue.issue_id, {}).get(
            "Manual Completion Date", ""
        )
        history = derive_state_history(
            youtrack.issue_activities(issue.issue_id),
            snapshot,
            config,
        )
        derived = history.first_completion_date
        effective = manual or derived
        completed_in_period = (
            manual
            if is_date_in_period(manual, snapshot)
            else history.completed_in_period_date
        )
        preserved = existing_manuals.get(issue.issue_id, {})
        rows.append(
            {
                "Snapshot Key": snapshot.key,
                "Snapshot Date": snapshot.snapshot_date,
                "Period Start": snapshot.period_start,
                "Period End": snapshot.period_end,
                "Issue ID": issue.issue_id,
                "Sprint": issue.sprint,
                "State at Snapshot": history.state_at_snapshot,
                "Summary": issue.summary,
                "Assignee": issue.assignee,
                "Story Points": issue.story_points,
                "Manual Completion Date": manual,
                "Derived Completion Date": derived,
                "Effective Completion Date": effective,
                "Ticket Updated At": issue.updated_at,
                "Last Commit Datetime": preserved.get("Last Commit Datetime", ""),
                "Commit Count": preserved.get("Commit Count", ""),
                "Pairing Note": preserved.get("Pairing Note", ""),
                "Last In Progress Date": history.last_in_progress_date,
                "State at Period End": history.state_at_period_end,
                "Started in Period Date": history.started_in_period_date,
                "Started in Period Source": history.started_in_period_source,
                "Completed in Period Date": completed_in_period,
            }
        )
        if not include_snapshot_row(rows[-1], config, snapshot):
            rows.pop()
    return sorted(rows, key=lambda row: row_sort_key(row, config))


def include_snapshot_row(
    row: dict[str, str], config: Config, snapshot: Snapshot
) -> bool:
    if row["State at Period End"] == "In Progress":
        return True
    if row["Started in Period Date"]:
        return True
    return bool(row["Completed in Period Date"])


def is_date_in_period(value: str, snapshot: Snapshot) -> bool:
    return (
        bool(value)
        and snapshot.period_start <= value <= snapshot.period_end
    )


def build_existing_manual_map(
    existing_rows: list[dict[str, str]], snapshot: Snapshot
) -> dict[str, dict[str, str]]:
    global_manual: dict[str, dict[str, str]] = {}
    same_period: dict[str, dict[str, str]] = {}
    exact: dict[str, dict[str, str]] = {}
    for row in existing_rows:
        issue_id = row["Issue ID"]
        if not issue_id:
            continue
        preserved = {field: row.get(field, "") for field in PRESERVED_FIELDS}
        if any(preserved.values()):
            global_manual[issue_id] = merge_preserved(
                global_manual.get(issue_id, {}), preserved
            )
        if row["Snapshot Key"] == snapshot.key:
            exact[issue_id] = merge_preserved(exact.get(issue_id, {}), preserved)
        elif (
            row["Period Start"] == snapshot.period_start
            and row["Period End"] == snapshot.period_end
        ):
            same_period[issue_id] = merge_preserved(
                same_period.get(issue_id, {}), preserved
            )
    return {**global_manual, **same_period, **exact}


def merge_preserved(
    base: dict[str, str] | None, update: dict[str, str]
) -> dict[str, str]:
    merged = {field: (base or {}).get(field, "") for field in PRESERVED_FIELDS}
    for field in PRESERVED_FIELDS:
        if update.get(field):
            merged[field] = update[field]
    return merged


def derive_state_history(
    activities: list[dict[str, Any]], snapshot: Snapshot, config: Config
) -> StateHistory:
    snapshot_end = exclusive_day_end(snapshot.snapshot_date, config.timezone)
    period_start, period_end = period_bounds(snapshot, config.timezone)
    active_states = {"In Progress", *config.completed_states}
    state_at_snapshot = ""
    state_at_period_end = ""
    first_completion_timestamp: int | None = None
    last_in_progress_timestamp: int | None = None
    first_started_in_period: tuple[int, str] | None = None
    first_completed_in_period: int | None = None
    prior_state = ""
    for activity in sorted(
        activities,
        key=lambda item: int(item.get("timestamp") or 0),
    ):
        field = activity.get("field") or {}
        if field.get("name") != "State":
            continue
        timestamp = activity.get("timestamp")
        if timestamp is None:
            continue
        timestamp = int(timestamp)
        added_values = list_values(activity.get("added"))
        if not added_values:
            continue
        added_state = added_values[-1]
        occurred_at = datetime.fromtimestamp(timestamp / 1000, config.timezone)
        if occurred_at < snapshot_end:
            state_at_snapshot = added_state
        if occurred_at < period_end:
            state_at_period_end = added_state
        if added_state in config.completed_states and occurred_at < snapshot_end:
            if (
                first_completion_timestamp is None
                or timestamp < first_completion_timestamp
            ):
                first_completion_timestamp = timestamp
        in_period = period_start <= occurred_at < period_end
        if (
            in_period
            and added_state in config.completed_states
            and prior_state not in config.completed_states
            and (
                first_completed_in_period is None
                or timestamp < first_completed_in_period
            )
        ):
            first_completed_in_period = timestamp
        if in_period and prior_state not in active_states:
            source = (
                "In Progress"
                if added_state == "In Progress"
                else f"Direct to {added_state}"
                if added_state in config.completed_states
                else ""
            )
            if source and first_started_in_period is None:
                first_started_in_period = (timestamp, source)
        if added_state == "In Progress" and occurred_at < snapshot_end and (
            last_in_progress_timestamp is None
            or timestamp > last_in_progress_timestamp
        ):
            last_in_progress_timestamp = timestamp
        prior_state = added_state
    return StateHistory(
        state_at_snapshot=state_at_snapshot,
        first_completion_date=(
            date_value(first_completion_timestamp, config.timezone)
            if first_completion_timestamp
            else ""
        ),
        last_in_progress_date=(
            date_value(last_in_progress_timestamp, config.timezone)
            if last_in_progress_timestamp
            else ""
        ),
        state_at_period_end=state_at_period_end,
        started_in_period_date=(
            date_value(first_started_in_period[0], config.timezone)
            if first_started_in_period
            else ""
        ),
        started_in_period_source=(
            first_started_in_period[1] if first_started_in_period else ""
        ),
        completed_in_period_date=(
            date_value(first_completed_in_period, config.timezone)
            if first_completed_in_period
            else ""
        ),
    )


def exclusive_day_end(value: str, timezone: ZoneInfo) -> datetime:
    return datetime.combine(
        date.fromisoformat(value) + timedelta(days=1),
        time.min,
        timezone,
    )


def period_bounds(snapshot: Snapshot, timezone: ZoneInfo) -> tuple[datetime, datetime]:
    return (
        datetime.combine(date.fromisoformat(snapshot.period_start), time.min, timezone),
        exclusive_day_end(snapshot.period_end, timezone),
    )


def diff_snapshot_rows(
    existing_rows: list[dict[str, str]],
    expected_rows: list[dict[str, str]],
    snapshot: Snapshot,
    config: Config,
    *,
    replace_same_period: bool = False,
) -> dict[str, Any]:
    existing = {
        row["Issue ID"]: row
        for row in existing_rows
        if is_target_snapshot_row(row, snapshot, replace_same_period)
        and row["Issue ID"]
    }
    expected = {row["Issue ID"]: row for row in expected_rows}
    adds = [
        row for row in expected_rows if row["Issue ID"] not in existing
    ]
    removed_rows = [
        existing[issue_id] for issue_id in set(existing) - set(expected)
    ]
    removed_rows = sorted(removed_rows, key=lambda row: row_sort_key(row, config))
    removes = [row for row in removed_rows if not is_protected_manual_row(row)]
    protected = [
        manual_exclusion_row(row, snapshot)
        for row in removed_rows
        if is_protected_manual_row(row)
    ]
    updates: list[tuple[dict[str, str], dict[str, str], dict[str, tuple[str, str]]]] = []
    for after in expected_rows:
        issue_id = after["Issue ID"]
        if issue_id not in existing:
            continue
        before = existing[issue_id]
        changed = {
            column: (before.get(column, ""), after.get(column, ""))
            for column in TASK_COLUMNS
            if before.get(column, "") != after.get(column, "")
        }
        if changed:
            updates.append((before, after, changed))
    return {
        "adds": adds,
        "updates": updates,
        "removes": removes,
        "protected": protected,
    }


def print_plan(
    mode: str,
    config: Config,
    snapshot: Snapshot,
    warnings: list[str],
    diff: dict[str, Any],
    replace_same_period: bool,
    summary_exists: bool,
) -> None:
    print(f"Mode: {mode}")
    print(f"Sheet: {config.sheet_id}")
    print(f"Snapshot: {snapshot.key}")
    print(f"Watched sprints: {', '.join(config.watched_sprints)}")
    if replace_same_period:
        print("Replace same period: enabled")
    print(
        "Summary: already exists; refreshing its formula blocks"
        if summary_exists
        else "Summary: will append new snapshot blocks"
    )
    for warning in warnings:
        print(f"WARNING: {warning}")
    print()
    print(f"Add: {len(diff['adds'])}")
    print(f"Update: {len(diff['updates'])}")
    print(f"Remove: {len(diff['removes'])}")
    print(f"Protected manual rows kept: {len(diff['protected'])}")
    print_rows("ADD", diff["adds"])
    print_updates(diff["updates"])
    print_rows("REMOVE", diff["removes"])
    print_rows(
        "PROTECTED MANUAL ROWS KEPT",
        diff["protected"],
        fields=["Snapshot Key", *REVIEW_FIELDS],
    )


def print_rows(
    title: str, rows: list[dict[str, str]], fields: list[str] | None = None
) -> None:
    if not rows:
        return
    fields = fields or REVIEW_FIELDS
    print(f"\n{title}")
    for row in rows:
        values = [row.get(field, "") for field in fields]
        print(" | ".join(values))


def print_updates(
    updates: list[tuple[dict[str, str], dict[str, str], dict[str, tuple[str, str]]]]
) -> None:
    if not updates:
        return
    print("\nUPDATE")
    for _before, after, changed in updates:
        print(f"{after['Issue ID']} | {after['Sprint']} | {after['Summary']}")
        for column, (old, new) in changed.items():
            if column == "Snapshot Key":
                continue
            print(f"  {column}: {old or '<empty>'} -> {new or '<empty>'}")


def write_snapshot(
    sheets: SheetsClient,
    config: Config,
    snapshot: Snapshot,
    existing_rows: list[dict[str, str]],
    expected_rows: list[dict[str, str]],
    existing_summary: list[list[str]],
    *,
    replace_same_period: bool = False,
) -> None:
    expected_issue_ids = {row["Issue ID"] for row in expected_rows}
    kept_rows: list[dict[str, str]] = []
    for row in existing_rows:
        normalized = normalize_existing_row(row)
        if not is_target_snapshot_row(normalized, snapshot, replace_same_period):
            kept_rows.append(normalized)
        elif (
            is_protected_manual_row(normalized)
            and normalized["Issue ID"] not in expected_issue_ids
        ):
            kept_rows.append(manual_exclusion_row(normalized, snapshot))
    ordered_rows = order_task_rows(
        [*kept_rows, *expected_rows],
        config,
        snapshot_key_order(existing_rows, snapshot.key),
    )
    task_values = [TASK_COLUMNS] + [
        [row.get(column, "") for column in TASK_COLUMNS]
        for row in ordered_rows
    ]
    old_task_row_count = len(existing_rows) + 1
    sheets.update_values(f"{TASKS_SHEET}!A1:V{len(task_values)}", task_values)
    clear_trailing_rows(sheets, TASKS_SHEET, len(task_values), old_task_row_count)

    summary_values = build_summary_values(existing_summary, config, snapshot)
    if summary_values != existing_summary:
        sheets.update_values(
            f"{SUMMARY_SHEET}!A1:G{len(summary_values)}", summary_values
        )


def is_protected_manual_row(row: dict[str, str]) -> bool:
    return any(row.get(field, "") for field in PRESERVED_FIELDS)


def manual_exclusion_row(row: dict[str, str], snapshot: Snapshot) -> dict[str, str]:
    excluded = normalize_existing_row(row)
    issue_id = excluded.get("Issue ID", "unknown")
    excluded["Snapshot Key"] = f"manual-excluded::{snapshot.key}::{issue_id}"
    excluded["Snapshot Date"] = "manual-excluded"
    excluded["Period Start"] = "manual-excluded"
    excluded["Period End"] = "manual-excluded"
    return excluded


def is_target_snapshot_row(
    row: dict[str, str], snapshot: Snapshot, replace_same_period: bool
) -> bool:
    if replace_same_period:
        return (
            row.get("Period Start", "") == snapshot.period_start
            and row.get("Period End", "") == snapshot.period_end
        )
    return row.get("Snapshot Key", "") == snapshot.key


def snapshot_key_order(
    existing_rows: list[dict[str, str]], current_snapshot_key: str
) -> list[str]:
    order: list[str] = []
    for row in existing_rows:
        key = row.get("Snapshot Key", "")
        if key and key not in order:
            order.append(key)
    if current_snapshot_key not in order:
        order.append(current_snapshot_key)
    return order


def order_task_rows(
    rows: list[dict[str, str]], config: Config, snapshot_order: list[str]
) -> list[dict[str, str]]:
    snapshot_index = {key: index for index, key in enumerate(snapshot_order)}
    return sorted(
        rows,
        key=lambda row: (
            snapshot_index.get(row.get("Snapshot Key", ""), len(snapshot_index)),
            row_sort_key(row, config),
        ),
    )


def clear_trailing_rows(
    sheets: SheetsClient,
    sheet_name: str,
    new_row_count: int,
    old_row_count: int,
    *,
    end_col: str = "V",
) -> None:
    if old_row_count > new_row_count:
        sheets.clear_values(
            f"{sheet_name}!A{new_row_count + 1}:{end_col}{old_row_count}"
        )


def build_summary_values(
    existing_summary: list[list[str]],
    config: Config,
    snapshot: Snapshot,
) -> list[list[str]]:
    existing_start = summary_snapshot_start(existing_summary, snapshot.key)
    if existing_start is not None:
        refreshed = build_summary_blocks(
            config,
            snapshot,
            first_row=existing_start + 1,
        )
        end = existing_start + len(refreshed)
        return existing_summary[:existing_start] + refreshed + existing_summary[end:]
    preserved = [list(row) for row in existing_summary]
    while preserved and not any(str(cell).strip() for cell in preserved[-1]):
        preserved.pop()
    first_new_row = len(preserved) + 1
    if preserved:
        preserved.append([])
        first_new_row += 1
    new_blocks = build_summary_blocks(
        config,
        snapshot,
        first_row=first_new_row,
    )
    return preserved + new_blocks


def summary_contains_snapshot(rows: list[list[str]], snapshot_key: str) -> bool:
    return summary_snapshot_start(rows, snapshot_key) is not None


def summary_snapshot_start(rows: list[list[str]], snapshot_key: str) -> int | None:
    for index, row in enumerate(rows):
        if row and str(row[0]) == snapshot_key:
            return index
    return None


def build_summary_blocks(
    config: Config, snapshot: Snapshot, *, first_row: int
) -> list[list[str]]:
    blocks: list[list[str]] = []
    current_row = first_row
    for sprint_index, sprint in enumerate(config.watched_sprints):
        metadata_row = current_row
        blocks.append(
            [
                snapshot.key,
                sprint,
                snapshot.snapshot_date,
                snapshot.period_start,
                snapshot.period_end,
                "",
                "",
            ]
        )
        blocks.append(
            [
                "Assignee",
                "Completed Tasks",
                "Completed Story Points",
                "In Progress at Period End Tasks",
                "In Progress at Period End Story Points",
                "Started Tasks",
                "Started Story Points",
            ]
        )
        current_row += 2
        for assignee in config.summary_assignees:
            row_number = current_row
            blocks.append(
                [
                    assignee,
                    completed_count_formula(metadata_row, row_number),
                    completed_points_formula(metadata_row, row_number),
                    in_progress_count_formula(metadata_row, row_number),
                    in_progress_points_formula(metadata_row, row_number),
                    started_count_formula(metadata_row, row_number),
                    started_points_formula(metadata_row, row_number),
                ]
            )
            current_row += 1
        if sprint_index < len(config.watched_sprints) - 1:
            blocks.append([])
            current_row += 1
    return blocks


def completed_count_formula(metadata_row: int, row_number: int) -> str:
    return (
        f'=COUNTIFS(Tasks!$A:$A,$A${metadata_row},Tasks!$F:$F,$B${metadata_row},'
        f'Tasks!$I:$I,$A${row_number},Tasks!$V:$V,">="&$D${metadata_row},'
        f'Tasks!$V:$V,"<"&($E${metadata_row}+1))'
    )


def completed_points_formula(metadata_row: int, row_number: int) -> str:
    return (
        f'=SUMIFS(Tasks!$J:$J,Tasks!$A:$A,$A${metadata_row},'
        f'Tasks!$F:$F,$B${metadata_row},Tasks!$I:$I,$A${row_number},'
        f'Tasks!$V:$V,">="&$D${metadata_row},Tasks!$V:$V,"<"&($E${metadata_row}+1))'
    )


def in_progress_count_formula(metadata_row: int, row_number: int) -> str:
    return (
        f'=COUNTIFS(Tasks!$A:$A,$A${metadata_row},Tasks!$F:$F,$B${metadata_row},'
        f'Tasks!$I:$I,$A${row_number},Tasks!$S:$S,"In Progress")'
    )


def in_progress_points_formula(metadata_row: int, row_number: int) -> str:
    return (
        f'=SUMIFS(Tasks!$J:$J,Tasks!$A:$A,$A${metadata_row},'
        f'Tasks!$F:$F,$B${metadata_row},Tasks!$I:$I,$A${row_number},'
        f'Tasks!$S:$S,"In Progress")'
    )


def started_count_formula(metadata_row: int, row_number: int) -> str:
    return (
        f'=COUNTIFS(Tasks!$A:$A,$A${metadata_row},Tasks!$F:$F,$B${metadata_row},'
        f'Tasks!$I:$I,$A${row_number},Tasks!$T:$T,">="&$D${metadata_row},'
        f'Tasks!$T:$T,"<"&($E${metadata_row}+1))'
    )


def started_points_formula(metadata_row: int, row_number: int) -> str:
    return (
        f'=SUMIFS(Tasks!$J:$J,Tasks!$A:$A,$A${metadata_row},'
        f'Tasks!$F:$F,$B${metadata_row},Tasks!$I:$I,$A${row_number},'
        f'Tasks!$T:$T,">="&$D${metadata_row},'
        f'Tasks!$T:$T,"<"&($E${metadata_row}+1))'
    )


def pad_row(row: list[str], width: int) -> list[str]:
    return row + [""] * max(0, width - len(row))


def issue_sort_key(issue: Issue, config: Config) -> tuple[int, int, int, int]:
    return (
        index_or_end(config.sprint_order, issue.sprint),
        index_or_end(config.state_order, issue.state),
        index_or_end(config.assignee_order, issue.assignee),
        issue_number(issue.issue_id),
    )


def row_sort_key(row: dict[str, str], config: Config) -> tuple[int, int, int, int]:
    return (
        index_or_end(config.sprint_order, row.get("Sprint", "")),
        index_or_end(config.state_order, row.get("State at Period End", "")),
        index_or_end(config.assignee_order, row.get("Assignee", "")),
        issue_number(row.get("Issue ID", "")),
    )


def index_or_end(values: list[str], value: str) -> int:
    try:
        return values.index(value)
    except ValueError:
        return len(values)


def issue_number(issue_id: str) -> int:
    try:
        return int(issue_id.split("-", 1)[1])
    except (IndexError, ValueError):
        return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyError as exc:
        print(f"Missing required environment variable or config key: {exc}", file=sys.stderr)
        raise SystemExit(2)