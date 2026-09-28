"""Executable checks for the Core package quickstart."""

from pathlib import Path
import re


QUICKSTART = Path(__file__).parents[1] / "docs" / "quickstart.md"


def _quickstart_example() -> str:
    text = QUICKSTART.read_text(encoding="utf-8")
    match = re.search(
        r"<!-- quickstart-example-start -->\s*```python\n(.*?)\n```\s*"
        r"<!-- quickstart-example-end -->",
        text,
        re.DOTALL,
    )
    assert match is not None, "quickstart executable example markers are missing"
    return match.group(1)


def test_quickstart_example_executes_with_expected_output(capsys) -> None:
    namespace = {"__name__": "__quickstart__"}

    exec(compile(_quickstart_example(), str(QUICKSTART), "exec"), namespace)

    assert capsys.readouterr().out == (
        "SYS= | USER=Hello from the echo provider!\n"
    )
    session = namespace["session"]
    assert [message.role for message in session.messages] == ["user", "assistant"]