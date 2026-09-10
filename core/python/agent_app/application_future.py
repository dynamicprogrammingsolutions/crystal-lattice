from __future__ import annotations

import asyncio
import copy
import concurrent.futures
from dataclasses import dataclass
import hashlib
import json
import inspect
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    cast,
)
import uuid
from contextlib import contextmanager
from datetime import datetime
import os
import threading

from agent_core import AgentCore, Message, ModelDiscoveryCache, Session
from agent_core.plugin.loader import validate_plugin_for_kind
from .app_context import ApplicationContext

from .app_plugins import ApplicationPluginWrapper
from .application_notifications import (
    ApplicationNotificationMutation,
    ApplicationNotificationStore,
)
from .application_owner import ApplicationControl
from .config import (
    build_config_resolution_env,
    build_runtime_overlay_env,
    build_agent_config,
    load_raw_config,
    resolve_config_mixins,
    resolve_placeholders,
    resolve_request_config,
    validate_resolved_config_variants,
)
from .events import EventStore, InMemoryEventStore
from .session_assets import FilesystemSessionAssetStore
from .session_listing import SessionListFilterEvaluator, SessionListService
from .session_request_status import SessionRequestStatusService
from .session_filters import (
    SessionListFilterEngine,
    coerce_session_list_filter_input,
)
from .sessions import (
    FilesystemSessionStore,
    NullSnapshotSelectionStore,
    SessionFileState,
    SessionSnapshotRecord,
    SnapshotSelectionStore,
)
from .tool_loop import RequestCancellation, ToolLoopRunner, ToolLoopCheckpointError
from agent_core.utils import get_logger
from .plugin_manager import PluginManager
from .plugin_sources.types import PluginSource
from .runtime_env import RuntimeEnvOverlay
from .notifications import SessionNotifications
from .operations import get_application_operation_service
from .request_execution import (
    SessionRequestCoordinator,
    SessionRequestResult,
    SessionRequestStart,
)
import weakref


@dataclass(frozen=True)
class _ToolLoopConfig:
    """Configuration for the built-in tool loop.

    Kept aligned with the original application-layer behaviour so that
    implementations can be compared side-by-side with a diff.
    """

    max_loops: int = 100


@dataclass(frozen=True)
class _AgentPluginRuntime:
    """Resolved plugin catalog and default enablement for one agent."""

    plugin_classes: Dict[str, List[type[Any]]]
    plugins_by_kind_and_id: Dict[str, Dict[str, type[Any]]]
    default_enabled_ids: Optional[List[str]]


@dataclass(frozen=True)
class ExecutedAction:
    plugin_id: str
    action_id: str
    action_owner: Optional[str]
    result: Dict[str, Any]


@dataclass(frozen=True)
class _ResolvedActionCandidate:
    plugin_id: str
    action_id: str
    action_owner: str


@dataclass
class _CheckpointBaseline:
    session: Session
    file_state: SessionFileState


class SessionConflictError(RuntimeError):
    def __init__(
        self,
        detail: str,
        *,
        reason: str,
        backup_path: Path | None = None,
    ) -> None:
        super().__init__(detail)
        self.detail = detail
        self.reason = reason
        self.backup_path = backup_path


class ReadonlySessionViewError(RuntimeError):
    """Raised when a mutating operation targets a readonly snapshot view."""


