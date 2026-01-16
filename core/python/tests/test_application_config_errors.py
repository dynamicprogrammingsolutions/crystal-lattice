from __future__ import annotations

from pathlib import Path
import os
import json

from agent_app.application_future import AgentApplication


def test_application_exposes_plugin_errors(tmp_path: Path, monkeypatch) -> None:
    # Use the localpath config fixture but point to a non-existent plugins dir
    fixtures_cfg = Path(__file__).parent / "fixtures" / "configs" / "localpath_plugins.json"
    cfg = json.loads(fixtures_cfg.read_text(encoding="utf-8"))
    plugin_cache = tmp_path / "cache"
    plugin_cache.mkdir(parents=True, exist_ok=True)
    # Write a temp config with env placeholders intact
    temp_cfg = tmp_path / "cfg.json"
    cfg["plugin_cache_dir"] = str(plugin_cache)
    temp_cfg.write_text(json.dumps(cfg), encoding="utf-8")
    # Set DEV_PLUGINS_DIR to a path that does not exist
    monkeypatch.setenv("DEV_PLUGINS_DIR", str(tmp_path / "does_not_exist"))
    # Required provider envs
    monkeypatch.setenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
    monkeypatch.setenv("OLLAMA_MODEL_TOOLS", "qwen3:0.6b")
    app = AgentApplication(str(temp_cfg), str(tmp_path / "sessions"))
    errs = app.get_config_errors()
    assert any(e.get("type") in {"plugin_path_invalid", "plugin_import_error"} for e in errs)
