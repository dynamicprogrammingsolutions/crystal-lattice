from __future__ import annotations

import html
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from markdown import markdown as markdown_to_html
from xhtml2pdf import pisa


PDF_ENGINE_AUTO = "auto"
PDF_ENGINE_PANDOC = "pandoc"
PDF_ENGINE_XHTML2PDF = "xhtml2pdf"
SUPPORTED_PDF_ENGINES = {
    PDF_ENGINE_AUTO,
    PDF_ENGINE_PANDOC,
    PDF_ENGINE_XHTML2PDF,
}
DEFAULT_LANGUAGE = "en-US"
DEFAULT_TOC_DEPTH = 2
DEFAULT_EPUB_TITLE = "Untitled EPUB"
DEFAULT_LUA_FILTER_PATH = Path(__file__).with_name("strip_local_file_references.lua")


@dataclass(frozen=True)
class MessageExportContext:
    session_id: str
    session_short_id: str
    message_index: int
    role: str
    content: str
    metadata: Dict[str, Any]
    multipart_count: int
    default_title: str
    default_filename_stem: str


@dataclass(frozen=True)
class SessionExportContext:
    session_id: str
    session_short_id: str
    session_title: str | None
    default_title: str
    default_filename_stem: str
    entries: Tuple[MessageExportContext, ...]


def normalize_pdf_engine(raw_value: Any) -> str:
    if not isinstance(raw_value, str):
        return PDF_ENGINE_AUTO
    normalized = raw_value.strip().lower()
    if normalized in SUPPORTED_PDF_ENGINES:
        return normalized
    return PDF_ENGINE_AUTO


