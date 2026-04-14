from __future__ import annotations

from pathlib import Path
import json
import pytest

from agent_app.application_future import AgentApplication


def test_application_raises_for_plugin_errors(tmp_path: Path, monkeypatch) -> None:
    # Use the localpath config fixture but point to a non-existent plugins dir
    fixtures_cfg = Path(__file__).parent / "fixtures" / "configs" / "localpath_plugins.json"
    cfg = json.loads(fixtures_cfg.read_text(encoding="utf-8"))
    # Write a temp config with env placeholders intact
    temp_cfg = tmp_path / "cfg.json"
    temp_cfg.write_text(json.dumps(cfg), encoding="utf-8")
    # Set DEV_PLUGINS_DIR to a path that does not exist
    monkeypatch.setenv("DEV_PLUGINS_DIR", str(tmp_path / "does_not_exist"))
    # Required provider envs
    monkeypatch.setenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
    monkeypatch.setenv("OLLAMA_MODEL_TOOLS", "qwen3:0.6b")
    with pytest.raises(RuntimeError, match="Plugin resolution failed"):
        AgentApplication(str(temp_cfg), str(tmp_path / "sessions"))


def test_application_defaults_plugin_cache_dir_relative_to_config(tmp_path: Path) -> None:
    cfg = {
        "providers": {
            "dummy": {"provider": "dummy_provider", "model": "test-model"}
        },
        "plugins": ["tests.dummy_provider.DummyProvider"],
        "agents": {"default": {"provider": "dummy"}},
    }

    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(cfg), encoding="utf-8")

    app = AgentApplication(str(config_path), str(tmp_path / "sessions"))

    assert app.get_config_errors() == []