class AsyncRuntimeHost:
    """Application-owned persistent asyncio host for plugin async hooks."""

    def __init__(self) -> None:
        self._thread = threading.Thread(
            target=self._thread_main,
            name="agent-application-async-runtime",
            daemon=True,
        )
        self._loop_ready = threading.Event()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._closed = False
        self._thread.start()
        self._loop_ready.wait()

    def _thread_main(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop
        self._loop_ready.set()
        try:
            loop.run_forever()
        finally:
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            if pending:
                loop.run_until_complete(
                    asyncio.gather(*pending, return_exceptions=True)
                )
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()

    def run_blocking(self, awaitable: Any) -> Any:
        if self._closed:
            raise RuntimeError("AsyncRuntimeHost is closed")
        loop = self._loop
        if loop is None:
            raise RuntimeError("AsyncRuntimeHost loop is not available")
        future = asyncio.run_coroutine_threadsafe(awaitable, loop)
        return future.result()

    async def run_async(self, awaitable: Any) -> Any:
        return await asyncio.wrap_future(self.submit(awaitable))

    def submit(self, awaitable: Any) -> concurrent.futures.Future[Any]:
        if self._closed:
            raise RuntimeError("AsyncRuntimeHost is closed")
        loop = self._loop
        if loop is None:
            raise RuntimeError("AsyncRuntimeHost loop is not available")
        return asyncio.run_coroutine_threadsafe(awaitable, loop)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        loop = self._loop
        if loop is not None:
            loop.call_soon_threadsafe(loop.stop)
        self._thread.join(timeout=5)


class RuntimeStore:
    """Generic application-owned store for opaque long-lived runtime objects."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._values: Dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        if not isinstance(key, str) or not key:
            return default
        with self._lock:
            return self._values.get(key, default)

    def get_or_create(self, key: str, factory: Callable[[], Any]) -> Any:
        if not isinstance(key, str) or not key:
            raise ValueError("key must be a non-empty string")
        with self._lock:
            existing = self._values.get(key)
            if existing is not None:
                return existing
            value = factory()
            self._values[key] = value
            return value

    def set(self, key: str, value: Any) -> None:
        if not isinstance(key, str) or not key:
            raise ValueError("key must be a non-empty string")
        old: Any | None = None
        with self._lock:
            old = self._values.get(key)
            self._values[key] = value
        if old is not None and old is not value:
            self._close_value(old)

    def setdefault(self, key: str, value: Any) -> Any:
        if not isinstance(key, str) or not key:
            raise ValueError("key must be a non-empty string")
        with self._lock:
            return self._values.setdefault(key, value)

    def pop(self, key: str, default: Any = None, *, close: bool = False) -> Any:
        if not isinstance(key, str) or not key:
            return default
        with self._lock:
            value = self._values.pop(key, default)
        if close and value is not default:
            self._close_value(value)
        return value

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._values)

    def clear(self) -> None:
        with self._lock:
            items = list(self._values.values())
            self._values.clear()
        for value in items:
            self._close_value(value)

    def close(self) -> None:
        self.clear()

    @staticmethod
    def _close_value(value: Any) -> None:
        for attr in ("aclose", "close"):
            fn = getattr(value, attr, None)
            if not callable(fn):
                continue
            try:
                result = fn()
                if inspect.isawaitable(result):
                    try:
                        asyncio.run(result)
                    except RuntimeError:
                        with concurrent.futures.ThreadPoolExecutor(
                            max_workers=1
                        ) as executor:
                            executor.submit(asyncio.run, result).result()
            except Exception:
                return
            return


class AgentApplication:
    """Future application-layer API around :class:`agent_core.AgentCore`.

    This variant focuses on the *core-first* architecture used by
    Example 13. It exposes only the typed helpers and the
    :meth:`send_request` event generator.

    The original dict-based HTTP-style API
    (``create_session``, ``add_message``, ``send_request``,
    ``get_events``, ``stream_events``) has been replaced by this
    implementation.

    Structure and helper method names intentionally mirror the original
    application-layer implementation so it can be compared easily.
    """

    _PROTECTED_SESSION_METADATA_KEYS = frozenset(
        {
            "agent_id",
            "plugins",
            "native_messages",
            "native_messages_integrity",
        }
    )
    _MISSING_METADATA = object()
    _SESSION_CONFLICT_REASON_TEXTS = {
        "stored_session_disappeared": "stored session disappeared",
        "session_id_changed": "session id changed",
        "message_count_changed": "message count changed",
        "messages_changed": "messages changed",
        "protected_metadata_changed": "protected metadata changed",
    }

    @staticmethod
    def _core_factory_with_model_cache(
        core_factory: Callable[[], AgentCore],
        model_cache: ModelDiscoveryCache,
    ) -> Callable[[], AgentCore]:
        if core_factory is AgentCore:
            return lambda: AgentCore(model_cache=model_cache)

        try:
            signature = inspect.signature(core_factory)
        except (TypeError, ValueError):
            return core_factory

        for parameter in signature.parameters.values():
            if parameter.kind == inspect.Parameter.VAR_KEYWORD:
                return lambda: core_factory(model_cache=model_cache)  # type: ignore[call-arg]
            if parameter.name == "model_cache":
                return lambda: core_factory(model_cache=model_cache)  # type: ignore[call-arg]

        return core_factory

    def __init__(
        self,
        config_path: str | Path,
        session_root: str | Path,
        core_factory: Callable[[], AgentCore] = AgentCore,
        event_store: Optional[EventStore] = None,
        application_notification_store: ApplicationNotificationStore | None = None,
        snapshot_selection_store: SnapshotSelectionStore | None = None,
        env_overrides: Mapping[str, str] | None = None,
        config_env: Mapping[str, str] | None = None,
        replay_server_settings_on_startup: bool = True,
        application_control: ApplicationControl | None = None,
        notification_owner_epoch: str | None = None,
        plugin_sources: Optional[List[PluginSource]] = None,
    ) -> None:
        logger = get_logger("AgentApplication")
        self._logger = logger
        self._closed = False
        # Core factory is stored so that per-session cores can be created
        # without sharing wrapper/runtime state across requests. Model
        # discovery cache is intentionally shared at the application scope.
        self._model_cache = ModelDiscoveryCache()
        self._core_factory = self._core_factory_with_model_cache(
            core_factory,
            self._model_cache,
        )
        self._event_store: EventStore = event_store or InMemoryEventStore()
        self._application_notification_store = application_notification_store
        self._application_control = application_control
        store_owner_epoch = getattr(
            application_notification_store,
            "owner_epoch",
            None,
        )
        self._notification_owner_epoch = (
            notification_owner_epoch
            if isinstance(notification_owner_epoch, str) and notification_owner_epoch
            else (
                store_owner_epoch
                if isinstance(store_owner_epoch, str) and store_owner_epoch
                else f"owner_{uuid.uuid4().hex}"
            )
        )
        self._non_streaming_provider_classes: Set[type[Any]] = set()
        self._provider_capability_lock = threading.Lock()

        # A single core instance is still used for import/export with the
        # filesystem session store; inference uses fresh cores created via
        # ``_new_core``.
        core = self._core_factory()
        self._core = core

        config_path_resolved = Path(config_path).resolve()
        self._config_path = config_path_resolved
        raw_config = load_raw_config(config_path_resolved)
        self._raw_config: Dict[str, Any] = raw_config
        config_base_dir = str(config_path_resolved.parent)
        resolution_env = build_config_resolution_env(
            config_path,
            env_overrides=env_overrides,
            config_env=config_env,
        )
        resolved_config, placeholder_errors = resolve_placeholders(
            raw_config, env=resolution_env
        )
        mixin_resolved_config, mixin_errors = resolve_config_mixins(resolved_config)
        variant_errors = validate_resolved_config_variants(mixin_resolved_config)
        self._config: Dict[str, Any] = mixin_resolved_config
        self._config_errors: List[Dict[str, Any]] = (
            placeholder_errors + mixin_errors + variant_errors
        )
        self._resolved_env: Dict[str, str] = dict(resolution_env)
        self._runtime_env_overlay = RuntimeEnvOverlay(
            build_runtime_overlay_env(config_path, env_overrides=env_overrides)
        )
        self._runtime_env_overlay.install()
        self._runtime_env_finalizer = weakref.finalize(
            self,
            AgentApplication._release_runtime_env_overlay,
            self._runtime_env_overlay,
        )

        plugin_specs = self._coerce_plugin_specs(
            self._config.get("plugins"),
            "plugins",
            self._config_errors,
        )
        global_disabled_plugins = self._coerce_plugin_ids(
            self._config.get("disabled_plugins"),
            "disabled_plugins",
            self._config_errors,
        )

        plugin_cache_dir = self._config.get("plugin_cache_dir")
        if not (isinstance(plugin_cache_dir, str) and plugin_cache_dir.strip()):
            # Use a deterministic directory near the config so tests and
            # local runs do not write into the developer's home unexpectedly.
            cache_path = Path(config_base_dir) / ".plugin_cache" / "plugins"
        else:
            cache_path = Path(os.path.expanduser(plugin_cache_dir))
            if not cache_path.is_absolute():
                cache_path = Path(config_base_dir) / cache_path

        plugin_policy_in = self._config.get("plugin_policy") or {}
        plugin_policy: Dict[str, Any] = (
            dict(plugin_policy_in) if isinstance(plugin_policy_in, dict) else {}
        )
        plugin_policy.setdefault("base_dir", config_base_dir)
        preinstalled_manifest = self._resolved_env.get(
            "CRYSTAL_PREINSTALLED_PLUGIN_MANIFEST"
        )
        if preinstalled_manifest:
            plugin_policy.setdefault(
                "preinstalled_plugin_manifest", preinstalled_manifest
            )

        mgr = PluginManager(
            cache_dir=cache_path,
            policy=plugin_policy,
            sources=plugin_sources,
        )

        providers_cfg = self._config.get("providers") or {}
        provider_plugin_specs: Dict[str, List[Any]] = {}
        provider_disabled_plugins: Dict[str, List[str]] = {}
        if isinstance(providers_cfg, dict):
            for provider_id, provider_cfg in providers_cfg.items():
                if not isinstance(provider_cfg, dict):
                    continue
                provider_plugin_specs[provider_id] = self._coerce_plugin_specs(
                    provider_cfg.get("plugins"),
                    f"providers.{provider_id}.plugins",
                    self._config_errors,
                )
                provider_disabled_plugins[provider_id] = self._coerce_plugin_ids(
                    provider_cfg.get("disabled_plugins"),
                    f"providers.{provider_id}.disabled_plugins",
                    self._config_errors,
                )

        agents = self._config.get("agents") or {}
        agent_plugin_specs: Dict[str, List[Any]] = {}
        agent_disabled_plugins: Dict[str, List[str]] = {}
        if isinstance(agents, dict):
            for agent_id, agent_cfg in agents.items():
                if not isinstance(agent_cfg, dict):
                    continue
                agent_plugin_specs[agent_id] = self._coerce_plugin_specs(
                    agent_cfg.get("plugins"),
                    f"agents.{agent_id}.plugins",
                    self._config_errors,
                )
                agent_disabled_plugins[agent_id] = self._coerce_plugin_ids(
                    agent_cfg.get("disabled_plugins"),
                    f"agents.{agent_id}.disabled_plugins",
                    self._config_errors,
                )

        spec_resolution_cache: Dict[str, List[type[Any]]] = {}
        app_plugin_classes: List[type[Any]] = []
        all_plugin_classes_by_kind: Dict[str, List[type[Any]]] = {
            "providers": [],
            "features": [],
            "tools": [],
            "extensions": [],
        }

        for spec in self._iter_unique_specs(
            plugin_specs,
            provider_plugin_specs.values(),
            agent_plugin_specs.values(),
        ):
            resolved_classes = self._resolve_plugin_spec_cached(
                mgr,
                spec,
                spec_resolution_cache,
                self._config_errors,
                logger,
            )
            for cls in resolved_classes:
                kind = self._classify_plugin_class(cls)
                if kind == "application":
                    if cls not in app_plugin_classes:
                        app_plugin_classes.append(cls)
                elif kind in all_plugin_classes_by_kind:
                    all_plugin_classes_by_kind[kind].append(cls)
                else:
                    self._config_errors.append(
                        {
                            "type": "plugin_type_unknown",
                            "detail": "Could not classify plugin by duck-typing",
                            "path": f"{getattr(cls, '__module__', '')}.{getattr(cls, '__qualname__', '')}",
                        }
                    )

        self._plugin_classes, self._plugins_by_kind_and_id = (
            self._dedupe_plugin_classes_by_id(all_plugin_classes_by_kind)
        )

        # Manual registration from config on the shared core uses the
        # application-wide deduplicated catalog.
        provider_exts = self._plugin_classes.get("extensions") or []
        for provider_cls in self._plugin_classes.get("providers") or []:
            core.register_provider(provider_cls, extensions=provider_exts)
        for feature_cls in self._plugin_classes.get("features") or []:
            core.register_feature(feature_cls)
        for tool_cls in self._plugin_classes.get("tools") or []:
            core.register_tool(tool_cls)

        # Application-level plugins are configured separately from core
        # provider/feature/tool plugins. They operate on the
        # :class:`AgentApplication` level (sessions, storage, actions).
        self._app_plugin_classes = app_plugin_classes

        self._app_plugins: Dict[str, ApplicationPluginWrapper] = {}
        for plugin_class in self._app_plugin_classes:
            plugin_id = self._plugin_id_for_class(plugin_class)
            # First registration for a given id wins to preserve config order.
            if plugin_id in self._app_plugins:
                continue
            wrapper = ApplicationPluginWrapper(
                plugin_id=plugin_id, plugin_class=plugin_class
            )
            wrapper.init(self._config)
            self._app_plugins[plugin_id] = wrapper

        session_root_path = Path(session_root)
        self._session_store = FilesystemSessionStore(session_root_path, core)
        self._snapshot_selection_store = (
            snapshot_selection_store or NullSnapshotSelectionStore()
        )
        self._session_asset_store = FilesystemSessionAssetStore(
            session_root_path.parent / "session_assets"
        )
        self._runtime_state_root = session_root_path.parent / "runtime"
        self._runtime_state_root.mkdir(parents=True, exist_ok=True)
        self._server_settings_path = self._runtime_state_root / "server_settings.json"
        self._server_settings_lock = threading.RLock()
        self._runtime_store = RuntimeStore()
        self._runtime_store.set("agent_core.model_discovery_cache", self._model_cache)
        self._application_operations = get_application_operation_service(
            self._runtime_store
        )
        self._tool_runtime = self._runtime_store
        self._context = ApplicationContext(
            app=self,
            application=self,
            session_asset_store=self._session_asset_store,
            runtime_state_root=self._runtime_state_root,
            runtime_store=self._runtime_store,
            tool_runtime=self._runtime_store,
        )
        self._session_notifications = SessionNotifications(self)
        application_ref = weakref.ref(self)

        def _require_application() -> "AgentApplication":
            application = application_ref()
            if application is None:
                raise RuntimeError("AgentApplication is no longer available")
            return application

        def _list_session_actions() -> List[Dict[str, Any]]:
            return _require_application().get_application_actions()

        def _list_session_ui_elements() -> List[Dict[str, Any]]:
            return _require_application().get_application_ui_schema()

        def _execute_session_list_action(
            plugin_id: str,
            action_id: str,
            params: Dict[str, Any],
            context: Optional[Dict[str, Any]],
        ) -> Dict[str, Any]:
            return _require_application().execute_application_action(
                plugin_id,
                action_id,
                params,
                context=context,
            )

        self._session_list_filter_engine = SessionListFilterEngine()
        self._session_list_service = SessionListService(
            store=self._session_store,
            list_actions=_list_session_actions,
            list_ui_elements=_list_session_ui_elements,
            execute_action=_execute_session_list_action,
            logger=self._logger,
            filter_evaluator=self._session_list_filter_engine,
        )
        self._async_runtime_host = AsyncRuntimeHost()
        self._tool_loop_cfg = _ToolLoopConfig()
        self._request_cancellations_lock = threading.RLock()
        self._cancelled_requests: set[str] = set()
        self._request_cancellations: Dict[str, RequestCancellation] = {}
        self._session_request_coordinator = SessionRequestCoordinator(
            app=self,
            application_control=self._application_control,
            operations=self._application_operations,
            new_request_id=self._new_request_id,
            logger=self._logger,
        )
        self._session_request_status_service = SessionRequestStatusService(
            store=self._session_store,
            get_active_request_id=self.get_active_session_request_id,
        )

        # Event compaction controls. These are primarily intended for
        # debugging and tests; in normal operation they remain enabled
        # so that HTTP and terminal polling see compacted batches.
        self._enable_event_compaction: bool = True
        self._enable_drop_redundant_partials: bool = True
        self._enable_merge_consecutive_partials: bool = True

        # Cache per-agent base configs and plugin catalogs to avoid recomputing
        # on every call.
        self._agent_base_configs: Dict[str, Dict[str, Any]] = {}
        self._agent_plugin_ids: Dict[str, Optional[List[str]]] = {}
        self._agent_plugin_runtimes: Dict[str, _AgentPluginRuntime] = {}
        for agent_id, agent_cfg in agents.items():
            if not isinstance(agent_cfg, dict):
                continue
            self._agent_base_configs[agent_id] = build_agent_config(
                self._config, agent_id
            )

            provider_name = agent_cfg.get("provider")
            provider_spec_list = (
                provider_plugin_specs.get(provider_name, [])
                if isinstance(provider_name, str)
                else []
            )
            provider_disabled = (
                provider_disabled_plugins.get(provider_name, [])
                if isinstance(provider_name, str)
                else []
            )

            effective_classes_by_kind: Dict[str, List[type[Any]]] = {
                "providers": [],
                "features": [],
                "tools": [],
                "extensions": [],
            }
            for spec in self._iter_specs_in_order(
                plugin_specs,
                provider_spec_list,
                agent_plugin_specs.get(agent_id, []),
            ):
                for cls in self._resolve_plugin_spec_cached(
                    mgr,
                    spec,
                    spec_resolution_cache,
                    self._config_errors,
                    logger,
                ):
                    kind = self._classify_plugin_class(cls)
                    if kind in effective_classes_by_kind:
                        effective_classes_by_kind[kind].append(cls)

            deduped_classes, deduped_by_id = self._dedupe_plugin_classes_by_id(
                effective_classes_by_kind
            )

            # Collect plugins with default_enabled=False (disabled by default)
            plugins_disabled_by_default: Set[str] = set()
            for kind in ("providers", "extensions", "features", "tools"):
                for plugin_cls in deduped_classes.get(kind) or []:
                    plugin_id = self._plugin_id_for_class(plugin_cls)
                    default_enabled_attr = getattr(plugin_cls, "default_enabled", True)
                    if default_enabled_attr is False:
                        plugins_disabled_by_default.add(plugin_id)

            # Get enabled_plugins from agent config (re-enable disabled-by-default plugins)
            agent_enabled_plugins: Set[str] = set(
                self._coerce_plugin_ids(
                    agent_cfg.get("enabled_plugins"),
                    f"agents.{agent_id}.enabled_plugins",
                    self._config_errors,
                )
            )

            disabled_set = set(global_disabled_plugins)
            disabled_set.update(provider_disabled)
            disabled_set.update(agent_disabled_plugins.get(agent_id, []))
            # Add plugins disabled by default, unless explicitly enabled via enabled_plugins
            disabled_set.update(plugins_disabled_by_default - agent_enabled_plugins)

            all_plugin_ids = self._collect_plugin_ids(deduped_by_id)
            default_enabled_ids = [
                pid for pid in all_plugin_ids if pid not in disabled_set
            ]
            if default_enabled_ids == all_plugin_ids:
                default_enabled: Optional[List[str]] = None
            else:
                default_enabled = default_enabled_ids

            runtime = _AgentPluginRuntime(
                plugin_classes=deduped_classes,
                plugins_by_kind_and_id=deduped_by_id,
                default_enabled_ids=default_enabled,
            )
            self._agent_plugin_runtimes[agent_id] = runtime
            self._agent_plugin_ids[agent_id] = runtime.default_enabled_ids

        self._raise_for_fatal_config_errors()
        if replay_server_settings_on_startup:
            self._replay_server_settings_on_startup()

    # ------------------------------------------------------------------
    # Helper methods (kept in the same order as application.AgentApplication)
    # ------------------------------------------------------------------

    @contextmanager
    def acquire_session_lock(self, session_id: str) -> Iterator[None]:
        """Yield under the event store's lock for ``session_id``."""

        with self._event_store.acquire_session_lock(session_id):
            yield

    def _new_request_id(self) -> str:
        return str(uuid.uuid4())

    def _get_agent_base_config(self, agent_id: str) -> Dict[str, Any]:
        cfg = self._agent_base_configs.get(agent_id)
        if cfg is None:
            cfg = build_agent_config(self._config, agent_id)
            self._agent_base_configs[agent_id] = cfg
        return cfg

    @staticmethod
    def _coerce_plugin_specs(
        raw_value: Any,
        path: str,
        errors: List[Dict[str, Any]],
    ) -> List[Any]:
        if raw_value is None:
            return []
        if isinstance(raw_value, list):
            return list(raw_value)
        errors.append(
            {
                "type": "plugin_config_invalid",
                "detail": f"'{path}' should be a list; coerced single value into list",
                "path": path,
            }
        )
        return [raw_value]

    def _raise_for_fatal_config_errors(self) -> None:
        fatal_errors = [
            err
            for err in self._config_errors
            if isinstance(err, dict)
            and (
                str(err.get("type") or "").startswith("plugin_")
                or str(err.get("type") or "").startswith("mixin_")
                or str(err.get("type") or "").startswith("config_merge_")
                or str(err.get("type") or "").startswith("config_variant_")
            )
        ]
        if not fatal_errors:
            return

        details: List[str] = []
        for err in fatal_errors:
            err_type = str(err.get("type") or "plugin_error")
            path = err.get("path")
            detail = err.get("detail")
            parts = [err_type]
            if isinstance(path, str) and path:
                parts.append(path)
            if isinstance(detail, str) and detail:
                parts.append(detail)
            details.append(" - ".join(parts))

        raise RuntimeError(
            "Configuration resolution failed:\n"
            + "\n".join(f"- {item}" for item in details)
        )

    @staticmethod
    def _coerce_plugin_ids(
        raw_value: Any,
        path: str,
        errors: List[Dict[str, Any]],
    ) -> List[str]:
        if raw_value is None:
            return []
        values = raw_value if isinstance(raw_value, list) else [raw_value]
        if not isinstance(raw_value, list):
            errors.append(
                {
                    "type": "plugin_config_invalid",
                    "detail": f"'{path}' should be a list; coerced single value into list",
                    "path": path,
                }
            )
        return [value for value in values if isinstance(value, str) and value]

    @staticmethod
    def _spec_cache_key(spec: Any) -> str:
        if isinstance(spec, str):
            return f"str:{spec}"
        try:
            encoded = json.dumps(spec, sort_keys=True, separators=(",", ":"))
        except Exception:
            encoded = repr(spec)
        return f"json:{encoded}"

    @classmethod
    def _iter_specs_in_order(cls, *spec_lists: List[Any]) -> Iterator[Any]:
        seen: Set[str] = set()
        for spec_list in spec_lists:
            for spec in spec_list:
                cache_key = cls._spec_cache_key(spec)
                if cache_key in seen:
                    continue
                seen.add(cache_key)
                yield spec

    @classmethod
    def _iter_unique_specs(cls, first: List[Any], *rest: Any) -> Iterator[Any]:
        flat_lists: List[List[Any]] = [first]
        for value in rest:
            for spec_list in value:
                flat_lists.append(list(spec_list))
        yield from cls._iter_specs_in_order(*flat_lists)

    def _resolve_plugin_spec_cached(
        self,
        mgr: PluginManager,
        spec: Any,
        cache: Dict[str, List[type[Any]]],
        errors: List[Dict[str, Any]],
        logger: Any,
    ) -> List[type[Any]]:
        cache_key = self._spec_cache_key(spec)
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        resolution = mgr.resolve_all(spec)
        if resolution.errors:
            logger.error("plugin_manager_resolve_errors", errors=resolution.errors)
        errors.extend(resolution.errors)
        cache[cache_key] = list(resolution.classes)
        return cache[cache_key]

    def _dedupe_plugin_classes_by_id(
        self,
        plugin_classes: Dict[str, List[type[Any]]],
    ) -> Tuple[Dict[str, List[type[Any]]], Dict[str, Dict[str, type[Any]]]]:
        deduped_classes: Dict[str, List[type[Any]]] = {}
        deduped_by_id: Dict[str, Dict[str, type[Any]]] = {}
        for kind, classes in plugin_classes.items():
            by_id: Dict[str, type[Any]] = {}
            ordered: List[type[Any]] = []
            for plugin_cls in classes or []:
                plugin_id = self._plugin_id_for_class(plugin_cls)
                if plugin_id in by_id:
                    continue
                by_id[plugin_id] = plugin_cls
                ordered.append(plugin_cls)
            deduped_classes[kind] = ordered
            deduped_by_id[kind] = by_id
        return deduped_classes, deduped_by_id

    @staticmethod
    def _collect_plugin_ids(
        plugins_by_kind_and_id: Dict[str, Dict[str, type[Any]]],
    ) -> List[str]:
        ordered: List[str] = []
        seen: Set[str] = set()
        for kind in ("providers", "extensions", "features", "tools"):
            for plugin_id in (plugins_by_kind_and_id.get(kind) or {}).keys():
                if plugin_id in seen:
                    continue
                seen.add(plugin_id)
                ordered.append(plugin_id)
        return ordered

    def _get_agent_plugin_runtime(self, agent_id: str) -> _AgentPluginRuntime:
        runtime = self._agent_plugin_runtimes.get(agent_id)
        if runtime is None:
            raise KeyError(f"Unknown agent_id {agent_id!r}")
        return runtime

    @staticmethod
    def _is_unknown_agent_error(error: BaseException) -> bool:
        if not isinstance(error, KeyError):
            return False
        if not error.args:
            return False
        detail = error.args[0]
        return isinstance(detail, str) and detail.startswith("Unknown agent_id")

    def _configured_agent_plugin_ids(self, agent_id: str) -> Optional[List[str]]:
        agents = self._config.get("agents") if isinstance(self._config, dict) else {}
        agent_cfg = agents.get(agent_id) if isinstance(agents, dict) else None
        if not isinstance(agent_cfg, dict):
            return None

        raw_plugins = agent_cfg.get("plugins")
        if not isinstance(raw_plugins, list):
            return None

        known_ids = set(
            self._collect_plugin_ids(
                self._get_agent_plugin_runtime(agent_id).plugins_by_kind_and_id
            )
        )
        configured_ids = [
            item for item in raw_plugins if isinstance(item, str) and item in known_ids
        ]
        return configured_ids or None

    def _plugin_id_for_class(self, plugin_class: type[Any]) -> str:
        """Return the stable plugin id for a plugin class.

        Uses the class-level ``name`` attribute when present, falling back
        to the class name. This matches the identity used by the core and
        the terminal application.
        """

        plugin_id = getattr(plugin_class, "name", None)
        if not isinstance(plugin_id, str) or not plugin_id:
            plugin_id = plugin_class.__name__
        return plugin_id

    def _classify_plugin_class(self, plugin_class: type[Any]) -> Optional[str]:
        """Return a plugin kind for the class via duck-typing.

        Kinds are checked in priority order so providers/tools/extensions do not
        accidentally get classified as features.
        """

        for kind in ("providers", "tools", "extensions", "application", "features"):
            if validate_plugin_for_kind(plugin_class, kind) is None:
                return kind
        return None

    def _build_core_with_enabled_ids(
        self,
        enabled_ids: Optional[List[str]],
        selected_provider_config: Optional[Dict[str, Any]] = None,
        plugins_by_kind_and_id: Optional[Dict[str, Dict[str, type[Any]]]] = None,
    ) -> AgentCore:
        """Construct a fresh AgentCore with only selected plugins enabled.

        When ``enabled_ids`` is ``None``, all available plugins are
        registered. Unknown plugin ids are ignored.

        Raises:
            RuntimeError: If no provider plugins are enabled.
        """

        core = self._core_factory()

        enabled_set: Optional[Set[str]]
        if enabled_ids is None:
            enabled_set = None
        else:
            enabled_set = {p for p in enabled_ids if isinstance(p, str)}

        catalog = plugins_by_kind_and_id or self._plugins_by_kind_and_id

        def _filter_plugins(kind: str) -> List[type[Any]]:
            all_for_kind = catalog.get(kind, {})
            if enabled_set is None:
                return list(all_for_kind.values())
            return [cls for pid, cls in all_for_kind.items() if pid in enabled_set]

        enabled_providers = _filter_plugins("providers")
        if not enabled_providers:
            raise RuntimeError("No provider plugins enabled")

        if isinstance(selected_provider_config, dict):
            selected_provider = self._resolve_provider_class_for_config(
                enabled_providers,
                selected_provider_config,
            )
            enabled_providers = [selected_provider]

        enabled_extensions = _filter_plugins("extensions")
        enabled_features = _filter_plugins("features")
        enabled_tools = _filter_plugins("tools")

        for provider_cls in enabled_providers:
            core.register_provider(provider_cls, extensions=enabled_extensions)
        for feature_cls in enabled_features:
            core.register_feature(feature_cls)
        for tool_cls in enabled_tools:
            core.register_tool(tool_cls)

        return core

    def _new_core(self) -> AgentCore:
        """Construct a fresh :class:`AgentCore` instance with all plugins.

        This mirrors the original application-layer implementation but is
        used exclusively by the typed helpers and the new request API in
        this module.
        """

        return self._build_core_with_enabled_ids(None)

    def _provider_class_for_request(
        self,
        session: Session,
        config: Dict[str, Any],
    ) -> Optional[type[Any]]:
        agent_id = None
        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        raw_agent_id = metadata.get("agent_id") if isinstance(metadata, dict) else None
        if isinstance(raw_agent_id, str) and raw_agent_id in self._agent_base_configs:
            agent_id = raw_agent_id

        if agent_id is not None:
            provider_classes = list(
                (
                    self._get_agent_plugin_runtime(agent_id).plugin_classes.get(
                        "providers"
                    )
                    or []
                )
            )
        else:
            provider_classes = list(self._plugin_classes.get("providers") or [])

        if not provider_classes:
            return None
        return self._resolve_provider_class_for_config(provider_classes, config)

    def _provider_supports_streaming(self, provider_class: Optional[type[Any]]) -> bool:
        if provider_class is None:
            return True
        with self._provider_capability_lock:
            return provider_class not in self._non_streaming_provider_classes

    def _mark_provider_non_streaming(self, provider_class: Optional[type[Any]]) -> None:
        if provider_class is None:
            return
        with self._provider_capability_lock:
            self._non_streaming_provider_classes.add(provider_class)

    def _resolve_request_stream_mode(
        self,
        *,
        requested_stream: bool,
        config: Dict[str, Any],
        provider_class: Optional[type[Any]],
    ) -> bool:
        if not requested_stream:
            return False

        config_stream = config.get("stream")
        if isinstance(config_stream, bool) and config_stream is False:
            return False

        if not self._provider_supports_streaming(provider_class):
            return False

        return True

    def _provider_identities_for_class(self, provider_class: type[Any]) -> List[str]:
        names: List[str] = []

        raw_names: List[Any] = [
            getattr(provider_class, "name", None),
            getattr(provider_class, "__name__", None),
            getattr(provider_class, "__qualname__", None),
        ]
        for value in raw_names:
            if isinstance(value, str) and value:
                names.append(value)

        module = getattr(provider_class, "__module__", None)
        if isinstance(module, str) and module:
            class_names: List[str] = []
            qual = getattr(provider_class, "__qualname__", "") or ""
            if qual:
                class_names.append(qual)
            cls_name = getattr(provider_class, "__name__", "") or ""
            if cls_name and cls_name not in class_names:
                class_names.append(cls_name)
            cfg_name = getattr(provider_class, "name", None)
            if isinstance(cfg_name, str) and cfg_name and cfg_name not in class_names:
                class_names.append(cfg_name)
            for class_name in class_names:
                names.append(f"{module}.{class_name}")

        seen: Set[str] = set()
        unique: List[str] = []
        for name in names:
            if name not in seen:
                seen.add(name)
                unique.append(name)
        return unique

    def _resolve_provider_class_for_config(
        self,
        provider_classes: List[type[Any]],
        config: Dict[str, Any],
    ) -> type[Any]:
        if len(provider_classes) == 1 and "provider" not in config:
            return provider_classes[0]

        provider_value = config.get("provider")
        identity_map: Dict[str, List[type[Any]]] = {}
        for provider_class in provider_classes:
            for ident in self._provider_identities_for_class(provider_class):
                identity_map.setdefault(ident, []).append(provider_class)

        def _format_available() -> str:
            items: List[str] = []
            for provider_class in provider_classes:
                idents = self._provider_identities_for_class(provider_class)
                if not idents:
                    continue
                primary = idents[0]
                extras = [ident for ident in idents[1:] if ident != primary]
                if extras:
                    items.append(f"{primary} (also: {', '.join(extras)})")
                else:
                    items.append(primary)
            return ", ".join(items)

        if not isinstance(provider_value, str) or not provider_value.strip():
            raise RuntimeError(
                "Configuration must include a non-empty 'provider' string when multiple provider "
                "plugins are enabled. Known providers: "
                f"{_format_available()}"
            )

        provider_key = provider_value.strip()
        matches = identity_map.get(provider_key, [])
        if not matches:
            raise RuntimeError(
                f"Unknown provider '{provider_key}' in configuration. Known providers: "
                f"{_format_available()}"
            )

        if len(matches) > 1:
            suggestions: List[str] = []
            for provider_class in matches:
                idents = self._provider_identities_for_class(provider_class)
                fq = next(
                    (ident for ident in idents if "." in ident),
                    idents[0] if idents else "",
                )
                if fq:
                    suggestions.append(fq)
            suggestions_str = ", ".join(sorted(set(suggestions)))
            raise RuntimeError(
                f"Ambiguous provider name '{provider_key}' in configuration; it matches multiple "
                "enabled provider plugins. Please choose a more specific value, for example one of: "
                f"{suggestions_str}"
            )

        return matches[0]

    def _effective_overrides(
        self,
        session_metadata: Dict[str, Any],
        overrides: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        stored_raw = session_metadata.get("overrides")
        stored = stored_raw if isinstance(stored_raw, dict) else {}
        if not isinstance(overrides, dict) or not overrides:
            return stored
        if not stored:
            return overrides
        return {**stored, **overrides}

    def _enabled_plugin_ids_for_session(
        self,
        agent_id: str,
        session_metadata: Dict[str, Any],
    ) -> Optional[List[str]]:
        plugins_from_session = session_metadata.get("plugins")
        if isinstance(plugins_from_session, list):
            return [p for p in plugins_from_session if isinstance(p, str)]
        return self._agent_plugin_ids.get(agent_id)

    def _resolve_runtime_for_session(
        self,
        session: Session,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> Tuple[AgentCore, Dict[str, Any], Dict[str, Any]]:
        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        agent_id = metadata.get("agent_id")
        if not isinstance(agent_id, str) or not agent_id:
            raise RuntimeError("session.metadata must contain non-empty 'agent_id'")

        base_cfg = self._get_agent_base_config(agent_id)
        plugin_runtime = self._get_agent_plugin_runtime(agent_id)
        enabled_ids = self._enabled_plugin_ids_for_session(agent_id, metadata)
        effective_overrides = self._effective_overrides(metadata, overrides)
        effective_config = resolve_request_config(base_cfg, effective_overrides)
        core = self._build_core_with_enabled_ids(
            enabled_ids,
            selected_provider_config=effective_config,
            plugins_by_kind_and_id=plugin_runtime.plugins_by_kind_and_id,
        )
        return core, base_cfg, effective_config

    def resolve_effective_config(
        self,
        base_config: Dict[str, Any],
        session: Session,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        effective_overrides = self._effective_overrides(metadata, overrides)
        return resolve_request_config(base_config, effective_overrides)

    @staticmethod
    def _session_messages_digest(session: Session) -> str:
        return AgentApplication._messages_digest(session.messages)

    @staticmethod
    def _messages_digest(messages: Sequence[Message]) -> str:
        payload = json.dumps(
            [message.to_dict() for message in messages],
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    @classmethod
    def _protected_session_metadata(cls, session: Session) -> Dict[str, Any]:
        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        return {
            key: value
            for key, value in metadata.items()
            if key in cls._PROTECTED_SESSION_METADATA_KEYS
        }

    @classmethod
    def _merge_non_protected_session_metadata(
        cls,
        *,
        baseline_session: Session,
        stored_session: Session,
        current_session: Session,
    ) -> Dict[str, Any]:
        baseline_metadata = (
            dict(baseline_session.metadata)
            if isinstance(baseline_session.metadata, dict)
            else {}
        )
        stored_metadata = (
            dict(stored_session.metadata)
            if isinstance(stored_session.metadata, dict)
            else {}
        )
        current_metadata = (
            dict(current_session.metadata)
            if isinstance(current_session.metadata, dict)
            else {}
        )

        merged_metadata = dict(current_metadata)
        all_keys = set(baseline_metadata) | set(stored_metadata) | set(current_metadata)
        for key in all_keys:
            if key in cls._PROTECTED_SESSION_METADATA_KEYS:
                continue

            baseline_value = baseline_metadata.get(key, cls._MISSING_METADATA)
            stored_value = stored_metadata.get(key, cls._MISSING_METADATA)

            if stored_value != baseline_value:
                if stored_value is cls._MISSING_METADATA:
                    merged_metadata.pop(key, None)
                else:
                    merged_metadata[key] = stored_value

        return merged_metadata

    def _merge_session_if_compatible(
        self,
        *,
        baseline_session: Session,
        stored_session: Session,
        current_session: Session,
    ) -> Session:
        if stored_session.session_id != baseline_session.session_id:
            raise ValueError("session_id_changed")

        if len(stored_session.messages) != len(baseline_session.messages):
            raise ValueError("message_count_changed")

        if self._session_messages_digest(
            stored_session
        ) != self._session_messages_digest(baseline_session):
            raise ValueError("messages_changed")

        if self._protected_session_metadata(
            stored_session
        ) != self._protected_session_metadata(baseline_session):
            raise ValueError("protected_metadata_changed")

        merged_metadata = self._merge_non_protected_session_metadata(
            baseline_session=baseline_session,
            stored_session=stored_session,
            current_session=current_session,
        )
        return Session(
            session_id=current_session.session_id,
            messages=current_session.messages,
            metadata=merged_metadata,
        )

    def _reconcile_session_with_store(
        self,
        *,
        baseline_session: Session,
        baseline_file_state: SessionFileState | None,
        current_session: Session,
        persist_on_success: bool,
        conflict_prefix: str | None = None,
        backup_on_conflict: bool = False,
        conflict_request_id: str | None = None,
    ) -> tuple[Session, _CheckpointBaseline | None]:
        current_state = self._session_store.get_file_state(current_session.session_id)

        try:
            if baseline_file_state is not None and current_state == baseline_file_state:
                if not persist_on_success:
                    return current_session, _CheckpointBaseline(
                        session=baseline_session,
                        file_state=baseline_file_state,
                    )

                persisted = self._save_session_low_level(current_session)
                saved_state = self._session_store.get_file_state(
                    current_session.session_id
                )
                return persisted, _CheckpointBaseline(
                    session=persisted,
                    file_state=saved_state,
                )

            if not current_state.exists:
                if not persist_on_success:
                    return current_session, None

                persisted = self._save_session_low_level(current_session)
                saved_state = self._session_store.get_file_state(
                    current_session.session_id
                )
                return persisted, _CheckpointBaseline(
                    session=persisted,
                    file_state=saved_state,
                )

            stored_session = self.load_session_record(current_session.session_id)
            if stored_session is None:
                raise ValueError("stored_session_disappeared")

            merged_session = self._merge_session_if_compatible(
                baseline_session=baseline_session,
                stored_session=stored_session,
                current_session=current_session,
            )

            if not persist_on_success:
                return merged_session, _CheckpointBaseline(
                    session=stored_session,
                    file_state=current_state,
                )

            persisted = self._save_session_low_level(merged_session)
            saved_state = self._session_store.get_file_state(merged_session.session_id)
            return persisted, _CheckpointBaseline(
                session=persisted,
                file_state=saved_state,
            )
        except ValueError as exc:
            if conflict_prefix is None:
                raise
            backup_path: Path | None = None
            if backup_on_conflict:
                backup_path = self._save_session_conflict_backup(
                    current_session,
                    request_id=conflict_request_id or self._new_request_id(),
                )
            suffix = self._SESSION_CONFLICT_REASON_TEXTS.get(
                str(exc),
                str(exc).replace("_", " "),
            )
            detail = f"{conflict_prefix}{suffix}."
            if backup_path is not None:
                detail = f"{detail} Backup saved to {backup_path}"
            raise SessionConflictError(
                detail,
                reason=str(exc),
                backup_path=backup_path,
            ) from exc

    def _save_session_conflict_backup(
        self,
        session: Session,
        *,
        request_id: str,
    ) -> Path:
        return self._session_store.save_backup(session, request_id=request_id)

    @staticmethod
    def _action_matches_trigger(action: Dict[str, Any], lifecycle: str) -> bool:
        trigger_val = action.get("trigger")
        if isinstance(trigger_val, str):
            return trigger_val == lifecycle
        if isinstance(trigger_val, list):
            return any(
                isinstance(item, str) and item == lifecycle for item in trigger_val
            )
        return False

    @staticmethod
    def _ensure_serializable_context(
        context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if context is None:
            return {}
        if not isinstance(context, dict):
            raise TypeError("context must be a mapping")
        try:
            json.dumps(context)
        except Exception as exc:
            raise TypeError("context must be JSON-serializable") from exc
        return dict(context)

    def _build_lifecycle_context(
        self,
        lifecycle: str,
        session: Session,
        config: Dict[str, Any],
        extra_context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        context = self._ensure_serializable_context(extra_context)
        return self._context.build_lifecycle_context(
            lifecycle=lifecycle,
            session=session,
            config=config,
            base_config=self._config,
            extra=context,
        )

    @staticmethod
    def _session_from_result_value(value: Any) -> Optional[Session]:
        if isinstance(value, Session):
            return value
        if isinstance(value, dict):
            try:
                return Session.from_dict(value)
            except Exception:
                return None
        return None

    def _apply_lifecycle_result(
        self,
        session: Session,
        result: Dict[str, Any],
    ) -> Session:
        next_session = self._session_from_result_value(result.get("session")) or session

        metadata_patch_raw = result.get("session_metadata")
        metadata_patch = (
            metadata_patch_raw if isinstance(metadata_patch_raw, dict) else {}
        )

        overrides_patch_raw = result.get("session_overrides")
        overrides_patch = (
            overrides_patch_raw if isinstance(overrides_patch_raw, dict) else {}
        )

        if not metadata_patch and not overrides_patch:
            return next_session

        metadata = (
            dict(next_session.metadata)
            if isinstance(next_session.metadata, dict)
            else {}
        )
        metadata.update(metadata_patch)

        if overrides_patch:
            stored_overrides = metadata.get("overrides")
            normalized_overrides = (
                stored_overrides if isinstance(stored_overrides, dict) else {}
            )
            metadata["overrides"] = {**normalized_overrides, **overrides_patch}

        return Session(
            session_id=next_session.session_id,
            messages=next_session.messages,
            metadata=metadata,
        )

    def run_session_lifecycle(
        self,
        lifecycle: str,
        session: Session,
        *,
        core: Optional[AgentCore] = None,
        base_config: Optional[Dict[str, Any]] = None,
        overrides: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[AgentCore, Dict[str, Any], Session, List[Dict[str, Any]]]:
        if not isinstance(lifecycle, str) or not lifecycle:
            raise ValueError("lifecycle must be a non-empty string")

        current_session = session
        if core is None or base_config is None:
            core, base_config, effective_config = self._resolve_runtime_for_session(
                current_session,
                overrides,
            )
        else:
            effective_config = self.resolve_effective_config(
                base_config,
                current_session,
                overrides,
            )

        results: List[Dict[str, Any]] = []

        for action in self.get_application_actions():
            if not isinstance(action, dict) or not self._action_matches_trigger(
                action, lifecycle
            ):
                continue
            plugin_id = action.get("plugin")
            action_id = action.get("id")
            if not isinstance(plugin_id, str) or not isinstance(action_id, str):
                continue

            action_context = self._build_lifecycle_context(
                lifecycle,
                current_session,
                effective_config,
                context,
            )
            result = self.execute_application_action(
                plugin_id,
                action_id,
                {},
                context=action_context,
            )
            results.append(
                {
                    "plugin": plugin_id,
                    "action_id": action_id,
                    "action_owner": "application",
                    "result": result,
                }
            )
            current_session = self._apply_lifecycle_result(current_session, result)
            core, base_config, effective_config = self._resolve_runtime_for_session(
                current_session,
                overrides,
            )

        current_session, core_results = core.execute_lifecycle_actions(
            current_session,
            effective_config,
            lifecycle,
            context=self.build_core_handoff_context(
                base_config=self._config,
                extra=context,
            ),
        )
        results.extend(core_results)
        core, base_config, _ = self._resolve_runtime_for_session(
            current_session, overrides
        )
        return core, base_config, current_session, results

    def _build_application_lifecycle_context(
        self,
        lifecycle: str,
        extra_context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        context = self._ensure_serializable_context(extra_context)
        return self._context.build_application_lifecycle_context(
            lifecycle=lifecycle,
            config=self._config,
            extra=context,
        )

    def run_application_lifecycle(
        self,
        lifecycle: str,
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        if not isinstance(lifecycle, str) or not lifecycle:
            raise ValueError("lifecycle must be a non-empty string")

        results: List[Dict[str, Any]] = []
        for action in self.get_application_actions():
            if not isinstance(action, dict) or not self._action_matches_trigger(
                action, lifecycle
            ):
                continue
            plugin_id = action.get("plugin")
            action_id = action.get("id")
            if not isinstance(plugin_id, str) or not isinstance(action_id, str):
                continue

            action_context = self._build_application_lifecycle_context(
                lifecycle,
                context,
            )
            result = self.execute_application_action(
                plugin_id,
                action_id,
                {},
                context=action_context,
            )
            results.append(
                {
                    "plugin": plugin_id,
                    "action_id": action_id,
                    "action_owner": "application",
                    "result": result,
                }
            )
        return results

    @staticmethod
    def _normalized_settings(value: Any) -> Dict[str, Any]:
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _validate_settings_updates(updates: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(updates, dict):
            raise ValueError("settings updates must be a mapping")
        for key in updates.keys():
            if not isinstance(key, str) or not key:
                raise ValueError("settings keys must be non-empty strings")
        try:
            json.dumps(updates)
        except Exception as exc:
            raise ValueError("settings values must be JSON-serializable") from exc
        return dict(updates)

    @staticmethod
    def _changed_setting_keys(
        old_settings: Dict[str, Any],
        new_settings: Dict[str, Any],
    ) -> List[str]:
        keys = set(old_settings) | set(new_settings)
        return sorted(
            key
            for key in keys
            if old_settings.get(key, AgentApplication._MISSING_METADATA)
            != new_settings.get(key, AgentApplication._MISSING_METADATA)
        )

    def _read_server_settings_unlocked(self) -> Dict[str, Any]:
        path = self._server_settings_path
        if not path.exists():
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        settings = payload.get("settings") if isinstance(payload, dict) else None
        return dict(settings) if isinstance(settings, dict) else {}

    def _write_server_settings_unlocked(self, settings: Dict[str, Any]) -> None:
        payload = {"settings": dict(settings)}
        tmp_path = self._server_settings_path.with_suffix(
            self._server_settings_path.suffix + ".tmp"
        )
        tmp_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        tmp_path.replace(self._server_settings_path)

    def get_server_settings(self) -> Dict[str, Any]:
        with self._server_settings_lock:
            return self._read_server_settings_unlocked()

    def patch_server_settings(
        self,
        updates: Dict[str, Any],
        *,
        source: str = "api",
    ) -> Dict[str, Any]:
        normalized_updates = self._validate_settings_updates(updates)
        with self._server_settings_lock:
            old_settings = self._read_server_settings_unlocked()
            new_settings = {**old_settings, **normalized_updates}
            changed_keys = self._changed_setting_keys(old_settings, new_settings)
            if not changed_keys:
                return new_settings
            self._write_server_settings_unlocked(new_settings)

        self.run_application_lifecycle(
            "server_settings_changed",
            context={
                "scope": "server",
                "old_settings": old_settings,
                "new_settings": new_settings,
                "changed_keys": changed_keys,
                "source": source,
            },
        )
        return new_settings

    def delete_server_setting(
        self,
        key: str,
        *,
        source: str = "api",
    ) -> Dict[str, Any]:
        if not isinstance(key, str) or not key:
            raise ValueError("key must be a non-empty string")
        with self._server_settings_lock:
            old_settings = self._read_server_settings_unlocked()
            if key not in old_settings:
                return old_settings
            new_settings = dict(old_settings)
            new_settings.pop(key, None)
            changed_keys = [key]
            self._write_server_settings_unlocked(new_settings)

        self.run_application_lifecycle(
            "server_settings_changed",
            context={
                "scope": "server",
                "old_settings": old_settings,
                "new_settings": new_settings,
                "changed_keys": changed_keys,
                "source": source,
            },
        )
        return new_settings

    def _replay_server_settings_on_startup(self) -> None:
        settings = self.get_server_settings()
        if not settings:
            return
        self.run_application_lifecycle(
            "server_settings_changed",
            context={
                "scope": "server",
                "old_settings": {},
                "new_settings": settings,
                "changed_keys": sorted(settings.keys()),
                "source": "startup",
            },
        )

    def get_session_settings(self, session_id: str) -> Dict[str, Any]:
        ctx = self.load_session(session_id)
        if ctx is None:
            raise KeyError(f"Session {session_id!r} not found")
        _core, _base_config, session = ctx
        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        return dict(self._normalized_settings(metadata.get("overrides")))

    def patch_session_settings(
        self,
        session_id: str,
        updates: Dict[str, Any],
        *,
        source: str = "api",
    ) -> Session:
        normalized_updates = self._validate_settings_updates(updates)
        with self.acquire_session_lock(session_id):
            ctx = self.load_session(session_id)
            if ctx is None:
                raise KeyError(f"Session {session_id!r} not found")

            core, base_config, session = ctx
            metadata = session.metadata if isinstance(session.metadata, dict) else {}
            old_settings = dict(self._normalized_settings(metadata.get("overrides")))
            new_settings = {**old_settings, **normalized_updates}
            changed_keys = self._changed_setting_keys(old_settings, new_settings)
            if not changed_keys:
                return session

            updated = Session(
                session_id=session.session_id,
                messages=session.messages,
                metadata={**metadata, "overrides": new_settings},
            )
            saved = self.save_session(updated)
            core, base_config, saved, _results = self.run_session_lifecycle(
                "session_settings_changed",
                saved,
                core=core,
                base_config=base_config,
                context={
                    "scope": "session",
                    "old_settings": old_settings,
                    "new_settings": new_settings,
                    "changed_keys": changed_keys,
                    "source": source,
                },
            )
            return self.save_session(saved)

    def delete_session_setting(
        self,
        session_id: str,
        key: str,
        *,
        source: str = "api",
    ) -> Session:
        if not isinstance(key, str) or not key:
            raise ValueError("key must be a non-empty string")
        with self.acquire_session_lock(session_id):
            ctx = self.load_session(session_id)
            if ctx is None:
                raise KeyError(f"Session {session_id!r} not found")

            core, base_config, session = ctx
            metadata = session.metadata if isinstance(session.metadata, dict) else {}
            old_settings = dict(self._normalized_settings(metadata.get("overrides")))
            if key not in old_settings:
                return session

            new_settings = dict(old_settings)
            new_settings.pop(key, None)
            new_metadata = dict(metadata)
            if new_settings:
                new_metadata["overrides"] = new_settings
            else:
                new_metadata.pop("overrides", None)

            updated = Session(
                session_id=session.session_id,
                messages=session.messages,
                metadata=new_metadata,
            )
            saved = self.save_session(updated)
            core, base_config, saved, _results = self.run_session_lifecycle(
                "session_settings_changed",
                saved,
                core=core,
                base_config=base_config,
                context={
                    "scope": "session",
                    "old_settings": old_settings,
                    "new_settings": new_settings,
                    "changed_keys": [key],
                    "source": source,
                },
            )
            return self.save_session(saved)

    def _load_session_required(self, session_id: str) -> Session:
        session = self._session_store.load(session_id)
        if session is None:
            raise KeyError(f"Session {session_id!r} not found")
        return session

    def _extract_tool_calls(
        self, messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        tool_calls: List[Dict[str, Any]] = []
        for msg in messages:
            if msg.get("role") != "assistant":
                continue
            metadata = msg.get("metadata") or {}
            calls = metadata.get("tool_calls") or []
            if isinstance(calls, list):
                tool_calls.extend([c for c in calls if isinstance(c, dict)])
        return tool_calls

    def _extract_pending_tool_calls_from_session(
        self, session: Session
    ) -> List[Dict[str, Any]]:
        """Return tool_calls from the last assistant message, if not yet answered.

        A simple heuristic is used: if there is any tool message after the last
        assistant-with-tool_calls, we treat the calls as already handled.
        """

        last_tc_index: Optional[int] = None
        last_tc_calls: List[Dict[str, Any]] = []

        for idx, message in enumerate(session.messages):
            if message.role != "assistant":
                continue
            metadata = message.metadata or {}
            calls = metadata.get("tool_calls") or []
            if isinstance(calls, list) and calls:
                last_tc_index = idx
                last_tc_calls = [c for c in calls if isinstance(c, dict)]

        if last_tc_index is None or not last_tc_calls:
            return []

        # If there is any tool message after this index, assume the calls have
        # already been processed.
        for msg in session.messages[last_tc_index + 1 :]:
            if msg.role == "tool":
                return []

        return last_tc_calls

    # ------------------------------------------------------------------
    # Public helpers for tests / applications (manual registration)
    # ------------------------------------------------------------------

    def register_provider(
        self, plugin_class: type, extensions: Optional[List[type]] = None
    ) -> None:
        self._core.register_provider(plugin_class, extensions=extensions or [])

    def register_feature(self, plugin_class: type) -> None:
        self._core.register_feature(plugin_class)

    def register_tool(self, plugin_class: type) -> None:
        self._core.register_tool(plugin_class)

    # ------------------------------------------------------------------
    # Typed helpers for applications (core-first API)
    # ------------------------------------------------------------------

    def get_config_errors(self) -> List[Dict[str, Any]]:
        """Return configuration and plugin loading errors captured at startup.

        This accessor is useful in tests or diagnostics to surface
        placeholder resolution problems and plugin loader errors
        (e.g., invalid local paths or import failures).

        Example:
            >>> app = AgentApplication("config.json", "./sessions")
            >>> for err in app.get_config_errors():
            ...     print(err.get("type"), err.get("detail"))

        See also:
            - application/python/docs/configuration.md (Troubleshooting)
        """

        return list(self._config_errors)

    def get_event_store(self) -> EventStore:
        """Return the configured event store for this application."""

        return self._event_store

    def compact_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Return a compacted view of ``events``.

        This helper removes redundant assistant partials before ``final`` and
        non-terminal tool start/stream partials before ``tool_results`` for
        the same ``session_id``/``request_id`` pair within one batch.
        ``tool_partial`` events with ``phase == "end"`` are preserved because
        they carry the final display-aware result used by renderers. The
        underlying event store is not modified, and kept-event order is
        preserved.
        """

        if not events or not self._enable_event_compaction:
            return events

        # ------------------------------------------------------------------
        # Pass 1: drop redundant partials that precede terminal events
        # ------------------------------------------------------------------

        if self._enable_drop_redundant_partials:
            keep_flags: List[bool] = [True] * len(events)
            seen_final: Dict[Tuple[Optional[str], Optional[str]], bool] = {}
            seen_tool_results: Dict[Tuple[Optional[str], Optional[str]], bool] = {}

            for idx in range(len(events) - 1, -1, -1):
                ev = events[idx]
                etype = ev.get("type")
                session_id = ev.get("session_id")
                request_id = ev.get("request_id")
                key = (session_id, request_id)

                if etype == "final":
                    seen_final[key] = True
                    keep_flags[idx] = True
                elif etype == "tool_results":
                    seen_tool_results[key] = True
                    keep_flags[idx] = True
                elif etype == "partial":
                    if seen_final.get(key):
                        keep_flags[idx] = False
                    else:
                        keep_flags[idx] = True
                elif etype == "tool_partial":
                    if seen_tool_results.get(key) and ev.get("phase") != "end":
                        keep_flags[idx] = False
                    else:
                        keep_flags[idx] = True
                else:
                    keep_flags[idx] = True

            if all(keep_flags):
                dropped = events
            else:
                dropped = [ev for idx, ev in enumerate(events) if keep_flags[idx]]
        else:
            dropped = events

        # ------------------------------------------------------------------
        # Pass 2: merge consecutive partial/tool_partial events where possible
        # ------------------------------------------------------------------

        def _merge_two(
            a: Dict[str, Any], b: Dict[str, Any]
        ) -> Optional[Dict[str, Any]]:
            """Return a merged event for ``a`` and ``b`` or ``None``.

            Only consecutive events of type ``partial`` or
            ``tool_partial`` with matching ``session_id`` and
            ``request_id`` are considered for merging.
            """

            atype = a.get("type")
            btype = b.get("type")
            if atype != btype:
                return None

            session_id_a = a.get("session_id")
            session_id_b = b.get("session_id")
            request_id_a = a.get("request_id")
            request_id_b = b.get("request_id")
            if session_id_a != session_id_b or request_id_a != request_id_b:
                return None

            if atype == "partial":
                msg_a = a.get("message") or {}
                msg_b = b.get("message") or {}
                if not isinstance(msg_a, dict) or not isinstance(msg_b, dict):
                    return None

                md_a = msg_a.get("metadata") or {}
                md_b = msg_b.get("metadata") or {}
                if not isinstance(md_a, dict) or not isinstance(md_b, dict):
                    md_a = {}
                    md_b = {}

                reasoning_a = md_a.get("reasoning")
                reasoning_b = md_b.get("reasoning")
                content_a = msg_a.get("content")
                content_b = msg_b.get("content")

                has_reasoning = isinstance(reasoning_a, str) or isinstance(
                    reasoning_b, str
                )
                has_content = isinstance(content_a, str) or isinstance(content_b, str)
                if not (has_reasoning or has_content):
                    return None

                merged_event = dict(b)
                merged_msg = dict(msg_b)
                merged_md = dict(md_b)

                if has_reasoning:
                    ra = reasoning_a if isinstance(reasoning_a, str) else ""
                    rb = reasoning_b if isinstance(reasoning_b, str) else ""
                    merged_md["reasoning"] = ra + rb

                if has_content:
                    ca = content_a if isinstance(content_a, str) else ""
                    cb = content_b if isinstance(content_b, str) else ""
                    merged_msg["content"] = ca + cb

                merged_msg["metadata"] = merged_md
                merged_event["message"] = merged_msg
                return merged_event

            if atype == "tool_partial":
                # Tool partials stream tool output via payload.part.
                tool_id_a = a.get("tool_call_id")
                tool_id_b = b.get("tool_call_id")
                if tool_id_a != tool_id_b:
                    return None

                phase_a = a.get("phase")
                phase_b = b.get("phase")
                # Do not merge "end" events carrying the final result.
                if phase_a == "end" or phase_b == "end":
                    return None

                payload_a = a.get("payload") or {}
                payload_b = b.get("payload") or {}
                if not isinstance(payload_a, dict) or not isinstance(payload_b, dict):
                    return None

                part_a = payload_a.get("part")
                part_b = payload_b.get("part")
                if not (isinstance(part_a, str) or isinstance(part_b, str)):
                    return None

                merged_event = dict(b)
                merged_payload = dict(payload_b)
                pa = part_a if isinstance(part_a, str) else ""
                pb = part_b if isinstance(part_b, str) else ""
                merged_payload["part"] = pa + pb
                merged_event["payload"] = merged_payload
                return merged_event

            return None

        if not self._enable_merge_consecutive_partials:
            return dropped

        merged: List[Dict[str, Any]] = []
        current: Optional[Dict[str, Any]] = None

        for ev in dropped:
            if current is None:
                current = ev
                continue

            combined = _merge_two(current, ev)
            if combined is not None:
                current = combined
            else:
                merged.append(current)
                current = ev

        if current is not None:
            merged.append(current)

        return merged

    def advance_session_cursor(self, session_id: str, event_id: str) -> None:
        """Advance the per-session event cursor to ``event_id``.

        The cursor represents the latest event id whose effects are
        known to be reflected in the persisted session state for the
        given ``session_id``.
        """

        self._event_store.advance_session_cursor(session_id, event_id)

    def get_session_cursor_event_id(self, session_id: str) -> Optional[str]:
        """Return the latest cursor event id for ``session_id``."""
        return self._event_store.get_session_cursor_event_id(session_id)

    # Backwards-compatible alias; prefer get_session_cursor_event_id.
    def get_checkpoint_event_id(self, session_id: str) -> Optional[str]:
        return self.get_session_cursor_event_id(session_id)

    def record_checkpoint(
        self,
        session_id: str,
        request_id: Optional[str],
    ) -> Optional[str]:
        """Publish a lightweight checkpoint marker for ``session_id``.

        The marker is written to the shared event store and the session
        cursor is advanced to the checkpoint event's own ``event_id``.
        """

        marker = self._event_store.publish(
            {
                "type": "checkpoint",
                "session_id": session_id,
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        )
        marker_id = marker.get("event_id")
        if isinstance(marker_id, str):
            self.advance_session_cursor(session_id, marker_id)
            return marker_id
        return None

    def publish_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Publish an event to the underlying event store.

        This helper is intentionally low-level: it does not emit
        checkpoint markers or advance session cursors. Callers that
        need to track persistence boundaries should combine this with
        :meth:`record_checkpoint` or :meth:`advance_session_cursor` as
        appropriate.
        """

        stored = self._event_store.publish(event)
        return stored

    def get_application_config(self) -> Dict[str, Any]:
        """Return application-level configuration section.

        This helper exposes the top-level "application" config subtree used
        for frontend-specific settings such as rendering limits.
        """

        cfg = self._config if isinstance(self._config, dict) else {}
        raw_app_cfg = (
            cfg.get("application") if isinstance(cfg.get("application"), dict) else {}
        )
        return cast(Dict[str, Any], raw_app_cfg)

    def get_config_path(self) -> Path:
        """Return the path of the configuration file used by this application."""

        return self._config_path

    def get_raw_config(self) -> Dict[str, Any]:
        """Return the unresolved top-level configuration mapping.

        The raw config is useful for tools that need to preserve placeholders
        such as ``${env:...}`` and ``${file:...}`` when producing derived
        configuration artifacts.
        """

        return cast(Dict[str, Any], copy.deepcopy(self._raw_config))

    def get_resolved_env(self) -> Dict[str, str]:
        """Return the runtime env mapping used for config placeholder resolution."""

        return dict(self._resolved_env)

    @staticmethod
    def _release_runtime_env_overlay(overlay: RuntimeEnvOverlay) -> None:
        overlay.close()

    def close(self) -> None:
        """Release plugin and process-global runtime resources owned by this app."""

        if self._closed:
            return
        self._closed = True
        self._session_request_coordinator.close()

        for wrapper in list(self._app_plugins.values()):
            try:
                wrapper.close()
            except Exception as exc:  # pragma: no cover - defensive cleanup
                self._logger.warning(
                    "application_plugin_close_failed",
                    plugin_id=wrapper.plugin_id,
                    error=str(exc),
                )
        self._runtime_store.close()
        self._async_runtime_host.close()
        if self._runtime_env_finalizer.alive:
            self._runtime_env_finalizer()

    def request_application_reload(
        self,
        *,
        reason: str = "application_action",
        on_failure: Callable[[], None] | None = None,
    ) -> Dict[str, Any]:
        if self._application_control is None:
            raise RuntimeError("Application reload is not managed by an owner")
        return self._application_control.request_reload(
            reason=reason,
            on_failure=on_failure,
        )

    def create_session_notification(
        self,
        session_id: str,
        notification: Dict[str, Any],
        *,
        request_id: str | None = None,
    ) -> Dict[str, Any]:
        return self._session_notifications.create(
            session_id, notification, request_id=request_id
        )

    def update_session_notification(
        self,
        session_id: str,
        notification_id: str,
        patch: Dict[str, Any],
        *,
        request_id: str | None = None,
        expected_revision: int | str | None = None,
    ) -> Dict[str, Any]:
        return self._session_notifications.update(
            session_id,
            notification_id,
            patch,
            request_id=request_id,
            expected_revision=expected_revision,
        )

    def update_session_notification_by_key(
        self,
        session_id: str,
        key: str,
        patch: Dict[str, Any],
        *,
        request_id: str | None = None,
        expected_revision: int | str | None = None,
    ) -> Dict[str, Any]:
        return self._session_notifications.update_by_key(
            session_id,
            key,
            patch,
            request_id=request_id,
            expected_revision=expected_revision,
        )

    def resolve_session_notification(
        self,
        session_id: str,
        notification_id: str,
        resolution: Dict[str, Any],
        *,
        request_id: str | None = None,
        expected_revision: int | str | None = None,
    ) -> Dict[str, Any]:
        return self._session_notifications.resolve(
            session_id,
            notification_id,
            resolution,
            request_id=request_id,
            expected_revision=expected_revision,
        )

    def dismiss_session_notification(
        self,
        session_id: str,
        notification_id: str,
        *,
        reason: str | None = None,
        request_id: str | None = None,
        expected_revision: int | str | None = None,
    ) -> Dict[str, Any]:
        return self._session_notifications.dismiss(
            session_id,
            notification_id,
            reason=reason,
            request_id=request_id,
            expected_revision=expected_revision,
        )

    def expire_session_notification(
        self,
        session_id: str,
        notification_id: str,
        *,
        reason: str = "expired",
        request_id: str | None = None,
        expected_revision: int | str | None = None,
    ) -> Dict[str, Any]:
        return self._session_notifications.expire(
            session_id,
            notification_id,
            reason=reason,
            request_id=request_id,
            expected_revision=expected_revision,
        )

    def list_session_notifications(
        self,
        session_id: str,
        *,
        include_resolved: bool = False,
        include_terminal: bool | None = None,
    ) -> list[Dict[str, Any]]:
        return self._session_notifications.list(
            session_id,
            include_resolved=include_resolved,
            include_terminal=include_terminal,
        )

    def create_application_notification(
        self,
        notification: Dict[str, Any],
        *,
        request_id: str | None = None,
    ) -> Dict[str, Any]:
        store = self._require_application_notification_store()
        prepared_notification = notification
        retention = notification.get("retention")
        if (
            isinstance(retention, dict)
            and retention.get("policy") == "until_server_restart"
            and not retention.get("owner_epoch")
        ):
            prepared_notification = {
                **notification,
                "retention": {
                    **retention,
                    "owner_epoch": self._notification_owner_epoch,
                },
            }
        return self._complete_application_notification_mutation(
            store.create(
                prepared_notification,
                request_id=request_id,
                history_limit=self._notification_history_limit(),
            )
        )

    def update_application_notification(
        self,
        notification_id: str,
        patch: Dict[str, Any],
        *,
        expected_revision: int | str | None = None,
    ) -> Dict[str, Any]:
        store = self._require_application_notification_store()
        return self._complete_application_notification_mutation(
            store.update(
                notification_id,
                patch,
                expected_revision=expected_revision,
                history_limit=self._notification_history_limit(),
            )
        )

    def resolve_application_notification(
        self,
        notification_id: str,
        resolution: Dict[str, Any] | None = None,
        *,
        expected_revision: int | str | None = None,
    ) -> Dict[str, Any]:
        store = self._require_application_notification_store()
        return self._complete_application_notification_mutation(
            store.resolve(
                notification_id,
                resolution or {},
                expected_revision=expected_revision,
                history_limit=self._notification_history_limit(),
            )
        )

    def dismiss_application_notification(
        self,
        notification_id: str,
        *,
        reason: str | None = None,
        expected_revision: int | str | None = None,
    ) -> Dict[str, Any]:
        store = self._require_application_notification_store()
        return self._complete_application_notification_mutation(
            store.dismiss(
                notification_id,
                reason=reason,
                expected_revision=expected_revision,
                history_limit=self._notification_history_limit(),
            )
        )

    def expire_application_notification(
        self,
        notification_id: str,
        *,
        reason: str = "expired",
        expected_revision: int | str | None = None,
    ) -> Dict[str, Any]:
        store = self._require_application_notification_store()
        return self._complete_application_notification_mutation(
            store.expire(
                notification_id,
                reason=reason,
                expected_revision=expected_revision,
                history_limit=self._notification_history_limit(),
            )
        )

    def list_application_notifications(
        self,
        *,
        include_terminal: bool = True,
    ) -> list[Dict[str, Any]]:
        return self._require_application_notification_store().list(
            include_terminal=include_terminal
        )

    def recover_session_notification_owner_lifetime(
        self,
        session_id: str,
    ) -> list[Dict[str, Any]]:
        return self._session_notifications.recover_owner_lifetime(session_id)

    def _notification_history_limit(self) -> int:
        application = self.get_application_config()
        notifications = (
            application.get("notifications") if isinstance(application, dict) else None
        )
        if not isinstance(notifications, dict):
            return 500
        value = notifications.get(
            "history_limit",
            notifications.get("max_items", 500),
        )
        return (
            value
            if isinstance(value, int) and not isinstance(value, bool) and value > 0
            else 500
        )

    def _expire_request_notifications(
        self,
        session_id: str,
        request_id: str,
    ) -> None:
        try:
            self._session_notifications.expire_request(session_id, request_id)
        except Exception as exc:
            self._logger.warning(
                "session_request_notification_expiration_failed",
                session_id=session_id,
                request_id=request_id,
                error=str(exc),
            )
        try:
            mutations = self._require_application_notification_store().expire_request(
                request_id,
                history_limit=self._notification_history_limit(),
            )
        except Exception as exc:
            self._logger.warning(
                "application_request_notification_expiration_failed",
                request_id=request_id,
                error=str(exc),
            )
            return
        for mutation in mutations:
            self._complete_application_notification_mutation(mutation)

    def _require_application_notification_store(
        self,
    ) -> ApplicationNotificationStore:
        store = self._application_notification_store
        if store is None:
            raise RuntimeError(
                "Application notifications require an injected notification store"
            )
        return store

    def _complete_application_notification_mutation(
        self,
        mutation: ApplicationNotificationMutation,
    ) -> Dict[str, Any]:
        if mutation.event_type is not None:
            try:
                self._event_store.publish(
                    {
                        "type": mutation.event_type,
                        "notification": mutation.notification,
                    }
                )
            except Exception:
                # Durable state remains authoritative when best-effort event
                # publication is unavailable.
                pass
        return mutation.notification

    def cancel_request(self, request_id: str) -> None:
        """Request cooperative cancellation for an in-flight request.

        Cancellation is best-effort and affects only send_request calls that
        observe this ``request_id``. Providers and tool loops must periodically
        check for cancellation; long-running non-streaming calls may not stop
        immediately.
        """

        if not isinstance(request_id, str) or not request_id:
            raise ValueError("request_id must be a non-empty string")

        with self._request_cancellations_lock:
            self._cancelled_requests.add(request_id)
            cancellation = self._request_cancellations.get(request_id)
        if cancellation is not None:
            cancellation.cancel()

    def _register_request_cancellation(
        self,
        request_id: str,
    ) -> RequestCancellation:
        """Atomically register live cancellation after honoring early requests."""

        with self._request_cancellations_lock:
            cancellation = RequestCancellation(
                cancelled=request_id in self._cancelled_requests
            )
            self._request_cancellations[request_id] = cancellation
            return cancellation

    def _clear_request_cancellation(self, request_id: str) -> None:
        with self._request_cancellations_lock:
            self._cancelled_requests.discard(request_id)
            self._request_cancellations.pop(request_id, None)

    def start_session_request(
        self,
        session_id: str,
        overrides: Optional[Dict[str, Any]] = None,
        *,
        stream: bool = True,
    ) -> SessionRequestStart:
        """Start a coordinated request without appending a message."""

        return self._session_request_coordinator.start(
            session_id,
            overrides,
            stream=stream,
        )

    def start_session_request_with_message(
        self,
        session_id: str,
        *,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        multipart_content: Optional[List[Dict[str, Any]]] = None,
        overrides: Optional[Dict[str, Any]] = None,
        stream: bool = True,
    ) -> SessionRequestStart:
        """Atomically append one message and start a coordinated request."""

        return self._session_request_coordinator.start(
            session_id,
            overrides,
            stream=stream,
            message={
                "role": role,
                "content": content,
                "metadata": metadata,
                "multipart_content": multipart_content,
            },
        )

    def run_session_request(
        self,
        session_id: str,
        overrides: Optional[Dict[str, Any]] = None,
        *,
        stream: bool = True,
        on_checkpoint: Callable[[Session], None] | None = None,
    ) -> SessionRequestResult:
        """Run a coordinated request synchronously."""

        return self._session_request_coordinator.run(
            session_id,
            overrides,
            stream=stream,
            on_checkpoint=on_checkpoint,
        )

    def get_active_session_request_id(self, session_id: str) -> str | None:
        """Return the active coordinated request id for one session."""

        return self._session_request_coordinator.get_active_request_id(session_id)

    def get_session_request_statuses(
        self,
        session_ids: Sequence[str],
    ) -> Dict[str, Any]:
        """Return derived status for explicitly requested sessions."""

        snapshot = self._session_request_status_service.query(session_ids)
        return {
            "version": 1,
            "authority": "derived_transient",
            "statuses": [status.to_dict() for status in snapshot.statuses],
            "missing_session_ids": list(snapshot.missing_session_ids),
        }

    def list_agents(self) -> List[str]:
        """Return the configured agent identifiers.

        The list is derived from the resolved configuration and sorted
        for stable ordering.
        """

        return sorted(self._agent_base_configs.keys())

    def get_agent_plugins(self, agent_id: str) -> Optional[List[str]]:
        """Return the default enabled plugin id list for an agent.

        Returns the default enabled plugin ids after applying merged
        config-layer plugin catalogs and ``disabled_plugins`` filtering,
        or ``None`` to indicate that all plugins in the agent's resolved
        catalog are enabled by default.
        """

        if not isinstance(agent_id, str) or not agent_id:
            raise ValueError("agent_id must be a non-empty string")
        if agent_id not in self._agent_base_configs:
            raise KeyError(f"Unknown agent_id {agent_id!r}")

        value = self._agent_plugin_ids.get(agent_id)
        return value if value is not None else None

    def list_plugins_for_agent(self, agent_id: str) -> List[Dict[str, Any]]:
        """Return metadata for the resolved plugin catalog of ``agent_id``."""

        if not isinstance(agent_id, str) or not agent_id:
            raise ValueError("agent_id must be a non-empty string")
        runtime = self._get_agent_plugin_runtime(agent_id)

        result: List[Dict[str, Any]] = []
        for kind in ("providers", "extensions", "features", "tools"):
            for plugin_class in runtime.plugin_classes.get(kind) or []:
                plugin_id = self._plugin_id_for_class(plugin_class)
                result.append(
                    {
                        "kind": kind,
                        "id": plugin_id,
                        "class_path": f"{plugin_class.__module__}.{plugin_class.__qualname__}",
                    }
                )
        return result

    def list_plugins(self) -> List[Dict[str, Any]]:
        """Return metadata for all available plugins.

        Entries are ordered by kind and then by configuration order.
        """

        result: List[Dict[str, Any]] = []
        for kind in ("providers", "extensions", "features", "tools"):
            for plugin_class in self._plugin_classes.get(kind) or []:
                plugin_id = self._plugin_id_for_class(plugin_class)
                entry: Dict[str, Any] = {
                    "kind": kind,
                    "id": plugin_id,
                    "class_path": f"{plugin_class.__module__}.{plugin_class.__qualname__}",
                    "class_name": plugin_class.__name__,
                }
                name_attr = getattr(plugin_class, "name", None)
                if isinstance(name_attr, str) and name_attr:
                    entry["name"] = name_attr
                result.append(entry)
        return result

    # ------------------------------------------------------------------
    # Application-level plugins (actions + UI schema)
    # ------------------------------------------------------------------

    def list_application_plugins(self) -> List[Dict[str, Any]]:
        """Return metadata for all registered application-level plugins.

        Entries are ordered by configuration order.
        """

        result: List[Dict[str, Any]] = []
        for plugin_id, wrapper in self._app_plugins.items():
            plugin_class = wrapper.plugin_class
            entry: Dict[str, Any] = {
                "id": plugin_id,
                "class_path": f"{plugin_class.__module__}.{plugin_class.__qualname__}",
                "class_name": plugin_class.__name__,
            }
            name_attr = getattr(plugin_class, "name", None)
            if isinstance(name_attr, str) and name_attr:
                entry["name"] = name_attr
            result.append(entry)
        return result

    def get_application_actions(self) -> List[Dict[str, Any]]:
        """Return all application-level action definitions.

        Each returned action dictionary includes a ``"plugin"`` field naming
        the contributing plugin.
        """

        actions: List[Dict[str, Any]] = []
        for plugin_id, wrapper in self._app_plugins.items():
            for raw_action in wrapper.get_actions():
                if not isinstance(raw_action, dict):
                    continue
                if "plugin" in raw_action and isinstance(raw_action["plugin"], str):
                    actions.append(raw_action)
                else:
                    action = dict(raw_action)
                    action["plugin"] = plugin_id
                    actions.append(action)
        return actions

    def get_application_ui_schema(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Return flattened UI schema elements from application plugins.

        Each element is normalized to include a ``"plugin"`` field naming
        the contributing plugin. Optional config/tags/models are passed
        through so plugins can return config-aware UI. Additional context is
        delivered through the shared application context channel.
        """

        safe_config: Dict[str, Any] = dict(config or {})
        safe_tags: List[str] = list(tags or [])
        safe_models: List[Dict[str, Any]] = [
            dict(model) for model in (models or []) if isinstance(model, Mapping)
        ]
        ui_context_name = "application"
        if isinstance(context, Mapping) and isinstance(context.get("ui_context"), str):
            ui_context_name = cast(str, context["ui_context"])
        application_context = self._context.build_application_ui_context(
            ui_context=ui_context_name,
            config=safe_config,
            tags=safe_tags,
            models=safe_models,
            server_settings=self.get_server_settings(),
            extra=context,
        )

        elements: List[Dict[str, Any]] = []
        for plugin_id, wrapper in self._app_plugins.items():
            for raw_element in wrapper.get_ui_elements(
                config=safe_config,
                context=application_context,
            ):
                if not isinstance(raw_element, dict):
                    continue
                if "plugin" in raw_element and isinstance(raw_element["plugin"], str):
                    elements.append(raw_element)
                else:
                    element = dict(raw_element)
                    element["plugin"] = plugin_id
                    elements.append(element)
        return elements

    @staticmethod
    def _resolve_ui_tags_and_models(
        core: AgentCore,
        config: Dict[str, Any],
    ) -> Tuple[List[str], List[Dict[str, Any]]]:
        tags: List[str] = []
        models: List[Dict[str, Any]] = []
        try:
            if hasattr(core, "_resolve_plugins_for_config"):
                provider, _, _, _, resolved_tags = core._resolve_plugins_for_config(
                    config
                )
                tags = list(resolved_tags or [])
                if provider is not None and hasattr(core, "_get_models_for_config"):
                    raw_models = core._get_models_for_config(provider, config)
                    models = [
                        dict(model)
                        for model in (raw_models or [])
                        if isinstance(model, Mapping)
                    ]
        except Exception:
            return [], []
        return tags, models

    def get_session_application_ui_schema_for_session(
        self,
        core: AgentCore,
        base_config: Dict[str, Any],
        session: Session,
        *,
        plugin: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Return application UI schema for an already-loaded session."""

        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        overrides = metadata.get("overrides")
        if not isinstance(overrides, dict):
            overrides = {}
        effective_config = resolve_request_config(base_config, overrides)
        tags, models = self._resolve_ui_tags_and_models(core, effective_config)

        try:
            elements = self.get_application_ui_schema(
                config=effective_config,
                tags=tags,
                models=models,
                context={
                    "ui_context": "session",
                    "session": session.to_dict(),
                    "session_id": session.session_id,
                    "base_config": base_config,
                },
            )
        except Exception as exc:  # pragma: no cover - defensive
            self._logger.exception(
                "error getting application_ui_schema", error=str(exc)
            )
            elements = []

        if plugin:
            return [
                element
                for element in elements
                if isinstance(element, dict) and element.get("plugin") == plugin
            ]
        return [element for element in elements if isinstance(element, dict)]

    def get_session_application_ui_schema(
        self,
        session_id: str,
        *,
        plugin: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Return application UI schema for a persisted session id."""

        ctx = self.load_session(session_id)
        if ctx is None:
            raise KeyError(f"Session {session_id!r} not found")
        core, base_config, session = ctx
        return self.get_session_application_ui_schema_for_session(
            core,
            base_config,
            session,
            plugin=plugin,
        )

    def get_server_settings_ui_schema(self) -> List[Dict[str, Any]]:
        """Return application UI schema elements for server settings surfaces."""

        settings = self.get_server_settings()
        return self.get_application_ui_schema(
            config={},
            tags=[],
            models=[],
            context={
                "ui_context": "server_settings",
                "settings_scope": "server",
                "settings": settings,
                "server_settings": settings,
            },
        )

    def get_application_commands(self) -> List[Dict[str, Any]]:
        """Return flattened command bindings from application plugins.

        Each returned command dictionary includes a ``"plugin"`` field naming
        the contributing plugin. Commands are frontend-facing bindings onto
        existing application actions rather than a second executable surface.
        """

        commands: List[Dict[str, Any]] = []
        for plugin_id, wrapper in self._app_plugins.items():
            for raw_command in wrapper.get_commands():
                if not isinstance(raw_command, dict):
                    continue
                if "plugin" in raw_command and isinstance(raw_command["plugin"], str):
                    commands.append(raw_command)
                else:
                    command = dict(raw_command)
                    command["plugin"] = plugin_id
                    commands.append(command)
        return commands

    # Internal helpers for action validation ---------------------------------

    class _ApplicationActionValidationError(Exception):
        """Internal exception used for application action input validation.

        Carries a ``details`` mapping suitable for surfacing in higher-level
        error envelopes.
        """

        def __init__(
            self, message: str, details: Optional[Dict[str, Any]] = None
        ) -> None:
            super().__init__(message)
            self.details: Dict[str, Any] = details or {}

    class _ApplicationActionResolutionError(Exception):
        """Internal exception used for action-id-only resolution errors."""

        def __init__(
            self,
            error_type: str,
            message: str,
            details: Optional[Dict[str, Any]] = None,
        ) -> None:
            super().__init__(message)
            self.error_type = error_type
            self.details: Dict[str, Any] = details or {}

    def _find_application_action_definition(
        self,
        plugin_id: str,
        action_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Return the action definition for ``(plugin_id, action_id)`` if present."""

        for action in self.get_application_actions():
            if not isinstance(action, dict):
                continue
            if action.get("plugin") == plugin_id and action.get("id") == action_id:
                return action
        return None

    def _action_session_id(
        self,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> Optional[str]:
        session_id = params.get("session_id") if isinstance(params, dict) else None
        if isinstance(session_id, str) and session_id:
            return session_id
        if isinstance(context, dict):
            context_session_id = context.get("session_id")
            if isinstance(context_session_id, str) and context_session_id:
                return context_session_id
        return None

    def _session_action_definitions(self, session_id: str) -> List[Dict[str, Any]]:
        ctx = self.load_session(session_id)
        if ctx is None:
            raise KeyError(f"Session {session_id!r} not found")
        core, base_config, session = ctx
        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        overrides = metadata.get("overrides")
        if not isinstance(overrides, dict):
            overrides = {}
        effective_config = self.resolve_effective_config(
            base_config, session, overrides
        )
        return core.get_session_actions(effective_config)

    def _application_action_candidates(
        self,
        action_id: str,
    ) -> List[_ResolvedActionCandidate]:
        candidates: List[_ResolvedActionCandidate] = []
        seen: set[Tuple[str, str, str]] = set()
        for action in self.get_application_actions():
            if not isinstance(action, dict) or action.get("id") != action_id:
                continue
            plugin = action.get("plugin")
            if not isinstance(plugin, str) or not plugin:
                continue
            key = (plugin, action_id, "application")
            if key in seen:
                continue
            seen.add(key)
            candidates.append(
                _ResolvedActionCandidate(
                    plugin_id=plugin,
                    action_id=action_id,
                    action_owner="application",
                )
            )
        return candidates

    def _session_action_candidates(
        self,
        session_id: str,
        action_id: str,
        *,
        action_owner: Optional[str] = None,
    ) -> List[_ResolvedActionCandidate]:
        candidates: List[_ResolvedActionCandidate] = []
        seen: set[Tuple[str, str, str]] = set()
        for action in self._session_action_definitions(session_id):
            if not isinstance(action, dict) or action.get("id") != action_id:
                continue
            owner = action.get("action_owner")
            if not isinstance(owner, str) or not owner:
                owner = "provider_extension"
            if action_owner is not None and owner != action_owner:
                continue
            plugin = action.get("plugin")
            if not isinstance(plugin, str) or not plugin:
                continue
            key = (plugin, action_id, owner)
            if key in seen:
                continue
            seen.add(key)
            candidates.append(
                _ResolvedActionCandidate(
                    plugin_id=plugin,
                    action_id=action_id,
                    action_owner=owner,
                )
            )
        return candidates

    def _candidate_to_details(
        self,
        candidate: _ResolvedActionCandidate,
    ) -> Dict[str, Any]:
        return {
            "plugin": candidate.plugin_id,
            "action_id": candidate.action_id,
            "action_owner": candidate.action_owner,
        }

    def _resolve_action_candidate(
        self,
        plugin_id: Optional[str],
        action_id: str,
        params: Dict[str, Any],
        *,
        action_owner: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> _ResolvedActionCandidate:
        if not isinstance(action_id, str) or not action_id:
            raise ValueError("action_id must be a non-empty string")
        if not isinstance(params, dict):
            raise ValueError("params must be a mapping of action inputs")

        session_id = self._action_session_id(params, context)

        if plugin_id is not None:
            if not isinstance(plugin_id, str) or not plugin_id:
                raise ValueError("plugin_id must be a non-empty string")
            if action_owner == "application":
                return _ResolvedActionCandidate(plugin_id, action_id, "application")
            if action_owner in {"provider_extension", "feature"}:
                return _ResolvedActionCandidate(plugin_id, action_id, action_owner)
            if (
                self._find_application_action_definition(plugin_id, action_id)
                is not None
            ):
                return _ResolvedActionCandidate(plugin_id, action_id, "application")
            if session_id is not None:
                for candidate in self._session_action_candidates(session_id, action_id):
                    if candidate.plugin_id == plugin_id:
                        return candidate
            return _ResolvedActionCandidate(plugin_id, action_id, "application")

        candidates: List[_ResolvedActionCandidate] = []
        if action_owner in {None, "application"}:
            candidates.extend(self._application_action_candidates(action_id))

        if session_id is not None and action_owner in {
            None,
            "provider_extension",
            "feature",
        }:
            candidates.extend(
                self._session_action_candidates(
                    session_id,
                    action_id,
                    action_owner=action_owner,
                )
            )

        if not candidates:
            raise self._ApplicationActionResolutionError(
                "unknown_action",
                f"Unknown action_id {action_id!r}",
                {"action_id": action_id},
            )

        if len(candidates) > 1:
            raise self._ApplicationActionResolutionError(
                "ambiguous_action",
                f"Ambiguous action_id {action_id!r}",
                {
                    "action_id": action_id,
                    "candidates": [
                        self._candidate_to_details(candidate)
                        for candidate in candidates
                    ],
                },
            )

        return candidates[0]

    def resolve_application_action_plugin_id(self, action_id: str) -> str:
        """Resolve an application action id to a unique contributing plugin id."""

        candidate = self._resolve_action_candidate(
            None,
            action_id,
            {},
            action_owner="application",
        )
        return candidate.plugin_id

    @staticmethod
    def _action_param_type_matches(value: Any, expected_type: str) -> bool:
        """Return True when ``value`` matches the declared primitive type.

        Supported types are ``string``, ``integer``, ``number``, and
        ``boolean``. Unknown types are treated as "accept any" so that
        application plugins can experiment with richer parameter types
        without breaking validation.
        """

        if expected_type == "string":
            return isinstance(value, str)
        if expected_type == "integer":
            # ``bool`` is a subclass of ``int``; treat it separately.
            return isinstance(value, int) and not isinstance(value, bool)
        if expected_type == "number":
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        if expected_type == "boolean":
            return isinstance(value, bool)
        return True

    def _validate_action_inputs(
        self,
        action_def: Dict[str, Any],
        raw_inputs: Any,
    ) -> Dict[str, Any]:
        """Validate and normalize inputs for an application-level action.

        Returns the validated mapping or raises
        :class:`_ApplicationActionValidationError`.
        """

        schema = action_def.get("inputs") or {}
        if not isinstance(schema, dict):
            schema = {}

        if raw_inputs is None:
            inputs: Dict[str, Any] = {}
        elif isinstance(raw_inputs, dict):
            inputs = raw_inputs
        else:
            raise self._ApplicationActionValidationError(
                "inputs must be an object mapping parameter names to values",
                {"reason": "inputs_type", "actual_type": type(raw_inputs).__name__},
            )

        validated: Dict[str, Any] = {}
        missing: List[str] = []
        invalid_types: Dict[str, Dict[str, Any]] = {}

        for name, spec in schema.items():
            if not isinstance(spec, dict):
                continue

            param_type = spec.get("type")
            required = bool(spec.get("required", False))
            has_value = name in inputs
            value = inputs.get(name)

            if not has_value or value is None:
                if "default" in spec:
                    validated[name] = spec["default"]
                elif required:
                    missing.append(name)
                continue

            if isinstance(param_type, str):
                if not self._action_param_type_matches(value, param_type):
                    invalid_types[name] = {
                        "expected": param_type,
                        "actual_type": type(value).__name__,
                    }
                else:
                    validated[name] = value
            else:
                validated[name] = value

        extra = [name for name in inputs.keys() if name not in schema]

        if missing or invalid_types or extra:
            details: Dict[str, Any] = {}
            if missing:
                details["missing_params"] = missing
            if invalid_types:
                details["invalid_types"] = invalid_types
            if extra:
                details["extra_params"] = extra

            raise self._ApplicationActionValidationError(
                "action input validation failed", details
            )

        return validated

    def execute_application_action(
        self,
        plugin_id: str,
        action_id: str,
        params: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute an application-level action.

        This helper validates that the plugin, action id, and inputs are
        valid and then delegates execution to the corresponding application
        plugin wrapper.
        """

        if not isinstance(plugin_id, str) or not plugin_id:
            raise ValueError("plugin_id must be a non-empty string")
        if not isinstance(action_id, str) or not action_id:
            raise ValueError("action_id must be a non-empty string")
        if not isinstance(params, dict):
            raise ValueError("params must be a mapping of action inputs")

        wrapper = self._app_plugins.get(plugin_id)
        if wrapper is None:
            raise KeyError(f"Unknown application plugin {plugin_id!r}")

        action_def = self._find_application_action_definition(plugin_id, action_id)
        if action_def is None:
            raise KeyError(f"Unknown action_id {action_id!r} for plugin {plugin_id!r}")

        validated_inputs = self._validate_action_inputs(action_def, params)

        return wrapper.execute_action(
            self, action_id, validated_inputs, context=context
        )

    def execute_session_action(
        self,
        plugin_id: str,
        action_id: str,
        params: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a provider-extension session action via the core layer."""

        if not isinstance(plugin_id, str) or not plugin_id:
            raise ValueError("plugin_id must be a non-empty string")
        if not isinstance(action_id, str) or not action_id:
            raise ValueError("action_id must be a non-empty string")
        if not isinstance(params, dict):
            raise ValueError("params must be a mapping of action inputs")

        session_id = params.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            if isinstance(context, dict):
                session_id = context.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id must be a non-empty string")

        action_params = dict(params)
        action_params.pop("session_id", None)

        with self.acquire_session_lock(session_id):
            ctx = self.load_session(session_id)
            if ctx is None:
                raise KeyError(f"Session {session_id!r} not found")
            core, base_config, session = ctx
            baseline_file_state = self.get_session_file_state(session_id)

        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        overrides = metadata.get("overrides")
        if not isinstance(overrides, dict):
            overrides = {}
        effective_config = self.resolve_effective_config(
            base_config, session, overrides
        )
        action_mutates_session = core.session_action_mutates(
            effective_config,
            plugin_id,
            action_id,
        )
        if action_mutates_session:
            self._require_live_session_writable(session_id)

        try:
            new_session, result = core.execute_session_action(
                session,
                effective_config,
                plugin_id,
                action_id,
                action_params,
                context=self.build_core_handoff_context(
                    base_config=base_config,
                    config=effective_config,
                    extra=context,
                ),
            )
        except AgentCore._SessionActionValidationError as exc:  # type: ignore[attr-defined]
            raise self._ApplicationActionValidationError(
                str(exc),
                getattr(exc, "details", {}) or {},
            ) from exc

        if not isinstance(result, dict):
            result = {}

        mutations = (
            result.get("mutations") if isinstance(result.get("mutations"), dict) else {}
        )
        ui_effects = (
            result.get("ui_effects")
            if isinstance(result.get("ui_effects"), dict)
            else {}
        )

        if not action_mutates_session:
            return {
                **result,
                "mutations": {
                    "created_session_ids": [],
                    "updated_session_ids": [],
                    "deleted_session_ids": [],
                },
                "ui_effects": ui_effects,
            }

        self.save_session(
            new_session,
            reconcile=True,
            baseline_session=session,
            baseline_file_state=baseline_file_state,
            conflict_prefix="Concurrent session modification detected while executing action; ",
            backup_on_conflict=True,
            acquire_lock=True,
        )

        reload_ids = ui_effects.get("reload_session_ids")
        reload_list = list(reload_ids) if isinstance(reload_ids, list) else []
        if session_id not in reload_list:
            reload_list.append(session_id)

        updated_ids = mutations.get("updated_session_ids")
        updated_list = list(updated_ids) if isinstance(updated_ids, list) else []
        if session_id not in updated_list:
            updated_list.append(session_id)

        return {
            **result,
            "mutations": {
                "created_session_ids": [],
                "updated_session_ids": updated_list,
                "deleted_session_ids": [],
            },
            "ui_effects": {
                **ui_effects,
                "reload_session_ids": reload_list,
            },
        }

    def execute_action_with_metadata(
        self,
        plugin_id: Optional[str],
        action_id: str,
        params: Dict[str, Any],
        *,
        action_owner: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutedAction:
        """Execute either an application action or a provider-extension session action."""

        candidate = self._resolve_action_candidate(
            plugin_id,
            action_id,
            params,
            action_owner=action_owner,
            context=context,
        )

        if candidate.action_owner == "application":
            context = self._session_scoped_application_action_context(context)
            result = self.execute_application_action(
                candidate.plugin_id,
                candidate.action_id,
                params,
                context=context,
            )
        else:
            result = self.execute_session_action(
                candidate.plugin_id,
                candidate.action_id,
                params,
                context=context,
            )

        return ExecutedAction(
            plugin_id=candidate.plugin_id,
            action_id=candidate.action_id,
            action_owner=candidate.action_owner,
            result=result if isinstance(result, dict) else {},
        )

    def execute_action(
        self,
        plugin_id: Optional[str],
        action_id: str,
        params: Dict[str, Any],
        *,
        action_owner: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute an action and return only the plugin-provided result."""

        return self.execute_action_with_metadata(
            plugin_id,
            action_id,
            params,
            action_owner=action_owner,
            context=context,
        ).result

    def _session_scoped_application_action_context(
        self,
        context: Optional[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        if not isinstance(context, dict):
            return context
        session_id = context.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            if isinstance(context.get("config"), dict):
                return context
            if isinstance(context.get("base_config"), dict):
                return {**context, "config": dict(context["base_config"])}
            return context
        loaded = self.load_session(session_id)
        if loaded is None:
            if isinstance(context.get("config"), dict):
                return context
            if isinstance(context.get("base_config"), dict):
                return {**context, "config": dict(context["base_config"])}
            return context
        _core, base_config, session = loaded
        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        overrides = metadata.get("overrides")
        if not isinstance(overrides, dict):
            overrides = {}
        effective_config = self.resolve_effective_config(
            base_config, session, overrides
        )
        return self._context.build_session_action_context(
            session=session,
            base_config=base_config,
            config=effective_config,
            extra=context,
        )

    def load_session(
        self,
        session_id: str,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> Optional[Tuple[AgentCore, Dict[str, Any], Session]]:
        """Load a session and return ``(core, base_config, session)`` or ``None``.

        A fresh :class:`AgentCore` instance is constructed for each call so
        that per-agent plugin configuration can be applied cleanly.
        """

        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id must be a non-empty string")

        snapshot_id = self.get_selected_session_snapshot(session_id)
        session = self._session_store.load(session_id, snapshot_id=snapshot_id)
        if session is None:
            return None

        core, base_cfg, _effective_config = self._resolve_runtime_for_session(
            session, overrides
        )
        return core, base_cfg, session

    def list_session_summaries(
        self,
        *,
        filter_values: Optional[Dict[str, object]] = None,
        apply_filter_defaults: bool = False,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Return shared ordered summaries for all live stored sessions."""

        return self._session_list_service.list_session_summaries(
            filter_values=filter_values,
            apply_filter_defaults=apply_filter_defaults,
            limit=limit,
        )

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Return the shared unfiltered summary for one exact session id."""

        self.recover_session_notification_owner_lifetime(session_id)
        return self._session_list_service.get_session_summary(session_id)

    def get_session_list_diagnostics(self) -> List[Dict[str, Any]]:
        """Return structured nonfatal diagnostics from the latest list query."""

        return self._session_list_service.get_last_diagnostics()

    def get_session_list_filter_schema(self) -> Dict[str, Any]:
        """Return the normalized declarative session-list filter schema."""

        return self._session_list_filter_engine.schema(
            self.get_application_ui_schema()
        ).to_dict()

    def coerce_session_list_filter_input(
        self,
        filter_id: str,
        raw_value: str | Sequence[str],
    ) -> object:
        """Coerce terminal-style input using the current filter declaration."""

        schema = self._session_list_filter_engine.schema(
            self.get_application_ui_schema()
        )
        declaration = next(
            (item for item in schema.filters if item.element_id == filter_id),
            None,
        )
        if declaration is None:
            raise KeyError(f"Unknown session-list filter {filter_id!r}")
        return coerce_session_list_filter_input(declaration, raw_value)

    def set_session_list_filter_evaluator(
        self,
        evaluator: SessionListFilterEvaluator,
    ) -> None:
        """Install the in-process filter evaluator used by terminal queries."""

        self._session_list_service.set_filter_evaluator(evaluator)

    def load_session_record(self, session_id: str) -> Optional[Session]:
        """Load a session from the underlying store.

        Unlike :meth:`load_session`, this does not require resolving the
        session's ``agent_id`` to a configured agent.
        """

        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id must be a non-empty string")

        snapshot_id = self.get_selected_session_snapshot(session_id)
        return self._session_store.load(session_id, snapshot_id=snapshot_id)

    def load_live_session_record(self, session_id: str) -> Optional[Session]:
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id must be a non-empty string")
        return self._session_store.load(session_id)

    def get_selected_session_snapshot(self, session_id: str) -> str | None:
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id must be a non-empty string")
        selected = self._snapshot_selection_store.get_selected_snapshot(session_id)
        if not isinstance(selected, str) or not selected:
            return None
        if self._session_store.load(session_id, snapshot_id=selected) is None:
            self._snapshot_selection_store.clear_selected_snapshot(session_id)
            return None
        return selected

    def _require_live_session_writable(self, session_id: str) -> None:
        selected = self._snapshot_selection_store.get_selected_snapshot(session_id)
        if isinstance(selected, str) and selected:
            raise ReadonlySessionViewError(
                f"Session {session_id!r} is viewing readonly snapshot {selected!r}; clear selection before writing"
            )

    def list_session_snapshots(self, session_id: str) -> List[SessionSnapshotRecord]:
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id must be a non-empty string")
        return self._session_store.list_snapshots(session_id)

    def create_session_snapshot(
        self,
        session_id: str,
        *,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SessionSnapshotRecord:
        live = self.load_live_session_record(session_id)
        if live is None:
            raise KeyError(f"Session {session_id!r} not found")
        return self._session_store.create_snapshot(
            live, reason=reason, metadata=metadata
        )

    def select_session_snapshot(self, session_id: str, snapshot_id: str) -> None:
        if self.load_live_session_record(session_id) is None:
            raise KeyError(f"Session {session_id!r} not found")
        if self._session_store.load(session_id, snapshot_id=snapshot_id) is None:
            raise KeyError(
                f"Snapshot {snapshot_id!r} not found for session {session_id!r}"
            )
        self._snapshot_selection_store.select_snapshot(session_id, snapshot_id)

    def clear_selected_session_snapshot(self, session_id: str) -> None:
        self._snapshot_selection_store.clear_selected_snapshot(session_id)

    def delete_session_snapshot(self, session_id: str, snapshot_id: str) -> bool:
        return self._session_store.delete_snapshot(session_id, snapshot_id)

    def restore_session_snapshot(self, session_id: str, snapshot_id: str) -> Session:
        live = self.load_live_session_record(session_id)
        if live is None:
            raise KeyError(f"Session {session_id!r} not found")
        restored = self._session_store.load(session_id, snapshot_id=snapshot_id)
        if restored is None:
            raise KeyError(
                f"Snapshot {snapshot_id!r} not found for session {session_id!r}"
            )
        if live.to_dict() != restored.to_dict():
            self._session_store.create_snapshot(live, reason="before restore")
        live_metadata = live.metadata if isinstance(live.metadata, dict) else {}
        restored_metadata = (
            dict(restored.metadata) if isinstance(restored.metadata, dict) else {}
        )
        if "notifications" in live_metadata:
            restored_metadata["notifications"] = live_metadata["notifications"]
        else:
            restored_metadata.pop("notifications", None)
        restored = Session(
            session_id=restored.session_id,
            messages=restored.messages,
            metadata=restored_metadata,
        )
        self._snapshot_selection_store.clear_selected_snapshot(session_id)
        saved = self.save_session(restored, acquire_lock=False)
        return saved

    def get_session_asset_store(self) -> FilesystemSessionAssetStore:
        return self._session_asset_store

    def build_core_handoff_context(
        self,
        *,
        base_config: Mapping[str, Any],
        config: Optional[Mapping[str, Any]] = None,
        extra: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Build application-owned context for a direct AgentCore handoff."""

        return self._context.build_core_handoff_context(
            base_config=base_config,
            config=config,
            extra=extra,
        )

    def get_runtime_state_root(self) -> Path:
        return self._runtime_state_root

    def get_runtime_store(self) -> RuntimeStore:
        return self._runtime_store

    def get_tool_runtime(self) -> RuntimeStore:
        return self._runtime_store

    def run_awaitable_blocking(self, awaitable: Any) -> Any:
        return self._async_runtime_host.run_blocking(awaitable)

    def get_session_file_state(self, session_id: str) -> SessionFileState:
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id must be a non-empty string")
        return self._session_store.get_file_state(session_id)

    def _prepare_session_for_save(self, session: Session) -> Session:
        _core, _base_cfg, prepared_session, _results = self.run_session_lifecycle(
            "session_save_prepare",
            session,
            context={"session_id": session.session_id},
        )
        return prepared_session

    def _save_session_low_level(self, session: Session) -> Session:
        self._session_store.save(session)
        self._session_list_service.invalidate(session.session_id)
        self._session_request_status_service.invalidate(session.session_id)
        return self.load_session_record(session.session_id) or session

    def save_session(
        self,
        session: Session,
        *,
        reconcile: bool = False,
        baseline_session: Session | None = None,
        baseline_file_state: SessionFileState | None = None,
        conflict_prefix: str | None = None,
        backup_on_conflict: bool = False,
        conflict_request_id: str | None = None,
        acquire_lock: bool = False,
    ) -> Session:
        """Persist a session using the configured session store."""
        if reconcile and baseline_session is None:
            raise ValueError("baseline_session is required when reconcile=True")
        self._require_live_session_writable(session.session_id)

        @contextmanager
        def _maybe_lock() -> Iterator[None]:
            if not acquire_lock:
                yield
                return
            with self.acquire_session_lock(session.session_id):
                yield

        with _maybe_lock():
            prepared_session = self._prepare_session_for_save(session)
            if not reconcile:
                return self._save_session_low_level(prepared_session)

            persisted, _baseline = self._reconcile_session_with_store(
                baseline_session=cast(Session, baseline_session),
                baseline_file_state=baseline_file_state,
                current_session=prepared_session,
                persist_on_success=True,
                conflict_prefix=conflict_prefix,
                backup_on_conflict=backup_on_conflict,
                conflict_request_id=conflict_request_id,
            )
            return persisted

    def delete_session(self, session_id: str) -> None:
        """Delete a session from the store (no-op if missing)."""

        self._require_live_session_writable(session_id)
        session = self._session_store.load(session_id)
        if session is not None:
            self.run_session_lifecycle(
                "session_delete_prepare",
                session,
                context={"session_id": session_id},
            )
        self._session_store.delete(session_id)
        self._session_list_service.invalidate(session_id)
        self._session_request_status_service.invalidate(session_id)

    def create_session(
        self, agent_id: str
    ) -> Tuple[AgentCore, Dict[str, Any], Session]:
        """Create and persist a new empty session for the given agent.

        Returns a tuple of ``(core, base_config, session)`` where ``core`` is a
        freshly configured :class:`AgentCore` instance and ``base_config`` is
        the provider configuration for the agent before per-request overrides.
        """

        core, base_cfg, session = self.create_session_ephemeral(agent_id)
        self.save_session(session)
        stored = self.load_session_record(session.session_id)
        session = stored or session
        core, base_cfg, _effective_config = self._resolve_runtime_for_session(session)
        return core, base_cfg, session

    def create_session_ephemeral(
        self, agent_id: str
    ) -> Tuple[AgentCore, Dict[str, Any], Session]:
        """Create a new empty session for the given agent without persisting it.

        This helper mirrors :meth:`create_session` but does not write the
        session to the configured session store. Callers are responsible for
        explicitly persisting the session via :meth:`save_session` once
        meaningful content has been added.
        """

        if not isinstance(agent_id, str) or not agent_id:
            raise ValueError("agent_id must be a non-empty string")

        base_cfg = self._get_agent_base_config(agent_id)
        plugin_runtime = self._get_agent_plugin_runtime(agent_id)
        enabled_ids = self._agent_plugin_ids.get(agent_id)
        effective_config = resolve_request_config(base_cfg, None)
        core = self._build_core_with_enabled_ids(
            enabled_ids,
            selected_provider_config=effective_config,
            plugins_by_kind_and_id=plugin_runtime.plugins_by_kind_and_id,
        )

        base = core.create_session()
        session = Session(
            session_id=base.session_id,
            messages=base.messages,
            metadata={"agent_id": agent_id},
        )
        core, base_cfg, session, _results = self.run_session_lifecycle(
            "session_create",
            session,
            core=core,
            base_config=base_cfg,
            context={"agent_id": agent_id, "session_id": session.session_id},
        )

        return core, base_cfg, session

    def fork_session(
        self,
        core: AgentCore,
        session: Session,
        base_config: Dict[str, Any],
        *,
        upto_index: int,
        new_session_id: Optional[str] = None,
    ) -> Tuple[AgentCore, Dict[str, Any], Session]:
        """Fork ``session`` and run lifecycle-triggered actions on the fork."""

        if not isinstance(upto_index, int):
            raise TypeError("upto_index must be an integer")

        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        overrides_val = metadata.get("overrides")
        overrides: Dict[str, Any] = (
            overrides_val if isinstance(overrides_val, dict) else {}
        )
        config = resolve_request_config(base_config, overrides)

        fork_id = new_session_id or str(uuid.uuid4())
        new_session = core.fork_session(
            session,
            config,
            upto_index=upto_index,
            new_session_id=fork_id,
        )
        core, base_config, new_session, _results = self.run_session_lifecycle(
            "session_fork",
            new_session,
            core=core,
            base_config=base_config,
            context={
                "session_id": new_session.session_id,
                "fork_upto_index": upto_index,
                "original_session": session.to_dict(),
            },
        )
        return core, base_config, new_session

    def update_agent(
        self, agent_id: str, session: Session
    ) -> Tuple[AgentCore, Dict[str, Any], Session]:
        """Reconfigure core/base_config for ``agent_id`` and update session metadata.

        This does not persist the session; callers are responsible for deciding
        when to save. The returned session keeps the same ``session_id`` and
        ``messages`` as the input, with only ``metadata['agent_id']`` updated.
        """

        if not isinstance(agent_id, str) or not agent_id:
            raise ValueError("agent_id must be a non-empty string")

        existing_metadata = (
            session.metadata if isinstance(session.metadata, dict) else {}
        )
        previous_agent_id = existing_metadata.get("agent_id")
        switch_context = {
            "session_id": session.session_id,
            "previous_agent_id": (
                previous_agent_id if isinstance(previous_agent_id, str) else None
            ),
            "next_agent_id": agent_id,
        }
        previous_agent_unavailable = False

        try:
            current_core, current_base_cfg, _current_config = (
                self._resolve_runtime_for_session(session)
            )
            _prep_core, _prep_base_cfg, prepared_session, _prep_results = (
                self.run_session_lifecycle(
                    "agent_switch_prepare",
                    session,
                    core=current_core,
                    base_config=current_base_cfg,
                    context=switch_context,
                )
            )
        except KeyError as exc:
            if not self._is_unknown_agent_error(exc):
                raise
            previous_agent_unavailable = True
            prepared_session = session

        metadata = prepared_session.metadata or {}
        switched_metadata = {**metadata, "agent_id": agent_id}

        # Session-scoped plugin selections are tied to the previous agent's
        # provider stack. When switching agents, reset that selection to the
        # target agent defaults so we do not carry forward an incompatible
        # provider-only subset that excludes the new agent's provider.
        target_plugin_ids = self._agent_plugin_ids.get(agent_id)
        if target_plugin_ids is None:
            configured_plugin_ids = self._configured_agent_plugin_ids(agent_id)
            if configured_plugin_ids is None:
                switched_metadata.pop("plugins", None)
            else:
                switched_metadata["plugins"] = list(configured_plugin_ids)
        else:
            switched_metadata["plugins"] = list(target_plugin_ids)

        switched_session = Session(
            session_id=prepared_session.session_id,
            messages=prepared_session.messages,
            metadata=switched_metadata,
        )

        base_cfg = self._get_agent_base_config(agent_id)
        plugin_runtime = self._get_agent_plugin_runtime(agent_id)
        enabled_ids = self._enabled_plugin_ids_for_session(agent_id, switched_metadata)
        effective_config = resolve_request_config(base_cfg, None)
        core = self._build_core_with_enabled_ids(
            enabled_ids,
            selected_provider_config=effective_config,
            plugins_by_kind_and_id=plugin_runtime.plugins_by_kind_and_id,
        )
        if previous_agent_unavailable:
            switch_context = {
                **switch_context,
                "previous_agent_unavailable": True,
            }
        core, base_cfg, switched_session, _results = self.run_session_lifecycle(
            "agent_switch_complete",
            switched_session,
            core=core,
            base_config=base_cfg,
            context=switch_context,
        )
        return core, base_cfg, switched_session

    def prepare_tools_for_session(
        self,
        core: AgentCore,
        session: Session,
        base_config: Dict[str, Any],
        overrides: Optional[Dict[str, Any]] = None,
        *,
        request_id: Optional[str] = None,
    ) -> Tuple[AgentCore, Dict[str, Any], Session, Dict[str, Any], str]:
        """Run request_prepare and explicitly prepare tools for the resulting runtime."""
        rid = request_id or self._new_request_id()
        request_context = {
            "session_id": session.session_id,
            "request_id": rid,
            "stream": False,
            "overrides": dict(overrides or {}),
        }
        core, base_config, session, _results = self.run_session_lifecycle(
            "request_prepare",
            session,
            core=core,
            base_config=base_config,
            overrides=overrides,
            context=request_context,
        )
        config = self.resolve_effective_config(base_config, session, overrides)
        core.prepare_tools(
            config,
            context=self._context.build_tool_context(
                session=session,
                request_id=rid,
                base_config=base_config,
                config=config,
            ),
        )
        return core, base_config, session, config, rid

    async def prepare_tools_for_session_async(
        self,
        core: AgentCore,
        session: Session,
        base_config: Dict[str, Any],
        overrides: Optional[Dict[str, Any]] = None,
        *,
        request_id: Optional[str] = None,
    ) -> Tuple[AgentCore, Dict[str, Any], Session, Dict[str, Any], str]:
        """Async variant of :meth:`prepare_tools_for_session`."""
        rid = request_id or self._new_request_id()
        request_context = {
            "session_id": session.session_id,
            "request_id": rid,
            "stream": False,
            "overrides": dict(overrides or {}),
        }
        core, base_config, session, _results = self.run_session_lifecycle(
            "request_prepare",
            session,
            core=core,
            base_config=base_config,
            overrides=overrides,
            context=request_context,
        )
        config = self.resolve_effective_config(base_config, session, overrides)
        await core.prepare_tools_async(
            config,
            context=self._context.build_tool_context(
                session=session,
                request_id=rid,
                base_config=base_config,
                config=config,
            ),
        )
        return core, base_config, session, config, rid

    # ------------------------------------------------------------------
    # Core-first request API (new architecture)
    # ------------------------------------------------------------------

    def send_request(
        self,
        core: AgentCore,
        session: Session,
        base_config: Dict[str, Any],
        overrides: Optional[Dict[str, Any]] = None,
        *,
        stream: bool = False,
        request_id: Optional[str] = None,
        baseline_file_state: SessionFileState | None = None,
    ) -> Iterator[Dict[str, Any]]:
        """Core-first request API that yields events.

        This method is the *new* request entry point, corresponding to the
        original :meth:`send_request` method in
        the original application-layer ``send_request`` implementation but implemented as a
        generator over typed events instead of a dict-based one-shot call.

        Key differences from the legacy API:

        - Checkpoint persistence is handled internally by the application
        - The caller decides whether and how to expose public events externally
        - Tool loops are handled internally, with a configurable maximum
          depth (:class:`_ToolLoopConfig`).
        """

        rid = request_id or self._new_request_id()
        self._require_live_session_writable(session.session_id)

        request_context = {
            "session_id": session.session_id,
            "request_id": rid,
            "stream": bool(stream),
            "overrides": dict(overrides or {}),
        }
        try:
            with self.acquire_session_lock(session.session_id):
                session, request_reconcile_baseline = (
                    self._reconcile_session_with_store(
                        baseline_session=session,
                        baseline_file_state=baseline_file_state,
                        current_session=session,
                        persist_on_success=False,
                        conflict_prefix="Concurrent session modification detected before request start; ",
                        backup_on_conflict=True,
                        conflict_request_id=rid,
                    )
                )
        except SessionConflictError as exc:
            yield {
                "type": "error",
                "session_id": session.session_id,
                "request_id": rid,
                "detail": exc.detail,
            }
            self._expire_request_notifications(session.session_id, rid)
            yield {
                "type": "request_completed",
                "session_id": session.session_id,
                "request_id": rid,
            }
            return
        original_session = session

        core, base_config, session, _results = self.run_session_lifecycle(
            "request_prepare",
            session,
            core=core,
            base_config=base_config,
            overrides=overrides,
            context=request_context,
        )
        config = self.resolve_effective_config(base_config, session, overrides)
        provider_class = self._provider_class_for_request(session, config)
        effective_stream = self._resolve_request_stream_mode(
            requested_stream=bool(stream),
            config=config,
            provider_class=provider_class,
        )
        request_context["stream"] = effective_stream

        latest_session = session

        # Initial request_started event
        yield {
            "type": "request_started",
            "session_id": session.session_id,
            "request_id": rid,
            "stream": effective_stream,
        }

        tool_context = self._context.build_tool_context(
            session=session,
            request_id=rid,
            base_config=base_config,
            config=config,
        )
        try:
            core.prepare_tools(config, context=tool_context)
        except (
            Exception,
            asyncio.CancelledError,
            concurrent.futures.CancelledError,
        ) as exc:
            detail = str(exc) or type(exc).__name__
            yield {
                "type": "error",
                "session_id": session.session_id,
                "request_id": rid,
                "detail": f"Tool preparation failed: {detail}",
            }
            self._expire_request_notifications(session.session_id, rid)
            yield {
                "type": "request_completed",
                "session_id": session.session_id,
                "request_id": rid,
            }
            self.record_checkpoint(session.session_id, None)
            return

        cancellation = self._register_request_cancellation(rid)

        def _is_cancelled() -> bool:
            return cancellation.is_cancelled()

        def _refresh_config_for_session(current_session: Session) -> Dict[str, Any]:
            refreshed = self.resolve_effective_config(
                base_config, current_session, overrides
            )
            core.prepare_tools(
                refreshed,
                context={
                    **self._context.build_tool_context(
                        session=current_session,
                        request_id=rid,
                        base_config=base_config,
                        config=refreshed,
                    ),
                    "cancellation": cancellation,
                },
            )
            return refreshed

        def _persist_checkpoint(current_session: Session) -> Session:
            nonlocal request_baseline_session
            nonlocal request_baseline_file_state
            with self.acquire_session_lock(current_session.session_id):
                baseline_session = request_baseline_session or current_session
                baseline_file_state = request_baseline_file_state
                try:
                    reconciled = self.save_session(
                        current_session,
                        reconcile=True,
                        baseline_session=baseline_session,
                        baseline_file_state=baseline_file_state,
                        conflict_prefix="Concurrent session modification detected; ",
                        backup_on_conflict=True,
                        conflict_request_id=rid,
                    )
                    request_baseline_session = reconciled
                    request_baseline_file_state = self.get_session_file_state(
                        reconciled.session_id
                    )
                    self.record_checkpoint(reconciled.session_id, rid)
                except SessionConflictError as exc:
                    raise ToolLoopCheckpointError(exc.detail) from exc
            return reconciled

        def _sync_phase_session_for_request(current_session: Session) -> Session:
            nonlocal request_baseline_session
            nonlocal request_baseline_file_state
            with self.acquire_session_lock(current_session.session_id):
                if request_baseline_session is None:
                    return current_session
                try:
                    refreshed, refreshed_baseline = self._reconcile_session_with_store(
                        baseline_session=request_baseline_session,
                        baseline_file_state=request_baseline_file_state,
                        current_session=current_session,
                        persist_on_success=False,
                        conflict_prefix="Concurrent session modification detected before the next phase; ",
                        backup_on_conflict=True,
                        conflict_request_id=rid,
                    )
                    if refreshed_baseline is None:
                        request_baseline_session = None
                        request_baseline_file_state = None
                    else:
                        request_baseline_session = refreshed_baseline.session
                        request_baseline_file_state = refreshed_baseline.file_state
                except SessionConflictError as exc:
                    raise ToolLoopCheckpointError(exc.detail) from exc
            return refreshed

        latest_session = session
        request_baseline_session = (
            request_reconcile_baseline.session
            if request_reconcile_baseline is not None
            else None
        )
        request_baseline_file_state = (
            request_reconcile_baseline.file_state
            if request_reconcile_baseline is not None
            else None
        )
        if session != original_session:
            latest_session = _persist_checkpoint(session)
            yield {
                "type": "session_checkpoint",
                "session_id": latest_session.session_id,
                "request_id": rid,
                "session": latest_session,
            }

        error_seen = False

        try:
            current_stream = effective_stream
            while True:
                loop_runner = ToolLoopRunner(
                    core=core,
                    config=config,
                    request_id=rid,
                    tool_loop_cfg=self._tool_loop_cfg,
                    app_context=self._context,
                    base_config=base_config,
                    overrides=overrides,
                    cancel_callback=_is_cancelled,
                    cancellation=cancellation,
                    on_session_checkpoint=_persist_checkpoint,
                    session_for_phase=_sync_phase_session_for_request,
                    config_for_session=_refresh_config_for_session,
                )

                yielded_tool_loop_events = False
                try:
                    for event in loop_runner.run(
                        session=session, stream=current_stream
                    ):
                        yielded_tool_loop_events = True
                        event_type = event.get("type")

                        if event_type == "session_checkpoint":
                            event_session = event.get("session")
                            if isinstance(event_session, Session):
                                latest_session = event_session
                            yield event
                            continue

                        if event_type == "error":
                            yield event
                            if not error_seen:
                                error_seen = True
                                before_session = latest_session
                                core, base_config, latest_session, _ = (
                                    self.run_session_lifecycle(
                                        "request_error",
                                        latest_session,
                                        core=core,
                                        base_config=base_config,
                                        overrides=overrides,
                                        context={
                                            **request_context,
                                            "error": {
                                                "message": event.get("detail"),
                                            },
                                        },
                                    )
                                )
                                if latest_session != before_session:
                                    try:
                                        latest_session = _persist_checkpoint(
                                            latest_session
                                        )
                                    except ToolLoopCheckpointError:
                                        pass
                                    else:
                                        yield {
                                            "type": "session_checkpoint",
                                            "session_id": latest_session.session_id,
                                            "request_id": rid,
                                            "session": latest_session,
                                        }
                            continue

                        if event_type == "request_completed":
                            if not error_seen:
                                before_session = latest_session
                                core, base_config, latest_session, _ = (
                                    self.run_session_lifecycle(
                                        "request_complete",
                                        latest_session,
                                        core=core,
                                        base_config=base_config,
                                        overrides=overrides,
                                        context=request_context,
                                    )
                                )
                                if latest_session != before_session:
                                    try:
                                        latest_session = _persist_checkpoint(
                                            latest_session
                                        )
                                    except ToolLoopCheckpointError as exc:
                                        error_seen = True
                                        yield {
                                            "type": "error",
                                            "session_id": latest_session.session_id,
                                            "request_id": rid,
                                            "detail": exc.detail,
                                        }
                                    else:
                                        yield {
                                            "type": "session_checkpoint",
                                            "session_id": latest_session.session_id,
                                            "request_id": rid,
                                            "session": latest_session,
                                        }
                            self._expire_request_notifications(
                                latest_session.session_id,
                                rid,
                            )
                            yield event
                            self.record_checkpoint(latest_session.session_id, None)
                            continue

                        yield event
                    break
                except NotImplementedError as exc:
                    if not current_stream or yielded_tool_loop_events:
                        raise
                    self._mark_provider_non_streaming(provider_class)
                    current_stream = False
                    request_context["stream"] = False
                    self._logger.warning(
                        "provider_streaming_not_implemented_falling_back_to_non_streaming",
                        provider_class=(
                            f"{provider_class.__module__}.{provider_class.__qualname__}"
                            if provider_class is not None
                            else None
                        ),
                        request_id=rid,
                        session_id=session.session_id,
                        detail=str(exc),
                    )
                    continue
        finally:
            self._clear_request_cancellation(rid)
