from __future__ import annotations

from agent_app.plugin_sources import DottedClassSource


def test_dotted_class_source_matches_only_valid_dotted_paths() -> None:
    src = DottedClassSource()

    assert src.supports("plugins.openai_provider.OpenAICompatibleProvider")
    assert src.supports("tests.dummy_provider.DummyProvider")
    assert not src.supports("bash:./tests/fixtures/bash_tools/read_line_range.bash")
    assert not src.supports("bash+git:https://example.com/repo.git#v1")
    assert not src.supports("node:plugins/js-echo-tool")
    assert not src.supports("path:./plugins/some-python-plugin")
    assert not src.supports("git+https://example.com/repo.git")
