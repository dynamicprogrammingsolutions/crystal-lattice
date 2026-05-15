from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any, Dict, Mapping, Tuple

from agent_app.application_future import AgentApplication
from agent_app.config import (
    build_config_resolution_env,
    load_raw_config,
    resolve_placeholders,
)
from agent_app.events import InMemoryEventStore


def _collect_dotenv_values(config_dir: Path) -> Dict[str, str]:
    try:
        from dotenv import dotenv_values  # type: ignore[import-not-found]
    except Exception:
        return {}

    env_path = config_dir / ".env"
    if not env_path.is_file():
        return {}

    collected: Dict[str, str] = {}
    try:
        values = dotenv_values(str(env_path))
    except Exception:
        return {}

    for key, value in values.items():
        if not isinstance(key, str) or not key:
            continue
        if not isinstance(value, str):
            continue
        if key in os.environ:
            continue
        collected[key] = value
    return collected


@dataclass(frozen=True)
class EvaluationPaths:
    config_dir: Path
    config_path: Path
    agents_path: Path
    env_path: Path
    auth_dir: Path
    cache_root: Path
    results_root: Path
    manifests_root: Path
    workspace_root: Path
    profiles_root: Path


@dataclass(frozen=True)
class EvaluationEnvironment:
    paths: EvaluationPaths
    config_env: Dict[str, str]
    env_overrides: Dict[str, str]
    raw_config: Dict[str, Any]
    resolved_config: Dict[str, Any]
    config_errors: list[Dict[str, Any]]

    def build_application(self, *, session_root: Path | None = None) -> AgentApplication:
        root = session_root or (self.paths.results_root / "_sessions")
        root.mkdir(parents=True, exist_ok=True)
        return AgentApplication(
            str(self.paths.config_path),
            str(root),
            event_store=InMemoryEventStore(),
            env_overrides=self.env_overrides,
        )


def _root_from_subtree(config_dir: Path, raw_value: Any, fallback_name: str) -> Path:
    if isinstance(raw_value, str) and raw_value.strip():
        return Path(raw_value).expanduser()
    return config_dir / fallback_name


def load_evaluation_environment(config_dir: str | Path) -> EvaluationEnvironment:
    config_dir_path = Path(config_dir).expanduser().resolve()
    config_path = config_dir_path / "config.json"
    agents_path = config_dir_path / "AGENTS.md"
    env_path = config_dir_path / ".env"
    auth_dir = config_dir_path / "auth"

    raw_config = load_raw_config(config_path)
    config_env = _collect_dotenv_values(config_dir_path)
    env_overrides = {
        "CONFIG_DIR": str(config_dir_path),
        **config_env,
    }
    resolution_env = build_config_resolution_env(
        config_path,
        config_env=config_env,
        env_overrides=env_overrides,
    )
    resolved_config, errors = resolve_placeholders(raw_config, env=resolution_env)

    eval_cfg = resolved_config.get("agentic_evaluations")
    if not isinstance(eval_cfg, dict):
        eval_cfg = {}

    cache_root = _root_from_subtree(
        config_dir_path,
        eval_cfg.get("cache_root"),
        "cache",
    )
    results_root = _root_from_subtree(
        config_dir_path,
        eval_cfg.get("results_root"),
        "results",
    )
    manifests_root = _root_from_subtree(
        config_dir_path,
        eval_cfg.get("manifests_root"),
        "manifests",
    )
    workspace_root = _root_from_subtree(
        config_dir_path,
        eval_cfg.get("workspace_root"),
        "workspaces",
    )
    profiles_root = _root_from_subtree(
        config_dir_path,
        eval_cfg.get("profiles_root"),
        "profiles",
    )

    paths = EvaluationPaths(
        config_dir=config_dir_path,
        config_path=config_path,
        agents_path=agents_path,
        env_path=env_path,
        auth_dir=auth_dir,
        cache_root=cache_root,
        results_root=results_root,
        manifests_root=manifests_root,
        workspace_root=workspace_root,
        profiles_root=profiles_root,
    )

    return EvaluationEnvironment(
        paths=paths,
        config_env=config_env,
        env_overrides=env_overrides,
        raw_config=raw_config,
        resolved_config=resolved_config,
        config_errors=errors,
    )


