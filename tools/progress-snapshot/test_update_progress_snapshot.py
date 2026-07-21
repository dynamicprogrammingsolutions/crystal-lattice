from datetime import datetime, timezone

from update_progress_snapshot import (
    Snapshot,
    TASK_COLUMNS,
    build_summary_values,
    derive_state_history,
    diff_snapshot_rows,
    build_warnings,
    include_snapshot_row,
    normalize_existing_row,
    is_protected_manual_row,
    manual_exclusion_row,
    order_task_rows,
    snapshot_key_order,
)


def test_warns_when_snapshot_date_is_outside_period():
    snapshot = Snapshot(
        period_start="2026-05-20",
        period_end="2026-05-31",
        snapshot_date="2026-06-01",
    )

    assert build_warnings(snapshot)


def test_normalizes_legacy_completion_date_to_manual_completion_date():
    row = {
        "Snapshot Key": "2026-05-20..2026-06-02@2026-06-02",
        "Issue ID": "CL-1",
        "Completion Date": "2026-05-27",
    }

    normalized = normalize_existing_row(row)

    assert normalized["Manual Completion Date"] == "2026-05-27"
    assert normalized["Effective Completion Date"] == "2026-05-27"


def test_manual_completion_date_overrides_existing_effective_completion_date():
    row = {
        "Snapshot Key": "2026-05-20..2026-05-31@2026-06-01",
        "Issue ID": "CL-350",
        "Manual Completion Date": "2026-05-14",
        "Derived Completion Date": "2026-05-27",
        "Effective Completion Date": "2026-05-27",
    }

    normalized = normalize_existing_row(row)

    assert normalized["Effective Completion Date"] == "2026-05-14"


def test_normalizes_sheet_datetime_without_leading_zero_hour():
    row = {
        "Issue ID": "CL-304",
        "Ticket Updated At": "2026-06-02 7:30:37",
    }

    normalized = normalize_existing_row(row)

    assert normalized["Ticket Updated At"] == "2026-06-02 07:30:37"


def test_normalizes_legacy_state_to_state_at_snapshot():
    normalized = normalize_existing_row({"State": "In Progress"})

    assert normalized["State at Snapshot"] == "In Progress"


def test_period_reporting_columns_match_summary_formula_positions():
    assert TASK_COLUMNS[18] == "State at Period End"
    assert TASK_COLUMNS[19] == "Started in Period Date"
    assert TASK_COLUMNS[20] == "Started in Period Source"
    assert TASK_COLUMNS[21] == "Completed in Period Date"


def test_derives_period_end_state_and_respects_midnight_boundary():
    class Config:
        completed_states = ["Staging", "Done"]
        timezone = timezone.utc

    config = Config()

    def timestamp(year, month, day):
        return int(datetime(year, month, day, tzinfo=timezone.utc).timestamp() * 1000)

    snapshot = Snapshot("2026-06-01", "2026-06-14", "2026-06-28")
    activities = [
        {
            "timestamp": timestamp(2026, 6, 1),
            "field": {"name": "State"},
            "added": [{"name": "In Progress"}],
        },
        {
            "timestamp": timestamp(2026, 6, 13),
            "field": {"name": "State"},
            "added": [{"name": "Staging"}],
        },
        {
            "timestamp": timestamp(2026, 6, 15),
            "field": {"name": "State"},
            "added": [{"name": "In Progress"}],
        },
    ]

    history = derive_state_history(activities, snapshot, config)

    assert history.state_at_snapshot == "In Progress"
    assert history.first_completion_date == "2026-06-13"
    assert history.last_in_progress_date == "2026-06-15"
    assert history.state_at_period_end == "Staging"
    assert history.started_in_period_date == "2026-06-01"
    assert history.started_in_period_source == "In Progress"
    assert history.completed_in_period_date == "2026-06-13"


def test_counts_direct_completion_as_started_work_once():
    class Config:
        completed_states = ["Staging", "Done"]
        timezone = timezone.utc

    snapshot = Snapshot("2026-06-01", "2026-06-14", "2026-06-14")
    activities = [
        {
            "timestamp": int(
                datetime(2026, 6, 5, tzinfo=timezone.utc).timestamp() * 1000
            ),
            "field": {"name": "State"},
            "added": [{"name": "Done"}],
        }
    ]

    history = derive_state_history(activities, snapshot, Config())

    assert history.state_at_period_end == "Done"
    assert history.started_in_period_date == "2026-06-05"
    assert history.started_in_period_source == "Direct to Done"
    assert history.completed_in_period_date == "2026-06-05"