def slugify_filename_stem(value: str, *, fallback: str) -> str:
    text = (value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text or fallback


def ensure_suffix(filename: str, suffix: str) -> str:
    cleaned = (filename or "").strip()
    if not cleaned:
        return suffix
    if cleaned.lower().endswith(suffix.lower()):
        return cleaned
    return f"{cleaned}{suffix}"


def build_message_export_context(
    *,
    session_id: str,
    message_index: int,
    message: Any,
) -> MessageExportContext:
    role = str(getattr(message, "role", "") or "unknown")
    content = getattr(message, "content", "")
    metadata = getattr(message, "metadata", None)
    multipart_content = getattr(message, "multipart_content", None)

    text_content = str(content or "")
    metadata_dict = metadata if isinstance(metadata, dict) else {}
    multipart_count = len(multipart_content) if isinstance(multipart_content, list) else 0
    session_short_id = session_id[:8]
    default_title = f"Session {session_short_id} Message {message_index}"
    default_filename_stem = f"session-{session_short_id}-message-{message_index}"

    return MessageExportContext(
        session_id=session_id,
        session_short_id=session_short_id,
        message_index=message_index,
        role=role,
        content=text_content,
        metadata=dict(metadata_dict),
        multipart_count=multipart_count,
        default_title=default_title,
        default_filename_stem=default_filename_stem,
    )


def build_session_export_context(
    *,
    session_id: str,
    session_title: str | None,
    messages: Sequence[Any],
) -> SessionExportContext:
    session_short_id = session_id[:8]
    entries: List[MessageExportContext] = []
    for index, message in enumerate(messages):
        role = str(getattr(message, "role", "") or "")
        content = str(getattr(message, "content", "") or "")
        if role == "assistant" and not content.strip():
            continue
        if role not in {"user", "assistant"}:
            continue
        entries.append(
            build_message_export_context(
                session_id=session_id,
                message_index=index,
                message=message,
            )
        )

    default_title = session_title.strip() if isinstance(session_title, str) and session_title.strip() else f"Session {session_short_id}"
    default_filename_stem = f"session-{session_short_id}"
    return SessionExportContext(
        session_id=session_id,
        session_short_id=session_short_id,
        session_title=session_title.strip() if isinstance(session_title, str) and session_title.strip() else None,
        default_title=default_title,
        default_filename_stem=default_filename_stem,
        entries=tuple(entries),
    )


def _role_label(role: str) -> str:
    if role == "assistant":
        return "Assistant"
    if role == "user":
        return "User"
    return role.title() if role else "Message"


def demote_markdown_headings(markdown_text: str, *, base_level: int = 3) -> str:
    offset = max(base_level - 1, 0)
    lines = markdown_text.splitlines()
    adjusted: List[str] = []
    for line in lines:
        match = re.match(r"^(\s{0,3})(#{1,6})(\s+.*)$", line)
        if not match:
            adjusted.append(line)
            continue
        indent, hashes, rest = match.groups()
        new_level = min(len(hashes) + offset, 6)
        adjusted.append(f"{indent}{'#' * new_level}{rest}")
    return "\n".join(adjusted)


def render_message_markdown(context: MessageExportContext, *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- Session ID: `{context.session_id}`",
        f"- Message Index: `{context.message_index}`",
        f"- Role: `{context.role}`",
    ]
    if context.multipart_count:
        lines.append(f"- Multipart attachments omitted in this export: `{context.multipart_count}`")
    lines.extend(["", "---", ""])
    if context.content.strip():
        lines.append(context.content)
    else:
        lines.append("_This message has no text content._")
    return "\n".join(lines).strip() + "\n"


def render_session_markdown(context: SessionExportContext, *, title: str) -> str:
    h1 = f"# {context.session_id}"
    if context.session_title:
        h1 = f"# {context.session_id} - {context.session_title}"
    if title != context.default_title:
        h1 = f"# {context.session_id} - {title}"

    lines: List[str] = [h1, ""]
    if not context.entries:
        lines.append("_This session has no exportable user or assistant messages._")
        return "\n".join(lines).strip() + "\n"

    for entry in context.entries:
        lines.extend(
            [
                f"## {_role_label(entry.role)} message {entry.message_index}",
                "",
            ]
        )
        if entry.content.strip():
            lines.append(demote_markdown_headings(entry.content, base_level=3))
        else:
            lines.append("_This message has no text content._")
        lines.extend(["", ""])

    return "\n".join(lines).strip() + "\n"


def pandoc_available() -> bool:
    return shutil.which("pandoc") is not None


def _pandoc_pdf_engine_name() -> str | None:
    if shutil.which("xelatex") is not None:
        return "xelatex"
    if shutil.which("pdflatex") is not None:
        return "pdflatex"
    return None


def _pandoc_pdf_usable() -> bool:
    return pandoc_available() and _pandoc_pdf_engine_name() is not None


def select_pdf_runtime_engine(engine_setting: str) -> Tuple[str, str | None]:
    normalized = normalize_pdf_engine(engine_setting)
    if normalized == PDF_ENGINE_XHTML2PDF:
        return PDF_ENGINE_XHTML2PDF, None
    if normalized == PDF_ENGINE_PANDOC:
        pdf_engine = _pandoc_pdf_engine_name()
        if not pandoc_available():
            raise RuntimeError("PDF export is configured to use pandoc, but pandoc is not installed.")
        if pdf_engine is None:
            raise RuntimeError(
                "PDF export is configured to use pandoc, but no supported PDF engine was found. "
                "Install xelatex or pdflatex."
            )
        return PDF_ENGINE_PANDOC, pdf_engine
    if _pandoc_pdf_usable():
        return PDF_ENGINE_PANDOC, _pandoc_pdf_engine_name()
    return PDF_ENGINE_XHTML2PDF, None


def convert_markdown_to_epub(
    *,
    markdown_text: str,
    title: str,
    output_path: Path,
    author: str | None = None,
    language: str = DEFAULT_LANGUAGE,
    toc_depth: int = DEFAULT_TOC_DEPTH,
    lua_filter: Path | None = None,
) -> None:
    if not pandoc_available():
        raise RuntimeError("EPUB export requires pandoc, but pandoc is not installed.")

    with tempfile.TemporaryDirectory(prefix="message-export-epub-") as tmpdir:
        work_dir = Path(tmpdir)
        markdown_path = work_dir / "document.md"
        markdown_path.write_text(markdown_text, encoding="utf-8")
        metadata_path = work_dir / "metadata.yaml"

        effective_title = title or DEFAULT_EPUB_TITLE
        effective_language = language or DEFAULT_LANGUAGE
        effective_toc_depth = toc_depth if isinstance(toc_depth, int) and toc_depth > 0 else DEFAULT_TOC_DEPTH
        effective_filter = lua_filter or DEFAULT_LUA_FILTER_PATH
        if not effective_filter.is_file():
            raise RuntimeError(f"EPUB export Lua filter not found: {effective_filter}")

        if author:
            metadata_path.write_text(
                (
                    f"---\n"
                    f'title: "{effective_title}"\n'
                    f"author:\n"
                    f'  - "{author}"\n'
                    f'language: "{effective_language}"\n'
                    f"toc: true\n"
                    f"toc-depth: {effective_toc_depth}\n"
                    f"---\n"
                ),
                encoding="utf-8",
            )
        else:
            metadata_path.write_text(
                (
                    f"---\n"
                    f'title: "{effective_title}"\n'
                    f'language: "{effective_language}"\n'
                    f"toc: true\n"
                    f"toc-depth: {effective_toc_depth}\n"
                    f"---\n"
                ),
                encoding="utf-8",
            )

        cmd = [
            "pandoc",
            str(metadata_path),
            str(markdown_path),
            f"--lua-filter={effective_filter}",
            "--toc",
            f"--toc-depth={effective_toc_depth}",
            "-o",
            str(output_path),
        ]
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "unknown error").strip()
            raise RuntimeError(f"pandoc EPUB conversion failed: {detail}")


