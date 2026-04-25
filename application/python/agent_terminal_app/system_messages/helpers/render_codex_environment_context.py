from pathlib import Path
from typing import TYPE_CHECKING
from xml.sax.saxutils import escape


if TYPE_CHECKING:
    cwd = ""
    shell = ""


_cwd = escape(str(Path(cwd).resolve()))
_shell = escape(str(shell))

SYSTEM_MESSAGE_VALUE = (
    "<environment_context>\n"
    f"<cwd>{_cwd}</cwd>\n"
    f"<shell>{_shell}</shell>\n"
    "</environment_context>"
)