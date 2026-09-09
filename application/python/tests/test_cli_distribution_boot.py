from __future__ import annotations

import json
import os
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from crystal_lattice_cli_boot import (  # noqa: E402
    assert_default_config_boot,
    build_isolated_cli_environment,
    collect_env_placeholder_names,
)


def test_collect_env_placeholder_names_ignores_raw_values(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "resolved": "${env:FIRST}/x/${env:SECOND}",
                "nested": [{"value": "${env:THIRD}"}],
                "literal": {"$raw": "${env:IGNORED}"},
            }
        ),
        encoding="utf-8",
    )

    assert collect_env_placeholder_names(config_path) == {
        "FIRST",
        "SECOND",
        "THIRD",
    }


def test_build_isolated_cli_environment_removes_config_inputs_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        '{"api_key": "${env:CONFIG_INPUT}", '
        '"literal": {"$raw": "${env:DIRECT_PLUGIN_INPUT}"}}',
        encoding="utf-8",
    )
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    monkeypatch.setenv("CONFIG_INPUT", "must-not-leak")
    monkeypatch.setenv("DIRECT_PLUGIN_INPUT", "plugin-owned")
    monkeypatch.setenv("PYTHONPATH", "must-not-leak")

    env, removed = build_isolated_cli_environment(
        config_path,
        home_dir=home_dir,
    )

    assert removed == {"CONFIG_INPUT"}
    assert "CONFIG_INPUT" not in env
    assert "PYTHONPATH" not in env
    assert env["DIRECT_PLUGIN_INPUT"] == "plugin-owned"
    assert env["HOME"] == str(home_dir.resolve())
    assert env["USERPROFILE"] == str(home_dir.resolve())


def test_default_config_boot_uses_clean_state_and_stops_server(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = _write_default_config(tmp_path)
    server_script = _write_fake_cli_server(tmp_path)
    workspace = tmp_path / "workspace"
    home_dir = tmp_path / "home"
    monkeypatch.setenv("CONFIG_INPUT", "must-not-leak")

    result = assert_default_config_boot(
        [sys.executable, server_script, config_path, home_dir],
        default_config_template=config_path,
        workspace=workspace,
        home_dir=home_dir,
        plugin_cache_expectation="empty",
        timeout_seconds=20,
    )

    assert result.agents == ("alpha", "beta")
    assert result.generated_config == workspace / ".crystal" / "config.json"
    assert result.removed_placeholder_names == ("CONFIG_INPUT",)
    assert (workspace / ".env").read_text(encoding="utf-8") == ""


@pytest.mark.skipif(os.name != "nt", reason="Windows .cmd process-tree coverage")
def test_windows_cmd_boot_stops_descendant_python_server(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = _write_default_config(tmp_path)
    server_script = _write_fake_cli_server(tmp_path)
    workspace = tmp_path / "workspace"
    home_dir = tmp_path / "home"
    wrapper = tmp_path / "fake-crystal-lattice.cmd"
    wrapper.write_text(
        "@echo off\r\n"
        f'"{sys.executable}" "{server_script}" "{config_path}" "{home_dir}" %*\r\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("CONFIG_INPUT", "must-not-leak")

    result = assert_default_config_boot(
        [wrapper],
        default_config_template=config_path,
        workspace=workspace,
        home_dir=home_dir,
        plugin_cache_expectation="empty",
        timeout_seconds=20,
    )

    assert result.agents == ("alpha", "beta")


def _write_default_config(tmp_path: Path) -> Path:
    config_path = tmp_path / "default-config.json"
    config_path.write_text(
        json.dumps(
            {
                "credential": "${env:CONFIG_INPUT}",
                "agents": {"beta": {}, "alpha": {}},
            }
        ),
        encoding="utf-8",
    )
    return config_path


def _write_fake_cli_server(tmp_path: Path) -> Path:
    script_path = tmp_path / "fake_cli_server.py"
    script_path.write_text(
        """
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import sys


template = Path(sys.argv[1])
expected_home = Path(sys.argv[2]).resolve()
parser = argparse.ArgumentParser()
parser.add_argument("--server", action="store_true")
parser.add_argument("--config-local", action="store_true")
parser.add_argument("--host", required=True)
parser.add_argument("--port", required=True, type=int)
args = parser.parse_args(sys.argv[3:])

if os.environ.get("CONFIG_INPUT") is not None:
    raise SystemExit("CONFIG_INPUT leaked into child")
if Path.home().resolve() != expected_home:
    raise SystemExit(f"unexpected home: {Path.home()}")

config = json.loads(template.read_text(encoding="utf-8"))
config_dir = Path.cwd() / ".crystal"
config_dir.mkdir()
(config_dir / "config.json").write_text(json.dumps(config), encoding="utf-8")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/hello":
            payload = {"message": "hello"}
        elif self.path == "/agents":
            payload = {"agents": sorted(config["agents"])}
        else:
            self.send_response(404)
            self.end_headers()
            return
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()
""".lstrip(),
        encoding="utf-8",
    )
    return script_path
