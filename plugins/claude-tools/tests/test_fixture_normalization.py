# Copyright 2026 Dynamic Programming Solutions Kft.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "plugins/claude-tools/investigation/scripts"
FIXTURES = ROOT / "plugins/claude-tools/investigation/fixtures"
sys.path.insert(0, str(SCRIPTS))

from normalize_proxy_log import (  # noqa: E402
    contains_user_home_path,
    normalize_value,
)


def test_normalize_value_replaces_platform_user_home_paths() -> None:
    value = {
        "macos": "/" + "Users/alice/project/file.txt",
        "linux": ["/" + "home/bob/project/file.txt"],
        "windows_backslash": "C:" + r"\Users\carol\project\file.txt",
        "windows_slash": "D:" + "/Users/dave/project/file.txt",
        "encoded_macos": "-" + "Users-alice-project",
        "encoded_linux": "-" + "home-bob-project",
        "encoded_windows": "-" + "C--Users-carol-project",
    }

    assert normalize_value(value, {}) == {
        "macos": "<USER_HOME>/project/file.txt",
        "linux": ["<USER_HOME>/project/file.txt"],
        "windows_backslash": r"<USER_HOME>\project\file.txt",
        "windows_slash": "<USER_HOME>/project/file.txt",
        "encoded_macos": "<USER_HOME_KEY>-project",
        "encoded_linux": "<USER_HOME_KEY>-project",
        "encoded_windows": "<USER_HOME_KEY>-project",
    }


def test_explicit_replacements_take_precedence_over_home_normalization() -> None:
    workspace = "/" + "Users/alice/project"

    assert normalize_value(
        {
            "workspace": f"{workspace}/file.txt",
            "home": "/" + "Users/alice/.claude/debug.log",
        },
        {workspace: "<WORKSPACE>"},
    ) == {
        "workspace": "<WORKSPACE>/file.txt",
        "home": "<USER_HOME>/.claude/debug.log",
    }


def test_normalization_preserves_placeholders_and_unrelated_urls() -> None:
    value = {
        "workspace": "<WORKSPACE>/file.txt",
        "home": "<USER_HOME>/.claude/debug.log",
        "url": "https://example.com/home/alice",
        "schema": "Use /home-relative paths only when explicitly requested.",
    }

    assert normalize_value(value, {}) == value


def test_committed_fixtures_have_no_real_user_home_paths() -> None:
    findings = [
        path.relative_to(ROOT).as_posix()
        for path in FIXTURES.rglob("*")
        if path.is_file()
        and contains_user_home_path(path.read_text(encoding="utf-8", errors="replace"))
    ]

    assert findings == []