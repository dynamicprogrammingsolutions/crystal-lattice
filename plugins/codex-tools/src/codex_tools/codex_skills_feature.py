from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

from agent_core.types import FeaturePlugin

from skill_shared import DiscoveryOptions

from .codex_skill_loader import (
    build_skill_injection_message,
    collect_explicit_skill_mentions,
    existing_injected_skill_keys,
    load_codex_skills,
    render_codex_skills_section,
)


class CodexSkillsFeature(FeaturePlugin):
    name: str = "codex_skills"
    version: str = "0.1.0"
    priority: int = 90

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "skills_enabled": {
                "type": "boolean",
                "default": True,
                "description": "Enable Codex skills discovery and manual activation.",
            },
            "skills_roots": {
                "type": "array",
                "items": {"type": "string"},
                "default": [],
                "description": "Ordered explicit skill roots for Codex skill discovery.",
            },
            "skills_follow_symlinks": {
                "type": "boolean",
                "default": False,
                "description": "Whether skill discovery follows symlinked directories.",
            },
            "skills_max_scan_depth": {
                "type": "integer",
                "default": 6,
                "description": "Maximum directory depth scanned under each explicit skill root.",
            },
            "skills_max_dirs_per_root": {
                "type": "integer",
                "default": 2000,
                "description": "Maximum directories scanned per explicit skill root.",
            },
        }

    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        context: Dict[str, Any] | None = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        config = state.get("config", {}) or {}
        if not bool(config.get("skills_enabled", True)):
            return list(native_messages), state

        roots = self._resolve_roots(config)
        options = DiscoveryOptions(
            follow_symlinks=bool(config.get("skills_follow_symlinks", False)),
            max_scan_depth=max(0, int(config.get("skills_max_scan_depth", 6) or 6)),
            max_dirs_per_root=max(
                1, int(config.get("skills_max_dirs_per_root", 2000) or 2000)
            ),
        )
        skills = load_codex_skills(roots, options=options)
        skills_section = render_codex_skills_section(skills)

        existing_variables = state.get("system_message_variables")
        merged_variables = (
            dict(existing_variables) if isinstance(existing_variables, dict) else {}
        )
        merged_variables["CODEX_SKILLS_SECTION"] = skills_section
        new_state = {**state, "system_message_variables": merged_variables}

        base_messages = self._request_messages_or_native(native_messages, state)
        selected_skills = collect_explicit_skill_mentions(base_messages, skills)
        if not selected_skills:
            return list(native_messages), new_state

        existing_skill_keys = existing_injected_skill_keys(base_messages)
        selected_skills = [
            skill
            for skill in selected_skills
            if (skill.name.lower(), skill.path_to_skills_md.as_posix())
            not in existing_skill_keys
        ]
        if not selected_skills:
            return list(native_messages), new_state

        if not isinstance(context, dict):
            return list(native_messages), new_state

        core = context.get("core")
        request_config = context.get("config")
        if core is None or not hasattr(core, "core_messages_to_native"):
            return list(native_messages), new_state
        if not isinstance(request_config, dict):
            request_config = config

        injection_core_messages = []
        for skill in selected_skills:
            try:
                contents = skill.path_to_skills_md.read_text(encoding="utf-8")
            except OSError:
                continue
            injection_core_messages.append(
                build_skill_injection_message(
                    skill,
                    contents=contents,
                )
            )

        if not injection_core_messages:
            return list(native_messages), new_state

        converted_native = core.core_messages_to_native(
            injection_core_messages,
            request_config,
        )
        if not isinstance(converted_native, list) or not converted_native:
            return list(native_messages), new_state

        returned_native = [*native_messages, *converted_native]
        request = state.get("request") or {}
        request_messages = request.get("messages")
        if isinstance(request_messages, list):
            new_request = {
                **request,
                "messages": [*request_messages, *converted_native],
            }
            return returned_native, {**new_state, "request": new_request}

        return returned_native, new_state

    def _resolve_roots(self, config: Dict[str, Any]) -> list[Path]:
        raw_roots = config.get("skills_roots") or []
        if not isinstance(raw_roots, list):
            return []

        working_directory = config.get("working_directory") or "."
        try:
            base_dir = Path(str(working_directory)).resolve()
        except OSError:
            base_dir = Path(".").resolve()

        roots: list[Path] = []
        for raw_root in raw_roots:
            if not isinstance(raw_root, str) or not raw_root:
                continue
            candidate = Path(raw_root)
            if not candidate.is_absolute():
                candidate = base_dir / candidate
            roots.append(candidate)
        return roots

    def _request_messages_or_native(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        request = state.get("request") or {}
        request_messages = request.get("messages")
        if isinstance(request_messages, list):
            return list(request_messages)
        return list(native_messages)

__all__ = ["CodexSkillsFeature"]