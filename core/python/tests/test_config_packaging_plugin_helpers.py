from __future__ import annotations

from agent_app.config import collect_unique_declared_plugin_specs
from agent_app.config import remove_declared_plugin_specs_by_exact_match


def test_collect_unique_declared_plugin_specs_uses_structural_plugin_lists_only() -> None:
    config = {
        "plugins": [
            "path:/plugins/openrouter",
        ],
        "providers": {
            "shared": {
                "plugins": [
                    "path:/plugins/codex-tools",
                ]
            }
        },
        "agents": {
            "assistant": {
                "provider": "shared",
                "plugins": [
                    "path:/plugins/openrouter",
                    {"path": "/plugins/cloud-agent-app"},
                ],
            }
        },
        "application": {
            "cloud_agent": {
                "disabled_plugins": [
                    {"$raw": "path:/plugins/message-export-actions"}
                ]
            }
        },
        "note": "path:/plugins/not-a-plugin-selection",
    }

    specs = collect_unique_declared_plugin_specs(config)

    assert specs == [
        "path:/plugins/openrouter",
        "path:/plugins/codex-tools",
        {"path": "/plugins/cloud-agent-app"},
    ]


def test_remove_declared_plugin_specs_by_exact_match_filters_only_plugin_lists() -> None:
    config = {
        "plugins": [
            "path:/plugins/openrouter",
            "path:/plugins/message-export-actions",
        ],
        "providers": {
            "shared": {
                "plugins": [
                    "path:/plugins/message-export-actions",
                    "path:/plugins/codex-tools",
                ]
            }
        },
        "agents": {
            "assistant": {
                "provider": "shared",
                "plugins": [
                    "path:/plugins/message-export-actions",
                ],
            }
        },
        "application": {
            "cloud_agent": {
                "disabled_plugins": [
                    {"$raw": "path:/plugins/message-export-actions"}
                ]
            }
        },
    }

    manifest = remove_declared_plugin_specs_by_exact_match(
        config, ["path:/plugins/message-export-actions"]
    )

    assert config["plugins"] == ["path:/plugins/openrouter"]
    assert config["providers"]["shared"]["plugins"] == ["path:/plugins/codex-tools"]
    assert config["agents"]["assistant"]["plugins"] == []
    assert config["application"]["cloud_agent"]["disabled_plugins"] == [
        {"$raw": "path:/plugins/message-export-actions"}
    ]
    assert manifest["requested"] == ["path:/plugins/message-export-actions"]
    assert len(manifest["removed"]) == 3