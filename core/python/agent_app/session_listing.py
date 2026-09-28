"""Shared application-layer session-list construction and query service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import itertools
import json
import math
import queue
import threading
import time
from typing import Any, Callable, cast, Dict, List, Mapping, Optional, Protocol, Sequence, Tuple

from agent_core import Session

from ._session_list_cache import (
    _default_cache_path,
    _NullSessionSummaryCache,
    _PersistedSessionSummary,
    _SQLiteSessionSummaryCache,
    _stable_revision_token,
)
from .sessions import SessionStore, SessionStoreRecord


_RESERVED_SUMMARY_KEYS = frozenset(
    {
        "session_id",
        "modified",
        "preview",
        "metadata",
        "presentation",
    }
)
_EXCLUDED_METADATA_KEYS = frozenset({"native_messages"})


class SessionListFilterEvaluator(Protocol):
    """Cold-path filter seam implemented by the filter feature task."""

    def __call__(
        self,
        summaries: List[Dict[str, Any]],
        *,
        ui_elements: Sequence[Dict[str, Any]],
        filter_values: Optional[Dict[str, object]],
        apply_filter_defaults: bool,
    ) -> "SessionListFilterEvaluation | List[Dict[str, Any]]":  # pragma: no cover - protocol
        ...


@dataclass(frozen=True)
class SessionListFilterEvaluation:
    summaries: List[Dict[str, Any]]
    diagnostics: Tuple["SessionListDiagnostic", ...] = ()


def _identity_filter_evaluator(
    summaries: List[Dict[str, Any]],
    *,
    ui_elements: Sequence[Dict[str, Any]],
    filter_values: Optional[Dict[str, object]],
    apply_filter_defaults: bool,
) -> List[Dict[str, Any]]:
    _ = ui_elements, filter_values, apply_filter_defaults
    return summaries


@dataclass(frozen=True)
class SessionListDiagnostic:
    code: str
    message: str
    plugin_id: Optional[str] = None
    action_id: Optional[str] = None
    session_id: Optional[str] = None
    element_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "code": self.code,
            "message": self.message,
        }
        if self.plugin_id is not None:
            result["plugin_id"] = self.plugin_id
        if self.action_id is not None:
            result["action_id"] = self.action_id
        if self.session_id is not None:
            result["session_id"] = self.session_id
        if self.element_id is not None:
            result["element_id"] = self.element_id
        if self.details is not None:
            result["details"] = self.details
        return result


@dataclass(frozen=True)
class ResolvedPath:
    found: bool
    value: Any = None


def resolve_session_list_path(root: Any, path: str) -> ResolvedPath:
    """Resolve a dotted path while preserving missing-versus-null semantics."""

    if not isinstance(path, str) or not path:
        return ResolvedPath(found=False)

    current = root
    for part in path.split("."):
        if isinstance(current, Mapping):
            if part not in current:
                return ResolvedPath(found=False)
            current = current[part]
            continue
        if isinstance(current, (list, tuple)):
            try:
                index = int(part)
            except (TypeError, ValueError):
                return ResolvedPath(found=False)
            if index < 0 or index >= len(current):
                return ResolvedPath(found=False)
            current = current[index]
            continue
        return ResolvedPath(found=False)
    return ResolvedPath(found=True, value=current)


@dataclass(frozen=True)
class _SessionListField:
    element_id: str
    plugin_id: Optional[str]
    role: str
    data: str
    template: str
    order: float
    metadata: Dict[str, Any]
    declaration_index: int


@dataclass(frozen=True)
class _TriggerAction:
    plugin_id: str
    action_id: str
    definition: Dict[str, Any]
    plugin_index: int
    action_index: int


@dataclass(frozen=True)
class _OrderSpec:
    key: str
    direction: str
    has_fallback: bool
    fallback: Any
    priority: int
    plugin_id: str
    action_id: str
    plugin_index: int
    action_index: int
    declaration_index: int

    @property
    def slot(self) -> Tuple[int, int, int]:
        return (self.plugin_index, self.action_index, self.declaration_index)

    def equivalent_contract(self, other: "_OrderSpec") -> bool:
        return (
            self.key == other.key
            and self.direction == other.direction
            and self.has_fallback == other.has_fallback
            and self.fallback == other.fallback
            and self.priority == other.priority
        )


@dataclass
class _CachedSummary:
    revision: object
    revision_token: str
    contract_token: str
    summary: Dict[str, Any]
    order_specs: Tuple[_OrderSpec, ...]
    diagnostics: Tuple[SessionListDiagnostic, ...]
    complete: bool
    cacheable: bool


@dataclass(frozen=True)
class _ResolutionTask:
    key: Tuple[str, str, str, int]
    record: SessionStoreRecord
    actions: Tuple[_TriggerAction, ...]
    fields: Tuple[_SessionListField, ...]
    contract_token: str
    build: Callable[
        [
            SessionStoreRecord,
            Sequence[_TriggerAction],
            Sequence[_SessionListField],
            str,
        ],
        _CachedSummary,
    ]
    persist: Callable[[_CachedSummary], None]


class _BackgroundSummaryResolver:
    """Private newest-first resolver with cooperative daemon-worker shutdown."""

    def __init__(self, *, worker_count: int) -> None:
        self._worker_count = max(1, worker_count)
        self._condition = threading.Condition(threading.RLock())
        self._queue: queue.PriorityQueue[Tuple[float, int, Optional[_ResolutionTask]]] = (
            queue.PriorityQueue()
        )
        self._sequence = itertools.count()
        self._workers: List[threading.Thread] = []
        self._desired: Dict[str, Tuple[str, str, str, int]] = {}
        self._latest_tasks: Dict[str, _ResolutionTask] = {}
        self._scheduled: Dict[str, Tuple[str, str, str, int]] = {}
        self._results: Dict[str, Tuple[Tuple[str, str, str, int], _CachedSummary]] = {}
        self._epochs: Dict[str, int] = {}
        self._closed = False

    def _key_for(
        self,
        record: SessionStoreRecord,
        contract_token: str,
    ) -> Tuple[str, str, str, int]:
        return (
            record.session_id,
            _stable_revision_token(record.revision),
            contract_token,
            self._epochs.get(record.session_id, 0),
        )

    def _ensure_workers_locked(self) -> None:
        if self._workers or self._closed:
            return
        for index in range(self._worker_count):
            worker = threading.Thread(
                target=self._worker,
                name=f"session-list-resolver-{index + 1}",
                daemon=True,
            )
            self._workers.append(worker)
            worker.start()

    def resolve(
        self,
        *,
        records: Sequence[SessionStoreRecord],
        actions: Sequence[_TriggerAction],
        fields: Sequence[_SessionListField],
        contract_token: str,
        persisted: Mapping[str, _CachedSummary],
        build: Callable[
            [
                SessionStoreRecord,
                Sequence[_TriggerAction],
                Sequence[_SessionListField],
                str,
            ],
            _CachedSummary,
        ],
        persist: Callable[[_CachedSummary], None],
        timeout_seconds: float,
    ) -> Dict[str, _CachedSummary]:
        ordered_records = sorted(
            records,
            key=lambda record: record.modified,
            reverse=True,
        )
        with self._condition:
            if self._closed:
                return {}
            live_ids = {record.session_id for record in ordered_records}
            for session_id in tuple(self._desired):
                if session_id not in live_ids:
                    self._desired.pop(session_id, None)
                    self._latest_tasks.pop(session_id, None)
                    self._results.pop(session_id, None)

            for record in ordered_records:
                key = self._key_for(record, contract_token)
                self._desired[record.session_id] = key
                existing = self._results.get(record.session_id)
                if existing is not None and existing[0] != key:
                    self._results.pop(record.session_id, None)
                    existing = None

                seeded = persisted.get(record.session_id)
                if existing is None and seeded is not None:
                    self._results[record.session_id] = (key, seeded)
                    existing = (key, seeded)

                task = _ResolutionTask(
                    key=key,
                    record=record,
                    actions=tuple(actions),
                    fields=tuple(fields),
                    contract_token=contract_token,
                    build=build,
                    persist=persist,
                )
                self._latest_tasks[record.session_id] = task
                if existing is None:
                    self._enqueue_latest_locked(record.session_id)

            self._ensure_workers_locked()
            deadline = time.monotonic() + max(0.0, timeout_seconds)
            while not self._all_desired_resolved_locked(ordered_records):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                self._condition.wait(timeout=remaining)

            return self._snapshot_locked(ordered_records, contract_token)

    def _enqueue_latest_locked(self, session_id: str) -> None:
        if self._closed or session_id in self._scheduled:
            return
        desired = self._desired.get(session_id)
        task = self._latest_tasks.get(session_id)
        result = self._results.get(session_id)
        if (
            desired is None
            or task is None
            or task.key != desired
            or (result is not None and result[0] == desired)
        ):
            return
        self._scheduled[session_id] = task.key
        self._queue.put(
            (
                -float(task.record.modified),
                next(self._sequence),
                task,
            )
        )

    def _all_desired_resolved_locked(
        self,
        records: Sequence[SessionStoreRecord],
    ) -> bool:
        for record in records:
            desired = self._desired.get(record.session_id)
            result = self._results.get(record.session_id)
            if desired is None or result is None or result[0] != desired:
                return False
        return True

    def _snapshot_locked(
        self,
        records: Sequence[SessionStoreRecord],
        contract_token: str,
    ) -> Dict[str, _CachedSummary]:
        snapshot: Dict[str, _CachedSummary] = {}
        for record in records:
            key = self._key_for(record, contract_token)
            result = self._results.get(record.session_id)
            if result is not None and result[0] == key:
                snapshot[record.session_id] = result[1]
        return snapshot

    def get(
        self,
        *,
        record: SessionStoreRecord,
        contract_token: str,
    ) -> Optional[_CachedSummary]:
        with self._condition:
            key = self._key_for(record, contract_token)
            result = self._results.get(record.session_id)
            if result is None or result[0] != key:
                return None
            return result[1]

    def install(
        self,
        *,
        record: SessionStoreRecord,
        contract_token: str,
        result: _CachedSummary,
    ) -> None:
        with self._condition:
            if self._closed:
                return
            key = self._key_for(record, contract_token)
            self._desired[record.session_id] = key
            self._results[record.session_id] = (key, result)
            self._condition.notify_all()

    def pending_count(self) -> int:
        with self._condition:
            return sum(
                1
                for session_id, desired in self._desired.items()
                if (session_id not in self._results or self._results[session_id][0] != desired)
            )

    def invalidate(self, session_id: Optional[str] = None) -> None:
        with self._condition:
            if session_id is None:
                affected = set(self._desired) | set(self._results) | set(self._epochs)
                for affected_id in affected:
                    self._epochs[affected_id] = self._epochs.get(affected_id, 0) + 1
                self._desired.clear()
                self._results.clear()
            else:
                self._epochs[session_id] = self._epochs.get(session_id, 0) + 1
                self._desired.pop(session_id, None)
                self._results.pop(session_id, None)
            self._condition.notify_all()

    def _worker(self) -> None:
        while True:
            _priority, _sequence, task = self._queue.get()
            if task is None:
                self._queue.task_done()
                return
            try:
                with self._condition:
                    if self._closed or self._desired.get(task.record.session_id) != task.key:
                        if self._scheduled.get(task.record.session_id) == task.key:
                            self._scheduled.pop(task.record.session_id, None)
                        self._enqueue_latest_locked(task.record.session_id)
                        self._condition.notify_all()
                        continue
                result = task.build(
                    task.record,
                    task.actions,
                    task.fields,
                    task.contract_token,
                )
                with self._condition:
                    current = (
                        not self._closed and self._desired.get(task.record.session_id) == task.key
                    )
                if current and result.cacheable:
                    task.persist(result)
                with self._condition:
                    if self._scheduled.get(task.record.session_id) == task.key:
                        self._scheduled.pop(task.record.session_id, None)
                    if not self._closed and self._desired.get(task.record.session_id) == task.key:
                        self._results[task.record.session_id] = (task.key, result)
                    else:
                        self._enqueue_latest_locked(task.record.session_id)
                    self._condition.notify_all()
            except Exception:
                with self._condition:
                    if self._scheduled.get(task.record.session_id) == task.key:
                        self._scheduled.pop(task.record.session_id, None)
                    self._enqueue_latest_locked(task.record.session_id)
                    self._condition.notify_all()
            finally:
                self._queue.task_done()

    def shutdown(self) -> None:
        with self._condition:
            if self._closed:
                return
            self._closed = True
            self._desired.clear()
            self._latest_tasks.clear()
            self._results.clear()
            for _worker in self._workers:
                self._queue.put((0.0, next(self._sequence), None))
            self._condition.notify_all()


ListActions = Callable[[], List[Dict[str, Any]]]
ListUiElements = Callable[[], List[Dict[str, Any]]]
ExecuteAction = Callable[
    [str, str, Dict[str, Any], Optional[Dict[str, Any]]],
    Dict[str, Any],
]


class SessionListService:
    """Build and query shared session summaries for all application consumers."""

    _DERIVATION_VERSION = 2

    def __init__(
        self,
        *,
        store: SessionStore,
        list_actions: ListActions,
        list_ui_elements: ListUiElements,
        execute_action: ExecuteAction,
        logger: Any,
        filter_evaluator: Optional[SessionListFilterEvaluator] = None,
        context: Optional[Mapping[str, Any]] = None,
    ) -> None:
        self._store = store
        self._list_actions = list_actions
        self._list_ui_elements = list_ui_elements
        self._execute_action = execute_action
        self._logger = logger
        self._filter_evaluator: SessionListFilterEvaluator = (
            filter_evaluator or _identity_filter_evaluator
        )
        self._last_diagnostics: Tuple[SessionListDiagnostic, ...] = ()
        self._lock = threading.RLock()
        self._action_lock = threading.RLock()
        self._closed = threading.Event()
        self._context = context or {}
        self._configuration_diagnostics: Tuple[SessionListDiagnostic, ...] = ()
        (
            foreground_timeout,
            worker_count,
            persistent_cache,
        ) = self._configure_resolution()
        self._foreground_timeout_seconds = foreground_timeout
        self._persistent_cache = persistent_cache
        self._resolver = _BackgroundSummaryResolver(worker_count=worker_count)
        self._summary_context_token = self._build_summary_context_token()

    def _configure_resolution(
        self,
    ) -> Tuple[
        float,
        int,
        _SQLiteSessionSummaryCache | _NullSessionSummaryCache,
    ]:
        diagnostics: List[SessionListDiagnostic] = []
        raw_config = self._context.get("application_config")
        raw_application = raw_config.get("application") if isinstance(raw_config, Mapping) else None
        application: Mapping[str, Any] = (
            raw_application if isinstance(raw_application, Mapping) else {}
        )
        raw_implementation_config = application.get("cached_background_session_list")
        implementation_config: Mapping[str, Any] = (
            raw_implementation_config if isinstance(raw_implementation_config, Mapping) else {}
        )

        raw_timeout = implementation_config.get(
            "foreground_timeout_seconds",
            10.0,
        )
        if (
            isinstance(raw_timeout, (int, float))
            and not isinstance(raw_timeout, bool)
            and math.isfinite(float(raw_timeout))
            and float(raw_timeout) >= 0.0
        ):
            foreground_timeout = float(raw_timeout)
        else:
            foreground_timeout = 10.0
            diagnostics.append(
                SessionListDiagnostic(
                    code="invalid_session_list_resolution_config",
                    message=(
                        "cached background session-list foreground timeout "
                        "must be a non-negative finite number; using 10 seconds."
                    ),
                )
            )

        raw_workers = implementation_config.get("worker_count", 1)
        if (
            isinstance(raw_workers, int)
            and not isinstance(raw_workers, bool)
            and 1 <= raw_workers <= 8
        ):
            worker_count = raw_workers
        else:
            worker_count = 1
            diagnostics.append(
                SessionListDiagnostic(
                    code="invalid_session_list_resolution_config",
                    message=(
                        "cached background session-list worker count must be "
                        "an integer from 1 through 8; using one worker."
                    ),
                )
            )

        cache: _SQLiteSessionSummaryCache | _NullSessionSummaryCache
        cache_enabled = implementation_config.get(
            "persistent_cache_enabled",
            True,
        )
        if not isinstance(cache_enabled, bool):
            cache_enabled = True
            diagnostics.append(
                SessionListDiagnostic(
                    code="invalid_session_list_resolution_config",
                    message=(
                        "cached background session-list persistent cache "
                        "enabled must be a boolean; enabling persistent reuse."
                    ),
                )
            )
        store_identity = self._context.get("session_store_identity")
        override = implementation_config.get("local_cache_directory")
        if override is not None and not isinstance(override, str):
            diagnostics.append(
                SessionListDiagnostic(
                    code="invalid_session_list_resolution_config",
                    message=(
                        "cached background session-list local cache directory "
                        "must be a string; using the default."
                    ),
                )
            )
            override = None

        if cache_enabled and isinstance(store_identity, str) and store_identity:
            cache = _SQLiteSessionSummaryCache(
                _default_cache_path(
                    session_store_identity=store_identity,
                    override=override,
                )
            )
            cache_error = cache.take_error()
            if cache_error is not None:
                diagnostics.append(
                    SessionListDiagnostic(
                        code="session_list_cache_unavailable",
                        message=(
                            "Persistent session-list summaries required "
                            "recovery or are unavailable; continuing safely."
                        ),
                        details={"error": cache_error},
                    )
                )
        else:
            cache = _NullSessionSummaryCache()

        self._configuration_diagnostics = tuple(diagnostics)
        return foreground_timeout, worker_count, cache

    def _build_summary_context_token(self) -> str:
        payload = {
            "derivation_version": self._DERIVATION_VERSION,
            "application_config": self._context.get("application_config"),
            "application_plugins": self._context.get("application_plugins"),
        }
        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            default=repr,
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def set_filter_evaluator(self, evaluator: SessionListFilterEvaluator) -> None:
        """Install the filter evaluator supplied by the filter feature layer."""

        if not callable(evaluator):
            raise TypeError("evaluator must be callable")
        with self._lock:
            self._filter_evaluator = evaluator

    def invalidate(self, session_id: Optional[str] = None) -> None:
        self._resolver.invalidate(session_id)
        self._persistent_cache.invalidate(session_id)

    def get_last_diagnostics(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [diagnostic.to_dict() for diagnostic in self._last_diagnostics]

    def list_session_summaries(
        self,
        *,
        filter_values: Optional[Dict[str, object]] = None,
        apply_filter_defaults: bool = False,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        started = time.monotonic()
        diagnostics: List[SessionListDiagnostic] = list(self._configuration_diagnostics)
        actions, ui_elements, fields, contract_token = self._load_contract(diagnostics)

        # Membership enumeration intentionally precedes the foreground content
        # resolution budget. Stores return only opaque identities and metadata.
        records = self._store.list_records()
        resolution_deadline = time.monotonic() + self._foreground_timeout_seconds
        revision_tokens = {
            record.session_id: _stable_revision_token(record.revision) for record in records
        }
        persisted = self._load_persisted_summaries(
            records=records,
            revision_tokens=revision_tokens,
            contract_token=contract_token,
        )
        self._persistent_cache.remove_missing([record.session_id for record in records])
        resolved = self._resolver.resolve(
            records=records,
            actions=actions,
            fields=fields,
            contract_token=contract_token,
            persisted=persisted,
            build=self._build_summary_for_record,
            persist=self._persist_summary,
            timeout_seconds=max(
                0.0,
                resolution_deadline - time.monotonic(),
            ),
        )

        complete_summaries: List[Dict[str, Any]] = []
        metadata_summaries: List[Dict[str, Any]] = []
        all_specs: List[_OrderSpec] = []
        records_by_id = {record.session_id: record for record in records}
        for record in records:
            result = resolved.get(record.session_id)
            if result is not None:
                diagnostics.extend(result.diagnostics)
                if result.complete:
                    complete_summaries.append(result.summary)
                    all_specs.extend(result.order_specs)
                    continue
                metadata_summaries.append(result.summary)
                continue
            metadata_summaries.append(self._build_metadata_summary(record=record, fields=fields))

        ordered_complete = self._apply_ordering(
            complete_summaries,
            all_specs,
            diagnostics,
        )
        with self._lock:
            filter_evaluator = self._filter_evaluator
        filter_evaluation = filter_evaluator(
            ordered_complete,
            ui_elements=ui_elements,
            filter_values=filter_values,
            apply_filter_defaults=apply_filter_defaults,
        )
        if isinstance(filter_evaluation, SessionListFilterEvaluation):
            filtered_complete = filter_evaluation.summaries
            diagnostics.extend(filter_evaluation.diagnostics)
        else:
            filtered_complete = filter_evaluation

        metadata_summaries.sort(
            key=lambda summary: records_by_id[str(summary.get("session_id") or "")].modified,
            reverse=True,
        )
        filtered = [*filtered_complete, *metadata_summaries]
        if limit is not None and isinstance(limit, int) and not isinstance(limit, bool):
            if limit >= 0:
                filtered = filtered[:limit]

        cache_error = self._persistent_cache.take_error()
        if cache_error is not None:
            diagnostics.append(
                SessionListDiagnostic(
                    code="session_list_cache_unavailable",
                    message=(
                        "Persistent session-list summaries became unavailable; "
                        "continuing with process-local results."
                    ),
                    details={"error": cache_error},
                )
            )
        self._publish_diagnostics(diagnostics)
        self._log_resolution(
            record_count=len(records),
            complete_count=len(complete_summaries),
            metadata_count=len(metadata_summaries),
            persistent_hit_count=len(persisted),
            pending_count=self._resolver.pending_count(),
            elapsed_seconds=time.monotonic() - started,
        )
        return filtered

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id must be a non-empty string")

        diagnostics: List[SessionListDiagnostic] = list(self._configuration_diagnostics)
        actions, _ui_elements, fields, contract_token = self._load_contract(diagnostics)
        record = self._store.get_record(session_id)
        if record is None:
            self.invalidate(session_id)
            raise KeyError(f"Session {session_id!r} not found")

        result = self._resolver.get(
            record=record,
            contract_token=contract_token,
        )
        if result is None:
            persisted = self._load_persisted_summaries(
                records=[record],
                revision_tokens={record.session_id: _stable_revision_token(record.revision)},
                contract_token=contract_token,
            )
            result = persisted.get(record.session_id)
        if result is None:
            result = self._build_summary_for_record(
                record,
                actions,
                fields,
                contract_token,
            )
            if result.cacheable:
                self._persist_summary(result)
        self._resolver.install(
            record=record,
            contract_token=contract_token,
            result=result,
        )
        diagnostics.extend(result.diagnostics)
        self._publish_diagnostics(diagnostics)
        return result.summary

    def _shutdown(self) -> None:
        self._closed.set()
        self._resolver.shutdown()
        self._persistent_cache.close()

    def _log_resolution(
        self,
        *,
        record_count: int,
        complete_count: int,
        metadata_count: int,
        persistent_hit_count: int,
        pending_count: int,
        elapsed_seconds: float,
    ) -> None:
        log = getattr(self._logger, "debug", None)
        if callable(log):
            log(
                "session_list_resolution",
                record_count=record_count,
                complete_count=complete_count,
                metadata_count=metadata_count,
                persistent_hit_count=persistent_hit_count,
                pending_count=pending_count,
                elapsed_seconds=elapsed_seconds,
            )

    def _publish_diagnostics(self, diagnostics: Sequence[SessionListDiagnostic]) -> None:
        with self._lock:
            self._last_diagnostics = tuple(diagnostics)
        for diagnostic in diagnostics:
            log = getattr(self._logger, "warning", None)
            if callable(log):
                log(
                    "session list contract diagnostic",
                    **diagnostic.to_dict(),
                )

    @staticmethod
    def _contract_token(
        actions: Sequence[_TriggerAction],
        fields: Sequence[_SessionListField],
    ) -> str:
        payload = {
            "actions": [action.definition for action in actions],
            "fields": [
                {
                    "id": field.element_id,
                    "plugin": field.plugin_id,
                    "role": field.role,
                    "data": field.data,
                    "template": field.template,
                    "order": field.order,
                    "metadata": field.metadata,
                }
                for field in fields
            ],
        }
        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            default=repr,
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def _load_contract(
        self,
        diagnostics: List[SessionListDiagnostic],
    ) -> Tuple[
        List[_TriggerAction],
        List[Dict[str, Any]],
        List[_SessionListField],
        str,
    ]:
        try:
            raw_actions = self._list_actions()
        except Exception as exc:
            diagnostics.append(
                SessionListDiagnostic(
                    code="session_list_actions_unavailable",
                    message="Could not load application action definitions.",
                    details={"error": str(exc)},
                )
            )
            raw_actions = []

        try:
            raw_ui_elements = self._list_ui_elements()
        except Exception as exc:
            diagnostics.append(
                SessionListDiagnostic(
                    code="session_list_ui_unavailable",
                    message="Could not load application UI definitions.",
                    details={"error": str(exc)},
                )
            )
            raw_ui_elements = []

        ui_elements = [element for element in raw_ui_elements if isinstance(element, dict)]
        actions = self._collect_trigger_actions(raw_actions)
        fields = self._normalize_fields(ui_elements, diagnostics)
        local_token = self._contract_token(actions, fields)
        combined_token = hashlib.sha256(
            f"{local_token}:{self._summary_context_token}".encode("utf-8")
        ).hexdigest()
        return actions, ui_elements, fields, combined_token

    @staticmethod
    def _collect_trigger_actions(
        raw_actions: Sequence[Dict[str, Any]],
    ) -> List[_TriggerAction]:
        plugin_indices: Dict[str, int] = {}
        action_indices: Dict[str, int] = {}
        actions: List[_TriggerAction] = []

        for raw_action in raw_actions:
            if not isinstance(raw_action, dict):
                continue
            plugin_id = raw_action.get("plugin")
            action_id = raw_action.get("id")
            if not isinstance(plugin_id, str) or not plugin_id:
                continue
            action_index = action_indices.get(plugin_id, 0)
            action_indices[plugin_id] = action_index + 1
            plugin_index = plugin_indices.setdefault(plugin_id, len(plugin_indices))

            trigger = raw_action.get("trigger")
            matches = trigger == "session_list" or (
                isinstance(trigger, list) and "session_list" in trigger
            )
            if not matches or not isinstance(action_id, str) or not action_id:
                continue
            actions.append(
                _TriggerAction(
                    plugin_id=plugin_id,
                    action_id=action_id,
                    definition=raw_action,
                    plugin_index=plugin_index,
                    action_index=action_index,
                )
            )
        return actions

    @staticmethod
    def _normalize_fields(
        ui_elements: Sequence[Dict[str, Any]],
        diagnostics: List[SessionListDiagnostic],
    ) -> List[_SessionListField]:
        fields: List[_SessionListField] = []
        for declaration_index, element in enumerate(ui_elements):
            if element.get("ui_type") != "session_list_field":
                continue
            element_id = element.get("id")
            plugin_id = element.get("plugin")
            role = element.get("role")
            data = element.get("data")
            template = element.get("template", "{{data}}")
            raw_order = element.get("order", 0)
            raw_metadata = element.get("metadata", {})

            invalid_reason: Optional[str] = None
            if not isinstance(element_id, str) or not element_id:
                invalid_reason = "id must be a non-empty string"
            elif role not in {"title", "subtitle", "meta"}:
                invalid_reason = "role must be title, subtitle, or meta"
            elif not isinstance(data, str) or not data:
                invalid_reason = "data must be a non-empty dotted path"
            elif not isinstance(template, str):
                invalid_reason = "template must be a string"
            elif (
                not isinstance(raw_order, (int, float))
                or isinstance(raw_order, bool)
                or not math.isfinite(float(raw_order))
            ):
                invalid_reason = "order must be a finite number"
            elif not isinstance(raw_metadata, dict):
                invalid_reason = "metadata must be an object"

            if invalid_reason is not None:
                diagnostics.append(
                    SessionListDiagnostic(
                        code="invalid_session_list_field",
                        message=f"Ignoring invalid session_list_field: {invalid_reason}.",
                        plugin_id=plugin_id if isinstance(plugin_id, str) else None,
                        element_id=(element_id if isinstance(element_id, str) else None),
                    )
                )
                continue

            fields.append(
                _SessionListField(
                    element_id=cast(str, element_id),
                    plugin_id=plugin_id if isinstance(plugin_id, str) else None,
                    role=cast(str, role),
                    data=cast(str, data),
                    template=template,
                    order=float(raw_order),
                    metadata=raw_metadata,
                    declaration_index=declaration_index,
                )
            )
        return fields

    def _build_summary_for_record(
        self,
        record: SessionStoreRecord,
        actions: Sequence[_TriggerAction],
        fields: Sequence[_SessionListField],
        contract_token: str,
    ) -> _CachedSummary:
        diagnostics: List[SessionListDiagnostic] = []
        session: Optional[Session]
        try:
            session = self._store.load(record.session_id)
        except Exception as exc:
            session = None
            diagnostics.append(
                SessionListDiagnostic(
                    code="session_summary_load_failed",
                    message="Stored session could not be loaded; using summary fallbacks.",
                    session_id=record.session_id,
                    details={"error": str(exc)},
                )
            )

        if self._closed.is_set():
            return _CachedSummary(
                revision=record.revision,
                revision_token=_stable_revision_token(record.revision),
                contract_token=contract_token,
                summary=self._build_metadata_summary(record=record, fields=fields),
                order_specs=(),
                diagnostics=tuple(diagnostics),
                complete=False,
                cacheable=False,
            )

        summary = self._build_base_summary(record, session)
        order_specs: List[_OrderSpec] = []
        cacheable = session is not None
        with self._action_lock:
            for action in actions:
                action_diagnostics, action_specs, succeeded = self._run_trigger_action(
                    action=action,
                    record=record,
                    session=session,
                    summary=summary,
                )
                diagnostics.extend(action_diagnostics)
                order_specs.extend(action_specs)
                cacheable = cacheable and succeeded

        summary["presentation"] = derive_session_list_presentation(summary, fields)
        return _CachedSummary(
            revision=record.revision,
            revision_token=_stable_revision_token(record.revision),
            contract_token=contract_token,
            summary=summary,
            order_specs=tuple(order_specs),
            diagnostics=tuple(diagnostics),
            complete=session is not None,
            cacheable=cacheable,
        )

    @classmethod
    def _build_metadata_summary(
        cls,
        *,
        record: SessionStoreRecord,
        fields: Sequence[_SessionListField],
    ) -> Dict[str, Any]:
        summary = cls._build_base_summary(record, None)
        summary["presentation"] = derive_session_list_presentation(summary, fields)
        return summary

    def _load_persisted_summaries(
        self,
        *,
        records: Sequence[SessionStoreRecord],
        revision_tokens: Mapping[str, str],
        contract_token: str,
    ) -> Dict[str, _CachedSummary]:
        persisted = self._persistent_cache.load_valid(
            revision_tokens=revision_tokens,
            contract_token=contract_token,
        )
        records_by_id = {record.session_id: record for record in records}
        results: Dict[str, _CachedSummary] = {}
        for session_id, stored in persisted.items():
            record = records_by_id.get(session_id)
            if record is None:
                continue
            try:
                order_specs = tuple(self._order_spec_from_dict(raw) for raw in stored.order_specs)
                diagnostics = tuple(self._diagnostic_from_dict(raw) for raw in stored.diagnostics)
            except (KeyError, TypeError, ValueError):
                continue
            results[session_id] = _CachedSummary(
                revision=record.revision,
                revision_token=stored.revision_token,
                contract_token=stored.contract_token,
                summary=stored.summary,
                order_specs=order_specs,
                diagnostics=diagnostics,
                complete=True,
                cacheable=True,
            )
        return results

    def _persist_summary(self, result: _CachedSummary) -> None:
        if not result.cacheable or not result.complete:
            return
        session_id = result.summary.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            return
        self._persistent_cache.put(
            _PersistedSessionSummary(
                session_id=session_id,
                revision_token=result.revision_token,
                contract_token=result.contract_token,
                summary=result.summary,
                order_specs=tuple(self._order_spec_to_dict(spec) for spec in result.order_specs),
                diagnostics=tuple(diagnostic.to_dict() for diagnostic in result.diagnostics),
            )
        )

    @staticmethod
    def _order_spec_to_dict(spec: _OrderSpec) -> Dict[str, Any]:
        return {
            "key": spec.key,
            "direction": spec.direction,
            "has_fallback": spec.has_fallback,
            "fallback": spec.fallback,
            "priority": spec.priority,
            "plugin_id": spec.plugin_id,
            "action_id": spec.action_id,
            "plugin_index": spec.plugin_index,
            "action_index": spec.action_index,
            "declaration_index": spec.declaration_index,
        }

    @staticmethod
    def _order_spec_from_dict(raw: Mapping[str, Any]) -> _OrderSpec:
        return _OrderSpec(
            key=str(raw["key"]),
            direction=str(raw["direction"]),
            has_fallback=bool(raw["has_fallback"]),
            fallback=raw.get("fallback"),
            priority=int(raw["priority"]),
            plugin_id=str(raw["plugin_id"]),
            action_id=str(raw["action_id"]),
            plugin_index=int(raw["plugin_index"]),
            action_index=int(raw["action_index"]),
            declaration_index=int(raw["declaration_index"]),
        )

    @staticmethod
    def _diagnostic_from_dict(
        raw: Mapping[str, Any],
    ) -> SessionListDiagnostic:
        details = raw.get("details")
        return SessionListDiagnostic(
            code=str(raw["code"]),
            message=str(raw["message"]),
            plugin_id=(
                str(raw["plugin_id"])
                if isinstance(raw.get("plugin_id"), str)
                else None
            ),
            action_id=(
                str(raw["action_id"])
                if isinstance(raw.get("action_id"), str)
                else None
            ),
            session_id=(
                str(raw["session_id"])
                if isinstance(raw.get("session_id"), str)
                else None
            ),
            element_id=(
                str(raw["element_id"])
                if isinstance(raw.get("element_id"), str)
                else None
            ),
            details=details if isinstance(details, dict) else None,
        )

    @staticmethod
    def _build_base_summary(
        record: SessionStoreRecord,
        session: Optional[Session],
    ) -> Dict[str, Any]:
        metadata: Dict[str, Any] = {}
        preview = ""
        if session is not None:
            raw_metadata = session.metadata
            if isinstance(raw_metadata, dict):
                metadata = {
                    key: value
                    for key, value in raw_metadata.items()
                    if key not in _EXCLUDED_METADATA_KEYS
                }
            for message in session.messages:
                if message.role != "user":
                    continue
                content = message.content
                if not isinstance(content, str) or not content:
                    continue
                single_line = " ".join(content.split())
                preview = single_line[:77] + "..." if len(single_line) > 80 else single_line
                break
        return {
            "session_id": record.session_id,
            "modified": record.modified,
            "preview": preview,
            "metadata": metadata,
        }

    def _run_trigger_action(
        self,
        *,
        action: _TriggerAction,
        record: SessionStoreRecord,
        session: Optional[Session],
        summary: Dict[str, Any],
    ) -> Tuple[List[SessionListDiagnostic], List[_OrderSpec], bool]:
        diagnostics: List[SessionListDiagnostic] = []
        params: Dict[str, Any] = {}
        inputs = action.definition.get("inputs")
        if not isinstance(inputs, dict):
            inputs = {}
        if "session_id" in inputs:
            params["session_id"] = record.session_id
        if "session_summary" in inputs:
            params["session_summary"] = summary
        if "session" in inputs:
            if session is None:
                diagnostics.append(
                    SessionListDiagnostic(
                        code="session_list_action_session_unavailable",
                        message="List-trigger action requires a loadable session.",
                        plugin_id=action.plugin_id,
                        action_id=action.action_id,
                        session_id=record.session_id,
                    )
                )
                return diagnostics, [], True
            params["session"] = session

        try:
            result = self._execute_action(
                action.plugin_id,
                action.action_id,
                params,
                {
                    "lifecycle": "session_list",
                    "trigger_source": "application",
                    "session_id": record.session_id,
                },
            )
        except Exception as exc:
            diagnostics.append(
                SessionListDiagnostic(
                    code="session_list_action_failed",
                    message="List-trigger action failed and was ignored.",
                    plugin_id=action.plugin_id,
                    action_id=action.action_id,
                    session_id=record.session_id,
                    details={"error": str(exc)},
                )
            )
            return diagnostics, [], False

        fields = result.get("session_list_fields")
        if fields is not None and not isinstance(fields, dict):
            diagnostics.append(
                SessionListDiagnostic(
                    code="invalid_session_list_fields_result",
                    message="session_list_fields must be an object.",
                    plugin_id=action.plugin_id,
                    action_id=action.action_id,
                    session_id=record.session_id,
                )
            )
        elif isinstance(fields, dict):
            for key, value in fields.items():
                if not isinstance(key, str) or not key or key in _RESERVED_SUMMARY_KEYS:
                    diagnostics.append(
                        SessionListDiagnostic(
                            code="invalid_session_list_field_result",
                            message="Ignoring a contributed field with an invalid or reserved key.",
                            plugin_id=action.plugin_id,
                            action_id=action.action_id,
                            session_id=record.session_id,
                            details={"key": repr(key)},
                        )
                    )
                    continue
                try:
                    json.dumps(value, allow_nan=False)
                except (TypeError, ValueError):
                    diagnostics.append(
                        SessionListDiagnostic(
                            code="non_serializable_session_list_field",
                            message="Ignoring a contributed field that is not JSON-serializable.",
                            plugin_id=action.plugin_id,
                            action_id=action.action_id,
                            session_id=record.session_id,
                            details={"key": key},
                        )
                    )
                    continue
                summary[key] = value

        specs = self._normalize_order_specs(
            result.get("session_list_order"),
            action=action,
            session_id=record.session_id,
            diagnostics=diagnostics,
        )
        return diagnostics, specs, True

    @staticmethod
    def _normalize_order_specs(
        raw_specs: Any,
        *,
        action: _TriggerAction,
        session_id: str,
        diagnostics: List[SessionListDiagnostic],
    ) -> List[_OrderSpec]:
        if raw_specs is None:
            return []
        if isinstance(raw_specs, dict):
            candidates = [raw_specs]
        elif isinstance(raw_specs, list):
            candidates = raw_specs
        else:
            diagnostics.append(
                SessionListDiagnostic(
                    code="invalid_session_list_order_result",
                    message="session_list_order must be an object or list.",
                    plugin_id=action.plugin_id,
                    action_id=action.action_id,
                    session_id=session_id,
                )
            )
            return []

        specs: List[_OrderSpec] = []
        for declaration_index, candidate in enumerate(candidates):
            if not isinstance(candidate, dict):
                diagnostics.append(
                    SessionListDiagnostic(
                        code="invalid_session_list_order_spec",
                        message="Ignoring a non-object session-list order specification.",
                        plugin_id=action.plugin_id,
                        action_id=action.action_id,
                        session_id=session_id,
                    )
                )
                continue
            key = candidate.get("key")
            direction = candidate.get("direction")
            raw_priority = candidate.get("priority", 100)
            invalid_reason: Optional[str] = None
            if not isinstance(key, str) or not key:
                invalid_reason = "key must be a non-empty dotted path"
            elif direction not in {"asc", "desc"}:
                invalid_reason = "direction must be asc or desc"
            elif not isinstance(raw_priority, int) or isinstance(raw_priority, bool):
                invalid_reason = "priority must be an integer"

            if invalid_reason is not None:
                diagnostics.append(
                    SessionListDiagnostic(
                        code="invalid_session_list_order_spec",
                        message=f"Ignoring order specification: {invalid_reason}.",
                        plugin_id=action.plugin_id,
                        action_id=action.action_id,
                        session_id=session_id,
                        details={"spec": candidate},
                    )
                )
                continue

            specs.append(
                _OrderSpec(
                    key=cast(str, key),
                    direction=cast(str, direction),
                    has_fallback="fallback" in candidate,
                    fallback=candidate.get("fallback"),
                    priority=raw_priority,
                    plugin_id=action.plugin_id,
                    action_id=action.action_id,
                    plugin_index=action.plugin_index,
                    action_index=action.action_index,
                    declaration_index=declaration_index,
                )
            )
        return specs

    @staticmethod
    def _apply_ordering(
        summaries: List[Dict[str, Any]],
        raw_specs: Sequence[_OrderSpec],
        diagnostics: List[SessionListDiagnostic],
    ) -> List[Dict[str, Any]]:
        ordered = sorted(
            summaries,
            key=lambda summary: _numeric_modified(summary.get("modified")),
            reverse=True,
        )
        if not ordered or not raw_specs:
            return ordered

        specs_by_slot: Dict[Tuple[int, int, int], _OrderSpec] = {}
        for spec in raw_specs:
            existing = specs_by_slot.get(spec.slot)
            if existing is None:
                specs_by_slot[spec.slot] = spec
                continue
            if existing.equivalent_contract(spec):
                continue
            diagnostics.append(
                SessionListDiagnostic(
                    code="conflicting_session_list_order_spec",
                    message="Conflicting order declarations occupied the same plugin slot; the first was used.",
                    plugin_id=spec.plugin_id,
                    action_id=spec.action_id,
                    details={"key": spec.key},
                )
            )

        candidates = sorted(
            specs_by_slot.values(),
            key=lambda spec: (
                spec.priority,
                spec.plugin_index,
                spec.action_index,
                spec.declaration_index,
            ),
        )
        valid: List[Tuple[_OrderSpec, Dict[str, Any]]] = []
        for spec in candidates:
            values_by_session: Dict[str, Any] = {}
            categories: set[str] = set()
            invalid = False
            for summary in ordered:
                resolved = resolve_session_list_path(summary, spec.key)
                if not resolved.found:
                    if not spec.has_fallback:
                        diagnostics.append(
                            SessionListDiagnostic(
                                code="session_list_order_missing_fallback",
                                message="Ignoring order specification because a key is missing and no fallback was declared.",
                                plugin_id=spec.plugin_id,
                                action_id=spec.action_id,
                                details={"key": spec.key},
                            )
                        )
                        invalid = True
                        break
                    value = spec.fallback
                else:
                    value = resolved.value
                category = _sortable_category(value)
                if category is None:
                    diagnostics.append(
                        SessionListDiagnostic(
                            code="session_list_order_value_not_sortable",
                            message="Ignoring order specification with a non-sortable value.",
                            plugin_id=spec.plugin_id,
                            action_id=spec.action_id,
                            details={"key": spec.key},
                        )
                    )
                    invalid = True
                    break
                categories.add(category)
                values_by_session[str(summary.get("session_id") or "")] = value
            if invalid:
                continue
            if len(categories) > 1:
                diagnostics.append(
                    SessionListDiagnostic(
                        code="session_list_order_values_incomparable",
                        message="Ignoring order specification whose values have incompatible types.",
                        plugin_id=spec.plugin_id,
                        action_id=spec.action_id,
                        details={"key": spec.key},
                    )
                )
                continue
            valid.append((spec, values_by_session))

        for spec, values_by_session in reversed(valid):
            ordered.sort(
                key=lambda summary: _sortable_key(
                    values_by_session[str(summary.get("session_id") or "")]
                ),
                reverse=spec.direction == "desc",
            )
        return ordered


def _numeric_modified(value: Any) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return 0.0


def _sortable_category(value: Any) -> Optional[str]:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if isinstance(value, float) and not math.isfinite(value):
            return None
        return "number"
    if isinstance(value, str):
        return "string"
    return None


def _sortable_key(value: Any) -> Any:
    if value is None:
        return 0
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return value


def _stringify_template_value(value: Any) -> str:
    if value is None:
        return ""
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _render_template(template: str, value: Any) -> str:
    text = _stringify_template_value(value)
    return template.replace("{{data}}", text, 1).replace("{{ data }}", text, 1)


def _format_datetime(value: Any) -> Any:
    parsed: Optional[datetime] = None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            parsed = datetime.fromtimestamp(float(value), tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return value
    elif isinstance(value, str) and value:
        try:
            normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            return value
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        parsed = parsed.astimezone(timezone.utc)
    if parsed is None:
        return value
    return parsed.isoformat(timespec="seconds").replace("+00:00", "Z")


def _format_field_value(field: _SessionListField, value: Any) -> Any:
    if field.metadata.get("format") == "datetime":
        return _format_datetime(value)
    return value


def derive_session_list_presentation(
    summary: Dict[str, Any],
    fields: Sequence[_SessionListField],
) -> Dict[str, Any]:
    """Derive title, subtitle, and meta presentation from normalized fields."""

    grouped = {
        "title": sorted(
            (field for field in fields if field.role == "title"),
            key=lambda field: (field.order, field.declaration_index),
        ),
        "subtitle": sorted(
            (field for field in fields if field.role == "subtitle"),
            key=lambda field: (field.order, field.declaration_index),
        ),
        "meta": sorted(
            (field for field in fields if field.role == "meta"),
            key=lambda field: (field.order, field.declaration_index),
        ),
    }

    def first_value(role: str) -> Optional[str]:
        for field in grouped[role]:
            resolved = resolve_session_list_path(summary, field.data)
            if not resolved.found or resolved.value is None or resolved.value == "":
                continue
            text = _render_template(
                field.template,
                _format_field_value(field, resolved.value),
            )
            if text:
                return text
        return None

    title = first_value("title")
    if title is None:
        preview = summary.get("preview")
        if isinstance(preview, str) and preview.strip():
            title = preview
        else:
            session_id = summary.get("session_id")
            prefix = session_id[:8] if isinstance(session_id, str) else ""
            title = f"Session {prefix}"

    meta_parts: List[str] = []
    for field in grouped["meta"]:
        resolved = resolve_session_list_path(summary, field.data)
        if not resolved.found or resolved.value is None or resolved.value == "":
            continue
        text = _render_template(
            field.template,
            _format_field_value(field, resolved.value),
        )
        if text:
            meta_parts.append(text)

    return {
        "title": title,
        "subtitle": first_value("subtitle"),
        "meta": " · ".join(meta_parts) if meta_parts else None,
    }


__all__ = [
    "ResolvedPath",
    "SessionListDiagnostic",
    "SessionListFilterEvaluation",
    "SessionListFilterEvaluator",
    "SessionListService",
    "derive_session_list_presentation",
    "resolve_session_list_path",
]