def test_does_not_count_staging_to_done_as_another_period_completion():
    class Config:
        completed_states = ["Staging", "Done"]
        timezone = timezone.utc

    snapshot = Snapshot("2026-06-01", "2026-06-14", "2026-06-14")
    activities = [
        {
            "timestamp": int(
                datetime(2026, 5, 31, tzinfo=timezone.utc).timestamp() * 1000
            ),
            "field": {"name": "State"},
            "added": [{"name": "Staging"}],
        },
        {
            "timestamp": int(
                datetime(2026, 6, 5, tzinfo=timezone.utc).timestamp() * 1000
            ),
            "field": {"name": "State"},
            "added": [{"name": "Done"}],
        },
    ]

    history = derive_state_history(activities, snapshot, Config())

    assert history.state_at_period_end == "Done"
    assert history.started_in_period_date == ""
    assert history.completed_in_period_date == ""


def test_contiguous_periods_reconcile_in_progress_started_and_completed():
    class Config:
        completed_states = ["Staging", "Done"]
        timezone = timezone.utc

    def activity(year, month, day, state):
        return {
            "timestamp": int(
                datetime(year, month, day, tzinfo=timezone.utc).timestamp() * 1000
            ),
            "field": {"name": "State"},
            "added": [{"name": state}],
        }

    first = Snapshot("2026-06-01", "2026-06-14", "2026-06-14")
    second = Snapshot("2026-06-15", "2026-06-28", "2026-06-28")
    histories = [
        [activity(2026, 5, 20, "In Progress")],
        [activity(2026, 6, 15, "In Progress")],
        [activity(2026, 6, 1, "In Progress"), activity(2026, 6, 16, "Done")],
    ]
    first_period = [
        derive_state_history(activities, first, Config()) for activities in histories
    ]
    second_period = [
        derive_state_history(activities, second, Config()) for activities in histories
    ]

    first_in_progress = sum(
        history.state_at_period_end == "In Progress" for history in first_period
    )
    second_in_progress = sum(
        history.state_at_period_end == "In Progress" for history in second_period
    )
    second_started = sum(
        bool(history.started_in_period_date) for history in second_period
    )
    second_completed = sum(
        bool(history.completed_in_period_date) for history in second_period
    )

    assert second_in_progress == first_in_progress + second_started - second_completed


def test_diff_snapshot_rows_detects_add_update_and_remove():
    class Config:
        sprint_order = ["Sprint 3"]
        state_order = ["Staging", "Done", "In Progress"]
        assignee_order = ["ferenci84", "Pujan", "Unassigned"]

    key = "2026-05-20..2026-05-31@2026-06-01"
    existing_rows = [
        {
            "Snapshot Key": key,
            "Issue ID": "CL-1",
            "Summary": "Old",
            "Sprint": "Sprint 3",
        },
        {
            "Snapshot Key": key,
            "Issue ID": "CL-2",
            "Summary": "Removed",
        },
        {
            "Snapshot Key": "other@date",
            "Issue ID": "CL-3",
            "Summary": "Ignored",
        },
    ]
    expected_rows = [
        {
            "Snapshot Key": key,
            "Issue ID": "CL-1",
            "Summary": "New",
            "Sprint": "Sprint 3",
        },
        {
            "Snapshot Key": key,
            "Issue ID": "CL-4",
            "Summary": "Added",
        },
    ]

    snapshot = Snapshot("2026-05-20", "2026-05-31", "2026-06-01")
    diff = diff_snapshot_rows(existing_rows, expected_rows, snapshot, Config())

    assert [row["Issue ID"] for row in diff["adds"]] == ["CL-4"]
    assert [row["Issue ID"] for row in diff["removes"]] == ["CL-2"]
    assert diff["protected"] == []
    assert diff["updates"][0][2]["Summary"] == ("Old", "New")


def test_diff_snapshot_rows_keeps_protected_manual_rows_out_of_removals():
    class Config:
        sprint_order = ["Sprint 3"]
        state_order = ["Staging", "Done", "In Progress"]
        assignee_order = ["ferenci84", "Pujan", "Unassigned"]

    existing_rows = [
        {
            "Snapshot Key": "2026-05-20..2026-05-31@2026-06-01",
            "Issue ID": "CL-1",
            "Summary": "Manual override",
            "Manual Completion Date": "2026-05-19",
        }
    ]

    snapshot = Snapshot("2026-05-20", "2026-05-31", "2026-06-01")
    diff = diff_snapshot_rows(existing_rows, [], snapshot, Config())

    assert diff["removes"] == []
    assert [row["Issue ID"] for row in diff["protected"]] == ["CL-1"]
    assert diff["protected"][0]["Snapshot Key"].startswith("manual-excluded::")
    assert diff["protected"][0]["Period Start"] == "manual-excluded"


