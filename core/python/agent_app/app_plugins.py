from __future__ import annotations

"""Application-level plugin protocol and wrappers.

This module defines the :class:`ApplicationPlugin` protocol and a lightweight
wrapper used by :class:`agent_app.application_future.AgentApplication`.

Application plugins operate at the application layer (sessions, storage,
requests) rather than at the core provider/feature/tool layer. They expose
logical actions and UI schema elements that higher-level applications (HTTP
server, terminal, mobile) can use to build flows such as copy/fork/delete or
session summarization.
"""

import inspect
from typing import Any, Dict, List, Optional, Protocol, TYPE_CHECKING, cast, runtime_checkable

if TYPE_CHECKING:  # pragma: no cover - imported only for type checking
    from .application_future import AgentApplication


@runtime_checkable
class ApplicationPlugin(Protocol):
    """Protocol for application-level plugins.

    Application plugins are instantiated once per :class:`AgentApplication`
    instance. They receive the fully resolved application configuration via
    :meth:`init` and keep any internal state in an explicit ``state``
    dictionary passed between lifecycle methods.

    Plugins define logical actions via :meth:`get_actions` and provide
    application‑level UI schema elements via :meth:`get_ui_elements`.
    """

    # Identity (attributes on the class)
    name: str
    version: str

    # Config/UI -----------------------------------------------------------------
    def get_config_schema(self) -> Dict[str, Any]:
        """Return JSON schema describing this plugin's configuration.

        The returned mapping is treated as opaque by the application layer and
        primarily exists for configuration UIs. Plugins may return an empty
        dict when they do not require configuration.
        """

    def get_ui_elements(
        self,
        state: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) :
        """Return UI element definitions contributed by this plugin.

        Elements describe configuration controls and display elements as well
        as higher‑level action UI definitions. The application layer treats
        these as opaque dictionaries and only normalizes cross‑cutting fields
        such as the ``"plugin"`` identifier.

        The ``state`` argument is the plugin state dictionary returned from
        :meth:`init`. Optional ``config``, ``tags``, and ``models`` allow
        config-aware UI (e.g. when called with effective session config).
        """

    def get_commands(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return CLI/slash command bindings contributed by this plugin.

        Commands are frontend bindings to existing application actions rather
        than a second execution surface. Each command definition is an opaque
        dictionary that higher-level frontends can interpret to expose a real
        CLI command, a slash command, or both.
        """

    # Lifecycle -----------------------------------------------------------------
    def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize plugin state from the resolved application config.

        Args:
            app_config: Fully resolved top‑level configuration mapping.

        Returns:
            Initial opaque state dictionary owned by the plugin.
        """

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return logical action definitions for this plugin.

        The returned list contains plain dictionaries describing available
        actions (ids, labels, input schemas). The application layer will attach
        a ``"plugin"`` field naming the contributing plugin when flattening
        these definitions.
        """

    def execute_action(
        self,
        app: "AgentApplication",
        action_id: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute an action with already‑validated parameters.

        Args:
            app: Owning :class:`AgentApplication` instance.
            action_id: Action identifier defined by :meth:`get_actions`.
            params: Final, validated parameters for the action.
            context: Optional execution context, used especially for
                lifecycle-triggered actions. The mapping is expected to be
                serializable and language-neutral.
            state: Current plugin state returned from :meth:`init`.

        Returns:
            Result dictionary describing the outcome of the action. The shape
            is defined by the plugin; higher‑level layers wrap this in a
            standardized response envelope when exposing it over HTTP.
        """


class ApplicationPluginWrapper:
    """Wrapper for an :class:`ApplicationPlugin` instance.

    The wrapper owns the plugin instance and its associated state dictionary.
    It exposes a minimal, typed surface that :class:`AgentApplication` uses
    to list actions, UI schema, and execute actions.
    """

    def __init__(self, plugin_id: str, plugin_class: type[Any]) -> None:
        if not isinstance(plugin_id, str) or not plugin_id:
            raise ValueError("plugin_id must be a non-empty string")

        self.plugin_id = plugin_id
        self.plugin_class = plugin_class
        # The protocol guarantees a no‑arg constructor.
        self.plugin: ApplicationPlugin = plugin_class()  # type: ignore[assignment]
        self._state: Dict[str, Any] = {}
        self.name = getattr(plugin_class, "name", plugin_id)
        self.version = getattr(plugin_class, "version", "unknown")

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def init(self, app_config: Dict[str, Any]) -> None:
        """Initialize the underlying plugin and cache its state."""

        state = self.plugin.init(app_config)
        if not isinstance(state, dict):
            # Guard against misbehaving plugins; treat non-dict state as empty.
            state = {}
        self._state = state

    @property
    def state(self) -> Dict[str, Any]:
        """Return the current plugin state dictionary."""

        return self._state

    # ------------------------------------------------------------------
    # Introspection helpers
    # ------------------------------------------------------------------

    def get_actions(self) -> List[Dict[str, Any]]:
        """Return sanitized action definitions from the plugin."""

        actions = self.plugin.get_actions(self._state)
        if not isinstance(actions, list):
            return []
        return [a for a in actions if isinstance(a, dict)]

    def get_ui_elements(self, config: Optional[Dict[str, Any]] = None, tags: Optional[List[str]] = None, models: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """Return sanitized UI element definitions from the plugin."""

        elements = self.plugin.get_ui_elements(self._state, config, tags, models)
        if not isinstance(elements, list):
            return []
        return [e for e in elements if isinstance(e, dict)]

    def get_commands(self) -> List[Dict[str, Any]]:
        """Return sanitized command definitions from the plugin."""

        fn = getattr(self.plugin, "get_commands", None)
        if not callable(fn):
            return []
        commands = fn(self._state)
        if not isinstance(commands, list):
            return []
        return [c for c in commands if isinstance(c, dict)]

    # ------------------------------------------------------------------
    # Action execution
    # ------------------------------------------------------------------

    def execute_action(
        self,
        app: "AgentApplication",
        action_id: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Invoke the underlying plugin's :meth:`execute_action` method."""

        fn = self.plugin.execute_action
        try:
            sig = inspect.signature(fn)
        except (TypeError, ValueError):
            result = fn(app, action_id, params, context, self._state)
        else:
            params_sig = list(sig.parameters.values())
            if any(
                p.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
                for p in params_sig
            ):
                result = fn(app, action_id, params, context, self._state)
            else:
                positional = [
                    p
                    for p in params_sig
                    if p.kind
                    in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
                ]
                if len(positional) >= 5:
                    result = fn(app, action_id, params, context, self._state)
                else:
                    result = fn(app, action_id, params, self._state)  # type: ignore[misc]
        if not isinstance(result, dict):
            return {}
        return result


__all__ = ["ApplicationPlugin", "ApplicationPluginWrapper"]