def _html_document(*, title: str, markdown_text: str) -> str:
    body_html = markdown_to_html(
        markdown_text,
        extensions=["extra", "fenced_code", "tables", "sane_lists", "nl2br"],
    )
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>{html.escape(title)}</title>
    <style>
      body {{
        font-family: Helvetica, Arial, sans-serif;
        font-size: 11pt;
        line-height: 1.45;
        color: #111827;
        margin: 24pt 30pt;
      }}
      h1, h2, h3, h4, h5, h6 {{
        color: #111827;
        margin-top: 1.1em;
        margin-bottom: 0.4em;
      }}
      p, li {{
        margin: 0.35em 0;
      }}
      code, pre {{
        font-family: Courier, monospace;
        background: #f3f4f6;
      }}
      pre {{
        padding: 8pt;
        border: 1px solid #d1d5db;
        white-space: pre-wrap;
      }}
      hr {{
        border: none;
        border-top: 1px solid #d1d5db;
        margin: 1em 0;
      }}
    </style>
  </head>
  <body>
    {body_html}
  </body>
</html>
"""


def _convert_markdown_to_pdf_pandoc(
    *,
    markdown_text: str,
    title: str,
    output_path: Path,
    pdf_engine: str,
) -> None:
    with tempfile.TemporaryDirectory(prefix="message-export-pdf-pandoc-") as tmpdir:
        work_dir = Path(tmpdir)
        markdown_path = work_dir / "document.md"
        markdown_path.write_text(markdown_text, encoding="utf-8")

        cmd = [
            "pandoc",
            "--from",
            "gfm",
            "--metadata",
            f"title={title}",
            "--pdf-engine",
            pdf_engine,
            "-o",
            str(output_path),
            str(markdown_path),
        ]
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "unknown error").strip()
            raise RuntimeError(f"pandoc PDF conversion failed: {detail}")


def _convert_markdown_to_pdf_xhtml2pdf(
    *,
    markdown_text: str,
    title: str,
    output_path: Path,
) -> None:
    document = _html_document(title=title, markdown_text=markdown_text)
    with output_path.open("wb") as stream:
        result = pisa.CreatePDF(document, dest=stream, encoding="utf-8")
    if getattr(result, "err", 0):
        raise RuntimeError("xhtml2pdf conversion failed.")


def convert_markdown_to_pdf(
    *,
    markdown_text: str,
    title: str,
    output_path: Path,
    engine_setting: str,
) -> str:
    runtime_engine, pandoc_pdf_engine = select_pdf_runtime_engine(engine_setting)
    if runtime_engine == PDF_ENGINE_PANDOC:
        _convert_markdown_to_pdf_pandoc(
            markdown_text=markdown_text,
            title=title,
            output_path=output_path,
            pdf_engine=str(pandoc_pdf_engine),
        )
        return PDF_ENGINE_PANDOC

    _convert_markdown_to_pdf_xhtml2pdf(
        markdown_text=markdown_text,
        title=title,
        output_path=output_path,
    )
    return PDF_ENGINE_XHTML2PDF


def temp_output_path(*, filename: str) -> Path:
    safe_name = os.path.basename(filename) or "export.bin"
    tmp_dir = tempfile.mkdtemp(prefix="message-export-")
    return Path(tmp_dir) / safe_name