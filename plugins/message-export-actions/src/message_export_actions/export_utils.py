from __future__ import annotations

import html
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

from markdown import markdown as markdown_to_html
from xhtml2pdf import pisa


PDF_ENGINE_AUTO = "auto"
PDF_ENGINE_PANDOC = "pandoc"
PDF_ENGINE_PLAYWRIGHT = "playwright"
PDF_ENGINE_XHTML2PDF = "xhtml2pdf"
SUPPORTED_PDF_ENGINES = {
    PDF_ENGINE_AUTO,
    PDF_ENGINE_PANDOC,
    PDF_ENGINE_PLAYWRIGHT,
    PDF_ENGINE_XHTML2PDF,
}
PDF_STYLE_WEB = "web"
PDF_STYLE_CLASSIC = "classic"
SUPPORTED_PDF_STYLES = {
    PDF_STYLE_WEB,
    PDF_STYLE_CLASSIC,
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


def normalize_pdf_style(raw_value: Any) -> str:
    if not isinstance(raw_value, str):
        return PDF_STYLE_WEB
    normalized = raw_value.strip().lower()
    if normalized in SUPPORTED_PDF_STYLES:
        return normalized
    return PDF_STYLE_WEB


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
    if normalized == PDF_ENGINE_PLAYWRIGHT:
        return PDF_ENGINE_PLAYWRIGHT, None
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


def _classic_html_css() -> str:
    return """
      body {
        font-family: Helvetica, Arial, sans-serif;
        font-size: 11pt;
        line-height: 1.45;
        color: #111827;
        margin: 24pt 30pt;
      }
      h1, h2, h3, h4, h5, h6 {
        color: #111827;
        margin-top: 1.1em;
        margin-bottom: 0.4em;
      }
      p, li {
        margin: 0.35em 0;
      }
      code, pre {
        font-family: Courier, monospace;
        background: #f3f4f6;
      }
      pre {
        padding: 8pt;
        border: 1px solid #d1d5db;
        white-space: pre-wrap;
      }
      hr {
        border: none;
        border-top: 1px solid #d1d5db;
        margin: 1em 0;
      }
    """


def _web_html_css() -> str:
    return """
      @page {
        margin: 24pt 30pt;
      }
      body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
        font-size: 10.5pt;
        line-height: 1.55;
        color: #172033;
        margin: 0;
      }
      .document {
        max-width: 720pt;
      }
      h1 {
        font-size: 23pt;
        line-height: 1.15;
        font-weight: 700;
        color: #0f172a;
        margin: 0 0 18pt;
        padding-bottom: 10pt;
        border-bottom: 1pt solid #d8dee8;
      }
      h2 {
        font-size: 16pt;
        line-height: 1.25;
        font-weight: 700;
        color: #1e293b;
        margin: 22pt 0 8pt;
      }
      h3, h4, h5, h6 {
        color: #334155;
        font-weight: 650;
        margin: 14pt 0 5pt;
      }
      h3 {
        font-size: 13pt;
      }
      p {
        margin: 0 0 8pt;
      }
      ul, ol {
        margin: 0 0 10pt 18pt;
        padding: 0;
      }
      li {
        margin: 2pt 0 4pt;
      }
      a {
        color: #2563eb;
        text-decoration: none;
      }
      blockquote {
        color: #475569;
        border-left: 3pt solid #cbd5e1;
        margin: 10pt 0;
        padding: 2pt 0 2pt 10pt;
      }
      code {
        font-family: "SFMono-Regular", Menlo, Consolas, Courier, monospace;
        font-size: 9.5pt;
        color: #0f172a;
        background: #f1f5f9;
      }
      pre {
        font-family: "SFMono-Regular", Menlo, Consolas, Courier, monospace;
        font-size: 9.5pt;
        line-height: 1.4;
        color: #0f172a;
        background: #f8fafc;
        border: 1pt solid #d8dee8;
        padding: 9pt 10pt;
        white-space: pre-wrap;
      }
      pre code {
        background: transparent;
      }
      hr {
        border: none;
        border-top: 1pt solid #d8dee8;
        margin: 16pt 0;
      }
      table {
        border-collapse: collapse;
        margin: 10pt 0;
        width: 100%;
      }
      th, td {
        border: 1pt solid #d8dee8;
        padding: 5pt 7pt;
      }
      th {
        background: #f8fafc;
        color: #334155;
        font-weight: 700;
      }
    """


def _html_document(*, title: str, markdown_text: str, style: str = PDF_STYLE_WEB) -> str:
    body_html = markdown_to_html(
        markdown_text,
        extensions=["extra", "fenced_code", "tables", "sane_lists", "nl2br"],
    )
    css = _classic_html_css() if normalize_pdf_style(style) == PDF_STYLE_CLASSIC else _web_html_css()
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>{html.escape(title)}</title>
    <style>
{css}
    </style>
  </head>
  <body>
    <main class="document">
      {body_html}
    </main>
  </body>
</html>
"""


def _convert_markdown_to_pdf_pandoc(
    *,
    markdown_text: str,
    title: str,
    output_path: Path,
    pdf_engine: str,
    style: str,
) -> None:
    with tempfile.TemporaryDirectory(prefix="message-export-pdf-pandoc-") as tmpdir:
        work_dir = Path(tmpdir)
        markdown_path = work_dir / "document.md"
        markdown_path.write_text(markdown_text, encoding="utf-8")
        header_path = work_dir / "web-style.tex"
        style_args: List[str] = []
        if normalize_pdf_style(style) == PDF_STYLE_WEB:
            header_path.write_text(
                "\n".join(
                    [
                        r"\renewcommand{\familydefault}{\sfdefault}",
                        r"\setlength{\parindent}{0pt}",
                        r"\setlength{\parskip}{0.55em}",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            font_args: List[str]
            if pdf_engine == "xelatex":
                font_args = [
                    "--variable",
                    "mainfont=Helvetica Neue",
                    "--variable",
                    "sansfont=Helvetica Neue",
                    "--variable",
                    "monofont=Menlo",
                ]
            else:
                font_args = [
                    "--variable",
                    "fontfamily=helvet",
                ]
            style_args = [
                "--variable",
                "documentclass=article",
                "--variable",
                "geometry:margin=0.72in",
                "--variable",
                "fontsize=11pt",
                "--variable",
                "linestretch=1.08",
                *font_args,
                "--variable",
                "colorlinks=true",
                "--variable",
                "linkcolor=2563EB",
                "--variable",
                "urlcolor=2563EB",
                "--include-in-header",
                str(header_path),
            ]

        cmd = [
            "pandoc",
            "--from",
            "gfm",
            "--metadata",
            f"title={title}",
            "--pdf-engine",
            pdf_engine,
            *style_args,
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
    style: str,
) -> None:
    document = _html_document(title=title, markdown_text=markdown_text, style=style)
    with output_path.open("wb") as stream:
        result = pisa.CreatePDF(document, dest=stream, encoding="utf-8")
    if getattr(result, "err", 0):
        raise RuntimeError("xhtml2pdf conversion failed.")


def _convert_markdown_to_pdf_playwright(
    *,
    markdown_text: str,
    title: str,
    output_path: Path,
    style: str,
) -> None:
    document = _html_document(title=title, markdown_text=markdown_text, style=style)
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "PDF export is configured to use Playwright, but the playwright package is not installed."
        ) from exc

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            try:
                page = browser.new_page()
                page.set_content(document, wait_until="load")
                page.pdf(
                    path=str(output_path),
                    format="Letter",
                    print_background=True,
                    prefer_css_page_size=True,
                )
            finally:
                browser.close()
    except PlaywrightError as exc:
        raise RuntimeError(
            "Playwright PDF conversion failed. If Chromium is not installed, run "
            "`python -m playwright install chromium` in the plugin/runtime environment."
        ) from exc


def convert_markdown_to_pdf(
    *,
    markdown_text: str,
    title: str,
    output_path: Path,
    engine_setting: str,
    style_setting: str = PDF_STYLE_WEB,
) -> str:
    runtime_engine, pandoc_pdf_engine = select_pdf_runtime_engine(engine_setting)
    normalized_style = normalize_pdf_style(style_setting)
    if runtime_engine == PDF_ENGINE_PANDOC:
        _convert_markdown_to_pdf_pandoc(
            markdown_text=markdown_text,
            title=title,
            output_path=output_path,
            pdf_engine=str(pandoc_pdf_engine),
            style=normalized_style,
        )
        return PDF_ENGINE_PANDOC
    if runtime_engine == PDF_ENGINE_PLAYWRIGHT:
        _convert_markdown_to_pdf_playwright(
            markdown_text=markdown_text,
            title=title,
            output_path=output_path,
            style=normalized_style,
        )
        return PDF_ENGINE_PLAYWRIGHT

    _convert_markdown_to_pdf_xhtml2pdf(
        markdown_text=markdown_text,
        title=title,
        output_path=output_path,
        style=normalized_style,
    )
    return PDF_ENGINE_XHTML2PDF


def temp_output_path(*, filename: str) -> Path:
    safe_name = os.path.basename(filename) or "export.bin"
    tmp_dir = tempfile.mkdtemp(prefix="message-export-")
    return Path(tmp_dir) / safe_name