def merge_dicts(base: Mapping[str, Any], overlay: Mapping[str, Any]) -> Dict[str, Any]:
    merged: Dict[str, Any] = dict(base)
    for key, value in overlay.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, Mapping)
        ):
            merged[key] = merge_dicts(merged[key], value)
        else:
            merged[key] = value
    return merged


def benchmark_settings(env: EvaluationEnvironment) -> Dict[str, Any]:
    subtree = env.resolved_config.get("agentic_evaluations")
    if isinstance(subtree, dict):
        return dict(subtree)
    return {}


def _resolve_profile_path_override(config_dir: Path, raw_value: Any) -> Path | None:
    if not isinstance(raw_value, str) or not raw_value.strip():
        return None
    candidate = Path(raw_value).expanduser()
    if candidate.is_absolute():
        return candidate
    return (config_dir / candidate).resolve()


def _resolve_artifact_root(raw_value: Any) -> Path | None:
    if not isinstance(raw_value, str) or not raw_value.strip():
        return None
    return Path(raw_value).expanduser().resolve()


def _artifact_scoped_path(
    *,
    config_dir: Path,
    current_root: Path,
    category: str,
    artifact_root: Path,
) -> Path:
    base_category_root = (config_dir / category).resolve()
    try:
        suffix = current_root.resolve().relative_to(base_category_root)
    except ValueError:
        parts = list(current_root.parts)
        if category in parts:
            suffix = Path(*parts[parts.index(category) + 1 :])
        else:
            suffix = Path(current_root.name)
    if str(suffix) == ".":
        return artifact_root / category
    return artifact_root / category / suffix


def apply_profile_path_overrides(
    env: EvaluationEnvironment,
    profile_payload: Mapping[str, Any],
) -> EvaluationEnvironment:
    raw_paths = profile_payload.get("paths")
    if not isinstance(raw_paths, Mapping):
        return env

    paths = env.paths
    cache_root = _resolve_profile_path_override(paths.config_dir, raw_paths.get("cache_root")) or paths.cache_root
    results_root = _resolve_profile_path_override(paths.config_dir, raw_paths.get("results_root")) or paths.results_root
    manifests_root = (
        _resolve_profile_path_override(paths.config_dir, raw_paths.get("manifests_root")) or paths.manifests_root
    )
    workspace_root = (
        _resolve_profile_path_override(paths.config_dir, raw_paths.get("workspace_root")) or paths.workspace_root
    )

    return EvaluationEnvironment(
        paths=EvaluationPaths(
            config_dir=paths.config_dir,
            config_path=paths.config_path,
            agents_path=paths.agents_path,
            env_path=paths.env_path,
            auth_dir=paths.auth_dir,
            cache_root=cache_root,
            results_root=results_root,
            manifests_root=manifests_root,
            workspace_root=workspace_root,
            profiles_root=paths.profiles_root,
        ),
        config_env=env.config_env,
        env_overrides=env.env_overrides,
        raw_config=env.raw_config,
        resolved_config=env.resolved_config,
        config_errors=env.config_errors,
    )


def apply_artifact_root(
    env: EvaluationEnvironment,
    artifact_root: str | Path | None,
) -> EvaluationEnvironment:
    resolved_artifact_root = _resolve_artifact_root(str(artifact_root) if artifact_root is not None else None)
    if resolved_artifact_root is None:
        return env

    paths = env.paths
    results_root = _artifact_scoped_path(
        config_dir=paths.config_dir,
        current_root=paths.results_root,
        category="results",
        artifact_root=resolved_artifact_root,
    )
    workspace_root = _artifact_scoped_path(
        config_dir=paths.config_dir,
        current_root=paths.workspace_root,
        category="workspaces",
        artifact_root=resolved_artifact_root,
    )
    return EvaluationEnvironment(
        paths=EvaluationPaths(
            config_dir=paths.config_dir,
            config_path=paths.config_path,
            agents_path=paths.agents_path,
            env_path=paths.env_path,
            auth_dir=paths.auth_dir,
            cache_root=paths.cache_root,
            results_root=results_root,
            manifests_root=paths.manifests_root,
            workspace_root=workspace_root,
            profiles_root=paths.profiles_root,
        ),
        config_env=env.config_env,
        env_overrides=env.env_overrides,
        raw_config=env.raw_config,
        resolved_config=env.resolved_config,
        config_errors=env.config_errors,
    )
