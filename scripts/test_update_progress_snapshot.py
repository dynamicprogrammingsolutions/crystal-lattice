from update_progress_snapshot import (
    Snapshot,
    TASK_COLUMNS,
    build_summary_values,
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


def test_build_summary_values_does_not_modify_existing_snapshot_summary():
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

    assert build_summary_values(existing_summary, Config(), snapshot) == existing_summary


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
            "State": "In Progress",
            "Assignee": "ferenci84",
            "Issue ID": "CL-3",
        },
        {
            "Snapshot Key": "old",
            "Sprint": "Release 1",
            "State": "Done",
            "Assignee": "Pujan",
            "Issue ID": "CL-2",
        },
        {
            "Snapshot Key": "current",
            "Sprint": "Sprint 3",
            "State": "Staging",
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


def test_completed_rows_are_only_included_when_completion_date_is_in_period():
    class Config:
        completed_states = ["Staging", "Done"]

    snapshot = Snapshot(
        period_start="2026-05-20",
        period_end="2026-05-31",
        snapshot_date="2026-06-01",
    )

    assert not include_snapshot_row(
        {"State": "Done", "Effective Completion Date": "2026-03-02"},
        Config(),
        snapshot,
    )
    assert include_snapshot_row(
        {"State": "Done", "Effective Completion Date": "2026-05-27"},
        Config(),
        snapshot,
    )
    assert include_snapshot_row(
        {"State": "In Progress", "Effective Completion Date": ""},
        Config(),
        snapshot,
    )


def test_completed_row_with_creation_date_fallback_is_included_when_in_period():
    class Config:
        completed_states = ["Staging", "Done"]

    snapshot = Snapshot(
        period_start="2026-05-20",
        period_end="2026-05-31",
        snapshot_date="2026-06-01",
    )

    assert include_snapshot_row(
        {"State": "Staging", "Effective Completion Date": "2026-05-28"},
        Config(),
        snapshot,
    )