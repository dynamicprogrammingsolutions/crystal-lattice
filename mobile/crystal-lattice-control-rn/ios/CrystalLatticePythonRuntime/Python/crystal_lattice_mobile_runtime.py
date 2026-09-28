from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import parse_qs, unquote, urlsplit
import uuid

from agent_app.application_future import AgentApplication, ReadonlySessionViewError
from agent_app.application_notifications import InMemoryApplicationNotificationStore
from agent_app.plugin_sources.dotted import DottedClassSource
from agent_app.sessions import FilesystemSnapshotSelectionStore
from agent_core.types import ProviderPlugin, Session


class EmbeddedSmokeProvider(ProviderPlugin):
    name = "embedded_smoke_provider"
    version = "0.1.0"

    def init(self, config: dict[str, Any]) -> dict[str, Any]:
        return {"config": config}

    def call_api(
        self,
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
    ) -> tuple[
        list[dict[str, Any]],
        list[dict[str, Any]],
        list[dict[str, Any]],
        dict[str, Any],
    ]:
        final = {
            "role": "assistant",
            "content": "Embedded runtime smoke response",
            "metadata": {"development_smoke_provider": True},
        }
        return [], [final], [*native_messages, final], state

    def stream_api(
        self,
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
    ) -> Iterator[dict[str, Any]]:
        _ = native_messages, state
        yield {"content": "Embedded runtime smoke response"}


PROFILE_ORDER = (
    "compatible",
    "reviewer",
    "openai",
    "openrouter",
    "anthropic",
)
PROFILE_DEFAULTS: dict[str, dict[str, Any]] = {
    "compatible": {
        "enabled": False,
        "base_url": "http://127.0.0.1:3000/v1",
        "model": "qwen3.5:0.8b",
    },
    "reviewer": {
        "enabled": True,
        "base_url": "https://ireland-s1.dynamicprogrammingsolutions.com:3443/v1",
        "model": "gpt-5.6-luna",
        "tls_ca_bundle": "",
    },
    "openai": {
        "enabled": False,
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-5.6-luna",
        "auth_mode": "api",
    },
    "openrouter": {
        "enabled": False,
        "base_url": "https://openrouter.ai/api/v1",
        "model": "anthropic/claude-haiku-4.5",
    },
    "anthropic": {
        "enabled": False,
        "base_url": "https://api.anthropic.com",
        "model": "claude-haiku-4-5-20251001",
    },
}
PROFILE_AGENTS = {
    "compatible": "compatible-claude",
    "reviewer": "reviewer-codex",
    "openai": "openai-codex",
    "openrouter": "openrouter-claude",
    "anthropic": "anthropic-claude",
}
CLAUDE_TOOL_PLUGINS = [
    "embedded_claude_tools.read_tool.ClaudeLikeReadTool",
    "embedded_claude_tools.write_tool.ClaudeLikeWriteTool",
    "embedded_claude_tools.edit_tool.ClaudeLikeEditTool",
    "embedded_claude_tools.glob_tool.ClaudeLikeGlobTool",
    "embedded_claude_tools.grep_tool.ClaudeLikeGrepTool",
    "embedded_claude_tools.web_fetch_tool.ClaudeLikeWebFetchTool",
]
CODEX_TOOL_PLUGINS = [
    "embedded_codex_tools.sed_tool.CodexLikeSedTool",
    "embedded_codex_tools.rg_tool.CodexLikeRgTool",
    "embedded_codex_tools.find_tool.CodexLikeFindTool",
    "embedded_codex_tools.curl_tool.CodexLikeCurlTool",
    "embedded_codex_tools.apply_patch_tool.CodexLikeApplyPatchTool",
]
APPLICATION_PLUGINS = [
    "chatgpt_auth_app.ChatGPTAuthAppPlugin",
    "generate_title_app.GenerateTitleAppPlugin",
    "session_actions_app.SessionActionsAppPlugin",
    "session_archive_app.SessionArchiveAppPlugin",
    "session_main_search_app.SessionMainSearchAppPlugin",
    "session_message_count_meta_app.SessionMessageCountMetaAppPlugin",
    "session_ordering_buckets_app.SessionOrderingBucketsAppPlugin",
    "session_pinned_app.SessionPinnedAppPlugin",
    "session_status_app.SessionStatusAppPlugin",
    "session_timestamp_meta_app.SessionTimestampMetaAppPlugin",
    "session_title_app.SessionTitleAppPlugin",
    "session_asset_attachments.SessionAssetAttachmentsAppPlugin",
]
APPLICATION_CONFIG = {
    "generate_title_max_messages": 999,
    "session_actions": {"allow_delete": True},
    "session_status_show_in_session_list_footer": True,
}


def _normalized_profile(
    profile_id: str,
    raw_profile: Any,
) -> dict[str, Any]:
    defaults = PROFILE_DEFAULTS[profile_id]
    source = raw_profile if isinstance(raw_profile, dict) else {}
    return {
        "enabled": bool(source.get("enabled", defaults["enabled"])),
        "base_url": str(
            source.get("base_url")
            or source.get("proxy_url")
            or defaults["base_url"]
        ).strip(),
        "model": str(source.get("model") or defaults["model"]).strip(),
        "auth_mode": (
            lambda mode: mode if mode in {"api", "chatgpt"} else "api"
        )(str(
            source.get("auth_mode")
            or defaults.get("auth_mode")
            or "api"
        ).strip().lower()),
        "tls_ca_bundle": str(
            source.get("tls_ca_bundle")
            or defaults.get("tls_ca_bundle")
            or ""
        ).strip(),
        "api_key": str(source.get("api_key") or "").strip(),
    }


def _normalized_runtime_configuration(
    runtime_configuration: dict[str, Any] | None,
) -> dict[str, Any]:
    source = runtime_configuration if isinstance(runtime_configuration, dict) else {}
    raw_profiles = source.get("providers")
    profiles_source = raw_profiles if isinstance(raw_profiles, dict) else {}

    if not profiles_source and any(
        source.get(key) for key in ("api_key", "model", "proxy_url")
    ):
        profiles_source = {
            "compatible": {
                "enabled": True,
                "api_key": source.get("api_key"),
                "model": source.get("model"),
                "base_url": source.get("proxy_url"),
            }
        }

    profiles = {
        profile_id: _normalized_profile(
            profile_id,
            profiles_source.get(profile_id),
        )
        for profile_id in PROFILE_ORDER
    }
    default_agent = str(
        source.get("default_agent") or PROFILE_AGENTS["reviewer"]
    ).strip()
    if default_agent not in PROFILE_AGENTS.values():
        default_agent = PROFILE_AGENTS["reviewer"]
    return {
        "version": 2,
        "default_agent": default_agent,
        "providers": profiles,
    }


