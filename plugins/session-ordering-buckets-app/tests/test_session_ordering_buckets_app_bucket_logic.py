from __future__ import annotations

from typing import Any, Dict

import pytest

from session_ordering_buckets_app import SessionOrderingBucketsAppPlugin


def test_order_bucket_fields_and_specs(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_now = 1_700_000_000.0
    monkeypatch.setattr("session_ordering_buckets_app.time.time", lambda: fake_now)

    plugin = SessionOrderingBucketsAppPlugin()
    state = plugin.init(
        {
            "application": {
                "session_order_24h_window_seconds": 86400,
                "session_order_use_updated_at": True,
            }
        }
    )

    recent_pinned = plugin.execute_action(
        app=object(),
        action_id="compute_session_order_buckets",
        params={
            "session_id": "s_recent_pinned",
            "session_summary": {
                "session_updated_at": fake_now - 3600,
                "metadata": {"pinned": True},
            },
        },
        state=state,
    )

    recent_unpinned = plugin.execute_action(
        app=object(),
        action_id="compute_session_order_buckets",
        params={
            "session_id": "s_recent_unpinned",
            "session_summary": {
                "session_updated_at": fake_now - 7200,
                "metadata": {"pinned": False},
            },
        },
        state=state,
    )

    old_pinned = plugin.execute_action(
        app=object(),
        action_id="compute_session_order_buckets",
        params={
            "session_id": "s_old_pinned",
            "session_summary": {
                "session_updated_at": fake_now - 3 * 86400,
                "metadata": {"pinned": True},
            },
        },
        state=state,
    )

    def _fields(payload: Dict[str, Any]) -> Dict[str, Any]:
        fields = payload.get("session_list_fields")
        assert isinstance(fields, dict)
        return fields

    f_recent_pinned = _fields(recent_pinned)
    assert f_recent_pinned["recent_archived_rank"] == 0
    assert f_recent_pinned["updated_24h_rank"] == 0
    assert f_recent_pinned["pinned_rank"] == 0
    assert f_recent_pinned["last_updated_sort_key"] == -(fake_now - 3600)

    f_recent_unpinned = _fields(recent_unpinned)
    assert f_recent_unpinned["recent_archived_rank"] == 0
    assert f_recent_unpinned["updated_24h_rank"] == 0
    assert f_recent_unpinned["pinned_rank"] == 1
    assert f_recent_unpinned["last_updated_sort_key"] == -(fake_now - 7200)

    f_old_pinned = _fields(old_pinned)
    assert f_old_pinned["recent_archived_rank"] == 0
    assert f_old_pinned["updated_24h_rank"] == 1
    assert f_old_pinned["pinned_rank"] == 0
    assert f_old_pinned["last_updated_sort_key"] == -(fake_now - 3 * 86400)

    order = recent_pinned.get("session_list_order")
    assert isinstance(order, list)
    keys = [o.get("key") for o in order if isinstance(o, dict)]
    assert keys[:4] == [
        "recent_archived_rank",
        "updated_24h_rank",
        "pinned_rank",
        "last_updated_sort_key",
    ]


def test_recent_archive_rank_respects_the_exact_60_day_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_now = 1_700_000_000.0
    monkeypatch.setattr("session_ordering_buckets_app.time.time", lambda: fake_now)

    plugin = SessionOrderingBucketsAppPlugin()
    state = plugin.init({"application": {"session_order_use_updated_at": True}})

    def archive_rank(*, age_seconds: float, archived: object) -> int:
        result = plugin.execute_action(
            app=object(),
            action_id="compute_session_order_buckets",
            params={
                "session_id": f"session-{age_seconds}",
                "session_summary": {
                    "session_updated_at": fake_now - age_seconds,
                    "metadata": {"archived": archived},
                },
            },
            state=state,
        )
        fields = result["session_list_fields"]
        assert isinstance(fields, dict)
        return fields["recent_archived_rank"]

    archive_window_seconds = 60 * 24 * 60 * 60
    assert archive_rank(age_seconds=archive_window_seconds - 1, archived=True) == 1
    assert archive_rank(age_seconds=archive_window_seconds, archived=True) == 1
    assert archive_rank(age_seconds=archive_window_seconds + 1, archived=True) == 0
    assert archive_rank(age_seconds=3600, archived=False) == 0
    assert archive_rank(age_seconds=3600, archived="true") == 0
