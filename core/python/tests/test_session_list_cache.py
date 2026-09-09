from __future__ import annotations

from pathlib import Path

from agent_app._session_list_cache import (
    _PersistedSessionSummary,
    _SQLiteSessionSummaryCache,
)


def _record(*, revision: str = "revision") -> _PersistedSessionSummary:
    return _PersistedSessionSummary(
        session_id="session",
        revision_token=revision,
        contract_token="contract",
        summary={
            "session_id": "session",
            "modified": 1.0,
            "preview": "preview",
            "metadata": {},
            "presentation": {
                "title": "preview",
                "subtitle": None,
                "meta": None,
            },
        },
        order_specs=(),
        diagnostics=(),
    )


# Requirements:
# - SLIST-014: Confirms only matching revision and contract entries are reusable.
# - SLIST-018: Confirms complete summaries round-trip through private persistence.
def test_sqlite_summary_cache_round_trips_only_valid_entries(
    tmp_path: Path,
) -> None:
    cache = _SQLiteSessionSummaryCache(tmp_path / "cache.sqlite3")
    cache.put(_record())

    assert cache.load_valid(
        revision_tokens={"session": "revision"},
        contract_token="contract",
    ) == {"session": _record()}
    assert (
        cache.load_valid(
            revision_tokens={"session": "changed"},
            contract_token="contract",
        )
        == {}
    )
    assert (
        cache.load_valid(
            revision_tokens={"session": "revision"},
            contract_token="changed",
        )
        == {}
    )


# Requirements:
# - SLIST-018: Confirms missing and explicitly invalidated rows are removed safely.
# - SLIST-019: Confirms invalidation removes obsolete persistent summaries.
def test_sqlite_summary_cache_removes_missing_and_invalidated_entries(
    tmp_path: Path,
) -> None:
    cache = _SQLiteSessionSummaryCache(tmp_path / "cache.sqlite3")
    cache.put(_record())

    cache.remove_missing([])

    assert (
        cache.load_valid(
            revision_tokens={"session": "revision"},
            contract_token="contract",
        )
        == {}
    )

    cache.put(_record())
    cache.invalidate("session")
    assert (
        cache.load_valid(
            revision_tokens={"session": "revision"},
            contract_token="contract",
        )
        == {}
    )


# Requirements:
# - SLIST-018: Confirms corrupt derived state is moved aside and rebuilt.
def test_sqlite_summary_cache_rebuilds_corrupt_database(tmp_path: Path) -> None:
    path = tmp_path / "cache.sqlite3"
    path.write_bytes(b"not a sqlite database")

    cache = _SQLiteSessionSummaryCache(path)
    cache.put(_record())

    assert cache.available is True
    assert cache.take_error() is not None
    assert cache.load_valid(
        revision_tokens={"session": "revision"},
        contract_token="contract",
    ) == {"session": _record()}
    assert list(tmp_path.glob("cache.sqlite3.corrupt-*"))
