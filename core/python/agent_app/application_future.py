from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Mapping, Optional, Sequence, Set, Tuple, cast
import uuid
from contextlib import contextmanager
from datetime import datetime
import os
import threading

from agent_core import AgentCore, Message, Session
from agent_core.plugin.loader import validate_plugin_for_kind

from .app_plugins import ApplicationPluginWrapper
from .config import (
    build_config_resolution_env,
    build_runtime_overlay_env,
    build_agent_config,
    load_raw_config,
    resolve_config_mixins,
    resolve_placeholders,
    resolve_request_config,
)
from .events import EventStore, InMemoryEventStore
from .session_assets import FilesystemSessionAssetStore
from .sessions import FilesystemSessionStore, SessionFileState
from .tool_loop import RequestCancellation, ToolLoopRunner, ToolLoopCheckpointError
from agent_core.utils import get_logger
from .plugin_manager import PluginManager
from .runtime_env import RuntimeEnvOverlay
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


@dataclass
class _CheckpointBaseline:
    session: Session
    file_state: SessionFileState


class _ToolRuntimeStore:
    """Application-owned store for long-lived tool runtime objects.

    The store is intentionally minimal in this task: long-running hooks may use
    it to persist live managers or clients between fresh ``AgentCore``
    instances, while cheap hooks consume only JSON-like prepared data.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._values: Dict[Tuple[str, str], Any] = {}

    def get(self, namespace: str, key: str) -> Any | None:
        if not isinstance(namespace, str) or not namespace:
            return None
        if not isinstance(key, str) or not key:
            return None
        with self._lock:
            return self._values.get((namespace, key))

    def set(self, namespace: str, key: str, value: Any) -> None:
        if not isinstance(namespace, str) or not namespace:
            raise ValueError("namespace must be a non-empty string")
        if not isinstance(key, str) or not key:
            raise ValueError("key must be a non-empty string")
        with self._lock:
            self._values[(namespace, key)] = value

    def pop(self, namespace: str, key: str) -> Any | None:
        if not isinstance(namespace, str) or not namespace:
            return None
        if not isinstance(key, str) or not key:
            return None
        with self._lock:
            return self._values.pop((namespace, key), None)


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

    def __init__(
        self,
        config_path: str | Path,
        session_root: str | Path,
        core_factory: Callable[[], AgentCore] = AgentCore,
        event_store: Optional[EventStore] = None,
        env_overrides: Mapping[str, str] | None = None,
    ) -> None:
        logger = get_logger("AgentApplication")
        # Core factory is stored so that per-session cores can be created
        # without sharing state across requests.
        self._core_factory = core_factory
        self._event_store: EventStore = event_store or InMemoryEventStore()

        # A single core instance is still used for import/export with the
        # filesystem session store; inference uses fresh cores created via
        # ``_new_core``.
        core = core_factory()
        self._core = core

        raw_config = load_raw_config(config_path)
        config_base_dir = str(Path(config_path).resolve().parent)
        resolution_env = build_config_resolution_env(
            config_path,
            env_overrides=env_overrides,
        )
        resolved_config, placeholder_errors = resolve_placeholders(raw_config, env=resolution_env)
        mixin_resolved_config, mixin_errors = resolve_config_mixins(resolved_config)
        self._config: Dict[str, Any] = mixin_resolved_config
        self._config_errors: List[Dict[str, Any]] = placeholder_errors + mixin_errors
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
        plugin_policy: Dict[str, Any] = dict(plugin_policy_in) if isinstance(plugin_policy_in, dict) else {}
        plugin_policy.setdefault("base_dir", config_base_dir)

        mgr = PluginManager(cache_dir=cache_path, policy=plugin_policy)

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

        self._plugin_classes, self._plugins_by_kind_and_id = self._dedupe_plugin_classes_by_id(
            all_plugin_classes_by_kind
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
            wrapper = ApplicationPluginWrapper(plugin_id=plugin_id, plugin_class=plugin_class)
            wrapper.init(self._config)
            self._app_plugins[plugin_id] = wrapper

        session_root_path = Path(session_root)
        self._session_store = FilesystemSessionStore(session_root_path, core)
        self._session_asset_store = FilesystemSessionAssetStore(
            session_root_path.parent / "session_assets"
        )
        self._tool_runtime = _ToolRuntimeStore()
        self._tool_loop_cfg = _ToolLoopConfig()
        self._cancelled_requests: set[str] = set()
        self._request_cancellations: Dict[str, RequestCancellation] = {}

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
            self._agent_base_configs[agent_id] = build_agent_config(self._config, agent_id)

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
            default_enabled_ids = [pid for pid in all_plugin_ids if pid not in disabled_set]
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
            "Configuration resolution failed:\n" + "\n".join(f"- {item}" for item in details)
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
    def _collect_plugin_ids(plugins_by_kind_and_id: Dict[str, Dict[str, type[Any]]]) -> List[str]:
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

        known_ids = set(self._collect_plugin_ids(self._get_agent_plugin_runtime(agent_id).plugins_by_kind_and_id))
        configured_ids = [item for item in raw_plugins if isinstance(item, str) and item in known_ids]
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
                fq = next((ident for ident in idents if "." in ident), idents[0] if idents else "")
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
        effective_config = self._decorate_runtime_config(
            resolve_request_config(base_cfg, effective_overrides)
        )
        core = self._build_core_with_enabled_ids(
            enabled_ids,
            selected_provider_config=effective_config,
            plugins_by_kind_and_id=plugin_runtime.plugins_by_kind_and_id,
        )
        return core, base_cfg, effective_config

    def _decorate_runtime_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            **config,
            "_session_asset_store": self._session_asset_store,
        }

    def resolve_effective_config(
        self,
        base_config: Dict[str, Any],
        session: Session,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        effective_overrides = self._effective_overrides(metadata, overrides)
        return self._decorate_runtime_config(
            resolve_request_config(base_config, effective_overrides)
        )

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

        if self._session_messages_digest(stored_session) != self._session_messages_digest(
            baseline_session
        ):
            raise ValueError("messages_changed")

        if self._protected_session_metadata(stored_session) != self._protected_session_metadata(
            baseline_session
        ):
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
    ) -> tuple[Session, _CheckpointBaseline | None]:
        current_state = self._session_store.get_file_state(current_session.session_id)

        if baseline_file_state is not None and current_state == baseline_file_state:
            if not persist_on_success:
                return current_session, _CheckpointBaseline(
                    session=baseline_session,
                    file_state=baseline_file_state,
                )

            self.save_session(current_session)
            persisted = self.load_session_record(current_session.session_id) or current_session
            saved_state = self._session_store.get_file_state(current_session.session_id)
            return persisted, _CheckpointBaseline(
                session=persisted,
                file_state=saved_state,
            )

        if not current_state.exists:
            if not persist_on_success:
                return current_session, None

            self.save_session(current_session)
            persisted = self.load_session_record(current_session.session_id) or current_session
            saved_state = self._session_store.get_file_state(current_session.session_id)
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

        self.save_session(merged_session)
        persisted = self.load_session_record(merged_session.session_id) or merged_session
        saved_state = self._session_store.get_file_state(merged_session.session_id)
        return persisted, _CheckpointBaseline(
            session=persisted,
            file_state=saved_state,
        )

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
            return any(isinstance(item, str) and item == lifecycle for item in trigger_val)
        return False

    @staticmethod
    def _ensure_serializable_context(context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
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
        return {
            **context,
            "lifecycle": lifecycle,
            "trigger_source": "application",
            "session": session.to_dict(),
            "config": config,
            "app": self,
            "application": self,
            "base_config": self._config,
        }

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
        metadata_patch = metadata_patch_raw if isinstance(metadata_patch_raw, dict) else {}

        overrides_patch_raw = result.get("session_overrides")
        overrides_patch = overrides_patch_raw if isinstance(overrides_patch_raw, dict) else {}

        if not metadata_patch and not overrides_patch:
            return next_session

        metadata = dict(next_session.metadata) if isinstance(next_session.metadata, dict) else {}
        metadata.update(metadata_patch)

        if overrides_patch:
            stored_overrides = metadata.get("overrides")
            normalized_overrides = stored_overrides if isinstance(stored_overrides, dict) else {}
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
            if not isinstance(action, dict) or not self._action_matches_trigger(action, lifecycle):
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

        core_context = self._build_lifecycle_context(
            lifecycle,
            current_session,
            effective_config,
            context,
        )
        current_session, core_results = core.execute_lifecycle_actions(
            current_session,
            effective_config,
            lifecycle,
            context=core_context,
        )
        results.extend(core_results)
        core, base_config, _ = self._resolve_runtime_for_session(current_session, overrides)
        return core, base_config, current_session, results

    def _load_session_required(self, session_id: str) -> Session:
        session = self._session_store.load(session_id)
        if session is None:
            raise KeyError(f"Session {session_id!r} not found")
        return session

    def _extract_tool_calls(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        tool_calls: List[Dict[str, Any]] = []
        for msg in messages:
            if msg.get("role") != "assistant":
                continue
            metadata = msg.get("metadata") or {}
            calls = metadata.get("tool_calls") or []
            if isinstance(calls, list):
                tool_calls.extend([c for c in calls if isinstance(c, dict)])
        return tool_calls

    def _extract_pending_tool_calls_from_session(self, session: Session) -> List[Dict[str, Any]]:
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

    def register_provider(self, plugin_class: type, extensions: Optional[List[type]] = None) -> None:
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
            - docs/plugins/application-config.md (Troubleshooting)
        """

        return list(self._config_errors)

    def get_event_store(self) -> EventStore:
        """Return the configured event store for this application."""

        return self._event_store

    def compact_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Return a compacted view of ``events``.

        This helper removes redundant ``partial`` and ``tool_partial``
        events that precede terminal events (``final`` or
        ``tool_results``) for the same ``session_id``/``request_id``
        pair within a single batch. It does not modify the underlying
        event store and preserves the order of all kept events.
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
                    if seen_tool_results.get(key):
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

        def _merge_two(a: Dict[str, Any], b: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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

                has_reasoning = isinstance(reasoning_a, str) or isinstance(reasoning_b, str)
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
        raw_app_cfg = cfg.get("application") if isinstance(cfg.get("application"), dict) else {}
        return cast(Dict[str, Any], raw_app_cfg)

    def get_resolved_env(self) -> Dict[str, str]:
        """Return the runtime env mapping used for config placeholder resolution."""

        return dict(self._resolved_env)

    @staticmethod
    def _release_runtime_env_overlay(overlay: RuntimeEnvOverlay) -> None:
        overlay.close()

    def close(self) -> None:
        """Release process-global runtime env overlay owned by this app."""

        if self._runtime_env_finalizer.alive:
            self._runtime_env_finalizer()

    def cancel_request(self, request_id: str) -> None:
        """Request cooperative cancellation for an in-flight request.

        Cancellation is best-effort and affects only send_request calls that
        observe this ``request_id``. Providers and tool loops must periodically
        check for cancellation; long-running non-streaming calls may not stop
        immediately.
        """

        if not isinstance(request_id, str) or not request_id:
            raise ValueError("request_id must be a non-empty string")

        self._cancelled_requests.add(request_id)
        cancellation = self._request_cancellations.get(request_id)
        if cancellation is not None:
            cancellation.cancel()

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
    ) -> List[Dict[str, Any]]:
        """Return flattened UI schema elements from application plugins.

        Each element is normalized to include a ``"plugin"`` field naming
        the contributing plugin. Optional config/tags/models are passed
        through so plugins can return config-aware UI.
        """

        elements: List[Dict[str, Any]] = []
        for plugin_id, wrapper in self._app_plugins.items():
            for raw_element in wrapper.get_ui_elements(config=config, tags=tags, models=models):
                if not isinstance(raw_element, dict):
                    continue    
                if "plugin" in raw_element and isinstance(raw_element["plugin"], str):
                    elements.append(raw_element)
                else:
                    element = dict(raw_element)
                    element["plugin"] = plugin_id
                    elements.append(element)
        return elements

    # Internal helpers for action validation ---------------------------------

    class _ApplicationActionValidationError(Exception):
        """Internal exception used for application action input validation.

        Carries a ``details`` mapping suitable for surfacing in higher-level
        error envelopes.
        """

        def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
            super().__init__(message)
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
            return (isinstance(value, (int, float)) and not isinstance(value, bool))
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

        return wrapper.execute_action(self, action_id, validated_inputs, context=context)

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
            raise ValueError("session_id must be a non-empty string")

        action_params = dict(params)
        action_params.pop("session_id", None)

        with self.acquire_session_lock(session_id):
            ctx = self.load_session(session_id)
            if ctx is None:
                raise KeyError(f"Session {session_id!r} not found")

            core, base_config, session = ctx
            metadata = session.metadata if isinstance(session.metadata, dict) else {}
            overrides = metadata.get("overrides")
            if not isinstance(overrides, dict):
                overrides = {}
            effective_config = self.resolve_effective_config(base_config, session, overrides)

            action_context = dict(context) if isinstance(context, dict) else {}
            action_context.setdefault("app", self)
            action_context.setdefault("application", self)
            action_context.setdefault("session_asset_store", self._session_asset_store)
            action_context.setdefault("base_config", base_config)

            try:
                new_session, result = core.execute_session_action(
                    session,
                    effective_config,
                    plugin_id,
                    action_id,
                    action_params,
                    context=action_context,
                )
            except AgentCore._SessionActionValidationError as exc:  # type: ignore[attr-defined]
                raise self._ApplicationActionValidationError(
                    str(exc),
                    getattr(exc, "details", {}) or {},
                ) from exc

            self.save_session(new_session)

        if not isinstance(result, dict):
            result = {}

        mutations = result.get("mutations") if isinstance(result.get("mutations"), dict) else {}
        ui_effects = result.get("ui_effects") if isinstance(result.get("ui_effects"), dict) else {}

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

    def execute_action(
        self,
        plugin_id: str,
        action_id: str,
        params: Dict[str, Any],
        *,
        action_owner: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute either an application action or a provider-extension session action."""

        if action_owner == "application":
            return self.execute_application_action(plugin_id, action_id, params, context=context)
        if action_owner in {"provider_extension", "feature"}:
            return self.execute_session_action(plugin_id, action_id, params, context=context)

        try:
            return self.execute_application_action(plugin_id, action_id, params, context=context)
        except KeyError:
            if not (isinstance(params, dict) and isinstance(params.get("session_id"), str)):
                raise
            return self.execute_session_action(plugin_id, action_id, params, context=context)

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

        session = self._session_store.load(session_id)
        if session is None:
            return None

        core, base_cfg, _effective_config = self._resolve_runtime_for_session(session, overrides)
        return core, base_cfg, session

    def load_session_record(self, session_id: str) -> Optional[Session]:
        """Load a session from the underlying store.

        Unlike :meth:`load_session`, this does not require resolving the
        session's ``agent_id`` to a configured agent.
        """

        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id must be a non-empty string")

        return self._session_store.load(session_id)

    def get_session_asset_store(self) -> FilesystemSessionAssetStore:
        return self._session_asset_store

    def get_tool_runtime(self) -> _ToolRuntimeStore:
        return self._tool_runtime

    def save_session(self, session: Session) -> None:
        """Persist a session using the configured session store."""

        _core, _base_cfg, prepared_session, _results = self.run_session_lifecycle(
            "session_save_prepare",
            session,
            context={"session_id": session.session_id},
        )
        self._session_store.save(prepared_session)

    def delete_session(self, session_id: str) -> None:
        """Delete a session from the store (no-op if missing)."""

        session = self._session_store.load(session_id)
        if session is not None:
            self.run_session_lifecycle(
                "session_delete_prepare",
                session,
                context={"session_id": session_id},
            )
        self._session_store.delete(session_id)

    def create_session(self, agent_id: str) -> Tuple[AgentCore, Dict[str, Any], Session]:
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

    def create_session_ephemeral(self, agent_id: str) -> Tuple[AgentCore, Dict[str, Any], Session]:
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
        core = self._build_core_with_enabled_ids(
            enabled_ids,
            selected_provider_config=base_cfg,
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

    def update_agent(self, agent_id: str, session: Session) -> Tuple[AgentCore, Dict[str, Any], Session]:
        """Reconfigure core/base_config for ``agent_id`` and update session metadata.

        This does not persist the session; callers are responsible for deciding
        when to save. The returned session keeps the same ``session_id`` and
        ``messages`` as the input, with only ``metadata['agent_id']`` updated.
        """

        if not isinstance(agent_id, str) or not agent_id:
            raise ValueError("agent_id must be a non-empty string")

        existing_metadata = session.metadata if isinstance(session.metadata, dict) else {}
        previous_agent_id = existing_metadata.get("agent_id")
        switch_context = {
            "session_id": session.session_id,
            "previous_agent_id": previous_agent_id if isinstance(previous_agent_id, str) else None,
            "next_agent_id": agent_id,
        }
        previous_agent_unavailable = False

        try:
            current_core, current_base_cfg, _current_config = self._resolve_runtime_for_session(session)
            _prep_core, _prep_base_cfg, prepared_session, _prep_results = self.run_session_lifecycle(
                "agent_switch_prepare",
                session,
                core=current_core,
                base_config=current_base_cfg,
                context=switch_context,
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
        core = self._build_core_with_enabled_ids(
            enabled_ids,
            selected_provider_config=base_cfg,
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

    def _build_tool_context(
        self,
        *,
        session: Session,
        request_id: str,
    ) -> Dict[str, Any]:
        return {
            "app": self,
            "application": self,
            "base_config": self._config,
            "session": session.to_dict(),
            "request_id": request_id,
            "session_asset_store": self._session_asset_store,
            "tool_runtime": self._tool_runtime,
            "trigger_source": "application",
        }

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
            context=self._build_tool_context(session=session, request_id=rid),
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
            context=self._build_tool_context(session=session, request_id=rid),
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
    ) -> Iterator[Dict[str, Any]]:
        """Core-first request API that yields events.

        This method is the *new* request entry point, corresponding to the
        original :meth:`send_request` method in
        the original application-layer ``send_request`` implementation but implemented as a
        generator over typed events instead of a dict-based one-shot call.

        Key differences from the legacy API:

        - Persistence is the responsibility of the caller
        - The caller decides whether and how to expose events externally
        - Tool loops are handled internally, with a configurable maximum
          depth (:class:`_ToolLoopConfig`).
        """

        rid = request_id or self._new_request_id()

        request_context = {
            "session_id": session.session_id,
            "request_id": rid,
            "stream": bool(stream),
            "overrides": dict(overrides or {}),
        }
        reason_texts = {
            "stored_session_disappeared": "stored session disappeared",
            "session_id_changed": "session id changed",
            "message_count_changed": "message count changed",
            "messages_changed": "messages changed",
            "protected_metadata_changed": "protected metadata changed",
        }

        def _format_session_conflict_detail(
            *,
            prefix: str,
            reason: str,
            backup_session: Session,
        ) -> str:
            backup_path = self._save_session_conflict_backup(
                backup_session,
                request_id=rid,
            )
            suffix = reason_texts.get(reason, reason.replace("_", " "))
            return f"{prefix}{suffix}. Backup saved to {backup_path}"

        try:
            with self.acquire_session_lock(session.session_id):
                session, checkpoint_baseline = self._reconcile_session_with_store(
                    baseline_session=session,
                    baseline_file_state=None,
                    current_session=session,
                    persist_on_success=False,
                )
        except ValueError as exc:
            yield {
                "type": "error",
                "session_id": session.session_id,
                "request_id": rid,
                "detail": _format_session_conflict_detail(
                    prefix="Concurrent session modification detected before request start; ",
                    reason=str(exc),
                    backup_session=session,
                ),
            }
            yield {
                "type": "request_completed",
                "session_id": session.session_id,
                "request_id": rid,
            }
            return
        original_session = session

        latest_session = session

        # Initial request_started event
        yield {
            "type": "request_started",
            "session_id": session.session_id,
            "request_id": rid,
            "stream": bool(stream),
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
            context=self._build_tool_context(session=session, request_id=rid),
        )

        cancellation = RequestCancellation(cancelled=rid in self._cancelled_requests)
        self._request_cancellations[rid] = cancellation

        def _is_cancelled() -> bool:
            return cancellation.is_cancelled()

        def _refresh_config_for_session(current_session: Session) -> Dict[str, Any]:
            refreshed = self.resolve_effective_config(base_config, current_session, overrides)
            core.prepare_tools(
                refreshed,
                context={
                    **self._build_tool_context(session=current_session, request_id=rid),
                    "cancellation": cancellation,
                },
            )
            return refreshed

        def _persist_checkpoint(current_session: Session) -> Session:
            nonlocal checkpoint_baseline
            with self.acquire_session_lock(current_session.session_id):
                baseline_session = (
                    checkpoint_baseline.session
                    if checkpoint_baseline is not None
                    else current_session
                )
                baseline_file_state = (
                    checkpoint_baseline.file_state
                    if checkpoint_baseline is not None
                    else None
                )
                try:
                    reconciled, checkpoint_baseline = self._reconcile_session_with_store(
                        baseline_session=baseline_session,
                        baseline_file_state=baseline_file_state,
                        current_session=current_session,
                        persist_on_success=True,
                    )
                except ValueError as exc:
                    raise ToolLoopCheckpointError(
                        _format_session_conflict_detail(
                            prefix="Concurrent session modification detected; ",
                            reason=str(exc),
                            backup_session=current_session,
                        )
                    ) from exc
            return reconciled

        def _sync_phase_session_for_request(current_session: Session) -> Session:
            nonlocal checkpoint_baseline
            with self.acquire_session_lock(current_session.session_id):
                if checkpoint_baseline is None:
                    return current_session
                try:
                    refreshed, checkpoint_baseline = self._reconcile_session_with_store(
                        baseline_session=checkpoint_baseline.session,
                        baseline_file_state=checkpoint_baseline.file_state,
                        current_session=current_session,
                        persist_on_success=False,
                    )
                except ValueError as exc:
                    raise ToolLoopCheckpointError(
                        _format_session_conflict_detail(
                            prefix="Concurrent session modification detected before the next phase; ",
                            reason=str(exc),
                            backup_session=current_session,
                        )
                    ) from exc
            return refreshed

        latest_session = session
        if session != original_session:
            latest_session = _persist_checkpoint(session)
            yield {
                "type": "session_checkpoint",
                "session_id": latest_session.session_id,
                "request_id": rid,
                "session": latest_session,
            }

        loop_runner = ToolLoopRunner(
            core=core,
            config=config,
            request_id=rid,
            tool_loop_cfg=self._tool_loop_cfg,
            cancel_callback=_is_cancelled,
            cancellation=cancellation,
            context={
                **self._build_tool_context(session=session, request_id=rid),
                "cancellation": cancellation,
            },
            on_session_checkpoint=_persist_checkpoint,
            session_for_phase=_sync_phase_session_for_request,
            config_for_session=_refresh_config_for_session,
        )

        error_seen = False

        try:
            for event in loop_runner.run(session=session, stream=stream):
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
                        core, base_config, latest_session, _ = self.run_session_lifecycle(
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
                        if latest_session != before_session:
                            try:
                                latest_session = _persist_checkpoint(latest_session)
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
                        core, base_config, latest_session, _ = self.run_session_lifecycle(
                            "request_complete",
                            latest_session,
                            core=core,
                            base_config=base_config,
                            overrides=overrides,
                            context=request_context,
                        )
                        if latest_session != before_session:
                            try:
                                latest_session = _persist_checkpoint(latest_session)
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
                    yield event
                    continue

                yield event
        finally:
            self._cancelled_requests.discard(rid)
            self._request_cancellations.pop(rid, None)