def test_protected_manual_row_detection_uses_preserved_fields():
    row = {column: "" for column in TASK_COLUMNS}
    assert not is_protected_manual_row(row)

    row["Manual Completion Date"] = "2026-05-19"
    assert is_protected_manual_row(row)


def test_manual_exclusion_row_moves_row_out_of_snapshot_filters():
    row = {
        "Snapshot Key": "2026-05-20..2026-05-31@2026-06-01",
        "Snapshot Date": "2026-06-01",
        "Period Start": "2026-05-20",
        "Period End": "2026-05-31",
        "Issue ID": "CL-244",
        "Manual Completion Date": "2026-05-19",
    }
    snapshot = Snapshot("2026-05-20", "2026-05-31", "2026-06-01")

    excluded = manual_exclusion_row(row, snapshot)

    assert excluded["Snapshot Key"] == (
        "manual-excluded::2026-05-20..2026-05-31@2026-06-01::CL-244"
    )
    assert excluded["Snapshot Date"] == "manual-excluded"
    assert excluded["Period Start"] == "manual-excluded"
    assert excluded["Period End"] == "manual-excluded"
    assert excluded["Manual Completion Date"] == "2026-05-19"


def test_build_summary_values_appends_new_period_after_existing_report():
    class Config:
        watched_sprints = ["Sprint 3"]
        summary_assignees = ["ferenci84", "Pujan", "Unassigned"]

    existing_summary = [
        ["Sprint 3", "2026-06-02", "2026-05-20", "2026-06-02"],
        ["Assignee", "Completed Tasks", "Completed Story Points"],
        ["ferenci84", "1", "3"],
    ]
    snapshot = Snapshot(
        period_start="2026-05-20",
        period_end="2026-05-31",
        snapshot_date="2026-06-01",
    )

    values = build_summary_values(existing_summary, Config(), snapshot)

    assert values[:3] == existing_summary
    assert values[3] == []
    assert values[4][:5] == [
        "2026-05-20..2026-05-31@2026-06-01",
        "Sprint 3",
        "2026-06-01",
        "2026-05-20",
        "2026-05-31",
    ]
    assert "Tasks!$I:$I" in values[6][1]
    assert "SUMIFS(Tasks!$J:$J" in values[6][2]
    assert values[5] == [
        "Assignee",
        "Completed Tasks",
        "Completed Story Points",
        "In Progress at Period End Tasks",
        "In Progress at Period End Story Points",
        "Started Tasks",
        "Started Story Points",
    ]
    assert "Tasks!$V:$V" in values[6][1]
    assert "Tasks!$S:$S" in values[6][3]
    assert "Tasks!$T:$T" in values[6][5]
    assert "SUMIFS(Tasks!$J:$J" in values[6][6]


def test_build_summary_values_refreshes_existing_snapshot_formulas():
    class Config:
        watched_sprints = ["Sprint 3"]
        summary_assignees = ["ferenci84", "Pujan", "Unassigned"]

    existing_summary = [
        ["2026-05-20..2026-05-31@2026-06-01", "Sprint 3", "2026-06-01"],
        ["Assignee", "Completed Tasks", "Completed Story Points"],
        ["ferenci84", "1", "3"],
        ["Sum", "=SUM(B2:B3)", "=SUM(C2:C3)"],
    ]
    snapshot = Snapshot("2026-05-20", "2026-05-31", "2026-06-01")

    values = build_summary_values(existing_summary, Config(), snapshot)

    assert values[0][:5] == [
        "2026-05-20..2026-05-31@2026-06-01",
        "Sprint 3",
        "2026-06-01",
        "2026-05-20",
        "2026-05-31",
    ]
    assert values[1][-2:] == ["Started Tasks", "Started Story Points"]
    assert "Tasks!$T:$T" in values[2][-2]
    assert "SUMIFS(Tasks!$J:$J" in values[2][-1]


