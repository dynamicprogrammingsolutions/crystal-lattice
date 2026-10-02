"""Codex model-family helpers for shell tool auto-selection."""

from __future__ import annotations

import re


SHELL_ARRAY_MODEL_RE = re.compile(r"^(?:openai/)?gpt-(?:5(?:\.0)?)(?:-mini)?$")

FUTURE_SHELL_COMMAND_MODEL_RE = re.compile(
    r"^(?:openai/)?gpt-(?:5\.(?:[1-9]\d*)|[6-9](?:\.\d+)?|\d{2,}(?:\.\d+)?)"
    r"(?:-(?:mini|sol|terra|luna|astra))?$"
)

CODEX_SUFFIX_MODEL_RE = re.compile(r".*-codex(?:-(?:mini|max))?$")


def uses_shell_command_model(model: str) -> bool:
    """Return True when a model should auto-select ``shell_command``."""

    if not isinstance(model, str) or not model:
        return False
    if SHELL_ARRAY_MODEL_RE.match(model):
        return False
    return bool(
        CODEX_SUFFIX_MODEL_RE.match(model)
        or FUTURE_SHELL_COMMAND_MODEL_RE.match(model)
    )


def is_shell_command_family_model(model: str) -> bool:
    """Return whether the model belongs to the shell-command family."""

    return uses_shell_command_model(model)


def is_codex_variant_model(model: str) -> bool:
    """Backward-compatible alias for the shell-command family helper."""

    return is_shell_command_family_model(model)


__all__ = [
    "CODEX_SUFFIX_MODEL_RE",
    "FUTURE_SHELL_COMMAND_MODEL_RE",
    "SHELL_ARRAY_MODEL_RE",
    "is_codex_variant_model",
    "is_shell_command_family_model",
    "uses_shell_command_model",
]