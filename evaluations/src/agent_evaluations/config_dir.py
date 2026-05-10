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