def test_build_summary_values_preserves_existing_formula_cells():
    class Config:
        watched_sprints = ["Sprint 3"]
        summary_assignees = ["ferenci84", "Pujan", "Unassigned"]

    existing_summary = [
        ["existing", "Sprint 3", "2026-06-01", "2026-05-20", "2026-05-31"],
        ["Assignee", "Completed Tasks"],
        ["ferenci84", "=COUNTIFS(Tasks!$A:$A,A1)"],
    ]
    snapshot = Snapshot("2026-06-01", "2026-06-14", "2026-06-14")

    values = build_summary_values(existing_summary, Config(), snapshot)

    assert values[: len(existing_summary)] == existing_summary


def test_order_task_rows_preserves_snapshot_group_order_and_sorts_within_group():
    class Config:
        sprint_order = ["Sprint 3", "Release 1"]
        state_order = ["Staging", "Done", "In Progress"]
        assignee_order = ["ferenci84", "Pujan", "Unassigned"]

    existing_rows = [
        {"Snapshot Key": "old", "Issue ID": "CL-2"},
        {"Snapshot Key": "current", "Issue ID": "CL-4"},
    ]
    rows = [
        {
            "Snapshot Key": "current",
            "Sprint": "Sprint 3",
            "State at Period End": "In Progress",
            "Assignee": "ferenci84",
            "Issue ID": "CL-3",
        },
        {
            "Snapshot Key": "old",
            "Sprint": "Release 1",
            "State at Period End": "Done",
            "Assignee": "Pujan",
            "Issue ID": "CL-2",
        },
        {
            "Snapshot Key": "current",
            "Sprint": "Sprint 3",
            "State at Period End": "Staging",
            "Assignee": "Pujan",
            "Issue ID": "CL-1",
        },
    ]

    ordered = order_task_rows(
        rows,
        Config(),
        snapshot_key_order(existing_rows, "current"),
    )

    assert [row["Issue ID"] for row in ordered] == ["CL-2", "CL-1", "CL-3"]


def test_diff_can_target_all_rows_for_the_same_period():
    class Config:
        sprint_order = ["Sprint 3"]
        state_order = ["Staging", "Done", "In Progress"]
        assignee_order = ["ferenci84", "Pujan", "Unassigned"]

    existing_rows = [
        {
            "Snapshot Key": "2026-05-20..2026-05-31@2026-06-01",
            "Snapshot Date": "2026-06-01",
            "Period Start": "2026-05-20",
            "Period End": "2026-05-31",
            "Issue ID": "CL-1",
            "Sprint": "Sprint 3",
            "State": "Staging",
            "Assignee": "ferenci84",
        },
        {
            "Snapshot Key": "2026-05-20..2026-05-31@2026-06-02",
            "Snapshot Date": "2026-06-02",
            "Period Start": "2026-05-20",
            "Period End": "2026-05-31",
            "Issue ID": "CL-2",
            "Sprint": "Sprint 3",
            "State": "Staging",
            "Assignee": "ferenci84",
        },
    ]
    snapshot = Snapshot("2026-05-20", "2026-05-31", "2026-06-01")

    diff = diff_snapshot_rows(
        existing_rows,
        [],
        snapshot,
        Config(),
        replace_same_period=True,
    )

    assert [row["Issue ID"] for row in diff["removes"]] == ["CL-1", "CL-2"]


def test_rows_are_included_for_period_completion_period_end_or_started_work():
    class Config:
        completed_states = ["Staging", "Done"]

    snapshot = Snapshot(
        period_start="2026-05-20",
        period_end="2026-05-31",
        snapshot_date="2026-06-01",
    )

    assert not include_snapshot_row(
        {
            "State at Period End": "Done",
            "Started in Period Date": "",
            "Completed in Period Date": "",
        },
        Config(),
        snapshot,
    )
    assert include_snapshot_row(
        {
            "State at Period End": "Done",
            "Started in Period Date": "",
            "Completed in Period Date": "2026-05-27",
        },
        Config(),
        snapshot,
    )
    assert include_snapshot_row(
        {
            "State at Period End": "In Progress",
            "Started in Period Date": "",
            "Completed in Period Date": "",
        },
        Config(),
        snapshot,
    )


def test_started_row_is_included_when_not_done_or_in_progress_at_period_end():
    class Config:
        completed_states = ["Staging", "Done"]

    snapshot = Snapshot(
        period_start="2026-05-20",
        period_end="2026-05-31",
        snapshot_date="2026-06-01",
    )

    assert include_snapshot_row(
        {
            "State at Period End": "Open",
            "Started in Period Date": "2026-05-28",
            "Completed in Period Date": "",
        },
        Config(),
        snapshot,
    )