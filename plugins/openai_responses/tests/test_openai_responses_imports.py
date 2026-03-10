from __future__ import annotations

import importlib
import json
from pathlib import Path

from openai_responses_plugins import (
    OpenAIResponsesProvider,
    OpenAIResponsesReasoningExtension,
    OpenAIResponsesToolsExtension,
    OpenAIResponsesUsageExtension,
    OpenAIResponsesVerbosityExtension,
)


def _import_symbol(dotted_path: str):
    module_path, _, symbol_name = dotted_path.rpartition(".")
    module = importlib.import_module(module_path)
    return getattr(module, symbol_name)


def test_all_entry_classes_are_importable() -> None:
    assert OpenAIResponsesProvider.name == "openai_responses"
    assert OpenAIResponsesToolsExtension.name == "openai_responses_tools"
    assert OpenAIResponsesReasoningExtension.name == "openai_responses_reasoning"
    assert OpenAIResponsesUsageExtension.name == "openai_responses_usage"
    assert OpenAIResponsesVerbosityExtension.name == "openai_responses_verbosity"


def test_descriptor_entries_match_and_import() -> None:
    descriptor_path = Path(__file__).resolve().parents[1] / "agent_plugin.json"
    data = json.loads(descriptor_path.read_text(encoding="utf-8"))

    assert data.get("module") == "openai_responses_plugins"
    entries = data.get("entries")
    assert isinstance(entries, list) and entries

    for entry in entries:
        symbol = _import_symbol(entry)
        assert symbol is not None