def _profile_is_ready(profile: dict[str, Any]) -> bool:
    if profile.get("enabled") is not True:
        return False
    if not all(
        isinstance(profile.get(key), str) and bool(profile[key])
        for key in ("base_url", "model")
    ):
        return False
    if profile.get("auth_mode") in {"auto", "chatgpt"}:
        return True
    return isinstance(profile.get("api_key"), str) and bool(profile["api_key"])


def _runtime_provider_mode(configuration: dict[str, Any]) -> str:
    profiles = configuration.get("providers")
    if not isinstance(profiles, dict):
        return "smoke"
    configured = [
        profile_id
        for profile_id in PROFILE_ORDER
        if isinstance(profiles.get(profile_id), dict)
        and _profile_is_ready(profiles[profile_id])
    ]
    if configured == ["compatible"]:
        return "openai-compatible"
    return "multi-provider" if configured else "smoke"


def _default_profile_id(configuration: dict[str, Any]) -> str:
    default_agent = configuration.get("default_agent")
    for profile_id, agent_id in PROFILE_AGENTS.items():
        if default_agent == agent_id:
            return profile_id
    return "reviewer"


def _config_payload(
    runtime_configuration: dict[str, Any] | None = None,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    configuration = _normalized_runtime_configuration(runtime_configuration)
    profiles = configuration["providers"]
    application_config = dict(APPLICATION_CONFIG)
    if workspace_root is not None:
        auth_root = workspace_root.parent / "config" / "auth"
        application_config["chatgpt_auth"] = {
            "credentials_path": str(auth_root / "chatgpt-auth.json"),
            "rate_limits_path": str(auth_root / "chatgpt-rate-limits.json"),
        }
    ready_profiles = [
        profile_id
        for profile_id in PROFILE_ORDER
        if _profile_is_ready(profiles[profile_id])
    ]
    if not ready_profiles:
        return {
            "plugin_policy": {
                "allow_bash_tools": False,
                "allow_dynamic_plugin_install": False,
                "allow_node_tools": False,
                "allow_remote": False,
            },
            "providers": {
                "embedded": {
                    "provider": "embedded_smoke_provider",
                    "model": "embedded-smoke",
                }
            },
            "plugins": [
                "crystal_lattice_mobile_runtime.EmbeddedSmokeProvider",
                *APPLICATION_PLUGINS,
            ],
            "agents": {"local": {"provider": "embedded"}},
            "application": application_config,
        }
    if workspace_root is None:
        raise ValueError("workspace_root is required for configured providers")

    default_agent = configuration["default_agent"]
    default_profile = next(
        (
            profile_id
            for profile_id in ready_profiles
            if PROFILE_AGENTS[profile_id] == default_agent
        ),
        ready_profiles[0],
    )
    ordered_profiles = [
        default_profile,
        *[profile_id for profile_id in ready_profiles if profile_id != default_profile],
    ]

    provider_plugins: dict[str, list[str]] = {
        "compatible": [
            (
                "reference_openai_compatible_provider.provider."
                "OpenAICompatibleProvider"
            ),
            (
                "reference_openai_compatible_provider.tools_extension."
                "OpenAICompatibleToolsExtension"
            ),
        ],
        "reviewer": [
            (
                "openai_responses_plugins.openai_responses_provider."
                "OpenAIResponsesProvider"
            ),
            (
                "openai_responses_plugins.openai_responses_tools_extension."
                "OpenAIResponsesToolsExtension"
            ),
            (
                "openai_responses_plugins.openai_responses_reasoning_extension."
                "OpenAIResponsesReasoningExtension"
            ),
            (
                "openai_responses_plugins.openai_responses_usage_extension."
                "OpenAIResponsesUsageExtension"
            ),
        ],
        "openai": [
            (
                "openai_responses_plugins.openai_responses_provider."
                "OpenAIResponsesProvider"
            ),
            (
                "openai_responses_plugins.openai_responses_tools_extension."
                "OpenAIResponsesToolsExtension"
            ),
            (
                "openai_responses_plugins.openai_responses_reasoning_extension."
                "OpenAIResponsesReasoningExtension"
            ),
            (
                "openai_responses_plugins.openai_responses_usage_extension."
                "OpenAIResponsesUsageExtension"
            ),
            (
                "openai_responses_plugins.openai_responses_chatgpt_auth_feature."
                "OpenAIResponsesChatGPTAuthFeature"
            ),
        ],
        "openrouter": [
            "openrouter_plugins.openrouter_provider.OpenRouterProvider",
            (
                "openrouter_plugins.openrouter_tools_extension."
                "OpenRouterToolsExtension"
            ),
            (
                "openrouter_plugins.openrouter_reasoning_extension."
                "OpenRouterReasoningExtension"
            ),
            (
                "openrouter_plugins.openrouter_usage_extension."
                "OpenRouterUsageExtension"
            ),
        ],
        "anthropic": [
            "anthropic_plugins.provider.AnthropicProvider",
            "anthropic_plugins.tools_extension.AnthropicToolsExtension",
            "anthropic_plugins.reasoning_extension.AnthropicReasoningExtension",
            "anthropic_plugins.usage_extension.AnthropicUsageExtension",
        ],
    }
    providers: dict[str, dict[str, Any]] = {
        "embedded": {
            "provider": "embedded_smoke_provider",
            "model": "embedded-smoke",
        }
    }
    agents: dict[str, dict[str, Any]] = {"local": {"provider": "embedded"}}
    plugins: list[str] = [
        "crystal_lattice_mobile_runtime.EmbeddedSmokeProvider",
        *APPLICATION_PLUGINS,
    ]
    for profile_id in ordered_profiles:
        profile = profiles[profile_id]
        provider_config: dict[str, Any] = {
            "api_key": profile["api_key"],
            "base_url": profile["base_url"],
            "model": profile["model"],
            "timeout": 180,
            "working_directory": str(workspace_root),
            "allowed_paths": [str(workspace_root)],
        }
        if profile_id == "compatible":
            provider_config["provider"] = "reference_openai_compatible"
            tool_plugins = CLAUDE_TOOL_PLUGINS
        elif profile_id == "reviewer":
            provider_config.update(
                {
                    "provider": "openai_responses",
                    "provider_transport": "requests",
                    "auth_mode": "api",
                    "reasoning_effort": "low",
                    "reasoning_summary": "concise",
                }
            )
            if profile["tls_ca_bundle"]:
                provider_config["tls_ca_bundle"] = profile["tls_ca_bundle"]
            tool_plugins = CODEX_TOOL_PLUGINS
        elif profile_id == "openai":
            provider_config.update(
                {
                    "provider": "openai_responses",
                    "provider_transport": "requests",
                    "auth_mode": profile["auth_mode"],
                    "chatgpt_credentials_path": application_config[
                        "chatgpt_auth"
                    ]["credentials_path"],
                    "chatgpt_rate_limits_path": application_config[
                        "chatgpt_auth"
                    ]["rate_limits_path"],
                    "reasoning_effort": "low",
                    "reasoning_summary": "concise",
                }
            )
            tool_plugins = CODEX_TOOL_PLUGINS
        elif profile_id == "openrouter":
            provider_config["provider"] = "openrouter"
            tool_plugins = CLAUDE_TOOL_PLUGINS
        else:
            provider_config.update(
                {
                    "provider": "anthropic",
                    "provider_transport": "requests",
                    "max_tokens": 4096,
                }
            )
            tool_plugins = CLAUDE_TOOL_PLUGINS

        providers[profile_id] = provider_config
        agent_id = PROFILE_AGENTS[profile_id]
        agents[agent_id] = {
            "provider": profile_id,
            "plugins": list(tool_plugins),
            "working_directory": str(workspace_root),
            "allowed_paths": [str(workspace_root)],
            "tool_family": (
                "codex-like"
                if profile_id in {"reviewer", "openai"}
                else "claude-like"
            ),
        }
        for plugin in provider_plugins[profile_id]:
            if plugin not in plugins:
                plugins.append(plugin)

    return {
        "plugin_policy": {
            "allow_bash_tools": False,
            "allow_dynamic_plugin_install": False,
            "allow_node_tools": False,
            "allow_remote": False,
        },
        "providers": providers,
        "plugins": plugins,
        "agents": agents,
        "application": application_config,
    }


def _provider_import_smoke() -> list[str]:
    from anthropic_plugins.provider import AnthropicProvider
    from openai_responses_plugins.openai_responses_provider import (
        OpenAIResponsesProvider,
    )
    from openrouter_plugins.openrouter_provider import OpenRouterProvider

    openai_state = OpenAIResponsesProvider().init(
        {
            "provider_transport": "requests",
            "api_key": "import-smoke",
            "base_url": "https://api.openai.com/v1",
            "model": "import-smoke",
        }
    )
    openai_client = openai_state.get("client")
    close_openai = getattr(openai_client, "close", None)
    if callable(close_openai):
        close_openai()

    anthropic_client = AnthropicProvider()._client(
        {
            "provider_transport": "requests",
            "api_key": "import-smoke",
            "base_url": "https://api.anthropic.com",
        }
    )
    anthropic_client.close()
    openrouter_state = OpenRouterProvider().init(
        {
            "api_key": "import-smoke",
            "base_url": "https://openrouter.ai/api/v1",
            "model": "import-smoke",
        }
    )
    if not isinstance(openrouter_state, dict):
        raise RuntimeError("OpenRouter provider import smoke returned invalid state")
    return [
        "openai_responses:requests",
        "openrouter:requests",
        "anthropic:requests",
    ]


class MobileRuntime:
    def __init__(
        self,
        runtime_root: str,
        runtime_configuration: dict[str, Any] | None = None,
    ) -> None:
        self.root = Path(runtime_root)
        self.runtime_configuration = _normalized_runtime_configuration(
            runtime_configuration
        )
        self.config_dir = self.root / "config"
        self.sessions_dir = self.root / "sessions"
        self.workspace_dir = self.root / "workspace"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        input_path = self.workspace_dir / "input.txt"
        if not input_path.exists():
            input_path.write_text(
                "alpha beta gamma\n",
                encoding="utf-8",
            )

        self.config_path = self.config_dir / "config.json"
        self.config_path.write_text(
            json.dumps(
                _config_payload(
                    self.runtime_configuration,
                    self.workspace_dir,
                ),
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        self.application = AgentApplication(
            self.config_path,
            self.sessions_dir,
            application_notification_store=InMemoryApplicationNotificationStore(),
            snapshot_selection_store=FilesystemSnapshotSelectionStore(
                self.sessions_dir / ".snapshots"
            ),
            plugin_sources=[DottedClassSource()],
        )

    def create_session(
        self,
        *,
        agent_id: str | None = None,
        system_message: str | None = None,
    ) -> Session:
        available_agents = self.application.list_agents()
        configured_default = self.runtime_configuration.get("default_agent")
        selected_agent = agent_id or (
            configured_default
            if configured_default in available_agents
            else available_agents[0]
        )
        core, base_config, session = self.application.create_session(selected_agent)
        if system_message:
            session = core.add_message(
                session,
                "system",
                system_message,
                config=base_config,
            )
            session = self.application.save_session(session)
        stored = self.application.publish_event(
            {
                "type": "session_created",
                "session_id": session.session_id,
                "agent_id": selected_agent,
            }
        )
        self.application.record_checkpoint(
            session.session_id,
            stored.get("request_id"),
        )
        return session

    def append_message(self, session_id: str, message: dict[str, Any]) -> Session:
        loaded = self.application.load_session(session_id)
        if loaded is None:
            raise KeyError(f"Session {session_id!r} not found")
        core, base_config, session = loaded
        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        overrides = metadata.get("overrides")
        effective_config = self.application.resolve_effective_config(
            base_config,
            session,
            overrides if isinstance(overrides, dict) else {},
        )
        next_session = core.add_message(
            session,
            str(message.get("role") or "user"),
            str(message.get("content") or ""),
            (
                message.get("metadata")
                if isinstance(message.get("metadata"), dict)
                else None
            ),
            effective_config,
            multipart_content=(
                message.get("multipartContent")
                if isinstance(message.get("multipartContent"), list)
                else None
            ),
            tool_result=(
                message.get("toolResult")
                if isinstance(message.get("toolResult"), dict)
                else None
            ),
        )
        persisted = self.application.save_session(next_session)
        index = len(persisted.messages) - 1
        stored_message = persisted.messages[index]
        event = self.application.publish_event(
            {
                "type": "message_appended",
                "session_id": session_id,
                "index": index,
                "message": stored_message.to_dict(),
                "role": stored_message.role,
                "content": stored_message.content,
                "metadata": stored_message.metadata or {},
            }
        )
        self.application.record_checkpoint(session_id, event.get("request_id"))
        return persisted


_runtime: MobileRuntime | None = None


def _get_runtime(
    runtime_root: str,
    runtime_configuration: dict[str, Any] | None = None,
) -> MobileRuntime:
    global _runtime
    resolved = str(Path(runtime_root).resolve())
    normalized_configuration = _normalized_runtime_configuration(runtime_configuration)
    if (
        _runtime is None
        or str(_runtime.root.resolve()) != resolved
        or _runtime.runtime_configuration != normalized_configuration
    ):
        if _runtime is not None:
            _runtime.application.close()
        _runtime = MobileRuntime(resolved, normalized_configuration)
    return _runtime


def shutdown_runtime() -> None:
    global _runtime
    if _runtime is None:
        return
    _runtime.application.close()
    _runtime = None


def run_application_smoke(runtime_root: str) -> dict[str, Any]:
    runtime = _get_runtime(runtime_root)
    session = runtime.create_session()
    stored = runtime.append_message(
        session.session_id,
        {
            "role": "user",
            "content": "Embedded application smoke",
        },
    )

    return {
        "status": "ready",
        "pythonVersion": ".".join(map(str, __import__("sys").version_info[:3])),
        "pythonPlatform": __import__("sys").platform,
        "agents": runtime.application.list_agents(),
        "sessionId": stored.session_id,
        "messageCount": len(stored.messages),
    }


def _response(status: int, data: Any) -> dict[str, Any]:
    return {"status": status, "data": data}


def _int_query(
    query: dict[str, list[str]],
    key: str,
) -> int | None:
    values = query.get(key)
    if not values:
        return None
    return int(values[-1])


def _session_parts(path_parts: list[str]) -> tuple[str, list[str]]:
    if len(path_parts) < 2:
        raise ValueError("Session path is missing a session identifier")
    return path_parts[1], path_parts[2:]


def _session_context(runtime: MobileRuntime, session_id: str):
    loaded = runtime.application.load_session(session_id)
    if loaded is None:
        raise KeyError(f"Session {session_id!r} not found")
    return loaded


def _session_overrides(session: Session) -> dict[str, Any]:
    metadata = session.metadata if isinstance(session.metadata, dict) else {}
    overrides = metadata.get("overrides")
    return overrides if isinstance(overrides, dict) else {}


def _update_session_metadata(
    runtime: MobileRuntime,
    session: Session,
    metadata: dict[str, Any],
) -> Session:
    updated = Session(
        session_id=session.session_id,
        messages=session.messages,
        metadata=metadata,
    )
    return runtime.application.save_session(updated)


def _normalize_message_index(raw_index: int, message_count: int) -> int:
    index = raw_index + message_count if raw_index < 0 else raw_index
    if index < 0 or index >= message_count:
        raise ValueError("message index out of range")
    return index


def _session_plugins(
    application: AgentApplication,
    core: Any,
    base_config: dict[str, Any],
    session: Session,
) -> list[dict[str, Any]]:
    metadata = session.metadata if isinstance(session.metadata, dict) else {}
    agent_id = str(metadata.get("agent_id") or "")
    all_plugins = (
        application.list_plugins_for_agent(agent_id)
        if agent_id
        else application.list_plugins()
    )
    configured_plugins = metadata.get("plugins")
    if isinstance(configured_plugins, list):
        enabled_ids: set[str] | None = {
            value for value in configured_plugins if isinstance(value, str)
        }
        source = "session"
    else:
        default_ids = application.get_agent_plugins(agent_id) if agent_id else None
        enabled_ids = (
            {value for value in default_ids if isinstance(value, str)}
            if isinstance(default_ids, list)
            else None
        )
        source = "agent" if enabled_ids is not None else "implicit"

    effective_config = application.resolve_effective_config(
        base_config,
        session,
        _session_overrides(session),
    )
    try:
        active_by_kind = core.get_plugins_for_config(effective_config)
    except Exception:
        active_by_kind = None

    result: list[dict[str, Any]] = []
    for entry in all_plugins:
        plugin_id = entry.get("id")
        if not isinstance(plugin_id, str) or not plugin_id:
            continue
        kind = entry.get("kind")
        active = True
        if isinstance(active_by_kind, dict) and isinstance(kind, str):
            active_ids = active_by_kind.get(kind)
            if isinstance(active_ids, list):
                active = plugin_id in active_ids
        result.append(
            {
                **entry,
                "enabled": enabled_ids is None or plugin_id in enabled_ids,
                "source": "implicit" if enabled_ids is None else source,
                "active": active,
            }
        )
    return result


def _snapshot_payload(snapshot: Any) -> dict[str, Any]:
    return {
        "snapshot_id": snapshot.snapshot_id,
        "session_id": snapshot.session_id,
        "created_at": snapshot.created_at,
        "reason": snapshot.reason,
    }


def _execute_action_response(
    application: AgentApplication,
    body: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    plugin_id = body.get("plugin")
    action_id = body.get("action_id")
    action_owner = body.get("action_owner")
    inputs = body.get("inputs") or {}
    resolved_plugin_id = plugin_id
    try:
        executed = application.execute_action_with_metadata(
            plugin_id=plugin_id if "plugin" in body else None,
            action_id=action_id,
            params=inputs,
            action_owner=action_owner if isinstance(action_owner, str) else None,
            context={"session_id": session_id} if session_id else None,
        )
        resolved_plugin_id = executed.plugin_id
        return {
            "status": "ok",
            "plugin": executed.plugin_id,
            "action_id": executed.action_id,
            "action_owner": executed.action_owner,
            "result": executed.result if isinstance(executed.result, dict) else {},
        }
    except AgentApplication._ApplicationActionResolutionError as error:
        return {
            "status": "error",
            "plugin": resolved_plugin_id,
            "action_id": action_id,
            "action_owner": action_owner,
            "error_type": getattr(error, "error_type", "unknown_action"),
            "message": str(error),
            "details": getattr(error, "details", {}) or {},
        }
    except AgentApplication._ApplicationActionValidationError as error:
        return {
            "status": "error",
            "plugin": resolved_plugin_id,
            "action_id": action_id,
            "action_owner": action_owner,
            "error_type": "validation",
            "message": str(error),
            "details": getattr(error, "details", {}) or {},
        }
    except KeyError as error:
        error_type = "not_found"
        message = str(error)
    except ReadonlySessionViewError as error:
        error_type = "readonly"
        message = str(error)
    except ValueError as error:
        error_type = "validation"
        message = str(error)
    except Exception as error:
        error_type = "internal"
        message = str(error)
    return {
        "status": "error",
        "plugin": resolved_plugin_id,
        "action_id": action_id,
        "action_owner": action_owner,
        "error_type": error_type,
        "message": message,
        "details": {},
    }


def _handle_session_request(
    runtime: MobileRuntime,
    method: str,
    path_parts: list[str],
    query: dict[str, list[str]],
    body: dict[str, Any],
) -> dict[str, Any]:
    session_id, tail = _session_parts(path_parts)
    application = runtime.application

    if not tail and method == "GET":
        return _response(200, {"session": application.get_session_summary(session_id)})
    if not tail and method == "DELETE":
        application.delete_session(session_id)
        return _response(200, {"status": "ok"})

    if tail == ["summary"] and method == "GET":
        return _response(200, {"session": application.get_session_summary(session_id)})

    if tail == ["agent"]:
        loaded = _session_context(runtime, session_id)
        core, _base_config, session = loaded
        if method == "GET":
            agent_id = session.metadata.get("agent_id")
            return _response(200, {"agent_id": agent_id})
        if method == "PATCH":
            agent_id = str(body.get("agent_id") or "")
            next_core, next_base_config, next_session = application.update_agent(
                agent_id,
                session,
            )
            _ = core, next_core, next_base_config
            application.save_session(next_session)
            return _response(200, {"status": "ok"})

    if tail == ["messages"]:
        if method == "GET":
            session = application.load_session_record(session_id)
            if session is None:
                raise KeyError(f"Session {session_id!r} not found")
            snapshot_id = application.get_selected_session_snapshot(session_id)
            message_count = len(session.messages)
            start = _int_query(query, "start")
            end = _int_query(query, "end")
            start_index, end_index, _step = slice(start, end).indices(message_count)
            messages = [
                {"index": index, "message": session.messages[index].to_dict()}
                for index in range(start_index, end_index)
            ]
            return _response(
                200,
                {
                    "messages": messages,
                    "cursor_event_id": application.get_session_cursor_event_id(
                        session_id
                    ),
                    "active_request_id": application.get_active_session_request_id(
                        session_id
                    )
                    if snapshot_id is None
                    else None,
                    "readonly": snapshot_id is not None,
                    "snapshot_id": snapshot_id,
                },
            )
        if method == "POST":
            session = runtime.append_message(session_id, body)
            return _response(200, {"session": session.to_dict()})
        if method == "DELETE":
            with application.acquire_session_lock(session_id):
                core, base_config, session = _session_context(runtime, session_id)
                message_count = len(session.messages)
                if message_count == 0:
                    raise ValueError("no messages to delete")
                modes = [
                    key for key in ("indices", "range", "last") if key in body
                ]
                if len(modes) != 1:
                    raise ValueError(
                        "Exactly one of 'indices', 'range', or 'last' must be provided"
                    )
                remove_indices: list[int]
                if modes[0] == "indices":
                    indices = body.get("indices")
                    if not isinstance(indices, list):
                        raise ValueError("indices must be a list of integers")
                    remove_indices = [
                        _normalize_message_index(value, message_count)
                        for value in indices
                        if isinstance(value, int) and not isinstance(value, bool)
                    ]
                elif modes[0] == "range":
                    range_value = body.get("range")
                    if not isinstance(range_value, dict):
                        raise ValueError("range must be an object")
                    start = range_value.get("start")
                    end = range_value.get("end")
                    start_index, end_index, _step = slice(start, end).indices(
                        message_count
                    )
                    remove_indices = list(range(start_index, end_index))
                else:
                    last = body.get("last")
                    if not isinstance(last, int) or isinstance(last, bool) or last <= 0:
                        raise ValueError("last must be a positive integer")
                    remove_indices = list(
                        range(max(0, message_count - last), message_count)
                    )
                concrete_indices = sorted(set(remove_indices))
                if not concrete_indices:
                    return _response(
                        200,
                        {
                            "session": session.to_dict(),
                            "deleted_indices": [],
                        },
                    )
                application.create_session_snapshot(
                    session_id,
                    reason=(
                        "Before deleting messages ["
                        + ", ".join(str(index) for index in concrete_indices)
                        + "]"
                    ),
                )
                effective_config = application.resolve_effective_config(
                    base_config,
                    session,
                    _session_overrides(session),
                )
                next_session = core.slice_session(
                    session,
                    effective_config,
                    remove_indices=concrete_indices,
                )
                application.save_session(next_session)
                stored = application.publish_event(
                    {
                        "type": "messages_deleted",
                        "session_id": session_id,
                        "indices": concrete_indices,
                    }
                )
                application.record_checkpoint(
                    session_id,
                    stored.get("request_id"),
                )
            return _response(
                200,
                {
                    "session": next_session.to_dict(),
                    "deleted_indices": concrete_indices,
                },
            )

    if len(tail) == 2 and tail[0] == "messages" and method == "PATCH":
        index = int(tail[1])
        core, base_config, session = _session_context(runtime, session_id)
        effective_config = application.resolve_effective_config(
            base_config,
            session,
            _session_overrides(session),
        )
        next_session = core.modify_message(
            session,
            index,
            str(body.get("content") or ""),
            effective_config,
        )
        application.save_session(next_session)
        application.publish_event(
            {
                "type": "message_modified",
                "session_id": session_id,
                "index": index,
                "message": next_session.messages[index].to_dict(),
            }
        )
        return _response(200, {"status": "ok"})

    if tail == ["send"] and method == "POST":
        started = application.start_session_request(
            session_id,
            (
                body.get("config_overrides")
                if isinstance(body.get("config_overrides"), dict)
                else {}
            ),
            stream=False,
        )
        return _response(
            200,
            {
                "status": started.status,
                "request_id": started.request_id,
            },
        )

    if tail == ["send_message"] and method == "POST":
        message = body.get("message")
        if not isinstance(message, dict):
            raise ValueError("send_message requires a message")
        started = application.start_session_request_with_message(
            session_id,
            role=str(message.get("role") or "user"),
            content=str(message.get("content") or ""),
            metadata=(
                message.get("metadata")
                if isinstance(message.get("metadata"), dict)
                else None
            ),
            multipart_content=(
                message.get("multipartContent")
                if isinstance(message.get("multipartContent"), list)
                else None
            ),
            overrides=(
                body.get("config_overrides")
                if isinstance(body.get("config_overrides"), dict)
                else {}
            ),
            stream=False,
        )
        return _response(
            200,
            {
                "status": started.status,
                "request_id": started.request_id,
                "session_id": session_id,
            },
        )

    if tail == ["plugins"] and method == "GET":
        core, base_config, session = _session_context(runtime, session_id)
        return _response(
            200,
            {
                "plugins": _session_plugins(
                    application,
                    core,
                    base_config,
                    session,
                )
            },
        )
    if tail == ["plugins"] and method in {"PUT", "DELETE"}:
        with application.acquire_session_lock(session_id):
            core, base_config, session = _session_context(runtime, session_id)
            metadata = (
                dict(session.metadata) if isinstance(session.metadata, dict) else {}
            )
            if method == "PUT":
                enabled = body.get("enabled")
                if not isinstance(enabled, list):
                    raise ValueError("enabled must be a list of plugin ids")
                metadata["plugins"] = list(
                    dict.fromkeys(
                        value
                        for value in enabled
                        if isinstance(value, str) and value
                    )
                )
            else:
                metadata.pop("plugins", None)
            updated = _update_session_metadata(runtime, session, metadata)
            refreshed = application.load_session(session_id)
            if refreshed is not None:
                core, base_config, updated = refreshed
            plugins = _session_plugins(
                application,
                core,
                base_config,
                updated,
            )
        return _response(
            200,
            {"session": updated.to_dict(), "plugins": plugins},
        )

    if tail == ["ui-schema"] and method == "GET":
        core, base_config, session = _session_context(runtime, session_id)
        effective_config = application.resolve_effective_config(
            base_config,
            session,
            _session_overrides(session),
        )
        return _response(
            200,
            {"elements": core.get_ui_schema(config=effective_config) or []},
        )

    if tail == ["application", "ui-schema"] and method == "GET":
        plugin = (query.get("plugin") or [None])[-1]
        return _response(
            200,
            {
                "elements": application.get_session_application_ui_schema(
                    session_id,
                    plugin=plugin,
                )
            },
        )
    if tail == ["config", "schema"] and method == "GET":
        core, _base_config, _session = _session_context(runtime, session_id)
        return _response(200, {"schema": core.get_config_schema() or []})
    if tail == ["config", "base"] and method == "GET":
        _core, base_config, _session = _session_context(runtime, session_id)
        return _response(200, {"config": base_config})

    if tail == ["overrides"]:
        _core, _base_config, session = _session_context(runtime, session_id)
        if method == "GET":
            return _response(200, {"overrides": _session_overrides(session)})
        if method == "PATCH":
            values = body.get("values")
            if not isinstance(values, dict):
                raise ValueError("Override values must be an object")
            metadata = dict(session.metadata)
            metadata["overrides"] = {**_session_overrides(session), **values}
            _update_session_metadata(runtime, session, metadata)
            return _response(200, {"status": "ok"})

    if len(tail) == 2 and tail[0] == "overrides" and method == "DELETE":
        _core, _base_config, session = _session_context(runtime, session_id)
        metadata = dict(session.metadata)
        overrides = dict(_session_overrides(session))
        overrides.pop(tail[1], None)
        metadata["overrides"] = overrides
        _update_session_metadata(runtime, session, metadata)
        return _response(200, {"status": "ok"})

    if tail == ["actions"] and method == "POST":
        return _response(
            200,
            _execute_action_response(
                application,
                body,
                session_id=session_id,
            ),
        )

    if tail == ["snapshots"]:
        if method == "GET":
            return _response(
                200,
                {
                    "snapshots": [
                        _snapshot_payload(snapshot)
                        for snapshot in application.list_session_snapshots(
                            session_id
                        )
                    ]
                },
            )
        if method == "POST":
            reason = body.get("reason")
            if not isinstance(reason, str) or not reason.strip():
                raise ValueError("reason must be a non-empty string")
            with application.acquire_session_lock(session_id):
                snapshot = application.create_session_snapshot(
                    session_id,
                    reason=reason.strip(),
                    metadata=(
                        body.get("metadata")
                        if isinstance(body.get("metadata"), dict)
                        else None
                    ),
                )
            return _response(200, {"snapshot": _snapshot_payload(snapshot)})
    if tail == ["snapshots", "selected"]:
        if method == "GET":
            return _response(
                200,
                {
                    "snapshot_id": application.get_selected_session_snapshot(
                        session_id
                    )
                },
            )
        if method == "DELETE":
            with application.acquire_session_lock(session_id):
                application.clear_selected_session_snapshot(session_id)
                stored = application.publish_event(
                    {
                        "type": "session_snapshot_cleared",
                        "session_id": session_id,
                    }
                )
                event_id = stored.get("event_id")
                if isinstance(event_id, str) and event_id:
                    application.advance_session_cursor(session_id, event_id)
            return _response(200, {"status": "ok", "snapshot_id": None})
    if len(tail) == 3 and tail[0] == "snapshots" and method == "POST":
        snapshot_id = tail[1]
        operation = tail[2]
        if operation == "select":
            with application.acquire_session_lock(session_id):
                application.select_session_snapshot(session_id, snapshot_id)
                stored = application.publish_event(
                    {
                        "type": "session_snapshot_selected",
                        "session_id": session_id,
                        "snapshot_id": snapshot_id,
                    }
                )
                event_id = stored.get("event_id")
                if isinstance(event_id, str) and event_id:
                    application.advance_session_cursor(session_id, event_id)
            return _response(
                200,
                {"status": "ok", "snapshot_id": snapshot_id},
            )
        if operation == "restore":
            with application.acquire_session_lock(session_id):
                restored = application.restore_session_snapshot(
                    session_id,
                    snapshot_id,
                )
                stored = application.publish_event(
                    {
                        "type": "session_restored_from_snapshot",
                        "session_id": session_id,
                        "snapshot_id": snapshot_id,
                    }
                )
                event_id = stored.get("event_id")
                if isinstance(event_id, str) and event_id:
                    application.advance_session_cursor(session_id, event_id)
            return _response(
                200,
                {"status": "ok", "session": restored.to_dict()},
            )
    if len(tail) == 2 and tail[0] == "snapshots" and method == "DELETE":
        return _response(
            200,
            {
                "status": "ok",
                "deleted": bool(
                    application.delete_session_snapshot(session_id, tail[1])
                ),
            },
        )

    if tail == ["fork"] and method == "POST":
        raw_index = body.get("index", -1)
        if not isinstance(raw_index, int) or isinstance(raw_index, bool):
            raise ValueError("index must be an integer")
        with application.acquire_session_lock(session_id):
            core, base_config, session = _session_context(runtime, session_id)
            if not session.messages:
                raise ValueError("no messages to fork")
            target_index = _normalize_message_index(
                raw_index,
                len(session.messages),
            )
            _new_core, _new_config, forked = application.fork_session(
                core,
                session,
                base_config,
                upto_index=target_index,
                new_session_id=str(uuid.uuid4()),
            )
            application.save_session(forked)
            stored = application.publish_event(
                {
                    "type": "session_created",
                    "session_id": forked.session_id,
                    "agent_id": forked.metadata.get("agent_id"),
                    "source_session_id": session_id,
                    "fork_upto_index": target_index,
                }
            )
            application.record_checkpoint(
                forked.session_id,
                stored.get("request_id"),
            )
        return _response(
            200,
            {
                "session": forked.to_dict(),
                "source_session_id": session_id,
                "fork_upto_index": target_index,
            },
        )
    if tail == ["notifications"] and method == "GET":
        return _response(
            200,
            {
                "notifications": application.list_session_notifications(
                    session_id,
                    include_terminal=True,
                )
            },
        )

    raise ValueError(f"Unsupported embedded session route: {method} {'/'.join(tail)}")


def _handle_request(
    runtime: MobileRuntime,
    request: dict[str, Any],
) -> dict[str, Any]:
    method = str(request.get("method") or "GET").upper()
    parsed = urlsplit(str(request.get("path") or "/"))
    path_parts = [unquote(part) for part in parsed.path.split("/") if part]
    query = parse_qs(parsed.query)
    body = request.get("body")
    body = body if isinstance(body, dict) else {}
    application = runtime.application

    if path_parts == ["api", "hello"] and method == "GET":
        output_path = runtime.workspace_dir / "output.txt"
        return _response(
            200,
            {
                "message": "Embedded Python runtime is ready",
                "provider_mode": _runtime_provider_mode(
                    runtime.runtime_configuration
                ),
                "workspace_output": (
                    output_path.read_text(encoding="utf-8")
                    if output_path.is_file()
                    else None
                ),
            },
        )

    if path_parts == ["api", "data"] and method in {"GET", "PUT"}:
        return _response(
            200,
            {
                "message": "Embedded Python runtime",
                "echo": body if method == "PUT" else None,
            },
        )

    if path_parts == ["embedded", "runtime", "status"] and method == "GET":
        return _response(
            200,
            {
                "provider_mode": _runtime_provider_mode(
                    runtime.runtime_configuration
                ),
                "default_agent": runtime.runtime_configuration["default_agent"],
                "providers": {
                    profile_id: {
                        "enabled": profile["enabled"],
                        "has_api_key": bool(profile["api_key"]),
                        "model": profile["model"],
                        "base_url": profile["base_url"],
                        "ready": _profile_is_ready(profile),
                    }
                    for profile_id, profile in runtime.runtime_configuration[
                        "providers"
                    ].items()
                },
            },
        )

    if path_parts == ["embedded", "runtime", "provider-imports"] and method == "GET":
        return _response(200, {"providers": _provider_import_smoke()})

    if path_parts == ["embedded", "runtime", "web-fetch-smoke"] and method == "GET":
        from embedded_claude_tools import ClaudeLikeWebFetchTool

        tool = ClaudeLikeWebFetchTool()
        result = tool.execute_tool(
            "WebFetch",
            {
                "url": "https://www.python.org/",
                "prompt": "Identify the page title",
            },
            tool.init({}),
        )
        if not result.get("success"):
            raise RuntimeError(str(result.get("error") or "WebFetch failed"))
        content = str(result.get("result") or "")
        title = next(
            (
                line.removeprefix("Title:").strip()
                for line in content.splitlines()
                if line.startswith("Title:")
            ),
            "",
        )
        return _response(
            200,
            {
                "status": "ok",
                "title": title,
                "content": content,
            },
        )

    if path_parts == ["embedded", "runtime", "validate"] and method == "POST":
        requested_profile_id = str(
            body.get("profile_id")
            or _default_profile_id(runtime.runtime_configuration)
        )
        profiles = runtime.runtime_configuration["providers"]
        profile = profiles.get(requested_profile_id)
        if not isinstance(profile, dict) or not _profile_is_ready(profile):
            return _response(400, {"detail": "Provider configuration is incomplete"})
        provider_config = {
            "api_key": profile["api_key"],
            "base_url": profile["base_url"],
            "model": profile["model"],
            "timeout": 15,
        }
        if profile.get("tls_ca_bundle"):
            provider_config["tls_ca_bundle"] = profile["tls_ca_bundle"]
        if requested_profile_id == "compatible":
            from reference_openai_compatible_provider.provider import (
                OpenAICompatibleProvider,
            )

            provider = OpenAICompatibleProvider()
        elif requested_profile_id in {"reviewer", "openai"}:
            from openai_responses_plugins.openai_responses_provider import (
                OpenAIResponsesProvider,
            )

            provider_config.update(
                {
                    "provider_transport": "requests",
                    "auth_mode": (
                        profile.get("auth_mode")
                        if requested_profile_id == "openai"
                        else "api"
                    ),
                }
            )
            provider = OpenAIResponsesProvider()
        elif requested_profile_id == "openrouter":
            from openrouter_plugins.openrouter_provider import OpenRouterProvider

            provider = OpenRouterProvider()
        elif requested_profile_id == "anthropic":
            from anthropic_plugins.provider import AnthropicProvider

            provider_config["provider_transport"] = "requests"
            provider = AnthropicProvider()
        else:
            return _response(404, {"detail": "Unknown provider profile"})
        models = provider.get_models(provider_config)
        model_ids = {
            model.get("id")
            for model in models
            if isinstance(model, dict) and isinstance(model.get("id"), str)
        }
        configured_model = profile["model"]
        if configured_model not in model_ids:
            return _response(
                401,
                {
                    "detail": (
                        "The proxy credentials were rejected or the configured "
                        "model is unavailable"
                    )
                },
            )
        return _response(
            200,
            {
                "status": "ok",
                "profile_id": requested_profile_id,
                "model": configured_model,
            },
        )

    if path_parts == ["embedded", "workspace", "reset"] and method == "POST":
        input_content = body.get("input")
        if not isinstance(input_content, str):
            input_content = "alpha beta gamma\n"
        (runtime.workspace_dir / "input.txt").write_text(
            input_content,
            encoding="utf-8",
        )
        (runtime.workspace_dir / "output.txt").unlink(missing_ok=True)
        return _response(200, {"status": "ok"})

    if path_parts == ["embedded", "workspace", "output"] and method == "GET":
        output_path = runtime.workspace_dir / "output.txt"
        return _response(
            200,
            {
                "exists": output_path.is_file(),
                "content": (
                    output_path.read_text(encoding="utf-8")
                    if output_path.is_file()
                    else ""
                ),
                "provider_mode": _runtime_provider_mode(
                    runtime.runtime_configuration
                ),
            },
        )

    if path_parts == ["agents"] and method == "GET":
        return _response(200, {"agents": application.list_agents()})

    if path_parts == ["sessions"] and method == "POST":
        session = runtime.create_session(
            agent_id=(
                str(body.get("agent_id"))
                if isinstance(body.get("agent_id"), str)
                else None
            ),
            system_message=(
                str(body.get("system_message"))
                if isinstance(body.get("system_message"), str)
                else None
            ),
        )
        return _response(
            200,
            {
                "session": session.to_dict(),
                "errors": application.get_config_errors(),
            },
        )

    if path_parts == ["sessions"] and method == "GET":
        limit = _int_query(query, "limit")
        return _response(
            200,
            {"sessions": application.list_session_summaries(limit=limit)},
        )

    if path_parts == ["sessions", "request-statuses"] and method == "POST":
        session_ids = body.get("session_ids")
        if not isinstance(session_ids, list):
            session_ids = []
        return _response(
            200,
            application.get_session_request_statuses(
                [value for value in session_ids if isinstance(value, str)]
            ),
        )

    if path_parts and path_parts[0] == "sessions":
        return _handle_session_request(
            runtime,
            method,
            path_parts,
            query,
            body,
        )

    if path_parts == ["events"] and method == "GET":
        result = application.get_event_store().list(
            since_id=(query.get("since_id") or [None])[-1],
            request_id=(query.get("request_id") or [None])[-1],
            session_id=(query.get("session_id") or [None])[-1],
            limit=_int_query(query, "limit") or 100,
        )
        return _response(200, result)

    if len(path_parts) == 3 and path_parts[:1] == ["requests"]:
        if path_parts[2] == "cancel" and method == "POST":
            application.cancel_request(path_parts[1])
            return _response(200, {"status": "ok"})
        if path_parts[2] == "soft-cancel" and method == "POST":
            application.soft_cancel_request(path_parts[1])
            return _response(
                200,
                {
                    "request_id": path_parts[1],
                    "status": "soft_cancel_requested",
                },
            )

    if path_parts == ["application", "actions"] and method == "GET":
        plugin = (query.get("plugin") or [None])[-1]
        actions = [
            action
            for action in application.get_application_actions()
            if isinstance(action, dict)
            and (plugin is None or action.get("plugin") == plugin)
        ]
        return _response(200, {"actions": actions})
    if path_parts == ["application", "ui-schema"] and method == "GET":
        plugin = (query.get("plugin") or [None])[-1]
        elements = [
            element
            for element in application.get_application_ui_schema()
            if isinstance(element, dict)
            and (plugin is None or element.get("plugin") == plugin)
        ]
        return _response(200, {"elements": elements})
    if path_parts == ["application", "plugins"] and method == "GET":
        return _response(
            200,
            {"plugins": application.list_application_plugins()},
        )
    if path_parts == ["application", "notifications"] and method == "GET":
        return _response(
            200,
            {
                "notifications": application.list_application_notifications(
                    include_terminal=True,
                )
            },
        )
    if path_parts == ["server", "settings"]:
        if method == "GET":
            return _response(
                200,
                {"settings": application.get_server_settings()},
            )
        if method == "PATCH":
            values = body.get("values", body)
            if not isinstance(values, dict):
                raise ValueError(
                    "server settings body must be an object or {'values': object}"
                )
            return _response(
                200,
                {
                    "settings": application.patch_server_settings(
                        values,
                        source="api",
                    )
                },
            )
    if path_parts == ["server", "settings", "ui-schema"] and method == "GET":
        plugin = (query.get("plugin") or [None])[-1]
        elements = [
            element
            for element in application.get_server_settings_ui_schema()
            if isinstance(element, dict)
            and (plugin is None or element.get("plugin") == plugin)
        ]
        return _response(200, {"elements": elements})
    if (
        len(path_parts) == 3
        and path_parts[:2] == ["server", "settings"]
        and method == "DELETE"
    ):
        return _response(
            200,
            {
                "settings": application.delete_server_setting(
                    path_parts[2],
                    source="api",
                )
            },
        )

    if path_parts == ["actions"] and method == "POST":
        return _response(
            200,
            _execute_action_response(application, body),
        )

    raise ValueError(f"Unsupported embedded runtime route: {method} {parsed.path}")


def execute_json(command_json: str, runtime_root: str) -> str:
    try:
        request = json.loads(command_json)
        if not isinstance(request, dict):
            raise ValueError("Embedded runtime request must be an object")
        runtime_configuration = request.get("runtimeConfiguration")
        response = _handle_request(
            _get_runtime(
                runtime_root,
                (
                    runtime_configuration
                    if isinstance(runtime_configuration, dict)
                    else None
                ),
            ),
            request,
        )
    except KeyError as error:
        response = _response(404, {"detail": str(error)})
    except ReadonlySessionViewError as error:
        response = _response(409, {"detail": str(error)})
    except ValueError as error:
        response = _response(400, {"detail": str(error)})
    except Exception as error:
        response = _response(
            500,
            {"detail": f"{type(error).__name__}: {error}"},
        )
    return json.dumps(response, separators=(",", ":"))
